"""Language negotiation and translation fallback """

from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import aliased

from app.models.content import Question, QuestionTranslation

SUPPORTED: tuple[str, ...] = ("en", "fr")
DEFAULT = "en"


def parse_accept_language(header: str) -> list[str]:
    """Sorts the languages a browser asked for best first

    `fr-CA,fr;q=0.9,en;q=0.8` -> ['fr-ca', 'fr', 'en']

    A missing `q` counts as 1.0
    `q=0` explicitly means "not this language" and drops the tag
    Ties on q are broken by order of appearance
    which is why the index is part of the sort key
    """
    items: list[tuple[float, int, str]] = []
    for index, part in enumerate(header.split(",")):
        part = part.strip()
        if not part:
            continue
        tag, _, params = part.partition(";")
        tag = tag.strip().lower()
        if not tag:
            continue
        q = 1.0
        for param in params.split(";"):
            key, _, value = param.partition("=")
            if key.strip() == "q":
                try:
                    q = float(value)
                except ValueError:
                    q = 0.0
        if q > 0:
            items.append((-q, index, tag))
    return [tag for _, _, tag in sorted(items)]


def resolve_locale(
    query: str | None = None,
    user_locale: str | None = None,
    accept_language: str | None = None,
) -> str:
    """Picks a language in order

    `?locale=` then the account preference then `Accept-Language` then `en`
    """
    for candidate in (query, user_locale):
        if candidate and candidate.lower() in SUPPORTED:
            return candidate.lower()

    for tag in parse_accept_language(accept_language or ""):
        if tag in SUPPORTED:
            return tag
        primary = tag.split("-")[0]
        if primary in SUPPORTED:
            return primary

    return DEFAULT


def translated_questions(locale: str) -> Select:
    """Builds the question SELECT with the `en` fallback resolved in SQL

    One round trip whatever the list length. Returns a `Select` so callers
    add their own filters, sorting and pagination.
    """
    wanted = aliased(QuestionTranslation, name="t")
    fallback = aliased(QuestionTranslation, name="en")

    return (
        select(
            Question.id,
            func.coalesce(wanted.title, fallback.title).label("title"),
            func.coalesce(wanted.stem, fallback.stem).label("stem"),
            func.coalesce(wanted.explanation, fallback.explanation).label("explanation"),
            wanted.question_id.is_(None).label("is_fallback"),
        )
        .select_from(Question)
        .outerjoin(
            wanted,
            (wanted.question_id == Question.id) & (wanted.locale == locale),
        )
        .outerjoin(
            fallback,
            (fallback.question_id == Question.id) & (fallback.locale == DEFAULT),
        )
    )
