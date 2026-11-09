"""WebSocket connections and in-memory multiplayer rooms."""

from __future__ import annotations

import logging
import time
from collections.abc import Iterable
from secrets import token_hex
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)
QUESTION_DURATION_SECONDS = 20
# A right answer earns CORRECT_ANSWER_POINTS, plus a bonus for being among the
# first to find it: +5 for the first right answer, +3 the second, +1 the third
CORRECT_ANSWER_POINTS = 10
SPEED_BONUS_BY_RANK = (5, 3, 1)
FINISHED_ROOM_RETENTION_SECONDS = 300
# Between two questions everyone sees which choice was right. The pause belongs
# to the server, like the question timer: held by the clients it would eat into
# the next question's answering time, and each screen would drift apart
REVEAL_SECONDS = 4

TEMPORARY_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": 1,
        "text": "Que signifie HTTP ?",
        "choices": [
            {"id": 1, "text": "HyperText Transfer Protocol"},
            {"id": 2, "text": "High Transfer Text Process"},
            {"id": 3, "text": "Hyperlink Transmission Type Program"},
            {"id": 4, "text": "Host Text Transfer Package"},
        ],
        "correct_choice_id": 1,
    },
    {
        "id": 2,
        "text": "Que signifie CSS ?",
        "choices": [
            {"id": 1, "text": "Computer Style System"},
            {"id": 2, "text": "Cascading Style Sheets"},
            {"id": 3, "text": "Code Syntax Selector"},
            {"id": 4, "text": "Central Styling Service"},
        ],
        "correct_choice_id": 2,
    },
    {
        "id": 3,
        "text": "Quel langage est principalement utilise dans Node.js ?",
        "choices": [
            {"id": 1, "text": "Python"},
            {"id": 2, "text": "Java"},
            {"id": 3, "text": "JavaScript"},
            {"id": 4, "text": "C"},
        ],
        "correct_choice_id": 3,
    },
]


