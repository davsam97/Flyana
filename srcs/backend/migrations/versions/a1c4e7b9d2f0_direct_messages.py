"""direct_messages

Revision ID: a1c4e7b9d2f0
Revises: bbd3c8683790
Create Date: 2026-09-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1c4e7b9d2f0"
down_revision: Union[str, Sequence[str], None] = "bbd3c8683790"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "direct_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("recipient_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.String(length=2000), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "sender_id <> recipient_id", name=op.f("ck_direct_messages_not_self")
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["users.id"],
            name=op.f("fk_direct_messages_sender_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recipient_id"],
            ["users.id"],
            name=op.f("fk_direct_messages_recipient_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_direct_messages")),
    )
    # Thread fetch: (a,b) and (b,a) normalised to one key, then time-ordered.
    # Must compile to exactly the text() in models/message.py or autogenerate
    # will propose dropping and recreating it forever.
    op.execute(
        "CREATE INDEX ix_direct_messages_conversation ON direct_messages "
        "(LEAST(sender_id, recipient_id), GREATEST(sender_id, recipient_id), created_at)"
    )
    op.create_index(
        "ix_direct_messages_recipient_read",
        "direct_messages",
        ["recipient_id", "read_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_direct_messages_recipient_read", table_name="direct_messages")
    op.execute("DROP INDEX IF EXISTS ix_direct_messages_conversation")
    op.drop_table("direct_messages")
