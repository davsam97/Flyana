from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import engine, get_db
from app.main import app
from app.models.user import User
from app.services.ratelimit import grading_limiter, login_limiter, register_limiter, totp_limiter
from app.services.attempts import llm_budget
from app.services.security import hash_password


@pytest.fixture(autouse=True)
def reset_rate_limiters() -> None:
    """Empties the token buckets before every test.

    They are module-level singletons and every test shares one client IP, so
    without this a test's outcome would depend on collection order (429s).
    """
    for limiter in (login_limiter, register_limiter, totp_limiter, grading_limiter):
        limiter._buckets.clear()
    llm_budget.clear()


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """One test, one Postgres transaction, rolled back at teardown.

    `join_transaction_mode="create_savepoint"`: a route's `db.commit()` only
    releases a SAVEPOINT, so the outer transaction is still there to roll back.
    """
    async with engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(
            bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()


@pytest.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """In-process httpx client with `get_db` swapped for the test session

    `https://` because the auth cookies are `Secure` and httpx would not
    resend them over `http://`.
    """
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def user_factory(
    db: AsyncSession,
) -> Callable[..., Awaitable[tuple[User, str]]]:
    """Inserts a `User` row directly (bypassing `/auth/register`)."""

    async def _make(
        *,
        display_name: str = "testuser",
        email: str = "test@example.com",
        password: str = "correcthorsebatterystaple",
        **extra: object,
    ) -> tuple[User, str]:
        user = User(
            display_name=display_name,
            email=email,
            password_hash=await hash_password(password),
            **extra,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user, password

    return _make


@pytest.fixture
def as_user(
    client: AsyncClient,
    user_factory: Callable[..., Awaitable[tuple[User, str]]],
) -> Callable[..., Awaitable[User]]:
    """Creates a user and logs the shared client in as them.

    Calling it again switches the shared client to another user. Also copies
    the `csrf_token` cookie into `X-CSRF-Token`, as the frontend does.
    """

    async def _login(**kwargs: object) -> User:
        user, password = await user_factory(**kwargs)
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": password},
        )
        assert r.status_code == 200, r.text
        client.headers["x-csrf-token"] = client.cookies["csrf_token"]
        return user

    return _login


@pytest.fixture
def login(client: AsyncClient) -> Callable[..., Awaitable[None]]:
    """Switches the shared client to an already-created user."""

    async def _login(
        email: str, password: str = "correcthorsebatterystaple"
    ) -> None:
        r = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        assert r.status_code == 200, r.text
        client.headers["x-csrf-token"] = client.cookies["csrf_token"]

    return _login
