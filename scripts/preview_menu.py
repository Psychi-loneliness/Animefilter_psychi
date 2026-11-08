"""Print the bot's real screens as text — no token, no network.

    python -m scripts.preview_menu
"""
from __future__ import annotations

import asyncio
import re

from animebot import ui
from animebot.config import Config
from animebot.db import Database

HTML_TAG = re.compile(r"<[^>]+>")


def plain(text: str) -> str:
    return HTML_TAG.sub("", text).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def render(text: str, markup) -> None:
    print("┌" + "─" * 58)
    for line in plain(text).splitlines():
        print("│ " + line)
    if markup is not None:
        print("│")
        for row in markup.inline_keyboard:
            print("│   " + "  ".join(f"[ {b.text} ]" for b in row))
    print("└" + "─" * 58)
    print()


async def main() -> None:
    db = await Database(":memory:").connect()
    await db.upsert_filter("action", "🔥 Action")
    await db.upsert_filter("romance", "💞 Romance")
    await db.upsert_filter("isekai", "🌀 Isekai")
    await db.add_anime("Demon Slayer: Hashira Training", "https://t.me/+demo", "hindi",
                       tags=["action"], popularity=98)
    await db.add_anime("Solo Leveling", "https://t.me/+demo2", "hindi",
                       tags=["action", "isekai"], popularity=94)
    await db.add_anime("Horimiya", "https://t.me/+demo3", "hindi",
                       tags=["romance"], popularity=84)
    await db.set_group("menu", "https://t.me/+YOUR_GROUP")
    cfg = Config(bot_token="offline", brand="Anime Galaxy", page_size=8)

    print("\n=== 1. someone says 'hi' in the group ===")
    render(ui.auto_menu_text(cfg.brand), ui.auto_menu())

    print("=== 2. they press the button → the 4 options ===")
    render(ui.main_menu_text(cfg.brand, await db.count_anime()), ui.main_menu(cfg.brand))

    print("=== 3. 🔥 Latest Uploaded ===")
    items = await db.anime_by_filter("latest")
    render(ui.pick_anime_text("🔥 Latest uploaded", len(items)),
           ui.anime_list(items, 0, 1, "latest"))

    print("=== 4. ⭐ Popular ===")
    items = await db.anime_by_filter("popular")
    render(ui.pick_anime_text("⭐ Popular right now", len(items)),
           ui.anime_list(items, 0, 1, "popular"))

    print("=== 5. 🎭 Genre ===")
    genres = [(r["slug"], r["name"]) for r in await db._fetchall("SELECT slug, name FROM filters")]
    render(ui.genre_menu_text(), ui.genre_page(genres, 0, 1))

    print("=== 6. 🔍 Search → Hindi / English ===")
    render(ui.search_lang_text(), ui.search_langs())

    print("=== 7. after pressing 🇮🇳 Hindi ===")
    render(ui.search_prompt_text("hindi"), None)

    print("=== 8. they type 'demon' ===")
    results = await db.search("demon", "hindi")
    render(ui.pick_anime_text("🔍 Results for “demon”", len(results)),
           ui.anime_list(results, 0, 1, "search", "hindi"))

    print("=== 9. they tap a title → posted in the GC with the link ===")
    anime = await db.get_anime(results[0]["id"])
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("🚀 Join & watch Demon Slayer", url="https://t.me/+YOUR_GROUP")
    ]])
    render(ui.anime_card(anime["title"], anime["language"], anime["filters"]), markup)
    await db.close()


if __name__ == "__main__":
    asyncio.run(main())
