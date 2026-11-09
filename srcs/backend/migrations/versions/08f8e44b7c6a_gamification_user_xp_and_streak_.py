"""gamification: user xp and streak, achievements

Revision ID: 08f8e44b7c6a
Revises: 5d1e8b3a7c42
Create Date: 2026-09-23 08:53:33.534509

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '08f8e44b7c6a'
down_revision: Union[str, Sequence[str], None] = '5d1e8b3a7c42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('achievements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=64), nullable=False),
    sa.Column('icon', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_achievements')),
    sa.UniqueConstraint('code', name=op.f('uq_achievements_code'))
    )
    op.create_table('user_achievements',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('achievement_id', sa.Integer(), nullable=False),
    sa.Column('earned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], name=op.f('fk_user_achievements_achievement_id_achievements'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_achievements_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'achievement_id', name=op.f('pk_user_achievements'))
    )
    op.add_column('users', sa.Column('xp', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('current_streak', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('last_activity_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_activity_date')
    op.drop_column('users', 'current_streak')
    op.drop_column('users', 'xp')
    op.drop_table('user_achievements')
    op.drop_table('achievements')
