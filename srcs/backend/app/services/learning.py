"""Learning: the adaptive check quiz, module progress and lessons read

Adaptivity is an Elo rating on both sides. Each student has a rating per
module, each question has `difficulty_rating`, and every answer in a check
quiz moves both: a right answer to a hard question raises the student a lot
and lowers the question a little. The next question is the one whose rating
is closest to where the student should succeed about 70 % of the time: hard
enough to learn from, easy enough not to discourage.

A check quiz is a run served one question at a time. A module is passed by a
run with at least 80 % right answers.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import exists, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.i18n import DEFAULT, translated_questions
from app.models.attempt import Attempt
from app.models.content import (
    Choice, ChoiceTranslation, LearningPath, LearningPathTranslation, Lesson,
    LessonTranslation, PathModule, Question, Topic, TopicTranslation
)
from app.models.enums import AttemptSource, GraderKind, QuestionKind, QuestionStatus
from app.models.learning import LessonRead, ModuleProgress, QuizRun, UserTopicRating
from app.models.user import User
from app.services.attempts import already_solved
from app.services.gamification import XP_CORRECT_QUIZ, XP_MODULE_PASSED, record_activity
from app.services.grading import grade_choices, grade_numeric

# A run of at least this share of right answers passes the module
PASS_RATIO = Decimal("0.8")
DEFAULT_QUIZ_QUESTIONS = 10

# The kinds a check quiz asks: graded by code, never by a model
QUIZ_KINDS = (QuestionKind.single_choice, QuestionKind.multi_choice, QuestionKind.numeric)

# Elo. A student's first answers in a module move their rating fast, so it
# settles near their level within one quiz; questions move slowly, being
# rated by every student
USER_START_RATING = Decimal("1000")
K_USER_NEW = 48
K_USER = 24
NEW_ANSWERS = 10
K_QUESTION = 8
# Questions stay inside the range the difficulty facets and labels know
QUESTION_RATING_BOUNDS = (Decimal("800"), Decimal("2000"))
USER_RATING_BOUNDS = (Decimal("400"), Decimal("2400"))

# The chance of success the next question aims at
TARGET_SUCCESS = 0.7
# Spreads the draw over questions of nearly the same rating, so two runs at
# the same level do not ask the same questions in the same order
DRAW_JITTER = 60
# A question answered right this recently comes last: there is little to
# learn from it again so soon
RECENT_SUCCESS = timedelta(days=7)

CENT = Decimal("0.01")


def expected_score(user_rating: Decimal, question_rating: Decimal) -> float:
    """The chance, by Elo, that a student of `user_rating` answers right"""
    return 1 / (1 + 10 ** (float(question_rating - user_rating) / 400))


def _clamp(value: Decimal, bounds: tuple[Decimal, Decimal]) -> Decimal:
    low, high = bounds
    return min(max(value, low), high).quantize(CENT, rounding=ROUND_HALF_UP)


def rate(
    user_rating: Decimal, question_rating: Decimal, correct: bool, user_answers: int
) -> tuple[Decimal, Decimal]:
    """The student's and the question's ratings after one answer

    `user_answers` counts the student's previous answers in this module
    """
    surprise = Decimal(str((1.0 if correct else 0.0) - expected_score(user_rating, question_rating)))
    k_user = K_USER_NEW if user_answers < NEW_ANSWERS else K_USER
    return (
        _clamp(user_rating + k_user * surprise, USER_RATING_BOUNDS),
        _clamp(question_rating - K_QUESTION * surprise, QUESTION_RATING_BOUNDS),
    )


def target_difficulty(user_rating: Decimal) -> Decimal:
    """The question rating a student of `user_rating` answers right `TARGET_SUCCESS` of the time"""
    offset = 400 * math.log10(TARGET_SUCCESS / (1 - TARGET_SUCCESS))
    return (user_rating - Decimal(str(offset))).quantize(CENT)


def passes(correct: int, total: int) -> bool:
    """Whether `correct` right answers out of `total` pass the module

    Integer arithmetic: 8 out of 10 passes, 5 out of 7 (71 %) does not
    """
    numerator, denominator = PASS_RATIO.as_integer_ratio()
    return total > 0 and correct * denominator >= total * numerator


def quiz_questions():
    """The questions a check quiz may ask, as a reusable filter"""
    return (
        Question.status == QuestionStatus.published,
        Question.kind.in_(QUIZ_KINDS),
    )


async def pick_question(
    db: AsyncSession,
    user_id: int,
    topic_id: int,
    rating: Decimal,
    exclude: Sequence[int],
) -> int | None:
    """The next question for this student, None when the module has no more"""
    recently_right = exists().where(
        Attempt.user_id == user_id,
        Attempt.question_id == Question.id,
        Attempt.is_correct.is_(True),
        Attempt.created_at > datetime.now(UTC) - RECENT_SUCCESS,
    )
    target = target_difficulty(rating)
    return await db.scalar(
        select(Question.id)
        .where(*quiz_questions(), Question.topic_id == topic_id, Question.id.not_in(exclude))
        .order_by(
            recently_right,
            func.abs(Question.difficulty_rating - target) + func.random() * DRAW_JITTER,
        )
        .limit(1)
    )


async def question_payload(db: AsyncSession, question_id: int, locale: str) -> dict[str, Any]:
    """A question as the student sees it before answering

    Choices in the order of the content file, which places the right ones,
    and never a word of the answer key: no `is_correct`, no expected value
    """
    row = (
        await db.execute(
            translated_questions(locale)
            .add_columns(Question.kind, Question.unit, Question.difficulty_rating)
            .where(Question.id == question_id)
        )
    ).one()

    wanted = aliased(ChoiceTranslation, name="t")
    fallback = aliased(ChoiceTranslation, name="en")
    choices = await db.execute(
        select(Choice.id, func.coalesce(wanted.text, fallback.text).label("text"))
        .outerjoin(wanted, (wanted.choice_id == Choice.id) & (wanted.locale == locale))
        .outerjoin(fallback, (fallback.choice_id == Choice.id) & (fallback.locale == DEFAULT))
        .where(Choice.question_id == question_id)
        .order_by(Choice.position)
    )
    return {
        "id": row.id,
        "kind": row.kind,
        "title": row.title,
        "stem": row.stem,
        "unit": row.unit,
        "difficulty_rating": row.difficulty_rating,
        "choices": [{"id": choice.id, "text": choice.text} for choice in choices],
    }


async def _quiz_length(db: AsyncSession, topic_id: int) -> int:
    """How many questions a run asks: the path's setting, capped by the pool"""
    wanted = await db.scalar(
        select(PathModule.min_questions).where(PathModule.topic_id == topic_id).limit(1)
    )
    pool = await db.scalar(
        select(func.count()).select_from(Question).where(
            *quiz_questions(), Question.topic_id == topic_id
        )
    )
    return min(wanted or DEFAULT_QUIZ_QUESTIONS, pool or 0)


