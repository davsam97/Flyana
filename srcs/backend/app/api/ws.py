"""Realtime channel: presence, plus a thin relay for chat side-signals

One socket per browser tab, authenticated the same way as REST calls (the
`access_token` cookie). nginx already proxies the upgrade at `/api/ws`.

The socket never carries anything the REST API cannot rebuild: presence
transitions and "is typing" hints only. Messages themselves are stored by
`POST /api/v1/chat/messages` and pushed from there.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, WebSocket
from sqlalchemy import update
from starlette.websockets import WebSocketDisconnect

from app.db import SessionLocal
from app.deps import DbSession, WsUser
from app.models.user import User
from app.services.realtime import (
    FINISHED_ROOM_RETENTION_SECONDS,
    hub,
)
from app.services.match_questions import load_published_questions
from app.services.match_persistence import (
    add_player,
    create_match,
    finish_match,
    record_attempt,
    start_question,
    start_match,
)
from app.services.social import friend_ids
from app.schemas.realtime import validate_client_message

logger = logging.getLogger(__name__)
router = APIRouter(tags=["realtime"])


async def remove_finished_room_after_retention(room_id: str) -> None:
    await asyncio.sleep(FINISHED_ROOM_RETENTION_SECONDS)
    if hub.remove_finished_room(room_id):
        logger.info("Removed finished match room %s", room_id)


async def announce_unlocked(unlocked: dict[int, list[str]]) -> None:
    """Tells each player which achievements the match just gave them"""
    for user_id, codes in unlocked.items():
        if codes:
            await hub.send_to(
                user_id, {"type": "achievements.unlocked", "codes": codes}
            )


async def forfeit_player(room_id: str, user_id: int) -> bool:
    """Takes a player out of a room, closing the match if one is left

    Returns whether the match ended, so callers skip the lobby refresh
    """
    finished = hub.forfeit_user(room_id, user_id)
    if finished is None:
        return False

    # A forfeit ends the match for good, so it is written down like any
    # other ending. The standings only hold the players still in the
    # room: the one who left keeps their score and no rank
    async with SessionLocal() as db:
        unlocked = await finish_match(db, room_id, finished["standings"])
    await hub.broadcast(hub.room_players(room_id), finished)
    if unlocked:
        await announce_unlocked(unlocked)
    asyncio.create_task(remove_finished_room_after_retention(room_id))
    return True


async def expire_player_after_grace(user_id: int) -> None:
    await asyncio.sleep(60)
    expired_rooms = hub.expire_disconnected_user(user_id)

    for room_id in expired_rooms:
        players = hub.room_players(room_id)
        if not players:
            continue

        await hub.broadcast(
            players,
            {
                "type": "match.player_forfeit",
                "match_id": room_id,
                "user_id": user_id,
            },
        )
        if await forfeit_player(room_id, user_id):
            continue

        lobby = hub.lobby_message(room_id)
        if lobby is not None:
            await hub.broadcast(players, lobby)


async def run_match_timer(room_id: str) -> None:
    """Paces the match: closes each question, then the reveal that follows it

    Every question change goes through here, whether the question ran out of
    time or everyone answered early. One driver rather than two keeps the
    reveal from being skipped by the last answer to arrive
    """
    async with SessionLocal() as db:
        while hub.is_match_running(room_id):
            await asyncio.sleep(1)

            expired = hub.expire_question(room_id)
            if expired is not None:
                await hub.broadcast(hub.room_players(room_id), expired)

            event = hub.expire_reveal(room_id)
            if event is None:
                continue

            # Written before it is announced: the end-of-match screen reads the
            # match back as soon as it receives this event, and the summary
            # route refuses a match the database still calls running
            unlocked = {}
            if event["type"] == "match.finished":
                unlocked = await finish_match(db, room_id, event["standings"])

            await hub.broadcast(hub.room_players(room_id), event)

            if event["type"] == "match.finished":
                await announce_unlocked(unlocked)
                asyncio.create_task(
                    remove_finished_room_after_retention(room_id)
                )
                return

            await start_question(db, room_id, event["question_number"])


@router.websocket("/ws")
async def realtime(ws: WebSocket, user: WsUser, db: DbSession) -> None:
    """Registers the socket, announces presence, then relays ping and typing

    Presence only fires on the *first* socket in and the *last* socket out:
    opening a second tab must not spam friends with a redundant "online".
    """
    await ws.accept()
    friends = await friend_ids(db, user.id)

    if await hub.connect(user.id, ws):
        await hub.broadcast(
            friends, {"type": "presence", "user_id": user.id, "online": True}
        )

    restored_rooms = hub.restore_user(user.id)
    for restored_id in restored_rooms:
        players = hub.room_players(restored_id)
        await hub.broadcast(
            players,
            {
                "type": "match.player_presence",
                "match_id": restored_id,
                "user_id": user.id,
                "connected": True,
            },
        )

    for state in hub.state_sync(user.id):
        await ws.send_json(state)

    try:
        while True:
            raw_message = await ws.receive_json()
            message = validate_client_message(raw_message)
            if message is None:
                await ws.send_json({
                    "type": "error",
                    "code": "INVALID_MESSAGE",
                })
                continue
            message_type = message.get("type")

            if message_type == "ping":
                await ws.send_json({"type": "pong"})

            elif message_type == "chat.typing":
                target = message.get("to")

                if isinstance(target, int):
                    await hub.send_to(
                        target,
                        {
                            "type": "chat.typing",
                            "user_id": user.id,
                        },
                    )

            elif message_type == "match.create":
                max_players = message.get("max_players", 8)

                if not isinstance(max_players, int):
                    await ws.send_json({
                        "type": "error",
                        "code": "INVALID_MAX_PLAYERS",
                    })
                    continue

                # Already shaped by `CreateMatchMessage`. An unknown slug simply
                # matches nothing, and the empty draw below is what says so
                topics = message.get("topics", [])
                question_count = message.get("question_count", 10)

                max_players = max(2, min(max_players, 8))
                # `user` was resolved once, when the socket opened, and this
                # connection outlives that: it is the same one for every match
                # the tab plays. Re-read the locale rather than trust a value
                # that may predate a language change made mid-session.
                await db.refresh(user, attribute_names=["locale"])
                questions = await load_published_questions(
                    db, user.locale, limit=question_count, topics=topics
                )
                if not questions:
                    await ws.send_json({
                        "type": "error",
                        "code": "NO_QUESTIONS_AVAILABLE",
                    })
                    continue

                new_room_id = hub.create_room(
                    user.id,
                    max_players,
                    questions,
                    {
                        "display_name": user.display_name,
                        "avatar_path": user.avatar_path,
                    },
                    topics,
                )
                await create_match(db, new_room_id, user.id, max_players, questions)
                lobby = hub.lobby_message(new_room_id)

                await ws.send_json({
                    "type": "match.created",
                    "match_id": new_room_id,
                })

                if lobby is not None:
                    await hub.broadcast(hub.room_players(new_room_id), lobby)

            elif message_type == "match.join":
                room_id = message.get("match_id")

                if not isinstance(room_id, str):
                    await ws.send_json({
                        "type": "error",
                        "code": "INVALID_MATCH_ID",
                    })
                    continue

                error_code = hub.join_room(
                    room_id,
                    user.id,
                    {
                        "display_name": user.display_name,
                        "avatar_path": user.avatar_path,
                    },
                )

                if error_code is not None:
                    await ws.send_json({
                        "type": "error",
                        "code": error_code,
                    })
                    continue

                await add_player(db, room_id, user.id)

                lobby = hub.lobby_message(room_id)
                if lobby is not None:
                    await hub.broadcast(hub.room_players(room_id), lobby)

            elif message_type == "match.ready":
                room_id = message.get("match_id")
                ready = message.get("ready")

                if not isinstance(room_id, str) or not isinstance(ready, bool):
                    await ws.send_json({
                        "type": "error",
                        "code": "INVALID_READY_MESSAGE",
                    })
                    continue

                error_code = hub.set_ready(room_id, user.id, ready)

                if error_code is not None:
                    await ws.send_json({
                        "type": "error",
                        "code": error_code,
                    })
                    continue

                if hub.room_is_ready(room_id):
                    started = hub.start_match(room_id)
                    if started is not None:
                        await start_match(db, room_id)
                        players = hub.room_players(room_id)
                        await hub.broadcast(players, started)
                        question = hub.current_question(room_id)
                        if question is not None:
                            await hub.broadcast(players, question)
                        asyncio.create_task(run_match_timer(room_id))
                else:
                    lobby = hub.lobby_message(room_id)
                    if lobby is not None:
                        await hub.broadcast(hub.room_players(room_id), lobby)

            elif message_type == "match.answer":
                room_id = message.get("match_id")
                question_id = message.get("question_id")
                choice_id = message.get("choice_id")

                if (
                    not isinstance(room_id, str)
                    or not isinstance(question_id, int)
                    or not isinstance(choice_id, int)
                ):
                    await ws.send_json({"type": "error", "code": "INVALID_ANSWER"})
                    continue

                result = hub.answer(room_id, user.id, question_id, choice_id)
                if result.get("type") == "error":
                    await ws.send_json(result)
                    continue

                await record_attempt(
                    db,
                    room_id,
                    user.id,
                    result["_question_number"],
                    choice_id,
                    result["_correct"],
                    result["_response_ms"],
                    result["_score_delta"],
                )
                public_result = {
                    key: value for key, value in result.items() if not key.startswith("_")
                }
                players = hub.room_players(room_id)
                # The last answer opens the reveal but does not move the match
                # on: `run_match_timer` does that once the pause is over
                await hub.broadcast(players, public_result)

            elif message_type == "match.leave":
                room_id = message.get("match_id")

                if isinstance(room_id, str):
                    ended = await forfeit_player(room_id, user.id)
                    lobby = hub.lobby_message(room_id)

                    if not ended and lobby is not None:
                        await hub.broadcast(hub.room_players(room_id), lobby)

                    await hub.send_to(
                        user.id,
                        {
                            "type": "match.left",
                            "match_id": room_id,
                        },
                    )

            else:
                await ws.send_json({
                    "type": "error",
                    "code": "UNKNOWN_MESSAGE_TYPE",
                })
    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected for user %s", user.id)
    finally:
        became_offline = await hub.disconnect(user.id, ws)

        if became_offline:
            affected_rooms = hub.mark_user_disconnected(user.id)
            for room_id in affected_rooms:
                players = hub.room_players(room_id)
                lobby = hub.lobby_message(room_id)
                await hub.broadcast(
                    players,
                    {
                        "type": "match.player_presence",
                        "match_id": room_id,
                        "user_id": user.id,
                        "connected": False,
                    },
                )
                if lobby is not None:
                    await hub.broadcast(players, lobby)

            if affected_rooms:
                asyncio.create_task(expire_player_after_grace(user.id))

            # an UPDATE, not an attribute write: the account may have just been
            # deleted, and the ORM would raise on flushing a vanished row
            await db.execute(
                update(User)
                .where(User.id == user.id)
                .values(last_seen_at=datetime.now(UTC))
                .execution_options(synchronize_session=False)
            )
            await db.commit()
            await hub.broadcast(
                friends,
                {"type": "presence", "user_id": user.id, "online": False},
            )