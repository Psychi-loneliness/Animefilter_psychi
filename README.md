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

## 2. Save anime (name + logo) — the important part

You have two ways; both accept the same extras:

**A. Reply to an image (recommended)**

```
1. send the anime logo/poster in the chat
2. reply to that image with:
   /save Demon Slayer
   /save Demon Slayer | hindi | action,shonen | 95
```

**B. Caption the image**

```
send the image with caption:
/save Solo Leveling | hindi | isekai | 90
```

Extras are recognised **in any order**, so you can skip the link:

| you type | meaning |
|---|---|
| `https://t.me/+abc` | group / filter bot link for this title |
| `hindi`, `en`, `eng`, `multi` | audio language (default `any`) |
| `action,shonen` | genres (creates the genre button if new) |
| `95` | popularity → shows higher under ⭐ Popular |
| `lang=hindi`, `tags=action,fantasy`, `pop=95` | explicit form |

Other admin commands:

| command | what it does |
|---|---|
| `/poster 12` | reply to an image → attach / replace the logo of #12 |
| `/find demon` | list ids of matching titles |
| `/del 12` | delete a title |
| `/quick 12 95` | set popularity |
| `/add Title \| link \| hindi \| action \| 90` | add without a logo |
| `/filter isekai 🌀 Isekai` | create a genre/filter button |
| `/filters` `/unfilter isekai` | list / delete filters |
| `/setgroup menu https://t.me/+xxxx` | default join link (used by any filter) |
| `/setgroup action:hindi https://t.me/+yyyy` | dedicated link for a filter + language |
| `/groups` `/ungroup action` | list / delete saved links |
| `/posthere` | in a group: DM menus also post their cards here |
| `/automenu on\|off` `/cooldown 120` | control the nudge |
| `/stats` `/broadcast text` | counters / message subscribers |

### Which group link is used?

When a member taps a title, the bot looks for the most specific link first:

```
<filter>:<language>   →   <filter>   →   <filter>   →   menu (default)
```

Example: tapping a title found under **🎭 Action** while the user searched in
**Hindi** uses `action:hindi` if you saved one, otherwise `action`, otherwise the
default `menu` link. Because a poster-only entry has no link of its own, the saved
group link is what makes the "Join & watch" button work.

---

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
python -m pytest -q                 # 34 tests, no network / token needed
python -m scripts.preview_menu      # print every screen as text
```

Layout:

```
animebot/
  __main__.py     entry point, Application wiring (long polling)
  config.py       .env → Config
  db.py           SQLite: anime, posters, filters, group links, subscribers
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
