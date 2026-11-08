"""Menu, filter browsing, search and the join flow."""
from __future__ import annotations

import logging
import time
from typing import Any

from telegram import Chat, InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from .. import ui
from ..db import Database

log = logging.getLogger(__name__)

PAGE_SIZE_DEFAULT = 8

# user_id -> {"language": "hindi", "expires": ts, "chat_id": int}
SEARCH_STATE: dict[int, dict[str, Any]] = {}

# chat_id -> last time we showed the "tap the menu" nudge
AUTO_MENU_SEEN: dict[int, float] = {}


def _db(context: ContextTypes.DEFAULT_TYPE) -> Database:
    return context.application.bot_data["db"]


def _cfg(context: ContextTypes.DEFAULT_TYPE):
    return context.application.bot_data["config"]


def is_group(chat: Chat) -> bool:
    return chat.type in (Chat.GROUP, Chat.SUPERGROUP)


# ------------------------------------------------------------------- entry
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_menu(update, context)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_menu(update, context)


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db, cfg = _db(context), _cfg(context)
    text = ui.main_menu_text(cfg.brand, await db.count_anime())
    markup = ui.main_menu(cfg.brand)
    message = update.effective_message
    if message is None:
        return
    if update.callback_query is not None:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(
                text, reply_markup=markup, parse_mode=ParseMode.HTML
            )
            return
        except Exception:  # message content unchanged -> just send a fresh one
            log.debug("edit failed, sending new menu", exc_info=True)
    await message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


# --------------------------------------------------------------- navigation
async def on_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles every ``m:*`` callback from the inline menu."""
    query = update.callback_query
    if query is None or query.data is None:
        return
    db, cfg = _db(context), _cfg(context)
    parts = query.data.split(":")
    action = parts[1] if len(parts) > 1 else "home"

    if action == "close":
        await query.answer("Menu closed.")
        try:
            await query.message.delete()
        except Exception:
            await query.edit_message_text("Menu closed. Use /menu anytime.")
        return

    if action == "home":
        await query.answer()
        await query.edit_message_text(
            ui.main_menu_text(cfg.brand, await db.count_anime()),
            reply_markup=ui.main_menu(cfg.brand),
            parse_mode=ParseMode.HTML,
        )
        return

    if action == "genres":
        await show_genres(update, context, page=0)
        return

    if action == "latest":
        await query.answer("Loading latest uploaded…")
        await show_filter(update, context, "latest", 0)
        return

    if action == "popular":
        await query.answer("Loading popular…")
        await show_filter(update, context, "popular", 0)
        return

    if action == "search" and len(parts) == 2:
        await query.answer()
        await query.edit_message_text(
            ui.search_lang_text(),
            reply_markup=ui.search_langs(),
            parse_mode=ParseMode.HTML,
        )
        return

    if action == "search" and len(parts) > 2:
        lang_code = parts[2] if len(parts) > 2 else "hi"
        language = {"hi": "hindi", "en": "english"}.get(lang_code, "hindi")
        SEARCH_STATE[query.from_user.id] = {
            "language": language,
            "expires": time.time() + cfg.search_timeout,
            "chat_id": query.message.chat_id if query.message else None,
        }
        await query.answer(f"Search in {language} 🎯")
        await query.edit_message_text(
            ui.search_prompt_text(language),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Back", callback_data=f"{ui.CALLBACK_MENU}:search")]]
            ),
            parse_mode=ParseMode.HTML,
        )
        return

    await query.answer()


async def show_genres(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int) -> None:
    query = update.callback_query
    db = _db(context)
    genres = [
        (row["slug"], row["name"])
        for row in await db._fetchall("SELECT slug, name FROM filters ORDER BY name")
    ]
    if not genres:
        if query:
            await query.answer()
            await query.edit_message_text(
                "No genres added yet. An admin can add one with "
                "<code>/filter action Action &amp; Adventure</code>",
                parse_mode=ParseMode.HTML,
            )
        return
    page_size = 10
    pages = max(1, (len(genres) + page_size - 1) // page_size)
    page = max(0, min(page, pages - 1))
    chunk = genres[page * page_size : (page + 1) * page_size]
    if query:
        await query.answer()
        await query.edit_message_text(
            ui.genre_menu_text(),
            reply_markup=ui.genre_page(chunk, page, pages),
            parse_mode=ParseMode.HTML,
        )


async def on_genre_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return
    await show_genres(update, context, int(query.data.split(":")[1]))


async def on_genre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return
    _, slug, page_raw = query.data.split(":")
    await query.answer()
    await show_filter(update, context, slug, int(page_raw))


async def on_list_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """``lp:<slug>:<language>:<page>`` — paginate a result list."""
    query = update.callback_query
    if query is None or query.data is None:
        return
    _, slug, language, page_raw = query.data.split(":")
    await query.answer()
    await show_filter(update, context, slug, int(page_raw), language or None)


async def show_filter(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    slug: str,
    page: int = 0,
    language: str | None = None,
) -> None:
    query = update.callback_query
    db = _db(context)
    cfg = _cfg(context)
    heading = await _heading(db, slug)

    items = await db.anime_by_filter(slug, limit=200)
    if language:
        items = [i for i in items if i["language"] in (language, "any")]

    if not items:
        if query:
            await query.edit_message_text(
                ui.empty_filter_text(heading), parse_mode=ParseMode.HTML
            )
        return

    page_size = cfg.page_size or PAGE_SIZE_DEFAULT
    pages = max(1, (len(items) + page_size - 1) // page_size)
    page = max(0, min(page, pages - 1))
    chunk = items[page * page_size : (page + 1) * page_size]

    if query:
        await query.edit_message_text(
            ui.pick_anime_text(heading, len(items)),
            reply_markup=ui.anime_list(chunk, page, pages, slug, language),
            parse_mode=ParseMode.HTML,
        )


async def _heading(db: Database, slug: str) -> str:
    if slug == "latest":
        return "🔥 Latest uploaded"
    if slug == "popular":
        return "⭐ Popular right now"
    row = await db._fetchone("SELECT name FROM filters WHERE slug = ?", (slug,))
    return f"🎭 {row['name']}" if row else slug.replace("-", " ").title()


# ------------------------------------------------------------------- search
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Free text: either a search for a user in search mode, or the auto menu."""
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None or message.text is None:
        return
    text = message.text.strip()
    if text.startswith("/"):
        return  # commands are handled elsewhere

    state = SEARCH_STATE.get(user.id)
    if state and state["expires"] > time.time():
        await run_search(update, context, text, state["language"])
        return
    if state:
        SEARCH_STATE.pop(user.id, None)

    await maybe_auto_menu(update, context)


