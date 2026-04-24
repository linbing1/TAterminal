from __future__ import annotations

import re
from typing import Iterable, Protocol, TypeVar


class HasHotFields(Protocol):
    link: str
    comment_count: int


T = TypeVar("T", bound=HasHotFields)


def pick_next_unread(articles: Iterable[T], read_links: set[str]) -> T | None:
    unread = [article for article in articles if article.link not in read_links]
    unread.sort(key=lambda article: article.comment_count, reverse=True)
    return unread[0] if unread else None


def extract_why_it_matters(detail: str, importance: int) -> str:
    for raw_line in detail.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(">"):
            continue
        cleaned = re.sub(r"\*\*", "", line).strip()
        return f"Importance {importance}/5. {cleaned}"
    return f"Importance {importance}/5."
