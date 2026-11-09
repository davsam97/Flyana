"""Password hashing, JWTs and opaque tokens

- Argon2 takes 100-300 ms of CPU: every hash runs in `asyncio.to_thread` so it
  never blocks the event loop.
- A failed login costs the same time as a successful one (`dummy_verify`), so
  timing does not reveal whether an email exists.
- Secrets are compared with `secrets.compare_digest`, never `==`.
"""

from __future__ import annotations

import asyncio
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from functools import lru_cache
from cryptography.fernet import Fernet

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.config import get_settings

settings = get_settings()

ALGORITHM = "HS256"

_hasher = PasswordHash((Argon2Hasher(),))

# Checked by `dummy_verify` so a failed lookup costs a real Argon2 verify
_DUMMY_HASH = _hasher.hash("timing-equalisation-dummy-password")


def _hash_sync(password: str) -> str:
    """Argon2 hashing the blocking way

    Never call this straight from async code
    """
    return _hasher.hash(password)


def _verify_sync(password: str, password_hash: str) -> bool:
    """Argon2 checking the blocking way"""
    return _hasher.verify(password, password_hash)


async def hash_password(password: str) -> str:
    """Hashes a password for storage"""
    return await asyncio.to_thread(_hash_sync, password)


async def verify_password(password: str, password_hash: str | None) -> bool:
    """Checks a password against its stored hash

    Falls back to the dummy hash so a NULL hash still costs the same time
    """
    return await asyncio.to_thread(_verify_sync, password, _DUMMY_HASH if not password_hash else password_hash)


async def dummy_verify(password: str) -> bool:
    """Burns as much CPU as a real `verify_password` then fails anyway

    Used for an unknown email or an OAuth-only account: otherwise answering in
    1 ms instead of 200 ms would reveal that the email exists.
    """
    await asyncio.to_thread(_verify_sync, password, _DUMMY_HASH)
    return False


def _now() -> datetime:
    """Current time as an aware UTC datetime"""
    return datetime.now(UTC)


def _encode(payload: dict[str, Any], ttl: int, typ: str) -> str:
    """Signs a payload into a JWT"""
    now = _now()
    payload |= {
        "typ": typ,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(user_id: int, role: str) -> str:
    """Makes the short lived token that proves who you are

    Carries the role so most checks need no database read
    """
    # `sub` must be a string (RFC 7519): PyJWT rejects an int
    return _encode({"sub": str(user_id), "role": role}, settings.ACCESS_TOKEN_TTL, "access")


def create_partial_token(user_id: int) -> str:
    """Makes the half way token issued once the password is right

    Proves the password step passed but opens no session until the code is given
    """
    return _encode({"sub": str(user_id)}, settings.MFA_TOKEN_TTL, "mfa")


def decode_token(token: str, expected_typ: str = "access") -> dict[str, Any]:
    """Decodes a token and checks it is the type expected

    Raises `jwt.InvalidTokenError` on anything wrong

    - `algorithms=[ALGORITHM]` is explicit, never read from the token header,
      which prevents algorithm confusion (`alg: none`).
    - `expected_typ` stops a 2FA partial token from passing as an access token.

    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[ALGORITHM],
        options={"require": ["exp", "iat", "sub", "typ"]},
    )
    if payload.get("typ") != expected_typ:
        raise jwt.InvalidTokenError(f"expected token type : {expected_typ!r}")
    return payload


def generate_opaque_token() -> str:
    """Draws a refresh token as pure randomness never a JWT

    A refresh token must be revocable at once, which a JWT is not.
    """
    return secrets.token_urlsafe(32)


def hash_opaque_token(token: str) -> str:
    """Hashes a refresh token for storage with SHA-256 not Argon2

    256 bits of entropy cannot be brute-forced, so a slow hash would only add
    200 ms to every refresh.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def generate_csrf_token() -> str:
    """Draws a CSRF token which is random and carries no meaning"""
    return secrets.token_urlsafe(32)


@lru_cache
def _fernet() -> Fernet:
    """Builds the cipher used for TOTP secrets

    Cached so the key is read once
    Refuses to run without a configured key rather than storing secrets in clear
    """
    if not settings.TOTP_ENCRYPTION_KEY:
        raise RuntimeError(
            "TOTP_ENCRYPTION_KEY missing: make one with Fernet.generate_key()"
        )
    return Fernet(settings.TOTP_ENCRYPTION_KEY.encode())


def encrypt_totp_secret(secret: str) -> str:
    """Encrypts a TOTP secret before it goes to the database

    Encrypted not hashed because the server must read it back to check codes
    """
    return _fernet().encrypt(secret.encode()).decode()


def decrypt_totp_secret(blob: str) -> str:
    """Reads a stored TOTP secret back"""
    return _fernet().decrypt(blob.encode()).decode()

def generate_backup_code() -> str:
    """Human-typable recovery code.

    Low entropy (10 hex chars) is acceptable only because it is stored as an
    Argon2 hash, like a password.
    """
    return secrets.token_hex(5)
