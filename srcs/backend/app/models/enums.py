"""Domain enums

VARCHAR + CHECK constraint
via `sa.Enum(..., native_enum=False, create_constraint=True)`, not native types ENUM PostgreSQL.
Same validation, but can add or delete a value in a migration,
while native ENUM impose `ALTER TYPE … ADD VALUE` makes impossible deleting without recreating type

`create_constraint=True` is not optional : it defaults to False since SQLAlchemy 1.4,
and without it `native_enum=False` degrades to a plain VARCHAR with no validation at all

Cost: alembic autogenerate does not detect CHECK constraint changes
Adding a value to an enum produces an empty migration ; the drop/recreate of the
constraint has to be written by hand
"""

from __future__ import annotations

from enum import StrEnum

from sqlalchemy import Enum as SAEnum


class Role(StrEnum):
    """What a user is allowed to do

    Cumulative so each role holds everything the one before it holds
    """

    guest = "guest"
    student = "student"
    author = "author"
    moderator = "moderator"
    admin = "admin"

    @property
    def rank(self) -> int:
        """Position of this role in the ladder"""
        return _ROLE_ORDER.index(self.value)

    # The four operators below exist so a check reads `user.role >= Role.moderator`
    # instead of spelling out every role that qualifies
    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Role):
            return NotImplemented
        return self.rank < other.rank

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Role):
            return NotImplemented
        return self.rank <= other.rank

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Role):
            return NotImplemented
        return self.rank > other.rank

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Role):
            return NotImplemented
        return self.rank >= other.rank


_ROLE_ORDER: list[str] = [
    Role.guest.value,
    Role.student.value,
    Role.author.value,
    Role.moderator.value,
    Role.admin.value,
]


class QuestionKind(StrEnum):
    """How a question is answered"""

    single_choice = "single_choice"
    multi_choice = "multi_choice"
    free_text = "free_text"
    # A number checked against `numeric_answer` within a relative tolerance
    numeric = "numeric"


class QuestionStatus(StrEnum):
    """Where a question sits in its lifecycle

    Content files may only use `draft`, `published` and `archived`
    `in_review` and `rejected` are left over from an in-app moderation workflow
    that no longer exists, kept because the database enum still holds them
    """

    draft = "draft"
    in_review = "in_review"
    published = "published"
    archived = "archived"
    rejected = "rejected"


class AttemptSource(StrEnum):
    """Which part of the app an answer came from"""

    practice = "practice"
    review = "review"
    duel = "duel"
    arena = "arena"
    daily = "daily"


class GraderKind(StrEnum):
    """What marked an answer

    `deterministic`: checked by code against stored choices, for multiple-choice questions.
    `llm`: graded by the language model.
    `self_assessed`: the model was disabled or unreachable, the student saw the reference
    explanation and marked the answer themselves.
    """

    deterministic = "deterministic"
    llm = "llm"
    self_assessed = "self_assessed"


class MatchMode(StrEnum):
    """How many players a match holds"""

    solo = "solo"
    duel = "duel"
    arena = "arena"


class MatchStatus(StrEnum):
    """Where a match sits in its lifecycle"""

    lobby = "lobby"
    running = "running"
    finished = "finished"
    aborted = "aborted"


class FriendshipStatus(StrEnum):
    """Where a friend request sits"""

    pending = "pending"
    accepted = "accepted"
    blocked = "blocked"


class OAuthProvider(StrEnum):
    """Third party login providers"""

    google = "google"
    fortytwo = "fortytwo"
    github = "github"


class PathLevel(StrEnum):
    """Difficulty band of a learning path"""

    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


def enum_column(enum_cls: type[StrEnum], name: str, length: int = 32) -> SAEnum:
    """Builds an enum column as VARCHAR + CHECK as promised at the top of this module

    `name` becomes the `%(constraint_name)s` token of the `ck` naming convention
    in `base.py` so the constraint lands as `ck_<table>_<name>`
    """
    return SAEnum(
        enum_cls,
        native_enum=False,
        create_constraint=True,
        length=length,
        name=name,
        validate_strings=True,
    )
