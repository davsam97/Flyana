"""Editorial rules of the shipped course, beyond what the content schema checks

The schema says a file is well formed; these say the course is complete: each
module with questions has enough of them across the three levels, every
question explains its answer and cites where to check it, in both languages.
Parsed from the files, no database
"""

from __future__ import annotations

import tomllib
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import pytest

from seeds import ContentFile, LessonIn, PathIn, QuestionIn

CONTENT = Path(__file__).resolve().parent.parent / "seeds" / "content"

# The difficulty bands the interface labels easy, medium and hard
BANDS = {"easy": (0, 1100), "medium": (1100, 1300), "hard": (1300, 10_000)}
QUESTIONS_PER_MODULE = (12, 18)
MIN_PER_BAND = 3
MIN_LESSONS = 2
MAX_TOLERANCE = Decimal("0.1")


def _load() -> tuple[list[PathIn], list[QuestionIn], list[LessonIn]]:
    paths: list[PathIn] = []
    questions: list[QuestionIn] = []
    lessons: list[LessonIn] = []
    for file in sorted(CONTENT.rglob("*.toml")):
        content = ContentFile.model_validate(tomllib.loads(file.read_text(encoding="utf-8")))
        paths += content.paths
        questions += [q for q in content.questions if q.status == "published"]
        lessons += [lesson for lesson in content.lessons if lesson.status == "published"]
    return paths, questions, lessons


PATHS, QUESTIONS, LESSONS = _load()
BY_MODULE: dict[str, list[QuestionIn]] = defaultdict(list)
for _question in QUESTIONS:
    BY_MODULE[_question.topic].append(_question)
COURSE_MODULES = [module.topic for module in PATHS[0].modules] if PATHS else []
MODULES_WITH_QUESTIONS = [slug for slug in COURSE_MODULES if BY_MODULE[slug]]


def _band(question: QuestionIn) -> str:
    return next(
        name for name, (low, high) in BANDS.items() if low <= question.difficulty < high
    )


def test_every_question_belongs_to_a_course_module() -> None:
    assert {q.topic for q in QUESTIONS} <= set(COURSE_MODULES)


def test_the_course_holds_about_a_hundred_questions() -> None:
    assert 90 <= len(QUESTIONS) <= 110


def test_every_course_module_has_content() -> None:
    assert COURSE_MODULES, "the course path is missing"
    assert MODULES_WITH_QUESTIONS == COURSE_MODULES


@pytest.mark.parametrize("module", MODULES_WITH_QUESTIONS)
def test_a_module_has_enough_questions_at_every_level(module: str) -> None:
    questions = BY_MODULE[module]
    low, high = QUESTIONS_PER_MODULE
    assert low <= len(questions) <= high

    per_band = defaultdict(int)
    for question in questions:
        per_band[_band(question)] += 1
    assert all(per_band[band] >= MIN_PER_BAND for band in BANDS), dict(per_band)


@pytest.mark.parametrize("module", MODULES_WITH_QUESTIONS)
def test_a_module_has_its_course(module: str) -> None:
    assert sum(1 for lesson in LESSONS if lesson.topic == module) >= MIN_LESSONS


@pytest.mark.parametrize("module", MODULES_WITH_QUESTIONS)
def test_every_question_explains_and_cites(module: str) -> None:
    for question in BY_MODULE[module]:
        assert question.kind != "free_text", f"{question.slug}: the quiz grades by code only"
        assert question.source is not None, f"{question.slug}: no source"
        for locale, wording in question.translations.items():
            assert wording.explanation, f"{question.slug}: no {locale} explanation"


@pytest.mark.parametrize("module", MODULES_WITH_QUESTIONS)
def test_numeric_questions_are_answerable(module: str) -> None:
    for question in BY_MODULE[module]:
        if question.kind != "numeric":
            continue
        assert question.tolerance is not None and question.tolerance <= MAX_TOLERANCE, question.slug
        # A student needs the unit to type the right number
        assert question.unit is not None, f"{question.slug}: no unit"


@pytest.mark.parametrize("module", MODULES_WITH_QUESTIONS)
def test_choice_questions_offer_real_choices(module: str) -> None:
    for question in BY_MODULE[module]:
        if question.kind == "numeric":
            continue
        assert 3 <= len(question.choices) <= 6, question.slug
        right = sum(choice.correct for choice in question.choices)
        if question.kind == "single_choice":
            assert right == 1, question.slug
        else:
            # Several right answers, never all of them: ticking everything must fail
            assert 2 <= right < len(question.choices), question.slug
