"""Shared social-graph queries"""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import FriendshipStatus
from app.models.friendship import Friendship
from app.schemas.user import FriendshipView


def _pair(a: int, b: int):
    """A WHERE clause matching the friendship row for an unordered pair"""
    return or_(
        (Friendship.requester_id == a) & (Friendship.addressee_id == b),
        (Friendship.requester_id == b) & (Friendship.addressee_id == a),
    )


async def friend_ids(db: AsyncSession, user_id: int) -> list[int]:
    """Ids of every accepted friend, whichever side sent the request"""
    rows = await db.scalars(
        select(Friendship).where(
            (Friendship.requester_id == user_id)
            | (Friendship.addressee_id == user_id),
            Friendship.status == FriendshipStatus.accepted,
        )
    )
    return [
        row.addressee_id if row.requester_id == user_id else row.requester_id
        for row in rows
    ]


async def blocked_between(db: AsyncSession, a: int, b: int) -> bool:
    """Whether either user has blocked the other

    One `blocked` row covers both directions: the block is symmetric in effect
    even though `requester_id` records who set it.
    """
    row = await db.scalar(
        select(Friendship).where(_pair(a, b), Friendship.status == FriendshipStatus.blocked)
    )
    return row is not None


def _view_of(row: Friendship | None, me: int) -> FriendshipView:
    if row is None:
        return "none"
    if row.status == FriendshipStatus.accepted:
        return "friends"
    if row.status == FriendshipStatus.blocked:
        return "blocked"
    return "pending_out" if row.requester_id == me else "pending_in"


async def friendship_state(
    db: AsyncSession, me: int, other: int
) -> tuple[FriendshipView, int | None]:
    """`friendship_view` plus the row id, so a profile view can wire its
    accept / decline / remove button straight to `/friends/{id}` without a
    second round trip"""
    if me == other:
        return "none", None
    row = await db.scalar(select(Friendship).where(_pair(me, other)))
    return _view_of(row, me), (row.id if row is not None else None)
