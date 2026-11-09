"""Authentication with password"""

from __future__ import annotations

import logging
import secrets

from fastapi import APIRouter, HTTPException, Response, status, Cookie, Request, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, timedelta, UTC
import uuid
from typing import Annotated


from app.config import get_settings
from app.deps import CurrentUser, DbSession, client_ip, rate_limited
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.backup_code import BackupCode
from app.models.enums import OAuthProvider
from app.schemas.user import UserCreate, UserLogin, UserPublic
from app.schemas.auth import TwoFASetupResponse, TwoFAEnableResponse, TwoFAEnableRequest, TwoFAVerifyRequest, TwoFADisableRequest
import base64
import io
import pyotp
import qrcode
from qrcode.image.pil import PilImage
import jwt
from app.services import security
from app.services.ratelimit import login_limiter, register_limiter, totp_limiter, oauth_limiter
from app.services.oauth import GoogleOAuthClient, GithubOAuthClient, FortyTwoOAuthClient, OAuthExchangeError, OAuthClient
from app.models.oauth_account import OAuthAccount


logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])

OAUTH_STATE_COOKIE = "oauth_state"
OAUTH_STATE_PATH = "/api/v1/auth/oauth"
OAUTH_STATE_TTL = 300

def set_access_cookie(response: Response, token: str) -> None:
    """Sets the access token cookie: HttpOnly, Secure, SameSite=Lax"""
    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_TTL,
        path="/",
    )
    response.set_cookie(
        "access_expires_at",
        str(int(datetime.now(UTC).timestamp()) + settings.ACCESS_TOKEN_TTL),
        httponly=False,  # must be visible by JS
        secure=True,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_TTL,
        path="/",
    )


def _conflict_detail(exc: IntegrityError) -> str:
    """Translates a unique-constraint violation into a readable 409 detail

    Uniqueness is left to the database: a SELECT before the INSERT would race
    with a concurrent signup.
    """
    constraint = getattr(getattr(exc.orig, "__cause__", None), "constraint_name", "") or ""
    if "email" in constraint:
        return "email already used"
    if "display_name" in constraint:
        return "display name already used"
    return "uniqueness conflict"


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limited(register_limiter))],
    )
async def register(payload: UserCreate, db: DbSession) -> User:
    user = User(
        email=payload.email,
        display_name=payload.display_name,
        password_hash=await security.hash_password(payload.password),
        terms_accepted_at=datetime.now(UTC),
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail=_conflict_detail(exc)) from exc

    # Mandatory : `role`, `is_active`, `created_at` are server_default
    # `response_model` needs them to exist
    await db.refresh(user)
    return user


def _invalid_credentials() -> HTTPException:
    """One fail whatever the cause

    Unknown email and wrong password must be the same
    status, body and time => `dummy_verify`
    """
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid login")

async def _consume_backup_code(db: AsyncSession, user: User, code: str) -> bool:
    """Try `code` against the user's unused backup codes.

    Argon2 salts each hash, so there is no indexed lookup: every remaining
    code (10 at most) is tried in turn. Rare path, up to ~2 s worst case.
    """
    rows = await db.scalars(
        select(BackupCode).where(BackupCode.user_id == user.id, BackupCode.used_at.is_(None))
    )
    for row in rows:
        if await security.verify_password(code, row.code_hash):
            row.used_at = datetime.now(UTC)
            return True
    return False

@router.post(
    "/login",
    response_model=UserPublic,
    dependencies=[Depends(rate_limited(login_limiter))],
    )
