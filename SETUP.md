# 🚀 Setup from zero — every step

Follow in order. Each step says **do this** and **you should see**. If a step
fails, the fix is right there. Total time: about 15 minutes.

---

## Step 0 · What you need

- Your anime **group** where the bot will post (you must be its admin).
- Your **filter bot links** (the `https://t.me/+…` join links you already hand out).
- A computer that stays on (or a cheap VPS). A phone alone is not enough to host
  the bot for 24 hours.

---

## Step 1 · Create the bot on Telegram

**Do this**

1. Open [@BotFather](https://t.me/BotFather) → send `/newbot`.
2. Name it (e.g. `Anime Galaxy Bot`), then pick a username ending in `bot`
   (e.g. `animegalaxy_filters_bot`).
3. Copy the token it prints — looks like `8123456789:AAH…`.

**You should see**: `Done! Congratulations on your new bot.` + a token line.

**If not**: the username is taken — pick another ending in `bot`.

---

## Step 2 · Get your numeric id

**Do this**: message [@userinfobot](https://t.me/userinfobot) → it replies with `Id: 123456789`.

**You should see**: your id number. Keep it; it goes in `ADMIN_IDS`.

---

## Step 3 · Put the code on your machine

```bash
git clone https://github.com/Psychi-loneliness/Animefilter_psychi.git
cd Animefilter_psychi
git checkout arena/a2e62907-animefilter-psychi
```

**You should see** a folder with `animebot/`, `requirements.txt`, `README.md`.

> On a VPS: install git/python first — `sudo apt update && sudo apt install -y git python3 python3-venv python3-pip`.

---

## Step 4 · Create the Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**You should see**: `Successfully installed python-telegram-bot-22.8 … aiogram…` (a few packages).

**If `python3 -m venv` fails**: `sudo apt install -y python3-venv`.

---

## Step 5 · Fill in `.env`

```bash
cp .env.example .env
nano .env        # or: open it in any editor
```

Edit these two lines (leave the rest):

```env
BOT_TOKEN=8123456789:AAH…your token…
ADMIN_IDS=123456789
```

**You should see**: your real token and id, **no quotes, no spaces** around them.

**If the bot later says "BOT_TOKEN is missing"**: you saved `.env.txt`, or the file
is in the wrong folder — it must sit next to `README.md`.

---

## Step 6 · Check the setup

```bash
python -m scripts.doctor
```

**You should see** something like

```
── 1. token ──          ✅ BOT_TOKEN looks like a token
── 2. admins ──         ✅ ADMIN_IDS: [123456789]
── 3. database ──       ✅ database ready
── 4. telegram ──       ✅ connected as @animegalaxy_filters_bot
```

`❌ 0 anime saved` / `❌ 0 group link(s)` are **normal at this point** — you fill
those in Steps 10 and 11.

---

## Step 7 · Start the bot

```bash
python -m animebot
```

**You should see**:

```
Running as @animegalaxy_filters_bot • 0 titles • auto menu on
```

Leave this terminal open. `Ctrl+C` stops the bot.

**If you see `Conflict: terminated by other getUpdates request`**: the bot is
already running somewhere else (another terminal/PC) — stop that one.

---

## Step 8 · First contact (DM)

**Do this**: open your bot's chat → press **Start** → send `/start`.

**You should see**: the menu card with **🔥 Latest Uploaded / 🎭 Genre / ⭐ Popular / 🔍 Search**.

**If nothing happens**: the bot is not running (Step 7) or the token is wrong (Step 6).

---

## Step 9 · Put the bot in your group

**Do this**

1. Group → **Add members** → search your bot username → add.
2. Group → **Administrators** → add the bot → give it **Invite users** (needed for
   `/setgroup` without a link) and **Delete messages** (so it can clean up the
   chooser message).
3. In the group send `/menu`.

**You should see**: the same 4-option menu inside the group.

**If `/menu` does nothing**: the bot was added but not as admin and privacy mode is
on. Either make it admin, or in BotFather run `/setprivacy` → **Disable** (then
remove + re-add the bot to the group).

---

## Step 10 · Save the group link (the important one)

**Do this**: inside the group, send

```
/setgroup menu
```

…or, if you prefer to paste the link yourself:

```
/setgroup menu https://t.me/+YOURGROUPINVITE
```

**You should see**: `✅ Group link saved for menu.`

Repeat per genre only if a genre has its own different group:

```
/setgroup action https://t.me/+ACTIONGROUP
/setgroup action:hindi https://t.me/+ACTIONHINDI
```

**If it says "I couldn't create an invite link"**: make the bot admin with
**Invite users**, or paste the link as above.

---

## Step 11 · Add your first anime (exactly like your filter bot)

**Do this** — send this in the group (or in the bot DM):

```
/filter "the Case study of vanitas"[🍀Hindi dub🍀](buttonurl:https://t.me/+l16u8HgUO3BmZThl)
[🗞️Update](buttonurl:https://t.me/redlineanime)
```

**You should see**:

```
✅ Card saved as #1

🎬 The Case study of vanitas
🗣 language: hindi
🔗 join link: https://t.me/+l16u8HgUO3BmZThl

extra buttons on the card:
• 🗞️Update → https://t.me/redlineanime
```

**To add the logo too** (recommended for a nicer card):

1. Send the anime poster image.
2. **Reply to that image** with the same card but `/save` instead of `/filter`.

**You should see**: `✅ Saved #1 · 🖼 logo attached …`

**If it says "⛔ Admins only"**: your id is not in `ADMIN_IDS` (Step 5, then restart
the bot) — or you are not an admin of that group.

**If it says "I could not read a title"**: the title must be the first thing after
`/filter`, in quotes or plain, before the first `[`.

---

## Step 12 · Create genre buttons

**Do this**:

```
/filter action Action & Adventure
/filter romance Romance
/filter isekai Isekai
```

**You should see**: `✅ Filter Action & Adventure is live with slug action.`

Then attach anime to them by putting the genre word in the card label:

```
/save "Jujutsu Kaisen"[🔥Action🍀Hindi dub🔥](buttonurl:https://t.me/+jjk)
```

A genre word in the `[label]` tags the title automatically.

---

## Step 13 · Test the member flow

**Do this** (best with a second account that is just a group member):

1. Send any message in the group → **a small `[ 🎬 Anime menu ]` button appears**
   (once per 3 minutes per chat).
2. Tap it → **4 options**.
3. Tap **🔍 Search** → **🇮🇳 Hindi / 🇬🇧 English**.
4. Tap **🇮🇳 Hindi** → type `vanitas`.
5. Tap the result **1. The Case study of vanitas 🇮🇳**.

**You should see**: the chooser message disappears, then in the group

```
🎬 The Case study of vanitas
🗣 🇮🇳 Hindi

[ 🚀 Join & watch The Case study of vanit… ]
[ 🗞️Update ]
```

Tapping the join button opens your group link.

**If the button does not appear on chatter**: it is on cooldown — wait 3 minutes,
or run `/automenu on` and `/cooldown 60` to shorten it.
**If no results in Hindi search**: the title is saved with a different language —
re-save it with `[🍀Hindi dub🍀]` in the label.

---

## Step 14 · Optional polish

```
/posthere              (in the group)  → menu taps from DMs also post the card in the group
/filters               → see all genres with counts
/find vanitas          → get the id of a title
/quick 1 95            → push a title up in ⭐ Popular
/poster 1              (reply to an image) → change the logo of #1
/broadcast New episode out now!   → DM everyone who pressed 🔔 Send me new episodes
```

Also nice — BotFather → `/setcommands` → paste:

```
menu - Anime filter menu
latest - Latest uploaded
popular - Popular now
genre - Browse by genre
search - Search in Hindi or English
link - Our group links
help - How to use
```

---

## Step 15 · Keep it running 24/7

The bot only works while `python -m animebot` runs. On a VPS:

```bash
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

sudo systemctl daemon-reload
sudo systemctl enable --now animebot
sudo systemctl status animebot        # should say: active (running)
journalctl -u animebot -f             # live logs
```

**You should see** `active (running)` and the `Running as @…` line in the logs.

Quick alternative without systemd: `tmux new -s bot 'cd /opt/Animefilter_psychi && source .venv/bin/activate && python -m animebot'`.

---

## Step 16 · Back up your library

Everything lives in one file: `animebot.db`.

```bash
cp animebot.db backups/animebot-$(date +%F).db
```

Restore = put the file back and restart. Photos are stored as Telegram file ids,
so the database stays tiny (a few hundred KB).

---

## Troubleshooting cheat sheet

| symptom | cause | fix |
|---|---|---|
| `BOT_TOKEN is missing` | `.env` not next to `README.md`, or wrong name | `cp .env.example .env`, edit, restart |
| `Conflict: terminated by other getUpdates request` | two copies running | stop the other one |
| `/menu` silent in group | bot not admin + privacy on | make admin, or `/setprivacy` → Disable, re-add |
| `⛔ Admins only` | id not in `ADMIN_IDS` | add it, restart the bot |
| No join button / `No group link saved` | `/setgroup` not run | `/setgroup menu` in the group |
| Title missing from Hindi search | saved as English/any | re-save with `[🍀Hindi dub🍀]` in the label |
| Menu nudge never appears | cooldown / off | `/automenu on`, `/cooldown 60` |
| Nothing at all happens | bot process died | `python -m scripts.doctor`, then restart |
```
