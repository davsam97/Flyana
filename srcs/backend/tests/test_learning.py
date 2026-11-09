"""The course: Elo ratings, the adaptive check quiz, progress and lessons"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Choice, Question
from app.models.learning import ModuleProgress, QuizRun, UserTopicRating
from app.models.user import User
from app.services.gamification import XP_CORRECT_QUIZ, XP_MODULE_PASSED
from app.services.learning import expected_score, passes, rate, target_difficulty
from seeds import load_content


class TestElo:
    def test_equal_ratings_give_even_odds(self) -> None:
        assert expected_score(Decimal(1200), Decimal(1200)) == pytest.approx(0.5)

    def test_400_points_give_ten_to_one(self) -> None:
        assert expected_score(Decimal(1600), Decimal(1200)) == pytest.approx(10 / 11)

    def test_a_right_answer_raises_the_student_and_lowers_the_question(self) -> None:
        user, question = rate(Decimal(1000), Decimal(1000), True, user_answers=0)
        # K = 48 while the student is new in the module, 8 for the question
        assert user == Decimal("1024.00")
        assert question == Decimal("996.00")

    def test_a_wrong_answer_does_the_opposite(self) -> None:
        user, question = rate(Decimal(1000), Decimal(1000), False, user_answers=0)
        assert user == Decimal("976.00")
        assert question == Decimal("1004.00")

    def test_a_settled_student_moves_less(self) -> None:
        user, _ = rate(Decimal(1000), Decimal(1000), True, user_answers=10)
        assert user == Decimal("1012.00")

    def test_an_expected_success_barely_moves_anything(self) -> None:
        user, question = rate(Decimal(1800), Decimal(1000), True, user_answers=20)
        assert Decimal(1800) < user < Decimal("1800.5")
        assert Decimal("999.8") < question < Decimal(1000)

    def test_question_ratings_stay_in_their_range(self) -> None:
        _, question = rate(Decimal(2400), Decimal(800), True, user_answers=0)
        assert question == Decimal(800)
        _, question = rate(Decimal(400), Decimal(2000), False, user_answers=0)
        assert question == Decimal(2000)

    def test_the_target_aims_at_seventy_percent_success(self) -> None:
        target = target_difficulty(Decimal(1000))
        assert expected_score(Decimal(1000), target) == pytest.approx(0.7, abs=1e-3)


@pytest.mark.parametrize(
    ("correct", "total", "expected"),
    [(8, 10, True), (7, 10, False), (10, 10, True), (6, 7, True), (5, 7, False), (0, 0, False)],
)
def test_a_module_passes_at_eighty_percent(correct: int, total: int, expected: bool) -> None:
    assert passes(correct, total) is expected


def _choice_question(slug: str, difficulty: int, kind: str = "single_choice") -> str:
    second_right = "correct = true\n" if kind == "multi_choice" else ""
    return f"""
[[questions]]
slug = "{slug}"
topic = "t-course"
kind = "{kind}"
difficulty = {difficulty}
source = {{ label = "Reference {slug}" }}
[questions.translations.en]
title = "{slug}"
stem = "Stem {slug}"
explanation = "Because {slug}"
[questions.translations.fr]
title = "{slug}"
stem = "Énoncé {slug}"
explanation = "Parce que {slug}"
[[questions.choices]]
correct = true
text = {{ en = "Right", fr = "Juste" }}
[[questions.choices]]
{second_right}text = {{ en = "Also", fr = "Aussi" }}
[[questions.choices]]
text = {{ en = "Wrong", fr = "Faux" }}
"""


COURSE = (
    """
[[topics]]
slug = "t-course"
[topics.translations.en]
name = "Course"
description = "A module"
[topics.translations.fr]
name = "Cours"
description = "Un module"

[[lessons]]
slug = "t-course-one"
topic = "t-course"
position = 0
title = { en = "One", fr = "Un" }
body = { en = "one.en.md", fr = "one.fr.md" }

[[lessons]]
slug = "t-course-two"
topic = "t-course"
position = 1
title = { en = "Two", fr = "Deux" }
body = { en = "two.en.md", fr = "two.fr.md" }

[[paths]]
slug = "t-course-path"
[paths.translations.en]
title = "Path"
[paths.translations.fr]
title = "Parcours"
[[paths.modules]]
topic = "t-course"
quiz_questions = 5

