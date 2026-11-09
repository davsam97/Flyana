"""question_translation_title

Revision ID: 7b3f2c9e5a10
Revises: c3f8a1d05e27
Create Date: 2026-09-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7b3f2c9e5a10"
down_revision: Union[str, Sequence[str], None] = "c3f8a1d05e27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "question_translations", sa.Column("title", sa.String(length=120), nullable=True)
    )
    # Translations loaded before titles existed get a stand-in cut from the stem,
    # so the column can become NOT NULL; the next content load writes the real title
    op.execute("UPDATE question_translations SET title = left(stem, 120) WHERE title IS NULL")
    op.alter_column(
        "question_translations", "title", existing_type=sa.String(length=120), nullable=False
    )


def downgrade() -> None:
    op.drop_column("question_translations", "title")
