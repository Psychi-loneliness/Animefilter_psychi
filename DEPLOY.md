# Deploying — free options only

The bot is a Python process that polls Telegram: no domain, no open ports, no
webhook required. If the host sets `PORT`, it also serves `GET /` and `/healthz`
so platform health checks pass.

| option | cost | always awake | data |
|---|---|---|---|
| **Android + Termux** (`MOBILE.md` Option A) | ₹0 | while phone is on | safe on phone |
| **Render free** | ₹0, no card | no (sleeps 15 min, 750 h/month) | ephemeral → `/backup` + `AUTO_RESTORE_FILE_ID` |
| **Own PC** (`pip install -r requirements.txt && python -m animebot`) | ₹0 | while PC is on | safe on disk |

Paid options (Railway trial credit, Fly, VPS) are documented in git history but
not required — everything below is free.

## Render free plan
`render.yaml` is already configured: `plan: free`, no disk, `DB_PATH=/tmp/animebot.db`,
`AUTO_RESTORE_FILE_ID` as an optional secret. New → Blueprint → pick repo →
paste `BOT_TOKEN`, `ADMIN_IDS` → Apply.

After adding titles: `/backup` → copy the file id the bot prints →
Environment → `AUTO_RESTORE_FILE_ID=<id>` → Save. Wipes now self-heal.

## Android / Termux
`termux-setup.sh` (install) and `termux-run.sh` (start + auto-restart loop with a
wake lock) are in the repo root. Termux:Boot + `termux-boot.sh` gives auto-start
after a reboot. Details in `MOBILE.md`.

## Any host with Docker (free tiers on some providers)
```bash
docker build -t animebot .
docker run -d --name animebot --restart unless-stopped \
  -e BOT_TOKEN=… -e ADMIN_IDS=… -e DB_PATH=/data/animebot.db \
  -v animebot-data:/data animebot
docker logs -f animebot
```
On hosts without volumes, set `AUTO_RESTORE_FILE_ID` instead of a volume.

## Keeping the library
`/backup` sends `animebot-backup.db` + the file id; `/restore` (as the file's
caption) puts it back. The snapshot is a plain SQLite file (DELETE journal mode),
so it also opens on a PC.

## Updating
- Termux: `cd ~/Animefilter_psychi && git pull && bash termux-run.sh`
- Render: dashboard → **Manual Deploy → Deploy latest commit**
- Docker: rebuild and restart the container