[[questions]]
slug = "t-course-numeric"
topic = "t-course"
kind = "numeric"
difficulty = 1800
answer = 7.67
tolerance = 0.02
unit = "km/s"
[questions.translations.en]
title = "Numeric"
stem = "Speed?"
[questions.translations.fr]
title = "Numérique"
stem = "Vitesse ?"
"""
    + _choice_question("t-course-800", 800)
    + _choice_question("t-course-1000", 1000)
    + _choice_question("t-course-1200", 1200)
    + _choice_question("t-course-1400", 1400)
    + _choice_question("t-course-1600", 1600, kind="multi_choice")
)


@pytest.fixture
async def course(db: AsyncSession, tmp_path: Path) -> None:
    (tmp_path / "course.toml").write_text(COURSE, encoding="utf-8")
    for name, text in {
        "one.en.md": "# One\n", "one.fr.md": "# Un\n",
        "two.en.md": "# Two\n", "two.fr.md": "# Deux\n",
    }.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
    await load_content(db, tmp_path)


@pytest.fixture
async def student(course: None, as_user: Callable[..., Awaitable[User]]) -> User:
    return await as_user()


async def _right_answer(db: AsyncSession, question: dict[str, Any]) -> dict[str, Any]:
    """The body of a right answer to a served question, read from the answer key"""
    row = await db.get(Question, question["id"])
    assert row is not None
    if question["kind"] == "numeric":
        return {"question_id": question["id"], "value": str(row.numeric_answer)}
    right = list(await db.scalars(
        select(Choice.id).where(Choice.question_id == row.id, Choice.is_correct.is_(True))
    ))
    return {"question_id": question["id"], "choice_ids": right}


async def _wrong_answer(db: AsyncSession, question: dict[str, Any]) -> dict[str, Any]:
    if question["kind"] == "numeric":
        return {"question_id": question["id"], "value": "1"}
    wrong = await db.scalar(
        select(Choice.id).where(Choice.question_id == question["id"], Choice.is_correct.is_(False))
    )
    return {"question_id": question["id"], "choice_ids": [wrong]}


class TestPathAndLessons:
    async def test_anonymous_is_refused(self, client: AsyncClient, course: None) -> None:
        r = await client.get("/api/v1/paths/t-course-path")
        assert r.status_code == 401

    async def test_the_path_lists_its_modules_with_progress(
        self, client: AsyncClient, student: User
    ) -> None:
        r = await client.get("/api/v1/paths/t-course-path", params={"locale": "fr"})

        assert r.status_code == 200
        body = r.json()
        assert body["title"] == "Parcours"
        assert Decimal(body["pass_ratio"]) == Decimal("0.8")
        [module] = body["modules"]
        assert module["slug"] == "t-course"
        assert module["name"] == "Cours"
        assert (module["lessons_total"], module["lessons_read"]) == (2, 0)
        assert module["quiz_questions"] == 5
        assert module["passed"] is False
        assert module["best_score"] is None

    async def test_an_unknown_path_is_404(self, client: AsyncClient, student: User) -> None:
        r = await client.get("/api/v1/paths/nope")
        assert r.status_code == 404

    async def test_a_lesson_comes_in_the_asked_language_with_its_neighbours(
        self, client: AsyncClient, student: User
    ) -> None:
        r = await client.get("/api/v1/lessons/t-course-one", params={"locale": "fr"})

        assert r.status_code == 200
        lesson = r.json()
        assert (lesson["title"], lesson["body"]) == ("Un", "# Un\n")
        assert lesson["module_name"] == "Cours"
        assert (lesson["previous_slug"], lesson["next_slug"]) == (None, "t-course-two")

        r = await client.get("/api/v1/lessons/t-course-two", params={"locale": "en"})
        assert r.json()["body"] == "# Two\n"
        assert (r.json()["previous_slug"], r.json()["next_slug"]) == ("t-course-one", None)

    async def test_reading_a_lesson_counts_once(
        self, client: AsyncClient, student: User
    ) -> None:
        unlocked = []
        for _ in range(2):
            r = await client.post("/api/v1/lessons/t-course-one/read")
            assert r.status_code == 200
            unlocked.append(r.json()["achievements"])
        # The first lesson read is the lift-off, granted once
        assert unlocked == [["liftoff"], []]

        module = (await client.get("/api/v1/modules/t-course")).json()
        assert module["lessons_read"] == 1
        assert [lesson["read"] for lesson in module["lessons"]] == [True, False]


class TestCheckQuiz:
    async def test_a_served_question_carries_no_answer_key(
        self, client: AsyncClient, student: User
    ) -> None:
        r = await client.post("/api/v1/modules/t-course/quiz")

        assert r.status_code == 201
        run = r.json()
        assert (run["total"], run["answered"], run["result"]) == (5, 0, None)
        question = run["question"]
        assert set(question) == {
            "id", "kind", "title", "stem", "unit", "difficulty_rating", "choices"
        }
        assert all(set(choice) == {"id", "text"} for choice in question["choices"])
        assert "Because" not in r.text and "Reference" not in r.text

        module = (await client.get("/api/v1/modules/t-course")).json()
        assert module["open_run_id"] == run["id"]

    async def test_the_first_question_matches_a_new_student(
        self, client: AsyncClient, student: User
    ) -> None:
        """At 1000 the target is about 853: the 800 question, whatever the jitter"""
        run = (await client.post("/api/v1/modules/t-course/quiz")).json()
        assert run["question"]["title"] == "t-course-800"

    async def test_a_strong_student_gets_a_hard_question(
        self, client: AsyncClient, db: AsyncSession, student: User
    ) -> None:
        """At 1700 the target is about 1553: the 1600 question"""
        await client.post("/api/v1/modules/t-course/quiz")
        await db.execute(
            update(UserTopicRating)
            .where(UserTopicRating.user_id == student.id)
            .values(rating=Decimal(1700))
        )

        run = (await client.post("/api/v1/modules/t-course/quiz")).json()

        assert run["question"]["title"] == "t-course-1600"
        assert run["question"]["kind"] == "multi_choice"

    async def test_a_question_answered_right_lately_comes_last(
        self, client: AsyncClient, db: AsyncSession, student: User
    ) -> None:
        run = (await client.post("/api/v1/modules/t-course/quiz")).json()
        first = run["question"]
        await client.post(
            f"/api/v1/quiz-runs/{run['id']}/answer", json=await _right_answer(db, first)
        )
        await db.execute(
            update(UserTopicRating)
            .where(UserTopicRating.user_id == student.id)
            .values(rating=Decimal(1000))
        )

        again = (await client.post("/api/v1/modules/t-course/quiz")).json()

        assert again["question"]["id"] != first["id"]

    async def test_a_perfect_run_passes_the_module_and_pays_once(
        self, client: AsyncClient, db: AsyncSession, student: User
    ) -> None:
        run = (await client.post("/api/v1/modules/t-course/quiz")).json()
        question = run["question"]
        seen = []
        xp = 0
        while question is not None:
            seen.append(question["id"])
            r = await client.post(
                f"/api/v1/quiz-runs/{run['id']}/answer", json=await _right_answer(db, question)
            )
            assert r.status_code == 200, r.text
            answer = r.json()
            assert answer["correct"] is True
            assert answer["correction"]["explanation"] is not None
            xp += answer["xp"]
            question = answer["next_question"]

        assert len(set(seen)) == 5
        assert answer["result"] == {"correct": 5, "total": 5, "passed": True, "pass_ratio": "0.8"}
        assert xp == 5 * XP_CORRECT_QUIZ + XP_MODULE_PASSED

        finished = await db.get(QuizRun, run["id"])
        assert finished is not None
        progress = await db.get(ModuleProgress, (student.id, finished.topic_id))
        assert progress is not None
        assert progress.best_score == Decimal("1.000")
        assert progress.passed_at is not None

        # A second run pays nothing for questions already solved, nor for the module
        rerun = (await client.post("/api/v1/modules/t-course/quiz")).json()
        question = rerun["question"]
        xp = 0
        while question is not None:
            answer = (await client.post(
                f"/api/v1/quiz-runs/{rerun['id']}/answer", json=await _wrong_answer(db, question)
            )).json()
            xp += answer["xp"]
            question = answer["next_question"]
        assert answer["result"]["passed"] is False
        assert xp == 0

        await db.refresh(progress)
        assert progress.best_score == Decimal("1.000")
        assert progress.quizzes == 2

    async def test_four_right_out_of_five_passes(
        self, client: AsyncClient, db: AsyncSession, student: User
    ) -> None:
        run = (await client.post("/api/v1/modules/t-course/quiz")).json()
        question = run["question"]
        index = 0
        while question is not None:
            body = await (_wrong_answer if index == 0 else _right_answer)(db, question)
            answer = (await client.post(f"/api/v1/quiz-runs/{run['id']}/answer", json=body)).json()
            question = answer["next_question"]
            index += 1

        assert answer["result"]["correct"] == 4
        assert answer["result"]["passed"] is True

    async def test_ratings_move_with_the_answers(
        self, client: AsyncClient, db: AsyncSession, student: User
    ) -> None:
        # At 1150 the target is about 1003: the 1000 question, clear of the 800 floor
        await client.post("/api/v1/modules/t-course/quiz")
        await db.execute(
            update(UserTopicRating)
            .where(UserTopicRating.user_id == student.id)
            .values(rating=Decimal(1150))
        )
        run = (await client.post("/api/v1/modules/t-course/quiz")).json()
        question = await db.get(Question, run["question"]["id"])
        assert question is not None and question.slug == "t-course-1000"
        before = question.difficulty_rating

        answer = (await client.post(
            f"/api/v1/quiz-runs/{run['id']}/answer", json=await _right_answer(db, run["question"])
        )).json()

        assert Decimal(answer["rating"]) > Decimal(1150)
        await db.refresh(question)
        assert question.difficulty_rating < before
        assert (question.times_asked, question.times_correct) == (1, 1)

    async def test_a_numeric_answer_is_graded_within_its_tolerance(
        self, client: AsyncClient, db: AsyncSession, student: User
    ) -> None:
        await client.post("/api/v1/modules/t-course/quiz")
        await db.execute(
            update(UserTopicRating)
            .where(UserTopicRating.user_id == student.id)
            .values(rating=Decimal(2000))
        )
        run = (await client.post("/api/v1/modules/t-course/quiz")).json()
        assert run["question"]["kind"] == "numeric"
        assert run["question"]["unit"] == "km/s"

        r = await client.post(
            f"/api/v1/quiz-runs/{run['id']}/answer",
            json={"question_id": run["question"]["id"], "value": 7.7},
        )

        answer = r.json()
        assert answer["correct"] is True
        assert Decimal(answer["correction"]["expected_value"]) == Decimal("7.67")
        assert answer["correction"]["unit"] == "km/s"

    async def test_only_the_current_question_can_be_answered(
        self, client: AsyncClient, db: AsyncSession, student: User
    ) -> None:
        run = (await client.post("/api/v1/modules/t-course/quiz")).json()
        other = await db.scalar(
            select(Question.id).where(Question.slug == "t-course-1400")
        )

        r = await client.post(
            f"/api/v1/quiz-runs/{run['id']}/answer",
            json={"question_id": other, "choice_ids": [1]},
        )

        assert r.status_code == 409

    async def test_choices_of_another_question_are_refused(
        self, client: AsyncClient, db: AsyncSession, student: User
    ) -> None:
        run = (await client.post("/api/v1/modules/t-course/quiz")).json()
        foreign = await db.scalar(
            select(Choice.id)
            .join(Question, Question.id == Choice.question_id)
            .where(Question.slug == "t-course-1400")
        )

        r = await client.post(
            f"/api/v1/quiz-runs/{run['id']}/answer",
            json={"question_id": run["question"]["id"], "choice_ids": [foreign]},
        )

        assert r.status_code == 422

    @pytest.mark.parametrize(
        "extra",
        [{}, {"choice_ids": [1], "value": 2}, {"value": "NaN"}, {"value": "1e40"}, {"choice_ids": []}],
    )
    async def test_malformed_answers_are_refused(
        self, client: AsyncClient, student: User, extra: dict[str, Any]
    ) -> None:
        run = (await client.post("/api/v1/modules/t-course/quiz")).json()

        r = await client.post(
            f"/api/v1/quiz-runs/{run['id']}/answer",
            json={"question_id": run["question"]["id"], **extra},
        )

        assert r.status_code == 422

    async def test_someone_elses_run_is_404(
        self,
        client: AsyncClient,
        db: AsyncSession,
        student: User,
        as_user: Callable[..., Awaitable[User]],
    ) -> None:
        run = (await client.post("/api/v1/modules/t-course/quiz")).json()
        await as_user(display_name="other", email="other@example.com")

        assert (await client.get(f"/api/v1/quiz-runs/{run['id']}")).status_code == 404
        r = await client.post(
            f"/api/v1/quiz-runs/{run['id']}/answer", json=await _right_answer(db, run["question"])
        )
        assert r.status_code == 404

    async def test_a_new_quiz_closes_the_unfinished_one(
        self, client: AsyncClient, db: AsyncSession, student: User
    ) -> None:
        first = (await client.post("/api/v1/modules/t-course/quiz")).json()
        await client.post("/api/v1/modules/t-course/quiz")

        r = await client.post(
            f"/api/v1/quiz-runs/{first['id']}/answer",
            json=await _right_answer(db, first["question"]),
        )
        assert r.status_code == 409

        state = (await client.get(f"/api/v1/quiz-runs/{first['id']}")).json()
        assert state["question"] is None
        assert state["result"]["passed"] is False

    async def test_a_run_resumes_where_it_stands(
        self, client: AsyncClient, db: AsyncSession, student: User
    ) -> None:
        run = (await client.post("/api/v1/modules/t-course/quiz")).json()
        answer = (await client.post(
            f"/api/v1/quiz-runs/{run['id']}/answer", json=await _right_answer(db, run["question"])
        )).json()

        state = (await client.get(f"/api/v1/quiz-runs/{run['id']}")).json()

        assert (state["answered"], state["correct"]) == (1, 1)
        assert state["question"]["id"] == answer["next_question"]["id"]
