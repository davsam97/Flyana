"""Tests for the TOML content loader"""

from __future__ import annotations

from pathlib import Path
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import (
    Choice, ChoiceTranslation, LearningPath, Lesson, LessonTranslation, PathModule,
    Question, QuestionTag, QuestionTranslation, Tag, Topic, TopicTranslation
)
from app.models.enums import QuestionKind, QuestionStatus
from seeds import ContentError, load_content


def write(directory: Path, name: str, text: str) -> None:
    """Helper: write a string to a file in the given directory"""
    (directory / name).write_text(text, encoding="utf-8")


class TestContentLoader:
    """Loads versioned TOML content files into the database"""

    async def test_loads_topics_questions_translations_and_tags(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """Loads a complete, valid file with topics, questions, and translations"""
        content = """
[[topics]]
slug = "t-loader-parent"
position = 0

[topics.translations.en]
name = "Parent Topic"

[topics.translations.fr]
name = "Sujet Parent"

[[topics]]
slug = "t-loader-child"
parent = "t-loader-parent"
position = 1

[topics.translations.en]
name = "Child Topic"

[topics.translations.fr]
name = "Sujet Enfant"

[[questions]]
slug = "t-loader-q1"
topic = "t-loader-child"
kind = "free_text"
difficulty = 1500
tags = ["t-loader-tag1", "t-loader-tag2"]
key_points = ["stores address", "dereference with *"]

[questions.translations.en]
title = "Test title"
stem = "What is a pointer?"
explanation = "A pointer holds an address."

[questions.translations.fr]
title = "Test title"
stem = "Qu'est-ce qu'un pointeur?"
explanation = "Un pointeur contient une adresse."
"""
        write(tmp_path, "content.toml", content)

        summary = await load_content(db, tmp_path)

        assert summary.files == 1
        assert summary.topics == 2
        assert summary.questions == 1

        q = await db.scalar(
            select(Question).where(Question.slug == "t-loader-q1")
        )
        assert q is not None
        assert q.kind == QuestionKind.free_text
        assert q.status == QuestionStatus.published
        assert q.author_id is None
        assert q.difficulty_rating == Decimal("1500")
        assert q.key_points == ["stores address", "dereference with *"]

        en_trans = await db.scalar(
            select(QuestionTranslation).where(
                QuestionTranslation.question_id == q.id,
                QuestionTranslation.locale == "en",
            )
        )
        assert en_trans is not None
        assert en_trans.title == "Test title"
        assert en_trans.stem == "What is a pointer?"

        fr_trans = await db.scalar(
            select(QuestionTranslation).where(
                QuestionTranslation.question_id == q.id,
                QuestionTranslation.locale == "fr",
            )
        )
        assert fr_trans is not None
        assert fr_trans.stem == "Qu'est-ce qu'un pointeur?"

        tags = list(await db.scalars(
            select(Tag).where(Tag.slug.in_(["t-loader-tag1", "t-loader-tag2"]))
        ))
        assert len(tags) == 2

        q_tags = list(await db.scalars(
            select(QuestionTag).where(QuestionTag.question_id == q.id)
        ))
        assert len(q_tags) == 2

        parent = await db.scalar(
            select(Topic).where(Topic.slug == "t-loader-parent")
        )
        child = await db.scalar(
            select(Topic).where(Topic.slug == "t-loader-child")
        )
        assert parent is not None
        assert child is not None
        assert child.parent_id == parent.id

    async def test_reload_is_idempotent(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """Reloading the same content produces the same state"""
        content = """
[[questions]]
slug = "t-loader-idempotent"
topic = "t-loader-topic"
kind = "free_text"
tags = ["rank-05"]
key_points = ["point1", "point2"]

[questions.translations.en]
title = "Test title"
stem = "Test question"

[questions.translations.fr]
title = "Test title"
stem = "Question test"
"""

        base_topic = Topic(slug="t-loader-topic", position=0)
        db.add(base_topic)
        await db.flush()
        topic_id = base_topic.id

        write(tmp_path, "content.toml", content)

        summary1 = await load_content(db, tmp_path)
        q_id_1 = (
            await db.scalar(
                select(Question.id).where(Question.slug == "t-loader-idempotent")
            )
        )

        summary2 = await load_content(db, tmp_path)
        q_id_2 = (
            await db.scalar(
                select(Question.id).where(Question.slug == "t-loader-idempotent")
            )
        )

        # Same question ID = same row
        assert q_id_1 == q_id_2
        assert summary1.questions == 1
        assert summary2.questions == 1

        # Exactly 2 translations (en, fr), not 4
        translations = list(await db.scalars(
            select(QuestionTranslation).where(
                QuestionTranslation.question_id == q_id_1
            )
        ))
        assert len(translations) == 2

        tag_links = list(await db.scalars(
            select(QuestionTag).where(QuestionTag.question_id == q_id_1)
        ))
        assert len(tag_links) == 1

    async def test_reload_updates_wording_but_keeps_difficulty(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """Difficulty is fixed at insertion; wording can change on reload"""
        base_topic = Topic(slug="t-loader-topic", position=0)
        db.add(base_topic)
        await db.flush()

        content1 = """
[[questions]]
slug = "t-loader-difficulty-test"
topic = "t-loader-topic"
kind = "free_text"
difficulty = 1200
key_points = ["point"]

[questions.translations.en]
title = "Test title"
stem = "Original wording"

[questions.translations.fr]
title = "Test title"
stem = "Formulation originale"
"""
        write(tmp_path, "content.toml", content1)
        await load_content(db, tmp_path)

        q = await db.scalar(
            select(Question).where(Question.slug == "t-loader-difficulty-test")
        )
        assert q.difficulty_rating == Decimal("1200")

        # Manually increase difficulty to simulate student results
        await db.execute(
            update(Question)
            .where(Question.slug == "t-loader-difficulty-test")
            .values(difficulty_rating=Decimal("1500"))
        )

        # Reload with different wording AND different difficulty in the file
        content2 = """
[[questions]]
slug = "t-loader-difficulty-test"
topic = "t-loader-topic"
kind = "free_text"
difficulty = 900
key_points = ["updated point"]

[questions.translations.en]
title = "Test title"
stem = "New wording"

[questions.translations.fr]
title = "Test title"
stem = "Nouvelle formulation"
"""
        write(tmp_path, "content.toml", content2)
        await load_content(db, tmp_path)

        # Check: wording and key points follow the file, difficulty stayed at 1500
        q = await db.scalar(
            select(Question).where(Question.slug == "t-loader-difficulty-test")
        )
        en_trans = await db.scalar(
            select(QuestionTranslation).where(
                QuestionTranslation.question_id == q.id,
                QuestionTranslation.locale == "en",
            )
        )
        assert en_trans.stem == "New wording"
        # Re-read from the database: the ORM may otherwise hand back its cached copy
        await db.refresh(q)
        assert q.key_points == ["updated point"]
        assert q.difficulty_rating == Decimal("1500")  # NOT 900

    async def test_a_written_question_may_carry_duel_choices(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """The duel plays the exam questions, so a free_text one may offer choices"""
        content = """
[[topics]]
slug = "t"
[topics.translations.en]
name = "T"

[topics.translations.fr]
name = "T"

[[questions]]
slug = "q-written-with-choices"
topic = "t"
kind = "free_text"
key_points = ["KP the terminator is a zero byte"]
[questions.translations.en]
title = "The end of a string"
stem = "How does C know where a string ends?"

[questions.translations.fr]
title = "The end of a string"
stem = "How does C know where a string ends?"

[[questions.choices]]
correct = true
text = { en = "A byte worth zero", fr = "Un octet valant zero" }

[[questions.choices]]
text = { en = "Its length sits in the first byte", fr = "Sa longueur est dans le premier octet" }
"""
        write(tmp_path, "content.toml", content)

        await load_content(db, tmp_path)

        question = await db.scalar(
            select(Question).where(Question.slug == "q-written-with-choices")
        )
        assert question is not None
        assert question.kind == QuestionKind.free_text
        assert question.key_points == ["KP the terminator is a zero byte"]

        choices = list(
            await db.scalars(
                select(Choice).where(Choice.question_id == question.id).order_by(Choice.position)
            )
        )
        assert [c.is_correct for c in choices] == [True, False]
        texts = list(
            await db.scalars(
                select(ChoiceTranslation.text).where(
                    ChoiceTranslation.choice_id == choices[0].id
                )
            )
        )
        assert sorted(texts) == ["A byte worth zero", "Un octet valant zero"]

    async def test_two_correct_choices_are_rejected(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """A duel scores one answer: two right ones would make it unplayable"""
        content = """
[[topics]]
slug = "t"
[topics.translations.en]
name = "T"

[topics.translations.fr]
name = "T"

[[questions]]
slug = "q-two-right"
topic = "t"
kind = "free_text"
key_points = ["KP something"]
[questions.translations.en]
title = "T"
stem = "S"

[questions.translations.fr]
title = "T"
stem = "S"

[[questions.choices]]
correct = true
text = { en = "First", fr = "Premier" }

[[questions.choices]]
correct = true
text = { en = "Second", fr = "Second" }
"""
        write(tmp_path, "content.toml", content)

        with pytest.raises(ContentError) as exc:
            await load_content(db, tmp_path)
        assert "exactly 1 correct answer" in str(exc.value)

    async def test_unknown_topic_is_rejected(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """A question referencing a nonexistent topic raises ContentError"""
        content = """
[[questions]]
slug = "t-loader-bad-topic"
topic = "nonexistent-topic"
kind = "free_text"
key_points = ["point"]

[questions.translations.en]
title = "Test title"
stem = "Test"

[questions.translations.fr]
title = "Test title"
stem = "Test"
"""
        write(tmp_path, "content.toml", content)

        with pytest.raises(ContentError) as exc_info:
            await load_content(db, tmp_path)

        msg = str(exc_info.value)
        assert "content.toml" in msg
        assert "t-loader-bad-topic" in msg

    async def test_unknown_key_is_rejected(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """A typo in the TOML schema (e.g., keypoints instead of key_points) fails"""
        base_topic = Topic(slug="t-loader-topic", position=0)
        db.add(base_topic)
        await db.flush()

        content = """
[[questions]]
slug = "t-loader-typo"
topic = "t-loader-topic"
kind = "free_text"
keypoints = ["wrong key"]

[questions.translations.en]
title = "Test title"
stem = "Test"

[questions.translations.fr]
title = "Test title"
stem = "Test"
"""
        write(tmp_path, "content.toml", content)

        with pytest.raises(ContentError) as exc_info:
            await load_content(db, tmp_path)

        msg = str(exc_info.value)
        assert "content.toml" in msg

    async def test_published_free_text_without_key_points_is_rejected(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """A published free_text question without key_points fails validation"""
        base_topic = Topic(slug="t-loader-topic", position=0)
        db.add(base_topic)
        await db.flush()

        content = """
[[questions]]
slug = "t-loader-no-keypoints"
topic = "t-loader-topic"
kind = "free_text"
key_points = []

[questions.translations.en]
title = "Test title"
stem = "Test"

[questions.translations.fr]
title = "Test title"
stem = "Test"
"""
        write(tmp_path, "content.toml", content)

        with pytest.raises(ContentError) as exc_info:
            await load_content(db, tmp_path)

        msg = str(exc_info.value)
        assert "t-loader-no-keypoints" in msg

    async def test_duplicate_question_slug_is_rejected(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """Two files with the same question slug raise ContentError"""
        base_topic = Topic(slug="t-loader-topic", position=0)
        db.add(base_topic)
        await db.flush()

        content1 = """
[[questions]]
slug = "t-loader-duplicate"
topic = "t-loader-topic"
kind = "free_text"
key_points = ["point"]

[questions.translations.en]
title = "Test title"
stem = "First file"

[questions.translations.fr]
title = "Test title"
stem = "Premier fichier"
"""

        content2 = """
[[questions]]
slug = "t-loader-duplicate"
topic = "t-loader-topic"
kind = "free_text"
key_points = ["point"]

[questions.translations.en]
title = "Test title"
stem = "Second file"

[questions.translations.fr]
title = "Test title"
stem = "Deuxième fichier"
"""

        write(tmp_path, "file1.toml", content1)
        write(tmp_path, "file2.toml", content2)

        with pytest.raises(ContentError) as exc_info:
            await load_content(db, tmp_path)

        msg = str(exc_info.value)
        assert "t-loader-duplicate" in msg

    async def test_topic_cannot_be_its_own_parent(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """A topic with parent = slug raises ContentError"""
        content = """
[[topics]]
slug = "t-loader-self-parent"
parent = "t-loader-self-parent"

[topics.translations.en]
name = "Bad topic"

[topics.translations.fr]
name = "Bad topic"
"""
        write(tmp_path, "content.toml", content)

        with pytest.raises(ContentError) as exc_info:
            await load_content(db, tmp_path)

        msg = str(exc_info.value)
        assert "cannot be its own parent" in msg

    async def test_invalid_tag_is_rejected_with_file_name(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """A tag breaking the slug format fails at parse time and names the file"""
        content = """
[[questions]]
slug = "t-loader-bad-tag"
topic = "t-loader-topic"
kind = "free_text"
tags = ["Rank_05"]
key_points = ["point"]

[questions.translations.en]
title = "Test title"
stem = "Test"

[questions.translations.fr]
title = "Test title"
stem = "Test"
"""
        write(tmp_path, "tags.toml", content)

        with pytest.raises(ContentError) as exc_info:
            await load_content(db, tmp_path)

        assert "tags.toml" in str(exc_info.value)

    async def test_key_points_under_a_translation_are_rejected(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """key_points written under a translation raises ContentError"""
        base_topic = Topic(slug="t-loader-topic", position=0)
        db.add(base_topic)
        await db.flush()

        content = """
[[questions]]
slug = "t-loader-translation-keypoints"
topic = "t-loader-topic"
kind = "free_text"
key_points = ["point"]

[questions.translations.en]
title = "Test title"
stem = "Test"
key_points = ["wrong"]

[questions.translations.fr]
title = "Test title"
stem = "Test"
"""
        write(tmp_path, "content.toml", content)

        with pytest.raises(ContentError) as exc_info:
            await load_content(db, tmp_path)

        msg = str(exc_info.value)
        assert "content.toml" in msg

    async def test_draft_is_loaded_without_validation(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """A draft question is loaded without validation"""
        base_topic = Topic(slug="t-loader-topic", position=0)
        db.add(base_topic)
        await db.flush()

        content = """
[[questions]]
slug = "t-loader-draft"
topic = "t-loader-topic"
kind = "free_text"
status = "draft"

[questions.translations.en]
title = "Test title"
stem = "Test"

[questions.translations.fr]
title = "Test title"
stem = "Test"
"""
        write(tmp_path, "content.toml", content)

        # Should not raise ContentError even though key_points is missing
        summary = await load_content(db, tmp_path)
        assert summary.questions == 1

        q = await db.scalar(
            select(Question).where(Question.slug == "t-loader-draft")
        )
        assert q is not None
        assert q.status == QuestionStatus.draft

    async def test_archiving_in_the_file_retires_the_question(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """Setting status = archived in the file retires a question"""
        base_topic = Topic(slug="t-loader-topic", position=0)
        db.add(base_topic)
        await db.flush()

        content1 = """
[[questions]]
slug = "t-loader-archive-test"
topic = "t-loader-topic"
kind = "free_text"
key_points = ["point"]

[questions.translations.en]
title = "Test title"
stem = "Original"

[questions.translations.fr]
title = "Test title"
stem = "Original"
"""
        write(tmp_path, "content.toml", content1)
        await load_content(db, tmp_path)

        q = await db.scalar(
            select(Question).where(Question.slug == "t-loader-archive-test")
        )
        original_id = q.id
        assert q.status == QuestionStatus.published

        content2 = """
[[questions]]
slug = "t-loader-archive-test"
topic = "t-loader-topic"
kind = "free_text"
status = "archived"
key_points = ["point"]

[questions.translations.en]
title = "Test title"
stem = "Original"

[questions.translations.fr]
title = "Test title"
stem = "Original"
"""
        write(tmp_path, "content.toml", content2)
        await load_content(db, tmp_path)

        q = await db.scalar(
            select(Question).where(Question.slug == "t-loader-archive-test")
        )
        await db.refresh(q)
        assert q.id == original_id
        assert q.status == QuestionStatus.archived

    async def test_moderation_status_is_refused_in_files(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """status = in_review in a file raises ContentError"""
        base_topic = Topic(slug="t-loader-topic", position=0)
        db.add(base_topic)
        await db.flush()

        content = """
[[questions]]
slug = "t-loader-in-review"
topic = "t-loader-topic"
kind = "free_text"
status = "in_review"
key_points = ["point"]

[questions.translations.en]
title = "Test title"
stem = "Test"

[questions.translations.fr]
title = "Test title"
stem = "Test"
"""
        write(tmp_path, "content.toml", content)

        with pytest.raises(ContentError) as exc_info:
            await load_content(db, tmp_path)

        msg = str(exc_info.value)
        assert "content.toml" in msg

    async def test_translation_without_title_is_rejected(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """Every translation needs a short title, drafts included"""
        base_topic = Topic(slug="t-loader-topic", position=0)
        db.add(base_topic)
        await db.flush()

        content = """
[[questions]]
slug = "t-loader-no-title"
topic = "t-loader-topic"
kind = "free_text"
status = "draft"

[questions.translations.en]
stem = "Test"

[questions.translations.fr]
stem = "Test"
"""
        write(tmp_path, "content.toml", content)

        with pytest.raises(ContentError) as exc_info:
            await load_content(db, tmp_path)

        assert "content.toml" in str(exc_info.value)

    async def test_missing_directory_loads_nothing(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """Loading from a nonexistent directory returns zero counts"""
        nonexistent = tmp_path / "does-not-exist"

        summary = await load_content(db, nonexistent)

        assert summary.files == 0
        assert summary.topics == 0
        assert summary.questions == 0


QUIZ = """
[[questions]]
slug = "t-loader-quiz"
topic = "t-loader-quiz-topic"
kind = "single_choice"

[questions.translations.en]
title = "fork in the child"
stem = "What does fork return in the child?"

[questions.translations.fr]
title = "fork dans l'enfant"
stem = "Que renvoie fork dans l'enfant ?"

[[questions.choices]]
text = { en = "The pid of the child", fr = "Le pid de l'enfant" }

[[questions.choices]]
correct = true
text = { en = "0", fr = "0" }

[[questions.choices]]
text = { en = "-1", fr = "-1" }
"""


class TestChoiceQuestions:
    """single_choice questions carry their choices in the same file"""

    @pytest.fixture(autouse=True)
    async def topic(self, db: AsyncSession) -> None:
        db.add(Topic(slug="t-loader-quiz-topic", position=0))
        await db.flush()

    async def choices_of(self, db: AsyncSession, slug: str) -> list[Choice]:
        return list(await db.scalars(
            select(Choice)
            .join(Question, Question.id == Choice.question_id)
            .where(Question.slug == slug)
            .order_by(Choice.position)
        ))

    async def test_loads_choices_in_file_order_with_translations(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        write(tmp_path, "quiz.toml", QUIZ)

        await load_content(db, tmp_path)

        choices = await self.choices_of(db, "t-loader-quiz")
        assert [c.position for c in choices] == [0, 1, 2]
        assert [c.is_correct for c in choices] == [False, True, False]
        texts = {
            (t.choice_id, t.locale): t.text
            for t in await db.scalars(
                select(ChoiceTranslation).where(
                    ChoiceTranslation.choice_id.in_([c.id for c in choices])
                )
            )
        }
        assert texts[(choices[0].id, "fr")] == "Le pid de l'enfant"
        assert texts[(choices[1].id, "en")] == "0"
        assert len(texts) == 6

    async def test_reload_keeps_choice_ids_and_drops_removed_ones(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """A match remembers the choice each player picked: ids must survive"""
        write(tmp_path, "quiz.toml", QUIZ)
        await load_content(db, tmp_path)
        before = [c.id for c in await self.choices_of(db, "t-loader-quiz")]

        # the right answer moves first, the last choice is dropped
        shorter = QUIZ.replace(
            'text = { en = "The pid of the child", fr = "Le pid de l\'enfant" }',
            'correct = true\ntext = { en = "Zero", fr = "Zéro" }',
        ).replace(
            'correct = true\ntext = { en = "0", fr = "0" }',
            'text = { en = "The pid of the parent", fr = "Le pid du parent" }',
        ).replace(
            '\n[[questions.choices]]\ntext = { en = "-1", fr = "-1" }\n', "\n"
        )
        write(tmp_path, "quiz.toml", shorter)
        await load_content(db, tmp_path)

        after = await self.choices_of(db, "t-loader-quiz")
        assert [c.id for c in after] == before[:2]
        assert [c.is_correct for c in after] == [True, False]
        en = await db.scalar(
            select(ChoiceTranslation.text).where(
                ChoiceTranslation.choice_id == after[0].id,
                ChoiceTranslation.locale == "en",
            )
        )
        assert en == "Zero"

    async def test_two_right_answers_are_rejected(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        write(tmp_path, "quiz.toml", QUIZ.replace(
            'text = { en = "-1"', 'correct = true\ntext = { en = "-1"'
        ))

        with pytest.raises(ContentError, match="exactly 1 correct answer"):
            await load_content(db, tmp_path)

    async def test_free_text_with_choices_is_accepted(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """Since the duel plays the exam content, a written question may offer choices"""
        write(tmp_path, "quiz.toml", QUIZ.replace(
            'kind = "single_choice"', 'kind = "free_text"\nkey_points = ["returns 0"]'
        ))

        summary = await load_content(db, tmp_path)

        assert summary.questions == 1
        # By slug, not by kind: a seeded database holds many written questions
        question = await db.scalar(select(Question).where(Question.slug == "t-loader-quiz"))
        assert question is not None
        assert question.kind == QuestionKind.free_text
        assert question.key_points == ["returns 0"]
        assert len(list(await db.scalars(select(Choice).where(Choice.question_id == question.id)))) >= 2

    async def test_a_single_choice_is_rejected_whatever_the_kind(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        """One proposal is not a question: the guard still holds on written ones"""
        content = """
[[topics]]
slug = "t"
[topics.translations.en]
name = "T"

[topics.translations.fr]
name = "T"

[[questions]]
slug = "q-one-choice"
topic = "t"
kind = "free_text"
key_points = ["KP something"]
[questions.translations.en]
title = "T"
stem = "S"

[questions.translations.fr]
title = "T"
stem = "S"

[[questions.choices]]
correct = true
text = { en = "Alone", fr = "Seule" }
"""
        write(tmp_path, "content.toml", content)

        with pytest.raises(ContentError, match="at least 2 choices"):
            await load_content(db, tmp_path)

    async def test_choice_without_english_is_rejected(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        write(tmp_path, "quiz.toml", QUIZ.replace(
            'text = { en = "-1", fr = "-1" }', 'text = { fr = "-1" }'
        ))

        with pytest.raises(ContentError, match="missing translation: en"):
            await load_content(db, tmp_path)


async def test_shipped_content_loads(db: AsyncSession) -> None:
    """Every file under seeds/content passes validation, the course path included"""
    directory = Path(__file__).resolve().parent.parent / "seeds" / "content"

    summary = await load_content(db, directory)

    assert summary.paths == 1
    learning_path = await db.scalar(
        select(LearningPath).where(LearningPath.slug == "aerospace-basics")
    )
    assert learning_path is not None
    modules = list(await db.scalars(
        select(Topic.slug)
        .join(PathModule, PathModule.topic_id == Topic.id)
        .where(PathModule.path_id == learning_path.id)
        .order_by(PathModule.position)
    ))
    assert modules == [
        "aerodynamics", "flight-mechanics", "propulsion", "orbital-mechanics",
        "space-systems", "avionics", "history",
    ]


MODULE = """
[[topics]]
slug = "t-module"
[topics.translations.en]
name = "Module"
[topics.translations.fr]
name = "Module"

[[lessons]]
slug = "t-module-lesson"
topic = "t-module"
position = 0
title = { en = "Lift", fr = "La portance" }
body = { en = "lessons/lift.en.md", fr = "lessons/lift.fr.md" }

[[questions]]
slug = "t-module-orbital-speed"
topic = "t-module"
kind = "numeric"
answer = 7.67
tolerance = 0.02
unit = "km/s"
source = { label = "NASA JPL, Basics of Space Flight", url = "https://science.nasa.gov/learn/basics-of-space-flight/" }
[questions.translations.en]
title = "Orbital speed"
stem = "Speed on a circular orbit 400 km up?"
[questions.translations.fr]
title = "Vitesse orbitale"
stem = "Vitesse sur une orbite circulaire à 400 km ?"

[[questions]]
slug = "t-module-forces"
topic = "t-module"
kind = "multi_choice"
[questions.translations.en]
title = "Forces"
stem = "Which forces act on an aircraft in level flight?"
[questions.translations.fr]
title = "Forces"
stem = "Quelles forces s'exercent sur un avion en palier ?"
[[questions.choices]]
correct = true
text = { en = "Lift", fr = "La portance" }
[[questions.choices]]
correct = true
text = { en = "Weight", fr = "Le poids" }
[[questions.choices]]
text = { en = "Centrifugal force", fr = "La force centrifuge" }

[[paths]]
slug = "t-path"
[paths.translations.en]
title = "Path"
[paths.translations.fr]
title = "Parcours"
[[paths.modules]]
topic = "t-module"
quiz_questions = 12
"""


def write_module(root: Path, text: str = MODULE) -> None:
    """A module in its own folder, as the shipped content is laid out"""
    folder = root / "01-module"
    (folder / "lessons").mkdir(parents=True)
    write(folder, "module.toml", text)
    write(folder / "lessons", "lift.en.md", "# Lift\n\nThe wing deflects air downward.\n")
    write(folder / "lessons", "lift.fr.md", "# La portance\n\nL'aile dévie l'air vers le bas.\n")


class TestFlyanaContent:
    """Lessons, numeric and multi-choice questions, sources and paths"""

    async def test_a_module_folder_loads_everything(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        write_module(tmp_path)

        summary = await load_content(db, tmp_path)

        assert (summary.files, summary.lessons, summary.questions, summary.paths) == (1, 1, 2, 1)

        lesson = await db.scalar(select(Lesson).where(Lesson.slug == "t-module-lesson"))
        assert lesson is not None
        bodies = {
            row.locale: row
            for row in await db.scalars(
                select(LessonTranslation).where(LessonTranslation.lesson_id == lesson.id)
            )
        }
        assert bodies["fr"].title == "La portance"
        assert bodies["fr"].body.startswith("# La portance")
        assert bodies["en"].body.startswith("# Lift")

        numeric = await db.scalar(
            select(Question).where(Question.slug == "t-module-orbital-speed")
        )
        assert numeric is not None
        assert numeric.kind == QuestionKind.numeric
        assert numeric.numeric_answer == Decimal("7.67")
        assert numeric.tolerance_rel == Decimal("0.02")
        assert numeric.unit == "km/s"
        assert numeric.source_label == "NASA JPL, Basics of Space Flight"
        assert numeric.source_url is not None and numeric.source_url.startswith("https://")

        forces = await db.scalar(select(Question).where(Question.slug == "t-module-forces"))
        assert forces is not None
        assert forces.kind == QuestionKind.multi_choice
        correct = list(await db.scalars(
            select(Choice.is_correct).where(Choice.question_id == forces.id).order_by(Choice.position)
        ))
        assert correct == [True, True, False]

        module = await db.scalar(
            select(PathModule)
            .join(LearningPath, LearningPath.id == PathModule.path_id)
            .where(LearningPath.slug == "t-path")
        )
        assert module is not None and module.min_questions == 12

    async def test_reloading_a_module_is_idempotent(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        write_module(tmp_path)
        await load_content(db, tmp_path)
        await load_content(db, tmp_path)

        lessons = list(await db.scalars(select(Lesson).where(Lesson.slug == "t-module-lesson")))
        assert len(lessons) == 1
        translations = list(await db.scalars(
            select(LessonTranslation).where(LessonTranslation.lesson_id == lessons[0].id)
        ))
        assert len(translations) == 2
        modules = list(await db.scalars(
            select(PathModule)
            .join(LearningPath, LearningPath.id == PathModule.path_id)
            .where(LearningPath.slug == "t-path")
        ))
        assert len(modules) == 1

    @pytest.mark.parametrize(
        ("old", "new", "message"),
        [
            # Each language is required, whatever the entry
            ("[questions.translations.fr]\ntitle = \"Vitesse orbitale\"\nstem = \"Vitesse sur une orbite circulaire à 400 km ?\"\n",
             "", "missing translation: fr"),
            ('title = { en = "Lift", fr = "La portance" }', 'title = { en = "Lift" }',
             "missing translation: fr"),
            ('text = { en = "Weight", fr = "Le poids" }', 'text = { en = "Weight" }',
             "missing translation: fr"),
            # A numeric question carries its answer key, and only it does
            ("answer = 7.67\n", "", "needs `answer` and `tolerance`"),
            ("tolerance = 0.02\n", "tolerance = 0.9\n", "less than or equal to 0.5"),
            ('kind = "multi_choice"\n', 'kind = "multi_choice"\nunit = "N"\n',
             "belong to numeric questions"),
            # A source link must be a full https address
            ('url = "https://science.nasa.gov/learn/basics-of-space-flight/"',
             'url = "javascript:alert(1)"', "url"),
            # A lesson body stays inside the content directory
            ('en = "lessons/lift.en.md"', 'en = "../../../etc/passwd.md"', "outside the content directory"),
            ('en = "lessons/lift.en.md"', 'en = "lessons/missing.en.md"', "cannot read lesson body"),
            # A path needs at least one module
            ('[[paths.modules]]\ntopic = "t-module"\nquiz_questions = 12\n', "", "modules"),
        ],
    )
    async def test_invalid_module_is_rejected(
        self, db: AsyncSession, tmp_path: Path, old: str, new: str, message: str
    ) -> None:
        assert old in MODULE
        write_module(tmp_path, MODULE.replace(old, new))

        with pytest.raises(ContentError) as exc_info:
            await load_content(db, tmp_path)

        assert message in str(exc_info.value)

    async def test_a_numeric_question_with_choices_is_rejected(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        text = MODULE.replace(
            '[[questions]]\nslug = "t-module-forces"',
            '[[questions.choices]]\ncorrect = true\ntext = { en = "7.7", fr = "7,7" }\n\n'
            '[[questions]]\nslug = "t-module-forces"',
        )
        write_module(tmp_path, text)

        with pytest.raises(ContentError, match="no choices"):
            await load_content(db, tmp_path)

    async def test_a_multi_choice_question_needs_a_right_choice(
        self, db: AsyncSession, tmp_path: Path
    ) -> None:
        write_module(tmp_path, MODULE.replace("correct = true\ntext = { en = \"Lift\"", "text = { en = \"Lift\"").replace(
            "correct = true\ntext = { en = \"Weight\"", "text = { en = \"Weight\""
        ))

        with pytest.raises(ContentError, match="at least 1 correct answer"):
            await load_content(db, tmp_path)


async def test_archived_topics_leave_the_topic_tree(client: AsyncClient, db: AsyncSession) -> None:
    """A retired topic and everything below it disappear from listings"""
    retired = Topic(slug="t-archived-parent", position=0, archived=True)
    db.add(retired)
    await db.flush()
    db.add(Topic(slug="t-archived-child", position=0, parent_id=retired.id))
    db.add(Topic(slug="t-live", position=0))
    await db.flush()

    r = await client.get("/api/v1/topics")

    slugs = {topic["slug"] for topic in r.json()}
    assert "t-live" in slugs
    assert "t-archived-parent" not in slugs
    assert "t-archived-child" not in slugs