async def topic_rating(db: AsyncSession, user_id: int, topic_id: int) -> UserTopicRating:
    """The student's rating row in a module, created at the starting rating"""
    await db.execute(
        pg_insert(UserTopicRating)
        .values(user_id=user_id, topic_id=topic_id, rating=USER_START_RATING)
        .on_conflict_do_nothing(index_elements=["user_id", "topic_id"])
    )
    row = await db.get(UserTopicRating, (user_id, topic_id), with_for_update=True, populate_existing=True)
    assert row is not None
    return row


async def start_run(db: AsyncSession, user: User, topic: Topic) -> QuizRun:
    """Opens a check quiz on a module, leaving any unfinished one behind

    An abandoned run is closed as not passed and counts for nothing
    """
    count = await _quiz_length(db, topic.id)
    if count == 0:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="no questions")

    now = datetime.now(UTC)
    await db.execute(
        update(QuizRun)
        .where(
            QuizRun.user_id == user.id,
            QuizRun.topic_id == topic.id,
            QuizRun.finished_at.is_(None),
        )
        .values(finished_at=now, passed=False, current_question_id=None)
    )
    rating = await topic_rating(db, user.id, topic.id)
    first = await pick_question(db, user.id, topic.id, rating.rating, [])
    assert first is not None  # the pool holds at least `count` questions
    run = QuizRun(
        user_id=user.id,
        topic_id=topic.id,
        question_count=count,
        served_ids=[first],
        current_question_id=first,
    )
    db.add(run)
    await db.flush()
    return run


