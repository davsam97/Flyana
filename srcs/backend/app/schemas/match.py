"""What a finished match looks like once it is read back"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MatchPlayerOut(BaseModel):
    """One player's final standing"""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    display_name: str
    avatar_path: str | None
    score: int
    final_rank: int | None


class MatchChoiceOut(BaseModel):
    """One proposal, with the flag that the duel kept hidden while playing"""

    id: int
    text: str
    correct: bool


class MatchAttemptOut(BaseModel):
    """What one player answered to one question

    `choice_id` is null when they did not answer in time, or when the proposal
    was later removed from the content files
    """

    user_id: int
    choice_id: int | None
    is_correct: bool
    response_ms: int | None
    score: int


class MatchQuestionOut(BaseModel):
    """One round: the question as it was asked, and every answer to it"""

    position: int
    question_id: int
    slug: str
    stem: str
    is_fallback: bool
    choices: list[MatchChoiceOut]
    attempts: list[MatchAttemptOut]


class MatchSummaryOut(BaseModel):
    """A finished match, round by round"""

    public_id: str
    mode: str
    question_count: int
    started_at: datetime | None
    finished_at: datetime | None
    players: list[MatchPlayerOut]
    questions: list[MatchQuestionOut]


class PlayableTopicOut(BaseModel):
    """One exam level a room can be set to, with what it holds

    `question_count` is what the room configuration needs: a level with three
    playable questions makes a three-question match, not a ten-question one
    """

    slug: str
    name: str
    description: str | None
    parent_slug: str | None
    parent_name: str | None
    question_count: int
