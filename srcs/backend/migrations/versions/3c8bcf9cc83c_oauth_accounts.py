"""oauth_accounts

Revision ID: 3c8bcf9cc83c
Revises: 1b222c630292
Create Date: 2026-09-15 15:10:13.659398

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '3c8bcf9cc83c'
down_revision: Union[str, Sequence[str], None] = 'f7e2a6c1d9b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('oauth_accounts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('provider', sa.Enum('google', 'fortytwo', 'github', name='oauth_provider', native_enum=False, create_constraint=True, length=32), nullable=False),
    sa.Column('provider_account_id', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_oauth_accounts_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_oauth_accounts')),
    sa.UniqueConstraint('provider', 'provider_account_id', name='uq_oauth_accounts_provider_provider_account_id')
    )
    op.create_index('ix_oauth_accounts_user_id', 'oauth_accounts', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_oauth_accounts_user_id', table_name='oauth_accounts')
    op.drop_table('oauth_accounts')
