"""users_role_check

Revision ID: cefb74bd94bc
Revises: 12e6d8f50850
Create Date: 2026-08-10 19:18:37.776014

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'cefb74bd94bc'
down_revision: Union[str, Sequence[str], None] = '12e6d8f50850'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(op.f('ck_users_role'), 'users', type_='check')


def downgrade() -> None:
    op.create_check_constraint(op.f('ck_users_role'), 'users', "role::text = ANY (ARRAY['guest'::character varying, 'student'::character varying, 'author'::character varying, 'moderator'::character varying, 'admin'::character varying]::text[])")
