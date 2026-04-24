import asyncio
from pathlib import Path

from ta_terminal.cli import run_audio
from ta_terminal.state_store import CurrentArticle


class FakeStore:
    def __init__(self, article):
        self.article = article
        self.saved_pid = None

    def load_current_article(self):
        return self.article

    def audio_output_path(self, article):
        return Path("/tmp/test-audio.mp3")

    def save_playback_pid(self, pid):
        self.saved_pid = pid

    def clear_playback_pid(self):
        self.saved_pid = None


def test_run_audio_requires_current_article(capsys):
    exit_code = asyncio.run(run_audio(object(), FakeStore(None)))
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "no current article, run `ta news` first" in output


def test_run_audio_builds_script_synthesizes_and_plays(capsys, monkeypatch):
    article = CurrentArticle(
        title="中文标题",
        title_original="Original title",
        link="https://example.com/new",
        comment_count=88,
        published_at="2026-04-24T00:00:00+00:00",
        summary="summary text",
        detail="why text",
        analysis_payload={},
    )

    async def fake_synthesize(script, output_path, voice):
        assert script == "script text"
        assert output_path == Path("/tmp/test-audio.mp3")
        assert voice == "voice-1"
        return 125.4

    async def fake_play_with_progress(path, duration_seconds, rate):
        assert path == Path("/tmp/test-audio.mp3")
        assert duration_seconds == 125.4
        assert rate == 1.25
        return 9999

    monkeypatch.setattr("ta_terminal.cli.build_audio_script_for_current", lambda a, c: "script text")
    monkeypatch.setattr("ta_terminal.cli.synthesize", fake_synthesize)
    monkeypatch.setattr("ta_terminal.cli.play_with_progress", fake_play_with_progress)

    config = type("Config", (), {"audio_voice": "voice-1", "audio_rate": 1.25})()
    store = FakeStore(article)
    exit_code = asyncio.run(run_audio(config, store))

    assert exit_code == 0
    assert store.saved_pid is None  # cleared after normal finish
