from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


def _default_tanews_repo() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            capture_output=True, text=True, check=True,
            cwd=Path(__file__).parent,
        )
        # --git-common-dir returns the .git dir of the main worktree
        main_repo = Path(result.stdout.strip()).resolve().parent
        return main_repo.parent / "TAnews"
    except Exception:
        return Path(__file__).resolve().parents[2] / "TAnews"


@dataclass(frozen=True)
class AppConfig:
    page_url: str
    athletic_cookies: list[dict]
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    audio_voice: str
    audio_rate: float
    state_dir: Path
    tanews_repo: Path


def load_config() -> AppConfig:
    state_dir = Path(os.getenv("TA_STATE_DIR", "~/.ta-terminal")).expanduser()
    tanews_repo = Path(
        os.getenv("TANEWS_REPO", str(_default_tanews_repo()))
    ).expanduser()
    cookies = json.loads(os.getenv("ATHLETIC_COOKIES", "[]"))

    return AppConfig(
        page_url=os.getenv(
            "PAGE_URL",
            "https://www.nytimes.com/athletic/football/premier-league/",
        ),
        athletic_cookies=cookies,
        llm_base_url=os.getenv(
            "LLM_BASE_URL",
            "https://open.bigmodel.cn/api/coding/paas/v4",
        ),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_model=os.getenv("LLM_MODEL", "deepseek-chat"),
        audio_voice=os.getenv("AUDIO_VOICE", "zh-CN-YunjianNeural"),
        audio_rate=float(os.getenv("AUDIO_RATE", "1.25")),
        state_dir=state_dir,
        tanews_repo=tanews_repo,
    )
