
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlencode

import httpx

from app.config import Settings
from app.models.enums import OAuthProvider

@dataclass
class OAuthIdentity:
	provider_account_id: str
	email: str
	display_name_hint: str


class OAuthExchangeError(Exception):
	"""Raised when the code exchange fails; the route turns it into a redirect, not a 500"""

class OAuthClient(Protocol):
	def authorize_url(self, state: str) -> str: ...
	async def fetch_identity(self, code: str) -> OAuthIdentity: ...

def _redirect_uri(settings: Settings, provider: OAuthProvider) -> str:
	return f"{settings.public_url}/api/v1/auth/oauth/{provider.value}/callback"

class GoogleOAuthClient:
	def __init__(self, settings:Settings) -> None:
		self._client_id = settings.GOOGLE_CLIENT_ID
		self._client_secret = settings.GOOGLE_CLIENT_SECRET
		self._redirect_uri = _redirect_uri(settings, OAuthProvider.google)

	def authorize_url(self, state: str) -> str:
		base = "https://accounts.google.com/o/oauth2/v2/auth"
		params = {
			"response_type": "code",
			"client_id": self._client_id,
			"redirect_uri": self._redirect_uri,
			"scope": "openid email profile",
			"state": state,
		}
		return f"{base}?{urlencode(params)}"

	async def fetch_identity(self, code: str) -> OAuthIdentity:
		try:
			async with httpx.AsyncClient() as client:
				token_response = await client.post(
					"https://oauth2.googleapis.com/token",
					data={
						"code": code,
						"client_id": self._client_id,
						"client_secret": self._client_secret,
						"redirect_uri":self._redirect_uri,
						"grant_type": "authorization_code",
					},
				)
				token_response.raise_for_status()
				access_token = token_response.json()["access_token"]

				userinfo_response = await client.get(
					"https://openidconnect.googleapis.com/v1/userinfo",
					headers={"Authorization": f"Bearer {access_token}"},
				)
				userinfo_response.raise_for_status()
				data = userinfo_response.json()
		except (httpx.HTTPError, KeyError) as exc:
			raise OAuthExchangeError(f"google exchange failed: {exc}") from exc

		# An account is linked by e-mail, so the address must be one Google has
		# checked: an unverified one would let anyone claim someone else's account
		if str(data.get("email_verified")).lower() != "true":
			raise OAuthExchangeError("google email not verified")

		return OAuthIdentity(
			provider_account_id=data["sub"],
			email=data["email"],
			display_name_hint=data.get("name", data["email"]),
		)

class GithubOAuthClient:
	def __init__(self, settings: Settings) -> None:
		self._client_id = settings.GITHUB_CLIENT_ID
		self._client_secret = settings.GITHUB_CLIENT_SECRET
		self._redirect_uri = _redirect_uri(settings, OAuthProvider.github)

	def authorize_url(self, state: str) -> str:
		base = "https://github.com/login/oauth/authorize"
		params = {
			"client_id": self._client_id,
			"redirect_uri": self._redirect_uri,
			"scope": "read:user user:email",
			"state": state,
		}
		return f"{base}?{urlencode(params)}"

	async def fetch_identity(self, code: str) -> OAuthIdentity:
		try:
			async with httpx.AsyncClient() as client:
				token_response = await client.post(
					"https://github.com/login/oauth/access_token",
						headers={"Accept": "application/json"},
						data={
							"code": code,
							"client_secret": self._client_secret,
							"client_id": self._client_id,
							"redirect_uri": self._redirect_uri,
						},
				)
				token_response.raise_for_status()
				access_token = token_response.json()["access_token"]
				auth_header = {"Authorization": f"Bearer {access_token}"}

				user_response = await client.get("https://api.github.com/user",
									headers=auth_header)
				user_response.raise_for_status()
				user_data = user_response.json()

				# `user_data["email"]` is the address the user chose to publish on
				# their profile, verified or not. Only /user/emails says which one
				# GitHub has checked, and an account is linked by e-mail here
				emails_response = await client.get("https://api.github.com/user/emails", headers=auth_header)
				emails_response.raise_for_status()
				email = next(
					e["email"] for e in emails_response.json()
					if e["primary"] and e["verified"]
				)
		except (httpx.HTTPError, KeyError, StopIteration) as exc:
			raise OAuthExchangeError(f"github exchange failed: {exc}") from exc

		return OAuthIdentity(
			provider_account_id=str(user_data["id"]),
			email=email,
			display_name_hint=user_data.get("name") or user_data["login"],
		)

class FortyTwoOAuthClient:
	def __init__(self, settings: Settings) -> None:
		self._client_id = settings.FORTYTWO_CLIENT_ID
		self._client_secret = settings.FORTYTWO_CLIENT_SECRET
		self._redirect_uri = _redirect_uri(settings, OAuthProvider.fortytwo)

	def authorize_url(self, state: str) -> str:
		base = "https://api.intra.42.fr/oauth/authorize"
		params = {
			"response_type": "code",
			"client_id": self._client_id,
			"redirect_uri": self._redirect_uri,
			"scope": "public",
			"state": state,
		}
		return f"{base}?{urlencode(params)}"

	async def fetch_identity(self, code: str) -> OAuthIdentity:
		try:
			async with httpx.AsyncClient() as client:
				token_response = await client.post(
					"https://api.intra.42.fr/oauth/token",
					data={
						"code": code,
						"client_id": self._client_id,
						"client_secret": self._client_secret,
						"redirect_uri":self._redirect_uri,
						"grant_type": "authorization_code",
					},
				)
				token_response.raise_for_status()
				access_token = token_response.json()["access_token"]

				userinfo_response = await client.get(
					"https://api.intra.42.fr/v2/me",
					headers={"Authorization": f"Bearer {access_token}"},
				)
				userinfo_response.raise_for_status()
				data = userinfo_response.json()
		except (httpx.HTTPError, KeyError) as exc:
			raise OAuthExchangeError(f"42 exchange failed: {exc}") from exc

		# No verification flag to check here: the intra only ever returns the
		# address the school issued, which nobody chooses themselves
		return OAuthIdentity(
			provider_account_id=str(data["id"]),
			email=str(data["email"]),
			display_name_hint=str(data.get("login", data["email"])),
		)