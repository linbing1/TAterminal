from __future__ import annotations

import re
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Iterable, Protocol, TypeVar

from ta_terminal.config import AppConfig
from ta_terminal.state_store import CurrentArticle


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


def load_tanews_dependencies(repo: Path) -> dict[str, object]:
    repo_str = str(repo)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)

    from src.analyzer import analyze_articles
    from src.audio_scripter import build_audio_script
    from src.collector import collect_articles
    from src.llm import LLMClient
    from src.models import AnalyzedArticle
    from src.scraper import scrape_full_texts

    return {
        "collect_articles": collect_articles,
        "scrape_full_texts": scrape_full_texts,
        "analyze_articles": analyze_articles,
        "build_audio_script": build_audio_script,
        "LLMClient": LLMClient,
        "AnalyzedArticle": AnalyzedArticle,
    }


async def fetch_current_article(config: AppConfig, read_links: set[str]) -> CurrentArticle | None:
    deps = load_tanews_dependencies(config.tanews_repo)
    collect_articles = deps["collect_articles"]
    scrape_full_texts = deps["scrape_full_texts"]
    analyze_articles = deps["analyze_articles"]
    llm_type = deps["LLMClient"]

    articles = await collect_articles(config.page_url, config.athletic_cookies)
    selected = pick_next_unread(articles, read_links)
    if selected is None:
        return None

    scraped_articles, _ = await scrape_full_texts([selected], config.athletic_cookies)
    llm = llm_type(config.llm_base_url, config.llm_api_key, config.llm_model)
    analyzed = analyze_articles(scraped_articles, llm)
    if not analyzed:
        return None

    item = analyzed[0]
    return CurrentArticle(
        title=item.title_cn,
        title_original=item.title_original,
        link=item.link,
        comment_count=selected.comment_count,
        published_at=selected.published.isoformat(),
        summary=item.overview,
        why_it_matters=extract_why_it_matters(item.detail, item.importance),
        analysis_payload=asdict(item),
    )


def build_audio_script_for_current(article: CurrentArticle, config: AppConfig) -> str:
    deps = load_tanews_dependencies(config.tanews_repo)
    llm_type = deps["LLMClient"]
    analyzed_type = deps["AnalyzedArticle"]
    build_audio_script = deps["build_audio_script"]

    llm = llm_type(config.llm_base_url, config.llm_api_key, config.llm_model)
    analyzed_article = analyzed_type(**article.analysis_payload)
    return build_audio_script(
        [analyzed_article],
        llm,
        date.today(),
        title_prefix="英超热议文章",
    )
