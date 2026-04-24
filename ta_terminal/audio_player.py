from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import edge_tts


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