async def _answer_key(db: AsyncSession, question: Question) -> list[int]:
    return list(
        await db.scalars(
            select(Choice.id).where(Choice.question_id == question.id, Choice.is_correct.is_(True))
        )
    )


async def correction_payload(
    db: AsyncSession, question: Question, locale: str
) -> dict[str, Any]:
    """Everything that explains the right answer, shown once the student answered"""
    wording = (
        await db.execute(translated_questions(locale).where(Question.id == question.id))
    ).one()
    return {
        "correct_choice_ids": await _answer_key(db, question),
        "expected_value": question.numeric_answer,
        "tolerance_rel": question.tolerance_rel,
        "unit": question.unit,
        "explanation": wording.explanation,
        "source": (
            {"label": question.source_label, "url": question.source_url}
            if question.source_label
            else None
        ),
    }


async def answer_run(
    db: AsyncSession,
    run: QuizRun,
    user: User,
    *,
    question_id: int,
    choice_ids: list[int] | None,
    value: Decimal | None,
    locale: str,
) -> dict[str, Any]:
    """Grades the answer to the current question and moves the run on

    `run` must be locked by the caller (`with_for_update`), so a double click
    cannot grade the same question twice. No commit: the caller commits, so
    the attempt, the ratings and the XP land together or not at all
    """
    if run.finished_at is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="quiz finished")
    if run.current_question_id != question_id:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="not the current question")

    question = await db.get(Question, question_id, with_for_update=True, populate_existing=True)
    assert question is not None

    if question.kind == QuestionKind.numeric:
        if value is None:
            raise HTTPException(422, detail="a number is expected")
        assert question.numeric_answer is not None and question.tolerance_rel is not None
        correct = grade_numeric(question.numeric_answer, question.tolerance_rel, value)
        selected, raw = None, str(value)
    else:
        offered = set(await db.scalars(select(Choice.id).where(Choice.question_id == question.id)))
        if not choice_ids or not set(choice_ids) <= offered:
            raise HTTPException(422, detail="choices of this question are expected")
        correct = grade_choices(question.kind, await _answer_key(db, question), choice_ids)
        selected, raw = choice_ids, None

    # Before the attempt is added, or autoflush sends it and the query finds it
    first_success = correct and not await already_solved(db, user.id, question.id)
    db.add(
        Attempt(
            user_id=user.id,
            question_id=question.id,
            selected_choice_ids=selected,
            raw_response=raw,
            is_correct=correct,
            locale=locale,
            source=AttemptSource.practice,
            grader=GraderKind.deterministic,
            grader_meta={"quiz_run_id": run.id},
        )
    )

    rating = await topic_rating(db, user.id, run.topic_id)
    rating.rating, question.difficulty_rating = rate(
        rating.rating, question.difficulty_rating, correct, rating.answers
    )
    rating.answers += 1
    question.times_asked += 1
    question.times_correct += int(correct)

    run.answered += 1
    run.correct += int(correct)
    xp = XP_CORRECT_QUIZ if first_success else 0

    next_id: int | None = None
    if run.answered < run.question_count:
        next_id = await pick_question(db, user.id, run.topic_id, rating.rating, run.served_ids)
    if next_id is None:
        # Normally the last question; earlier only if the module lost questions mid-run
        run.question_count = run.answered
        xp += await _finish_run(db, run)
    else:
        run.served_ids = [*run.served_ids, next_id]
    run.current_question_id = next_id

    achievements = await record_activity(db, user, xp)
    return {
        "correct": correct,
        "correction": await correction_payload(db, question, locale),
        "xp": xp,
        "achievements": achievements,
        "rating": rating.rating,
        "next_question": (
            await question_payload(db, next_id, locale) if next_id is not None else None
        ),
        "result": run_result(run) if run.finished_at is not None else None,
    }


