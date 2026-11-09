"""Validated client messages for the realtime WebSocket."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt

# Annotated per item: a length constraint on `list[str]` itself never reaches
# the elements, so a slug is bounded here rather than in the handler
TopicSlug = Annotated[str, Field(min_length=1, max_length=64)]


class ClientMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PingMessage(ClientMessage):
    type: Literal["ping"]


class TypingMessage(ClientMessage):
    type: Literal["chat.typing"]
    to: StrictInt = Field(gt=0)


class CreateMatchMessage(ClientMessage):
    type: Literal["match.create"]
    max_players: StrictInt = Field(default=8, ge=2, le=8)
    # How many questions the match asks. Defaults to the historical 10 so an
    # older client keeps the same game length
    question_count: Literal[3, 5, 7, 10] = 10
    # The exam levels the room draws from. Empty means the whole pool, so a
    # client that knows nothing of this field keeps working. The cap only stops
    # a crafted message from building an unbounded `IN` list
    topics: list[TopicSlug] = Field(default_factory=list, max_length=32)


class JoinMatchMessage(ClientMessage):
    type: Literal["match.join"]
    match_id: str = Field(min_length=1, max_length=12)


class ReadyMessage(ClientMessage):
    type: Literal["match.ready"]
    match_id: str = Field(min_length=1, max_length=12)
    ready: bool


class AnswerMessage(ClientMessage):
    type: Literal["match.answer"]
    match_id: str = Field(min_length=1, max_length=12)
    question_id: StrictInt = Field(gt=0)
    choice_id: StrictInt = Field(gt=0)


class LeaveMessage(ClientMessage):
    type: Literal["match.leave"]
    match_id: str = Field(min_length=1, max_length=12)


_MESSAGE_MODELS: dict[str, type[ClientMessage]] = {
    "ping": PingMessage,
    "chat.typing": TypingMessage,
    "match.create": CreateMatchMessage,
    "match.join": JoinMatchMessage,
    "match.ready": ReadyMessage,
    "match.answer": AnswerMessage,
    "match.leave": LeaveMessage,
}


def validate_client_message(message: Any) -> dict[str, Any] | None:
    """Validate known messages and leave unknown types for protocol handling."""
    if not isinstance(message, dict):
        return None

    message_type = message.get("type")
    model = _MESSAGE_MODELS.get(message_type) if isinstance(message_type, str) else None
    if model is None:
        return message

    try:
        return model.model_validate(message).model_dump()
    except ValueError:
        return None
