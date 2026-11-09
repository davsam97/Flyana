"""Chat request and response contracts"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.user import UserSummary

BODY_MAX = 2000


class MessageCreate(BaseModel):
    """Body of `POST /chat/messages`"""

    recipient_id: int
    body: str = Field(min_length=1, max_length=BODY_MAX)

    @field_validator("body")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        """A message of only spaces/newlines is not a message"""
        stripped = v.strip()
        if not stripped:
            raise ValueError("message is empty")
        return stripped


class MessageOut(BaseModel):
    """The only shape a message is ever sent out in — REST body and WS frame"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_id: int
    recipient_id: int
    body: str
    created_at: datetime
    read_at: datetime | None


class MessagePage(BaseModel):
    """One page of a thread, oldest-first, plus a cursor for older history"""

    items: list[MessageOut]
    next_before: int | None


class ConversationOut(BaseModel):
    """One row of the conversation list: who, the last line, how many unread"""

    user: UserSummary
    last_message: MessageOut
    unread: int