async def login(
    payload: UserLogin, request: Request, response: Response, db: DbSession
    ) -> User | JSONResponse:
    # Limit by account AND IP
    acct_key = f"acct:{payload.email.lower()}"
    if not login_limiter.consume(acct_key):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="too many tries",
            headers={"Retry-After": str(login_limiter.retry_after(acct_key))},
        )

    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or user.password_hash is None:
        # Account doesn't exist, or account pure OAuth : same CPU cost, then same 401
        await security.dummy_verify(payload.password)
        raise _invalid_credentials()
    if not await security.verify_password(payload.password, user.password_hash):
        raise _invalid_credentials()
    if not user.is_active:
        raise _invalid_credentials()
    
    if user.totp_enabled:
        token = security.create_partial_token(user.id)
        mfa_response = JSONResponse({"mfa_required": True}, status_code=status.HTTP_202_ACCEPTED)
        set_mfa_cookie(mfa_response, token)
        # /2fa/verify is CSRF-protected (not in EXEMPT_PREFIXES); without a
        # csrf_token cookie here the browser could never complete the login.
        # Same double-submit token the full session uses.
        set_csrf_cookie(mfa_response, security.generate_csrf_token())
        return mfa_response

    await _issue_session(db, response, user, request)
    return user


@router.get("/me", response_model=UserPublic)
async def me(user: CurrentUser) -> User:
    return user


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        "refresh_token",
        token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_TTL,
        path="/api/v1/auth",
    )


def set_csrf_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        "csrf_token",
        token,
        httponly=False,  # must be visible by JS
        secure=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_TTL,
        path="/",
    )

def set_mfa_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        "mfa_token",
        token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.MFA_TOKEN_TTL,
        path="/api/v1/auth/2fa",
    )

def _clear_auth_cookies(response: Response) -> None:
    """Deletes the auth cookies

    `path` must match the one each cookie was set with, otherwise the refresh
    cookie survives logout and the session can still be refreshed.
    """
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("access_expires_at", path="/")
    response.delete_cookie("refresh_token", path="/api/v1/auth")
    response.delete_cookie("csrf_token", path="/")


async def _issue_session(
    db: AsyncSession,
    response: Response,
    user: User,
    request: Request,
    family_id: uuid.UUID | None = None,
) -> None:
    """Creates pair access+refresh and 3 cookies

    `family_id=None` = new connexion
    `family_id` provided = rotation
    """
    raw = security.generate_opaque_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=security.hash_opaque_token(raw),
            family_id=family_id or uuid.uuid4(),
            expires_at=datetime.now(UTC) + timedelta(seconds=settings.REFRESH_TOKEN_TTL),
            user_agent=(request.headers.get("user-agent") or "")[:255],
            ip=client_ip(request),
        )
    )
    await db.commit()

    set_access_cookie(response, security.create_access_token(user.id, user.role.value))
    set_refresh_cookie(response, raw)
    set_csrf_cookie(response, security.generate_csrf_token())


@router.post("/refresh", response_model=UserPublic)
async def refresh(
    request: Request,
    response: Response,
    db: DbSession,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> User | JSONResponse:
    if refresh_token is None:
        raise _invalid_credentials()

    # FOR UPDATE: otherwise two concurrent /refresh on the same token both
    # read `revoked_at IS NULL` and both pass
    row = await db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == security.hash_opaque_token(refresh_token))
        .with_for_update()
    )
    if row is None:
        raise _invalid_credentials()

    now = datetime.now(UTC)

    # Reuse of a revoked token: either the owner or a thief replayed it, and
    # the two cannot be told apart, so the whole family is revoked
    if row.revoked_at is not None:
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.family_id == row.family_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        await db.commit()
        logger.warning(
            "security.refresh_reuse user_id=%s family_id=%s ip=%s ua=%s",
            row.user_id, row.family_id, client_ip(request),
            request.headers.get("user-agent"),
        )
        revoked = JSONResponse({"detail": "Invalid login"}, status_code=401)
        _clear_auth_cookies(revoked)
        return revoked

    if row.expires_at <= now:
        raise _invalid_credentials()

    user = await db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise _invalid_credentials()

    row.revoked_at = now
    await _issue_session(db, response, user, request, family_id=row.family_id)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: DbSession,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> None:
    if refresh_token:
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == security.hash_opaque_token(refresh_token),
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        await db.commit()
    _clear_auth_cookies(response)

