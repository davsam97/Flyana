"""Learning progress: adaptive ratings, check quizzes, module results, lessons read"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserTopicRating(Base):
    """A student's Elo rating in one module, which steers the questions they get

    Played against `questions.difficulty_rating`: both move after every
    answer given in a check quiz
    """

    __tablename__ = "user_topic_ratings"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )
    rating: Mapped[Decimal] = mapped_column(Numeric(7, 2), server_default="1000", nullable=False)
    answers: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class QuizRun(Base):
    """One check quiz on a module, served one question at a time

    The server picks each question when the previous one is answered, so the
    student only ever answers `current_question_id`: the correction shown after
    each answer cannot be replayed against the same question in the same run
    """

    __tablename__ = "quiz_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    question_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # Every question served so far, in order, the current one last
    served_ids: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), server_default="{}", nullable=False
    )
    current_question_id: Mapped[int | None] = mapped_column(
        ForeignKey("questions.id", ondelete="SET NULL"), nullable=True
    )
    answered: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    correct: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    # NULL while running; set when the last answer lands or the run is abandoned
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_quiz_runs_user_topic", "user_id", "topic_id"),)


class ModuleProgress(Base):
    """A student's best check quiz on a module, and when they first passed it"""

    __tablename__ = "module_progress"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )
    # Share of right answers in the best finished quiz, from 0 to 1
    best_score: Mapped[Decimal] = mapped_column(Numeric(4, 3), server_default="0", nullable=False)
    quizzes: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    passed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LessonRead(Base):
    """A lesson a student has read to the end"""

    __tablename__ = "lesson_reads"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True
    )
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
