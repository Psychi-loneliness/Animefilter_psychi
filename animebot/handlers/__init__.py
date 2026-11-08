"""Command / callback registration."""
from __future__ import annotations

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from . import admin, menu


def register(app: Application) -> None:
    # --- commands ---------------------------------------------------------
    app.add_handler(CommandHandler("start", menu.start))
    app.add_handler(CommandHandler("menu", menu.menu_command))
    app.add_handler(CommandHandler("help", menu.help_command))
    app.add_handler(CommandHandler("link", menu.link_command))
    app.add_handler(CommandHandler("links", menu.link_command))
    app.add_handler(CommandHandler("cancel", menu.on_cancel))
    app.add_handler(CommandHandler(["latest", "popular", "genre", "search"], menu.shortcut))

    # --- admin commands ---------------------------------------------------
    app.add_handler(CommandHandler("save", admin.save_command))
    app.add_handler(CommandHandler("poster", admin.poster_command))
    app.add_handler(CommandHandler("add", admin.add_command))
    app.add_handler(CommandHandler("filter", admin.filter_command))
    app.add_handler(CommandHandler("filters", admin.filters_command))
    app.add_handler(CommandHandler("unfilter", admin.unfilter_command))
    app.add_handler(CommandHandler("setgroup", admin.setgroup_command))
    app.add_handler(CommandHandler("groups", admin.groups_command))
    app.add_handler(CommandHandler("ungroup", admin.ungroup_command))
    app.add_handler(CommandHandler("del", admin.del_command))
    app.add_handler(CommandHandler("quick", admin.quick_command))
    app.add_handler(CommandHandler("find", admin.find_command))
    app.add_handler(CommandHandler("stats", admin.stats_command))
    app.add_handler(CommandHandler("automenu", admin.automenu_command))
    app.add_handler(CommandHandler("cooldown", admin.cooldown_command))
    app.add_handler(CommandHandler("posthere", admin.posthere_command))
    app.add_handler(CommandHandler("broadcast", admin.broadcast_command))

    # --- inline keyboard callbacks ---------------------------------------
    app.add_handler(CallbackQueryHandler(menu.on_anime, pattern=r"^a:"))
    app.add_handler(CallbackQueryHandler(menu.on_list_page, pattern=r"^lp:"))
    app.add_handler(CallbackQueryHandler(menu.on_genre, pattern=r"^g:"))
    app.add_handler(CallbackQueryHandler(menu.on_genre_page, pattern=r"^gp:"))
    app.add_handler(CallbackQueryHandler(menu.on_subscribe, pattern=r"^sub:"))
    app.add_handler(CallbackQueryHandler(menu.noop, pattern=r"^noop$"))
    app.add_handler(CallbackQueryHandler(menu.on_menu_button, pattern=r"^m:"))

    # --- /save as the caption of a photo (CommandHandler ignores captions) --
    app.add_handler(
        MessageHandler(
            filters.CAPTION
            & (filters.PHOTO | filters.Document.IMAGE)
            & filters.CaptionRegex(r"^/save(@\w+)?"),
            admin.save_command,
        )
    )

    # --- free text (search + auto menu) ----------------------------------
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu.on_text))

    app.add_error_handler(on_error)


async def on_error(update: object, context) -> None:
    import logging

    logging.getLogger(__name__).exception(
        "Unhandled error while processing update", exc_info=context.error
    )
    if isinstance(update, Update) and update.effective_message is not None:
        try:
            await update.effective_message.reply_text(
                "😅 Something went wrong. Please try /menu again."
            )
        except Exception:
            pass
