"""Attempts: a written answer, graded by the model or by the student"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.config import get_settings
from app.deps import CurrentUser, DbSession, Grader, Locale
from app.i18n import translated_questions
from app.models.attempt import Attempt
from app.models.content import Question
from app.models.enums import GraderKind, QuestionKind, QuestionStatus
from app.schemas.attempt import AttemptIn, AttemptQuota, SelfAssessmentIn, SelfAssessmentOut
from app.services.llm.grading import GradingInput
from app.services.ratelimit import grading_limiter

from app.services.attempts import already_solved, exhausted_retry_after, grade_events, recent_attempts
from app.services.gamification import XP_CORRECT_SELF, record_activity

router = APIRouter(tags=["attempts"])

_EVENTS = (
    "One JSON object per line, each with a `type`: `verdict` (outcome, score, "
    "flagged, attempts_left), then `delta` text chunks, an optional `error`, and "
    "`done` (closed, and the reference explanation once the exercise is over). "
    "When no model can grade, a single `self_assessment` event instead."
)


@router.get("/questions/{question_id}/attempts", response_model=AttemptQuota)
async def attempt_quota(question_id: int, user: CurrentUser, db: DbSession) -> AttemptQuota:
    """How many tries this student has left on this question, out of the limit"""
    row = (
        await db.execute(
            select(Question.status, Question.kind).where(Question.id == question_id)
        )
    ).one_or_none()
    if (
        row is None
        or row.status != QuestionStatus.published
        or row.kind != QuestionKind.free_text
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="not found")

    limit = get_settings().LLM_ATTEMPTS_PER_QUESTION
    spent = len(await recent_attempts(db, user.id, question_id))
    return AttemptQuota(limit=limit, left=max(0, limit - spent))


@router.post(
    "/questions/{question_id}/attempts",
    response_class=StreamingResponse,
    responses={200: {"content": {"application/x-ndjson": {}}, "description": _EVENTS}},
)
async def submit_attempt(
    question_id: int,
    body: AttemptIn,
    user: CurrentUser,
    db: DbSession,
    locale: Locale,
    grader: Grader,
) -> StreamingResponse:
    """Grades a written answer and streams the verdict then the explanation

    `POST`, not `GET` + `EventSource`: the answer would otherwise sit in the URL,
    so in nginx's access log and the browser history, and be capped near 8 KB

    Every refusal happens here, before the stream starts, as a plain status the
    front can read: once streaming, the status is already 200
    """
    row = (
        await db.execute(
            translated_questions(locale)
            .add_columns(Question.status, Question.kind, Question.key_points)
            .where(Question.id == question_id)
        )
    ).one_or_none()
    # Same rule as `GET /questions/{id}`: 404, never 403, so an unpublished
    # question is not confirmed to exist
    if (
        row is None
        or row.status != QuestionStatus.published
        or row.kind != QuestionKind.free_text
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="not found")

    key = f"grade:{user.id}"
    if not grading_limiter.consume(key):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="too many tries",
            headers={"Retry-After": str(grading_limiter.retry_after(key))},
        )

    limit = get_settings().LLM_ATTEMPTS_PER_QUESTION
    recent = await recent_attempts(db, user.id, question_id)
    if len(recent) >= limit:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="attempts exhausted",
            headers={"Retry-After": str(exhausted_retry_after(recent, limit))},
        )

    item = GradingInput(
        stem=row.stem,
        key_points=list(row.key_points),
        answer=body.answer,
        locale=locale,
    )
    # The generator runs on the request's session: FastAPI (>= 0.118) closes a
    # yield dependency only once the response, stream included, has been sent.
    # Plain values rather than `user`: the generator commits, which a later
    # read of an ORM attribute must not depend on
    return StreamingResponse(
        grade_events(
            db,
            grader,
            item,
            user_id=user.id,
            question_id=question_id,
            explanation=row.explanation,
            attempts_left=limit - len(recent) - 1,
        ),
        media_type="application/x-ndjson",
        # Without it nginx buffers the response and the text arrives in one block
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@router.post("/attempts/{attempt_id}/self-assessment", response_model=SelfAssessmentOut)
async def self_assess(
    attempt_id: int, body: SelfAssessmentIn, user: CurrentUser, db: DbSession
) -> SelfAssessmentOut:
    """Records whether the student judged their own answer right

    Only on a self-assessed attempt still waiting for it: a model's verdict
    cannot be overridden, and a mark cannot be changed afterwards
    """
    attempt = await db.get(Attempt, attempt_id)
    # Someone else's attempt answers exactly like a missing one
    if attempt is None or attempt.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="not found")
    if attempt.grader != GraderKind.self_assessed or attempt.is_correct is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="already assessed")
    # Before setting `is_correct`: autoflush would count this very attempt
    first_success = body.correct and not await already_solved(
        db, user.id, attempt.question_id
    )
    attempt.is_correct = body.correct
    unlocked = await record_activity(db, user, XP_CORRECT_SELF if first_success else 0)
    await db.commit()
    return SelfAssessmentOut(achievements=unlocked)
