"""Checks every source link of the course: it must answer, and not be a "moved" page

NASA Glenn's old pages still answer 200 with a "This page has moved" notice,
so the status alone is not enough. Run: python -m seeds.check_links
"""

from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

CONTENT = Path(__file__).resolve().parent / "content"
URL = re.compile(r'url = "(https://[^"]+)"')
TITLE = re.compile(r"<title>([^<]*)", re.IGNORECASE)
MOVED = re.compile(r"has moved", re.IGNORECASE)


def check(url: str) -> str | None:
    """None when the link is fine, else what is wrong with it"""
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (link check)"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            page = response.read(200_000).decode("utf-8", "replace")
    except Exception as exc:  # any failure is a broken link to report
        return str(exc)
    title = TITLE.search(page)
    if title and MOVED.search(title.group(1)):
        return f"moved page: {title.group(1).strip()}"
    return None


def main() -> int:
    urls = sorted({url for file in CONTENT.rglob("*.toml") for url in URL.findall(file.read_text())})
    broken = 0
    for url in urls:
        problem = check(url)
        print(f"{'BROKEN' if problem else 'ok    '} {url}{f'  ({problem})' if problem else ''}")
        broken += problem is not None
    print(f"{len(urls)} links, {broken} broken")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