async def _finish_run(db: AsyncSession, run: QuizRun) -> int:
    """Closes a run and records it in the module's progress; returns the XP it earns"""
    run.finished_at = datetime.now(UTC)
    run.passed = passes(run.correct, run.question_count)
    score = (Decimal(run.correct) / Decimal(run.question_count)).quantize(Decimal("0.001"))

    await db.execute(
        pg_insert(ModuleProgress)
        .values(user_id=run.user_id, topic_id=run.topic_id)
        .on_conflict_do_nothing(index_elements=["user_id", "topic_id"])
    )
    progress = await db.get(
        ModuleProgress, (run.user_id, run.topic_id), with_for_update=True, populate_existing=True
    )
    assert progress is not None
    progress.quizzes += 1
    progress.best_score = max(progress.best_score, score)
    if run.passed and progress.passed_at is None:
        progress.passed_at = run.finished_at
        return XP_MODULE_PASSED
    return 0


def run_result(run: QuizRun) -> dict[str, Any]:
    """The outcome of a finished run"""
    return {
        "correct": run.correct,
        "total": run.question_count,
        "passed": bool(run.passed),
        "pass_ratio": PASS_RATIO,
    }


# --- Read side: the path, its modules and their lessons ---


async def module_topic(db: AsyncSession, slug: str) -> Topic:
    """A live module by slug; 404 for an unknown or archived one"""
    topic = await db.scalar(select(Topic).where(Topic.slug == slug, Topic.archived.is_(False)))
    if topic is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="not found")
    return topic


async def topic_wording(
    db: AsyncSession, topic_ids: Sequence[int], locale: str
) -> dict[int, tuple[str, str | None]]:
    """Name and description of each topic, the description from the same language as the name"""
    wanted = aliased(TopicTranslation, name="t")
    fallback = aliased(TopicTranslation, name="en")
    rows = await db.execute(
        select(
            Topic.id,
            Topic.slug,
            func.coalesce(wanted.name, fallback.name).label("name"),
            func.coalesce(wanted.description, fallback.description).label("description"),
        )
        .outerjoin(wanted, (wanted.topic_id == Topic.id) & (wanted.locale == locale))
        .outerjoin(fallback, (fallback.topic_id == Topic.id) & (fallback.locale == DEFAULT))
        .where(Topic.id.in_(topic_ids))
    )
    return {row.id: (row.name or row.slug, row.description) for row in rows}


async def module_summaries(
    db: AsyncSession, user_id: int, topics: Sequence[Topic], locale: str
) -> list[dict[str, Any]]:
    """Each module with the caller's progress, in the order given"""
    ids = [topic.id for topic in topics]
    wording = await topic_wording(db, ids, locale)

    # Comprehensions, not `dict(result)`: a Result has `keys()`, the column
    # names, so `dict()` would take it for a mapping
    lessons_total = {
        topic_id: count
        for topic_id, count in (
            await db.execute(
                select(Lesson.topic_id, func.count())
                .where(Lesson.topic_id.in_(ids), Lesson.status == QuestionStatus.published)
                .group_by(Lesson.topic_id)
            )
        ).tuples()
    }
    lessons_read = {
        topic_id: count
        for topic_id, count in (
            await db.execute(
                select(Lesson.topic_id, func.count())
                .join(LessonRead, LessonRead.lesson_id == Lesson.id)
                .where(
                    Lesson.topic_id.in_(ids),
                    Lesson.status == QuestionStatus.published,
                    LessonRead.user_id == user_id,
                )
                .group_by(Lesson.topic_id)
            )
        ).tuples()
    }
    progress = {
        row.topic_id: row
        for row in await db.scalars(
            select(ModuleProgress).where(
                ModuleProgress.user_id == user_id, ModuleProgress.topic_id.in_(ids)
            )
        )
    }
    ratings = {
        topic_id: rating
        for topic_id, rating in (
            await db.execute(
                select(UserTopicRating.topic_id, UserTopicRating.rating).where(
                    UserTopicRating.user_id == user_id, UserTopicRating.topic_id.in_(ids)
                )
            )
        ).tuples()
    }

    summaries = []
    for position, topic in enumerate(topics):
        name, description = wording[topic.id]
        done = progress.get(topic.id)
        summaries.append(
            {
                "slug": topic.slug,
                "name": name,
                "description": description,
                "position": position,
                "lessons_total": lessons_total.get(topic.id, 0),
                "lessons_read": lessons_read.get(topic.id, 0),
                "quiz_questions": await _quiz_length(db, topic.id),
                "best_score": done.best_score if done else None,
                "quizzes": done.quizzes if done else 0,
                "passed": done is not None and done.passed_at is not None,
                "rating": ratings.get(topic.id),
            }
        )
    return summaries


