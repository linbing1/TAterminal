from dataclasses import dataclass

from ta_terminal.tanews_adapter import extract_why_it_matters, pick_next_unread


@dataclass
class FakeArticle:
    title: str
    link: str
    comment_count: int


def test_pick_next_unread_returns_highest_comment_unread():
    articles = [
        FakeArticle("first", "https://example.com/1", 30),
        FakeArticle("second", "https://example.com/2", 80),
        FakeArticle("third", "https://example.com/3", 50),
    ]

    selected = pick_next_unread(articles, {"https://example.com/2"})

    assert selected.link == "https://example.com/3"


def test_extract_why_it_matters_cleans_markdown_prefixes():
    detail = """
    **战术转折：** Arsenal 压回中场。

    > Mikel Arteta said the shape changed everything.
    """.strip()

    assert extract_why_it_matters(detail, 4) == "Importance 4/5. 战术转折： Arsenal 压回中场。"
