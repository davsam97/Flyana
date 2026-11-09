"""question_slug_and_key_points

Revision ID: c3f8a1d05e27
Revises: a1c4e7b9d2f0
Create Date: 2026-09-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c3f8a1d05e27"
down_revision: Union[str, Sequence[str], None] = "a1c4e7b9d2f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("slug", sa.String(length=96), nullable=True))
    # Rows created before this migration have no slug: give each a unique one
    # derived from its id, so the column can become NOT NULL on any database
    op.execute("UPDATE questions SET slug = 'question-' || id WHERE slug IS NULL")
    op.alter_column(
        "questions", "slug", existing_type=sa.String(length=96), nullable=False
    )
    op.create_unique_constraint(op.f("uq_questions_slug"), "questions", ["slug"])
    op.add_column(
        "questions",
        sa.Column("key_points", postgresql.ARRAY(sa.Text()), server_default="{}", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("questions", "key_points")
    op.drop_constraint(op.f("uq_questions_slug"), "questions", type_="unique")
    op.drop_column("questions", "slug")
