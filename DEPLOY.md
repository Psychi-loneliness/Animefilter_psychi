# Deploy & operate (no laptop needed)

Pick one host, set two variables (`BOT_TOKEN`, `ADMIN_IDS`), deploy. The bot polls
Telegram — no domain, no port forwarding, no webhook. If the host provides `PORT`,
the bot also opens a tiny `GET /` health page so the platform sees it healthy.

## Railway
1. New Project → Deploy from GitHub repo → branch `arena/a2e62907-animefilter-psychi`
2. Variables: `BOT_TOKEN`, `ADMIN_IDS`, `BRAND`, `DB_PATH=/data/animebot.db`
3. Settings → Volumes → mount `/data` (1 GB)
4. Deploy → Logs should show `Running as @yourbot`

`railway.json` is included (start command + restart policy).

## Render
1. New → Blueprint → pick the repo (uses `render.yaml`)
2. Paste `BOT_TOKEN`, `ADMIN_IDS` → Apply
3. The blueprint already mounts a 1 GB disk at `…/data` and sets `DB_PATH`
4. Free plan sleeps after 15 min idle; first message then takes ~30 s

## Fly.io
```bash
fly launch --copy-config --no-deploy      # Dockerfile is included
fly volumes create botdata --size 1
fly secrets set BOT_TOKEN=… ADMIN_IDS=…
fly deploy
```
Mount the volume at `/data` and set `DB_PATH=/data/animebot.db`.

## Docker (any VPS)
```bash
docker build -t animebot .
docker run -d --name animebot --restart unless-stopped \
  -e BOT_TOKEN=… -e ADMIN_IDS=… -e DB_PATH=/data/animebot.db \
  -v animebot-data:/data animebot
docker logs -f animebot
```

## systemd (plain VPS)
See `SETUP.md` Step 15, or paste the block from `MOBILE.md` Option C.

## Keeping the library
`/backup` sends `animebot-backup.db` in Telegram; `/restore` (as the file's
caption) puts it back after a redeploy. The snapshot is written in plain SQLite
journal mode so it works on any host and is the same file you could open on a
PC.

## Updating the bot
- Railway/Render: push to the branch (or hit **Redeploy**) — the volume keeps data.
- VPS: `cd Animefilter_psychi && git pull && systemctl restart animebot`.
