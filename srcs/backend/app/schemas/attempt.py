"""Request bodies for attempt endpoints"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AttemptIn(BaseModel):
    """POST body for submitting an answer to a question"""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    answer: str = Field(min_length=1, max_length=2000)


class AttemptQuota(BaseModel):
    """How many tries are left on a question, out of how many"""

    limit: int
    left: int


class SelfAssessmentIn(BaseModel):
    """POST body for self-assessing a fallback attempt"""

    model_config = ConfigDict(extra="forbid")

    correct: bool


class SelfAssessmentOut(BaseModel):
    """What a self-assessment unlocked"""

    achievements: list[str]
