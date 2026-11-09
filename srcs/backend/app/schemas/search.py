"""Search request and response schemas"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import QuestionStatus
from app.schemas.question import QuestionOut


class QuestionFilters(BaseModel):
    """Every query parameter `GET /questions` accepts

    `per_page` is capped at 100 on purpose
    An unbounded `per_page=999999` hands any anonymous caller a denial of service
    since one request would make the database materialise the whole table

    `sort` and `status` are a `Literal` and an enum rather than plain `str`
    so Pydantic answers 422 for anything unexpected before it reaches the query
    That is what makes the sort lookup in `services/search.py` safe from injection
    """

    # Free-text search. Parsed by websearch_to_tsquery, so a user can type
    # `pointer OR array -python` and malformed input still cannot raise.
    q: str | None = None

    # Slugs rather than ids: URLs stay readable and survive a reseed.
    topic: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    difficulty_min: int | None = None
    difficulty_max: int | None = None

    # Honoured only for moderators and admins; every other caller is forced
    # back to `published` by the service. It appears here because the field
    # has to exist in the API surface, not because the client controls it.
    status: QuestionStatus | None = None

    locale: str | None = None

    # Accepted but not applied yet, see `services/search.py`
    answered: Literal["never", "wrong", "any"] | None = None

    sort: Literal[
        "relevance", "newest", "difficulty", "success_rate", "popularity"
    ] = "newest"
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class QuestionPage(BaseModel):
    """One page of results plus the counts the UI needs to draw its filters

    Declaring this as the route `response_model` is what keeps raw ORM objects
    away from the client since FastAPI narrows each item to `QuestionOut`
    """

    items: list[QuestionOut]
    page: int
    per_page: int
    total: int
    total_pages: int
    # {"topics": {"3": 43, ...}, "difficulty": {"2": 17, ...}} — JSON object
    # keys must be strings, which is why the ids and bucket numbers are cast.
    facets: dict[str, dict[str, int]]
