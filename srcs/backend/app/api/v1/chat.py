"""Direct chat between two users

Persistence is REST (`POST /chat/messages`); the WebSocket is only a live
mirror. Every message is written by the POST, then pushed to the recipient and
to the sender's other tabs as a `chat.message` frame. A client that missed a
frame (offline, just logged in) recovers the full state from `GET /chat/...` —
the socket never carries state the REST API cannot rebuild.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import case, func, or_, select, update
from sqlalchemy.engine import CursorResult

from app.deps import CurrentUser, DbSession
from app.models.message import DirectMessage
from app.models.user import User
from app.schemas.chat import ConversationOut, MessageCreate, MessageOut, MessagePage
from app.schemas.user import UserSummary
from app.services.ratelimit import message_limiter
from app.services.realtime import hub
from app.services.social import blocked_between

router = APIRouter(prefix="/chat", tags=["chat"])


def _pair(a: int, b: int):
    """WHERE clause matching every message exchanged between two users"""
    return or_(
        (DirectMessage.sender_id == a) & (DirectMessage.recipient_id == b),
        (DirectMessage.sender_id == b) & (DirectMessage.recipient_id == a),
    )


def _frame(message: DirectMessage) -> dict:
    """The `chat.message` WebSocket frame for a freshly stored message"""
    return {
        "type": "chat.message",
        "message": MessageOut.model_validate(message).model_dump(mode="json"),
    }


@router.post(
    "/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(payload: MessageCreate, user: CurrentUser, db: DbSession):
    """Sends a message to another user

    Anyone may message anyone who has not blocked them — friendship is not
    required, matching the "basic chat system" wording of the subject.
    """
    me = user.id
    other = payload.recipient_id
    if other == me:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid recipient")

    key = f"msg:{me}"
    if not message_limiter.consume(key):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="slow down",
            headers={"Retry-After": str(message_limiter.retry_after(key))},
        )

    recipient = await db.get(User, other)
    if recipient is None or not recipient.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="recipient not found")
    if await blocked_between(db, me, other):
        # same answer whether they blocked you or you blocked them
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="unavailable")

    row = DirectMessage(sender_id=me, recipient_id=other, body=payload.body)
    db.add(row)
    await db.commit()
    await db.refresh(row)

    frame = _frame(row)
    await hub.send_to(other, frame)
    await hub.send_to(me, frame)  # keep the sender's other tabs in sync
    return row


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(user: CurrentUser, db: DbSession):
    """Every thread you are part of, most-recently-active first"""
    me = user.id
    peer = case(
        (DirectMessage.sender_id == me, DirectMessage.recipient_id),
        else_=DirectMessage.sender_id,
    ).label("peer")

    # Postgres DISTINCT ON: the first ORDER BY term must be the distinct
    # expression, the rest picks which row survives per peer (the newest).
    latest_stmt = (
        select(DirectMessage, peer)
        .where(or_(DirectMessage.sender_id == me, DirectMessage.recipient_id == me))
        .order_by(peer, DirectMessage.created_at.desc(), DirectMessage.id.desc())
        .distinct(peer)
    )
    latest = (await db.execute(latest_stmt)).all()

    unread_rows = await db.execute(
        select(DirectMessage.sender_id, func.count())
        .where(DirectMessage.recipient_id == me, DirectMessage.read_at.is_(None))
        .group_by(DirectMessage.sender_id)
    )
    unread: dict[int, int] = {sender_id: n for sender_id, n in unread_rows.all()}

    peers = await db.scalars(
        select(User).where(User.id.in_([peer_id for _, peer_id in latest]))
    )
    users = {u.id: u for u in peers}

    convos = [
        ConversationOut(
            user=UserSummary.model_validate(users[peer_id]),
            last_message=MessageOut.model_validate(message),
            unread=unread.get(peer_id, 0),
        )
        for message, peer_id in latest
        if peer_id in users
    ]
    convos.sort(key=lambda c: c.last_message.created_at, reverse=True)
    return convos


@router.get("/with/{user_id}", response_model=MessagePage)
async def thread(
    user_id: int,
    user: CurrentUser,
    db: DbSession,
    before: int | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
):
    """The message history with one user, oldest-first, newest page first

    Pass the previous response's `next_before` as `?before=` to walk further
    back. Opening a thread also marks that user's messages to you as read and
    tells them so over the socket.
    """
    me = user.id
    stmt = (
        select(DirectMessage)
        .where(_pair(me, user_id))
        .order_by(DirectMessage.id.desc())
        .limit(limit + 1)  # one extra row is the "is there more" probe
    )
    if before is not None:
        stmt = stmt.where(DirectMessage.id < before)
    rows = list(await db.scalars(stmt))

    has_more = len(rows) > limit
    rows = rows[:limit]
    next_before = rows[-1].id if has_more else None

    marked = cast(
        CursorResult[Any],
        await db.execute(
            update(DirectMessage)
            .where(
                DirectMessage.recipient_id == me,
                DirectMessage.sender_id == user_id,
                DirectMessage.read_at.is_(None),
            )
            .values(read_at=datetime.now(UTC))
        ),
    )
    await db.commit()
    if marked.rowcount:
        await hub.send_to(user_id, {"type": "chat.read", "user_id": me})

    items = [MessageOut.model_validate(m) for m in reversed(rows)]
    return MessagePage(items=items, next_before=next_before)


@router.post("/with/{user_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(user_id: int, user: CurrentUser, db: DbSession) -> None:
    """Marks every message from `user_id` as read without fetching the thread"""
    me = user.id
    marked = cast(
        CursorResult[Any],
        await db.execute(
            update(DirectMessage)
            .where(
                DirectMessage.recipient_id == me,
                DirectMessage.sender_id == user_id,
                DirectMessage.read_at.is_(None),
            )
            .values(read_at=datetime.now(UTC))
        ),
    )
    await db.commit()
    if marked.rowcount:
        await hub.send_to(user_id, {"type": "chat.read", "user_id": me})
