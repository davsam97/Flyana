"""Gamification — XP, streaks and achievements"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class Achievement(Base):
    """One achievement a user can unlock

    A fixed, small catalog — labels live in the front's i18n, not here
    """

    __tablename__ = "achievements"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)

class UserAchievement(Base):
    """One unlocked achievement for one user"""

    __tablename__ = "user_achievements"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id", ondelete="CASCADE"), primary_key=True)
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)