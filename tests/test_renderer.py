from ta_terminal.renderer import render_news
from ta_terminal.state_store import CurrentArticle


def test_render_news_contains_sections_and_status_line():
    article = CurrentArticle(
        title="阿森纳重新找回节奏",
        title_original="Arsenal rediscover rhythm",
        link="https://example.com/a",
        comment_count=89,
        published_at="2026-04-24T00:00:00+00:00",
        summary="这是一段总结。",
        why_it_matters="这是一段价值判断。",
        analysis_payload={},
    )

    output = render_news(article)

    assert "[TA] next unread hot article" in output
    assert "Comments: 89" in output
    assert "Summary" in output
    assert "Why it matters" in output
    assert "Next: run `ta audio`" in output
    assert "marked as read" in output
