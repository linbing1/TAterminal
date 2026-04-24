from __future__ import annotations

import asyncio
import sys
import time

_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
_CLEAR_LINE = "\033[1A\033[2K"


class Step:
    def __init__(self, label: str, on_complete: object = None) -> None:
        self.label = label
        self._on_complete = on_complete
        self._task: asyncio.Task | None = None
        self._start: float = 0.0

    async def _spin(self) -> None:
        i = 0
        while True:
            elapsed = int(time.monotonic() - self._start)
            frame = _FRAMES[i % len(_FRAMES)]
            sys.stdout.write(f"\r  {frame} {self.label}... {elapsed}s")
            sys.stdout.flush()
            await asyncio.sleep(0.1)
            i += 1

    async def __aenter__(self) -> "Step":
        self._start = time.monotonic()
        self._task = asyncio.create_task(self._spin())
        return self

    async def __aexit__(self, exc_type, *_) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        elapsed = time.monotonic() - self._start
        mark = "✓" if exc_type is None else "✗"
        sys.stdout.write(f"\r  {mark} {self.label} ({elapsed:.1f}s)\n")
        sys.stdout.flush()
        if exc_type is None and self._on_complete:
            self._on_complete()


class Progress:
    def __init__(self) -> None:
        self._completed = 0

    def step(self, label: str) -> Step:
        return Step(label, on_complete=self._increment)

    def _increment(self) -> None:
        self._completed += 1

    def clear(self) -> None:
        for _ in range(self._completed):
            sys.stdout.write(_CLEAR_LINE)
        sys.stdout.flush()
        self._completed = 0


class _NoopStep:
    async def __aenter__(self) -> "_NoopStep":
        return self

    async def __aexit__(self, *_) -> None:
        pass


class NoopProgress:
    def step(self, label: str) -> _NoopStep:
        return _NoopStep()

    def clear(self) -> None:
        pass
