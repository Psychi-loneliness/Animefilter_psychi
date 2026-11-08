"""Admin commands: library, filters, group links, broadcast."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Awaitable, Callable

from telegram import Chat, Message, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from .. import card, ui
from ..db import Database

log = logging.getLogger(__name__)

_ADMIN_CACHE: dict[tuple[int, int], float] = {}
_ADMIN_TTL = 300

Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]


def _db(context: ContextTypes.DEFAULT_TYPE) -> Database:
    return context.application.bot_data["db"]


def _cfg(context: ContextTypes.DEFAULT_TYPE):
    return context.application.bot_data["config"]


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Env listed admins, plus admins of the group the command was typed in."""
    user = update.effective_user
    chat = update.effective_chat
    if user is None:
        return False
    if user.id in _cfg(context).admin_ids:
        return True
    if chat is None or chat.type not in (Chat.GROUP, Chat.SUPERGROUP):
        return False
    key = (chat.id, user.id)
    if time.time() - _ADMIN_CACHE.get(key, 0) < _ADMIN_TTL:
        return True
    try:
        member = await chat.get_member(user.id)
        if member.status in ("administrator", "creator"):
            _ADMIN_CACHE[key] = time.time()
            return True
    except Exception:
        log.debug("admin lookup failed", exc_info=True)
    return False


def admin_only(func: Handler) -> Handler:
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await is_admin(update, context):
            if update.effective_message:
                await update.effective_message.reply_text(
                    "⛔ Admins only. Ask the owner to add your id in ADMIN_IDS."
                )
            return
        await func(update, context)

    wrapper.__name__ = func.__name__
    return wrapper


def _payload(message: Message) -> str:
    text = message.text or message.caption or ""
    parts = text.split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ""


# ----------------------------------------------------------------- /add /save
def _extras_pairs(entry) -> list[list[str]]:
    return [[e.label, e.url] for e in entry.other_buttons()]


async def _persist(context, entry, poster: str = "") -> int:
    """Upsert a parsed card / entry and return the anime id."""
    db = _db(context)
    for tag in entry.tags:
        await db.upsert_filter(tag, tag.replace("-", " ").title())
    return await db.add_anime(
        title=entry.title,
        link=entry.primary_link,
        language=entry.language,
        tags=entry.tags,
        popularity=entry.popularity,
        poster=poster,
        extras=_extras_pairs(entry),
    )


def _poster_of(message: Message) -> str:
    """Return a reusable file_id for a photo / image document, else ''."""
    if message is None:
        return ""
    if message.photo:
        return message.photo[-1].file_id  # largest size
    doc = message.document
    if doc is not None and (doc.mime_type or "").startswith("image/"):
        return doc.file_id
    if message.animation and message.animation.thumbnail:
        return message.animation.thumbnail.file_id
    return ""


