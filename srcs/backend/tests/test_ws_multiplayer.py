from __future__ import annotations

import asyncio
import time
from collections.abc import Iterator
from contextlib import ExitStack
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import ws as ws_api
from app.deps import get_db, get_ws_user
from app.main import app
from app.services.realtime import TEMPORARY_QUESTIONS, hub


class FakeDb:
    async def commit(self) -> None:
        return None

    async def refresh(self, _instance, attribute_names=None) -> None:
        """No-op: the sockets run on plain namespaces, not ORM instances

        `ws.py` re-reads the locale off `user` before every draw, so the fake
        has to answer the call; the value it would reload is already there
        """
        return None

    async def execute(self, _statement) -> None:
        """No-op: `ws.py` stamps `last_seen_at` with an UPDATE on disconnect"""
        return None


def _user(user_id: int) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        locale="en",
        is_active=True,
        display_name=f"player{user_id}",
        avatar_path=None,
    )


def _message_of_type(client, message_type: str) -> dict:
    for _ in range(5):
        message = client.receive_json()
        if message.get("type") == message_type:
            return message
    raise AssertionError(f"did not receive {message_type}")


def test_two_clients_play_through_websocket(monkeypatch) -> None:
    current_user = {"id": 1}

    async def fake_ws_user():
        return _user(current_user["id"])

    async def fake_db() -> Iterator[FakeDb]:
        yield FakeDb()

    async def fake_friends(_db, _user_id: int) -> set[int]:
        return set()

    async def fake_questions(_db, _locale: str, **_options):
        return TEMPORARY_QUESTIONS

    async def ignore_persistence(*_args, **_kwargs) -> None:
        return None

    async def finish_without_unlocks(*_args, **_kwargs) -> dict[int, list[str]]:
        return {}

    app.dependency_overrides[get_ws_user] = fake_ws_user
    app.dependency_overrides[get_db] = fake_db
    monkeypatch.setattr(ws_api, "friend_ids", fake_friends)
    monkeypatch.setattr(ws_api, "load_published_questions", fake_questions)
    monkeypatch.setattr(ws_api, "create_match", ignore_persistence)
    monkeypatch.setattr(ws_api, "add_player", ignore_persistence)
    monkeypatch.setattr(ws_api, "start_match", ignore_persistence)
    monkeypatch.setattr(ws_api, "record_attempt", ignore_persistence)
    monkeypatch.setattr(ws_api, "finish_match", finish_without_unlocks)
    monkeypatch.setattr(ws_api, "start_question", ignore_persistence)
    hub._rooms.clear()

    try:
        with TestClient(app) as client_one:
            with client_one.websocket_connect("/api/ws") as socket_one:
                current_user["id"] = 2
                with client_one.websocket_connect("/api/ws") as socket_two:
                    current_user["id"] = 1
                    socket_one.send_json({"type": "match.create", "max_players": 2})
                    created = socket_one.receive_json()
                    room_id = created["match_id"]
                    assert created["type"] == "match.created"
                    _message_of_type(socket_one, "match.lobby")

                    current_user["id"] = 2
                    socket_two.send_json({"type": "match.join", "match_id": room_id})
                    _message_of_type(socket_one, "match.lobby")
                    _message_of_type(socket_two, "match.lobby")

                    current_user["id"] = 1
                    socket_one.send_json(
                        {"type": "match.ready", "match_id": room_id, "ready": True}
                    )
                    _message_of_type(socket_one, "match.lobby")
                    _message_of_type(socket_two, "match.lobby")

                    current_user["id"] = 2
                    socket_two.send_json(
                        {"type": "match.ready", "match_id": room_id, "ready": True}
                    )
                    _message_of_type(socket_one, "match.started")
                    _message_of_type(socket_two, "match.started")
                    _message_of_type(socket_one, "match.question")
                    _message_of_type(socket_two, "match.question")

                    current_user["id"] = 1
                    socket_one.send_json(
                        {
                            "type": "match.answer",
                            "match_id": room_id,
                            "question_id": 1,
                            "choice_id": 1,
                        }
                    )
                    first_standings = _message_of_type(socket_one, "match.standings")
                    _message_of_type(socket_two, "match.standings")
                    assert first_standings["all_answered"] is False
                    assert "correct" not in first_standings

                    current_user["id"] = 2
                    socket_two.send_json(
                        {
                            "type": "match.answer",
                            "match_id": room_id,
                            "question_id": 1,
                            "choice_id": 2,
                        }
                    )
                    final_standings = _message_of_type(socket_one, "match.standings")
                    _message_of_type(socket_two, "match.standings")
                    assert final_standings["all_answered"] is True
                    assert "correct" not in final_standings
                    _message_of_type(socket_one, "match.question")
                    _message_of_type(socket_two, "match.question")
    finally:
        app.dependency_overrides.clear()
        hub._rooms.clear()


