"""Profile and avatar"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import delete, exists, func, select
from sqlalchemy.exc import IntegrityError

from app.api.v1.auth import _clear_auth_cookies
from app.deps import CurrentUser, DbSession, rate_limited
from app.models.match import Match, MatchPlayer
from app.models.user import User
from app.schemas.user import AccountDeleteRequest, ProfileOut, UserPublic, UserSummary, UserUpdate
from app.services import security
from app.services.ratelimit import login_limiter
from app.schemas.user import UserPublic, UserUpdate
from app.services import media
from app.services.realtime import hub
from app.services.social import friendship_state

from app.models.gamification import Achievement, UserAchievement
from app.schemas.gamification import AchievementOut, UserStats
from app.models.attempt import Attempt

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me", response_model=UserPublic)
async def update_me(payload: UserUpdate, user: CurrentUser, db: DbSession):
    """Edits your own display name bio or language

    Only the fields listed in `UserUpdate` can be written
    so a client cannot promote itself by sending `role`
    """
    # exclude_unset : partial PATCH would erase bio with None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="name already taken"
        ) from exc
    await db.refresh(user)
    return user

@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limited(login_limiter))],
)
async def delete_me(
    payload: AccountDeleteRequest, response: Response, user: CurrentUser, db: DbSession
) -> None:
    """Deletes your account and everything tied to it, for good

    Every table pointing at `users` is `ON DELETE CASCADE` (attempts, friends,
    messages, tokens, 2FA codes, OAuth links, achievements, match results), so
    deleting the row is the deletion. Authored content is `SET NULL`: questions
    stay, without their author.
    """
    if payload.confirmation != user.display_name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="confirmation mismatch")
    if user.password_hash is not None and not await security.verify_password(
        payload.password or "", user.password_hash
    ):
        raise HTTPException(401, "Invalid password")
    # The in-memory room would keep scoring a user the database no longer has
    if hub.user_rooms(user.id):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="leave your match first")

    user_id = user.id
    avatar_path = user.avatar_path
    match_ids = (
        await db.scalars(select(MatchPlayer.match_id).where(MatchPlayer.user_id == user_id))
    ).all()

    await db.delete(user)
    await db.flush()
    # A match nobody is left in is just a husk: drop it with its questions
    if match_ids:
        await db.execute(
            delete(Match).where(
                Match.id.in_(match_ids),
                ~exists().where(MatchPlayer.match_id == Match.id),
            )
        )
    await db.commit()

    await media.delete_avatar(avatar_path)
    await hub.close_user(user_id)
    _clear_auth_cookies(response)

@router.post("/me/avatar", response_model=UserPublic)
async def upload_avatar(
    user: CurrentUser, db: DbSession, file: UploadFile = File(...)
):
    """Replaces your avatar with an uploaded image

    Caps the size then re encodes to WebP
    Re encoding is what strips metadata and any payload hidden in the file
    """
    raw = await media.read_limited(file)
    processed = await media.process_avatar(raw)
    user.avatar_path = await media.save_avatar(processed)
    await db.commit()
    await db.refresh(user)
    return user

@router.get("/me/achievements", response_model=list[AchievementOut])
async def my_achievements(user: CurrentUser, db: DbSession):
    """Every achievement of the catalog, with your unlock date or None"""
    result = await db.execute(
        select(Achievement.code, Achievement.icon, UserAchievement.earned_at)
        .outerjoin(
            UserAchievement,
            (UserAchievement.achievement_id == Achievement.id)
            & (UserAchievement.user_id == user.id),
        )
        .order_by(Achievement.id)
    )
    return result.all()

@router.get("", response_model=list[UserSummary])
async def search_users(
    user: CurrentUser,
    db: DbSession,
    q: str = Query(min_length=1, max_length=32),
    limit: int = Query(default=10, ge=1, le=25),
):
    """Finds users by a display-name fragment, to add a friend or start a chat"""
    rows = await db.scalars(
        select(User)
        .where(
            User.id != user.id,
            User.is_active.is_(True),
            func.lower(User.display_name).contains(q.lower()),
        )
        .order_by(User.display_name)
        .limit(limit)
    )
    return list(rows)


@router.get("/{user_id}", response_model=ProfileOut)
async def get_profile(user_id: int, viewer: CurrentUser, db: DbSession):
    """Public profile of one user, plus where the viewer stands with them"""
    target = await db.get(User, user_id)
    if target is None or not target.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user not found")
    view, friendship_id = await friendship_state(db, viewer.id, target.id)
    return ProfileOut(
        id=target.id,
        display_name=target.display_name,
        avatar_path=target.avatar_path,
        bio=target.bio,
        role=target.role,
        created_at=target.created_at,
        online=hub.is_online(target.id),
        friendship=view,
        friendship_id=friendship_id,
    )


@router.get("/{user_id}/avatar")
async def get_avatar(user_id: int, db: DbSession):
    """Serves the generated fallback avatar; uploaded ones are served by nginx"""
    return Response(
        media.identicon(user_id),
        media_type="image/webp",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/me/stats", response_model=UserStats)
async def my_stats(user: CurrentUser, db: DbSession) -> UserStats:
    """Questions solved, and questions tried but never solved

    Counted per question: three misses then a success make one solved exercise
    """
    per_question = (
        select(func.bool_or(Attempt.is_correct).label("solved"))
        .where(Attempt.user_id == user.id)
        .group_by(Attempt.question_id)
        .subquery()
    )
    solved, to_review = (
        await db.execute(
            select(
                func.count().filter(per_question.c.solved.is_(True)),
                # IS NOT TRUE, not == False: bool_or skips NULLs, so a question
                # whose only attempts await self-assessment comes out NULL
                func.count().filter(per_question.c.solved.is_not(True)),
            )
        )
    ).one()
    return UserStats(solved=solved, to_review=to_review)