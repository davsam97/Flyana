"""Content: entities and their translation tables, defined side by side"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, CheckConstraint, Computed, DateTime, ForeignKey, Index, Integer, Numeric,
    String, Text, func
)
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import PathLevel, QuestionKind, QuestionStatus, enum_column


class Topic(Base):
    """One subject questions are filed under"""

    __tablename__ = "topics"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), nullable=True
    )
    position: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # A retired topic stays in the table, its questions still referenced by
    # past attempts and matches, but no listing shows it any more
    archived: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)


class TopicTranslation(Base):
    """The name of a topic in one language"""

    __tablename__ = "topic_translations"
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )
    locale: Mapped[str] = mapped_column(String(5), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class LearningPath(Base):
    """An ordered course through several topics"""

    __tablename__ = "learning_paths"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    level: Mapped[PathLevel] = mapped_column(enum_column(PathLevel, "path_level"))
    status: Mapped[QuestionStatus] = mapped_column(enum_column(QuestionStatus, "path_status"))
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class LearningPathTranslation(Base):
    """The title of a learning path in one language"""

    __tablename__ = "learning_path_translations"
    path_id: Mapped[int] = mapped_column(
        ForeignKey("learning_paths.id", ondelete="CASCADE"), primary_key=True
    )
    locale: Mapped[str] = mapped_column(String(5), primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class PathModule(Base):
    """One step of a learning path"""

    __tablename__ = "path_modules"
    id: Mapped[int] = mapped_column(primary_key=True)
    path_id: Mapped[int] = mapped_column(ForeignKey("learning_paths.id", ondelete="CASCADE"))
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    min_questions: Mapped[int] = mapped_column(Integer, server_default="5", nullable=False)


class Question(Base):
    """One question"""

    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    # Natural key: the stable identity of a question across reloads of the
    # versioned content files in `seeds/content/`, which own every question
    slug: Mapped[str] = mapped_column(String(96), unique=True, nullable=False)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="RESTRICT"))
    kind: Mapped[QuestionKind] = mapped_column(enum_column(QuestionKind, "question_kind"))
    # What a good answer must contain, one point per item, and one grid per
    # question whatever the student's language, so every student is graded on
    # the same criteria. The LLM grades a free_text answer against these: this
    # is the answer key and must never reach a student before they answer
    key_points: Mapped[list[str]] = mapped_column(
        ARRAY(Text), server_default="{}", nullable=False
    )
    # The answer key of a `numeric` question, NULL for every other kind: the
    # value in `unit`, accepted within `tolerance_rel` of it (0.02 is ±2 %).
    # Like `key_points`, it must never reach a student before they answer
    numeric_answer: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    tolerance_rel: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # Where the right answer can be checked. Shown with the correction only
    source_label: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty_rating: Mapped[Decimal] = mapped_column(
        Numeric(7, 2), server_default="1200", nullable=False
    )
    status: Mapped[QuestionStatus] = mapped_column(
        enum_column(QuestionStatus, "question_status"),
        server_default=QuestionStatus.draft.value,
        nullable=False,
    )
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    times_asked: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    times_correct: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_questions_status_topic_difficulty", "status", "topic_id", "difficulty_rating"),
        # Named by the `ck` convention of `base.py`: lands as `ck_questions_numeric_key`
        CheckConstraint(
            "(kind = 'numeric') = (numeric_answer IS NOT NULL AND tolerance_rel IS NOT NULL)",
            name="numeric_key",
        ),
    )


class Lesson(Base):
    """One page of a module's course, its text in `lesson_translations`

    Owned by the content files like questions, so retired by archiving
    """

    __tablename__ = "lessons"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(96), unique=True, nullable=False)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="RESTRICT"))
    position: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    status: Mapped[QuestionStatus] = mapped_column(
        enum_column(QuestionStatus, "lesson_status"),
        server_default=QuestionStatus.published.value,
        nullable=False,
    )

    __table_args__ = (Index("ix_lessons_topic_position", "topic_id", "position"),)


class LessonTranslation(Base):
    """The title and Markdown body of a lesson in one language"""

    __tablename__ = "lesson_translations"
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True
    )
    locale: Mapped[str] = mapped_column(String(5), primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)


class QuestionTranslation(Base):
    """The wording of a question in one language

    `search_vector` is maintained by PostgreSQL and must never be assigned
    """

    __tablename__ = "question_translations"
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True
    )
    locale: Mapped[str] = mapped_column(String(5), primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # GENERATED column: PostgreSQL recomputes it on every write, never assign to it
    # WARNING: `to_tsvector('simple', ...)` the TWO-argument form
    # The one-argument form is not IMMUTABLE (depends on the session setting
    # `default_text_search_config`), PostgreSQL then rejects the
    # generated column with "generation expression is not immutable".
    #
    # 'simple' rather than 'english': no stemming, so a single code path covers en/fr/es
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('simple', coalesce(stem, ''))", persisted=True),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_qt_search", "search_vector", postgresql_using="gin"),
        # Trigrams: typo-tolerant search
        # Requires the pg_trgm extension
        Index(
            "ix_qt_stem_trgm", "stem",
            postgresql_using="gin", postgresql_ops={"stem": "gin_trgm_ops"},
        ),
    )


class Choice(Base):
    """One possible answer"""

    __tablename__ = "choices"
    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)


class ChoiceTranslation(Base):
    """The text of a choice in one language"""

    __tablename__ = "choice_translations"
    choice_id: Mapped[int] = mapped_column(
        ForeignKey("choices.id", ondelete="CASCADE"), primary_key=True
    )
    locale: Mapped[str] = mapped_column(String(5), primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)


class Tag(Base):
    """A free label for cutting across topics"""

    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)


class QuestionTag(Base):
    """Links a question to a tag"""

    __tablename__ = "question_tags"
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
