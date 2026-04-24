from __future__ import annotations

import argparse
import asyncio

from ta_terminal.config import load_config
from ta_terminal.renderer import render_news
from ta_terminal.state_store import StateStore
from ta_terminal.tanews_adapter import fetch_current_article


async def run_news(config, store: StateStore) -> int:
    article = await fetch_current_article(config, store.load_read_links())
    if article is None:
        print("no unread hot article found")
        return 1

    print(render_news(article))
    store.mark_read(article.link)
    store.save_current_article(article)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ta")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("news")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config()
    store = StateStore(config.state_dir)

    return asyncio.run(run_news(config, store))
