import asyncio
from pathlib import Path

from ta_terminal.audio_player import PlaybackResult, format_duration_label, synthesize_and_play


def test_format_duration_label_rounds_to_minutes_and_seconds():
    assert format_duration_label(125.4) == "02:05"


def test_synthesize_and_play_uses_edge_tts_and_afplay(monkeypatch, tmp_path):
    calls = {}

    class FakeCommunicate:
        def __init__(self, text, voice):
            calls["text"] = text
            calls["voice"] = voice

        async def save(self, output_path):
            Path(output_path).write_bytes(b"fake-mp3")

    monkeypatch.setattr("ta_terminal.audio_player.edge_tts.Communicate", FakeCommunicate)
    monkeypatch.setattr(
        "ta_terminal.audio_player.read_duration_seconds",
        lambda path: 125.4,
    )

    class FakeProcess:
        pid = 4321

    monkeypatch.setattr(
        "ta_terminal.audio_player.subprocess.Popen",
        lambda cmd, stdout, stderr: FakeProcess(),
    )

    result = asyncio.run(
        synthesize_and_play("hello world", tmp_path / "sample.mp3", "voice-1")
    )

    assert calls == {"text": "hello world", "voice": "voice-1"}
    assert result == PlaybackResult(
        path=tmp_path / "sample.mp3",
        duration_seconds=125.4,
        duration_label="02:05",
        pid=4321,
    )
