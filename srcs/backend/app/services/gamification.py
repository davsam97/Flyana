"""Gamification — XP and daily streak

`record_activity` is the single entry point: exercises and games call it,
never touch `xp` / `current_streak` directly
Days are counted in UTC, the same for every user
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import LearningPath, PathModule
from app.models.enums import QuestionStatus
from app.models.gamification import Achievement, UserAchievement
from app.models.learning import LessonRead, ModuleProgress
from app.models.user import User


@dataclass(frozen=True)
class CourseProgress:
    """Where a user stands in the course, for the flight-stage achievements"""

    lessons_read: int
    modules_passed: int
    modules_total: int


# code -> "has the user earned it?"
# Codes must match the rows seeded by the "seed achievements" migrations
ACHIEVEMENT_RULES: dict[str, Callable[[User, CourseProgress], bool]] = {
    "first_steps": lambda user, _: user.xp > 0,
    "level_5": lambda user, _: user.level >= 5,
    "level_10": lambda user, _: user.level >= 10,
    "streak_3": lambda user, _: user.current_streak >= 3,
    "streak_7": lambda user, _: user.current_streak >= 7,
    # The stages of a flight to orbit, along the course
    "liftoff": lambda _, course: course.lessons_read >= 1,
    "max_q": lambda _, course: course.modules_passed >= 1,
    "meco": lambda _, course: (
        course.modules_total > 0 and 2 * course.modules_passed >= course.modules_total
    ),
    "orbit": lambda _, course: (
        course.modules_total > 0 and course.modules_passed >= course.modules_total
    ),
}

XP_CORRECT_LLM = 50
XP_CORRECT_SELF = 20
XP_MATCH_PLAYED = 20
XP_MATCH_WON = 50
# Check quizzes: each question pays once, the first time it is answered right,
# and a module pays once, the first time it is passed
XP_CORRECT_QUIZ = 10
XP_MODULE_PASSED = 100

def utc_today() -> date:
    """Today's date in UTC"""
    return datetime.now(UTC).date()


def update_streak(user: User, today: date) -> None:
    """Counts `today` in the user's daily streak

    Same day: nothing, already counted
    Day after the last activity: +1
    Anything else (first activity, or a gap): starts over at 1
    """
    if user.last_activity_date == today - timedelta(days=1):
        user.last_activity_date = today
        user.current_streak = user.current_streak + 1
    elif user.last_activity_date == today:
        pass
    else:
        user.last_activity_date = today
        user.current_streak = 1



def effective_streak(user: User, today: date) -> int:
    """The streak to display

    `current_streak` is only written when the user acts: after a gap it still
    holds the old value, so reading it raw would show a dead streak
    """
    if user.last_activity_date == today or user.last_activity_date == today - timedelta(days=1):
        return user.current_streak
    return 0

async def course_progress(db: AsyncSession, user_id: int) -> CourseProgress:
    """Lessons read, modules passed, and modules in the published course paths"""
    lessons_read = await db.scalar(
        select(func.count()).select_from(LessonRead).where(LessonRead.user_id == user_id)
    )
    modules_passed = await db.scalar(
        select(func.count()).select_from(ModuleProgress).where(
            ModuleProgress.user_id == user_id, ModuleProgress.passed_at.is_not(None)
        )
    )
    modules_total = await db.scalar(
        select(func.count(func.distinct(PathModule.topic_id)))
        .join(LearningPath, LearningPath.id == PathModule.path_id)
        .where(LearningPath.status == QuestionStatus.published)
    )
    return CourseProgress(lessons_read or 0, modules_passed or 0, modules_total or 0)


async def check_achievements(db: AsyncSession, user: User) -> list[str]:
    """Grants every achievement the user now qualifies for

    Returns the codes newly granted, [] if none
    No commit: the caller commits
    """
    # a. codes the user already has
    result = await db.execute(
        select(Achievement.code)
        .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
        .where(UserAchievement.user_id == user.id)
    )
    owned = set(result.scalars().all())

    # b. earned now and not owned yet
    course = await course_progress(db, user.id)
    new_codes = [
        code
        for code, rule in ACHIEVEMENT_RULES.items()
        if code not in owned and rule(user, course)
    ]
    if not new_codes:
        return []

    # c. their ids
    achievements = (
        await db.scalars(select(Achievement).where(Achievement.code.in_(new_codes)))
    ).all()

    # d. grant them
    for achievement in achievements:
        db.add(UserAchievement(user_id=user.id, achievement_id=achievement.id))
    return [achievement.code for achievement in achievements]

async def record_activity(
    db: AsyncSession, user: User, xp_gained: int, today: date | None = None
) -> list[str]:
    """Credits XP, counts today in the streak, grants new achievements

    Returns the codes of the achievements unlocked by this activity
    No commit: the caller commits, so the answer and its XP land in the same
    transaction — or neither does
    """
    # Sessions keep objects as first loaded (`expire_on_commit=False`), and the
    # websocket's lives as long as the socket: `user` may hold an XP from long
    # ago. Reload the row, locked until the caller's commit, so two activities
    # at once add up instead of the last one overwriting the other
    await db.refresh(user, with_for_update=True)
    if today is None:
        today = utc_today()
    user.xp += xp_gained
    update_streak(user, today)
    return await check_achievements(db, user)

async def leaderboard(db: AsyncSession, limit: int) -> list[tuple[int, User]]:
    """The `limit` best active users by XP, each with their rank

    `RANK()`: equal XP share a rank and the next one skips (1, 1, 3)
    Users still at 0 XP stay out: they have not played yet
    """
    rank = func.rank().over(order_by=User.xp.desc()).label("rank")
    rows = await db.execute(
        select(rank, User)
        .where(User.is_active.is_(True), User.xp > 0)
        .order_by(User.xp.desc(), User.id)
        .limit(limit)
    )
    return [(r, user) for r, user in rows.tuples()]


async def rank_of(db: AsyncSession, user: User) -> int | None:
    """Where `user` stands on the leaderboard, None while still at 0 XP

    Same rule as `leaderboard`: one plus the number of users strictly ahead
    """
    if user.xp <= 0:
        return None
    ahead = await db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.is_active.is_(True), User.xp > user.xp)
    )
    return (ahead or 0) + 1
