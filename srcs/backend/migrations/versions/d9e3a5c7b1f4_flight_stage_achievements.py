"""flight-stage achievements

Revision ID: d9e3a5c7b1f4
Revises: c4f8b1e6d2a7
Create Date: 2026-11-09 00:00:00.000000

The course's badges, named after the stages of a flight to orbit: lift-off
(first lesson read), Max Q (first module passed), MECO (half the modules
passed) and orbit (every module passed)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d9e3a5c7b1f4"
down_revision: Union[str, Sequence[str], None] = "c4f8b1e6d2a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ACHIEVEMENT_CODES = ["liftoff", "max_q", "meco", "orbit"]

# Lightweight table: never import ORM models in a migration
achievements = sa.table("achievements", sa.column("code", sa.String))


def upgrade() -> None:
    op.bulk_insert(achievements, [{"code": code} for code in ACHIEVEMENT_CODES])


def downgrade() -> None:
    op.execute(achievements.delete().where(achievements.c.code.in_(ACHIEVEMENT_CODES)))
