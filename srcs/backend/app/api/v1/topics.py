"""Topics: the exam hierarchy, read only"""

from __future__ import annotations

from fastapi import APIRouter

from app.deps import DbSession, Locale
from app.schemas.topic import TopicOut
from app.services.content import topic_tree

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=list[TopicOut])
async def list_topics(db: DbSession, locale: Locale):
    """Returns the whole topic hierarchy in the caller's language"""
    return await topic_tree(db, locale)
