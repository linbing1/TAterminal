from __future__ import annotations

import argparse
import asyncio
import os
import signal
import sys

from ta_terminal.audio_player import play_with_progress, synthesize, synthesize_and_play
from ta_terminal.config import load_config
from ta_terminal.progress import Progress
from ta_terminal.renderer import render_news
from ta_terminal.state_store import StateStore
from ta_terminal.tanews_adapter import build_audio_script_for_current, fetch_current_article


async def run_news(config, store: StateStore) -> int:
    progress = Progress()
    article = await fetch_current_article(config, store.load_read_links(), progress=progress)
    progress.clear()
    if article is None:
        print("no unread hot article found")
        return 1

    print(render_news(article))
    store.mark_read(article.link)
    store.save_current_article(article)
    return 0


async def run_audio(config, store: StateStore) -> int:
    article = store.load_current_article()
    if article is None:
        print("no current article, run `ta news` first")
        return 1

    output_path = store.audio_output_path(article)
    progress = Progress()
    async with progress.step("生成音频脚本（LLM）"):
        script = await asyncio.to_thread(build_audio_script_for_current, article, config)
    async with progress.step("合成音频"):
        duration_seconds = await synthesize(script, output_path, config.audio_voice)

    try:
        pid = await play_with_progress(output_path, duration_seconds, config.audio_rate)
        store.save_playback_pid(pid)
        store.clear_playback_pid()
    except KeyboardInterrupt:
        store.clear_playback_pid()
        sys.stderr.write("\n")
        return 1
    return 0


def run_stop(store: StateStore) -> int:
    pid = store.load_playback_pid()
    if pid is None:
        print("no active playback")
        return 1
    try:
        os.kill(pid, signal.SIGTERM)
        store.clear_playback_pid()
        print(f"stopped (pid {pid})")
        return 0
    except ProcessLookupError:
        store.clear_playback_pid()
        print("playback already finished")
        return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ta")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("news")
    subparsers.add_parser("audio")
    subparsers.add_parser("stop")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config()
    store = StateStore(config.state_dir)

    if args.command == "news":
        return asyncio.run(run_news(config, store))
    if args.command == "audio":
        return asyncio.run(run_audio(config, store))
    if args.command == "stop":
        return run_stop(store)
    raise ValueError(f"Unsupported command: {args.command}")
