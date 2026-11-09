"""seed achievements

Revision ID: d40c2a46ca20
Revises: 08f8e44b7c6a
Create Date: 2026-09-28 19:37:39.425054

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd40c2a46ca20'
down_revision: Union[str, Sequence[str], None] = '08f8e44b7c6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ACHIEVEMENT_CODES = ["first_steps", "level_5", "level_10", "streak_3", "streak_7"]

# Lightweight table: never import ORM models in a migration,
# they follow the current code, not the schema at this revision
achievements = sa.table(
    "achievements",
    sa.column("code", sa.String),
)

def upgrade() -> None:
    """Seed the achievement catalog."""
    op.bulk_insert(achievements, [{"code": code} for code in ACHIEVEMENT_CODES])


def downgrade() -> None:
    """Remove the seeded achievements."""
    op.execute(
        achievements.delete().where(achievements.c.code.in_(ACHIEVEMENT_CODES))
    )
