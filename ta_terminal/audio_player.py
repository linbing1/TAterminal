from __future__ import annotations

import subprocess
from pathlib import Path

import edge_tts


async def synthesize(script: str, output_path: Path, voice: str) -> None:
    """Synthesize TTS audio and save to output_path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(script, voice)
    await communicate.save(str(output_path))


def play_with_progress(path: Path, rate: float = 1.25) -> int:
    """Run mpv in the foreground. Blocks until done or Ctrl+C. Returns pid."""
    process = subprocess.Popen(["mpv", f"--speed={rate}", str(path)])
    pid = process.pid
    process.wait()
    return pid
