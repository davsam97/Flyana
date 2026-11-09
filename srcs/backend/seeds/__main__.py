"""Loads the versioned content files into the database

Run inside the api container: `python -m seeds`
entrypoint.sh runs it at startup when SEED_DEMO_DATA=true
One transaction for everything: a single bad entry and nothing is written
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from app.db import SessionLocal, engine
from seeds import ContentError, load_content

CONTENT_DIR = Path(__file__).resolve().parent / "content"


async def main() -> int:
    try:
        async with SessionLocal() as db:
            try:
                summary = await load_content(db, CONTENT_DIR)
            except ContentError as exc:
                await db.rollback()
                print(f"content not loaded: {exc}", file=sys.stderr)
                return 1
            await db.commit()
        print(
            f"content loaded: {summary.files} file(s), "
            f"{summary.topics} topic(s), {summary.questions} question(s)"
        )
        return 0
    finally:
        await engine.dispose()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