async def maybe_auto_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """In a group, quietly offer the menu when people chat — never spam."""
    cfg = _cfg(context)
    chat = update.effective_chat
    message = update.effective_message
    if not cfg.auto_menu or chat is None or message is None or not is_group(chat):
        return
    last = AUTO_MENU_SEEN.get(chat.id, 0.0)
    if time.time() - last < cfg.auto_menu_cooldown:
        return
    AUTO_MENU_SEEN[chat.id] = time.time()
    try:
        await message.reply_text(
            ui.auto_menu_text(cfg.brand),
            reply_markup=ui.auto_menu(),
            parse_mode=ParseMode.HTML,
            disable_notification=True,
        )
    except Exception:
        log.debug("auto menu failed", exc_info=True)


async def run_search(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query: str, language: str
) -> None:
    db, cfg = _db(context), _cfg(context)
    results = await db.search(query, language)
    message = update.effective_message
    user = update.effective_user
    SEARCH_STATE.pop(user.id, None)  # one search per tap, no sticky mode
    if message is None:
        return
    if not results:
        await message.reply_text(
            ui.no_results_text(query),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔍 Search again", callback_data=f"{ui.CALLBACK_MENU}:search")]]
            ),
            parse_mode=ParseMode.HTML,
        )
        return
    heading = f"🔍 Results for “{query}”"
    page_size = cfg.page_size or PAGE_SIZE_DEFAULT
    pages = max(1, (len(results) + page_size - 1) // page_size)
    chunk = results[:page_size]
    await message.reply_text(
        ui.pick_anime_text(heading, len(results)),
        reply_markup=ui.anime_list(chunk, 0, pages, "search", language),
        parse_mode=ParseMode.HTML,
    )


# ---------------------------------------------------------------- join flow
async def _send_card(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int | str,
    anime: dict,
    caption: str,
    markup: InlineKeyboardMarkup,
) -> None:
    """Post the logo + caption when we have one, otherwise a plain text card."""
    if anime.get("poster"):
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=anime["poster"],
                caption=caption,
                reply_markup=markup,
                parse_mode=ParseMode.HTML,
            )
            return
        except Exception:
            log.warning("poster send failed, falling back to text", exc_info=True)
    await context.bot.send_message(
        chat_id=chat_id,
        text=caption,
        reply_markup=markup,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


async def on_anime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """``a:<anime_id>:<slug>:<language>`` — post the title + the group link."""
    query = update.callback_query
    if query is None or query.data is None:
        return
    db = _db(context)
    parts = query.data.split(":")
    anime_id = int(parts[1])
    slug = parts[2] if len(parts) > 2 else "latest"
    language = parts[3] if len(parts) > 3 else ""

    anime = await db.get_anime(anime_id)
    if anime is None:
        await query.answer("That title was removed.", show_alert=True)
        return

    # the link written in the card (/save …) wins; the filter/group link is the fallback
    group = await _link_for(db, slug, language or anime["language"])
    join_url = (anime.get("link") or "").strip() or (group["link"] if group else "")
    caption = ui.anime_card(anime["title"], anime["language"], anime["filters"])
    if not join_url:
        await query.answer("No group link saved for this filter yet.", show_alert=True)
        await query.message.reply_text(
            ui.no_group_link_text(), parse_mode=ParseMode.HTML
        )
        return

    label = f"🚀 Join & watch {ui.short(anime['title'], 24)}"
    rows = [[InlineKeyboardButton(label, url=join_url)]]
    # extra buttons written in the card, e.g. [🗞️Update](buttonurl:https://t.me/channel)
    for extra in anime.get("extras", []):
        try:
            extra_label, extra_url = extra
        except (TypeError, ValueError):
            continue
        if extra_url and extra_url != join_url:
            rows.append([InlineKeyboardButton(extra_label or "🔗 Open", url=extra_url)])
    rows.append(
        [
            InlineKeyboardButton(
                "🔔 Send me new episodes",
                callback_data=f"sub:{slug}:{language or anime['language']}",
            ),
            InlineKeyboardButton("🎬 Anime menu", callback_data=f"{ui.CALLBACK_MENU}:home"),
        ]
    )
    markup = InlineKeyboardMarkup(rows)

    chat = update.effective_chat
    posted_elsewhere = False
    # used from a DM: drop the card into the main group, exactly like the menu flow
    if chat is not None and not is_group(chat):
        target = await _post_chat(db)
        if target is not None:
            try:
                await _send_card(context, target, anime, caption, markup)
                posted_elsewhere = True
            except Exception:
                log.warning("could not post to %s", target, exc_info=True)

    await query.answer("Posted ✅")
    try:
        await query.message.delete()
    except Exception:
        pass

    note = "Posted in the group ✅ — tap to join:" if posted_elsewhere else "Here you go 👇"
    await _send_card(
        context,
        chat.id if chat else query.from_user.id,
        anime,
        f"{caption}\n\n<i>{note}</i>",
        markup,
    )


async def on_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """``sub:<slug>:<language>`` — remember the user so /broadcast reaches them."""
    query = update.callback_query
    if query is None or query.data is None:
        return
    db = _db(context)
    parts = query.data.split(":")
    slug = parts[1] if len(parts) > 1 else "latest"
    language = parts[2] if len(parts) > 2 else ""
    keys = [slug]
    if language:
        keys.append(f"{slug}:{language}")
    keys.append("menu")
    for key in keys:
        await db.mark_joined(query.from_user.id, key)
    await query.answer(
        "Done! I will DM you new episodes. (Turn on messages from the bot.)", show_alert=True
    )


async def _link_for(db: Database, slug: str, language: str) -> dict | None:
    candidates = []
    if language:
        candidates.append(f"{slug}:{language}")
    candidates.append(slug)
    if language:
        candidates.append(f"latest:{language}")
    candidates.append("menu")
    for candidate in candidates:
        row = await db.get_group(candidate)
        if row is not None:
            return row
    return None


async def _post_chat(db: Database) -> int | None:
    raw = await db.get_setting("post_chat_id", "")
    return int(raw) if raw.lstrip("-").isdigit() else None


# ------------------------------------------------------------------ misc
async def on_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user:
        SEARCH_STATE.pop(user.id, None)
    if update.effective_message:
        await update.effective_message.reply_text(
            "Cancelled. /menu whenever you need me."
        )


async def noop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query:
        await update.callback_query.answer()


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cfg = _cfg(context)
    user = update.effective_user
    lines = [
        f"<b>🎬 {ui.escape(cfg.brand)}</b>",
        "",
        "/menu — open the anime filter menu",
        "/latest — newest uploads",
        "/popular — most watched",
        "/genre — browse by genre",
        "/search — search (Hindi or English)",
        "/link — group links",
        "/help — this message",
    ]
    if user and user.id in cfg.admin_ids:
        lines += ["", ui.HELP_ADMIN]
    if update.effective_message:
        await update.effective_message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.HTML,
            reply_markup=ui.main_menu(cfg.brand),
            disable_web_page_preview=True,
        )


