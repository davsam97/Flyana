"""Configuration with types, read from env

`pydantic-settings` failed on start if variable missing

Two handling of secrets :

1. **One truth source.** `DATABASE_URL` not stored : composed from  `POSTGRES_*`.

2. **From file.** `X_FILE=/path`, content read as value
   format for secrets Docker/Podman (`/run/secrets/…`), secret never appears in `docker inspect`, `/proc/<pid>/environ`, or child processes.
"""

# from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import quote_plus

from cryptography.fernet import Fernet
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

FILE_SUFFIX = "_FILE"


def expand_file_secrets(environ: dict[str, str] | None = None) -> list[str]:
    """Replaces `X_FILE=/path` by `X=<content>`

    Variable already defined not replaced : priority on explicit env
    """
    env = environ if environ is not None else os.environ
    resolved: list[str] = []

    for key in [k for k in env if k.endswith(FILE_SUFFIX)]:
        target = key[: -len(FILE_SUFFIX)]
        if not target or env.get(target):
            continue
        path = Path(env[key])
        try:
            # `.strip()` : to avoid forgotten newline
            env[target] = path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise RuntimeError(f"{key} pointe vers {path}, illisible : {exc}") from exc
        resolved.append(target)

    return resolved


class Settings(BaseSettings):
    """Every setting the app reads from the environment

    Built once at import so a missing or malformed value fails at startup
    rather than halfway through serving a request
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Source : 4 POSTGRES_*.
    # DATABASE_URL is an escape (URL from provider) empty otherwise.
    POSTGRES_USER: str = "app"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "app"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = ""
    SQL_ECHO: bool = False

    # --- application ---
    SECRET_KEY: str = Field(min_length=32)
    TOTP_ENCRYPTION_KEY: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    FORTYTWO_CLIENT_ID: str = ""
    FORTYTWO_CLIENT_SECRET: str = ""
    ENVIRONMENT: Literal["dev", "prod"] = "dev"
    SERVER_NAME: str = "localhost"
    # Origin the browser sees, port included (https://localhost:8443 in dev).
    # Empty means https://<SERVER_NAME>, i.e. published on the default 443
    PUBLIC_URL: str = ""
    ALLOWED_ORIGINS: str = "https://localhost"
    ACCESS_TOKEN_TTL: int = 900
    REFRESH_TOKEN_TTL: int = 1_209_600
    MFA_TOKEN_TTL: int = 300

    # --- LLM grader ---
    # Off by default: without a reachable model every answer falls back to
    # self-assessment, so a fresh clone works with no GPU and no Tailscale key
    LLM_ENABLED: bool = False
    # Ollama's base URL. Through Tailscale it is the GPU machine's tailnet IP
    # (100.x.y.z): an IP needs no name resolution inside the userspace proxy,
    # and it is the address the tailnet policy grants access to
    LLM_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "gemma4:12b"
    # Empty means a direct connection; `http://tailscale:1055` sends the model
    # calls, and only them, through the Tailscale container's HTTP proxy
    LLM_PROXY_URL: str = ""
    # Seconds allowed between two reads from the model, generation included.
    # Connecting gets its own short timeout in the client, so a machine that is
    # switched off fails fast into the fallback instead of hanging a student
    LLM_TIMEOUT: float = 60.0
    # Model tokens (prompt + output) all students together may spend per sliding hour
    LLM_HOURLY_TOKEN_BUDGET: int = 200_000
    # Graded answers one student may send on one question per sliding 24 hours
    LLM_ATTEMPTS_PER_QUESTION: int = 3

    @property
    def public_url(self) -> str:
        """Origin used to build absolute URLs handed to third parties (OAuth)"""
        return (self.PUBLIC_URL or f"https://{self.SERVER_NAME}").rstrip("/")

    @property
    def database_url(self) -> str:
        """Builds the database URL from the POSTGRES_* settings

        The `postgresql+asyncpg://` prefix is mandatory: plain `postgresql://`
        selects psycopg2 instead and fails with a synchronous-driver error.

        `quote_plus` is applied to the user and the password because a `@`, a
        `/` or a `#` in the password would silently corrupt the URL, and the
        resulting error message would point nowhere near the real cause.
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if not self.POSTGRES_PASSWORD:
            raise RuntimeError(
                "Neither DATABASE_URL nor POSTGRES_PASSWORD is set. "
                "Set POSTGRES_PASSWORD (or POSTGRES_PASSWORD_FILE) in .env"
            )
        user = quote_plus(self.POSTGRES_USER)
        password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def safe_database_url(self) -> str:
        """Same URL with the password hidden

        The only form that may ever reach a log
        """
        url = self.database_url
        if "@" not in url:
            return url
        scheme, _, rest = url.partition("://")
        credentials, _, host = rest.partition("@")
        user = credentials.partition(":")[0]
        return f"{scheme}://{user}:***@{host}"

    @property
    def allowed_origins(self) -> set[str]:
        """Origins CORS will accept parsed from the comma separated setting"""
        return {o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()}

    @field_validator("TOTP_ENCRYPTION_KEY")
    @classmethod
    def _check_fernet_key(cls, v: str) -> str:
        """Refuses at startup a key Fernet would only reject at the first 2FA use"""
        if v:
            try:
                Fernet(v.encode())
            except ValueError as exc:
                raise ValueError(
                    "TOTP_ENCRYPTION_KEY must be a Fernet key (44 chars url-safe base64), not hex"
                ) from exc
        return v

    def assert_production_ready(self) -> None:
        """Refuses to start in production on an example configuration

        Catches a placeholder secret key or a missing encryption key
        before the app is exposed rather than after
        """
        if self.ENVIRONMENT != "prod":
            return
        problems: list[str] = []
        if len(self.SECRET_KEY) < 32:
            problems.append("SECRET_KEY < 32 chars")
        if not self.TOTP_ENCRYPTION_KEY:
            problems.append("TOTP_ENCRYPTION_KEY empty")
        if self.SERVER_NAME == "localhost":
            problems.append("SERVER_NAME is still localhost")
        if problems:
            raise RuntimeError("Configuration invalid: " + " ; ".join(problems))


@lru_cache
def get_settings() -> Settings:
    """env read once then used everywhere"""
    expand_file_secrets()
    return Settings()  # type: ignore[call-arg]
