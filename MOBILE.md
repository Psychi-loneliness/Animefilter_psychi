# 📱 Setup from an Android / iPhone only

No laptop needed. You will do everything in your phone browser and inside
Telegram. Time: ~15 minutes.

**The one rule:** the bot is a program that must run somewhere 24 hours a day.
A phone cannot be that place (Android/iOS kill background apps). So we put the
program on a free/cheap host and **you manage it from Telegram** — adding anime,
genres, links and backups are all chat commands.

```
your phone ──Telegram──► bot (@yourbot)          you type /filter, /save, /setgroup
                            │
                            ▼
                    host (Railway / Render / VPS) ← the program actually runs here
                            │
                            ▼
                    your anime group  ← members tap the menu
```

---

## Step 0 · Get your Telegram id (1 min)

1. In Telegram search **@userinfobot** → press **Start**.
2. It replies `Id: 123456789`. **Write this number down.**

---

## Step 1 · Create the bot (2 min)

1. Search **@BotFather** → **Start**.
2. Send `/newbot` → give it a name → give it a username ending in `bot`
   (e.g. `galaxy_anime_filters_bot`).
3. BotFather replies with a **token** like `8123456789:AAH…`.
4. **Long-press the token → Copy.** Send it to yourself in *Saved Messages* so you
   can paste it later — long-press again to copy from there.

> Never post the token in the group. Anyone with it controls your bot.

---

## Step 2 · Put the code on a host — pick ONE

### Option A · Railway (easiest, ~$5 free trial, no card for the trial)

1. Phone browser → **railway.app** → **Login with GitHub**.
2. **New Project → Deploy from GitHub repo** → choose
   `Psychi-loneliness/Animefilter_psychi`
   → in **Branch** pick `arena/a2e62907-animefilter-psychi`.
3. Open the service → **Variables** → add:

   | name | value |
   |---|---|
   | `BOT_TOKEN` | your token from Step 1 |
   | `ADMIN_IDS` | your id from Step 0 |
   | `BRAND` | `Anime Galaxy` (or your group name) |
   | `DB_PATH` | `/data/animebot.db` |

4. **Settings → Volumes** → *Add volume*, mount path **`/data`**, size 1 GB.
   (Without the volume your library is wiped on redeploys — see Step 6 backups.)
5. **Deploy**. Open **Logs** → you should read
   `Running as @galaxy_anime_filters_bot • 0 titles • auto menu on`.

### Option B · Render (free tier, sleeps after 15 min idle)

1. Phone browser → **render.com** → **Get Started with GitHub**.
2. **New → Blueprint** → pick the repo → it reads `render.yaml` automatically.
3. Paste `BOT_TOKEN` and `ADMIN_IDS` when asked → **Apply**.
4. Wait for `Live`. Logs should show the same `Running as @…` line.

> Free Render sleeps when idle: the first message after a pause takes ~30 s. If
> that annoys you, Railway or a small VPS is smoother.

### Option C · Cheap VPS (most reliable, ~₹200–350/month)

Buy any 1 GB VPS (Hetzner, Contabo, DigitalOcean…). On the **provider's own web
console** (a terminal in the browser — no laptop needed):

```bash
apt update && apt install -y git python3 python3-venv
git clone https://github.com/Psychi-loneliness/Animefilter_psychi.git
cd Animefilter_psychi && git checkout arena/a2e62907-animefilter-psychi
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env
nano .env          # paste BOT_TOKEN and ADMIN_IDS, save: Ctrl+O ⏎ then Ctrl+X
.venv/bin/python -m scripts.doctor     # all ✅ ?
.venv/bin/python -m animebot &         # quick test, then stop with: kill %1
```

Then keep it alive forever (copy-paste the whole block):

```bash
cat > /etc/systemd/system/animebot.service <<'EOF'
[Unit]
Description=Anime filter bot
After=network.target

[Service]
WorkingDirectory=/root/Animefilter_psychi
EnvironmentFile=/root/Animefilter_psychi/.env
ExecStart=/root/Animefilter_psychi/.venv/bin/python -m animebot
Restart=always

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload && systemctl enable --now animebot
systemctl status animebot        # should say: active (running)
```

**Already have a laptop/PC and want to try it free first?** Run both starter
files on it (`pip install -r requirements.txt`, then `python -m animebot`), but it
must stay on and online; your phone is just the keyboard.

---

## Step 3 · Verify it works (inside Telegram)

1. Open your bot's chat → **Start**.
2. You should get the 4-option menu:
   **🔥 Latest Uploaded · 🎭 Genre · ⭐ Popular · 🔍 Search**.

If nothing arrives: the host is not running — open its **Logs** and look for the
`Running as @…` line, or `Conflict: terminated by other getUpdates` (means two
copies run; stop one).

---

