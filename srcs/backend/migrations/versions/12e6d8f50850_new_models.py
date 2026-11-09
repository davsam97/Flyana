"""[new models]

Revision ID: 12e6d8f50850
Revises:
Create Date: 2026-08-10 12:15:43.353419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '12e6d8f50850'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', postgresql.CITEXT(), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=True),
    sa.Column('display_name', postgresql.CITEXT(), nullable=False),
    sa.Column('avatar_path', sa.String(length=255), nullable=True),
    sa.Column('bio', sa.String(length=500), nullable=True),
    sa.Column('locale', sa.String(length=5), server_default='en', nullable=False),
    sa.Column('role', sa.Enum('guest', 'student', 'author', 'moderator', 'admin', name='role', native_enum=False, create_constraint=True, length=32), server_default='student', nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('totp_secret_enc', sa.String(length=255), nullable=True),
    sa.Column('totp_enabled', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('display_name', name=op.f('uq_users_display_name')),
    sa.UniqueConstraint('email', name=op.f('uq_users_email'))
    )


def downgrade() -> None:
    op.drop_table('users')
