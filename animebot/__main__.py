"""``python -m animebot`` — long polling entry point."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from telegram.ext import Application, ApplicationBuilder

from .config import Config
from .db import Database
from .boot import auto_restore_if_empty
from .handlers import register
from .health import start_if_needed


def build_application(config: Config, db: Database) -> Application:
    app = (
        ApplicationBuilder()
        .token(config.bot_token)
        .concurrent_updates(True)
        .build()
    )
    app.bot_data["config"] = config
    app.bot_data["db"] = db
    register(app)
    return app


async def _post_init(app: Application) -> None:
    config: Config = app.bot_data["config"]
    db: Database = app.bot_data["db"]
    await db.connect()
    # persisted overrides from the admin commands
    config.auto_menu = (await db.get_setting("auto_menu", "1")) == "1"
    cooldown = await db.get_setting("auto_menu_cooldown", "")
    if cooldown.isdigit():
        config.auto_menu_cooldown = int(cooldown)
    restored = await auto_restore_if_empty(app.bot, db, config.auto_restore_file_id)
    me = await app.bot.get_me()
    logging.getLogger(__name__).info(
        "Running as @%s • %s titles • auto menu %s",
        me.username,
        await db.count_anime(),
        "on" if config.auto_menu else "off",
    )
    if restored:
        logging.getLogger(__name__).info(
            "library was empty — restored from AUTO_RESTORE_FILE_ID"
        )


async def _post_stop(app: Application) -> None:
    db: Database | None = app.bot_data.get("db")
    if db is not None:
        await db.close()


def main() -> None:
    config = Config.from_env()
    # hosts mount an empty volume, so create the folder before opening SQLite
    Path(config.db_path).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s • %(message)s",
    )
    if not config.bot_token:
        raise SystemExit(
            "BOT_TOKEN is missing. Copy .env.example to .env and paste your token "
            "from @BotFather."
        )
    start_if_needed()  # only when the host gives us a PORT (Render/Koyeb/Fly)
    app = build_application(config, Database(config.db_path))
    app.post_init = _post_init
    app.post_stop = _post_stop
    app.run_polling(allowed_updates=["message", "callback_query", "my_chat_member"])


if __name__ == "__main__":
    main()
