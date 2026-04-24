import asyncio

from ta_terminal.cli import run_news
from ta_terminal.state_store import CurrentArticle


class FakeStore:
    def __init__(self):
        self.read_links = {"https://example.com/old"}
        self.marked = []
        self.saved = None

    def load_read_links(self):
        return set(self.read_links)

    def mark_read(self, link):
        self.marked.append(link)

    def save_current_article(self, article):
        self.saved = article


def test_run_news_prints_article_and_updates_state(capsys, monkeypatch):
    article = CurrentArticle(
        title="中文标题",
        title_original="Original title",
        link="https://example.com/new",
        comment_count=88,
        published_at="2026-04-24T00:00:00+00:00",
        summary="summary text",
        why_it_matters="why text",
        analysis_payload={},
    )
    store = FakeStore()

    async def fake_fetch_current_article(config, read_links, **kwargs):
        assert read_links == {"https://example.com/old"}
        return article

    monkeypatch.setattr("ta_terminal.cli.fetch_current_article", fake_fetch_current_article)
    monkeypatch.setattr("ta_terminal.cli.render_news", lambda item: f"rendered {item.link}")

    exit_code = asyncio.run(run_news(object(), store))
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "rendered https://example.com/new" in output
    assert store.marked == ["https://example.com/new"]
    assert store.saved == article


def test_run_news_returns_one_when_no_unread_article(capsys, monkeypatch):
    async def fake_fetch_current_article(config, read_links, **kwargs):
        return None

    monkeypatch.setattr("ta_terminal.cli.fetch_current_article", fake_fetch_current_article)

    exit_code = asyncio.run(run_news(object(), FakeStore()))
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "no unread hot article found" in output
