"""Friends: requests, the friend list, and blocking"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from app.deps import CurrentUser, DbSession
from app.models.enums import FriendshipStatus
from app.models.friendship import Friendship
from app.models.user import User
from app.schemas.friends import (
    BlockCreate,
    FriendActionOut,
    FriendListOut,
    FriendOut,
    FriendRequestCreate,
    PendingRequestOut,
    PendingRequestsOut,
)
from app.schemas.user import UserSummary
from app.services.realtime import hub

router = APIRouter(prefix="/friends", tags=["friends"])


async def _users_by_id(db: DbSession, ids: list[int]) -> dict[int, User]:
    """Loads the given users in one query, keyed by id"""
    if not ids:
        return {}
    rows = await db.scalars(select(User).where(User.id.in_(ids)))
    return {u.id: u for u in rows}


@router.post(
    "/requests",
    response_model=FriendActionOut,
    status_code=status.HTTP_201_CREATED,
)
async def send_request(payload: FriendRequestCreate, user: CurrentUser, db: DbSession):
    """Sends a friend request to another user

    Answers `pending` normally.
    Answers `accepted` straight away if that user had already asked you.

    No pre-check: attempt the INSERT and let the canonical `(LEAST, GREATEST)`
    index tell us a row already exists. Between a SELECT and an INSERT another
    request could create the same pair, so the DB is the only safe arbiter.
    """
    # Snapshot the id BEFORE the commit: `rollback()` expires every ORM object
    # of the session, and reading `user.id` afterwards fires a lazy reload — IO
    # outside the greenlet, i.e. MissingGreenlet and a 500 on exactly the path
    # this endpoint exists to handle.
    me = user.id
    other = payload.addressee_id
    row = Friendship(requester_id=me, addressee_id=other)
    db.add(row)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        existing = await db.scalar(
            select(Friendship).where(
                or_(
                    (Friendship.requester_id == me) & (Friendship.addressee_id == other),
                    (Friendship.requester_id == other) & (Friendship.addressee_id == me),
                )
            )
        )
        if existing is None:
            # CHECK not_self, or the addressee does not exist (FK)
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid request")
        if existing.status == FriendshipStatus.blocked:
            # Do not confirm who blocked whom
            raise HTTPException(status.HTTP_409_CONFLICT, detail="unavailable")
        if (
            existing.requester_id == other
            and existing.status == FriendshipStatus.pending
        ):
            existing.status = FriendshipStatus.accepted
            existing.responded_at = datetime.now(UTC)
            await db.commit()
            await hub.send_to(other, {"type": "friend.accepted", "user_id": me})
            return FriendActionOut(status="accepted", friendship_id=existing.id)
        raise HTTPException(status.HTTP_409_CONFLICT, detail="request already exists")

    await db.refresh(row)
    await hub.send_to(other, {"type": "friend.request", "user_id": me})
    return FriendActionOut(status="pending", friendship_id=row.id)


@router.post("/requests/{friendship_id}/accept", response_model=FriendActionOut)
async def accept(friendship_id: int, user: CurrentUser, db: DbSession):
    """Accepts a pending request addressed to you

    Only the addressee can accept. 404 rather than 403 so nothing confirms the
    request exists to someone who is not part of it.
    """
    row = await db.get(Friendship, friendship_id)
    if row is None or row.addressee_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="cannot be found")
    if row.status != FriendshipStatus.pending:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="already handled")
    other = row.requester_id
    row.status = FriendshipStatus.accepted
    row.responded_at = datetime.now(UTC)
    await db.commit()
    await hub.send_to(other, {"type": "friend.accepted", "user_id": user.id})
    return FriendActionOut(status="accepted", friendship_id=friendship_id)


@router.delete("/{friendship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove(friendship_id: int, user: CurrentUser, db: DbSession) -> None:
    """Deletes a friendship or cancels a request

    Works from either side. A `blocked` row is not removed here — use
    `DELETE /friends/block/{user_id}`, which only the blocker may call.
    """
    row = await db.get(Friendship, friendship_id)
    if row is None or user.id not in (row.requester_id, row.addressee_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="cannot be found")
    if row.status == FriendshipStatus.blocked:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="blocked")
    await db.delete(row)
    await db.commit()


@router.get("", response_model=FriendListOut)
async def list_friends(user: CurrentUser, db: DbSession):
    """Lists your accepted friends, whichever side sent the request"""
    rows = await db.scalars(
        select(Friendship).where(
            or_(Friendship.requester_id == user.id, Friendship.addressee_id == user.id),
            Friendship.status == FriendshipStatus.accepted,
        )
    )
    pairs = [
        (row.id, row.addressee_id if row.requester_id == user.id else row.requester_id)
        for row in rows
    ]
    others = await _users_by_id(db, [oid for _, oid in pairs])
    return FriendListOut(
        items=[
            FriendOut(
                friendship_id=fid,
                user=UserSummary.model_validate(others[oid]),
                # a friend can be online without ever having disconnected
                # (`last_seen_at` only moves on disconnect), so ask the hub first
                online=hub.is_online(oid),
                last_seen_at=others[oid].last_seen_at,
            )
            for fid, oid in pairs
            if oid in others
        ]
    )


@router.get("/requests", response_model=PendingRequestsOut)
async def list_requests(user: CurrentUser, db: DbSession):
    """Every pending request touching you, split by direction"""
    rows = list(
        await db.scalars(
            select(Friendship).where(
                or_(
                    Friendship.requester_id == user.id,
                    Friendship.addressee_id == user.id,
                ),
                Friendship.status == FriendshipStatus.pending,
            )
        )
    )
    other_ids = [
        r.addressee_id if r.requester_id == user.id else r.requester_id for r in rows
    ]
    others = await _users_by_id(db, other_ids)

    def entry(r: Friendship, other_id: int) -> PendingRequestOut:
        return PendingRequestOut(
            friendship_id=r.id,
            user=UserSummary.model_validate(others[other_id]),
            created_at=r.created_at,
        )

    return PendingRequestsOut(
        incoming=[
            entry(r, r.requester_id)
            for r in rows
            if r.addressee_id == user.id and r.requester_id in others
        ],
        outgoing=[
            entry(r, r.addressee_id)
            for r in rows
            if r.requester_id == user.id and r.addressee_id in others
        ],
    )


@router.post("/block", response_model=FriendActionOut)
async def block(payload: BlockCreate, user: CurrentUser, db: DbSession):
    """Blocks a user: drops any friendship and stops messages both ways

    Upserts the pair row to `blocked` with `requester_id` = the blocker. A
    blocked pair disappears from both friend lists and `chat.py` refuses to
    deliver between them.
    """
    me = user.id
    other = payload.user_id
    if me == other:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid request")
    row = await db.scalar(
        select(Friendship).where(
            or_(
                (Friendship.requester_id == me) & (Friendship.addressee_id == other),
                (Friendship.requester_id == other) & (Friendship.addressee_id == me),
            )
        )
    )
    if row is None:
        row = Friendship(requester_id=me, addressee_id=other)
        db.add(row)
    else:
        # take ownership so only this caller can lift the block
        row.requester_id = me
        row.addressee_id = other
    row.status = FriendshipStatus.blocked
    row.responded_at = datetime.now(UTC)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="invalid request"
        ) from exc
    await db.refresh(row)
    return FriendActionOut(status="blocked", friendship_id=row.id)


@router.delete("/block/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unblock(user_id: int, user: CurrentUser, db: DbSession) -> None:
    """Lifts a block. Only the user who set it may call this."""
    row = await db.scalar(
        select(Friendship).where(
            Friendship.requester_id == user.id,
            Friendship.addressee_id == user_id,
            Friendship.status == FriendshipStatus.blocked,
        )
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="cannot be found")
    await db.delete(row)
    await db.commit()
