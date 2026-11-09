"""Table `users`"""

from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import Boolean, DateTime, String, Integer, Date
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column

from typing import Literal
from pydantic import BaseModel, Field, field_validator

from app.models.base import Base, TimestampMixin
from app.models.enums import Role, enum_column
from app.schemas.user import DISPLAY_NAME_RE

XP_PER_LEVEL = 1000

class User(Base, TimestampMixin):
    """One account"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)

    # NULL = OAuth
    # for login `password_hash IS NULL` must be a failure, not a server error
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    display_name: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)

    avatar_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    locale: Mapped[str] = mapped_column(String(5), server_default="en", nullable=False)

    role: Mapped[Role] = mapped_column(
        enum_column(Role, "role"),
        server_default=Role.student.value,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default="true", nullable=False
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    totp_secret_enc: Mapped[str | None] = mapped_column(String(255), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )

    # NULL = account created before the terms existed
    # OAuth signups accept them implicitly (notice under the provider buttons)
    terms_accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    xp: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)

    current_streak: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)

    last_activity_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    @property
    def has_password(self) -> bool:
        return self.password_hash is not None

    @property
    def level(self) -> int:
        return self.xp // XP_PER_LEVEL + 1

    @property
    def xp_max(self) -> int:
        return XP_PER_LEVEL

    @property
    def level_xp(self) -> int:
        """XP earned inside the current level, what the progress bar shows"""
        return self.xp % XP_PER_LEVEL

    @property
    def streak(self) -> int:
        """The streak to display: `current_streak` goes stale after a missed day"""
        # Imported here: services.gamification imports this module
        from app.services.gamification import effective_streak, utc_today

        return effective_streak(self, utc_today())