@router.post("/2fa/setup", response_model=TwoFASetupResponse)
async def setup_2fa(user: CurrentUser, db: DbSession) -> TwoFASetupResponse:
    if user.totp_enabled:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="2FA already enabled")

    secret = pyotp.random_base32()
    user.totp_secret_enc = security.encrypt_totp_secret(secret)
    await db.commit()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="Flyana")
    image_obj = qrcode.make(uri, image_factory=PilImage)
    buffer = io.BytesIO()
    image_obj.save(buffer, format="PNG")
    png_bytes = buffer.getvalue()
    qr_b64 = base64.b64encode(png_bytes).decode()
    return TwoFASetupResponse(otpauth_uri=uri, qr_code_png_base64=qr_b64)

@router.post("/2fa/enable"
            , response_model=TwoFAEnableResponse
            , dependencies=[Depends(rate_limited(totp_limiter))],
            )
async def enable_2fa(
    payload: TwoFAEnableRequest, user: CurrentUser, db: DbSession
) -> TwoFAEnableResponse:
    if user.totp_enabled:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="2FA already enabled")
    if user.totp_secret_enc is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="call /2fa/setup first")

    secret = security.decrypt_totp_secret(user.totp_secret_enc)
    if not pyotp.TOTP(secret).verify(payload.code, valid_window=1):
        raise HTTPException(400, "invalid code")

    user.totp_enabled = True

    plain_codes: list[str] = []

    for _ in range(10):
        code = security.generate_backup_code()
        db.add(BackupCode(user_id=user.id, code_hash=await security.hash_password(code)))
        plain_codes.append(code)

    await db.commit()
    return TwoFAEnableResponse(backup_codes=plain_codes)

@router.post("/2fa/verify",
             response_model=UserPublic,
             dependencies=[Depends(rate_limited(totp_limiter))],
            )
async def verify_2fa(
    payload: TwoFAVerifyRequest,
    request: Request,
    response: Response,
    db: DbSession,
    mfa_token: Annotated[str | None, Cookie()] = None,
) -> User:
    if mfa_token is None:
        raise _invalid_credentials()

    try:
        claims = security.decode_token(mfa_token, expected_typ="mfa")
    except jwt.InvalidTokenError:
        raise _invalid_credentials()

    user = await db.get(User, int(claims["sub"]))
    if user is None or not user.is_active or not user.totp_enabled or user.totp_secret_enc is None:
        raise _invalid_credentials()

    secret = security.decrypt_totp_secret(user.totp_secret_enc)
    if not pyotp.TOTP(secret).verify(payload.code, valid_window=1):
        if not await _consume_backup_code(db, user, payload.code):
            raise HTTPException(400, "invalid code")

    await _issue_session(db, response, user, request)
    return user


@router.delete("/2fa",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(rate_limited(totp_limiter))],
               )
async def disable_2fa(payload: TwoFADisableRequest, user: CurrentUser, db: DbSession) -> None:
    if not user.totp_enabled or user.totp_secret_enc is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="2FA not enabled")
    if not await security.verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid password")

    secret = security.decrypt_totp_secret(user.totp_secret_enc)
    if not pyotp.TOTP(secret).verify(payload.code, valid_window=1):
        if not await _consume_backup_code(db, user, payload.code):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid code")
    
    user.totp_enabled = False
    user.totp_secret_enc = None
    await db.execute(delete(BackupCode).where(BackupCode.user_id == user.id))

    await db.commit()

def _oauth_client(provider: OAuthProvider) -> OAuthClient:
    """Builds the client for one provider from settings"""
    if provider == OAuthProvider.google:
        return GoogleOAuthClient(settings)
    elif provider == OAuthProvider.github:
        return GithubOAuthClient(settings)
    elif provider == OAuthProvider.fortytwo:
        return FortyTwoOAuthClient(settings)

import re

def _slugify_display_name(hint: str) -> str:
    """Turns a provider's display name hint into a valid display_name"""
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "", hint)[:24]
    if len(cleaned) < 3:
        cleaned = (cleaned + secrets.token_hex(4))[:24]
    return cleaned

def _oauth_configured(provider: OAuthProvider) -> bool:
    """Whether this provider has both its id and its secret in the settings"""
    credentials = {
        OAuthProvider.google: (settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET),
        OAuthProvider.github: (settings.GITHUB_CLIENT_ID, settings.GITHUB_CLIENT_SECRET),
        OAuthProvider.fortytwo: (settings.FORTYTWO_CLIENT_ID, settings.FORTYTWO_CLIENT_SECRET),
    }
    return all(credentials[provider])