async def path_modules(db: AsyncSession, path_slug: str) -> tuple[LearningPath, list[Topic]]:
    """A published path and its live modules, in order; 404 if there is no such path"""
    learning_path = await db.scalar(
        select(LearningPath).where(
            LearningPath.slug == path_slug, LearningPath.status == QuestionStatus.published
        )
    )
    if learning_path is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="not found")
    topics = list(
        await db.scalars(
            select(Topic)
            .join(PathModule, PathModule.topic_id == Topic.id)
            .where(PathModule.path_id == learning_path.id, Topic.archived.is_(False))
            .order_by(PathModule.position)
        )
    )
    return learning_path, topics


async def path_wording(
    db: AsyncSession, path_id: int, locale: str
) -> tuple[str, str | None]:
    rows = {
        row.locale: row
        for row in await db.scalars(
            select(LearningPathTranslation).where(LearningPathTranslation.path_id == path_id)
        )
    }
    chosen = rows.get(locale) or rows[DEFAULT]
    return chosen.title, chosen.description


async def module_lessons(
    db: AsyncSession, user_id: int, topic_id: int, locale: str
) -> list[dict[str, Any]]:
    """The published lessons of a module, in order, each marked read or not"""
    wanted = aliased(LessonTranslation, name="t")
    fallback = aliased(LessonTranslation, name="en")
    read = exists().where(LessonRead.lesson_id == Lesson.id, LessonRead.user_id == user_id)
    rows = await db.execute(
        select(
            Lesson.slug,
            Lesson.position,
            func.coalesce(wanted.title, fallback.title).label("title"),
            read.label("read"),
        )
        .outerjoin(wanted, (wanted.lesson_id == Lesson.id) & (wanted.locale == locale))
        .outerjoin(fallback, (fallback.lesson_id == Lesson.id) & (fallback.locale == DEFAULT))
        .where(Lesson.topic_id == topic_id, Lesson.status == QuestionStatus.published)
        .order_by(Lesson.position, Lesson.slug)
    )
    return [
        {"slug": row.slug, "title": row.title, "position": row.position, "read": row.read}
        for row in rows
    ]


async def published_lesson(db: AsyncSession, slug: str) -> Lesson:
    """A published lesson of a live module; 404 otherwise"""
    lesson = await db.scalar(
        select(Lesson)
        .join(Topic, Topic.id == Lesson.topic_id)
        .where(
            Lesson.slug == slug,
            Lesson.status == QuestionStatus.published,
            Topic.archived.is_(False),
        )
    )
    if lesson is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="not found")
    return lesson


async def lesson_body(db: AsyncSession, lesson_id: int, locale: str) -> LessonTranslation:
    rows = {
        row.locale: row
        for row in await db.scalars(
            select(LessonTranslation).where(LessonTranslation.lesson_id == lesson_id)
        )
    }
    return rows.get(locale) or rows[DEFAULT]


async def mark_read(db: AsyncSession, user_id: int, lesson_id: int) -> None:
    await db.execute(
        pg_insert(LessonRead)
        .values(user_id=user_id, lesson_id=lesson_id)
        .on_conflict_do_nothing(index_elements=["user_id", "lesson_id"])
    )
