"""Request and response bodies of the course: path, modules, lessons, check quizzes"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import QuestionKind


class ModuleSummaryOut(BaseModel):
    """One module of the path, with the caller's progress in it"""

    slug: str
    name: str
    description: str | None
    position: int
    lessons_total: int
    lessons_read: int
    quiz_questions: int
    best_score: Decimal | None
    quizzes: int
    passed: bool
    rating: Decimal | None


class PathOut(BaseModel):
    slug: str
    title: str
    description: str | None
    pass_ratio: Decimal
    modules: list[ModuleSummaryOut]


class LessonSummaryOut(BaseModel):
    slug: str
    title: str
    position: int
    read: bool


class ModuleOut(ModuleSummaryOut):
    """A module's page: its lessons, and the check quiz left open if any"""

    lessons: list[LessonSummaryOut]
    open_run_id: int | None


class LessonOut(BaseModel):
    """One lesson, its Markdown body in the caller's language"""

    slug: str
    title: str
    body: str
    module_slug: str
    module_name: str
    position: int
    previous_slug: str | None
    next_slug: str | None
    read: bool


class LessonReadOut(BaseModel):
    """What reading a lesson unlocked"""

    achievements: list[str]


class ChoiceOut(BaseModel):
    id: int
    text: str


class QuizQuestionOut(BaseModel):
    """A question as the student sees it before answering: no answer key"""

    id: int
    kind: QuestionKind
    title: str | None
    stem: str | None
    unit: str | None
    difficulty_rating: Decimal
    choices: list[ChoiceOut]


class SourceOut(BaseModel):
    label: str
    url: str | None


class CorrectionOut(BaseModel):
    """Why the right answer is right, shown once the student has answered"""

    correct_choice_ids: list[int]
    expected_value: Decimal | None
    tolerance_rel: Decimal | None
    unit: str | None
    explanation: str | None
    source: SourceOut | None


class RunResultOut(BaseModel):
    correct: int
    total: int
    passed: bool
    pass_ratio: Decimal


class RunOut(BaseModel):
    """A check quiz where it stands: the question to answer, or its result"""

    id: int
    module_slug: str
    total: int
    answered: int
    correct: int
    question: QuizQuestionOut | None
    result: RunResultOut | None


class AnswerIn(BaseModel):
    """The answer to the current question: choices, or a number"""

    model_config = ConfigDict(extra="forbid")

    question_id: int = Field(gt=0)
    choice_ids: Annotated[list[Annotated[int, Field(gt=0)]], Field(min_length=1, max_length=16)] | None = None
    # Finite and bounded: no NaN, no infinity, no 10^1000 to grind through Decimal
    value: Decimal | None = Field(default=None, allow_inf_nan=False, ge=-1e30, le=1e30)

    @model_validator(mode="after")
    def _one_kind_of_answer(self) -> Self:
        if (self.choice_ids is None) == (self.value is None):
            raise ValueError("send either `choice_ids` or `value`")
        return self


class AnswerOut(BaseModel):
    correct: bool
    correction: CorrectionOut
    xp: int
    achievements: list[str]
    rating: Decimal
    answered: int
    total: int
    next_question: QuizQuestionOut | None
    result: RunResultOut | None