@admin_only
async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """``/save <name> …`` — accepts the filter-bot card syntax and/or a logo image.

    The image can be the message itself (as a caption) or the message the command
    replies to.
    """
    message = update.effective_message
    raw = _payload(message)
    if not raw:
        await message.reply_text(ui.SAVE_HELP, parse_mode=ParseMode.HTML)
        return

    entry = card.parse_entry(raw)
    if not entry.title:
        await message.reply_text("Give me a name: <code>/save Demon Slayer</code>",
                                 parse_mode=ParseMode.HTML)
        return

    poster = _poster_of(message) or _poster_of(message.reply_to_message)
    if not poster and not entry.primary_link:
        await message.reply_text(
            "🖼 I need the logo image or a join link.\n\n"
            "Send the image first, then <b>reply to it</b> with "
            f"<code>/save {ui.escape(entry.title)}</code>, "
            "or paste the card with a button URL.",
            parse_mode=ParseMode.HTML,
        )
        return

    anime_id = await _persist(context, entry, poster)
    preview = card.render_preview(entry, ui.escape)
    await message.reply_text(
        f"✅ <b>Saved #{anime_id}</b>"
        + (" · 🖼 logo attached" if poster else " · no logo yet (<code>/poster "
           + str(anime_id) + "</code> to add one)")
        + "\n\n"
        + preview
        + "\n\n<i>Live under 🔥 Latest and its genres.</i>",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    if entry.tags:
        await _notify_subscribers(context, entry.tags, entry.title)


@admin_only
async def poster_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Attach / replace the logo of an existing entry."""
    message = update.effective_message
    raw = _payload(message).strip().lstrip("#")
    if not raw.isdigit():
        await message.reply_text("Usage: reply to an image with /poster <anime_id>")
        return
    anime_id = int(raw)
    poster = _poster_of(message.reply_to_message) or _poster_of(message)
    if not poster:
        await message.reply_text(
            "Reply to the logo image with that command so I know which picture to use."
        )
        return
    db = _db(context)
    anime = await db.get_anime(anime_id)
    if anime is None:
        await message.reply_text("No anime with that id. Use /find to look it up.")
        return
    await db.set_poster(anime_id, poster)
    await message.reply_text(
        f"🖼 Logo updated for <b>{ui.escape(anime['title'])}</b> (#{anime_id}).",
        parse_mode=ParseMode.HTML,
    )


@admin_only
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """``/add`` — same parser as /save (link-only entries, no logo needed)."""
    message = update.effective_message
    raw = _payload(message)
    if not raw:
        await message.reply_text(
            "<b>Add an anime</b>\n"
            "<code>/add Demon Slayer | hindi | action,adventure | 90</code>\n"
            "<code>/add \"Demon Slayer\"[🍀Hindi dub🍀](buttonurl:https://t.me/+abc)</code>\n\n"
            "With a logo, use /save instead.",
            parse_mode=ParseMode.HTML,
        )
        return

    entry = card.parse_entry(raw)
    if not entry.title:
        await message.reply_text("Title is required.")
        return

    if not entry.primary_link:
        reply = message.reply_to_message
        if reply is not None and reply.text:
            entry.link = reply.text.strip()
    poster = _poster_of(message) or _poster_of(message.reply_to_message)

    if not entry.primary_link and not poster:
        await message.reply_text(
            "I need the filter bot link (or a logo image).\n"
            "<code>/add Title | https://…</code>\n"
            "<code>/add \"Title\"[🍀Hindi dub🍀](buttonurl:https://…)</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    anime_id = await _persist(context, entry, poster)
    await message.reply_text(
        f"✅ <b>Saved #{anime_id}</b>\n\n" + card.render_preview(entry, ui.escape),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    if entry.tags:
        await _notify_subscribers(context, entry.tags, entry.title)


async def _notify_subscribers(
    context: ContextTypes.DEFAULT_TYPE, tags: list[str], title: str
) -> None:
    db = _db(context)
    users = await db.joined_users(tags)
    if not users:
        return
    text = f"🎬 New drop: <b>{ui.escape(title)}</b>\nOpen the menu to grab the link."
    markup = ui.main_menu()
    for user_id in users:
        try:
            await context.bot.send_message(
                user_id, text, reply_markup=markup, parse_mode=ParseMode.HTML
            )
        except Exception:
            log.debug("dm failed for %s", user_id)


# -------------------------------------------------------------- /filter
@admin_only
async def filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Two jobs:

    1. Filter-bot card  → saves the anime
       ``/filter "The Case Study of Vanitas"[🍀Hindi dub🍀](buttonurl:https://t.me/+x)``
    2. Plain genre      → creates a genre button
       ``/filter action Action & Adventure``
    """
    message = update.effective_message
    raw = _payload(message)
    if not raw:
        await message.reply_text(
            "<b>Filter bot card → save the anime</b>\n"
            '<code>/filter "The Case Study of Vanitas"[🍀Hindi dub🍀]'
            "(buttonurl:https://t.me/+l16u8)</code>\n"
            "<code>[🗞️Update](buttonurl:https://t.me/redlineanime)</code>\n\n"
            "<b>Or create a genre button</b>\n"
            "<code>/filter action Action &amp; Adventure</code>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return

    if card.looks_like_card(raw):
        entry = card.parse_entry(raw)
        if not entry.title:
            await message.reply_text("I could not read a title in that card.")
            return
        poster = _poster_of(message) or _poster_of(message.reply_to_message)
        anime_id = await _persist(context, entry, poster)
        await message.reply_text(
            f"✅ <b>Card saved as #{anime_id}</b>"
            + (" · 🖼 logo attached" if poster else "")
            + "\n\n"
            + card.render_preview(entry, ui.escape)
            + "\n\n<i>Members now find it under 🔥 Latest, ⭐ Popular and its genres.</i>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        if entry.tags:
            await _notify_subscribers(context, entry.tags, entry.title)
        return

    # plain genre definition
    cleaned = raw.replace("|", " ").strip()
    parts = cleaned.split(maxsplit=1)
    slug = ui.slugify(parts[0])
    name = parts[1].strip() if len(parts) > 1 else slug.replace("-", " ").title()
    db = _db(context)
    await db.upsert_filter(slug, name)
    await message.reply_text(
        f"✅ Filter <b>{ui.escape(name)}</b> is live with slug <code>{slug}</code>.",
        parse_mode=ParseMode.HTML,
    )


@admin_only
async def filters_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = _db(context)
    rows = await db._fetchall("SELECT slug, name FROM filters ORDER BY name")
    if not rows:
        await update.effective_message.reply_text("No filters yet. Use /filter.")
        return
    lines = [f"🎭 <b>Filters</b> ({len(rows)})"]
    for row in rows:
        count = await db.count_by_filter(row["slug"])
        lines.append(f"• <code>{row['slug']}</code> — {ui.escape(row['name'])} ({count})")
    await update.effective_message.reply_text(
        "\n".join(lines), parse_mode=ParseMode.HTML
    )


@admin_only
async def unfilter_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    slug = ui.slugify(_payload(update.effective_message).split(" ")[0]) if _payload(
        update.effective_message) else ""
    if not slug:
        await update.effective_message.reply_text("Usage: /unfilter <slug>")
        return
    db = _db(context)
    row = await db._fetchone("SELECT id FROM filters WHERE slug = ?", (slug,))
    if row is None:
        await update.effective_message.reply_text(f"No filter with slug <code>{slug}</code>.",
                                                 parse_mode=ParseMode.HTML)
        return
    await db._exec("DELETE FROM anime_filter WHERE filter_id = ?", (row["id"],))
    await db._exec("DELETE FROM filters WHERE id = ?", (row["id"],))
    await update.effective_message.reply_text(f"🗑 Filter <code>{slug}</code> removed.",
                                              parse_mode=ParseMode.HTML)


# -------------------------------------------------------------- /setgroup
@admin_only
async def setgroup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    raw = _payload(message)
    if not raw:
        await message.reply_text(
            "<b>Save a group link</b>\n"
            "<code>/setgroup menu https://t.me/+xxxx</code> — default for every filter\n"
            "<code>/setgroup action https://t.me/+yyyy</code> — only the action filter\n"
            "<code>/setgroup action:hindi https://t.me/+zzzz</code> — that filter in Hindi\n\n"
            "Send <code>/setgroup menu</code> alone (in the group) and I will use this chat's invite link.",
            parse_mode=ParseMode.HTML,
        )
        return
    parts = raw.split(maxsplit=1)
    slug = parts[0].strip().lower()
    link = parts[1].strip() if len(parts) > 1 else ""

    if not link:
        chat = update.effective_chat
        if chat is None or chat.type not in (Chat.GROUP, Chat.SUPERGROUP):
            await message.reply_text("Add the link: /setgroup menu https://t.me/+xxxx")
            return
        try:
            link = await context.bot.export_chat_invite_link(chat.id)
        except Exception:
            await message.reply_text(
                "I couldn't create an invite link — make me admin with ‘invite users’ "
                "or paste the link: /setgroup menu https://t.me/+xxxx"
            )
            return

    if not (link.startswith("https://t.me/") or link.startswith("http")):
        await message.reply_text("That does not look like a t.me link.")
        return

    db = _db(context)
    await db.set_group(slug, link, title=update.effective_chat.title or "" if update.effective_chat else "")
    await message.reply_text(
        f"✅ Group link saved for <code>{ui.escape(slug)}</code>.\nTap an anime in the menu to try it.",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


@admin_only
async def groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = _db(context)
    groups = await db.list_groups()
    if not groups:
        await update.effective_message.reply_text("No group links yet. Use /setgroup.")
        return
    lines = [f"💬 <b>Group links</b> ({len(groups)})"]
    for g in groups:
        lines.append(f"• <code>{g['slug']}</code> → {ui.escape(g['link'])}")
    await update.effective_message.reply_text(
        "\n".join(lines), parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


@admin_only
async def ungroup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    slug = _payload(update.effective_message).strip().lower()
    if not slug:
        await update.effective_message.reply_text("Usage: /ungroup <slug>")
        return
    await _db(context).delete_group(slug)
    await update.effective_message.reply_text(f"🗑 Link for <code>{ui.escape(slug)}</code> removed.",
                                              parse_mode=ParseMode.HTML)


# ------------------------------------------------------------- library edit
@admin_only
async def del_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    raw = _payload(update.effective_message).strip().lstrip("#")
    if not raw.isdigit():
        await update.effective_message.reply_text("Usage: /del <anime_id>")
        return
    db = _db(context)
    anime = await db.get_anime(int(raw))
    if anime is None:
        await update.effective_message.reply_text("No anime with that id.")
        return
    await db.delete_anime(int(raw))
    await update.effective_message.reply_text(
        f"🗑 Removed <b>{ui.escape(anime['title'])}</b> (#{raw}).", parse_mode=ParseMode.HTML
    )


@admin_only
async def quick_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """``/quick 12 95`` — set popularity so it shows under ⭐ Popular."""
    parts = _payload(update.effective_message).replace("|", " ").split()
    if len(parts) < 2 or not parts[0].lstrip("#").isdigit() or not parts[1].isdigit():
        await update.effective_message.reply_text("Usage: /quick <anime_id> <popularity 0-100>")
        return
    db = _db(context)
    anime_id, popularity = int(parts[0].lstrip("#")), int(parts[1])
    if await db.get_anime(anime_id) is None:
        await update.effective_message.reply_text("No anime with that id.")
        return
    await db._exec("UPDATE anime SET popularity = ? WHERE id = ?", (popularity, anime_id))
    await update.effective_message.reply_text(f"⭐ #{anime_id} popularity set to {popularity}.")


@admin_only
async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = _payload(update.effective_message).strip()
    db = _db(context)
    rows = await db.search(query, "any", limit=15)
    if not rows:
        await update.effective_message.reply_text("Nothing found.")
        return
    lines = ["🔎 <b>Matches</b>"]
    for r in rows:
        lines.append(
            f"#{r['id']} — {ui.escape(r['title'])} "
            f"({ui.LANG_FLAG.get(r['language'], '🌐')} • ⭐{r['popularity']})"
        )
    await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


@admin_only
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = _db(context)
    stats = await db.stats()
    await update.effective_message.reply_text(
        "<b>📊 Bot stats</b>\n"
        f"🎬 Anime: {stats['anime']}\n"
        f"💬 Group links: {stats['groups']}\n"
        f"🔔 Subscribers: {stats['users']}\n"
        f"⚙️ Auto menu: {'on' if await db.get_setting('auto_menu', '1') == '1' else 'off'}",
        parse_mode=ParseMode.HTML,
    )


@admin_only
async def automenu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    value = _payload(update.effective_message).strip().lower()
    if value not in ("on", "off"):
        current = await _db(context).get_setting("auto_menu", "1")
        await update.effective_message.reply_text(
            f"Auto menu is currently {'on' if current == '1' else 'off'}.\nUse /automenu on|off"
        )
        return
    db = _db(context)
    await db.set_setting("auto_menu", "1" if value == "on" else "0")
    _cfg(context).auto_menu = value == "on"
    await update.effective_message.reply_text(f"✅ Auto menu {value}.")


@admin_only
async def cooldown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    raw = _payload(update.effective_message).strip()
    if not raw.isdigit():
        await update.effective_message.reply_text(
            f"Auto menu cooldown is {_cfg(context).auto_menu_cooldown}s. "
            "Usage: /cooldown <seconds>"
        )
        return
    seconds = max(10, int(raw))
    cfg = _cfg(context)
    cfg.auto_menu_cooldown = seconds
    await _db(context).set_setting("auto_menu_cooldown", str(seconds))
    await update.effective_message.reply_text(f"✅ Cooldown set to {seconds}s.")


@admin_only
async def posthere_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remember this chat as the place to post titles when the menu is used in DMs."""
    chat = update.effective_chat
    await _db(context).set_setting("post_chat_id", str(chat.id))
    await update.effective_message.reply_text(
        f"✅ Posts from DM menus will appear here ({ui.escape(chat.title or str(chat.id))}).",
        parse_mode=ParseMode.HTML,
    )


@admin_only
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = _payload(update.effective_message)
    if not text:
        await update.effective_message.reply_text(
            "Usage: /broadcast <text> (HTML allowed)\nReply to a photo/message to forward it."
        )
        return
    db = _db(context)
    users = await db.joined_users()
    sent = failed = 0
    status = await update.effective_message.reply_text(f"📤 Sending to {len(users)} chats…")
    for user_id in users:
        try:
            await context.bot.send_message(
                user_id, text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await status.edit_text(f"✅ Sent {sent} • ❌ Failed {failed}")
