from ta_terminal.state_store import CurrentArticle


def render_news(article: CurrentArticle) -> str:
    lines = [
        f"[TA] {article.title}",
        f"     {article.title_original}",
        f"     评论 {article.comment_count} | {article.published_at[:10]} | {article.link}",
        "",
        "摘要",
        article.summary,
        "",
        "详细内容",
        article.detail,
        "",
        "Next: run `ta audio`",
    ]
    return "\n".join(lines)
