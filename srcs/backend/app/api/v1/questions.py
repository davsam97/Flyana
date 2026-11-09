"""Questions: the public read side, search and detail"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.deps import DbSession, Locale, OptionalUser
from app.i18n import translated_questions
from app.models.content import Question
from app.models.enums import QuestionStatus, Role
from app.schemas.question import QuestionDetail
from app.schemas.search import QuestionFilters, QuestionPage
from app.services.search import search_questions

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("", response_model=QuestionPage)
async def list_questions(
    filters: Annotated[QuestionFilters, Query()],
    user: OptionalUser,
    db: DbSession,
    locale: Locale,
):
    """Searches filters sorts and paginates questions"""
    return await search_questions(db, filters, user, filters.locale or locale)


@router.get("/{question_id}", response_model=QuestionDetail)
async def get_question(
    question_id: int, user: OptionalUser, db: DbSession, locale: Locale
):
    """Returns one question in the caller's language"""
    row = (await db.execute(
        translated_questions(locale)
        .add_columns(
            Question.slug, Question.topic_id, Question.kind,
            Question.status, Question.difficulty_rating,
        )
        .where(Question.id == question_id)
    )).one_or_none()
    if row is None:
        raise HTTPException(404, detail="not found")

    is_moderator = user is not None and user.role >= Role.moderator
    if row.status != QuestionStatus.published and not is_moderator:
        raise HTTPException(404, detail="not found")

    return QuestionDetail(
        id=row.id,
        slug=row.slug,
        title=row.title,
        topic_id=row.topic_id,
        kind=row.kind,
        status=row.status,
        difficulty_rating=row.difficulty_rating,
        stem=row.stem,
        is_fallback=row.is_fallback,
    )
