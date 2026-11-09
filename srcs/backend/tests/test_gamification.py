"""Gamification — daily streak rules (pure) and achievements (database)"""

from datetime import UTC, date, datetime, timedelta

import uuid

import pytest

from sqlalchemy import select, text

from app.models.attempt import Attempt
from app.models.content import LearningPath, PathModule, Question, Topic
from app.models.enums import PathLevel, QuestionKind, QuestionStatus

from app.models.gamification import Achievement, UserAchievement
from app.models.learning import ModuleProgress
from app.models.user import User
from app.services.gamification import (
    ACHIEVEMENT_RULES,
    CourseProgress,
    check_achievements,
    course_progress,
    effective_streak,
    record_activity,
    update_streak,
    utc_today,
)

from app.services.match_persistence import add_player, create_match, finish_match

TODAY = date(2026, 9, 28)
YESTERDAY = TODAY - timedelta(days=1)


def make_user(streak: int, last: date | None) -> User:
    return User(xp=0, current_streak=streak, last_activity_date=last)


def test_first_activity_starts_at_one() -> None:
    user = make_user(0, None)
    update_streak(user, TODAY)
    assert user.current_streak == 1
    assert user.last_activity_date == TODAY

def test_same_day_changes_nothing() -> None:
    user = make_user(3, date(2026, 9, 28))
    update_streak(user, TODAY)
    assert user.current_streak == 3
    assert user.last_activity_date == TODAY

def test_next_day_increments() -> None:
    user = make_user(3, YESTERDAY)
    update_streak(user, TODAY)
    assert user.current_streak == 4
    assert user.last_activity_date == TODAY

def test_gap_resets() -> None:
    user = make_user(3, TODAY - timedelta(days=3))
    update_streak(user, TODAY)
    assert user.current_streak == 1
    assert user.last_activity_date == TODAY

def test_effective_streak_alive() -> None:
    user = make_user(4, YESTERDAY)
    assert effective_streak(user, TODAY) == 4

def test_effective_streak_broken() -> None:
    user = make_user(4, TODAY - timedelta(days=2))
    assert effective_streak(user, TODAY) == 0

# --- achievements: these need the database ---


async def test_nothing_earned(db, user_factory) -> None:
    user, _ = await user_factory()
    assert await check_achievements(db, user) == []


async def test_xp_grants_levels(db, user_factory) -> None:
    user, _ = await user_factory(xp=5000)
    assert set(await check_achievements(db, user)) == {"first_steps", "level_5"}


async def test_never_granted_twice(db, user_factory) -> None:
    user, _ = await user_factory(xp=5000)
    await check_achievements(db, user)
    assert await check_achievements(db, user) == []


async def test_record_activity_grants_first_steps(db, user_factory) -> None:
    user, _ = await user_factory()
    assert await record_activity(db, user, 10, today=TODAY) == ["first_steps"]

    result = await db.execute(
        select(Achievement.code)
        .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
        .where(UserAchievement.user_id == user.id)
    )
    assert result.scalars().all() == ["first_steps"]


async def test_record_activity_grants_streak(db, user_factory) -> None:
    user, _ = await user_factory(xp=10, current_streak=2, last_activity_date=YESTERDAY)
    assert set(await record_activity(db, user, 10, today=TODAY)) == {"first_steps", "streak_3"}

async def test_my_achievements_route(client, as_user, db) -> None:
    user = await as_user(xp=10)
    await check_achievements(db, user)

    r = await client.get("/api/v1/users/me/achievements")
    assert r.status_code == 200, r.text
    body = {a["code"]: a["earned_at"] for a in r.json()}
    # One row per rule: the catalogue seeded by the migrations matches the code
    assert set(body) == set(ACHIEVEMENT_RULES)
    assert body["first_steps"] is not None
    assert body["level_5"] is None

async def test_record_activity_reads_fresh_xp(db, user_factory) -> None:
    user, _ = await user_factory(xp=100)
    # Raw SQL: the ORM object is not told, like a write from another session
    await db.execute(text("UPDATE users SET xp = 500 WHERE id = :id"), {"id": user.id})
    await record_activity(db, user, 20, today=TODAY)
    assert user.xp == 520


async def make_match(db, *players: User) -> str:
    await create_match(db, "testmatch", players[0].id, len(players), [])
    for player in players[1:]:
        await add_player(db, "testmatch", player.id)
    return "testmatch"


async def test_finish_match_pays_winner(db, user_factory) -> None:
    alice, _ = await user_factory(display_name="alice", email="alice@example.com")
    bob, _ = await user_factory(display_name="bob", email="bob@example.com")
    match_id = await make_match(db, alice, bob)
    await finish_match(
        db, match_id, [{"user_id": alice.id, "score": 30}, {"user_id": bob.id, "score": 10}]
    )
    assert alice.xp == 70
    assert bob.xp == 20


async def test_finish_match_tie_has_no_winner(db, user_factory) -> None:
    alice, _ = await user_factory(display_name="alice", email="alice@example.com")
    bob, _ = await user_factory(display_name="bob", email="bob@example.com")
    match_id = await make_match(db, alice, bob)
    await finish_match(
        db, match_id, [{"user_id": alice.id, "score": 10}, {"user_id": bob.id, "score": 10}]
    )
    assert alice.xp == 20
    assert bob.xp == 20

def test_display_fields() -> None:
    user = User(xp=4820, current_streak=5, last_activity_date=utc_today() - timedelta(days=3))
    assert (user.level, user.level_xp) == (5, 820)
    # Missed days: the stored 5 is stale
    assert user.streak == 0


