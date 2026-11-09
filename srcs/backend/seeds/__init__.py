"""Loads versioned content files (TOML, plus Markdown lessons) into the database

Content files are reviewed in pull requests and then seeded via this module.
The process is idempotent: re-running yields the same database state,
never creating duplicates.

Idempotence stems from `ON CONFLICT DO UPDATE` on the `slug` natural key.

Every `*.toml` under the content directory is read, at any depth, so each
module keeps its questions and its lessons in its own folder. A lesson's
TOML entry names its Markdown files, relative to that TOML file.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal, Self

from fastapi import HTTPException
from pydantic import (
    AfterValidator, BaseModel, ConfigDict, Field, ValidationError, model_validator
)
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.i18n import SUPPORTED
from app.models.content import (
    Choice, ChoiceTranslation, LearningPath, LearningPathTranslation, Lesson,
    LessonTranslation, PathModule, Question, QuestionTag, QuestionTranslation, Tag,
    Topic, TopicTranslation
)
from app.models.enums import PathLevel, QuestionKind, QuestionStatus
from app.services.validation import assert_publishable


SLUG = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"

# Flyana is written in both languages: a missing one would silently fall back
# to the other, so every translated field must carry both
Locale = Literal["en", "fr"]
LOCALES: tuple[Locale, ...] = ("en", "fr")
assert set(LOCALES) == set(SUPPORTED), "the content schema must follow app.i18n.SUPPORTED"

# What a content file may set as a status. `in_review` and `rejected` are left
# over from an in-app moderation workflow that no longer exists, and are refused
FileStatus = Literal["draft", "published", "archived"]


def _both_locales[T](value: dict[Locale, T]) -> dict[Locale, T]:
    """Refuses a translated field that lacks one of the served languages"""
    missing = set(LOCALES) - value.keys()
    if missing:
        raise ValueError(f"missing translation: {', '.join(sorted(missing))}")
    return value


BothLocales = AfterValidator(_both_locales)


class ContentError(Exception):
    """Raised when a content file cannot be loaded"""

    pass


@dataclass
class LoadSummary:
    """Counts of loaded resources"""

    files: int
    topics: int
    questions: int
    lessons: int = 0
    paths: int = 0


class TopicTranslationIn(BaseModel):
    """Translations of one topic into one language"""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class TopicIn(BaseModel):
    """A topic that organizes questions hierarchically"""

    model_config = ConfigDict(extra="forbid")

    slug: str = Field(pattern=SLUG, max_length=64)
    parent: str | None = None
    position: int = 0
    translations: Annotated[dict[Locale, TopicTranslationIn], BothLocales]


class QuestionTranslationIn(BaseModel):
    """Translations of one question into one language"""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=120)
    stem: str = Field(min_length=1)
    explanation: str | None = None


class ChoiceIn(BaseModel):
    """One possible answer of a choice question, in every language at once

    The order in the file is the order shown to players
    """

    model_config = ConfigDict(extra="forbid")

    correct: bool = False
    text: Annotated[dict[Locale, Annotated[str, Field(min_length=1)]], BothLocales]


class SourceIn(BaseModel):
    """Where the right answer of a question can be checked"""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1)
    url: str | None = Field(default=None, pattern=r"^https://\S+$")


class QuestionIn(BaseModel):
    """A question, by `kind`:

    - `single_choice`: exactly one right choice
    - `multi_choice`: every right choice must be ticked, and only those
    - `numeric`: a number in `unit`, right within `tolerance` of `answer`
      (relative: 0.02 accepts ±2 %)
    - `free_text`: graded by the model against `key_points`, dormant in Flyana

    The counts of choices and right answers are checked by `assert_publishable`,
    like any other rule that spans several rows
    """

    model_config = ConfigDict(extra="forbid")

    slug: str = Field(pattern=SLUG, max_length=96)
    topic: str
    kind: Literal["free_text", "single_choice", "multi_choice", "numeric"]
    difficulty: Decimal = Decimal("1200")
    # The file owns the status: `draft` keeps a question hidden while it is being
    # written, `archived` retires it
    status: FileStatus = "published"
    # Annotated per item: a `pattern` on `list[str]` itself never reaches the
    # elements, so a bad tag is rejected here at parse time, where the
    # resulting ContentError still names the file
    tags: list[Annotated[str, Field(pattern=SLUG, max_length=64)]] = Field(default_factory=list)
    # One grid per question, written in English whatever the student's
    # language, so every student is graded on the same criteria
    key_points: list[str] = Field(default_factory=list)
    answer: Decimal | None = None
    tolerance: Decimal | None = Field(default=None, gt=0, le=Decimal("0.5"))
    unit: str | None = Field(default=None, min_length=1, max_length=32)
    source: SourceIn | None = None
    translations: Annotated[dict[Locale, QuestionTranslationIn], BothLocales]
    choices: list[ChoiceIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def _numeric_fields_match_the_kind(self) -> Self:
        """The answer key of a numeric question, and nothing of it elsewhere"""
        if self.kind == "numeric":
            if self.answer is None or self.tolerance is None:
                raise ValueError("a numeric question needs `answer` and `tolerance`")
            if self.choices:
                raise ValueError("a numeric question has no choices")
        elif self.answer is not None or self.tolerance is not None or self.unit is not None:
            raise ValueError("`answer`, `tolerance` and `unit` belong to numeric questions")
        return self


class LessonIn(BaseModel):
    """One page of a module's course

    `body` names a Markdown file per language, relative to the TOML file
    """

    model_config = ConfigDict(extra="forbid")

    slug: str = Field(pattern=SLUG, max_length=96)
    topic: str
    position: int = 0
    status: FileStatus = "published"
    title: Annotated[dict[Locale, Annotated[str, Field(min_length=1, max_length=160)]], BothLocales]
    body: Annotated[dict[Locale, Annotated[str, Field(pattern=r"^[\w./-]+\.md$")]], BothLocales]


class PathTranslationIn(BaseModel):
    """The title of a learning path in one language"""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=160)
    description: str | None = None


class PathModuleIn(BaseModel):
    """One step of a learning path: a topic and the length of its check quiz"""

    model_config = ConfigDict(extra="forbid")

    topic: str
    quiz_questions: int = Field(default=10, ge=1, le=50)


class PathIn(BaseModel):
    """An ordered course through several topics, in the order listed"""

    model_config = ConfigDict(extra="forbid")

    slug: str = Field(pattern=SLUG, max_length=64)
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    status: FileStatus = "published"
    translations: Annotated[dict[Locale, PathTranslationIn], BothLocales]
    modules: list[PathModuleIn] = Field(min_length=1)


class ContentFile(BaseModel):
    """The schema of one TOML file in `seeds/content/`"""

    model_config = ConfigDict(extra="forbid")

    topics: list[TopicIn] = Field(default_factory=list)
    questions: list[QuestionIn] = Field(default_factory=list)
    lessons: list[LessonIn] = Field(default_factory=list)
    paths: list[PathIn] = Field(default_factory=list)


async def load_content(db: AsyncSession, directory: Path) -> LoadSummary:
    """Loads all TOML files from `directory` into the database.

    Does not commit. On `ContentError` rows may already sit in the open
    transaction, so the caller must roll back, as `seeds/__main__.py` does.
    """
    files = sorted(directory.rglob("*.toml")) if directory.is_dir() else []

    # --- Parse all files, validating shape early ---
    all_topics: list[tuple[Path, TopicIn]] = []
    all_questions: list[tuple[Path, QuestionIn]] = []
    all_lessons: list[tuple[Path, LessonIn, dict[Locale, str]]] = []
    all_paths: list[tuple[Path, PathIn]] = []

    for path in files:
        try:
            raw = tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise ContentError(f"{path.name}: invalid TOML — {exc}") from exc

        try:
            content_file = ContentFile.model_validate(raw)
        except ValidationError as exc:
            raise ContentError(f"{path.name}: {exc}") from exc

        all_topics.extend((path, t) for t in content_file.topics)
        all_questions.extend((path, q) for q in content_file.questions)
        all_paths.extend((path, learning_path) for learning_path in content_file.paths)
        for lesson in content_file.lessons:
            bodies = {
                locale: _read_lesson_body(directory, path, name)
                for locale, name in lesson.body.items()
            }
            all_lessons.append((path, lesson, bodies))

    # --- Detect duplicate slugs (same slug in two places is an error) ---
    topic_slugs: dict[str, Path] = {}
    for path, topic in all_topics:
        if topic.slug in topic_slugs:
            raise ContentError(
                f"duplicate topic slug '{topic.slug}' in {topic_slugs[topic.slug].name} "
                f"and {path.name}"
            )
        topic_slugs[topic.slug] = path

    question_slugs: dict[str, Path] = {}
    for path, question in all_questions:
        if question.slug in question_slugs:
            raise ContentError(
                f"duplicate question slug '{question.slug}' in {question_slugs[question.slug].name} "
                f"and {path.name}"
            )
        question_slugs[question.slug] = path

    for kind, entries in (
        ("lesson", [(path, lesson.slug) for path, lesson, _ in all_lessons]),
        ("path", [(path, learning_path.slug) for path, learning_path in all_paths]),
    ):
        seen: dict[str, Path] = {}
        for path, slug in entries:
            if slug in seen:
                raise ContentError(
                    f"duplicate {kind} slug '{slug}' in {seen[slug].name} and {path.name}"
                )
            seen[slug] = path

    # --- Topics, pass 1: upsert all topics and collect IDs ---
    topic_id_by_slug: dict[str, int] = {}

    for path, topic in all_topics:
        insert_topic = pg_insert(Topic).values(slug=topic.slug, position=topic.position)
        upsert_topic = insert_topic.on_conflict_do_update(
            index_elements=["slug"],
            set_={"position": insert_topic.excluded.position},
        ).returning(Topic.id)
        topic_id = (await db.execute(upsert_topic)).scalar_one()
        topic_id_by_slug[topic.slug] = topic_id

        await db.execute(
            delete(TopicTranslation).where(TopicTranslation.topic_id == topic_id)
        )
        for locale in SUPPORTED:
            if locale in topic.translations:
                topic_tr = topic.translations[locale]
                db.add(
                    TopicTranslation(
                        topic_id=topic_id,
                        locale=locale,
                        name=topic_tr.name,
                        description=topic_tr.description,
                    )
                )

    # --- Topics, pass 2: resolve parent relationships ---
    for path, topic in all_topics:
        topic_id = topic_id_by_slug[topic.slug]

        if topic.parent is None:
            parent_id = None
        elif topic.parent == topic.slug:
            raise ContentError(
                f"{path.name}: topic '{topic.slug}' cannot be its own parent"
            )
        else:
            if topic.parent in topic_id_by_slug:
                parent_id = topic_id_by_slug[topic.parent]
            else:
                parent_id = await db.scalar(
                    select(Topic.id).where(Topic.slug == topic.parent)
                )
                if parent_id is None:
                    raise ContentError(
                        f"{path.name}: topic '{topic.slug}' references unknown parent "
                        f"'{topic.parent}'"
                    )

        await db.execute(
            update(Topic).where(Topic.id == topic_id).values(parent_id=parent_id)
        )

    # --- Tags: upsert all unique tag slugs ---
    all_tag_slugs: set[str] = set()
    for path, question in all_questions:
        all_tag_slugs.update(question.tags)

    if all_tag_slugs:
        await db.execute(
            pg_insert(Tag).values([{"slug": s} for s in all_tag_slugs]).on_conflict_do_nothing(
                index_elements=["slug"]
            )
        )

    tag_id_by_slug: dict[str, int] = {}
    if all_tag_slugs:
        rows = await db.execute(
            select(Tag.slug, Tag.id).where(Tag.slug.in_(all_tag_slugs))
        )
        # The lookup below goes from slug to id, so key on the slug explicitly:
        # `dict(rows)` keys on whichever column comes first and silently inverts
        tag_id_by_slug = {slug: tag_id for slug, tag_id in rows}

    async def resolve_topic(path: Path, what: str, topic_slug: str) -> int:
        """The id of a topic named by an entry, loaded now or already in the database"""
        if topic_slug in topic_id_by_slug:
            return topic_id_by_slug[topic_slug]
        existing_topic_id = await db.scalar(select(Topic.id).where(Topic.slug == topic_slug))
        if existing_topic_id is None:
            raise ContentError(
                f"{path.name}: {what} references unknown topic '{topic_slug}'"
            )
        topic_id_by_slug[topic_slug] = existing_topic_id
        return existing_topic_id

    # --- Questions ---
    for path, question in all_questions:
        topic_id = await resolve_topic(path, f"question '{question.slug}'", question.topic)

        insert_question = pg_insert(Question).values(
            slug=question.slug,
            topic_id=topic_id,
            kind=QuestionKind(question.kind),
            difficulty_rating=question.difficulty,
            status=QuestionStatus(question.status),
            key_points=question.key_points,
            numeric_answer=question.answer,
            tolerance_rel=question.tolerance,
            unit=question.unit,
            source_label=question.source.label if question.source else None,
            source_url=question.source.url if question.source else None,
        )
        upsert_question = insert_question.on_conflict_do_update(
            index_elements=["slug"],
            set_={
                "topic_id": insert_question.excluded.topic_id,
                "kind": insert_question.excluded.kind,
                # The file owns the status, so a reload applies it: setting
                # `archived` in the file retires the question. Deleting an entry
                # from its file leaves its row as last loaded — the loader never
                # removes rows — so retire a question by archiving it
                "status": insert_question.excluded.status,
                "key_points": insert_question.excluded.key_points,
                "numeric_answer": insert_question.excluded.numeric_answer,
                "tolerance_rel": insert_question.excluded.tolerance_rel,
                "unit": insert_question.excluded.unit,
                "source_label": insert_question.excluded.source_label,
                "source_url": insert_question.excluded.source_url,
                # `difficulty_rating` is left out: after insertion it evolves
                # only through student results
                "updated_at": func.now(),
            },
        ).returning(Question.id)
        question_id = (await db.execute(upsert_question)).scalar_one()

        await db.execute(
            delete(QuestionTranslation).where(QuestionTranslation.question_id == question_id)
        )
        for locale in SUPPORTED:
            if locale in question.translations:
                question_tr = question.translations[locale]
                db.add(
                    QuestionTranslation(
                        question_id=question_id,
                        locale=locale,
                        title=question_tr.title,
                        stem=question_tr.stem,
                        explanation=question_tr.explanation,
                    )
                )

        await db.execute(
            delete(QuestionTag).where(QuestionTag.question_id == question_id)
        )
        for tag_slug in question.tags:
            tag_id = tag_id_by_slug[tag_slug]
            db.add(QuestionTag(question_id=question_id, tag_id=tag_id))

        await _replace_choices(db, question_id, question.choices)

        # Only published questions are validated: a draft may be incomplete,
        # and an archived one is no longer shown
        if question.status == "published":
            # `populate_existing`: the raw upserts above bypass the identity map,
            # which would otherwise hand back the stale cached question
            question_entity = await db.get(Question, question_id, populate_existing=True)
            if question_entity is None:
                raise ContentError(f"{path.name}: question '{question.slug}' vanished after upsert")
            try:
                await assert_publishable(db, question_entity)
            except HTTPException as exc:
                raise ContentError(
                    f"{path.name}: question '{question.slug}': {exc.detail}"
                ) from exc

    # --- Lessons ---
    for path, lesson, bodies in all_lessons:
        topic_id = await resolve_topic(path, f"lesson '{lesson.slug}'", lesson.topic)
        insert_lesson = pg_insert(Lesson).values(
            slug=lesson.slug,
            topic_id=topic_id,
            position=lesson.position,
            status=QuestionStatus(lesson.status),
        )
        upsert_lesson = insert_lesson.on_conflict_do_update(
            index_elements=["slug"],
            set_={
                "topic_id": insert_lesson.excluded.topic_id,
                "position": insert_lesson.excluded.position,
                "status": insert_lesson.excluded.status,
            },
        ).returning(Lesson.id)
        lesson_id = (await db.execute(upsert_lesson)).scalar_one()

        await db.execute(delete(LessonTranslation).where(LessonTranslation.lesson_id == lesson_id))
        for locale in LOCALES:
            db.add(
                LessonTranslation(
                    lesson_id=lesson_id,
                    locale=locale,
                    title=lesson.title[locale],
                    body=bodies[locale],
                )
            )

    # --- Learning paths ---
    for path, learning_path in all_paths:
        insert_path = pg_insert(LearningPath).values(
            slug=learning_path.slug,
            level=PathLevel(learning_path.level),
            status=QuestionStatus(learning_path.status),
        )
        upsert_path = insert_path.on_conflict_do_update(
            index_elements=["slug"],
            set_={
                "level": insert_path.excluded.level,
                "status": insert_path.excluded.status,
            },
        ).returning(LearningPath.id)
        path_id = (await db.execute(upsert_path)).scalar_one()

        await db.execute(
            delete(LearningPathTranslation).where(LearningPathTranslation.path_id == path_id)
        )
        for locale in LOCALES:
            path_tr = learning_path.translations[locale]
            db.add(
                LearningPathTranslation(
                    path_id=path_id,
                    locale=locale,
                    title=path_tr.title,
                    description=path_tr.description,
                )
            )

        # Nothing references a module row, so the file's list simply replaces it
        await db.execute(delete(PathModule).where(PathModule.path_id == path_id))
        for position, module in enumerate(learning_path.modules):
            topic_id = await resolve_topic(path, f"path '{learning_path.slug}'", module.topic)
            db.add(
                PathModule(
                    path_id=path_id,
                    topic_id=topic_id,
                    position=position,
                    min_questions=module.quiz_questions,
                )
            )

    await db.flush()
    return LoadSummary(
        files=len(files),
        topics=len(all_topics),
        questions=len(all_questions),
        lessons=len(all_lessons),
        paths=len(all_paths),
    )


def _read_lesson_body(root: Path, toml_path: Path, name: str) -> str:
    """The Markdown of a lesson, read from beside its TOML file

    The file must stay inside the content directory: a `../` in a content file
    must not reach anything else on the disk
    """
    body_path = (toml_path.parent / name).resolve()
    if not body_path.is_relative_to(root.resolve()):
        raise ContentError(f"{toml_path.name}: lesson body '{name}' is outside the content directory")
    try:
        body = body_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContentError(f"{toml_path.name}: cannot read lesson body '{name}'") from exc
    if not body.strip():
        raise ContentError(f"{toml_path.name}: lesson body '{name}' is empty")
    return body


async def _replace_choices(
    db: AsyncSession, question_id: int, choices: list[ChoiceIn]
) -> None:
    """Makes the question's choices match the file, position by position

    Rows are updated in place rather than deleted and recreated: a finished
    match keeps pointing at the choice each player picked, so a reload must not
    change their ids. Positions the file no longer has are removed
    """
    existing = {
        choice.position: choice
        for choice in await db.scalars(select(Choice).where(Choice.question_id == question_id))
    }

    for position, choice_in in enumerate(choices):
        choice = existing.pop(position, None)
        if choice is None:
            choice = Choice(question_id=question_id, position=position)
            db.add(choice)
        choice.is_correct = choice_in.correct
        await db.flush()

        await db.execute(
            delete(ChoiceTranslation).where(ChoiceTranslation.choice_id == choice.id)
        )
        for locale in SUPPORTED:
            if locale in choice_in.text:
                db.add(
                    ChoiceTranslation(
                        choice_id=choice.id, locale=locale, text=choice_in.text[locale]
                    )
                )

    for choice in existing.values():
        await db.delete(choice)
    await db.flush()