## Step 4 · Add the bot to your group (on the phone)

1. Open your anime group → **group name** at the top → **Add members** →
   search `@galaxy_anime_filters_bot` → add.
2. **group name → Administrators → Add administrator** → choose the bot →
   enable **Invite Users** and **Delete Messages** → Save.
3. In the group send `/menu` → the 4-option menu must appear.
   - Nothing happened? In @BotFather send `/setprivacy` → **Disable** →
     then remove and re-add the bot to the group.

---

## Step 5 · Save the group link (once)

In the group, send:

```
/setgroup menu
```

You get `✅ Group link saved for menu.` The bot creates its own invite link — so
make sure it is admin with *Invite Users* (previous step).

Different group per genre? Send one line per genre:

```
/setgroup action https://t.me/+ACTIONGROUP
/setgroup action:hindi https://t.me/+ACTIONHINDI
```

---

## Step 6 · Add your anime — exactly like your filter bot

In the group (or the bot DM) send your normal card:

```
/filter "the Case study of vanitas"[🍀Hindi dub🍀](buttonurl:https://t.me/+l16u8HgUO3BmZThl)
[🗞️Update](buttonurl:https://t.me/redlineanime)
```

Reply:

```
✅ Card saved as #1
🎬 The Case study of vanitas
🗣 language: hindi
🔗 join link: https://t.me/+l16u8HgUO3BmZThl
```

### With the logo (nicer card) — works from phone photos

1. Open Telegram's **gallery/Google Images** → share/send the anime poster **to the
   group or the bot**.
2. **Long-press that image → Reply**.
3. Type the same card but with **`/save`** instead of `/filter`, then send.

The reply attaches the picture to the entry. Missed it? Send the image, long-press
→ reply → `/poster 1`.

**Genre buttons** — create them once:

```
/filter action Action & Adventure
/filter romance Romance
/filter isekai Isekai
```

To tag an anime with a genre, put the word in the label:
`/save "Jujutsu Kaisen"[🔥Action🍀Hindi dub🔥](buttonurl:https://t.me/+jjk)`

> Two-finger trick for long lines: type in **Notes/Keep** first, then copy-paste
> into Telegram. Emoji like 🍀🔥🗞️ can be found in the keyboard's emoji panel.

---

## Step 7 · Test as a member

Use a second account (or ask a friend who is only a member):

1. Chat in the group → a `[ 🎬 Anime menu ]` button appears (once per 3 min).
2. Tap → 4 options → **🔍 Search** → **🇮🇳 Hindi** → type `vanitas`.
3. Tap the result → the group gets the card with
   **🚀 Join & watch** and **🗞️Update** buttons.

---

## Step 8 · Keep your library safe (important on free hosts)

Free hosts can wipe the disk on redeploy. Your whole library lives in one file, so
**get a copy in Telegram whenever you add a batch of titles:**

```
/backup
```

The bot sends `animebot-backup.db`. **Long-press → Save to Saved Messages.**
After a redeploy, restore it:

```
send the backup file with the caption:  /restore
```
(or long-press the file → Reply → type `/restore`)

You should see `✅ Restored — 42 anime · 3 links`.

---

## Step 9 · Handy commands from the phone

| command | when you need it |
|---|---|
| `/menu` | show the 4-option menu |
| `/filter "Title"[🍀Hindi dub🍀](buttonurl:link)` | add/replace a title |
| `/save …` (reply to a poster) | add a title with its logo |
| `/poster 12` (reply to image) | change the logo of #12 |
| `/filters` | see all genres and counts |
| `/find vanitas` | find the id of a title |
| `/quick 12 95` | push #12 up in ⭐ Popular |
| `/del 12` | remove a title |
| `/setgroup menu` | re-save the join link |
| `/automenu on` · `/cooldown 60` | control the “tap the menu” nudge |
| `/stats` · `/backup` · `/restore` | health and safety |

---

## Troubleshooting (phone edition)

| what you see | what it means | fix |
|---|---|---|
| Bot silent, no menu | program not running | host → Logs; look for `Running as @…` |
| `Conflict: terminated by other getUpdates` | two copies running | stop one (delete second service / old PC run) |
| `/menu` silent in the group | bot not admin + privacy on | make it admin, or BotFather `/setprivacy` → Disable |
| `⛔ Admins only` | your id missing | add `ADMIN_IDS` in the host Variables, restart |
| `No group link saved` | `/setgroup` not run | send `/setgroup menu` in the group |
| Title missing in Hindi search | saved as English/any | re-send the card with `[🍀Hindi dub🍀]` |
| Library empty after redeploy | disk was wiped | send your backup with `/restore` |
| Buttons open a dead link | t.me link expired | edit it: re-send the card with the new link |
| First message slow (free Render) | service was asleep | wait ~30 s, or use Railway/VPS |
