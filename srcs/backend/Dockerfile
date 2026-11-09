FROM docker.io/library/python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM docker.io/library/python:3.14-slim AS runtime

# Overridden with the host uid so the media volume and bind mounts stay writable
ARG UID=1000
ARG GID=1000

RUN set -eux; \
    getent group  "$GID" >/dev/null || groupadd --gid "$GID" app; \
    getent passwd "$UID" >/dev/null || useradd --uid "$UID" --gid "$GID" \
                                               --home-dir /app --no-create-home app; \
    mkdir -p /srv/media/avatars; \
    chown -R "$UID:$GID" /srv/media

WORKDIR /app
COPY --from=builder --chown=$UID:$GID /app/.venv /app/.venv
COPY --chown=$UID:$GID . .
RUN chmod +x entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

USER $UID:$GID

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health').status == 200 else 1)"

CMD ["./entrypoint.sh"]
