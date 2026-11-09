"""Topic response schemas"""

from __future__ import annotations

from pydantic import BaseModel


class TopicOut(BaseModel):
    """One node of the topic hierarchy, named in the caller's language

    Flat on purpose: `parent_id` and `depth` let the client rebuild the tree,
    and a flat list stays a single query however deep the hierarchy goes
    `name` falls back to English, and is null only when English is missing too
    """

    id: int
    parent_id: int | None
    slug: str
    position: int
    depth: int
    name: str | None
    description: str | None
