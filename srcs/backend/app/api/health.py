from __future__ import annotations

import logging
from typing import Literal

from app.deps import DbSession
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


class Health(BaseModel):
    """What the health check reports"""

    status: Literal["ok", "degraded"]
    database: bool


@router.get("/health", response_model=Health)
async def health(db: DbSession) -> JSONResponse:
    """Says whether the api is up and can still reach the database"""
    try:
        await db.execute(text("SELECT 1"))
        database_ok = True
    except Exception:  # noqa: BLE001 is ok, catch everything
        logger.exception("healthcheck : cannot reach db")
        database_ok = False

    body = Health(status="ok" if database_ok else "degraded", database=database_ok)
    return JSONResponse(
        status_code=status.HTTP_200_OK if database_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=body.model_dump(),
    )
