from __future__ import annotations

from app.services.realtime import ConnectionHub


def _ready_room(hub: ConnectionHub, players: list[int]) -> str:
    room_id = hub.create_room(players[0], max_players=len(players))
    for user_id in players[1:]:
        assert hub.join_room(room_id, user_id) is None

    for user_id in players:
        assert hub.set_ready(room_id, user_id, True) is None

    return room_id


def test_room_supports_three_players_and_requires_everyone_ready() -> None:
    hub = ConnectionHub()
    room_id = hub.create_room(1, max_players=4)

    assert hub.join_room(room_id, 2) is None
    assert hub.join_room(room_id, 3) is None
    assert hub.room_players(room_id) == {1, 2, 3}
    assert hub.set_ready(room_id, 1, True) is None
    assert hub.set_ready(room_id, 2, True) is None
    assert hub.start_match(room_id) is None

    assert hub.set_ready(room_id, 3, True) is None
    started = hub.start_match(room_id)

    assert started is not None
    assert started["type"] == "match.started"
    assert hub.is_match_active(room_id)


def test_room_rejects_players_above_capacity() -> None:
    hub = ConnectionHub()
    room_id = hub.create_room(1, max_players=3)

    assert hub.join_room(room_id, 2) is None
    assert hub.join_room(room_id, 3) is None
    assert hub.join_room(room_id, 4) == "MATCH_FULL"


def test_answer_is_accepted_only_once_and_updates_score() -> None:
    hub = ConnectionHub()
    room_id = _ready_room(hub, [1, 2])
    assert hub.start_match(room_id) is not None

    result = hub.answer(room_id, 1, question_id=1, choice_id=1)

    assert result["type"] == "match.standings"
    assert "correct" not in result
    assert {row["user_id"]: row["score"] for row in result["standings"]}[1] == 0
    final_result = hub.answer(room_id, 2, question_id=1, choice_id=2)
    assert {row["user_id"]: row["score"] for row in final_result["standings"]}[1] == 15
    assert hub.answer(room_id, 1, question_id=1, choice_id=1) == {
        "type": "error",
        "code": "ALREADY_ANSWERED",
    }


def test_right_answers_earn_ten_plus_a_bonus_by_arrival_order() -> None:
    """+5 for the first right answer, +3 the second, +1 the third, then none"""
    hub = ConnectionHub()
    room_id = _ready_room(hub, [1, 2, 3, 4, 5, 6])
    assert hub.start_match(room_id) is not None

    # a wrong answer first takes no rank from the right ones after it
    hub.answer(room_id, 6, question_id=1, choice_id=2)
    for user_id in (3, 1, 5, 2):
        result = hub.answer(room_id, user_id, question_id=1, choice_id=1)
        assert "correct" not in result
    final_result = hub.answer(room_id, 4, question_id=1, choice_id=1)

    scores = {row["user_id"]: row["score"] for row in final_result["standings"]}
    assert scores == {3: 15, 1: 13, 5: 11, 2: 10, 4: 10, 6: 0}


def test_scores_add_up_across_questions() -> None:
    hub = ConnectionHub()
    room_id = _ready_room(hub, [1, 2])
    assert hub.start_match(room_id) is not None

    hub.answer(room_id, 1, question_id=1, choice_id=1)
    hub.answer(room_id, 2, question_id=1, choice_id=1)
    question = hub.advance_question(room_id)
    assert question is not None and question["type"] == "match.question"

    correct = hub._rooms[room_id]["questions"][1]["correct_choice_id"]
    hub.answer(room_id, 2, question_id=question["question_id"], choice_id=correct)
    final_result = hub.answer(
        room_id, 1, question_id=question["question_id"], choice_id=correct
    )

    scores = {row["user_id"]: row["score"] for row in final_result["standings"]}
    assert scores == {1: 15 + 13, 2: 13 + 15}


def test_invalid_choice_is_rejected() -> None:
    hub = ConnectionHub()
    room_id = _ready_room(hub, [1, 2])
    assert hub.start_match(room_id) is not None

    result = hub.answer(room_id, 1, question_id=1, choice_id=999)

    assert result == {"type": "error", "code": "INVALID_CHOICE"}


def test_all_players_answering_advances_to_the_next_question() -> None:
    hub = ConnectionHub()
    room_id = _ready_room(hub, [1, 2, 3])
    assert hub.start_match(room_id) is not None

    for user_id in (1, 2, 3):
        result = hub.answer(room_id, user_id, question_id=1, choice_id=1)

    assert result["all_answered"] is True
    next_question = hub.advance_question(room_id)

    assert next_question is not None
    assert next_question["type"] == "match.question"
    assert next_question["question_number"] == 2


