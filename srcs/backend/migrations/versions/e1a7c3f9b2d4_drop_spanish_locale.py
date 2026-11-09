"""drop the Spanish locale

Revision ID: e1a7c3f9b2d4
Revises: 9a4b1f6c3d85
Create Date: 2026-11-09 00:00:00.000000

Flyana is served in French and English only. Accounts set to Spanish move
to French, the default language of the interface. Spanish translations of
the old content stay in their tables: nothing reads them any more, and the
content they belong to is archived with the move to Flyana
"""
from typing import Sequence, Union

from alembic import op


revision: str = "e1a7c3f9b2d4"
down_revision: Union[str, Sequence[str], None] = "9a4b1f6c3d85"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE users SET locale = 'fr' WHERE locale = 'es'")


def downgrade() -> None:
    # Which accounts were Spanish is not kept: there is nothing to restore
    pass