async def shortcut(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """``/latest``, ``/popular``, ``/genre`` and ``/search`` as plain commands."""
    message = update.effective_message
    if message is None or message.text is None:
        return
    command = message.text.split()[0].split("@")[0].lstrip("/")
    user = update.effective_user
    cfg = _cfg(context)
    if command == "latest":
        await _send_list(update, context, "latest")
    elif command == "popular":
        await _send_list(update, context, "popular")
    elif command == "search":
        if user:
            SEARCH_STATE[user.id] = {
                "language": "hindi",
                "expires": time.time() + cfg.search_timeout,
                "chat_id": message.chat_id,
            }
        await message.reply_text(
            ui.search_lang_text(),
            reply_markup=ui.search_langs(),
            parse_mode=ParseMode.HTML,
        )
    elif command == "genre":
        await message.reply_text(
            ui.genre_menu_text(),
            reply_markup=(await _genre_markup(context)),
            parse_mode=ParseMode.HTML,
        )


async def _genre_markup(context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardMarkup:
    db = _db(context)
    genres = [(r["slug"], r["name"]) for r in await db._fetchall(
        "SELECT slug, name FROM filters ORDER BY name")]
    return ui.genre_page(genres[:10], 0, max(1, (len(genres) + 9) // 10))


async def _send_list(
    update: Update, context: ContextTypes.DEFAULT_TYPE, slug: str
) -> None:
    db, cfg = _db(context), _cfg(context)
    message = update.effective_message
    if message is None:
        return
    items = await db.anime_by_filter(slug, limit=200)
    heading = await _heading(db, slug)
    if not items:
        await message.reply_text(ui.empty_filter_text(heading), parse_mode=ParseMode.HTML)
        return
    page_size = cfg.page_size or PAGE_SIZE_DEFAULT
    pages = max(1, (len(items) + page_size - 1) // page_size)
    await message.reply_text(
        ui.pick_anime_text(heading, len(items)),
        reply_markup=ui.anime_list(items[:page_size], 0, pages, slug),
        parse_mode=ParseMode.HTML,
    )


async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = _db(context)
    groups = await db.list_groups()
    if not groups:
        await update.effective_message.reply_text(
            "No group links saved yet. An admin can add one with "
            "<code>/setgroup menu &lt;link&gt;</code>",
            parse_mode=ParseMode.HTML,
        )
        return
    rows = [
        [InlineKeyboardButton(f"💬 {g['title'] or g['slug']}", url=g["link"])]
        for g in groups[:20]
    ]
    await update.effective_message.reply_text(
        "<b>💬 Our groups</b>",
        reply_markup=InlineKeyboardMarkup(rows),
        parse_mode=ParseMode.HTML,
    )
