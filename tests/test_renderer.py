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
        detail="这是一段详细内容。",
        analysis_payload={},
    )

    output = render_news(article)

    assert "[TA]" in output
    assert "评论 89" in output
    assert "摘要" in output
    assert "详细内容" in output
    assert "Next: run `ta audio`" in output
