import json

from ta_terminal.state_store import CurrentArticle, StateStore


def test_mark_read_and_reload_links(tmp_path):
    store = StateStore(tmp_path)

    store.mark_read("https://example.com/a")
    store.mark_read("https://example.com/a")
    store.mark_read("https://example.com/b")

    assert store.load_read_links() == {
        "https://example.com/a",
        "https://example.com/b",
    }
    raw = json.loads((tmp_path / "read_articles.json").read_text(encoding="utf-8"))
    assert raw == [
        "https://example.com/a",
        "https://example.com/b",
    ]


def test_save_and_load_current_article(tmp_path):
    store = StateStore(tmp_path)
    article = CurrentArticle(
        title="中文标题",
        title_original="Original title",
        link="https://example.com/a",
        comment_count=42,
        published_at="2026-04-24T00:00:00+00:00",
        summary="summary text",
        detail="why text",
        analysis_payload={
            "title_cn": "中文标题",
            "title_original": "Original title",
            "article_type": "新闻报道",
            "importance": 5,
            "overview": "summary text",
            "detail": "**Key:** detail text",
            "link": "https://example.com/a",
        },
    )

    store.save_current_article(article)

    assert store.load_current_article() == article


def test_audio_output_path_is_stable_and_under_audio_dir(tmp_path):
    store = StateStore(tmp_path)
    article = CurrentArticle(
        title="中文标题",
        title_original="Original title",
        link="https://example.com/a",
        comment_count=42,
        published_at="2026-04-24T00:00:00+00:00",
        summary="summary text",
        detail="why text",
        analysis_payload={},
    )

    first = store.audio_output_path(article)
    second = store.audio_output_path(article)

    assert first == second
    assert first.parent == tmp_path / "audio"
    assert first.name.endswith(".mp3")