class ConnectionHub:
    def __init__(self) -> None:
        self._sockets: dict[int, set[WebSocket]] = {}
        self._rooms: dict[str, dict[str, Any]] = {}

    async def connect(self, user_id: int, ws: WebSocket) -> bool:
        """Registers a socket and returns whether the user was previously offline."""
        sockets = self._sockets.setdefault(user_id, set())
        was_offline = not sockets
        sockets.add(ws)
        return was_offline

    async def disconnect(self, user_id: int, ws: WebSocket) -> bool:
        """Removes a socket and returns whether the user is now fully offline."""
        sockets = self._sockets.get(user_id)

        if sockets is None:
            return False

        sockets.discard(ws)

        if sockets:
            return False

        del self._sockets[user_id]
        return True

    async def close_user(self, user_id: int, code: int = 4401) -> None:
        """Closes every socket a user has open, e.g. once the account is gone"""
        for ws in list(self._sockets.get(user_id, ())):
            try:
                await ws.close(code=code)
            except Exception:  # noqa: BLE001
                logger.debug("Could not close socket of user %s", user_id)

    def user_rooms(self, user_id: int) -> list[str]:
        """Rooms the user still plays in, lobby included, finished ones excluded"""
        return [
            room_id
            for room_id, room in self._rooms.items()
            if user_id in room["players"] and room["status"] != "finished"
        ]

    def is_online(self, user_id: int) -> bool:
        return bool(self._sockets.get(user_id))

    async def send_to(self, user_id: int, message: dict[str, Any]) -> None:
        for ws in list(self._sockets.get(user_id, ())):
            try:
                await ws.send_json(message)
            except Exception:  # noqa: BLE001
                logger.debug("Could not send message to user %s", user_id)

    async def broadcast(
        self,
        user_ids: Iterable[int],
        message: dict[str, Any],
    ) -> None:
        for user_id in user_ids:
            await self.send_to(user_id, message)

    def create_room(
        self,
        user_id: int,
        max_players: int = 8,
        questions: list[dict[str, Any]] | None = None,
        profile: dict[str, Any] | None = None,
        topics: list[str] | None = None,
    ) -> str:
        room_id = token_hex(3).upper()
        room_questions = questions or TEMPORARY_QUESTIONS

        self._rooms[room_id] = {
            # The exam levels the questions were drawn from, so whoever joins
            # sees what they are about to play. Empty means the whole pool
            "topics": list(topics or []),
            "players": {user_id},
            "profiles": {user_id: profile or {}},
            "ready": set(),
            "max_players": max_players,
            "status": "waiting",
            "question_number": 0,
            "question_count": len(room_questions),
            "questions": room_questions,
            "question_started_at": None,
            "question_deadline": None,
            "reveal_until": None,
            "answers": {},
            "pending_scores": {},
            "scores": {user_id: 0},
            "finish_reason": None,
            "winner_id": None,
            "disconnected_until": {},
        }

        return room_id

    def room_exists(self, room_id: str) -> bool:
        return room_id in self._rooms

    def room_players(self, room_id: str) -> set[int]:
        room = self._rooms.get(room_id)
        if room is None:
            return set()
        return set(room["players"])

    def join_room(
        self,
        room_id: str,
        user_id: int,
        profile: dict[str, Any] | None = None,
    ) -> str | None:
        room = self._rooms.get(room_id)

        if room is None:
            return "MATCH_NOT_FOUND"

        if room["status"] != "waiting":
            return "MATCH_ALREADY_STARTED"

        players: set[int] = room["players"]

        if user_id in players:
            return None

        if len(players) >= room["max_players"]:
            return "MATCH_FULL"

        players.add(user_id)
        room["profiles"][user_id] = profile or {}
        room["scores"][user_id] = 0
        return None

    def leave_room(self, room_id: str, user_id: int) -> bool:
        room = self._rooms.get(room_id)

        if room is None:
            return False

        players: set[int] = room["players"]
        ready: set[int] = room["ready"]

        players.discard(user_id)
        ready.discard(user_id)

        if not players:
            del self._rooms[room_id]

        return True

    def mark_user_disconnected(self, user_id: int) -> list[str]:
        affected_rooms: list[str] = []
        deadline = time.monotonic() + 60

        for room_id, room in self._rooms.items():
            if user_id in room["players"]:
                room["disconnected_until"][user_id] = deadline
                affected_rooms.append(room_id)

        return affected_rooms

    def restore_user(self, user_id: int) -> list[str]:
        restored_rooms: list[str] = []

        for room_id, room in self._rooms.items():
            if user_id in room["disconnected_until"]:
                del room["disconnected_until"][user_id]
                restored_rooms.append(room_id)

        return restored_rooms

    def expire_disconnected_user(self, user_id: int) -> list[str]:
        affected_rooms: list[str] = []
        now = time.monotonic()

        for room_id in list(self._rooms):
            room = self._rooms[room_id]
            deadline = room["disconnected_until"].get(user_id)

            if deadline is None or deadline > now:
                continue

            room["disconnected_until"].pop(user_id, None)
            affected_rooms.append(room_id)

        return affected_rooms

    def forfeit_user(self, room_id: str, user_id: int) -> dict[str, Any] | None:
        room = self._rooms.get(room_id)

        if room is None or user_id not in room["players"]:
            return None

        self.leave_room(room_id, user_id)
        remaining_players = self.room_players(room_id)

        if len(remaining_players) != 1 or room["status"] == "waiting":
            return None

        winner_id = next(iter(remaining_players))
        room = self._rooms[room_id]
        room["status"] = "finished"
        room["finish_reason"] = "forfeit"
        room["winner_id"] = winner_id

        return {
            "type": "match.finished",
            "match_id": room_id,
            "reason": "forfeit",
            "winner_id": winner_id,
            "standings": self.standings(room_id),
        }

    def is_match_active(self, room_id: str) -> bool:
        """A question is open, so an answer can still be taken"""
        room = self._rooms.get(room_id)
        return room is not None and room["status"] == "question_active"

    def is_match_running(self, room_id: str) -> bool:
        """The match still has something to send, question open or not

        Wider than `is_match_active` on purpose: the reveal is a phase of the
        match that the timer must keep driving, but it refuses answers
        """
        room = self._rooms.get(room_id)
        return room is not None and room["status"] in {"question_active", "reveal"}

    def remove_finished_room(self, room_id: str) -> bool:
        """Remove a finished room after clients had time to resync."""
        room = self._rooms.get(room_id)
        if room is None or room["status"] != "finished":
            return False
        del self._rooms[room_id]
        return True

    def state_sync(self, user_id: int) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        server_time = time.monotonic()

        for room_id, room in self._rooms.items():
            lobby = self.lobby_message(room_id)
            if user_id not in room["players"] or lobby is None:
                continue

            message: dict[str, Any] = {
                "type": "match.state_sync",
                "match_id": room_id,
                "status": room["status"],
                "players": lobby["players"],
                "max_players": room["max_players"],
                "topics": room["topics"],
                "question_count": room["question_count"],
                "server_time": server_time,
                "standings": [
                    standing for standing in self.standings(room_id)
                ],
            }

            # The reveal carries the question too: coming back during the pause
            # must land on the round being shown, not on the lobby
            if room["status"] in {"question_active", "reveal"}:
                reveal = room["status"] == "reveal"
                message["question"] = self.current_question(room_id)
                message["answered"] = user_id in room["answers"]
                # The question is closed during the reveal, whatever its own
                # deadline says: everyone answered early, or it ran out
                message["remaining_seconds"] = (
                    0.0 if reveal else max(0.0, room["question_deadline"] - server_time)
                )
                if reveal:
                    question = room["questions"][room["question_number"] - 1]
                    message["correct_choice_id"] = question["correct_choice_id"]
            elif room["status"] == "finished":
                message["reason"] = room["finish_reason"] or "normal"
                message["winner_id"] = room["winner_id"]

            messages.append(message)

        return messages

    def set_ready(self, room_id: str, user_id: int, ready: bool) -> str | None:
        room = self._rooms.get(room_id)

        if room is None:
            return "MATCH_NOT_FOUND"

        if user_id not in room["players"]:
            return "NOT_IN_MATCH"

        if ready:
            room["ready"].add(user_id)
        else:
            room["ready"].discard(user_id)

        return None

    def lobby_message(self, room_id: str) -> dict[str, Any] | None:
        room = self._rooms.get(room_id)

        if room is None:
            return None

        players = [
            {
                "id": user_id,
                "display_name": room["profiles"].get(user_id, {}).get(
                    "display_name", f"Joueur {user_id}"
                ),
                "avatar_path": room["profiles"].get(user_id, {}).get(
                    "avatar_path"
                ),
                "ready": user_id in room["ready"],
                "connected": self.is_online(user_id),
            }
            for user_id in sorted(room["players"])
        ]

        return {
            "type": "match.lobby",
            "match_id": room_id,
            "status": room["status"],
            "players": players,
            "max_players": room["max_players"],
            "topics": room["topics"],
            "question_count": room["question_count"],
        }

    def standings(self, room_id: str) -> list[dict[str, Any]]:
        room = self._rooms.get(room_id)
        if room is None:
            return []

        return [
            {
                "user_id": user_id,
                "display_name": room["profiles"].get(user_id, {}).get(
                    "display_name", f"Joueur {user_id}"
                ),
                "avatar_path": room["profiles"].get(user_id, {}).get(
                    "avatar_path"
                ),
                "score": room["scores"][user_id],
            }
            for user_id in sorted(room["players"])
        ]

    def room_is_ready(self, room_id: str) -> bool:
        room = self._rooms.get(room_id)

        if room is None:
            return False

        players: set[int] = room["players"]
        ready: set[int] = room["ready"]

        return len(players) >= 2 and players == ready

    def start_match(self, room_id: str) -> dict[str, Any] | None:
        room = self._rooms.get(room_id)

        if room is None or room["status"] != "waiting":
            return None

        if not self.room_is_ready(room_id):
            return None

        now = time.monotonic()
        room["status"] = "question_active"
        room["question_number"] = 1
        room["question_started_at"] = now
        room["question_deadline"] = now + 20
        room["answers"] = {}
        room["pending_scores"] = {}

        return {
            "type": "match.started",
            "match_id": room_id,
            "question_number": 1,
            "question_count": room["question_count"],
        }

    def current_question(self, room_id: str) -> dict[str, Any] | None:
        """The round being played, or the one the reveal is still showing"""
        room = self._rooms.get(room_id)

        if room is None or room["status"] not in {"question_active", "reveal"}:
            return None

        question = room["questions"][room["question_number"] - 1]

        return {
            "type": "match.question",
            "match_id": room_id,
            "question_number": room["question_number"],
            "question_count": room["question_count"],
            "question_id": question["id"],
            "text": question["text"],
            "choices": question["choices"],
            "started_at": room["question_started_at"],
            "deadline": room["question_deadline"],
            "duration_seconds": QUESTION_DURATION_SECONDS,
        }

    def answer(
        self,
        room_id: str,
        user_id: int,
        question_id: int,
        choice_id: int,
    ) -> dict[str, Any]:
        room = self._rooms.get(room_id)

        if room is None:
            return {"type": "error", "code": "MATCH_NOT_FOUND"}
        if user_id not in room["players"]:
            return {"type": "error", "code": "NOT_IN_MATCH"}
        # Checked before the state: during the reveal everyone has answered,
        # by choice or by timeout, so a click landing in the pause is a
        # duplicate and not a broken match. The clients ignore that code, and
        # would show an error banner for anything else
        if user_id in room["answers"]:
            return {"type": "error", "code": "ALREADY_ANSWERED"}
        if room["status"] != "question_active":
            return {"type": "error", "code": "INVALID_STATE"}

        now = time.monotonic()
        if now > room["question_deadline"]:
            return {"type": "error", "code": "ANSWER_TOO_LATE"}

        question = room["questions"][room["question_number"] - 1]
        if question["id"] != question_id:
            return {"type": "error", "code": "INVALID_QUESTION"}
        if choice_id not in {choice["id"] for choice in question["choices"]}:
            return {"type": "error", "code": "INVALID_CHOICE"}

        correct = choice_id == question["correct_choice_id"]
        score_delta = 0
        if correct:
            # answers arrive one at a time, in server order: the right answers
            # already recorded tell where this one ranks
            rank = sum(1 for was_correct in room["answers"].values() if was_correct)
            bonus = SPEED_BONUS_BY_RANK[rank] if rank < len(SPEED_BONUS_BY_RANK) else 0
            score_delta = CORRECT_ANSWER_POINTS + bonus
        room["answers"][user_id] = correct
        room["pending_scores"][user_id] = score_delta

        all_answered = len(room["answers"]) == len(room["players"])
        if all_answered:
            self._settle_answers(room)
            room["status"] = "reveal"
            room["reveal_until"] = now + REVEAL_SECONDS

        message: dict[str, Any] = {
            "type": "match.standings",
            "match_id": room_id,
            "answered_by": user_id,
            "all_answered": all_answered,
            "standings": self.standings(room_id),
            "_correct": correct,
            "_score_delta": score_delta,
            "_response_ms": round(
                max(0.0, now - room["question_started_at"]) * 1000
            ),
            "_question_number": room["question_number"],
        }
        if all_answered:
            # Only once the question is closed for everyone. Sent any earlier it
            # would hand the answer to whoever has not played yet
            message["correct_choice_id"] = question["correct_choice_id"]
        return message

    def advance_question(self, room_id: str) -> dict[str, Any] | None:
        """Leaves the reveal for the next question, or ends the match

        Only reachable from `reveal`: a question is never cut short while it is
        still open, and the pause that shows the right answer is never skipped
        """
        room = self._rooms.get(room_id)

        if room is None or room["status"] != "reveal":
            return None

        if len(room["answers"]) < len(room["players"]):
            return None

        if room["question_number"] >= room["question_count"]:
            room["status"] = "finished"
            standings = sorted(
                (
                    {
                        "user_id": user_id,
                        "display_name": room["profiles"].get(user_id, {}).get(
                            "display_name", f"Joueur {user_id}"
                        ),
                        "avatar_path": room["profiles"].get(user_id, {}).get(
                            "avatar_path"
                        ),
                        "score": room["scores"][user_id],
                    }
                    for user_id in room["players"]
                ),
                key=lambda player: (-player["score"], player["user_id"]),
            )
            room["finish_reason"] = "normal"
            room["winner_id"] = standings[0]["user_id"] if standings else None
            return {
                "type": "match.finished",
                "match_id": room_id,
                "standings": standings,
            }

        room["status"] = "question_active"
        room["question_number"] += 1
        room["question_started_at"] = time.monotonic()
        room["question_deadline"] = (
            room["question_started_at"] + QUESTION_DURATION_SECONDS
        )
        room["reveal_until"] = None
        room["answers"] = {}
        room["pending_scores"] = {}
        return self.current_question(room_id)

    def expire_question(self, room_id: str) -> dict[str, Any] | None:
        """Closes a question whose deadline has passed, and opens the reveal

        Whoever did not answer in time is counted wrong, like a wrong choice
        """
        room = self._rooms.get(room_id)

        if room is None or room["status"] != "question_active":
            return None

        now = time.monotonic()
        if now < room["question_deadline"]:
            return None

        for user_id in room["players"]:
            if user_id not in room["answers"]:
                room["answers"][user_id] = False
                room["pending_scores"][user_id] = 0

        self._settle_answers(room)
        room["status"] = "reveal"
        room["reveal_until"] = now + REVEAL_SECONDS
        question = room["questions"][room["question_number"] - 1]

        return {
            "type": "match.standings",
            "match_id": room_id,
            "answered_by": None,
            "all_answered": True,
            "standings": self.standings(room_id),
            "correct_choice_id": question["correct_choice_id"],
        }

    def expire_reveal(self, room_id: str) -> dict[str, Any] | None:
        """Ends the pause that shows the right answer, and moves the match on"""
        room = self._rooms.get(room_id)

        if room is None or room["status"] != "reveal":
            return None

        if time.monotonic() < room["reveal_until"]:
            return None

        return self.advance_question(room_id)

    @staticmethod
    def _settle_answers(room: dict[str, Any]) -> None:
        for user_id, score_delta in room["pending_scores"].items():
            room["scores"][user_id] += score_delta
        room["pending_scores"] = {}


hub = ConnectionHub()