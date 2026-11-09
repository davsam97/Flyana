"""Grading one written answer: limits, verdict, explanation, persistence

`grade_events` is the body of the streamed response: it grades, writes the
attempt, then streams the explanation, as NDJSON lines the front reads with
`fetch`. When no model can grade (switched off, over budget, unreachable) it
falls back to self-assessment instead of failing: the student reads the
reference explanation and says whether they had it right
"""

from __future__ import annotations

import json
import math
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.attempt import Attempt
from app.models.enums import AttemptSource, GraderKind
from app.services.llm.client import LLMUnavailable, Usage
from app.services.llm.grading import AnswerGrader, GradingInput, Verdict
from app.services.ratelimit import TokenBudget

from app.models.user import User
from app.services.gamification import XP_CORRECT_LLM, record_activity

# Shared by every student: the budget caps what the GPU machine spends per hour,
# whoever asks. In memory, so one process only, like the rate limiters
llm_budget = TokenBudget(per_hour=get_settings().LLM_HOURLY_TOKEN_BUDGET)

WINDOW = timedelta(hours=24)


async def recent_attempts(db: AsyncSession, user_id: int, question_id: int) -> list[datetime]:
    """When the model graded this student's answers to this question over the last 24 hours, oldest first

    Only model-graded attempts count: when no model can grade (switched off,
    over budget, unreachable) the student is not the one at fault, so the
    self-assessed fallback must not use up their tries
    """
    rows = await db.execute(
        select(Attempt.created_at)
        .where(
            Attempt.user_id == user_id,
            Attempt.question_id == question_id,
            Attempt.grader == GraderKind.llm,
            Attempt.created_at > datetime.now(UTC) - WINDOW,
        )
        .order_by(Attempt.created_at)
    )
    return list(rows.scalars())

async def already_solved(db: AsyncSession, user_id: int, question_id: int) -> bool:
    """Whether this student already got this question right, at any time

    XP is paid once per question: otherwise resending the same right answer
    until the daily limit would pay each time. Call it before adding the new
    attempt, or autoflush sends it first and the query finds it
    """
    found = await db.scalar(
        select(Attempt.id)
        .where(
            Attempt.user_id == user_id,
            Attempt.question_id == question_id,
            Attempt.is_correct.is_(True),
        )
        .limit(1)
    )
    return found is not None

def exhausted_retry_after(recent: list[datetime], limit: int) -> int:
    """Seconds until one of the counted attempts leaves the 24 hour window

    With `limit` attempts allowed, the one whose expiry frees a slot is the
    `limit`-th most recent, not always the oldest: there can be more rows than
    `limit` if the setting was lowered
    """
    freeing = recent[len(recent) - limit]
    remaining = (freeing + WINDOW - datetime.now(UTC)).total_seconds()
    return max(1, math.ceil(remaining))


def _line(event: dict[str, Any]) -> bytes:
    """One NDJSON line: a flat object with a `type` key, like the websocket messages"""
    return (json.dumps(event, ensure_ascii=False) + "\n").encode()


async def grade_events(
    db: AsyncSession,
    grader: AnswerGrader | None,
    item: GradingInput,
    *,
    user_id: int,
    question_id: int,
    explanation: str | None,
    attempts_left: int,
) -> AsyncIterator[bytes]:
    """Grades the answer and yields the events of the streamed response

    Runs after the response has started, so every refusal (auth, 404, limits)
    must already have happened in the route: from here on the status is 200
    and a failure can only be reported as an event
    """
    reason: str | None = None
    graded: tuple[Verdict, Usage] | None = None
    started = time.monotonic()
    if grader is None:
        reason = "disabled"
    elif not llm_budget.available():
        reason = "budget"
    else:
        try:
            graded = await grader.grade(item)
        except LLMUnavailable:
            reason = "unavailable"

    if grader is None or graded is None:
        attempt = Attempt(
            user_id=user_id,
            question_id=question_id,
            raw_response=item.answer,
            locale=item.locale,
            source=AttemptSource.practice,
            grader=GraderKind.self_assessed,
            is_correct=None,
            grader_meta={"reason": reason},
        )
        db.add(attempt)
        await db.commit()
        yield _line(
            {
                "type": "self_assessment",
                "attempt_id": attempt.id,
                "reason": reason,
                "explanation": explanation,
                # `attempts_left` assumed this attempt counts: a self-assessed one does not
                "attempts_left": attempts_left + 1,
            }
        )
        return

    verdict, usage = graded
    llm_budget.spend(usage.total)
    closed = verdict.validated or attempts_left == 0
    first_success = verdict.validated and not await already_solved(db, user_id, question_id)

    # Written before the explanation streams: a student who closes the tab
    # mid-stream has still spent the attempt, so reloading cannot buy a free retry
    attempt = Attempt(
        user_id=user_id,
        question_id=question_id,
        raw_response=item.answer,
        locale=item.locale,
        source=AttemptSource.practice,
        grader=GraderKind.llm,
        is_correct=verdict.validated,
        grader_meta={
            "model": grader.model,
            "outcome": verdict.outcome,
            "model_outcome": verdict.model_outcome,
            "score": verdict.score,
            "addresses_grader": verdict.addresses_grader,
            "false_statement": verdict.false_statement,
            "prompt_tokens": usage.prompt_tokens,
            "output_tokens": usage.output_tokens,
            "grade_ms": round((time.monotonic() - started) * 1000),
        },
    )
    db.add(attempt)
    user = await db.get(User, user_id)
    unlocked = (
        await record_activity(db, user, XP_CORRECT_LLM if first_success else 0)
        if user is not None
        else []
    )
    await db.commit()

    yield _line(
        {
            "type": "verdict",
            "attempt_id": attempt.id,
            "outcome": verdict.outcome,
            "score": round(verdict.score, 2),
            "flagged": verdict.addresses_grader,
            "attempts_left": attempts_left,
            "achievements": unlocked,
        }
    )

    # A flagged answer gets no generated text, the front shows a fixed message:
    # asked to comment on an injection, models sometimes copy it back verbatim.
    # A correct one needs none, the reference explanation follows in `done`
    if not verdict.addresses_grader and verdict.outcome != "correct":
        try:
            async for piece in grader.explain(item, verdict.outcome):
                if isinstance(piece, Usage):
                    llm_budget.spend(piece.total)
                else:
                    yield _line({"type": "delta", "text": piece})
        except LLMUnavailable:
            # The verdict is already recorded and sent: only the text is lost
            yield _line({"type": "error", "code": "explanation_failed"})

    # The reference explanation only once the exercise is over: before that the
    # student may still try again, and it would hand over the answer
    yield _line(
        {"type": "done", "closed": closed, "explanation": explanation if closed else None}
    )
