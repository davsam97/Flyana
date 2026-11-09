"""persistent multiplayer matches

Revision ID: 4c7d9e2a1f30
Revises: a1c4e7b9d2f0
Create Date: 2026-09-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4c7d9e2a1f30"
down_revision: Union[str, Sequence[str], None] = "3c8bcf9cc83c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=12), nullable=False),
        sa.Column(
            "mode",
            sa.Enum(
                "solo", "duel", "arena",
                name="match_mode",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "lobby", "running", "finished", "aborted",
                name="match_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            server_default="lobby",
            nullable=False,
        ),
        sa.Column("max_players", sa.Integer(), nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_matches")),
        sa.UniqueConstraint("public_id", name=op.f("uq_matches_public_id")),
    )
    op.create_table(
        "match_players",
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("final_rank", sa.Integer(), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("match_id", "user_id", name=op.f("pk_match_players")),
    )
    op.create_table(
        "match_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_match_questions")),
        sa.UniqueConstraint("match_id", "position", name=op.f("uq_match_questions_match_id")),
    )
    op.create_table(
        "match_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("match_question_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("choice_id", sa.Integer(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("response_ms", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["match_question_id"], ["match_questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["choice_id"], ["choices.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_match_attempts")),
        sa.UniqueConstraint(
            "match_question_id", "user_id",
            name=op.f("uq_match_attempts_match_question_id"),
        ),
    )


def downgrade() -> None:
    op.drop_table("match_attempts")
    op.drop_table("match_questions")
    op.drop_table("match_players")
    op.drop_table("matches")
