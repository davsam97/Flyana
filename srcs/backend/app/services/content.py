"""Topic hierarchy queries"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.i18n import DEFAULT

# `topics.parent_id` has no cycle constraint: without this cap a cycle would
# make the recursive CTE below loop forever
MAX_TOPIC_DEPTH = 10


async def topic_tree(db: AsyncSession, locale: str) -> list[dict[str, Any]]:
    """Returns the whole topic hierarchy translated in one query

    Archived topics are left out, and with them everything below them

    The description comes from the same translation as the name, so a name in
    the asked language is never paired with an English description
    """
    sql = text(
        """
        WITH RECURSIVE tree AS (
            SELECT id, parent_id, slug, position, 1 AS depth
            FROM topics WHERE parent_id IS NULL AND NOT archived
          UNION ALL
            SELECT t.id, t.parent_id, t.slug, t.position, tree.depth + 1
            FROM topics t
            JOIN tree ON t.parent_id = tree.id AND tree.depth < :max_depth
            WHERE NOT t.archived
        )
        SELECT tree.*,
               COALESCE(tr.name, en.name) AS name,
               CASE WHEN tr.topic_id IS NOT NULL THEN tr.description
                    ELSE en.description END AS description
        FROM tree
        LEFT JOIN topic_translations tr ON tr.topic_id = tree.id AND tr.locale = :locale
        LEFT JOIN topic_translations en ON en.topic_id = tree.id AND en.locale = :default
        ORDER BY depth, position
        """
    )
    rows = await db.execute(
        sql,
        {"locale": locale, "default": DEFAULT, "max_depth": MAX_TOPIC_DEPTH},
    )
    return [dict(row) for row in rows.mappings()]
