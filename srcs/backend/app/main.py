"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

import asyncio

from app.api import health, ws
from app.api.v1 import attempts, auth, chat, matches, users, friends, questions, topics, gamification, learning
from app.config import get_settings
from app.db import engine
from app.middleware.csrf import CSRFMiddleware
from app.services.ratelimit import (
    grading_limiter,
    login_limiter,
    message_limiter,
    register_limiter,
    totp_limiter,
)

logger = logging.getLogger(__name__)
settings = get_settings()


async def _prune_limiters() -> None:
    """Sweeps stale rate limit entries every 10 minutes

    The buckets live in memory so without this they grow one key per IP forever
    """
    while True:
        await asyncio.sleep(600)
        for limiter in (login_limiter, register_limiter, totp_limiter, message_limiter, grading_limiter):
            limiter.prune()

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    """Runs the startup and shutdown steps around the app"""
    settings.assert_production_ready()
    # safe_database_url masks the password, never log `database_url` directly
    logger.info("api starting, db=%s", settings.safe_database_url)
    task = asyncio.create_task(_prune_limiters())
    yield
    task.cancel()
    await engine.dispose()


OPENAPI_URL = "/api/openapi.json"

app = FastAPI(
    title="flyana api",
    version="0.1.0",
    lifespan=lifespan,
    # served manually below with vendored assets, so the strict CSP
    # (script-src/style-src 'self') doesn't block the default CDN-hosted UI
    docs_url=None,
    openapi_url=OPENAPI_URL,
)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/api/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/api/docs", include_in_schema=False)
async def swagger_ui() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url=OPENAPI_URL,
        title=f"{app.title} - Swagger UI",
        swagger_js_url="/api/static/swagger-ui/swagger-ui-bundle.js",
        swagger_css_url="/api/static/swagger-ui/swagger-ui.css",
        swagger_favicon_url="/api/static/swagger-ui/favicon-32x32.png",
    )


app.add_middleware(CSRFMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(settings.allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(friends.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(questions.router, prefix="/api/v1")
app.include_router(attempts.router, prefix="/api/v1")
app.include_router(topics.router, prefix="/api/v1")
app.include_router(matches.router, prefix="/api/v1")
app.include_router(ws.router, prefix="/api")
app.include_router(gamification.router, prefix="/api/v1")
app.include_router(learning.router, prefix="/api/v1")