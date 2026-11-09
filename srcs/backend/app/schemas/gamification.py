"""Gamification schemas"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AchievementOut(BaseModel):
    """One catalog achievement, and when the user unlocked it

    `earned_at` is None while still locked
    The label comes from the front's i18n, keyed by `code`
    """

    model_config = ConfigDict(from_attributes=True)

    code: str
    icon: str | None
    earned_at: datetime | None


class XpRewards(BaseModel):
    """XP paid for each kind of activity"""

    correct_llm: int
    correct_self: int
    match_played: int
    match_won: int
    quiz_correct: int
    module_passed: int


class GamificationRules(BaseModel):
    """How progression works, sent so the front never hardcodes the numbers"""

    xp_per_level: int
    xp: XpRewards


class UserStats(BaseModel):
    """Exercise counts shown on the dashboard"""

    solved: int
    to_review: int

class LeaderboardEntry(BaseModel):
    """One row of the leaderboard: public identity plus progression only"""

    rank: int
    id: int
    display_name: str
    avatar_path: str | None
    xp: int
    level: int


class Leaderboard(BaseModel):
    """The top of the board, and the caller's own row wherever it sits

    `me` is None while the caller is still at 0 XP
    """

    entries: list[LeaderboardEntry]
    me: LeaderboardEntry | None
