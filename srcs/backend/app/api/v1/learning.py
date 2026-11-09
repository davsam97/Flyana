"""The course: path, modules, lessons and the adaptive check quiz"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentUser, DbSession, Locale
from app.models.learning import QuizRun
from app.models.content import Topic
from app.schemas.learning import (
    AnswerIn, AnswerOut, LessonOut, LessonReadOut, ModuleOut, PathOut, RunOut
)
from app.services import learning
from app.services.gamification import record_activity

router = APIRouter(tags=["learning"])


@router.get("/paths/{slug}", response_model=PathOut)
async def get_path(slug: str, user: CurrentUser, db: DbSession, locale: Locale) -> PathOut:
    """A learning path, its modules in order, and the caller's progress in each"""
    learning_path, topics = await learning.path_modules(db, slug)
    title, description = await learning.path_wording(db, learning_path.id, locale)
    modules = await learning.module_summaries(db, user.id, topics, locale)
    return PathOut.model_validate(
        {
            "slug": learning_path.slug,
            "title": title,
            "description": description,
            "pass_ratio": learning.PASS_RATIO,
            "modules": modules,
        }
    )


@router.get("/modules/{slug}", response_model=ModuleOut)
async def get_module(slug: str, user: CurrentUser, db: DbSession, locale: Locale) -> ModuleOut:
    """A module's page: progress, lessons, and the check quiz left open if any"""
    topic = await learning.module_topic(db, slug)
    [summary] = await learning.module_summaries(db, user.id, [topic], locale)
    summary["lessons"] = await learning.module_lessons(db, user.id, topic.id, locale)
    summary["open_run_id"] = await db.scalar(
        select(QuizRun.id).where(
            QuizRun.user_id == user.id,
            QuizRun.topic_id == topic.id,
            QuizRun.finished_at.is_(None),
        )
    )
    return ModuleOut.model_validate(summary)


@router.get("/lessons/{slug}", response_model=LessonOut)
async def get_lesson(slug: str, user: CurrentUser, db: DbSession, locale: Locale) -> LessonOut:
    """One lesson in the caller's language, with its neighbours in the module"""
    lesson = await learning.published_lesson(db, slug)
    body = await learning.lesson_body(db, lesson.id, locale)
    siblings = await learning.module_lessons(db, user.id, lesson.topic_id, locale)
    index = next(i for i, sibling in enumerate(siblings) if sibling["slug"] == lesson.slug)
    topic = await db.get(Topic, lesson.topic_id)
    assert topic is not None
    [(module_name, _)] = (await learning.topic_wording(db, [topic.id], locale)).values()
    return LessonOut(
        slug=lesson.slug,
        title=body.title,
        body=body.body,
        module_slug=topic.slug,
        module_name=module_name,
        position=index,
        previous_slug=siblings[index - 1]["slug"] if index > 0 else None,
        next_slug=siblings[index + 1]["slug"] if index + 1 < len(siblings) else None,
        read=siblings[index]["read"],
    )


@router.post("/lessons/{slug}/read", response_model=LessonReadOut)
async def read_lesson(slug: str, user: CurrentUser, db: DbSession) -> LessonReadOut:
    """Marks a lesson read to the end. Marking it again changes nothing

    Reading counts as the day's activity for the streak, and may unlock the
    first flight-stage achievement
    """
    lesson = await learning.published_lesson(db, slug)
    await learning.mark_read(db, user.id, lesson.id)
    unlocked = await record_activity(db, user, 0)
    await db.commit()
    return LessonReadOut(achievements=unlocked)


async def _run_out(db: DbSession, run: QuizRun, locale: str) -> RunOut:
    topic = await db.get(Topic, run.topic_id)
    assert topic is not None
    return RunOut.model_validate(
        {
            "id": run.id,
            "module_slug": topic.slug,
            "total": run.question_count,
            "answered": run.answered,
            "correct": run.correct,
            "question": (
                await learning.question_payload(db, run.current_question_id, locale)
                if run.current_question_id is not None and run.finished_at is None
                else None
            ),
            "result": learning.run_result(run) if run.finished_at is not None else None,
        }
    )


async def _own_run(db: DbSession, run_id: int, user_id: int, *, lock: bool = False) -> QuizRun:
    """The caller's run; someone else's answers exactly like a missing one"""
    run = await db.get(QuizRun, run_id, with_for_update=lock, populate_existing=lock)
    if run is None or run.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="not found")
    return run


@router.post("/modules/{slug}/quiz", response_model=RunOut, status_code=status.HTTP_201_CREATED)
async def start_quiz(slug: str, user: CurrentUser, db: DbSession, locale: Locale) -> RunOut:
    """Starts a check quiz on a module and serves its first question

    A quiz left unfinished on the same module is closed as not passed
    """
    topic = await learning.module_topic(db, slug)
    run = await learning.start_run(db, user, topic)
    out = await _run_out(db, run, locale)
    await db.commit()
    return out


@router.get("/quiz-runs/{run_id}", response_model=RunOut)
async def get_quiz(run_id: int, user: CurrentUser, db: DbSession, locale: Locale) -> RunOut:
    """Where a check quiz stands, to pick it up after a reload"""
    return await _run_out(db, await _own_run(db, run_id, user.id), locale)


@router.post("/quiz-runs/{run_id}/answer", response_model=AnswerOut)
async def answer_quiz(
    run_id: int, body: AnswerIn, user: CurrentUser, db: DbSession, locale: Locale
) -> AnswerOut:
    """Grades the answer to the current question, then serves the next one or the result"""
    run = await _own_run(db, run_id, user.id, lock=True)
    outcome = await learning.answer_run(
        db,
        run,
        user,
        question_id=body.question_id,
        choice_ids=body.choice_ids,
        value=body.value,
        locale=locale,
    )
    out = AnswerOut.model_validate(
        {**outcome, "answered": run.answered, "total": run.question_count}
    )
    await db.commit()
    return out
