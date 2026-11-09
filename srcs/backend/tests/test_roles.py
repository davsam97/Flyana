"""Role hierarchy lock"""

import itertools

import pytest

from app.models.enums import Role

ORDER = [Role.guest, Role.student, Role.author, Role.moderator, Role.admin]


def test_strictly_decreasing() -> None:
    for bas, haut in itertools.pairwise(ORDER):
        assert bas < haut
        assert haut > bas
        assert bas <= haut
        assert not (haut <= bas)


def wrong_alpha() -> None:
    assert str(Role.admin) < str(Role.student)
    assert Role.admin > Role.student


@pytest.mark.parametrize("role", ORDER)
def test_reflexive(role: Role) -> None:
    assert role <= role and role >= role and not (role < role)


def comparison() -> None:
    """`NotImplemented` python must delegate to the right"""
    assert Role.admin.__lt__("admin") is NotImplemented
