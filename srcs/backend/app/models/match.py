"""Persistent records for realtime quiz matches."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import MatchMode, MatchStatus, enum_column


class Match(Base, TimestampMixin):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    mode: Mapped[MatchMode] = mapped_column(enum_column(MatchMode, "match_mode"))
    status: Mapped[MatchStatus] = mapped_column(
        enum_column(MatchStatus, "match_status"),
        server_default=MatchStatus.lobby.value,
        nullable=False,
    )
    max_players: Mapped[int] = mapped_column(Integer, nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class MatchPlayer(Base):
    __tablename__ = "match_players"

    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    score: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    final_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MatchQuestion(Base):
    __tablename__ = "match_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    choice_order: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), server_default="{}", nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("match_id", "position"),
    )


class MatchAttempt(Base):
    __tablename__ = "match_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    match_question_id: Mapped[int] = mapped_column(
        ForeignKey("match_questions.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    choice_id: Mapped[int | None] = mapped_column(
        ForeignKey("choices.id", ondelete="SET NULL"), nullable=True
    )
    is_correct: Mapped[bool] = mapped_column(nullable=False)
    response_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