def _oauth_error_redirect() -> RedirectResponse:
    """The single redirect used for every failed oauth attempt"""
    redirect = RedirectResponse("/login?error=oauth", status_code=status.HTTP_302_FOUND)
    redirect.delete_cookie(OAUTH_STATE_COOKIE, path=OAUTH_STATE_PATH)
    return redirect

@router.get("/oauth/{provider}/authorize", dependencies=[Depends(rate_limited(oauth_limiter))])
async def oauth_authorize(provider: OAuthProvider) -> RedirectResponse:
    """Redirects the browser to the provider's consent screen"""
    # An empty id would send the student to the provider's own error page, with
    # no way back: a button for a provider nobody configured stays harmless
    if not _oauth_configured(provider):
        return _oauth_error_redirect()

    client = _oauth_client(provider)
    state = security.generate_csrf_token()
    redirect = RedirectResponse(client.authorize_url(state), status_code=status.HTTP_302_FOUND)
    redirect.set_cookie(
        OAUTH_STATE_COOKIE,
        state,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=OAUTH_STATE_TTL,
        path=OAUTH_STATE_PATH,
    )
    return redirect

async def _resolve_oauth_user(db: DbSession, provider: OAuthProvider, identity) -> User:
    """Finds the existing account for this identity, links it, or creates it"""
    """-> compte deja lié"""
    oauth_account = await db.scalar(select(OAuthAccount).where(
        OAuthAccount.provider == provider,
        OAuthAccount.provider_account_id == identity.provider_account_id,
    ))
    if oauth_account is not None:
        linked = await db.get(User, oauth_account.user_id)
        # A missing row here means the account was deleted without its link:
        # fall through and rebuild it rather than answering with a 500
        if linked is not None:
            return linked
    
    """-> email deja existant, on le lie"""
    # Safe only because every client refuses an address the provider has not
    # verified: otherwise publishing someone's address would hand over their account
    user = await db.scalar(select(User).where(User.email == identity.email))
    if user is not None:
        db.add(OAuthAccount(
            user_id=user.id,
            provider = provider,
            provider_account_id=identity.provider_account_id,
        ))
        await db.commit()
        return user

    """-> creation de compte oauth"""
    base_name = _slugify_display_name(identity.display_name_hint)
    display_name = base_name

    for _ in range(5):
        user = User(
            email=identity.email,
            display_name=display_name,
            password_hash=None,
            email_verified_at=datetime.now(UTC),
            terms_accepted_at=datetime.now(UTC),
        )
        db.add(user)
        try:
            await db.flush()
        except IntegrityError as exc:
            await db.rollback()
            if _conflict_detail(exc) != "display name already used":
                raise
            display_name = f"{base_name[:19]}-{secrets.token_hex(2)}"
            continue

        db.add(OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_account_id=identity.provider_account_id,
        ))
        await db.commit()
        await db.refresh(user)
        return user

    raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "could not allocate display_name")


@router.get("/oauth/{provider}/callback", dependencies=[Depends(rate_limited(oauth_limiter))])
async def oauth_callback(
    provider: OAuthProvider,
    request: Request,
    db: DbSession,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    oauth_state: Annotated[str | None, Cookie()] = None,
) -> RedirectResponse:
    """Finishes the OAuth flow: exchanges the code, finds or creates the user, opens a session"""
    if error or not code or not state or not oauth_state or state != oauth_state:
        return _oauth_error_redirect()

    client = _oauth_client(provider)
    try:
        identity = await client.fetch_identity(code)
    except OAuthExchangeError as exc:
        logger.warning("oauth.exchange_failed provider=%s err=%s", provider.value, exc)
        return _oauth_error_redirect()

    user = await _resolve_oauth_user(db, provider, identity)
    if not user.is_active:
        return _oauth_error_redirect()

    redirect = RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)
    redirect.delete_cookie(OAUTH_STATE_COOKIE, path=OAUTH_STATE_PATH)
    await _issue_session(db, redirect, user, request) 
    return redirect

