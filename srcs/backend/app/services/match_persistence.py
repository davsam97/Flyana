"""Persistence helpers for realtime match events."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MatchMode, MatchStatus
from app.models.match import Match, MatchAttempt, MatchPlayer, MatchQuestion

from app.models.user import User
from app.services.gamification import XP_MATCH_PLAYED, XP_MATCH_WON, record_activity


async def create_match(
    db: AsyncSession,
    public_id: str,
    owner_id: int,
    max_players: int,
    questions: list[dict[str, Any]],
) -> None:
    match = Match(
        public_id=public_id,
        mode=MatchMode.duel if max_players == 2 else MatchMode.arena,
        max_players=max_players,
        question_count=len(questions),
    )
    db.add(match)
    await db.flush()
    db.add(MatchPlayer(match_id=match.id, user_id=owner_id))
    db.add_all(
        MatchQuestion(
            match_id=match.id,
            question_id=question["id"],
            position=position,
            choice_order=[choice["id"] for choice in question["choices"]],
        )
        for position, question in enumerate(questions, start=1)
    )
    await db.commit()


async def add_player(db: AsyncSession, public_id: str, user_id: int) -> None:
    match = await _get_match(db, public_id)
    existing = await db.get(
        MatchPlayer,
        {"match_id": match.id, "user_id": user_id},
    )
    if existing is not None:
        return
    db.add(MatchPlayer(match_id=match.id, user_id=user_id))
    await db.commit()


async def start_match(db: AsyncSession, public_id: str) -> None:
    match = await _get_match(db, public_id)
    now = datetime.now(UTC)
    match.status = MatchStatus.running
    match.started_at = now
    first_question = await db.scalar(
        select(MatchQuestion).where(
            MatchQuestion.match_id == match.id,
            MatchQuestion.position == 1,
        )
    )
    if first_question is not None:
        first_question.started_at = now
    await db.commit()


async def record_attempt(
    db: AsyncSession,
    public_id: str,
    user_id: int,
    question_number: int,
    choice_id: int,
    is_correct: bool,
    response_ms: int,
    score: int,
) -> None:
    match = await _get_match(db, public_id)
    match_question = await db.scalar(
        select(MatchQuestion).where(
            MatchQuestion.match_id == match.id,
            MatchQuestion.position == question_number,
        )
    )
    player = await db.get(MatchPlayer, {"match_id": match.id, "user_id": user_id})
    if match_question is None or player is None:
        return

    db.add(
        MatchAttempt(
            match_id=match.id,
            match_question_id=match_question.id,
            user_id=user_id,
            choice_id=choice_id,
            is_correct=is_correct,
            response_ms=response_ms,
            score=score,
        )
    )
    player.score += score
    await db.commit()


async def start_question(
    db: AsyncSession,
    public_id: str,
    question_number: int,
) -> None:
    match = await _get_match(db, public_id)
    match_question = await db.scalar(
        select(MatchQuestion).where(
            MatchQuestion.match_id == match.id,
            MatchQuestion.position == question_number,
        )
    )
    if match_question is None:
        return
    match_question.started_at = datetime.now(UTC)
    await db.commit()


async def finish_match(
    db: AsyncSession,
    public_id: str,
    standings: list[dict[str, int]],
    winner_id: int | None = None,
) -> dict[int, list[str]]:
    """Closes the match, stores the ranks, pays every player's XP

    Returns, per user id, the achievements this match unlocked
    """
    match = await _get_match(db, public_id)
    match.status = MatchStatus.finished
    match.finished_at = datetime.now(UTC)
    if winner_id is None:
        # Equal scores are ordered by user id only: a tie on top has no winner.
        # A match needs two players to start, so standings holding one player
        # come from a forfeit: the one left in the room wins it
        clear_winner = len(standings) == 1 or (
            len(standings) > 1 and standings[0]["score"] > standings[1]["score"]
        )
        winner_id = standings[0]["user_id"] if clear_winner else None
    unlocked: dict[int, list[str]] = {}
    for rank, standing in enumerate(standings, start=1):
        player = await db.get(
            MatchPlayer,
            {"match_id": match.id, "user_id": standing["user_id"]},
        )
        if player is None:
            continue
        player.score = standing["score"]
        player.final_rank = rank
        user = await db.get(User, standing["user_id"])
        if user is None:
            continue
        xp = XP_MATCH_PLAYED + (XP_MATCH_WON if user.id == winner_id else 0)
        unlocked[user.id] = await record_activity(db, user, xp)
    await db.commit()
    return unlocked


async def _get_match(db: AsyncSession, public_id: str) -> Match:
    match = await db.scalar(select(Match).where(Match.public_id == public_id))
    if match is None:
        raise LookupError(f"match {public_id} not found")
    return match
