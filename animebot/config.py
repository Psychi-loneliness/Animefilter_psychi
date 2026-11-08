"""Environment driven configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent


def _int_set(raw: str) -> frozenset[int]:
    out: set[int] = set()
    for chunk in raw.replace(";", ",").split(","):
        chunk = chunk.strip()
        if chunk.lstrip("-").isdigit():
            out.add(int(chunk))
    return frozenset(out)


def _bool(raw: str, default: bool) -> bool:
    if not raw:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "y"}


@dataclass(slots=True)
class Config:
    bot_token: str
    db_path: str = "animebot.db"
    admin_ids: frozenset[int] = field(default_factory=frozenset)
    brand: str = "Anime Galaxy"
    auto_menu: bool = True
    auto_menu_cooldown: int = 180
    search_timeout: int = 180
    page_size: int = 8
    log_level: str = "INFO"
    auto_restore_file_id: str = ""

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            bot_token=os.getenv("BOT_TOKEN", "").strip(),
            db_path=os.getenv("DB_PATH", str(ROOT / "animebot.db")),
            admin_ids=_int_set(os.getenv("ADMIN_IDS", "")),
            brand=os.getenv("BRAND", "Anime Galaxy").strip() or "Anime Galaxy",
            auto_menu=_bool(os.getenv("AUTO_MENU", ""), True),
            auto_menu_cooldown=int(os.getenv("AUTO_MENU_COOLDOWN", "180") or 180),
            search_timeout=int(os.getenv("SEARCH_TIMEOUT", "180") or 180),
            page_size=int(os.getenv("PAGE_SIZE", "8") or 8),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            auto_restore_file_id=os.getenv("AUTO_RESTORE_FILE_ID", "").strip(),
        )
