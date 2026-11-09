"""Verdict model and answer grading logic"""

from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Literal

from pydantic import BaseModel, ValidationError

from app.services.llm.client import LLMClient, LLMUnavailable, Usage
from app.services.llm.prompts import (
    EXPLAIN_CLOSING,
    EXPLAIN_MODES,
    EXPLAIN_SYSTEM,
    GRADE_CLOSING,
    GRADE_SYSTEM,
    VERDICT_SCHEMA,
    language_instruction,
    user_message,
)

Outcome = Literal["correct", "imprecise", "off_target"]


class Verdict(BaseModel):
    """Grading result after model output and code vetoes"""

    outcome: Outcome  # final, after the code's vetoes
    model_outcome: Outcome  # what the model chose, kept for grader_meta
    score: float  # 0..1, clamped
    addresses_grader: bool
    false_statement: bool

    @property
    def validated(self) -> bool:
        """Whether the answer is accepted"""
        return self.outcome != "off_target"


@dataclass(frozen=True)
class GradingInput:
    """Input to the grading pipeline"""

    stem: str
    key_points: list[str]
    answer: str
    locale: str


def decide(addresses_grader: bool, false_statement: bool, outcome: Outcome) -> Outcome:
    """Apply code vetoes to the model's outcome

    The model reports facts; the code decides. Text aimed at the grader or
    a false statement can never be accepted, whatever outcome the model picked.
    The benchmark showed models that flag an injection correctly and still call
    it "imprecise" (accepted).
    """
    if addresses_grader or false_statement:
        return "off_target"
    return outcome


class _RawVerdict(BaseModel):
    """Parse and validate the raw model output"""

    addresses_grader: bool
    false_statement: bool
    score: float
    outcome: Outcome

    model_config = {"extra": "ignore"}


class AnswerGrader:
    """Grade written answers against key points using the LLM"""

    def __init__(self, client: LLMClient) -> None:
        self._client = client

    @property
    def model(self) -> str:
        """The model name in use"""
        return self._client.model

    async def grade(self, item: GradingInput) -> tuple[Verdict, Usage]:
        """Get a structured verdict on the answer"""
        user_prompt = user_message(
            item.stem, item.key_points, item.answer, GRADE_CLOSING
        )

        parsed, usage = await self._client.complete_json(
            GRADE_SYSTEM, user_prompt, VERDICT_SCHEMA, max_tokens=300
        )

        try:
            raw = _RawVerdict(**parsed)
        except ValidationError as exc:
            raise LLMUnavailable("malformed verdict") from exc

        score = max(0.0, min(1.0, raw.score))
        final_outcome = decide(raw.addresses_grader, raw.false_statement, raw.outcome)

        verdict = Verdict(
            outcome=final_outcome,
            model_outcome=raw.outcome,
            score=score,
            addresses_grader=raw.addresses_grader,
            false_statement=raw.false_statement,
        )
        return verdict, usage

    async def explain(
        self, item: GradingInput, outcome: Outcome
    ) -> AsyncIterator[str | Usage]:
        """Stream an explanation for the outcome

        Only certain outcomes get explanations: "correct" answers show a stored
        reference, not generated text. Raises ValueError for unsupported outcomes.
        """
        if outcome not in EXPLAIN_MODES:
            raise ValueError(f"no explanation for outcome {outcome}")

        verdict_text, mode_text = EXPLAIN_MODES[outcome]
        system_prompt = EXPLAIN_SYSTEM.format(
            verdict=verdict_text,
            mode=mode_text,
            language=language_instruction(item.locale),
        )
        user_prompt = user_message(
            item.stem, item.key_points, item.answer, EXPLAIN_CLOSING
        )

        async for chunk in self._client.stream_text(
            system_prompt, user_prompt, max_tokens=500
        ):
            yield chunk
