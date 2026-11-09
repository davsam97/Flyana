"""`friendships` table"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint, DateTime, ForeignKey, Index, func, text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import FriendshipStatus, enum_column


class Friendship(Base):
    """One link between two users

    Covers the request and the friendship since accepting only flips the status
    Stored once per pair whichever direction the request went
    """

    __tablename__ = "friendships"

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    addressee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[FriendshipStatus] = mapped_column(
        enum_column(FriendshipStatus, "friendship_status"),
        server_default=FriendshipStatus.pending.value,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        # Uniqueness of the *unordered* pair: subsumes a plain UniqueConstraint on
        # (requester_id, addressee_id) since it also rejects the reversed pair.
        # Declared here, not only in the migration: alembic reflects expression indexes
        # and proposes to drop anything it finds in the DB but not in the metadata.
        # The text() must compile to exactly what the migration emits, or autogenerate
        # will flip-flop between dropping and recreating it.
        Index(
            "uq_friendships_canonical",
            text("LEAST(requester_id, addressee_id)"),
            text("GREATEST(requester_id, addressee_id)"),
            unique=True,
        ),
        CheckConstraint("requester_id <> addressee_id", name="not_self"),
        Index("ix_friendships_addressee_status", "addressee_id", "status"), 
    )
