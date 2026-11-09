"""`direct_messages` table — the one-to-one chat

One row per message. A conversation is not a stored entity: it is every row
where the two user ids match, ordered by `created_at`. That keeps writes to a
single INSERT and needs no "conversation" bookkeeping to stay consistent.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DirectMessage(Base):
    """A single message from one user to another"""

    __tablename__ = "direct_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # 2000 chars: long enough for a paragraph, short enough that a single
    # message can never be an upload channel. Enforced again in the schema.
    body: Mapped[str] = mapped_column(String(2000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        CheckConstraint("sender_id <> recipient_id", name="not_self"),
        # Thread fetch: every message between an unordered pair, newest first.
        # Same LEAST/GREATEST trick as friendships so (a,b) and (b,a) share a key.
        # The text() must compile to exactly what the migration emits or alembic
        # autogenerate flip-flops between dropping and recreating it.
        Index(
            "ix_direct_messages_conversation",
            text("LEAST(sender_id, recipient_id)"),
            text("GREATEST(sender_id, recipient_id)"),
            "created_at",
        ),
        # Unread badge and "mark thread read": both filter on this pair.
        Index("ix_direct_messages_recipient_read", "recipient_id", "read_at"),
    )