def test_three_clients_receive_synchronized_questions(monkeypatch) -> None:
    current_user = {"id": 1}

    async def fake_ws_user():
        return _user(current_user["id"])

    async def fake_db() -> Iterator[FakeDb]:
        yield FakeDb()

    async def fake_friends(_db, _user_id: int) -> set[int]:
        return set()

    async def fake_questions(_db, _locale: str, **_options):
        return TEMPORARY_QUESTIONS

    async def ignore_persistence(*_args, **_kwargs) -> None:
        return None

    async def finish_without_unlocks(*_args, **_kwargs) -> dict[int, list[str]]:
        return {}

    app.dependency_overrides[get_ws_user] = fake_ws_user
    app.dependency_overrides[get_db] = fake_db
    monkeypatch.setattr(ws_api, "friend_ids", fake_friends)
    monkeypatch.setattr(ws_api, "load_published_questions", fake_questions)
    for function_name in (
        "create_match",
        "add_player",
        "start_match",
        "record_attempt",
        "start_question",
    ):
        monkeypatch.setattr(ws_api, function_name, ignore_persistence)
    monkeypatch.setattr(ws_api, "finish_match", finish_without_unlocks)
    hub._rooms.clear()

    try:
        with TestClient(app) as client:
            with ExitStack() as stack:
                sockets = []
                for user_id in (1, 2, 3):
                    current_user["id"] = user_id
                    sockets.append(stack.enter_context(client.websocket_connect("/api/ws")))

                current_user["id"] = 1
                sockets[0].send_json({"type": "match.create", "max_players": 3})
                room_id = sockets[0].receive_json()["match_id"]
                _message_of_type(sockets[0], "match.lobby")

                for index in (1, 2):
                    current_user["id"] = index + 1
                    sockets[index].send_json(
                        {"type": "match.join", "match_id": room_id}
                    )
                    for socket in sockets[: index + 1]:
                        _message_of_type(socket, "match.lobby")

                for index, socket in enumerate(sockets, start=1):
                    current_user["id"] = index
                    socket.send_json(
                        {"type": "match.ready", "match_id": room_id, "ready": True}
                    )
                    if index < 3:
                        for peer in sockets:
                            _message_of_type(peer, "match.lobby")

                for socket in sockets:
                    _message_of_type(socket, "match.started")
                    question = _message_of_type(socket, "match.question")
                    assert question["question_number"] == 1
                    assert question["question_id"] == 1

                for index, socket in enumerate(sockets, start=1):
                    current_user["id"] = index
                    socket.send_json(
                        {
                            "type": "match.answer",
                            "match_id": room_id,
                            "question_id": 1,
                            "choice_id": 1,
                        }
                    )
                    for peer in sockets:
                        standings = _message_of_type(peer, "match.standings")
                        assert standings["all_answered"] is (index == 3)

                for socket in sockets:
                    next_question = _message_of_type(socket, "match.question")
                    assert next_question["question_number"] == 2
    finally:
        app.dependency_overrides.clear()
        hub._rooms.clear()


def test_client_reconnects_and_receives_active_match_state(monkeypatch) -> None:
    current_user = {"id": 1}

    async def fake_ws_user():
        return _user(current_user["id"])

    async def fake_db() -> Iterator[FakeDb]:
        yield FakeDb()

    async def fake_friends(_db, _user_id: int) -> set[int]:
        return set()

    async def fake_questions(_db, _locale: str, **_options):
        return TEMPORARY_QUESTIONS

    async def ignore_persistence(*_args, **_kwargs) -> None:
        return None

    async def finish_without_unlocks(*_args, **_kwargs) -> dict[int, list[str]]:
        return {}

    app.dependency_overrides[get_ws_user] = fake_ws_user
    app.dependency_overrides[get_db] = fake_db
    monkeypatch.setattr(ws_api, "friend_ids", fake_friends)
    monkeypatch.setattr(ws_api, "load_published_questions", fake_questions)
    for function_name in (
        "create_match",
        "add_player",
        "start_match",
        "record_attempt",
        "start_question",
    ):
        monkeypatch.setattr(ws_api, function_name, ignore_persistence)
    monkeypatch.setattr(ws_api, "finish_match", finish_without_unlocks)
    hub._rooms.clear()

    try:
        with TestClient(app) as client:
            with client.websocket_connect("/api/ws") as socket_one:
                current_user["id"] = 2
                with client.websocket_connect("/api/ws") as socket_two:
                    current_user["id"] = 1
                    socket_one.send_json({"type": "match.create", "max_players": 2})
                    room_id = socket_one.receive_json()["match_id"]
                    _message_of_type(socket_one, "match.lobby")

                    current_user["id"] = 2
                    socket_two.send_json(
                        {"type": "match.join", "match_id": room_id}
                    )
                    _message_of_type(socket_one, "match.lobby")
                    _message_of_type(socket_two, "match.lobby")

                    for user_id, socket in ((1, socket_one), (2, socket_two)):
                        current_user["id"] = user_id
                        socket.send_json(
                            {
                                "type": "match.ready",
                                "match_id": room_id,
                                "ready": True,
                            }
                        )
                        if user_id == 1:
                            _message_of_type(socket_one, "match.lobby")
                            _message_of_type(socket_two, "match.lobby")

                    _message_of_type(socket_one, "match.started")
                    _message_of_type(socket_two, "match.started")
                    _message_of_type(socket_one, "match.question")
                    _message_of_type(socket_two, "match.question")

                    current_user["id"] = 1
                    socket_one.send_json(
                        {
                            "type": "match.answer",
                            "match_id": room_id,
                            "question_id": 1,
                            "choice_id": 1,
                        }
                    )
                    _message_of_type(socket_one, "match.standings")
                    _message_of_type(socket_two, "match.standings")

                    socket_two.close()
                    presence = _message_of_type(socket_one, "match.player_presence")
                    assert presence["user_id"] == 2
                    assert presence["connected"] is False
                    _message_of_type(socket_one, "match.lobby")

                current_user["id"] = 2
                with client.websocket_connect("/api/ws") as reconnected:
                    state = _message_of_type(reconnected, "match.state_sync")
                    assert state["match_id"] == room_id
                    assert state["status"] == "question_active"
                    assert state["answered"] is False
                    assert state["question"]["question_number"] == 1
                    assert state["remaining_seconds"] <= 20
    finally:
        app.dependency_overrides.clear()
        hub._rooms.clear()


