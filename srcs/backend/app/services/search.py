"""Question search, filters, facets and pagination, all in PostgreSQL"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, false, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.i18n import DEFAULT
from app.models.content import (
    Question, QuestionTag, QuestionTranslation, Tag, Topic
)
from app.models.enums import QuestionStatus, Role
from app.models.user import User
from app.schemas.question import QuestionOut
from app.schemas.search import QuestionFilters

# Trigram similarity above which a misspelling still counts as a match. This
# is pg_trgm's own default; lower it and unrelated words start matching.
TRIGRAM_THRESHOLD = 0.3

# Difficulty facet: the 800..2000 rating range cut into 6 buckets of 200.
FACET_RANGE = (800, 2000, 6)

# NEVER interpolate a user-supplied sort key into SQL. This dict is the
# boundary. Pydantic's `Literal` rejects unknown keys before they reach here,
# and every value below is a SQLAlchemy expression object, never a string, so
# there is no code path where user text becomes SQL.
SORTS: dict[str, Any] = {
    "newest": Question.created_at.desc(),
    "difficulty": Question.difficulty_rating.asc(),
    "popularity": Question.times_asked.desc(),
    "success_rate": (
        Question.times_correct / func.nullif(Question.times_asked, 0)
    ).desc().nullslast(),
}


async def search_questions(
    db: AsyncSession, f: QuestionFilters, user: User | None, locale: str
) -> dict[str, Any]:
    """Runs a filtered sorted paginated question search

    `locale` picks which translation is preferred
    English is always joined as the fallback so a question with no translation
    in the asked language stays findable instead of silently vanishing
    """
    wanted = aliased(QuestionTranslation, name="t")
    fallback = aliased(QuestionTranslation, name="en")

    stmt = (
        select(
            Question,
            func.coalesce(wanted.title, fallback.title).label("title"),
            func.coalesce(wanted.stem, fallback.stem).label("stem"),
            wanted.question_id.is_(None).label("is_fallback"),
        )
        .outerjoin(
            wanted,
            (wanted.question_id == Question.id) & (wanted.locale == locale),
        )
        .outerjoin(
            fallback,
            (fallback.question_id == Question.id) & (fallback.locale == DEFAULT),
        )
    )

    # `status` is open to moderators only. Without this gate anyone could pass
    # ?status=draft and read every author's unpublished work.
    is_moderator = user is not None and user.role >= Role.moderator

    if f.status is None:
        stmt = stmt.where(Question.status == QuestionStatus.published)
    elif is_moderator or f.status == QuestionStatus.published:
        stmt = stmt.where(Question.status == f.status)
    else:
        # A status the caller may not see: an empty page rather than published
        # questions passed off as drafts. `false()` keeps total and facets consistent
        stmt = stmt.where(false())

    if f.topic:
        stmt = stmt.where(
            Question.topic_id.in_(select(Topic.id).where(Topic.slug.in_(f.topic)))
        )
    if f.tags:
        stmt = stmt.where(
            Question.id.in_(
                select(QuestionTag.question_id)
                .join(Tag, Tag.id == QuestionTag.tag_id)
                .where(Tag.slug.in_(f.tags))
            )
        )

    if f.difficulty_min is not None:
        stmt = stmt.where(Question.difficulty_rating >= f.difficulty_min)
    if f.difficulty_max is not None:
        stmt = stmt.where(Question.difficulty_rating <= f.difficulty_max)

    rank = None
    if f.q:
        # websearch_to_tsquery accepts Google-style syntax (`foo OR bar -baz`)
        # and NEVER raises on malformed input. to_tsquery does raise — a bare
        # `&&` is enough to turn it into a 500 — so websearch_to_tsquery is
        # the only safe choice for text typed by a user.
        #
        # 'simple' must match the config used by the generated column, or
        # PostgreSQL cannot use the GIN index at all.
        tsq = func.websearch_to_tsquery("simple", f.q)
        stmt = stmt.where(
            or_(
                wanted.search_vector.op("@@")(tsq),
                fallback.search_vector.op("@@")(tsq),
                # Trigram fallback catches typos that full-text search misses,
                # because tsvector matching is exact per lexeme.
                func.similarity(
                    func.coalesce(wanted.stem, fallback.stem), f.q
                ) > TRIGRAM_THRESHOLD,
            )
        )
        rank = func.ts_rank(
            func.coalesce(wanted.search_vector, fallback.search_vector), tsq
        )

    # `f.answered` is accepted but not applied yet

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    # "relevance" has no entry in SORTS because it is not a fixed column: it
    # only exists when `q` was supplied. Without a query it degrades to
    # "newest" instead of erroring.
    if f.sort == "relevance" and rank is not None:
        order = rank.desc()
    else:
        order = SORTS["newest" if f.sort == "relevance" else f.sort]

    # `Question.id` breaks ties: without it, rows sharing a sort value come back
    # in any order, and a question can repeat or vanish from one page to the next
    rows = (await db.execute(
        stmt.order_by(order, Question.id)
        .limit(f.per_page)
        .offset((f.page - 1) * f.per_page)
    )).all()

    tags_by_question: dict[int, list[str]] = {question.id: [] for question, *_ in rows}
    if tags_by_question:
        tag_rows = await db.execute(
            select(QuestionTag.question_id, Tag.slug)
            .join(Tag, Tag.id == QuestionTag.tag_id)
            .where(QuestionTag.question_id.in_(tags_by_question))
            .order_by(Tag.slug)
        )
        for question_id, slug in tag_rows:
            tags_by_question[question_id].append(slug)

    # Built field by field, never from the row: `questions` also holds
    # `key_points`, the answer key, which must never reach a client
    items = [
        QuestionOut(
            id=question.id,
            slug=question.slug,
            title=title,
            topic_id=question.topic_id,
            kind=question.kind,
            status=question.status,
            difficulty_rating=question.difficulty_rating,
            stem=stem,
            is_fallback=is_fallback,
            tags=tags_by_question[question.id],
            times_asked=question.times_asked,
            times_correct=question.times_correct,
            created_at=question.created_at,
            updated_at=question.updated_at,
        )
        for question, title, stem, is_fallback in rows
    ]

    return {
        "items": items,
        "page": f.page,
        "per_page": f.per_page,
        "total": total,
        "total_pages": (total + f.per_page - 1) // f.per_page,
        "facets": await _facets(db, stmt),
    }


async def _facets(db: AsyncSession, stmt: Select) -> dict[str, dict[str, int]]:
    """Counts the filtered set by topic and by difficulty band"""
    sub = stmt.subquery()

    by_topic = await db.execute(
        select(sub.c.topic_id, func.count())
        .select_from(sub)
        .group_by(sub.c.topic_id)
    )
    by_difficulty = await db.execute(
        select(
            func.width_bucket(sub.c.difficulty_rating, *FACET_RANGE).label("bucket"),
            func.count(),
        )
        .select_from(sub)
        .group_by("bucket")
    )

    return {
        "topics": {str(topic_id): n for topic_id, n in by_topic},
        "difficulty": {str(bucket): n for bucket, n in by_difficulty},
    }
