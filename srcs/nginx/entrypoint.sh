#!/bin/sh
set -e

CERT_DIR=/etc/nginx/certs
NAME="${SERVER_NAME:-localhost}"

# An IP address has to be declared as `IP:` in the alternative names. Written as
# `DNS:192.168.1.42`, browsers match it against nothing and refuse the
# certificate, which is what happens when the server is reached by its address
# on the local network instead of by a name.
# `-checkip` answers "does match" for anything it cannot read as an address, so
# the two checks are not interchangeable either: only the fitting one is run
case "$NAME" in
  *[!0-9.]*) ALT="DNS:${NAME}"; CHECK="-checkhost" ;;
  *)         ALT="IP:${NAME}";  CHECK="-checkip" ;;
esac
if [ "$NAME" != "localhost" ]; then
  ALT="${ALT},DNS:localhost"
fi
ALT="${ALT},IP:127.0.0.1"

# `-checkhost` and `-checkip` exit 0 whatever the answer: the verdict is the
# line they print, so it is the line that has to be read
covers_name() {
  openssl x509 -in "$CERT_DIR/server.crt" -noout "$CHECK" "$NAME" 2>/dev/null \
    | grep -q 'does match'
}

# Regenerate when the certificate no longer covers SERVER_NAME: moving the
# server to a LAN address is exactly that, and a certificate kept from a
# previous name would go on being served for a name nobody uses any more
if [ -f "$CERT_DIR/server.crt" ] && ! covers_name; then
  echo "Certification does not cover ${NAME} — regenerating"
  rm -f "$CERT_DIR/server.crt" "$CERT_DIR/server.key"
fi

if [ ! -f "$CERT_DIR/server.crt" ]; then
  echo "No certification found — self signed certification generation for ${NAME}"
  mkdir -p "$CERT_DIR"
  openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
    -keyout "$CERT_DIR/server.key" \
    -out    "$CERT_DIR/server.crt" \
    -subj   "/C=FR/O=flyana/CN=${NAME}" \
    -addext "subjectAltName=${ALT}"
  chmod 600 "$CERT_DIR/server.key"
else
  echo "Existing certification found (${CERT_DIR}/server.crt)"
fi
