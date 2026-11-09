"""Question request/response schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import QuestionKind, QuestionStatus


class QuestionOut(BaseModel):
    """One question in a list, as a student may see it before answering

    Built field by field by the search service, never from a whole row: the
    `questions` row also holds `key_points`, the answer key, so only what is
    listed here can ever reach a client
    `title` and `stem` are in the requested language, English when that one is
    missing, and `is_fallback` says which
    """

    id: int
    slug: str
    title: str | None
    topic_id: int
    kind: QuestionKind
    status: QuestionStatus
    difficulty_rating: Decimal
    stem: str | None
    is_fallback: bool
    tags: list[str]
    times_asked: int
    times_correct: int
    created_at: datetime
    updated_at: datetime


class QuestionDetail(BaseModel):
    """One question as a student may see it before answering

    The wording in the negotiated language, English when that one is missing
    Deliberately no `key_points` and no `explanation`: the first is the answer key
    and the second gives the answer away, so either would let a student read the
    solution before writing a word
    """

    id: int
    slug: str
    title: str | None
    topic_id: int
    kind: QuestionKind
    status: QuestionStatus
    difficulty_rating: Decimal
    stem: str | None
    is_fallback: bool
