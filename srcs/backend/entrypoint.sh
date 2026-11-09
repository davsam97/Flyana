#!/bin/sh
set -e

echo "Migrations"

if [ ! -w /srv/media ]; then
  echo "FATAL: /srv/media cannot be written by uid=$(id -u) gid=$(id -g)." >&2
  echo "rebuild with build args UID/GID then 'docker volume rm flyana_media'" >&2
  exit 1
fi

alembic upgrade head

if [ "$SEED_DEMO_DATA" = "true" ]; then
  echo "Content loading"
  python -m seeds
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