def test_reconnection_keeps_player_in_room_and_syncs_active_match() -> None:
    hub = ConnectionHub()
    room_id = _ready_room(hub, [1, 2])
    assert hub.start_match(room_id) is not None

    assert hub.mark_user_disconnected(1) == [room_id]
    assert hub.room_players(room_id) == {1, 2}
    assert hub.restore_user(1) == [room_id]

    state = hub.state_sync(1)[0]
    assert state["match_id"] == room_id
    assert state["status"] == "question_active"
    assert state["question"]["question_number"] == 1


def test_state_sync_contains_resume_data_for_active_match() -> None:
    hub = ConnectionHub()
    room_id = _ready_room(hub, [1, 2, 3])
    assert hub.start_match(room_id) is not None
    assert hub.answer(room_id, 1, question_id=1, choice_id=1)["type"] == (
        "match.standings"
    )

    state = hub.state_sync(1)[0]

    assert isinstance(state["server_time"], float)
    assert state["question"]["deadline"] > state["server_time"]
    assert state["answered"] is True
    assert state["standings"][0]["user_id"] == 1
    assert state["standings"][0]["score"] == 0
    assert [standing["user_id"] for standing in state["standings"][1:]] == [2, 3]
    assert [standing["score"] for standing in state["standings"][1:]] == [0, 0]


def test_expired_question_counts_missing_answers_as_incorrect(monkeypatch) -> None:
    hub = ConnectionHub()
    room_id = _ready_room(hub, [1, 2, 3])
    assert hub.start_match(room_id) is not None

    deadline = hub._rooms[room_id]["question_deadline"]
    assert deadline is not None
    monkeypatch.setattr("app.services.realtime.time.monotonic", lambda: deadline + 1)
    settled = hub.expire_question(room_id)

    assert settled is not None
    assert settled["type"] == "match.standings"
    assert settled["all_answered"] is True
    assert settled["correct_choice_id"] == 1
    # The question is closed but the match goes on: the reveal is a phase of it
    assert hub.is_match_active(room_id) is False
    assert hub.is_match_running(room_id) is True


def test_the_next_question_waits_for_the_reveal_to_end(monkeypatch) -> None:
    """The last answer opens the pause, it does not skip it"""
    hub = ConnectionHub()
    room_id = _ready_room(hub, [1, 2])
    assert hub.start_match(room_id) is not None

    hub.answer(room_id, 1, question_id=1, choice_id=1)
    settled = hub.answer(room_id, 2, question_id=1, choice_id=2)

    assert settled["all_answered"] is True
    assert settled["correct_choice_id"] == 1
    assert hub.expire_reveal(room_id) is None

    reveal_until = hub._rooms[room_id]["reveal_until"]
    monkeypatch.setattr("app.services.realtime.time.monotonic", lambda: reveal_until)
    next_question = hub.expire_reveal(room_id)

    assert next_question is not None
    assert next_question["question_number"] == 2
    assert hub.is_match_active(room_id) is True


def test_the_right_choice_stays_hidden_until_everyone_has_answered() -> None:
    hub = ConnectionHub()
    room_id = _ready_room(hub, [1, 2])
    assert hub.start_match(room_id) is not None

    first = hub.answer(room_id, 1, question_id=1, choice_id=1)

    assert first["all_answered"] is False
    assert "correct_choice_id" not in first


def test_finished_state_sync_keeps_winner_and_reason() -> None:
    hub = ConnectionHub()
    room_id = _ready_room(hub, [1, 2])
    assert hub.start_match(room_id) is not None

    hub._rooms[room_id]["question_number"] = hub._rooms[room_id]["question_count"]
    hub.answer(room_id, 1, question_id=3, choice_id=3)
    finished = hub.answer(room_id, 2, question_id=3, choice_id=1)
    assert finished["all_answered"] is True
    assert hub.advance_question(room_id)["type"] == "match.finished"

    state = hub.state_sync(1)[0]
    assert state["status"] == "finished"
    assert state["reason"] == "normal"
    assert state["winner_id"] == 1


def test_finished_room_can_be_cleaned_without_touching_active_room() -> None:
    hub = ConnectionHub()
    finished_room = _ready_room(hub, [1, 2])
    active_room = _ready_room(hub, [3, 4])
    assert hub.start_match(finished_room) is not None
    assert hub.start_match(active_room) is not None

    hub._rooms[finished_room]["status"] = "finished"

    assert hub.remove_finished_room(active_room) is False
    assert hub.remove_finished_room(finished_room) is True
    assert not hub.room_exists(finished_room)
    assert hub.room_exists(active_room)

def test_state_sync_during_the_reveal_keeps_the_question() -> None:
    """Coming back in the pause lands on the round, not on the lobby"""
    hub = ConnectionHub()
    room_id = _ready_room(hub, [1, 2])
    assert hub.start_match(room_id) is not None

    hub.answer(room_id, 1, question_id=1, choice_id=1)
    hub.answer(room_id, 2, question_id=1, choice_id=2)

    state = hub.state_sync(1)[0]

    assert state["status"] == "reveal"
    assert state["question"]["question_number"] == 1
    assert state["correct_choice_id"] == 1
    assert state["remaining_seconds"] == 0
