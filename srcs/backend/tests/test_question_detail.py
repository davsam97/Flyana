"""Question detail: fetching and language fallback"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Topic, Question, QuestionTag, QuestionTranslation, Choice, Tag
from app.models.enums import QuestionKind, QuestionStatus, Role
from app.services.validation import assert_publishable


async def _setup_question(
    db: AsyncSession,
    *,
    topic_slug: str = "t-detail",
    question_kind: QuestionKind = QuestionKind.free_text,
    question_status: QuestionStatus = QuestionStatus.published,
    question_slug: str = "t-detail-question",
    en_stem: str = "English question",
    en_title: str = "English title",
    en_explanation: str | None = None,
    key_points: list[str] | None = None,
    fr_stem: str | None = None,
    fr_title: str = "Titre français",
) -> Question:
    """Helper that inserts a topic, question, and its translations"""
    topic = Topic(slug=topic_slug, position=0, icon=None)
    db.add(topic)
    await db.flush()

    question = Question(
        topic_id=topic.id,
        kind=question_kind,
        status=question_status,
        slug=question_slug,
        key_points=key_points or [],
    )
    db.add(question)
    await db.flush()

    en_trans = QuestionTranslation(
        question_id=question.id,
        locale="en",
        title=en_title,
        stem=en_stem,
        explanation=en_explanation,
    )
    db.add(en_trans)

    if fr_stem is not None:
        fr_trans = QuestionTranslation(
            question_id=question.id,
            locale="fr",
            title=fr_title,
            stem=fr_stem,
            explanation=None,
        )
        db.add(fr_trans)

    await db.flush()
    return question


class TestQuestionDetail:
    async def test_published_question_hides_the_answer(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """Published free_text reveals stem but not key_points or explanation"""
        question = await _setup_question(
            db,
            question_kind=QuestionKind.free_text,
            question_status=QuestionStatus.published,
            en_stem="What is recursion?",
            en_explanation="Recursion is when a function calls itself",
            key_points=["base case", "recursive call"],
        )

        r = await client.get(f"/api/v1/questions/{question.id}")
        assert r.status_code == 200
        body = r.json()
        assert body["stem"] == "What is recursion?"
        assert "key_points" not in body
        assert "explanation" not in body
        assert body["is_fallback"] is False

    async def test_locale_and_english_fallback(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """Prefers the requested locale, falls back to English"""
        question = await _setup_question(
            db,
            en_stem="English question",
            fr_stem="Question française",
        )

        # French exists, use it
        r = await client.get(f"/api/v1/questions/{question.id}?locale=fr")
        assert r.status_code == 200
        assert r.json()["stem"] == "Question française"
        assert r.json()["title"] == "Titre français"
        assert r.json()["is_fallback"] is False

        # Spanish is not served: the request resolves to English, the default,
        # which is then the language asked for and not a fallback
        r = await client.get(f"/api/v1/questions/{question.id}?locale=es")
        assert r.status_code == 200
        assert r.json()["stem"] == "English question"
        assert r.json()["title"] == "English title"
        assert r.json()["is_fallback"] is False

    async def test_question_list_hides_the_answer(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """The public list serializes whole `Question` rows, which carry the key points"""
        question = await _setup_question(
            db,
            en_explanation="LIST-EXPLANATION",
            key_points=["LIST-KEY-POINT"],
        )

        r = await client.get("/api/v1/questions", params={"topic": "t-detail"})
        assert r.status_code == 200
        assert [item["id"] for item in r.json()["items"]] == [question.id]
        assert "key_points" not in r.text
        assert "LIST-KEY-POINT" not in r.text
        assert "LIST-EXPLANATION" not in r.text

    async def test_question_list_serves_stem_and_tags_in_the_requested_locale(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """Each list item carries its wording, its tags and the fallback flag"""
        question = await _setup_question(
            db, en_stem="English question", fr_stem="Question française"
        )
        for slug in ("t-detail-tag-b", "t-detail-tag-a"):
            tag = Tag(slug=slug)
            db.add(tag)
            await db.flush()
            db.add(QuestionTag(question_id=question.id, tag_id=tag.id))
        await db.flush()

        r = await client.get(
            "/api/v1/questions", params={"topic": "t-detail", "locale": "fr"}
        )
        assert r.status_code == 200
        [item] = r.json()["items"]
        assert item["stem"] == "Question française"
        assert item["title"] == "Titre français"
        assert item["is_fallback"] is False
        assert item["tags"] == ["t-detail-tag-a", "t-detail-tag-b"]
        assert "author_id" not in item
        assert "review_note" not in item

        r = await client.get(
            "/api/v1/questions", params={"topic": "t-detail", "locale": "es"}
        )
        [item] = r.json()["items"]
        assert item["stem"] == "English question"
        assert item["title"] == "English title"
        assert item["is_fallback"] is True

    @pytest.mark.parametrize(
        "hidden_status", [QuestionStatus.draft, QuestionStatus.archived]
    )
    async def test_unpublished_question_is_404_for_anonymous(
        self, client: AsyncClient, db: AsyncSession, hidden_status: QuestionStatus
    ) -> None:
        """Drafts and archived questions are hidden from anonymous callers"""
        question = await _setup_question(db, question_status=hidden_status)

        r = await client.get(f"/api/v1/questions/{question.id}")
        assert r.status_code == 404

    async def test_unpublished_question_is_404_for_a_student(
        self, client: AsyncClient, db: AsyncSession, as_user
    ) -> None:
        """Being logged in is not enough: only moderators see unpublished questions"""
        question = await _setup_question(db, question_status=QuestionStatus.draft)

        await as_user(
            email="student@example.com",
            display_name="student",
            role=Role.student,
        )
        r = await client.get(f"/api/v1/questions/{question.id}")
        assert r.status_code == 404

    async def test_unpublished_question_is_visible_to_moderator(
        self, client: AsyncClient, db: AsyncSession, as_user
    ) -> None:
        """Moderators can see unpublished questions"""
        question = await _setup_question(
            db,
            question_status=QuestionStatus.draft,
        )

        await as_user(
            email="mod@example.com",
            display_name="moderator",
            role=Role.moderator,
        )
        r = await client.get(f"/api/v1/questions/{question.id}")
        assert r.status_code == 200

    async def test_unknown_question_is_404(self, client: AsyncClient) -> None:
        """Fetching a non-existent question returns 404"""
        r = await client.get("/api/v1/questions/999999999")
        assert r.status_code == 404

    async def test_free_text_without_key_points_cannot_publish(
        self, db: AsyncSession
    ) -> None:
        """free_text with empty key_points fails validation"""
        question = await _setup_question(
            db,
            question_kind=QuestionKind.free_text,
            en_stem="Question",
            key_points=[],
        )

        with pytest.raises(HTTPException) as exc_info:
            await assert_publishable(db, question)
        assert exc_info.value.status_code == 422
        assert "key points" in str(exc_info.value).lower()

    async def test_free_text_with_a_lone_choice_cannot_publish(
        self, db: AsyncSession
    ) -> None:
        """A written question may carry choices for the duel, but not a single one"""
        question = await _setup_question(
            db,
            question_kind=QuestionKind.free_text,
            en_stem="Question",
            key_points=["point"],
        )

        choice = Choice(question_id=question.id, position=0, is_correct=True)
        db.add(choice)
        await db.flush()

        with pytest.raises(HTTPException) as exc_info:
            await assert_publishable(db, question)
        assert exc_info.value.status_code == 422
        assert "at least 2 choices" in str(exc_info.value).lower()

    async def test_free_text_with_key_points_is_publishable(
        self, db: AsyncSession
    ) -> None:
        """free_text with non-empty key_points passes validation"""
        question = await _setup_question(
            db,
            question_kind=QuestionKind.free_text,
            en_stem="Question",
            key_points=["first point", "second point"],
        )

        await assert_publishable(db, question)

    async def test_choice_question_rules_are_unchanged(
        self, db: AsyncSession
    ) -> None:
        """Existing validation for single_choice remains"""
        question = await _setup_question(
            db,
            question_kind=QuestionKind.single_choice,
            en_stem="Question",
        )

        choice = Choice(question_id=question.id, position=0, is_correct=True)
        db.add(choice)
        await db.flush()

        with pytest.raises(HTTPException) as exc_info:
            await assert_publishable(db, question)
        assert exc_info.value.status_code == 422
        exc_text = str(exc_info.value).lower()
        assert "at least 2 choices" in exc_text
