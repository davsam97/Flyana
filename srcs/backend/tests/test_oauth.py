"""OAuth identity: only an address the provider has verified may be returned"""

from __future__ import annotations

import json
from typing import Callable

import httpx
import pytest

from httpx import AsyncClient

from app.api.v1 import auth as auth_routes
from app.config import get_settings
from app.services.oauth import GithubOAuthClient, GoogleOAuthClient, OAuthExchangeError


def _mock_transport(monkeypatch: pytest.MonkeyPatch, routes: dict[str, object]) -> None:
    """Answers the provider calls from a path -> payload table"""

    def handler(request: httpx.Request) -> httpx.Response:
        for path, payload in routes.items():
            if request.url.path == path:
                return httpx.Response(200, content=json.dumps(payload))
        return httpx.Response(404, content="{}")

    original: Callable[..., httpx.AsyncClient] = httpx.AsyncClient

    def factory(*args: object, **kwargs: object) -> httpx.AsyncClient:
        kwargs.pop("transport", None)
        return original(transport=httpx.MockTransport(handler), **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(httpx, "AsyncClient", factory)


class TestGoogle:
    async def test_verified_address_is_accepted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _mock_transport(
            monkeypatch,
            {
                "/token": {"access_token": "tok"},
                "/v1/userinfo": {
                    "sub": "42",
                    "email": "nour@example.com",
                    "email_verified": True,
                    "name": "Nour",
                },
            },
        )
        identity = await GoogleOAuthClient(get_settings()).fetch_identity("code")
        assert identity.email == "nour@example.com"
        assert identity.provider_account_id == "42"

    @pytest.mark.parametrize("verified", [False, None])
    async def test_unverified_address_is_refused(
        self, monkeypatch: pytest.MonkeyPatch, verified: bool | None
    ) -> None:
        payload = {"sub": "42", "email": "victim@example.com", "name": "Nour"}
        if verified is not None:
            payload["email_verified"] = verified
        _mock_transport(monkeypatch, {"/token": {"access_token": "tok"}, "/v1/userinfo": payload})
        with pytest.raises(OAuthExchangeError):
            await GoogleOAuthClient(get_settings()).fetch_identity("code")


class TestGithub:
    async def test_the_verified_primary_address_wins_over_the_profile_one(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The profile e-mail is whatever the user published, verified or not"""
        _mock_transport(
            monkeypatch,
            {
                "/login/oauth/access_token": {"access_token": "tok"},
                "/user": {"id": 7, "email": "victim@example.com", "login": "nour"},
                "/user/emails": [
                    {"email": "other@example.com", "primary": False, "verified": True},
                    {"email": "victim@example.com", "primary": True, "verified": False},
                    {"email": "nour@example.com", "primary": True, "verified": True},
                ],
            },
        )
        identity = await GithubOAuthClient(get_settings()).fetch_identity("code")
        assert identity.email == "nour@example.com"

    async def test_without_a_verified_primary_address_the_exchange_fails(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _mock_transport(
            monkeypatch,
            {
                "/login/oauth/access_token": {"access_token": "tok"},
                "/user": {"id": 7, "email": "victim@example.com", "login": "nour"},
                "/user/emails": [
                    {"email": "victim@example.com", "primary": True, "verified": False}
                ],
            },
        )
        with pytest.raises(OAuthExchangeError):
            await GithubOAuthClient(get_settings()).fetch_identity("code")


class TestAuthorizeRoute:
    """A provider without credentials must not send the student away"""

    async def test_unconfigured_provider_comes_back_to_login(self, client: AsyncClient) -> None:
        r = await client.get("/api/v1/auth/oauth/google/authorize")
        assert r.status_code == 302
        assert r.headers["location"] == "/login?error=oauth"
        assert "oauth_state" not in r.cookies

    async def test_configured_provider_goes_to_the_consent_screen(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(auth_routes.settings, "GOOGLE_CLIENT_ID", "id-123")
        monkeypatch.setattr(auth_routes.settings, "GOOGLE_CLIENT_SECRET", "secret-123")
        r = await client.get("/api/v1/auth/oauth/google/authorize")
        assert r.status_code == 302
        assert r.headers["location"].startswith("https://accounts.google.com/")
        assert "client_id=id-123" in r.headers["location"]
        # The state must travel in a cookie, to be compared on the way back
        assert r.cookies["oauth_state"]
        assert "secret-123" not in r.headers["location"]
