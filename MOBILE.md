# 📱 Free setup from an Android phone

Everything here costs **₹0** and needs **no laptop, no credit card, no VPS**.

A bot is a program that must run 24/7, so a phone (or a free cloud host) has to
serve it. Two honest, free choices:

| | **A · Your own Android phone (Termux)** | **B · Render free plan** |
|---|---|---|
| Cost | ₹0 forever | ₹0 |
| Uptime | while the phone is on and online | sleeps after 15 min idle, wakes in ~30–60 s |
| Data safety | safe (it's your phone) | **disk wiped on restart** → use `/backup` + `AUTO_RESTORE_FILE_ID` |
| Needs | Android 7+, Termux from F-Droid | nothing but a browser |
| Extra | a spare/old phone is ideal | no credit card |

> Reality check on free cloud hosts (checked Nov 2026): Render free = 750 h/month,
> sleeps after 15 min, **no persistent disk**. Railway **is not free** (trial
> credit only). Koyeb's free tier now scales to zero. So "free + always awake"
> really means **Option A**.

---

## Step 0 · Bot token + your id (3 min, any phone)

1. **@BotFather** → `/newbot` → name it → username ending in `bot`
   (e.g. `galaxy_anime_bot`) → it prints a token `8123456789:AAH…`.
   **Long-press the token → Copy → paste into Saved Messages.**
2. **@userinfobot** → Start → it replies `Id: 123456789`. Save that number too.

---

## Option A · Run it on your own Android phone (free forever) ⭐ recommended

### A1. Install the two apps (from **F-Droid**, not the Play Store)

- **Termux** — https://f-droid.org/packages/com.termux/
- **Termux:Boot** — https://f-droid.org/packages/com.termux.boot/
  (lets the bot start again after a reboot)

### A2. One-line install

Open **Termux** and paste this single line, then Enter:

```bash
curl -sL https://raw.githubusercontent.com/Psychi-loneliness/Animefilter_psychi/arena/a2e62907-animefilter-psychi/termux-setup.sh | bash
```

It installs Python, downloads the bot, creates `.env`, opens an editor so you can
paste your **token** and **id**, and runs the self-check. Takes 3–5 minutes.
When you press Enter to open the editor: paste your values, save with `Ctrl+O`
`Enter`, exit with `Ctrl+X`.

**You should see** at the end:

```
✅ BOT_TOKEN looks like a token
✅ ADMIN_IDS: [123456789]
✅ database ready
✅ connected as @galaxy_anime_bot
```

### A3. Start it and keep it alive

```bash
bash ~/Animefilter_psychi/termux-run.sh
```

**You should see** `Running as @galaxy_anime_bot • 0 titles • auto menu on`.

Then (one time only):

1. **Settings → Apps → Termux → Battery → Unrestricted** (also for Termux:Boot).
2. Some phones (Xiaomi/Redmi, Realme, Oppo, Vivo) also need
   **Settings → Battery → App battery saver → Termux → No restrictions**.
3. Auto-start after reboot:
   ```bash
   mkdir -p ~/.termux/boot && cp ~/Animefilter_psychi/termux-boot.sh ~/.termux/boot/ && chmod +x ~/.termux/boot/termux-boot.sh
   ```

Keep the phone on a charger with Wi-Fi on — an old phone works perfectly.

### A4. Checking / controlling it

```bash
tail -f ~/animebot.log                 # live log (Ctrl+C to stop watching)
tmux attach -t animebot                # look inside the session (Ctrl+B then D to leave)
pkill -f "python -m animebot"          # stop the bot
bash ~/Animefilter_psychi/termux-run.sh # start/restart it
```

---

## Option B · Render free plan (browser only, sleeps when idle)

Use this if you have no spare Android phone. Two free-tier quirks you must accept:
the service sleeps after 15 minutes of silence (first message takes ~30–60 s)
and **the disk is wiped on restart** — the bot handles that with backups.

1. Phone browser → **render.com** → **Get Started with GitHub** → authorise.
2. **New → Blueprint** → choose `Psychi-loneliness/Animefilter_psychi`
   → branch `arena/a2e62907-animefilter-psychi` (reads `render.yaml`).
3. Paste `BOT_TOKEN` and `ADMIN_IDS` → **Apply** → wait for **Live**.
4. Logs should show `Running as @galaxy_anime_bot • 0 titles`.

### Saving your library on Render (important)

1. After you add a batch of anime, send **`/backup`** in the bot DM.
2. The bot replies with the file **and** a code under *“Free-host tip”*.
3. Long-press that code → **Copy** → Render dashboard → your service →
   **Environment** → add variable `AUTO_RESTORE_FILE_ID` = that code → Save.
4. Done: whenever Render wipes the disk, the bot restores itself on boot
   (log line: `library was empty — restored from AUTO_RESTORE_FILE_ID`).

> Free Render services also stop for the rest of the month once the 750 free
> hours are used — a 24/7 bot uses ~730 h/month, so keep the bot idle-ish or
> expect it to pause near month-end. Option A has no such limit.

---

## Step 1 · First contact in Telegram

Open your bot → **Start**.

**You should see** the 4-option menu:
**🔥 Latest Uploaded · 🎭 Genre · ⭐ Popular · 🔍 Search**.

Nothing? The program is not running: Termux `tail -f ~/animebot.log` (Option A)
or Render **Logs** (Option B).

---

## Step 2 · Add the bot to your anime group

1. Group → **group name** → **Add members** → search `@galaxy_anime_bot` → add.
2. **group name → Administrators → Add administrator** → pick the bot →
   **Invite Users** + **Delete Messages** → Save.
3. Send `/menu` in the group → the same 4-option menu appears.
   - Silent? @BotFather → `/setprivacy` → **Disable**, then remove and re-add the
     bot to the group.

---

## Step 3 · Save the join link (once)

In the group send:

```
/setgroup menu
```

**You should see** `✅ Group link saved for menu.` (the bot creates its own invite
link — that's why it needed *Invite Users*).

Different group per genre? One line each:

```
/setgroup action https://t.me/+ACTIONGROUP
/setgroup action:hindi https://t.me/+ACTIONHINDI
```

---

## Step 4 · Add your anime — your usual card

In the group or the bot DM:

```
/filter "the Case study of vanitas"[🍀Hindi dub🍀](buttonurl:https://t.me/+l16u8HgUO3BmZThl)
[🗞️Update](buttonurl:https://t.me/redlineanime)
```

**You should see**

```
✅ Card saved as #1
🎬 The Case study of vanitas
🗣 language: hindi
🔗 join link: https://t.me/+l16u8HgUO3BmZThl
```

### With the logo

1. Send the poster image to the bot/group (from Google Images or your gallery).
2. **Long-press the image → Reply**.
3. Type the same card with **`/save`** instead of `/filter` → send.

Wrong image later? Long-press the right one → Reply → `/poster 1`.

### Genre buttons (once)

```
/filter action Action & Adventure
/filter romance Romance
/filter isekai Isekai
```

Tag an anime with a genre by putting the word in the label:
`/save "Jujutsu Kaisen"[🔥Action🍀Hindi dub🔥](buttonurl:https://t.me/+jjk)`

> Phone trick: keep all your cards in a private channel or Saved Messages, then
> long-press → Copy → paste → change the title. Much faster than typing.

---

## Step 5 · Test like a member

Second account (or a friend who is only a member):

1. Chat in the group → `[ 🎬 Anime menu ]` appears (once per 3 min).
2. Tap → 4 options → **🔍 Search** → **🇮🇳 Hindi** → type `vanitas`.
3. Tap the result → group gets the card with **🚀 Join & watch** + **🗞️Update**.

---

## Step 6 · Free safety net

```
/backup     → bot sends animebot-backup.db  (long-press → Save to Saved Messages)
/restore    → send that file with the caption /restore  (or Reply → /restore)
```

Needed on Render; nice peace-of-mind on your phone (e.g. before changing phones —
copy the file to Google Drive, install Termux on the new phone, `/restore`).

---

## Free-host troubleshooting

| what you see | meaning | fix |
|---|---|---|
| Termux bot dies when screen locks | battery optimisation | `termux-wake-lock` (the run script does it) + Unrestricted battery |
| `Conflict: terminated by other getUpdates` | two copies running | `pkill -f "python -m animebot"`, start once |
| Render: first message takes a minute | sleeping free service | normal on free tier |
| Render: library empty after redeploy | disk wiped | `/restore` or set `AUTO_RESTORE_FILE_ID` |
| `⛔ Admins only` | id missing | fix `ADMIN_IDS` in `.env`/Render env, restart |
| `/menu` silent in group | privacy mode | BotFather `/setprivacy` → Disable, re-add bot |
| No join button | no group link | `/setgroup menu` in the group |
| Title not in Hindi search | saved without Hindi | re-send card with `[🍀Hindi dub🍀]` |
| Xiaomi/Realme kills Termux | OEM task killer | lock Termux in recents + battery: No restrictions |
