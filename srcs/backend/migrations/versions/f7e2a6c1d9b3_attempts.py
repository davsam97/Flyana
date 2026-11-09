"""attempts

Revision ID: f7e2a6c1d9b3
Revises: 7b3f2c9e5a10
Create Date: 2026-09-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f7e2a6c1d9b3"
down_revision: Union[str, Sequence[str], None] = "7b3f2c9e5a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("selected_choice_ids", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column("raw_response", sa.Text(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("response_ms", sa.Integer(), nullable=True),
        sa.Column(
            "source",
            sa.Enum(
                "practice", "review", "duel", "arena", "daily",
                name="attempt_source",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            server_default="practice",
            nullable=False,
        ),
        sa.Column("locale", sa.String(length=5), nullable=False),
        sa.Column(
            "grader",
            sa.Enum(
                "deterministic", "llm", "self_assessed",
                name="grader_kind",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            server_default="deterministic",
            nullable=False,
        ),
        sa.Column("grader_meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("grader_confidence", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
            name=op.f("fk_attempts_question_id_questions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_attempts_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_attempts")),
    )
    op.create_index(
        "ix_attempts_user_question_created",
        "attempts",
        ["user_id", "question_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_attempts_user_question_created", table_name="attempts")
    op.drop_table("attempts")