async def test_me_sends_display_fields(client, as_user) -> None:
    await as_user(xp=1250, current_streak=2, last_activity_date=utc_today())
    body = (await client.get("/api/v1/auth/me")).json()
    assert (body["level"], body["level_xp"], body["streak"]) == (2, 250, 2)
    assert "current_streak" not in body


async def test_finish_match_forfeit_pays_last_player(db, user_factory) -> None:
    alice, _ = await user_factory(display_name="alice", email="alice@example.com")
    bob, _ = await user_factory(display_name="bob", email="bob@example.com")
    match_id = await make_match(db, alice, bob)
    # Bob quit while ahead: he is gone from the standings, Alice still wins
    await finish_match(db, match_id, [{"user_id": alice.id, "score": 0}], alice.id)
    assert alice.xp == 70
    assert bob.xp == 0


async def make_questions(db, count: int) -> list[Question]:
    suffix = uuid.uuid4().hex[:8]
    topic = Topic(slug=f"t-stats-{suffix}", position=0)
    db.add(topic)
    await db.flush()
    questions = [
        Question(
            slug=f"q-stats-{suffix}-{n}",
            topic_id=topic.id,
            kind=QuestionKind.free_text,
            status=QuestionStatus.published,
        )
        for n in range(count)
    ]
    db.add_all(questions)
    await db.flush()
    return questions


async def test_me_stats_counts_per_question(client, as_user, db) -> None:
    user = await as_user()
    q1, q2, q3 = await make_questions(db, 3)
    # q1: missed then solved · q2: missed only · q3: waiting for self-assessment
    for question, is_correct in ((q1, False), (q1, True), (q2, False), (q3, None)):
        db.add(
            Attempt(user_id=user.id, question_id=question.id, is_correct=is_correct, locale="fr")
        )
    await db.flush()
    body = (await client.get("/api/v1/users/me/stats")).json()
    assert body == {"solved": 1, "to_review": 2}


async def test_me_stats_empty(client, as_user) -> None:
    await as_user()
    body = (await client.get("/api/v1/users/me/stats")).json()
    assert body == {"solved": 0, "to_review": 0}

async def test_leaderboard_orders_by_xp_and_shares_ties(client, as_user, user_factory) -> None:
    await user_factory(display_name="alice", email="alice@example.com", xp=3000)
    await user_factory(display_name="bob", email="bob@example.com", xp=1200)
    await user_factory(display_name="carol", email="carol@example.com", xp=1200)
    await user_factory(display_name="dormant", email="dormant@example.com", xp=0)
    await user_factory(display_name="banned", email="banned@example.com", xp=9000, is_active=False)
    me = await as_user(display_name="me", email="me@example.com", xp=500)

    body = (await client.get("/api/v1/gamification/leaderboard")).json()

    ranks = [(e["display_name"], e["rank"]) for e in body["entries"]]
    assert ranks == [("alice", 1), ("bob", 2), ("carol", 2), ("me", 4)]
    assert body["entries"][0]["level"] == 4
    assert body["me"]["id"] == me.id
    assert body["me"]["rank"] == 4
    assert "email" not in body["entries"][0]


async def test_leaderboard_me_outside_top(client, as_user, user_factory) -> None:
    await user_factory(display_name="alice", email="alice@example.com", xp=3000)
    await user_factory(display_name="bob", email="bob@example.com", xp=2000)
    await as_user(display_name="me", email="me@example.com", xp=100)

    body = (await client.get("/api/v1/gamification/leaderboard?limit=1")).json()

    assert [e["display_name"] for e in body["entries"]] == ["alice"]
    assert body["me"]["rank"] == 3


async def test_leaderboard_me_null_without_xp(client, as_user) -> None:
    await as_user(xp=0)
    body = (await client.get("/api/v1/gamification/leaderboard")).json()
    assert body == {"entries": [], "me": None}


async def test_leaderboard_requires_login(client) -> None:
    r = await client.get("/api/v1/gamification/leaderboard")
    assert r.status_code == 401


# --- flight-stage achievements: progress through the course ---

@pytest.mark.parametrize(
    ("course", "expected"),
    [
        (CourseProgress(0, 0, 4), set()),
        (CourseProgress(1, 0, 4), {"liftoff"}),
        (CourseProgress(3, 1, 4), {"liftoff", "max_q"}),
        (CourseProgress(9, 2, 4), {"liftoff", "max_q", "meco"}),
        (CourseProgress(9, 4, 4), {"liftoff", "max_q", "meco", "orbit"}),
        # No course published: nothing to pass, no orbit
        (CourseProgress(0, 0, 0), set()),
    ],
)
def test_flight_stage_rules(course: CourseProgress, expected: set[str]) -> None:
    stages = {"liftoff", "max_q", "meco", "orbit"}
    user = User(xp=0, current_streak=0)
    earned = {code for code in stages if ACHIEVEMENT_RULES[code](user, course)}
    assert earned == expected


async def test_passing_half_the_modules_is_meco(db, user_factory) -> None:
    user, _ = await user_factory()
    learning_path = LearningPath(
        slug="t-stages", level=PathLevel.beginner, status=QuestionStatus.published
    )
    db.add(learning_path)
    await db.flush()
    topics = [Topic(slug=f"t-stage-{n}", position=n) for n in range(4)]
    db.add_all(topics)
    await db.flush()
    db.add_all(
        PathModule(path_id=learning_path.id, topic_id=topic.id, position=n)
        for n, topic in enumerate(topics)
    )
    db.add_all(
        ModuleProgress(user_id=user.id, topic_id=topic.id, passed_at=datetime.now(UTC))
        for topic in topics[:2]
    )
    await db.flush()

    progress = await course_progress(db, user.id)

    assert (progress.modules_passed, progress.modules_total) == (2, 4)
    assert {"max_q", "meco"} <= set(await check_achievements(db, user))
