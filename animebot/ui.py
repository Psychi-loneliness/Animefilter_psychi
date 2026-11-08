"""All user facing text and inline keyboards in one place.

Keeping copy here makes it easy to translate or rebrand the bot without touching
the handler logic.
"""
from __future__ import annotations

from typing import Iterable, Sequence

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

LANG_BADGE = {"hindi": "🇮🇳 Hindi", "english": "🇬🇧 English", "any": "🌐 Multi"}
LANG_FLAG = {"hindi": "🇮🇳", "english": "🇬🇧", "any": "🌐"}

CALLBACK_MENU = "m"


# --------------------------------------------------------------------- helpers
def slugify(text: str) -> str:
    """Turn ``Action / Adventure`` into ``action-adventure``."""
    out, dash = [], False
    for ch in text.strip().lower():
        if ch.isalnum():
            out.append(ch)
            dash = False
        elif not dash and out:
            out.append("-")
            dash = True
    slug = "".join(out).strip("-")
    return slug or "misc"


def escape(text: str) -> str:
    """Escape user/admin supplied text for HTML parse mode."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def short(title: str, limit: int = 34) -> str:
    return title if len(title) <= limit else title[: limit - 1] + "…"


# ------------------------------------------------------------------------ text
def main_menu_text(brand: str, total: int) -> str:
    return (
        f"<b>🎬 {escape(brand)} — Anime Filters</b>\n"
        "<i>Choose what you are in the mood for.</i>\n\n"
        f"🔥 <b>Latest Uploaded</b> — fresh drops\n"
        f"🎭 <b>Genre</b> — action, romance, isekai…\n"
        f"⭐ <b>Popular</b> — what everyone is watching\n"
        f"🔍 <b>Search</b> — by name, Hindi or English dub\n\n"
        f"<blockquote>{total} titles in the library</blockquote>"
    )


def search_lang_text() -> str:
    return (
        "<b>🔍 Search anime</b>\n\n"
        "Pick the audio language you want first — "
        "you will type the name in the next step."
    )


def search_prompt_text(language: str) -> str:
    badge = LANG_BADGE.get(language, LANG_BADGE["any"])
    return (
        f"<b>🔍 {badge} search</b>\n\n"
        "Send me the anime name now (or part of it).\n"
        "<i>Example:</i> <code>demon slayer</code>\n\n"
        "Type /cancel to stop."
    )


def no_results_text(query: str) -> str:
    return (
        f"No match for <b>{escape(query)}</b> yet.\n\n"
        "Try a shorter name, or ask an admin to add it with /add."
    )


def genre_menu_text() -> str:
    return "<b>🎭 Pick a genre</b>\n<i>More titles are added every day.</i>"


def empty_filter_text(name: str) -> str:
    return (
        f"<b>{escape(name)}</b> is empty right now 👀\n"
        "Check back after the next upload batch."
    )


def pick_anime_text(heading: str, count: int) -> str:
    return (
        f"<b>{escape(heading)}</b>\n"
        f"<i>{count} title(s) — tap one and I will post it with the group link.</i>"
    )


def saved_text(anime_id: int, title: str, language: str, tags: Iterable[str], has_poster: bool) -> str:
    badge = LANG_BADGE.get(language, LANG_BADGE["any"])
    tag_line = " • ".join(f"#{t}" for t in tags) if tags else "—"
    return (
        f"✅ <b>Saved #{anime_id}</b>\n"
        f"🎬 {escape(title)}\n"
        f"🗣 {badge}\n"
        f"🏷 {escape(tag_line)}\n"
        f"🖼 Logo: {'yes' if has_poster else 'no (reply an image with /poster ' + str(anime_id) + ')'}\n\n"
        "It shows up under 🔥 Latest Uploaded and in its genre."
    )


SAVE_HELP = """<b>🖼 Save an anime</b>

