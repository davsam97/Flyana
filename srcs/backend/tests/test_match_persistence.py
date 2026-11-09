from __future__ import annotations

from typing import Any

import pytest

from app.models.match import Match, MatchPlayer, MatchQuestion
from app.services.match_persistence import create_match


class FakeSession:
    def __init__(self) -> None:
        self.items: list[Any] = []
        self.commits = 0

    def add(self, item: Any) -> None:
        self.items.append(item)

    def add_all(self, items: list[Any]) -> None:
        self.items.extend(items)

    async def flush(self) -> None:
        match = next(item for item in self.items if isinstance(item, Match))
        match.id = 41

    async def commit(self) -> None:
        self.commits += 1


@pytest.mark.asyncio
async def test_create_match_persists_players_and_questions() -> None:
    session = FakeSession()
    questions = [
        {"id": 10, "text": "Question 1", "choices": [], "correct_choice_id": 1},
        {"id": 20, "text": "Question 2", "choices": [], "correct_choice_id": 2},
    ]

    await create_match(session, "ABC123", 7, 4, questions)

    match = next(item for item in session.items if isinstance(item, Match))
    player = next(item for item in session.items if isinstance(item, MatchPlayer))
    stored_questions = [
        item for item in session.items if isinstance(item, MatchQuestion)
    ]

    assert match.public_id == "ABC123"
    assert match.question_count == 2
    assert match.mode.value == "arena"
    assert player.match_id == 41
    assert player.user_id == 7
    assert [(item.position, item.question_id) for item in stored_questions] == [
        (1, 10),
        (2, 20),
    ]
    assert session.commits == 1


@pytest.mark.asyncio
async def test_create_match_records_the_slot_order_of_every_round() -> None:
    """The draw shuffled them, so only the match knows what the players saw"""
    session = FakeSession()
    questions = [
        {
            "id": 10,
            "text": "Question 1",
            "choices": [{"id": 3, "text": "c"}, {"id": 1, "text": "a"}],
            "correct_choice_id": 1,
        },
        {
            "id": 20,
            "text": "Question 2",
            "choices": [{"id": 7, "text": "g"}, {"id": 5, "text": "e"}],
            "correct_choice_id": 5,
        },
    ]

    await create_match(session, "ORD123", 7, 4, questions)

    stored_questions = [item for item in session.items if isinstance(item, MatchQuestion)]
    assert [item.choice_order for item in stored_questions] == [[3, 1], [7, 5]]
