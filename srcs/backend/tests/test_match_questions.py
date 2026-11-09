"""What the duel is allowed to draw"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Choice, ChoiceTranslation, Question, QuestionTranslation, Topic
from app.models.enums import QuestionKind, QuestionStatus
from app.services.match_questions import load_published_questions


@pytest.fixture(autouse=True)
async def empty_pool(db: AsyncSession) -> None:
    """Starts every test from an empty pool"""
    await db.execute(delete(Choice))


async def _question(
    db: AsyncSession,
    slug: str,
    kind: QuestionKind,
    *,
    with_choices: bool = True,
    status: QuestionStatus = QuestionStatus.published,
) -> Question:
    topic = Topic(slug=f"topic-{slug}", position=0)
    db.add(topic)
    await db.flush()

    question = Question(
        slug=slug,
        topic_id=topic.id,
        kind=kind,
        status=status,
        key_points=["KP something"] if kind == QuestionKind.free_text else [],
    )
    db.add(question)
    await db.flush()
    for locale in ("en", "fr"):
        db.add(
            QuestionTranslation(
                question_id=question.id, locale=locale, title=slug, stem=f"stem {locale}"
            )
        )

    if with_choices:
        for position, (text, correct) in enumerate((("right", True), ("wrong", False))):
            choice = Choice(question_id=question.id, position=position, is_correct=correct)
            db.add(choice)
            await db.flush()
            for locale in ("en", "fr"):
                db.add(
                    ChoiceTranslation(choice_id=choice.id, locale=locale, text=f"{text} {locale}")
                )
    await db.flush()
    return question


class TestPlayableQuestions:
    async def test_a_written_question_with_choices_is_drawn(self, db: AsyncSession) -> None:
        question = await _question(db, "written-playable", QuestionKind.free_text)

        drawn = await load_published_questions(db, "fr", limit=10)

        picked = [q for q in drawn if q["id"] == question.id]
        assert len(picked) == 1
        assert picked[0]["text"] == "stem fr"
        # order left out on purpose: the slots are shuffled per draw
        assert {c["text"] for c in picked[0]["choices"]} == {"right fr", "wrong fr"}

    async def test_a_written_question_without_choices_is_left_out(
        self, db: AsyncSession
    ) -> None:
        """The rest of the exam content stays out of the duel until it has choices"""
        question = await _question(db, "written-only", QuestionKind.free_text, with_choices=False)

        drawn = await load_published_questions(db, "fr", limit=10)

        assert all(q["id"] != question.id for q in drawn)

    async def test_a_draft_is_never_drawn(self, db: AsyncSession) -> None:
        question = await _question(
            db, "draft-playable", QuestionKind.single_choice, status=QuestionStatus.draft
        )

        drawn = await load_published_questions(db, "fr", limit=10)

        assert all(q["id"] != question.id for q in drawn)

    async def test_a_multi_choice_question_is_never_drawn(self, db: AsyncSession) -> None:
        """A round scores one choice: a question with several right ones cannot be played"""
        question = await _question(db, "multi-playable", QuestionKind.multi_choice)

        drawn = await load_published_questions(db, "fr", limit=10)

        assert all(q["id"] != question.id for q in drawn)

    async def test_a_question_of_an_archived_topic_is_never_drawn(
        self, db: AsyncSession
    ) -> None:
        question = await _question(db, "archived-topic", QuestionKind.single_choice)
        topic = await db.get(Topic, question.topic_id)
        assert topic is not None
        topic.archived = True
        await db.flush()

        drawn = await load_published_questions(db, "fr", limit=10)

        assert all(q["id"] != question.id for q in drawn)

    async def test_the_payload_keeps_the_answer_out_of_the_choices(
        self, db: AsyncSession
    ) -> None:
        """Players receive texts only; which one scores is read server-side"""
        question = await _question(db, "no-leak", QuestionKind.free_text)

        drawn = await load_published_questions(db, "fr", limit=10)
        picked = next(q for q in drawn if q["id"] == question.id)

        assert all(set(choice) == {"id", "text"} for choice in picked["choices"])
        assert picked["correct_choice_id"] in {choice["id"] for choice in picked["choices"]}

    async def test_the_right_answer_does_not_sit_on_the_same_slot_every_draw(
        self, db: AsyncSession
    ) -> None:
        """The exam content writes it first; a player must not learn to click A"""
        question = Question(
            slug="shuffled",
            topic_id=(await self._topic(db)).id,
            kind=QuestionKind.free_text,
            status=QuestionStatus.published,
            key_points=["KP something"],
        )
        db.add(question)
        await db.flush()
        db.add(
            QuestionTranslation(
                question_id=question.id, locale="fr", title="shuffled", stem="stem fr"
            )
        )
        for position in range(4):
            choice = Choice(
                question_id=question.id, position=position, is_correct=position == 0
            )
            db.add(choice)
            await db.flush()
            db.add(
                ChoiceTranslation(choice_id=choice.id, locale="fr", text=f"choice {position}")
            )
        await db.flush()

        slots = set()
        for _ in range(20):
            drawn = next(q for q in await load_published_questions(db, "fr", limit=10))
            ids = [choice["id"] for choice in drawn["choices"]]
            assert len(ids) == 4
            slots.add(ids.index(drawn["correct_choice_id"]))

        assert len(slots) > 1

    @staticmethod
    async def _topic(db: AsyncSession) -> Topic:
        topic = Topic(slug="topic-shuffled", position=0)
        db.add(topic)
        await db.flush()
        return topic


class TestRoomTopics:
    """A room can be set to one or several exam levels"""

    async def test_the_draw_can_be_narrowed_to_chosen_levels(self, db: AsyncSession) -> None:
        first = await _question(db, "topic-a-question", QuestionKind.free_text)
        second = await _question(db, "topic-b-question", QuestionKind.free_text)

        only_first = await load_published_questions(
            db, "fr", limit=10, topics=["topic-topic-a-question"]
        )
        both = await load_published_questions(
            db, "fr", limit=10, topics=["topic-topic-a-question", "topic-topic-b-question"]
        )
        everything = await load_published_questions(db, "fr", limit=10, topics=[])

        assert [q["id"] for q in only_first] == [first.id]
        assert {q["id"] for q in both} == {first.id, second.id}
        assert {q["id"] for q in everything} == {first.id, second.id}

    async def test_an_unknown_level_draws_nothing(self, db: AsyncSession) -> None:
        """Rather than silently falling back on the whole pool"""
        await _question(db, "real-question", QuestionKind.free_text)

        drawn = await load_published_questions(db, "fr", limit=10, topics=["no-such-level"])

        assert drawn == []

    async def test_the_route_lists_playable_levels_with_their_counts(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        await _question(db, "listed-question", QuestionKind.free_text)
        await _question(db, "bare-question", QuestionKind.free_text, with_choices=False)

        r = await client.get("/api/v1/matches/topics")

        assert r.status_code == 200, r.text
        by_slug = {row["slug"]: row for row in r.json()}
        assert by_slug["topic-listed-question"]["question_count"] == 1
        # A level nobody has written choices for is not offered at all
        assert "topic-bare-question" not in by_slug
