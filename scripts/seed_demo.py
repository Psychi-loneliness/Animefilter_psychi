"""Seed the database with demo anime, genres and a placeholder group link.

    python -m scripts.seed_demo            # add demo rows
    python -m scripts.seed_demo --reset    # wipe the anime/filter tables first
"""
from __future__ import annotations

import argparse
import asyncio

from animebot.config import Config
from animebot.db import Database

GENRES = {
    "action": "🔥 Action",
    "adventure": "🗺 Adventure",
    "comedy": "😂 Comedy",
    "romance": "💞 Romance",
    "isekai": "🌀 Isekai",
    "fantasy": "🧙 Fantasy",
    "thriller": "🔪 Thriller",
    "sports": "🏀 Sports",
    "slice-of-life": "🌸 Slice of Life",
    "shonen": "💥 Shonen",
}

DEMO = [
    # title, language, tags, popularity
    ("Demon Slayer: Hashira Training", "hindi", ["action", "fantasy", "shonen"], 98),
    ("Jujutsu Kaisen Season 2", "hindi", ["action", "shonen", "thriller"], 96),
    ("One Piece", "hindi", ["action", "adventure", "shonen"], 99),
    ("Solo Leveling", "hindi", ["action", "fantasy", "isekai"], 94),
    ("Attack on Titan: Final Season", "hindi", ["action", "thriller"], 97),
    ("Spy x Family", "hindi", ["comedy", "action", "slice-of-life"], 90),
    ("Horimiya", "hindi", ["romance", "slice-of-life", "comedy"], 84),
    ("Haikyu!! Movie: The Dumpster Battle", "hindi", ["sports", "comedy"], 88),
    ("Naruto Shippuden", "hindi", ["action", "adventure", "shonen"], 95),
    ("Fullmetal Alchemist: Brotherhood", "hindi", ["action", "adventure", "fantasy"], 93),
    ("Demon Slayer: Hashira Training", "english", ["action", "fantasy", "shonen"], 98),
    ("Jujutsu Kaisen Season 2", "english", ["action", "shonen", "thriller"], 96),
    ("Frieren: Beyond Journey's End", "english", ["fantasy", "adventure", "slice-of-life"], 92),
    ("Oshi no Ko", "english", ["thriller", "slice-of-life"], 87),
    ("Blue Lock", "english", ["sports", "shonen"], 89),
    ("Re:Zero Season 3", "english", ["isekai", "fantasy", "thriller"], 86),
]


async def seed(reset: bool) -> None:
    config = Config.from_env()
    db = await Database(config.db_path).connect()
    try:
        if reset:
            for table in ("anime_filter", "anime", "filters"):
                await db._exec(f"DELETE FROM {table}")
        for slug, name in GENRES.items():
            await db.upsert_filter(slug, name)
        for title, language, tags, popularity in DEMO:
            await db.add_anime(
                title=title,
                link=f"https://t.me/+demo-{abs(hash(title + language)) % 10**8}",
                language=language,
                tags=tags,
                popularity=popularity,
            )
        if await db.get_group("menu") is None:
            await db.set_group("menu", "https://t.me/+REPLACE_WITH_YOUR_GROUP_LINK", "Main group")
        stats = await db.stats()
        print(f"Seeded ✅ anime={stats['anime']} groups={stats['groups']}")
        print("Now run: /setgroup menu <your real group link> inside Telegram.")
    finally:
        await db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    asyncio.run(seed(parser.parse_args().reset))