def test_websocket_rejects_invalid_known_messages(monkeypatch) -> None:
    async def fake_ws_user():
        return _user(1)

    async def fake_db() -> Iterator[FakeDb]:
        yield FakeDb()

    async def fake_friends(_db, _user_id: int) -> set[int]:
        return set()

    app.dependency_overrides[get_ws_user] = fake_ws_user
    app.dependency_overrides[get_db] = fake_db
    monkeypatch.setattr(ws_api, "friend_ids", fake_friends)

    try:
        with TestClient(app) as client:
            with client.websocket_connect("/api/ws") as socket:
                socket.send_json({"type": "match.create", "max_players": True})
                assert socket.receive_json() == {
                    "type": "error",
                    "code": "INVALID_MESSAGE",
                }

                socket.send_json({"type": "unsupported.event"})
                assert socket.receive_json() == {
                    "type": "error",
                    "code": "UNKNOWN_MESSAGE_TYPE",
                }
    finally:
        app.dependency_overrides.clear()
        hub._rooms.clear()


async def test_a_forfeit_is_written_down(monkeypatch) -> None:
    """A match won by forfeit ends in the database too"""

    class NoDb:
        async def __aenter__(self) -> FakeDb:
            return FakeDb()

        async def __aexit__(self, *_args: object) -> bool:
            return False

    async def no_wait(_seconds: float) -> None:
        return None

    recorded: dict[str, object] = {}

    async def spy(_db: object, public_id: str, standings: list[dict]) -> None:
        recorded["public_id"] = public_id
        recorded["standings"] = standings

    room_id = hub.create_room(1, max_players=2)
    assert hub.join_room(room_id, 2) is None
    assert hub.set_ready(room_id, 1, True) is None
    assert hub.set_ready(room_id, 2, True) is None
    assert hub.start_match(room_id) is not None
    hub._rooms[room_id]["disconnected_until"][2] = time.monotonic() - 1

    monkeypatch.setattr(ws_api, "finish_match", spy)
    monkeypatch.setattr(ws_api, "SessionLocal", NoDb)
    monkeypatch.setattr(asyncio, "sleep", no_wait)

    try:
        await ws_api.expire_player_after_grace(2)
    finally:
        hub._rooms.clear()

    assert recorded["public_id"] == room_id
    assert [standing["user_id"] for standing in recorded["standings"]] == [1]


def test_a_room_carries_the_levels_it_was_created_with(monkeypatch) -> None:
    """The chosen levels reach the draw and come back in the lobby"""
    asked: dict[str, object] = {}

    async def fake_ws_user():
        return _user(1)

    async def fake_db() -> Iterator[FakeDb]:
        yield FakeDb()

    async def fake_friends(_db, _user_id: int) -> set[int]:
        return set()

    async def fake_questions(_db, _locale: str, **options):
        asked.update(options)
        return TEMPORARY_QUESTIONS

    async def ignore_persistence(*_args, **_kwargs) -> None:
        return None

    app.dependency_overrides[get_ws_user] = fake_ws_user
    app.dependency_overrides[get_db] = fake_db
    monkeypatch.setattr(ws_api, "friend_ids", fake_friends)
    monkeypatch.setattr(ws_api, "load_published_questions", fake_questions)
    monkeypatch.setattr(ws_api, "create_match", ignore_persistence)

    chosen = ["exam-rank-02-level-0", "exam-rank-06-level-0"]
    try:
        with TestClient(app) as client:
            with client.websocket_connect("/api/ws") as socket:
                socket.send_json(
                    {"type": "match.create", "max_players": 2, "topics": chosen}
                )
                _message_of_type(socket, "match.created")
                lobby = _message_of_type(socket, "match.lobby")

                assert asked["topics"] == chosen
                assert lobby["topics"] == chosen
                assert lobby["question_count"] == len(TEMPORARY_QUESTIONS)
    finally:
        app.dependency_overrides.clear()
        hub._rooms.clear()
