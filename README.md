# 🎬 Anime Filter Bot for Telegram

An inline-menu bot for anime Telegram groups. Members tap a button when they want
something to watch; the bot posts the anime name (with its logo) **in the group**
together with the join link saved by your filter bot.

```
someone chats in the group
        ↓
   [ 🎬 Anime menu ]           ← optional, cooldown-protected nudge
        ↓
┌──────────────────────────────┐
│ 🔥 Latest Uploaded           │
│ 🎭 Genre      ⭐ Popular      │
│ 🔍 Search                    │
└──────────────────────────────┘
        ↓  🔍 Search
┌──────────────────────────────┐
│ 🇮🇳 Hindi        🇬🇧 English   │
└──────────────────────────────┘
        ↓
  member types "demon"
        ↓
  ┌ 1. Demon Slayer 🇮🇳 ┐      ← tap a title
        ↓
  🖼 logo + "Demon Slayer / 🇮🇳 Hindi / #action"
     [ 🚀 Join & watch Demon Slayer ]  ← your filter bot group link
```

Everything is stored in one SQLite file, so you can add titles from your phone in
seconds — including the **logo image**.

**New here?** [`SETUP.md`](SETUP.md) is a click-by-click walkthrough (BotFather →
running → first anime → 24/7 hosting). The short version is below.

---

## 1. Create the bot

