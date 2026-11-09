"""Deterministic grading of choice and numeric answers"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.models.enums import QuestionKind
from app.services.grading import grade_choices, grade_numeric


class TestGradeChoices:
    @pytest.mark.parametrize(
        ("selected", "expected"),
        [([2], True), ([1], False), ([], False), ([2, 3], False), ([2, 2], False)],
    )
    def test_single_choice_wants_the_one_right_choice(
        self, selected: list[int], expected: bool
    ) -> None:
        assert grade_choices(QuestionKind.single_choice, [2], selected) is expected

    @pytest.mark.parametrize(
        ("selected", "expected"),
        [
            ([1, 3], True),
            ([3, 1], True),  # order does not matter
            ([1], False),  # one right choice missing
            ([1, 2, 3], False),  # a wrong one ticked
            ([1, 2, 3, 4], False),  # ticking everything never scores
            ([1, 1, 3], False),  # a repeated id is a malformed answer
            ([], False),
        ],
    )
    def test_multi_choice_wants_exactly_the_right_set(
        self, selected: list[int], expected: bool
    ) -> None:
        assert grade_choices(QuestionKind.multi_choice, [1, 3], selected) is expected

    def test_a_key_without_a_right_choice_never_scores(self) -> None:
        assert grade_choices(QuestionKind.multi_choice, [], []) is False

    @pytest.mark.parametrize("kind", [QuestionKind.numeric, QuestionKind.free_text])
    def test_other_kinds_are_refused(self, kind: QuestionKind) -> None:
        with pytest.raises(ValueError):
            grade_choices(kind, [1], [1])


class TestGradeNumeric:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("7.67", True),
            ("7.5166", True),  # 2 % below 7.67 is 7.5166: the bound is included
            ("7.8234", True),  # 2 % above is 7.8234
            ("7.5", False),
            ("7.9", False),
            ("-7.67", False),
        ],
    )
    def test_relative_tolerance(self, value: str, expected: bool) -> None:
        assert grade_numeric(Decimal("7.67"), Decimal("0.02"), Decimal(value)) is expected

    def test_tolerance_scales_with_large_values(self) -> None:
        # Earth's gravitational parameter, accepted within 1 %
        mu = Decimal("3.986e14")
        assert grade_numeric(mu, Decimal("0.01"), Decimal("4.0e14")) is True
        assert grade_numeric(mu, Decimal("0.01"), Decimal("4.1e14")) is False

    def test_a_zero_answer_uses_the_tolerance_as_absolute(self) -> None:
        assert grade_numeric(Decimal(0), Decimal("0.05"), Decimal("0.04")) is True
        assert grade_numeric(Decimal(0), Decimal("0.05"), Decimal("0.06")) is False

    @pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
    def test_non_finite_values_never_score(self, value: str) -> None:
        assert grade_numeric(Decimal("7.67"), Decimal("0.5"), Decimal(value)) is False
