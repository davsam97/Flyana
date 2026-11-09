from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from app.config import get_settings


class TestRegister:
    async def test_success(self, client: AsyncClient) -> None:
        r = await client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "alice",
                "email": "alice@example.com",
                "password": "Correct-horse-battery-9",
                "accept_terms": True,
            },
        )
        assert r.status_code == 201
        body = r.json()
        assert body["display_name"] == "alice"
        assert body["email"] == "alice@example.com"
        assert body["role"] == "student"
        assert "password_hash" not in body

    async def test_duplicate_email_is_case_insensitive(self, client: AsyncClient, user_factory) -> None:
        await user_factory(email="bob@example.com", display_name="bob")

        r = await client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "someone_else",
                "email": "BOB@EXAMPLE.com",
                "password": "Correct-horse-battery-9",
                "accept_terms": True,
            },
        )
        assert r.status_code == 409
        assert r.json()["detail"] == "email already used"

    async def test_duplicate_display_name(self, client: AsyncClient, user_factory) -> None:
        await user_factory(display_name="carol", email="carol@example.com")

        r = await client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "carol",
                "email": "other@example.com",
                "password": "Correct-horse-battery-9",
                "accept_terms": True,
            },
        )
        assert r.status_code == 409
        assert r.json()["detail"] == "display name already used"

    @pytest.mark.parametrize(
        "password,expected_status",
        [
            pytest.param("Trombone9", 422, id="9-chars-rejected"),
            pytest.param("Trombone-9", 201, id="10-chars-accepted"),
        ],
    )
    async def test_password_length_boundary(
        self, client: AsyncClient, password: str, expected_status: int
    ) -> None:
        r = await client.post(
            "/api/v1/auth/register",
            json={"display_name": "boundary", "email": "boundary@example.com", "password": password, "accept_terms": True},
        )
        assert r.status_code == expected_status

    @pytest.mark.parametrize(
        "password",
        [
            pytest.param("TROMBONE-99", id="no-lowercase"),
            pytest.param("trombone-99", id="no-uppercase"),
            pytest.param("Trombone-xx", id="no-digit"),
            pytest.param("Trombone999", id="no-special"),
        ],
    )
    async def test_password_needs_every_class(self, client: AsyncClient, password: str) -> None:
        r = await client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "weakling",
                "email": "weakling@example.com",
                "password": password,
                "accept_terms": True,
            },
        )
        assert r.status_code == 422

    @pytest.mark.parametrize(
        "extra",
        [pytest.param({}, id="missing"), pytest.param({"accept_terms": False}, id="refused")],
    )
    async def test_terms_must_be_accepted(self, client: AsyncClient, extra: dict) -> None:
        r = await client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "noterms",
                "email": "noterms@example.com",
                "password": "Correct-horse-battery-9",
                **extra,
            },
        )
        assert r.status_code == 422


class TestLogin:
    async def test_success_sets_cookies(self, client: AsyncClient, user_factory) -> None:
        _, password = await user_factory(email="dave@example.com", display_name="dave")

        r = await client.post("/api/v1/auth/login", json={"email": "dave@example.com", "password": password})

        assert r.status_code == 200
        assert "access_token" in client.cookies
        assert "refresh_token" in client.cookies

    async def test_wrong_password(self, client: AsyncClient, user_factory) -> None:
        await user_factory(email="erin@example.com", display_name="erin")

        r = await client.post(
            "/api/v1/auth/login", json={"email": "erin@example.com", "password": "definitely wrong"}
        )
        assert r.status_code == 401
        assert r.json()["detail"] == "Invalid login"

    async def test_unknown_email_gives_same_message_as_wrong_password(self, client: AsyncClient) -> None:
        r = await client.post(
            "/api/v1/auth/login", json={"email": "ghost@example.com", "password": "whatever123"}
        )
        assert r.status_code == 401
        assert r.json()["detail"] == "Invalid login"

    async def test_disabled_account(self, client: AsyncClient, user_factory) -> None:
        _, password = await user_factory(email="frank@example.com", display_name="frank", is_active=False)

        r = await client.post("/api/v1/auth/login", json={"email": "frank@example.com", "password": password})
        assert r.status_code == 401


class TestAccessDeadline:
    """`access_expires_at`: the access cookie's deadline, in clear

    The token is HttpOnly, so without this the frontend cannot tell that a page
    holding only a websocket open is about to lose its session
    """

    @staticmethod
    def _set_cookie(response, name: str) -> str:
        """The raw `Set-Cookie` line for `name`, so its flags can be read"""
        line = next(
            (
                header
                for header in response.headers.get_list("set-cookie")
                if header.startswith(f"{name}=")
            ),
            None,
        )
        assert line is not None, f"{name} was not set"
        return line

    async def test_login_advertises_the_deadline_in_a_readable_cookie(
        self, client: AsyncClient, user_factory
    ) -> None:
        _, password = await user_factory(email="deadline@example.com", display_name="dl")
        before = int(datetime.now(UTC).timestamp())

        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "deadline@example.com", "password": password},
        )

        assert r.status_code == 200, r.text
        ttl = get_settings().ACCESS_TOKEN_TTL
        deadline = int(client.cookies["access_expires_at"])
        # the deadline the token itself carries, give or take the round trip
        assert before + ttl <= deadline <= int(datetime.now(UTC).timestamp()) + ttl

    async def test_the_deadline_is_readable_while_the_token_is_not(
        self, client: AsyncClient, user_factory
    ) -> None:
        """The whole point: JS must be able to read one and never the other"""
        _, password = await user_factory(email="flags@example.com", display_name="fl")

        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "flags@example.com", "password": password},
        )

        assert "httponly" in self._set_cookie(r, "access_token").lower()
        assert "httponly" not in self._set_cookie(r, "access_expires_at").lower()

    async def test_a_refresh_pushes_the_deadline_back(
        self, client: AsyncClient, as_user
    ) -> None:
        await as_user(email="refreshed@example.com", display_name="rf")
        first = int(client.cookies["access_expires_at"])

        r = await client.post("/api/v1/auth/refresh")

        assert r.status_code == 200, r.text
        assert int(client.cookies["access_expires_at"]) >= first

    async def test_logout_takes_the_deadline_with_it(
        self, client: AsyncClient, as_user
    ) -> None:
        """Left behind, it would schedule a refresh for a session that is gone"""
        await as_user(email="goodbye@example.com", display_name="bye")
        assert "access_expires_at" in client.cookies

        r = await client.post("/api/v1/auth/logout")

        assert r.status_code in (200, 204), r.text
        assert "access_expires_at" not in client.cookies


class TestMe:
    async def test_without_cookie(self, client: AsyncClient) -> None:
        r = await client.get("/api/v1/auth/me")
        assert r.status_code == 401

    async def test_with_garbage_cookie(self, client: AsyncClient) -> None:
        client.cookies.set("access_token", "not-a-real-jwt")
        r = await client.get("/api/v1/auth/me")
        assert r.status_code == 401

    async def test_with_valid_session(self, client: AsyncClient, user_factory) -> None:
        _, password = await user_factory(email="grace@example.com", display_name="grace")
        await client.post("/api/v1/auth/login", json={"email": "grace@example.com", "password": password})

        r = await client.get("/api/v1/auth/me")

        assert r.status_code == 200
        body = r.json()
        assert body["email"] == "grace@example.com"
        assert "password_hash" not in body
