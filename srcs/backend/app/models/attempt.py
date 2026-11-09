"""Table `attempts`"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import AttemptSource, GraderKind, enum_column


class Attempt(Base):
    """One answer to a question by a student

    `is_correct` is NULL only while a self-assessment is pending.
    `grader_confidence` stays NULL: every benchmarked model reported 1.0
    whatever the answer.
    """

    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    selected_choice_ids: Mapped[list[int] | None] = mapped_column(
        ARRAY(Integer), nullable=True
    )
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    response_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[AttemptSource] = mapped_column(
        enum_column(AttemptSource, "attempt_source"),
        server_default=AttemptSource.practice.value,
        nullable=False,
    )
    locale: Mapped[str] = mapped_column(String(5), nullable=False)
    grader: Mapped[GraderKind] = mapped_column(
        enum_column(GraderKind, "grader_kind"),
        server_default=GraderKind.deterministic.value,
        nullable=False,
    )
    grader_meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    grader_confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 3), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_attempts_user_question_created", "user_id", "question_id", "created_at"),
    )
