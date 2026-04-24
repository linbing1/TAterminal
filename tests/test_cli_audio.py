import asyncio
from pathlib import Path

from ta_terminal.cli import run_audio
from ta_terminal.state_store import CurrentArticle


class FakeStore:
    def __init__(self, article):
        self.article = article

    def load_current_article(self):
        return self.article

    def audio_output_path(self, article):
        return Path("/tmp/test-audio.mp3")


def test_run_audio_requires_current_article(capsys):
    exit_code = asyncio.run(run_audio(object(), FakeStore(None)))
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "no current article, run `ta news` first" in output


def test_run_audio_builds_script_and_starts_playback(capsys, monkeypatch):
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

    async def fake_synthesize_and_play(script, output_path, voice):
        assert script == "script text"
        assert output_path == Path("/tmp/test-audio.mp3")
        assert voice == "voice-1"

        class Result:
            path = output_path
            duration_label = "02:05"

        return Result()

    monkeypatch.setattr(
        "ta_terminal.cli.build_audio_script_for_current",
        lambda item, config: "script text",
    )
    monkeypatch.setattr(
        "ta_terminal.cli.synthesize_and_play",
        fake_synthesize_and_play,
    )

    config = type("Config", (), {"audio_voice": "voice-1"})()
    exit_code = asyncio.run(run_audio(config, FakeStore(article)))
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "loading current article" in output
    assert "generating audio script" in output
    assert "playing audio" in output
    assert "path: /tmp/test-audio.mp3 | duration: 02:05 | playback started" in output
