from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ta_terminal.config import load_config
from ta_terminal.tanews_adapter import fetch_current_article


class FakeCollectedArticle:
    def __init__(self, title: str, link: str, comment_count: int):
        self.title = title
        self.link = link
        self.summary = "raw summary"
        self.comment_count = comment_count
        self.published = datetime(2026, 4, 24, tzinfo=timezone.utc)
        self.full_text = ""


@dataclass
class FakeAnalyzedArticle:
    title_cn: str = "中文标题"
    title_original: str = "Original title"
    article_type: str = "新闻报道"
    importance: int = 5
    overview: str = "中文总结"
    detail: str = "**战术转折：** detail text"
    link: str = "https://example.com/3"


def test_load_config_reads_local_state_and_tanews_repo(monkeypatch, tmp_path):
    monkeypatch.setenv("TA_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("TANEWS_REPO", str(tmp_path / "TAnews"))
    monkeypatch.setenv("ATHLETIC_COOKIES", "[]")
    monkeypatch.setenv("LLM_API_KEY", "secret")

    config = load_config()

    assert config.state_dir == tmp_path / "state"
    assert config.tanews_repo == tmp_path / "TAnews"
    assert config.llm_api_key == "secret"


def test_fetch_current_article_skips_read_links(monkeypatch, tmp_path):
    async def fake_collect_articles(page_url, cookies):
        return [
            FakeCollectedArticle("first", "https://example.com/1", 30),
            FakeCollectedArticle("second", "https://example.com/2", 80),
            FakeCollectedArticle("third", "https://example.com/3", 50),
        ]

    async def fake_scrape_full_texts(articles, cookies):
        articles[0].full_text = "full text"
        return articles, False

    class FakeLLMClient:
        def __init__(self, base_url, api_key, model):
            self.base_url = base_url
            self.api_key = api_key
            self.model = model

    monkeypatch.setattr(
        "ta_terminal.tanews_adapter.load_tanews_dependencies",
        lambda repo: {
            "collect_articles": fake_collect_articles,
            "scrape_full_texts": fake_scrape_full_texts,
            "analyze_articles": lambda articles, llm: [FakeAnalyzedArticle()],
            "LLMClient": FakeLLMClient,
            "build_audio_script": None,
            "AnalyzedArticle": None,
        },
    )

    monkeypatch.setenv("ATHLETIC_COOKIES", "[]")
    monkeypatch.setenv("LLM_API_KEY", "secret")
    monkeypatch.setenv("TA_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("TANEWS_REPO", str(tmp_path / "TAnews"))

    article = __import__("asyncio").run(
        fetch_current_article(load_config(), {"https://example.com/2"})
    )

    assert article is not None
    assert article.link == "https://example.com/3"
    assert article.title == "中文标题"
    assert article.title_original == "Original title"
    assert article.summary == "中文总结"
    assert article.why_it_matters == "Importance 5/5. 战术转折： detail text"
