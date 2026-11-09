"""backup_codes

Revision ID: bbd3c8683790
Revises: eee92670a8c1
Create Date: 2026-08-12 14:03:16.989987

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'bbd3c8683790'
down_revision: Union[str, Sequence[str], None] = '1b222c630292'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('backup_codes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('code_hash', sa.String(length=255), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_backup_codes_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_backup_codes'))
    )
    op.create_index('ix_backup_codes_user_id', 'backup_codes', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_backup_codes_user_id', table_name='backup_codes')
    op.drop_table('backup_codes')
