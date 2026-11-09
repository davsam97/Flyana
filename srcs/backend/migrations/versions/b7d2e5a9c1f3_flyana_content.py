"""Flyana content: lessons, numeric questions, sources, archived topics

Revision ID: b7d2e5a9c1f3
Revises: e1a7c3f9b2d4
Create Date: 2026-11-09 00:00:00.000000

Also retires the 42 exam content: its questions are archived and its topics
hidden. Nothing is deleted, past attempts and matches still point at them
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7d2e5a9c1f3"
down_revision: Union[str, Sequence[str], None] = "e1a7c3f9b2d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATUSES = ("draft", "in_review", "published", "archived", "rejected")
KINDS_BEFORE = ("single_choice", "multi_choice", "free_text")
KINDS_AFTER = (*KINDS_BEFORE, "numeric")


def _kind_check(kinds: tuple[str, ...]) -> str:
    return "kind IN (" + ", ".join(f"'{kind}'" for kind in kinds) + ")"


def upgrade() -> None:
    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=96), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                *STATUSES, name="lesson_status", native_enum=False,
                create_constraint=True, length=32,
            ),
            server_default="published",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"], ["topics.id"],
            name=op.f("fk_lessons_topic_id_topics"), ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lessons")),
        sa.UniqueConstraint("slug", name=op.f("uq_lessons_slug")),
    )
    op.create_index("ix_lessons_topic_position", "lessons", ["topic_id", "position"])
    op.create_table(
        "lesson_translations",
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("locale", sa.String(length=5), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["lesson_id"], ["lessons.id"],
            name=op.f("fk_lesson_translations_lesson_id_lessons"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("lesson_id", "locale", name=op.f("pk_lesson_translations")),
    )

    op.add_column("questions", sa.Column("numeric_answer", sa.Numeric(), nullable=True))
    op.add_column(
        "questions", sa.Column("tolerance_rel", sa.Numeric(precision=6, scale=4), nullable=True)
    )
    op.add_column("questions", sa.Column("unit", sa.String(length=32), nullable=True))
    op.add_column("questions", sa.Column("source_label", sa.Text(), nullable=True))
    op.add_column("questions", sa.Column("source_url", sa.Text(), nullable=True))

    # Autogenerate never sees a CHECK change (see `enums.py`): rewritten by hand
    op.drop_constraint(op.f("ck_questions_question_kind"), "questions", type_="check")
    op.create_check_constraint("question_kind", "questions", _kind_check(KINDS_AFTER))
    op.create_check_constraint(
        "numeric_key",
        "questions",
        "(kind = 'numeric') = (numeric_answer IS NOT NULL AND tolerance_rel IS NOT NULL)",
    )

    op.add_column(
        "topics", sa.Column("archived", sa.Boolean(), server_default="false", nullable=False)
    )

    # The 42 exam content gives way to Flyana's
    op.execute("UPDATE topics SET archived = true WHERE slug LIKE 'exam-rank-%'")
    op.execute(
        "UPDATE questions SET status = 'archived' "
        "WHERE topic_id IN (SELECT id FROM topics WHERE slug LIKE 'exam-rank-%')"
    )


def downgrade() -> None:
    # The exam questions stay archived: which ones were published before is not kept
    op.drop_column("topics", "archived")
    op.execute("DELETE FROM questions WHERE kind = 'numeric'")
    op.drop_constraint(op.f("ck_questions_numeric_key"), "questions", type_="check")
    op.drop_constraint(op.f("ck_questions_question_kind"), "questions", type_="check")
    op.create_check_constraint("question_kind", "questions", _kind_check(KINDS_BEFORE))
    op.drop_column("questions", "source_url")
    op.drop_column("questions", "source_label")
    op.drop_column("questions", "unit")
    op.drop_column("questions", "tolerance_rel")
    op.drop_column("questions", "numeric_answer")
    op.drop_table("lesson_translations")
    op.drop_index("ix_lessons_topic_position", table_name="lessons")
    op.drop_table("lessons")
