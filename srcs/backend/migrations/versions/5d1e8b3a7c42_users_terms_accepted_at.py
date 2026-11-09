"""users.terms_accepted_at

Revision ID: 5d1e8b3a7c42
Revises: 4c7d9e2a1f30
Create Date: 2026-09-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5d1e8b3a7c42"
down_revision: Union[str, Sequence[str], None] = "4c7d9e2a1f30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "terms_accepted_at")
