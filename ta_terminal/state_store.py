from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(eq=True)
class CurrentArticle:
    title: str
    title_original: str
    link: str
    comment_count: int
    published_at: str
    summary: str
    detail: str
    analysis_payload: dict[str, Any]


class StateStore:
    def __init__(self, root: Path):
        self.root = Path(root).expanduser()
        self.root.mkdir(parents=True, exist_ok=True)
        self.audio_dir = self.root / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.current_article_path = self.root / "current_article.json"
        self.read_articles_path = self.root / "read_articles.json"
        self.playback_pid_path = self.root / "playback.pid"

    def load_read_links(self) -> set[str]:
        if not self.read_articles_path.exists():
            return set()
        raw = json.loads(self.read_articles_path.read_text(encoding="utf-8"))
        return set(raw)

    def mark_read(self, link: str) -> None:
        links = sorted(self.load_read_links() | {link})
        self.read_articles_path.write_text(
            json.dumps(links, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_current_article(self) -> CurrentArticle | None:
        if not self.current_article_path.exists():
            return None
        payload = json.loads(self.current_article_path.read_text(encoding="utf-8"))
        return CurrentArticle(**payload)

    def save_current_article(self, article: CurrentArticle) -> None:
        self.current_article_path.write_text(
            json.dumps(asdict(article), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def save_playback_pid(self, pid: int) -> None:
        self.playback_pid_path.write_text(str(pid), encoding="utf-8")

    def load_playback_pid(self) -> int | None:
        if not self.playback_pid_path.exists():
            return None
        try:
            return int(self.playback_pid_path.read_text(encoding="utf-8").strip())
        except ValueError:
            return None

    def clear_playback_pid(self) -> None:
        self.playback_pid_path.unlink(missing_ok=True)

    def audio_output_path(self, article: CurrentArticle) -> Path:
        digest = hashlib.sha1(article.link.encode("utf-8")).hexdigest()[:12]
        return self.audio_dir / f"{digest}.mp3"
