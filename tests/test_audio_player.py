import asyncio
from pathlib import Path

from ta_terminal.audio_player import synthesize


def test_synthesize_saves_file(monkeypatch, tmp_path):
    class FakeCommunicate:
        def __init__(self, text, voice):
            pass

        async def save(self, output_path):
            Path(output_path).write_bytes(b"fake-mp3")

    monkeypatch.setattr("ta_terminal.audio_player.edge_tts.Communicate", FakeCommunicate)

    output = tmp_path / "sample.mp3"
    asyncio.run(synthesize("hello world", output, "voice-1"))

    assert output.exists()
    assert output.read_bytes() == b"fake-mp3"
