"""Reading a finished duel back, and what a room can be set to"""

from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from app.deps import CurrentUser, DbSession, Locale
from app.i18n import translated_questions
from app.models.content import (
    Choice,
    ChoiceTranslation,
    Question,
    Topic,
    TopicTranslation,
)
from app.models.enums import MatchStatus
from app.models.match import Match, MatchAttempt, MatchPlayer, MatchQuestion
from app.models.user import User
from app.schemas.match import (
    MatchAttemptOut,
    MatchChoiceOut,
    MatchPlayerOut,
    MatchQuestionOut,
    MatchSummaryOut,
    PlayableTopicOut,
)
from app.services.match_questions import playable_questions

router = APIRouter(prefix="/matches", tags=["matches"])


def _as_played(
    choices: list[MatchChoiceOut], choice_order: list[int]
) -> list[MatchChoiceOut]:
    if not choice_order:
        return choices

    by_id = {choice.id: choice for choice in choices}
    played = [by_id.pop(choice_id) for choice_id in choice_order if choice_id in by_id]
    return played + [choice for choice in choices if choice.id in by_id]


# Declared before `/{public_id}`: FastAPI matches routes in order, and the
# parameterised one would otherwise swallow `topics` as a match id
@router.get("/topics", response_model=list[PlayableTopicOut])
async def playable_topics(db: DbSession, locale: Locale) -> list[PlayableTopicOut]:
    """Lists the exam levels a room can be set to, with how many questions each holds"""
    parent = aliased(Topic, name="parent")
    wanted = aliased(TopicTranslation, name="t")
    fallback = aliased(TopicTranslation, name="en")
    parent_wanted = aliased(TopicTranslation, name="pt")
    parent_fallback = aliased(TopicTranslation, name="pen")

    rows = await db.execute(
        select(
            Topic.slug,
            func.coalesce(wanted.name, fallback.name).label("name"),
            func.coalesce(wanted.description, fallback.description).label("description"),
            parent.slug.label("parent_slug"),
            func.coalesce(parent_wanted.name, parent_fallback.name).label("parent_name"),
            func.count(Question.id).label("question_count"),
        )
        .join(Question, Question.topic_id == Topic.id)
        .outerjoin(parent, parent.id == Topic.parent_id)
        .outerjoin(wanted, (wanted.topic_id == Topic.id) & (wanted.locale == locale))
        .outerjoin(fallback, (fallback.topic_id == Topic.id) & (fallback.locale == "en"))
        .outerjoin(
            parent_wanted,
            (parent_wanted.topic_id == parent.id) & (parent_wanted.locale == locale),
        )
        .outerjoin(
            parent_fallback,
            (parent_fallback.topic_id == parent.id) & (parent_fallback.locale == "en"),
        )
        .where(*playable_questions())
        .group_by(
            Topic.id,
            Topic.slug,
            Topic.position,
            wanted.name,
            fallback.name,
            wanted.description,
            fallback.description,
            parent.slug,
            parent.position,
            parent_wanted.name,
            parent_fallback.name,
        )
        .order_by(parent.position.nulls_first(), Topic.position, Topic.slug)
    )

    return [
        PlayableTopicOut(
            slug=row.slug,
            name=row.name or row.slug,
            description=row.description,
            parent_slug=row.parent_slug,
            parent_name=row.parent_name,
            question_count=row.question_count,
        )
        for row in rows
    ]


@router.get("/{public_id}", response_model=MatchSummaryOut)
async def match_summary(
    public_id: str, user: CurrentUser, db: DbSession, locale: Locale
) -> MatchSummaryOut:
    """Returns a finished match, round by round, to one of its players

    **This reveals the right answers**, which is why an unfinished match is
    refused: served mid-game it would hand a player the rest of the answers.

    Anyone who did not play it gets a 404 rather than a 403, like every other
    read in this API: the existence of a match is not confirmed to a stranger.
    """
    match = await db.scalar(select(Match).where(Match.public_id == public_id))
    if match is None or match.status != MatchStatus.finished:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="not found")

    played = await db.scalar(
        select(MatchPlayer).where(
            MatchPlayer.match_id == match.id, MatchPlayer.user_id == user.id
        )
    )
    if played is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="not found")

    players = [
        MatchPlayerOut(
            user_id=row.user_id,
            display_name=row.display_name,
            avatar_path=row.avatar_path,
            score=row.score,
            final_rank=row.final_rank,
        )
        for row in await db.execute(
            select(
                MatchPlayer.user_id,
                User.display_name,
                User.avatar_path,
                MatchPlayer.score,
                MatchPlayer.final_rank,
            )
            .join(User, User.id == MatchPlayer.user_id)
            .where(MatchPlayer.match_id == match.id)
            # Players who left keep their place; a missing rank sorts last
            .order_by(MatchPlayer.final_rank.nulls_last(), MatchPlayer.joined_at)
        )
    ]

    rounds = list(
        await db.execute(
            select(
                MatchQuestion.id,
                MatchQuestion.position,
                MatchQuestion.question_id,
                MatchQuestion.choice_order,
            )
            .where(MatchQuestion.match_id == match.id)
            .order_by(MatchQuestion.position)
        )
    )
    question_ids = [row.question_id for row in rounds]

    stems = {
        row.id: row
        for row in await db.execute(
            translated_questions(locale)
            .add_columns(Question.slug)
            .where(Question.id.in_(question_ids))
        )
    }

    wanted = aliased(ChoiceTranslation, name="t")
    fallback = aliased(ChoiceTranslation, name="en")
    choices_by_question: defaultdict[int, list[MatchChoiceOut]] = defaultdict(list)
    for row in await db.execute(
        select(
            Choice.id,
            Choice.question_id,
            Choice.is_correct,
            func.coalesce(wanted.text, fallback.text).label("text"),
        )
        .outerjoin(
            wanted, (wanted.choice_id == Choice.id) & (wanted.locale == locale)
        )
        .outerjoin(fallback, (fallback.choice_id == Choice.id) & (fallback.locale == "en"))
        .where(Choice.question_id.in_(question_ids))
        .order_by(Choice.question_id, Choice.position)
    ):
        choices_by_question[row.question_id].append(
            MatchChoiceOut(id=row.id, text=row.text or "", correct=row.is_correct)
        )

    attempts_by_round: defaultdict[int, list[MatchAttemptOut]] = defaultdict(list)
    for attempt in await db.scalars(
        select(MatchAttempt)
        .where(MatchAttempt.match_id == match.id)
        .order_by(MatchAttempt.created_at)
    ):
        attempts_by_round[attempt.match_question_id].append(
            MatchAttemptOut(
                user_id=attempt.user_id,
                choice_id=attempt.choice_id,
                is_correct=attempt.is_correct,
                response_ms=attempt.response_ms,
                score=attempt.score,
            )
        )

    # Every round resolves: `match_questions.question_id` is `ON DELETE
    # RESTRICT`, so a question played once can no longer leave the table
    questions = [
        MatchQuestionOut(
            position=row.position,
            question_id=row.question_id,
            slug=stems[row.question_id].slug,
            stem=stems[row.question_id].stem or "",
            is_fallback=bool(stems[row.question_id].is_fallback),
            choices=_as_played(choices_by_question[row.question_id], row.choice_order),
            attempts=attempts_by_round[row.id],
        )
        for row in rounds
    ]

    return MatchSummaryOut(
        public_id=match.public_id,
        mode=match.mode.value,
        question_count=match.question_count,
        started_at=match.started_at,
        finished_at=match.finished_at,
        players=players,
        questions=questions,
    )
