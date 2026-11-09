"""Friends: requests, list, and blocking"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from httpx import AsyncClient


async def _pair(user_factory) -> tuple:
    alice, _ = await user_factory(display_name="alice", email="alice@example.com")
    bob, _ = await user_factory(display_name="bob", email="bob@example.com")
    # Plain values, not the ORM objects: every request of a test shares one
    # session, so a route's `rollback()` expires these objects too, and reading
    # an expired attribute from test code fires a lazy load outside the
    # greenlet (MissingGreenlet)
    return (
        SimpleNamespace(id=alice.id, email=alice.email),
        SimpleNamespace(id=bob.id, email=bob.email),
    )


class TestRequests:
    async def test_request_then_accept(self, client: AsyncClient, user_factory, login) -> None:
        alice, bob = await _pair(user_factory)

        await login(alice.email)
        r = await client.post(
            "/api/v1/friends/requests", json={"addressee_id": bob.id}
        )
        assert r.status_code == 201
        assert r.json()["status"] == "pending"

        # it shows up as outgoing for alice, incoming for bob
        r = await client.get("/api/v1/friends/requests")
        assert [p["user"]["id"] for p in r.json()["outgoing"]] == [bob.id]

        await login(bob.email)
        r = await client.get("/api/v1/friends/requests")
        incoming = r.json()["incoming"]
        assert [p["user"]["id"] for p in incoming] == [alice.id]
        friendship_id = incoming[0]["friendship_id"]

        r = await client.post(f"/api/v1/friends/requests/{friendship_id}/accept")
        assert r.status_code == 200

        r = await client.get("/api/v1/friends")
        assert [f["user"]["id"] for f in r.json()["items"]] == [alice.id]

    async def test_reverse_request_auto_accepts(
        self, client: AsyncClient, user_factory, login
    ) -> None:
        alice, bob = await _pair(user_factory)

        await login(alice.email)
        await client.post("/api/v1/friends/requests", json={"addressee_id": bob.id})

        await login(bob.email)
        r = await client.post(
            "/api/v1/friends/requests", json={"addressee_id": alice.id}
        )
        assert r.status_code == 201
        assert r.json()["status"] == "accepted"

        r = await client.get("/api/v1/friends")
        assert [f["user"]["id"] for f in r.json()["items"]] == [alice.id]

    async def test_duplicate_request_conflicts(
        self, client: AsyncClient, user_factory, login
    ) -> None:
        alice, bob = await _pair(user_factory)
        await login(alice.email)
        r1 = await client.post(
            "/api/v1/friends/requests", json={"addressee_id": bob.id}
        )
        r2 = await client.post(
            "/api/v1/friends/requests", json={"addressee_id": bob.id}
        )
        assert r1.status_code == 201
        assert r2.status_code == 409

    async def test_cannot_friend_yourself(
        self, client: AsyncClient, user_factory, login
    ) -> None:
        alice, _ = await _pair(user_factory)
        await login(alice.email)
        r = await client.post(
            "/api/v1/friends/requests", json={"addressee_id": alice.id}
        )
        assert r.status_code == 400


class TestRemoveAndBlock:
    async def test_remove_friendship(
        self, client: AsyncClient, user_factory, login
    ) -> None:
        alice, bob = await _pair(user_factory)
        await login(alice.email)
        fid = (
            await client.post(
                "/api/v1/friends/requests", json={"addressee_id": bob.id}
            )
        ).json()["friendship_id"]
        await login(bob.email)
        await client.post(f"/api/v1/friends/requests/{fid}/accept")

        r = await client.delete(f"/api/v1/friends/{fid}")
        assert r.status_code == 204
        r = await client.get("/api/v1/friends")
        assert r.json()["items"] == []

    async def test_block_drops_friend_and_stops_requests(
        self, client: AsyncClient, user_factory, login
    ) -> None:
        alice, bob = await _pair(user_factory)

        await login(alice.email)
        r = await client.post("/api/v1/friends/block", json={"user_id": bob.id})
        assert r.status_code == 200
        assert r.json()["status"] == "blocked"
        assert (await client.get("/api/v1/friends")).json()["items"] == []

        # bob cannot send a request into the block
        await login(bob.email)
        r = await client.post(
            "/api/v1/friends/requests", json={"addressee_id": alice.id}
        )
        assert r.status_code == 409

        # only the blocker may lift it
        r = await client.delete(f"/api/v1/friends/block/{alice.id}")
        assert r.status_code == 404

        await login(alice.email)
        r = await client.delete(f"/api/v1/friends/block/{bob.id}")
        assert r.status_code == 204
