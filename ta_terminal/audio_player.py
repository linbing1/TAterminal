from __future__ import annotations

import asyncio
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import edge_tts

_BAR_WIDTH = 24


@dataclass(eq=True)
class PlaybackResult:
    path: Path
    duration_seconds: float
    duration_label: str
    pid: int


def format_duration_label(seconds: float) -> str:
    total_seconds = int(seconds)
    minutes, remainder = divmod(total_seconds, 60)
    return f"{minutes:02d}:{remainder:02d}"


def read_duration_seconds(path: Path) -> float:
    result = subprocess.run(
        ["afinfo", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    text = f"{result.stdout}\n{result.stderr}"
    match = re.search(r"estimated duration:\s*([0-9.]+)", text)
    if match is None:
        raise ValueError(f"Could not read duration from afinfo output for {path}")
    return float(match.group(1))


async def synthesize(script: str, output_path: Path, voice: str) -> float:
    """Synthesize TTS audio and return duration in seconds."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(script, voice)
    await communicate.save(str(output_path))
    return read_duration_seconds(output_path)


def _render_progress(elapsed_wall: float, duration_seconds: float, rate: float) -> str:
    audio_pos = min(elapsed_wall * rate, duration_seconds)
    pct = audio_pos / duration_seconds if duration_seconds > 0 else 0
    filled = int(_BAR_WIDTH * pct)
    bar = "█" * filled + "░" * (_BAR_WIDTH - filled)
    pos = format_duration_label(audio_pos)
    total = format_duration_label(duration_seconds)
    return f"  [{bar}]  {pos} / {total}"


async def play_with_progress(path: Path, duration_seconds: float, rate: float = 1.25) -> int:
    """Start afplay at given rate, show live progress bar, block until done. Returns pid."""
    process = subprocess.Popen(
        ["afplay", "-r", str(rate), str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    start = time.monotonic()
    try:
        while process.poll() is None:
            elapsed = time.monotonic() - start
            sys.stderr.write(f"\r{_render_progress(elapsed, duration_seconds, rate)}")
            sys.stderr.flush()
            await asyncio.sleep(0.5)
    except (asyncio.CancelledError, KeyboardInterrupt):
        process.terminate()
        raise
    finally:
        elapsed = time.monotonic() - start
        sys.stderr.write(f"\r{_render_progress(elapsed, duration_seconds, rate)}\n")
        sys.stderr.flush()
    return process.pid


# Kept for tests that mock this directly.
async def synthesize_and_play(script: str, output_path: Path, voice: str) -> PlaybackResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(script, voice)
    await communicate.save(str(output_path))

    duration_seconds = read_duration_seconds(output_path)
    process = subprocess.Popen(
        ["afplay", str(output_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return PlaybackResult(
        path=output_path,
        duration_seconds=duration_seconds,
        duration_label=format_duration_label(duration_seconds),
        pid=process.pid,
    )
