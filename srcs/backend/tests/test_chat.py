"""Direct chat: send, thread, conversation list, read state, blocking"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _pair(user_factory) -> tuple:
    alice, _ = await user_factory(display_name="alice", email="alice@example.com")
    bob, _ = await user_factory(display_name="bob", email="bob@example.com")
    return alice, bob


class TestSend:
    async def test_send_and_read_thread(
        self, client: AsyncClient, user_factory, login
    ) -> None:
        alice, bob = await _pair(user_factory)

        await login(alice.email)
        r = await client.post(
            "/api/v1/chat/messages",
            json={"recipient_id": bob.id, "body": "  hey bob  "},
        )
        assert r.status_code == 201
        assert r.json()["body"] == "hey bob"  # trimmed
        assert r.json()["read_at"] is None

        await login(bob.email)
        r = await client.get(f"/api/v1/chat/with/{alice.id}")
        body = r.json()
        assert [m["body"] for m in body["items"]] == ["hey bob"]
        assert body["next_before"] is None

    async def test_cannot_message_self(
        self, client: AsyncClient, user_factory, login
    ) -> None:
        alice, _ = await _pair(user_factory)
        await login(alice.email)
        r = await client.post(
            "/api/v1/chat/messages", json={"recipient_id": alice.id, "body": "hi"}
        )
        assert r.status_code == 400

    async def test_unknown_recipient(
        self, client: AsyncClient, user_factory, login
    ) -> None:
        alice, _ = await _pair(user_factory)
        await login(alice.email)
        r = await client.post(
            "/api/v1/chat/messages", json={"recipient_id": 999999, "body": "hi"}
        )
        assert r.status_code == 404

    async def test_empty_body_rejected(
        self, client: AsyncClient, user_factory, login
    ) -> None:
        alice, bob = await _pair(user_factory)
        await login(alice.email)
        r = await client.post(
            "/api/v1/chat/messages", json={"recipient_id": bob.id, "body": "   "}
        )
        assert r.status_code == 422

    async def test_blocked_cannot_send(
        self, client: AsyncClient, user_factory, login
    ) -> None:
        alice, bob = await _pair(user_factory)
        await login(bob.email)
        await client.post("/api/v1/friends/block", json={"user_id": alice.id})

        await login(alice.email)
        r = await client.post(
            "/api/v1/chat/messages", json={"recipient_id": bob.id, "body": "hi"}
        )
        assert r.status_code == 403


class TestConversationsAndReadState:
    async def test_conversation_list_and_unread(
        self, client: AsyncClient, user_factory, login
    ) -> None:
        alice, bob = await _pair(user_factory)

        await login(alice.email)
        await client.post(
            "/api/v1/chat/messages", json={"recipient_id": bob.id, "body": "one"}
        )
        await client.post(
            "/api/v1/chat/messages", json={"recipient_id": bob.id, "body": "two"}
        )

        await login(bob.email)
        convos = (await client.get("/api/v1/chat/conversations")).json()
        assert len(convos) == 1
        assert convos[0]["user"]["id"] == alice.id
        assert convos[0]["last_message"]["body"] == "two"
        assert convos[0]["unread"] == 2

        # opening the thread clears the unread count
        await client.get(f"/api/v1/chat/with/{alice.id}")
        convos = (await client.get("/api/v1/chat/conversations")).json()
        assert convos[0]["unread"] == 0

    async def test_thread_pagination(
        self, client: AsyncClient, user_factory, login
    ) -> None:
        alice, bob = await _pair(user_factory)
        await login(alice.email)
        for i in range(5):
            await client.post(
                "/api/v1/chat/messages",
                json={"recipient_id": bob.id, "body": f"m{i}"},
            )

        first = (await client.get("/api/v1/chat/with/{}?limit=2".format(bob.id))).json()
        assert [m["body"] for m in first["items"]] == ["m3", "m4"]
        assert first["next_before"] is not None

        older = (
            await client.get(
                f"/api/v1/chat/with/{bob.id}?limit=2&before={first['next_before']}"
            )
        ).json()
        assert [m["body"] for m in older["items"]] == ["m1", "m2"]
