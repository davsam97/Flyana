"""friendships_refresh_tokens

Revision ID: eee92670a8c1
Revises: cefb74bd94bc
Create Date: 2026-08-11 09:54:05.407453

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'eee92670a8c1'
down_revision: Union[str, Sequence[str], None] = 'cefb74bd94bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "friendships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("addressee_id", sa.Integer(), nullable=False),
        # native_enum=False + create_constraint=True: the CHECK ck_friendships_friendship_status
        # is emitted by CREATE TABLE itself, must not write it separately
        sa.Column(
            "status",
            sa.Enum("pending", "accepted", "blocked", name="friendship_status",
                    native_enum=False, create_constraint=True, length=32),
            server_default="pending", nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("requester_id <> addressee_id", name=op.f("ck_friendships_not_self")),
        sa.ForeignKeyConstraint(["addressee_id"], ["users.id"],
                                name=op.f("fk_friendships_addressee_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"],
                                name=op.f("fk_friendships_requester_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_friendships")),
    )
    # Normalise (a,b) and (b,a) to same key
    op.execute(
        "CREATE UNIQUE INDEX uq_friendships_canonical ON friendships "
        "(LEAST(requester_id, addressee_id), GREATEST(requester_id, addressee_id))"
    )
    op.create_index('ix_friendships_addressee_status', 'friendships',
                    ['addressee_id', 'status'], unique=False)
    op.create_table('refresh_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('family_id', sa.UUID(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('user_agent', sa.String(length=255), nullable=True),
    sa.Column('ip', sa.String(length=45), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_refresh_tokens_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_refresh_tokens')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_refresh_tokens_token_hash'))
    )
    op.create_index('ix_refresh_tokens_family_id', 'refresh_tokens', ['family_id'], unique=False)
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'], unique=False)
    # op.f() marks the name as final: without it the `ck` naming convention
    # (ck_%(table_name)s_%(constraint_name)s) is applied a second time here and the
    # constraint lands as ck_users_ck_users_role
    op.create_check_constraint(
    op.f("ck_users_role"), "users",
    "role IN ('guest', 'student', 'author', 'moderator', 'admin')",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_users_role"), "users", type_="check")
    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_family_id', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_index('ix_friendships_addressee_status', table_name='friendships')
    op.execute("DROP INDEX IF EXISTS uq_friendships_canonical")
    op.drop_table("friendships")
