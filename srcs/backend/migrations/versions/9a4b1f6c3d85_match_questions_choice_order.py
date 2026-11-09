"""match_questions.choice_order

Revision ID: 9a4b1f6c3d85
Revises: d40c2a46ca20
Create Date: 2026-10-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "9a4b1f6c3d85"
down_revision: Union[str, Sequence[str], None] = "d40c2a46ca20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rounds already played keep an empty array: their slot order was never
    # recorded, and the recap falls back on `choices.position` for those
    op.add_column(
        "match_questions",
        sa.Column(
            "choice_order",
            postgresql.ARRAY(sa.Integer()),
            server_default="{}",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("match_questions", "choice_order")
