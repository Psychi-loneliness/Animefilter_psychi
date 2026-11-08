"""Check the setup step by step — run this before and after starting the bot.

    python -m scripts.doctor
"""
from __future__ import annotations

import asyncio
import sys

from animebot.config import Config
from animebot.db import Database


def line(ok: bool, text: str, hint: str = "") -> None:
    print(f"{'✅' if ok else '❌'} {text}")
    if hint and not ok:
        print(f"   → {hint}")


async def main() -> int:
    config = Config.from_env()
    print("── 1. token ──────────────────────────────────────────────")
    has_token = bool(config.bot_token) and ":" in config.bot_token
    line(has_token, "BOT_TOKEN looks like a token" if has_token else "BOT_TOKEN missing/invalid",
         "copy .env.example to .env and paste the token from @BotFather")

    print("\n── 2. admins ─────────────────────────────────────────────")
    line(bool(config.admin_ids),
         f"ADMIN_IDS: {sorted(config.admin_ids) or 'empty'}",
         "add your numeric id (get it from @userinfobot): ADMIN_IDS=123456789")
    line(config.auto_menu, f"auto menu: {'on' if config.auto_menu else 'off'} "
                           f"(cooldown {config.auto_menu_cooldown}s)")

    print("\n── 3. database ───────────────────────────────────────────")
    db = await Database(config.db_path).connect()
    try:
        stats = await db.stats()
        line(True, f"database ready: {config.db_path}")
        line(stats["anime"] > 0, f"{stats['anime']} anime saved",
             "add one: /filter \"Title\"[🍀Hindi dub🍀](buttonurl:https://t.me/+xxxx)")
        line(stats["groups"] > 0, f"{stats['groups']} group link(s) saved",
             "inside the group run: /setgroup menu")
        filters = await db._fetchall("SELECT slug FROM filters ORDER BY name")
        line(bool(filters), f"genres: {', '.join(r['slug'] for r in filters) or 'none'}",
             "create one: /filter action Action & Adventure")
        post_chat = await db.get_setting("post_chat_id", "")
        line(bool(post_chat), f"DM posts go to chat {post_chat or '(not set)'}",
             "optional: run /posthere in the group")
    finally:
        await db.close()

    print("\n── 4. telegram ───────────────────────────────────────────")
    if not has_token:
        line(False, "skipped (no token)")
        return 1
    try:
        from telegram import Bot
        from telegram.error import InvalidToken

        async with Bot(config.bot_token) as bot:
            me = await bot.get_me()
            line(True, f"connected as @{me.username} ({me.first_name})")
            commands = await bot.get_my_commands()
            line(bool(commands), f"{len(commands)} commands published",
                 "BotFather → /setcommands, or see README")
    except InvalidToken:
        line(False, "telegram rejected the token",
             "re-copy it from @BotFather (no spaces or quotes)")
        return 1
    except Exception as exc:  # noqa: BLE001
        line(False, f"could not reach Telegram ({type(exc).__name__})",
             "check your internet / firewall, then rerun")
        return 1

    print("\nAll good — start the bot with:  python -m animebot")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
