"""Deterministic grading: choices and numbers, checked by code, never by a model

Pure functions over the answer key, so the rules read in one place and test
without a database. The caller loads the key and records the attempt
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from app.models.enums import QuestionKind


def grade_choices(
    kind: QuestionKind, correct_ids: Iterable[int], selected_ids: Iterable[int]
) -> bool:
    """Whether the ticked choices are exactly the right ones

    A single-choice answer is one choice, the right one. A multi-choice answer
    must tick every right choice and nothing else: no partial credit, or
    ticking everything would always score
    """
    correct = set(correct_ids)
    selected = list(selected_ids)
    if kind == QuestionKind.single_choice:
        return len(selected) == 1 and selected[0] in correct and len(correct) == 1
    if kind == QuestionKind.multi_choice:
        return len(selected) == len(set(selected)) and set(selected) == correct and bool(correct)
    raise ValueError(f"{kind} is not graded by choices")


def grade_numeric(expected: Decimal, tolerance_rel: Decimal, value: Decimal) -> bool:
    """Whether `value` lies within `tolerance_rel` of `expected`, relatively

    0.02 accepts ±2 % of the expected value, bounds included. An expected 0
    has no relative neighbourhood, so the tolerance is then taken as absolute
    """
    if not value.is_finite():
        return False
    margin = tolerance_rel * abs(expected) if expected != 0 else tolerance_rel
    return abs(value - expected) <= margin
