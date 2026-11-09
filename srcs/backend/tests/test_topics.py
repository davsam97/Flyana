"""Topics: the read-only exam hierarchy"""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Topic, TopicTranslation


async def _setup_hierarchy(db: AsyncSession) -> Topic:
    """A rank translated in English only, and a level translated in English and French"""
    rank = Topic(slug="t-topics-rank", position=0)
    db.add(rank)
    await db.flush()
    level = Topic(slug="t-topics-level", parent_id=rank.id, position=0)
    db.add(level)
    await db.flush()
    db.add_all([
        TopicTranslation(topic_id=rank.id, locale="en", name="Rank"),
        TopicTranslation(
            topic_id=level.id, locale="en", name="Level", description="English description"
        ),
        TopicTranslation(
            topic_id=level.id, locale="fr", name="Niveau", description="Description française"
        ),
    ])
    await db.flush()
    return rank


class TestTopics:
    async def test_hierarchy_in_the_requested_locale(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """Names follow the locale; parent_id and depth let the client rebuild the tree"""
        rank = await _setup_hierarchy(db)

        r = await client.get("/api/v1/topics", params={"locale": "fr"})
        assert r.status_code == 200
        by_slug = {topic["slug"]: topic for topic in r.json()}
        assert by_slug["t-topics-level"]["name"] == "Niveau"
        assert by_slug["t-topics-level"]["description"] == "Description française"
        assert by_slug["t-topics-level"]["parent_id"] == rank.id
        assert by_slug["t-topics-level"]["depth"] == 2
        assert by_slug["t-topics-rank"]["name"] == "Rank"
        assert by_slug["t-topics-rank"]["depth"] == 1

    async def test_missing_locale_falls_back_to_english(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """A topic with no translation in the asked language is served in English"""
        await _setup_hierarchy(db)

        r = await client.get("/api/v1/topics", params={"locale": "es"})
        by_slug = {topic["slug"]: topic for topic in r.json()}
        assert by_slug["t-topics-level"]["name"] == "Level"
        assert by_slug["t-topics-level"]["description"] == "English description"