<b>1. Filter-bot card (what you already write)</b>
<code>/filter "The Case Study of Vanitas"[🍀Hindi dub🍀](buttonurl:https://t.me/+l16u8)</code>
<code>[🗞️Update](buttonurl:https://t.me/redlineanime)</code>
Reads the title, language, join link and extra buttons automatically.
Replace /filter with /save when you also attach a logo.

<b>2. Reply to the logo image</b>
<code>/save Demon Slayer | hindi | action,shonen | 95</code>

<b>3. Caption the image</b>
<code>/save Demon Slayer[🍀Hindi dub🍀](buttonurl:https://t.me/+abc)</code>

Extras are optional and order-free: <code>hindi</code>/<code>english</code>,
<code>action,shonen</code>, <code>95</code>, a <code>t.me</code> link,
or explicit <code>lang=hindi | tags=action | pop=95</code>.

<code>/poster 12</code> (reply to an image) — attach or replace the logo of #12.
"""


def anime_card(name: str, language: str, tags: Iterable[str]) -> str:
    badge = LANG_BADGE.get(language, LANG_BADGE["any"])
    tag_line = " • ".join(f"#{t}" for t in tags) if tags else ""
    lines = [f"🎬 <b>{escape(name)}</b>", f"🗣 {badge}"]
    if tag_line:
        lines.append(f"🏷 {escape(tag_line)}")
    lines.append("\n👇 Join the group to watch the full episodes.")
    return "\n".join(lines)


def auto_menu_text(brand: str) -> str:
    return f"🎬 Looking for something to watch in <b>{escape(brand)}</b>? Tap the menu 👇"


def no_group_link_text() -> str:
    return (
        "⚠️ No group link saved for this filter yet.\n"
        "<i>An admin can add one with</i> <code>/setgroup &lt;filter&gt; &lt;link&gt;</code>"
    )


HELP_ADMIN = """<b>🛠 Admin commands</b>

<b>Library</b>
<code>/add Title | link | hindi | action,comedy | 80</code>
<code>/quick 125 | 90</code> — set popularity of anime #125
<code>/del 125</code> — remove anime by id
<code>/find word</code> — list ids

<b>Filters</b>
<code>/filter action Action &amp; Adventure</code>
<code>/filters</code> · <code>/unfilter slug</code>

<b>Group links</b>
<code>/setgroup menu https://t.me/+xxxx</code> — default link
<code>/setgroup action:hindi https://t.me/+yyyy</code>
<code>/groups</code> · <code>/ungroup slug</code>

<b>Behaviour</b>
<code>/automenu on|off</code> · <code>/cooldown 120</code>
<code>/stats</code> · <code>/broadcast your text</code>
"""


# -------------------------------------------------------------------- keyboards
def main_menu(brand: str = "") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔥 Latest Uploaded", callback_data=f"{CALLBACK_MENU}:latest")],
            [
                InlineKeyboardButton("🎭 Genre", callback_data=f"{CALLBACK_MENU}:genres"),
                InlineKeyboardButton("⭐ Popular", callback_data=f"{CALLBACK_MENU}:popular"),
            ],
            [InlineKeyboardButton("🔍 Search", callback_data=f"{CALLBACK_MENU}:search")],
            [InlineKeyboardButton("✖️ Close", callback_data=f"{CALLBACK_MENU}:close")],
        ]
    )


def auto_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🎬 Anime menu", callback_data=f"{CALLBACK_MENU}:home")]]
    )


def search_langs() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🇮🇳 Hindi", callback_data=f"{CALLBACK_MENU}:search:hi")],
            [InlineKeyboardButton("🇬🇧 English", callback_data=f"{CALLBACK_MENU}:search:en")],
            [InlineKeyboardButton("⬅️ Back", callback_data=f"{CALLBACK_MENU}:home")],
        ]
    )


def genre_page(
    genres: Sequence[tuple[str, str]], page: int, pages: int
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for slug, name in genres:
        row.append(InlineKeyboardButton(name, callback_data=f"g:{slug}:0"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"gp:{page - 1}"))
    nav.append(InlineKeyboardButton(f"{page + 1}/{max(pages, 1)}", callback_data="noop"))
    if page + 1 < pages:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"gp:{page + 1}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data=f"{CALLBACK_MENU}:home")])
    return InlineKeyboardMarkup(rows)


def anime_list(
    items: Sequence[dict],
    page: int,
    pages: int,
    heading_slug: str,
    language: str | None = None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    start = page * 0
    for index, item in enumerate(items, start=1):
        flag = LANG_FLAG.get(item.get("language", "any"), "🌐")
        label = f"{start + index}. {short(item['title'])} {flag}"
        lang = language or item.get("language", "")
        rows.append(
            [InlineKeyboardButton(label, callback_data=f"a:{item['id']}:{heading_slug}:{lang}")]
        )
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"lp:{heading_slug}:{language or ''}:{page - 1}"))
    if pages > 1:
        nav.append(InlineKeyboardButton(f"{page + 1}/{pages}", callback_data="noop"))
    if page + 1 < pages:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"lp:{heading_slug}:{language or ''}:{page + 1}"))
    if nav:
        rows.append(nav)
    back = f"{CALLBACK_MENU}:search" if language else f"{CALLBACK_MENU}:home"
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data=back)])
    return InlineKeyboardMarkup(rows)


def join_button(link: str, label: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(label, url=link)], [InlineKeyboardButton("🎬 Anime menu", callback_data=f"{CALLBACK_MENU}:home")]]
    )
