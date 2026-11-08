"""End-to-end walkthrough of the exact flow:

group chatter → "Anime menu" button → the 4 options → Hindi/English → title →
the bot posts the anime name in the group with the filter-bot group link.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from telegram import Chat, Message, Update, User

from animebot import ui
from animebot.config import Config
from animebot.db import Database
from animebot.handlers import menu


# --------------------------------------------------------------------- fakes
class FakeMessage:
    def __init__(self, chat: Chat, message_id: int = 1) -> None:
        self.chat = chat
        self.chat_id = chat.id
        self.message_id = message_id
        self.text = ""
        self.sent: list[dict] = []
        self.deleted = False

    async def reply_text(self, text, **kwargs):
        self.sent.append({"text": text, **kwargs})
        return FakeMessage(self.chat, len(self.sent) + 100)

    async def delete(self):
        self.deleted = True

    async def edit_text(self, text, **kwargs):
        self.sent.append({"text": text, "edited": True, **kwargs})


class FakeBot:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def send_message(self, chat_id, text, **kwargs):
        self.messages.append({"chat_id": chat_id, "text": text, **kwargs})
        return FakeMessage(Chat(chat_id, Chat.SUPERGROUP))


class FakeContext:
    def __init__(self, db, config) -> None:
        self.bot = FakeBot()
        self.application = SimpleNamespace(
            bot_data={"db": db, "config": config}
        )


def make_update(chat: Chat, user: User, text: str = "", callback: str | None = None):
    """Build a fake Update exposing the attributes the handlers touch."""
    message = FakeMessage(chat)
    message.text = text

    if callback is None:
        update = SimpleNamespace(
            callback_query=None,
            effective_message=message,
            effective_chat=chat,
            effective_user=user,
        )
        return update, message

    query = SimpleNamespace(
        data=callback,
        from_user=user,
        message=message,
        answered=[],
    )

    async def answer(text=None, show_alert=False):
        query.answered.append({"text": text, "alert": show_alert})

    async def edit_message_text(text, **kwargs):
        message.sent.append({"text": text, "edited": True, **kwargs})

    query.answer = answer
    query.edit_message_text = edit_message_text
    update = SimpleNamespace(
        callback_query=query,
        effective_message=message,
        effective_chat=chat,
        effective_user=user,
    )
    return update, message


@pytest.fixture
def group_chat():
    return Chat(id=-100123, type=Chat.SUPERGROUP, title="Anime GC")


@pytest.fixture
def user():
    return User(id=555, first_name="Psychi", is_bot=False, username="psychi")


@pytest.fixture
def config():
    return Config(bot_token="x", admin_ids=frozenset({1}), page_size=8)


@pytest.fixture
async def seeded(db):
    await db.upsert_filter("action", "🔥 Action")
    await db.upsert_filter("romance", "💞 Romance")
    await db.add_anime("Demon Slayer", "https://t.me/+demo-hi", "hindi",
                       tags=["action"], popularity=99)
    await db.add_anime("Horimiya", "https://t.me/+hori-hi", "hindi",
                       tags=["romance"], popularity=70)
    await db.add_anime("Blue Lock", "https://t.me/+blue-en", "english",
                       tags=["action"], popularity=95)
    await db.set_group("menu", "https://t.me/+MAIN_GC", "Main group")
    await db.set_group("action:hindi", "https://t.me/+ACTION_HINDI", "Action Hindi")
    return db


# -------------------------------------------------------------------- tests
@pytest.mark.asyncio
async def test_menu_opens_with_the_four_options(group_chat, user, config, seeded):
    update, message = make_update(group_chat, user, "/menu")
    context = FakeContext(seeded, config)
    await menu.menu_command(update, context)

    assert message.sent, "/menu must reply"
    markup = message.sent[0]["reply_markup"]
    labels = [b.text for row in markup.inline_keyboard for b in row]
    assert any("Latest" in lb for lb in labels)
    assert any("Genre" in lb for lb in labels)
    assert any("Popular" in lb for lb in labels)
    assert any("Search" in lb for lb in labels)
    callbacks = [b.callback_data for row in markup.inline_keyboard for b in row]
    assert "m:latest" in callbacks and "m:genres" in callbacks
    assert "m:popular" in callbacks and "m:search" in callbacks


@pytest.mark.asyncio
async def test_auto_menu_appears_on_group_chatter_only_once(group_chat, user, config, seeded):
    context = FakeContext(seeded, config)
    menu.AUTO_MENU_SEEN.clear()

    update, message = make_update(group_chat, user, "hey guys")
    await menu.on_text(update, context)
    assert message.sent and message.sent[0]["reply_markup"].inline_keyboard[0][0].callback_data == "m:home"

    update2, message2 = make_update(group_chat, user, "another message")
    await menu.on_text(update2, context)
    assert message2.sent == []  # cooldown: no spam per message


@pytest.mark.asyncio
async def test_auto_menu_respects_off_switch(group_chat, user, config, seeded):
    config.auto_menu = False
    context = FakeContext(seeded, config)
    menu.AUTO_MENU_SEEN.clear()
    update, message = make_update(group_chat, user, "hello")
    await menu.on_text(update, context)
    assert message.sent == []


@pytest.mark.asyncio
async def test_latest_button_lists_newest_anime(group_chat, user, config, seeded):
    update, message = make_update(group_chat, user, callback="m:latest")
    context = FakeContext(seeded, config)
    await menu.on_menu_button(update, context)

    buttons = message.sent[-1]["reply_markup"].inline_keyboard
    labels = " ".join(b.text for row in buttons for b in row)
    assert "Blue Lock" in labels  # added last -> newest
    assert buttons[0][0].callback_data.startswith("a:")


@pytest.mark.asyncio
async def test_search_flow_hindi_then_typed_name(group_chat, user, config, seeded):
    context = FakeContext(seeded, config)

    # 1) press 🔍 Search -> language choice
    update, message = make_update(group_chat, user, callback="m:search")
    await menu.on_menu_button(update, context)
    langs = [b.callback_data for row in message.sent[-1]["reply_markup"].inline_keyboard for b in row]
    assert "m:search:hi" in langs and "m:search:en" in langs

    # 2) press 🇮🇳 Hindi -> bot asks for the name
    update, message = make_update(group_chat, user, callback="m:search:hi")
    await menu.on_menu_button(update, context)
    assert "Hindi" in message.sent[-1]["text"]
    assert menu.SEARCH_STATE[user.id]["language"] == "hindi"

    # 3) type the name -> result buttons, not the auto menu
    update, message = make_update(group_chat, user, "demon")
    await menu.on_text(update, context)
    result_buttons = message.sent[-1]["reply_markup"].inline_keyboard
    assert "Demon Slayer" in result_buttons[0][0].text
    assert user.id not in menu.SEARCH_STATE  # one shot


@pytest.mark.asyncio
async def test_english_search_hides_hindi_only_titles(group_chat, user, config, seeded):
    context = FakeContext(seeded, config)
    update, _ = make_update(group_chat, user, callback="m:search:en")
    await menu.on_menu_button(update, context)
    update, message = make_update(group_chat, user, "l")  # single letter, broad match
    await menu.on_text(update, context)
    labels = " ".join(
        b.text for row in message.sent[-1]["reply_markup"].inline_keyboard for b in row
    )
    assert "Blue Lock" in labels
    assert "Demon Slayer" not in labels


@pytest.mark.asyncio
async def test_tapping_anime_posts_name_and_join_link_in_group(group_chat, user, config, seeded):
    context = FakeContext(seeded, config)
    anime = (await seeded.search("Demon Slayer", "hindi"))[0]

    update, message = make_update(
        group_chat, user, callback=f"a:{anime['id']}:latest:hindi"
    )
    await menu.on_anime(update, context)

    assert message.deleted, "the chooser message is cleaned up"
    assert context.bot.messages, "something must be posted"
    posted = context.bot.messages[-1]
    assert posted["chat_id"] == group_chat.id
    assert "Demon Slayer" in posted["text"]
    url_buttons = [
        b for row in posted["reply_markup"].inline_keyboard for b in row if b.url
    ]
    # the title's own link (as saved by the admin) wins
    assert url_buttons[0].url == "https://t.me/+demo-hi"
    assert "Join" in url_buttons[0].text


@pytest.mark.asyncio
async def test_hindi_action_filter_uses_the_dedicated_group_link(group_chat, user, config, seeded):
    context = FakeContext(seeded, config)
    # a poster-only entry (no link written in the card) falls back to /setgroup links
    await seeded.upsert_filter("action", "🔥 Action")
    anime_id = await seeded.add_anime("Bleach", "", "hindi", tags=["action"], poster="FILE")
    anime = {"id": anime_id}
    update, _ = make_update(group_chat, user, callback=f"a:{anime['id']}:action:hindi")
    await menu.on_anime(update, context)
    url = [b for row in context.bot.messages[-1]["reply_markup"].inline_keyboard
           for b in row if b.url][0]
    assert url.url == "https://t.me/+ACTION_HINDI"


@pytest.mark.asyncio
async def test_missing_group_link_tells_admin_what_to_do(group_chat, user, config, db):
    await db.add_anime("Lonely Show", "", "hindi")
    anime = (await db.search("Lonely", "hindi"))[0]
    context = FakeContext(db, config)
    update, message = make_update(group_chat, user, callback=f"a:{anime['id']}:latest:hindi")
    await menu.on_anime(update, context)
    assert "setgroup" in message.sent[-1]["text"]


@pytest.mark.asyncio
async def test_subscribe_records_user_for_broadcasts(group_chat, user, config, seeded):
    context = FakeContext(seeded, config)
    update, _ = make_update(group_chat, user, callback="sub:action:hindi")
    await menu.on_subscribe(update, context)
    assert user.id in await seeded.joined_users(["action:hindi"])
    assert user.id in await seeded.joined_users(["menu"])


@pytest.mark.asyncio
async def test_genre_button_lists_genres(group_chat, user, config, seeded):
    context = FakeContext(seeded, config)
    update, message = make_update(group_chat, user, callback="m:genres")
    await menu.on_menu_button(update, context)
    callbacks = [b.callback_data for row in message.sent[-1]["reply_markup"].inline_keyboard for b in row]
    assert any(cb.startswith("g:action") for cb in callbacks)
    assert any(cb.startswith("g:romance") for cb in callbacks)


@pytest.mark.asyncio
async def test_close_button_removes_menu(group_chat, user, config, seeded):
    context = FakeContext(seeded, config)
    update, message = make_update(group_chat, user, callback="m:close")
    await menu.on_menu_button(update, context)
    assert message.deleted


def test_slugify_and_helpers():
    assert ui.slugify("Action & Adventure") == "action-adventure"
    assert ui.slugify("Sci-Fi!!") == "sci-fi"
    assert ui.slugify("  ") == "misc"
    assert ui.escape("<b>x&y</b>") == "&lt;b&gt;x&amp;y&lt;/b&gt;"
    assert ui.short("a" * 40, 10).endswith("…")


# ------------------------------------------------------- /save with a logo
class FakePhoto:
    def __init__(self, file_id: str, width: int) -> None:
        self.file_id = file_id
        self.width = width


class AdminMessage(FakeMessage):
    """Message that can carry a photo / caption / reply."""

    def __init__(self, chat, message_id=1, caption="", photos=(), reply=None):
        super().__init__(chat, message_id)
        self.caption = caption
        self.photo = tuple(photos)
        self.document = None
        self.animation = None
        self.reply_to_message = reply


def make_admin_update(chat, user, text="", caption="", photos=(), reply=None):
    message = AdminMessage(chat, caption=caption, photos=photos, reply=reply)
    message.text = text
    update = SimpleNamespace(
        callback_query=None,
        effective_message=message,
        effective_chat=chat,
        effective_user=user,
    )
    return update, message


@pytest.mark.asyncio
async def test_save_with_replied_logo_image(group_chat, user, config, db):
    from animebot.handlers import admin

    config.admin_ids = frozenset({user.id})
    context = FakeContext(db, config)
    logo = AdminMessage(group_chat, photos=[FakePhoto("small", 90), FakePhoto("big", 900)])
    update, message = make_admin_update(
        group_chat, user, text="/save Demon Slayer | hindi | action,shonen | 97", reply=logo
    )
    await admin.save_command(update, context)

    assert "Saved" in message.sent[-1]["text"]
    rows = await db.search("Demon", "hindi")
    assert rows and rows[0]["poster"] == "big"  # largest size is stored
    assert "action" in (await db.get_anime(rows[0]["id"]))["filters"]
    assert rows[0]["popularity"] == 97


@pytest.mark.asyncio
async def test_save_as_photo_caption(group_chat, user, config, db):
    from animebot.handlers import admin

    config.admin_ids = frozenset({user.id})
    context = FakeContext(db, config)
    update, message = make_admin_update(
        group_chat, user, caption="/save Solo Leveling", photos=[FakePhoto("solo", 800)]
    )
    await admin.save_command(update, context)
    rows = await db.search("Solo", "any")
    assert rows[0]["language"] == "any"  # no language given
    assert rows[0]["poster"] == "solo"


@pytest.mark.asyncio
async def test_save_without_image_explains_how(group_chat, user, config, db):
    from animebot.handlers import admin

    config.admin_ids = frozenset({user.id})
    context = FakeContext(db, config)
    update, message = make_admin_update(group_chat, user, text="/save Bleach")
    await admin.save_command(update, context)
    assert "logo image" in message.sent[-1]["text"]
    assert await db.count_anime() == 0


@pytest.mark.asyncio
async def test_saved_logo_is_posted_with_join_link(group_chat, user, config, db):
    from telegram import InlineKeyboardMarkup
    from animebot.handlers import menu

    await db.set_group("menu", "https://t.me/+MAIN")
    anime_id = await db.add_anime("Bleach TYBW", "https://t.me/+f", "hindi", poster="FILE123")
    sent = {}

    class PhotoBot(FakeBot):
        async def send_photo(self, chat_id, photo, caption="", reply_markup=None, **kw):
            sent.update(chat_id=chat_id, photo=photo, caption=caption, markup=reply_markup)
            return FakeMessage(Chat(chat_id, Chat.SUPERGROUP))

    context = FakeContext(db, config)
    context.bot = PhotoBot()
    update, _ = make_update(group_chat, user, callback=f"a:{anime_id}:latest:hindi")
    await menu.on_anime(update, context)
    assert sent["photo"] == "FILE123"
    assert "Bleach TYBW" in sent["caption"]
    assert isinstance(sent["markup"], InlineKeyboardMarkup)


@pytest.mark.asyncio
async def test_poster_command_replaces_logo(group_chat, user, config, db):
    from animebot.handlers import admin

    anime_id = await db.add_anime("One Punch Man", "l", "hindi")
    config.admin_ids = frozenset({user.id})
    config.admin_ids = frozenset({user.id})
    context = FakeContext(db, config)
    logo = AdminMessage(group_chat, photos=[FakePhoto("new-logo", 900)])
    update, message = make_admin_update(group_chat, user, text=f"/poster {anime_id}", reply=logo)
    await admin.poster_command(update, context)
    assert (await db.get_anime(anime_id))["poster"] == "new-logo"


@pytest.mark.asyncio
async def test_add_keeps_existing_poster_when_link_updated(group_chat, user, config, db):
    from animebot.handlers import admin

    await db.add_anime("Frieren", "old-link", "hindi", poster="keep-me")
    config.admin_ids = frozenset({user.id})
    context = FakeContext(db, config)
    update, message = make_admin_update(
        group_chat, user, text="/add Frieren | https://t.me/+newlink | hindi"
    )
    await admin.add_command(update, context)
    row = (await db.search("Frieren", "hindi"))[0]
    assert row["link"] == "https://t.me/+newlink"
    assert row["poster"] == "keep-me"


# ------------------------------------------------- filter-bot card support
USER_CARD = (
    '/filter "the Case study of vanitas"[🍀Hindi dub🍀]'
    '(buttonurl:https://t.me/+l16u8HgUO3BmZThl)\n'
    '[🗞️Update](buttonurl:https://t.me/redlineanime)'
)


@pytest.mark.asyncio
async def test_filter_command_saves_the_filter_bot_card(group_chat, user, config, db):
    from animebot.handlers import admin

    await db.set_group("menu", "https://t.me/+MAIN")
    config.admin_ids = frozenset({user.id})
    context = FakeContext(db, config)
    update, message = make_admin_update(group_chat, user, text=USER_CARD)
    await admin.filter_command(update, context)

    assert "Card saved" in message.sent[-1]["text"]
    rows = await db.search("vanitas", "hindi")
    assert len(rows) == 1
    saved = await db.get_anime(rows[0]["id"])
    assert saved["title"] == "The Case study of vanitas"
    assert saved["language"] == "hindi"
    assert saved["link"] == "https://t.me/+l16u8HgUO3BmZThl"
    assert saved["extras"] == [["🗞️Update", "https://t.me/redlineanime"]]


@pytest.mark.asyncio
async def test_filter_command_still_creates_plain_genres(group_chat, user, config, db):
    from animebot.handlers import admin

    config.admin_ids = frozenset({user.id})
    context = FakeContext(db, config)
    update, message = make_admin_update(group_chat, user, text="/filter isekai 🌀 Isekai")
    await admin.filter_command(update, context)
    row = await db._fetchone("SELECT name FROM filters WHERE slug='isekai'")
    assert row["name"] == "🌀 Isekai"


@pytest.mark.asyncio
async def test_card_saved_by_save_also_keeps_update_button(group_chat, user, config, db):
    from animebot.handlers import admin
    from animebot.handlers import menu

    await db.set_group("menu", "https://t.me/+MAIN")
    config.admin_ids = frozenset({user.id})
    context = FakeContext(db, config)
    update, _ = make_admin_update(group_chat, user, text=USER_CARD.replace("/filter", "/save"))
    await admin.save_command(update, context)

    anime = (await db.search("vanitas", "hindi"))[0]
    card = await db.get_anime(anime["id"])
    update, _ = make_update(group_chat, user, callback=f"a:{anime['id']}:latest:hindi")
    await menu.on_anime(update, context)

    buttons = [
        button
        for row in context.bot.messages[-1]["reply_markup"].inline_keyboard
        for button in row
        if button.url
    ]
    by_url = {b.url: b.text for b in buttons}
    assert "https://t.me/+l16u8HgUO3BmZThl" in by_url
    assert any("Join" in text for text in by_url.values())
    assert by_url["https://t.me/redlineanime"] == "🗞️Update"


@pytest.mark.asyncio
async def test_card_without_image_posts_text_fallback(group_chat, user, config, db):
    from animebot.handlers import admin
    from animebot.handlers import menu

    await db.set_group("menu", "https://t.me/+MAIN")
    config.admin_ids = frozenset({user.id})
    context = FakeContext(db, config)
    update, _ = make_admin_update(group_chat, user, text=USER_CARD)
    await admin.filter_command(update, context)

    anime = (await db.search("vanitas", "hindi"))[0]
    update, _ = make_update(group_chat, user, callback=f"a:{anime['id']}:latest:hindi")
    await menu.on_anime(update, context)
    assert "Case study of vanitas" in context.bot.messages[-1]["text"]


# --------------------------------------------------------- backup / restore
@pytest.mark.asyncio
async def test_snapshot_roundtrip_keeps_everything(db):
    await db.upsert_filter("action", "Action")
    await db.add_anime("Bleach", "https://t.me/+b", "hindi", tags=["action"], poster="F1")
    await db.set_group("menu", "https://t.me/+main")
    await db.mark_joined(7, "action")
    raw = await db.snapshot()
    assert raw[:15] == b"SQLite format 3"
    assert raw[18] == 1  # portable DELETE journal, not WAL

    await db.add_anime("Temp", "", "english")
    await db.restore(raw)
    stats = await db.stats()
    assert stats == {"anime": 1, "groups": 1, "users": 1}
    anime = await db.get_anime(1)
    assert (anime["title"], anime["poster"], anime["link"]) == (
        "Bleach", "F1", "https://t.me/+b"
    )
    await db.add_anime("After", "", "hindi")  # still writable
    assert await db.count_anime() == 2


@pytest.mark.asyncio
async def test_backup_and_restore_commands(group_chat, user, config, db, tmp_path):
    from animebot.handlers import admin

    config.admin_ids = frozenset({user.id})
    await db.add_anime("Bleach", "https://t.me/+b", "hindi", poster="F1")
    context = FakeContext(db, config)

    sent = {}

    class DocMessage(FakeMessage):
        def __init__(self, chat, **kw):
            super().__init__(chat)
            self.kwargs = kw

        async def reply_document(self, document, filename="", caption="", **kw):
            sent.update(document=document, filename=filename, caption=caption)

    update = SimpleNamespace(
        callback_query=None, effective_message=DocMessage(group_chat),
        effective_chat=group_chat, effective_user=user,
    )
    await admin.backup_command(update, context)
    assert sent["filename"] == "animebot-backup.db"
    assert sent["document"][:15] == b"SQLite format 3"
    assert "1 anime" in sent["caption"].replace("<b>", "").replace("</b>", "")

    # wipe, then restore from that exact file
    backup = sent["document"]
    await db._exec("DELETE FROM anime")
    assert await db.count_anime() == 0

    class RestoreFile:
        def __init__(self, raw):
            self.raw = raw
            self.file_size = len(raw)
            self.file_id = "backup-file-id"

        async def download_as_bytearray(self):
            return bytearray(self.raw)

    class RestoreContext(FakeContext):
        def __init__(self, db, config, raw):
            super().__init__(db, config)
            self.bot.get_file = self._get_file
            self._raw = raw

        async def _get_file(self, file_id):
            raw = self._raw

            class F:
                async def download_as_bytearray(self_inner):
                    return bytearray(raw)

            return F()

    msg = AdminMessage(group_chat)
    msg.document = RestoreFile(backup)
    update = SimpleNamespace(
        callback_query=None, effective_message=msg,
        effective_chat=group_chat, effective_user=user,
    )
    await admin.restore_command(update, RestoreContext(db, config, backup))
    assert await db.count_anime() == 1
    assert "Restored" in msg.sent[-1]["text"]


# ------------------------------------------------------- free-host resilience
@pytest.mark.asyncio
async def test_auto_restore_refills_a_wiped_database(tmp_path):
    from animebot.boot import auto_restore_if_empty

    src = Database(str(tmp_path / "src.db"))
    await src.connect()
    await src.add_anime("Bleach", "https://t.me/+b", "hindi", poster="F1")
    backup = await src.snapshot()
    await src.close()

    wiped = Database(str(tmp_path / "wiped.db"))
    await wiped.connect()
    assert await wiped.count_anime() == 0

    class FakeFile:
        async def download_as_bytearray(self):
            return bytearray(backup)

    class FakeBot:
        async def get_file(self, file_id):
            assert file_id == "backup-id"
            return FakeFile()

    assert await auto_restore_if_empty(FakeBot(), wiped, "backup-id") is True
    assert await wiped.count_anime() == 1
    assert (await wiped.get_anime(1))["poster"] == "F1"

    # no id / not empty -> nothing happens
    assert await auto_restore_if_empty(FakeBot(), wiped, "") is False
    await wiped.close()


@pytest.mark.asyncio
async def test_auto_restore_survives_a_bad_file_id(tmp_path):
    from animebot.boot import auto_restore_if_empty

    db = Database(str(tmp_path / "x.db"))
    await db.connect()

    class BrokenBot:
        async def get_file(self, file_id):
            raise RuntimeError("bad file id")

    assert await auto_restore_if_empty(BrokenBot(), db, "oops") is False
    await db.close()