1. Open [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token.
2. `cp .env.example .env` and paste the token into `BOT_TOKEN`.
3. Put your numeric Telegram id in `ADMIN_IDS` (get it from [@userinfobot](https://t.me/userinfobot)).
4. Install & run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m scripts.seed_demo    # optional: demo titles + genres
python -m animebot             # start the bot (long polling)
```

5. In BotFather → `/setcommands` (optional, nice for users):

```
menu - Anime filter menu
latest - Latest uploaded
popular - Popular now
genre - Browse by genre
search - Search in Hindi or English
link - Our group links
help - How to use
```

6. **Groups:** add the bot to your anime group. For the auto-menu nudge and
   invite links, make it an admin with *invite users* permission.

---

## 2. Save anime — your filter-bot card works as-is

Paste the same line you already write for your filter bot:

```
/filter "the Case study of vanitas"[🍀Hindi dub🍀](buttonurl:https://t.me/+l16u8HgUO3BmZThl)
[🗞️Update](buttonurl:https://t.me/redlineanime)
```

The bot reads it like a human does:

| part of your line | what the bot stores |
|---|---|
| `"the Case study of vanitas"` | title (quotes optional) |
| `[🍀Hindi dub🍀]` | language → `hindi` (searched under 🇮🇳 Hindi) |
| first `(buttonurl:…)` | the join link used by the “🚀 Join & watch” button |
| extra `[🗞️Update](buttonurl:…)` | an extra button kept on the card |
| genre words in a label, e.g. `[🔥Action🍀Hindi dub🔥]` | genre tags |

So the posted card looks like this in the group:

```
🖼 <logo if you attached one>
🎬 The Case study of vanitas
🗣 🇮🇳 Hindi

[ 🚀 Join & watch The Case study of vanit… ]
[ 🗞️Update ]
```

Notes:

* `/filter` with a card **saves the anime**; `/filter action Action & Adventure`
  (no brackets) still just creates a genre button — both behaviours coexist.
* `/save` is identical to the card form **plus** it accepts the logo: send the
  image, reply to it with the card, done. You can also caption the image itself.
* `the Case…` gets its first letter capitalised; quotes, emoji and the
  `buttonurl:` prefix are stripped.
* Two dub buttons (e.g. Hindi + English) mark the title as multi-audio so it
  appears in both searches.
* Re-sending the same card updates the entry in place and keeps its logo.

```
/save "Demon Slayer"[🍀Hindi dub🍀](buttonurl:https://t.me/+abc)   ← reply to the logo
/filter "Solo Leveling" [🌀Isekai, Action🌀](buttonurl:https://t.me/+solo)
/save Demon Slayer | hindi | action,shonen | 95                    ← plain format too
```

Other admin commands:

| command | what it does |
|---|---|
| `/poster 12` | reply to an image → attach / replace the logo of #12 |
| `/find demon` | list ids of matching titles |
| `/del 12` | delete a title |
| `/quick 12 95` | set popularity |
| `/filters` `/unfilter action` | list / delete genre buttons |
| `/setgroup menu https://t.me/+xxxx` | default link (used when a card has no link) |
| `/setgroup action:hindi https://t.me/+yyyy` | link for a filter + language |
| `/groups` `/ungroup action` | list / delete saved links |
| `/posthere` | in a group: DM menus also post their cards here |
| `/automenu on\|off` `/cooldown 120` | control the nudge |
| `/stats` `/broadcast text` | counters / message subscribers |

### Which link is used for the join button?

```
link written in the card   →   <filter>:<language>   →   <filter>   →   menu (default)
```

The card’s own `buttonurl` always wins; otherwise the filter-specific link, then
the default `menu` link. If none exist the bot tells you to run `/setgroup`.

## 3. How members use it

* Every `/menu` (or the auto nudge) opens the 4 options: **Latest / Genre /
  Popular / Search**, and Search is split into **🇮🇳 Hindi** and **🇬🇧 English**.
* After the language is picked, the member just types the name — the bot replies
  with matching titles (one search per tap, no sticky mode; `/cancel` stops it).
* Tapping a title deletes the chooser and posts the card **in the group** with the
  join button, so the whole group sees what was requested.
* 🔔 *Send me new episodes* stores the member so `/broadcast` (or a new title
  tagged with their genre) can reach them in DM.

---

## 4. Configuration

| `.env` key | default | meaning |
|---|---|---|
| `BOT_TOKEN` | — | BotFather token (**required**) |
| `ADMIN_IDS` | — | comma separated admin user ids |
| `DB_PATH` | `animebot.db` | SQLite file |
| `BRAND` | `Anime Galaxy` | name shown in the menu |
| `AUTO_MENU` | `true` | show the "tap the menu" button when people chat |
| `AUTO_MENU_COOLDOWN` | `180` | seconds between two nudges per chat |
| `SEARCH_TIMEOUT` | `180` | how long a search waits for the typed name |
| `PAGE_SIZE` | `8` | titles per page |

Group admins are automatically treated as bot admins (with a 5-minute cache), so
the group owner does not need to edit `.env`.

---

## 5. Run it 24/7

```bash
# simple
tmux new -s animebot 'python -m animebot'

# systemd (recommended)
sudo tee /etc/systemd/system/animebot.service >/dev/null <<'EOF'
[Unit]
Description=Anime filter Telegram bot
After=network.target

[Service]
WorkingDirectory=/opt/Animefilter_psychi
EnvironmentFile=/opt/Animefilter_psychi/.env
ExecStart=/opt/Animefilter_psychi/.venv/bin/python -m animebot
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable --now animebot
```

A `Procfile` (`worker: python -m animebot`) is included for Railway/Render-style
hosts. Keep the SQLite file on a persistent volume, or set `DB_PATH` to one.

---

## 6. Develop

```bash
pip install -r requirements.txt pytest pytest-asyncio
python -m pytest -q                 # 42 tests, no network / token needed
python -m scripts.preview_menu      # print every screen as text
python -m scripts.doctor            # check .env, database and token
```

Layout:

```
animebot/
  __main__.py     entry point, Application wiring (long polling)
  config.py       .env → Config
  db.py           SQLite: anime, posters, filters, group links, subscribers
  card.py         filter-bot card parser  ["title"[label](buttonurl:…)]
  ui.py           all copy + inline keyboards (rebrand/translate here)
  handlers/
    menu.py       auto menu, 4 options, search, join posting
    admin.py      /save /poster /add /setgroup /filter /broadcast …
tests/            DB + end-to-end flow tests
scripts/          seed demo data, offline screen preview
```

### Notes

* Posters are stored as Telegram `file_id`s — instant to send, nothing to upload.
* Duplicate title + language updates the existing row and keeps its logo/link,
  so you can fix a typo or add a poster later without losing data.
* The auto menu fires at most once per `AUTO_MENU_COOLDOWN` per chat, so it never
  becomes spam.
