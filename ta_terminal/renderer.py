from ta_terminal.state_store import CurrentArticle


def render_news(article: CurrentArticle) -> str:
    lines = [
        "[TA] next unread hot article",
        "",
        f"Title: {article.title}",
        f"Original: {article.title_original}",
        f"Comments: {article.comment_count}",
        f"Published: {article.published_at}",
        f"Link: {article.link}",
        "",
        "Summary",
        article.summary,
        "",
        "Why it matters",
        article.why_it_matters,
        "",
        "Next: run `ta audio`",
        "Status: marked as read | saved as current article",
    ]
    return "\n".join(lines)
