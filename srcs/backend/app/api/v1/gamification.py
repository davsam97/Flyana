"""Gamification rules, public: the same for every user

And the XP leaderboard, for signed-in users only
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.deps import CurrentUser, DbSession
from app.models.user import XP_PER_LEVEL, User
from app.schemas.gamification import (
    GamificationRules,
    Leaderboard,
    LeaderboardEntry,
    XpRewards,
)
from app.services.gamification import (
    XP_CORRECT_LLM,
    XP_CORRECT_QUIZ,
    XP_CORRECT_SELF,
    XP_MATCH_PLAYED,
    XP_MATCH_WON,
    XP_MODULE_PASSED,
    leaderboard,
    rank_of,
)

router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.get("/rules", response_model=GamificationRules)
async def rules() -> GamificationRules:
    return GamificationRules(
        xp_per_level=XP_PER_LEVEL,
        xp=XpRewards(
            correct_llm=XP_CORRECT_LLM,
            correct_self=XP_CORRECT_SELF,
            match_played=XP_MATCH_PLAYED,
            match_won=XP_MATCH_WON,
            quiz_correct=XP_CORRECT_QUIZ,
            module_passed=XP_MODULE_PASSED,
        ),
    )


def _entry(rank: int, user: User) -> LeaderboardEntry:
    return LeaderboardEntry(
        rank=rank,
        id=user.id,
        display_name=user.display_name,
        avatar_path=user.avatar_path,
        xp=user.xp,
        level=user.level,
    )


@router.get("/leaderboard", response_model=Leaderboard)
async def get_leaderboard(
    user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=50, ge=1, le=100),
) -> Leaderboard:
    entries = [_entry(rank, u) for rank, u in await leaderboard(db, limit)]
    my_rank = await rank_of(db, user)
    return Leaderboard(
        entries=entries,
        me=_entry(my_rank, user) if my_rank is not None else None,
    )
