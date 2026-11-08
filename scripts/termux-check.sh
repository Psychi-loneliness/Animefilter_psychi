#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# "It is not working" — run this and forward the output.
#
#   bash ~/Animefilter_psychi/scripts/termux-check.sh
#
# It only reads things; it never changes your setup.
# ─────────────────────────────────────────────────────────────────────────────
DIR="$HOME/Animefilter_psychi"
LOG="$HOME/animebot.log"
SESSION="animebot"

hr() { printf '%.0s─' {1..64}; echo; }

hr; echo "1 · where am I"; hr
echo "repo:   $DIR $([ -d "$DIR/.git" ] && echo '(git ✓)' || echo '(MISSING — run the installer)')"
echo "branch: $(git -C "$DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
echo "commit: $(git -C "$DIR" log -1 --format='%h %s' 2>/dev/null || echo '?')"

hr; echo "2 · python + packages"; hr
cd "$DIR" 2>/dev/null || { echo "no repo → stop here"; exit 1; }
PY="python"
[ -x .venv/bin/python ] && PY=".venv/bin/python"
echo "interpreter: $PY → $($PY -V 2>&1)"
$PY - <<'PY'
import importlib, sys
for mod, label in (("telegram", "python-telegram-bot"), ("aiosqlite", "aiosqlite"),
                   ("dotenv", "python-dotenv"), ("httpx", "httpx")):
    try:
        m = importlib.import_module(mod)
        print(f"  ✓ {label} {getattr(m, '__version__', '')}")
    except Exception as exc:  # noqa: BLE001
        print(f"  ✗ {label} MISSING ({exc})")
PY

hr; echo "3 · .env"; hr
if [ -f .env ]; then
  tok=$(grep -E '^BOT_TOKEN=' .env | cut -d= -f2-)
  adm=$(grep -E '^ADMIN_IDS=' .env | cut -d= -f2-)
  echo "file:  .env found"
  echo "token: ${tok:0:10}… (${#tok} chars)$([ -z "$tok" ] && echo '  ← EMPTY, paste the BotFather token')"
  case "$tok" in
    *" "*) echo "       ← contains a space/quote, remove it" ;;
  esac
  echo "admins: ${adm:-EMPTY} $([ -z "$adm" ] && echo '← paste your id from @userinfobot')"
else
  echo "✗ .env missing → cp .env.example .env  (then edit it)"
fi

hr; echo "4 · is it running"; hr
pid=$(pgrep -f "python -m animebot" | head -1)
if [ -n "$pid" ]; then echo "✓ running (pid $pid)"; else echo "✗ not running → bash $DIR/termux-run.sh"; fi
tmux has-session -t "$SESSION" 2>/dev/null && echo "✓ tmux session '$SESSION' alive" \
  || echo "· no tmux session (fine if you run it in the foreground)"

hr; echo "5 · last log lines"; hr
if [ -f "$LOG" ]; then tail -n 25 "$LOG"; else echo "(no $LOG yet)"; fi

hr; echo "6 · what do those lines mean"; hr
if [ -f "$LOG" ]; then
  grep -qi "Conflict: terminated by other getUpdates" "$LOG" && \
    echo "! Two copies are polling. Fix: pkill -f 'python -m animebot' then bash $DIR/termux-run.sh"
  grep -qi "Unauthorized" "$LOG" && \
    echo "! Wrong token. Re-copy it from @BotFather into .env"
  grep -qi "InvalidToken" "$LOG" && \
    echo "! Token is malformed. Re-copy it from @BotFather"
  grep -qi "ModuleNotFoundError" "$LOG" && \
    echo "! Packages missing. Run: $DIR/.venv/bin/pip install -r $DIR/requirements.txt"
  grep -qi "database is locked" "$LOG" && \
    echo "! Two copies sharing one database. Stop all: pkill -f 'python -m animebot'"
  grep -qi "Running as @" "$LOG" && \
    echo "✓ The bot did start at least once — if Telegram is still quiet, check /setprivacy (Step 9)."
fi

hr; echo "7 · live token test (needs internet)"; hr
if [ -f .env ] && [ -n "${tok:-}" ]; then
  $PY - "$tok" <<'PY' 2>&1 | tail -5
import asyncio, sys
async def main():
    from telegram import Bot
    from telegram.error import InvalidToken
    try:
        async with Bot(sys.argv[1]) as bot:
            me = await bot.get_me()
            print(f"  ✓ token works → @{me.username}")
    except InvalidToken:
        print("  ✗ Telegram says the token is invalid → re-copy from @BotFather")
    except Exception as exc:  # noqa: BLE001
        print(f"  ? could not reach Telegram ({type(exc).__name__}) — check Wi-Fi/mobile data")
asyncio.run(main())
PY
fi

hr; echo "Done — copy everything above and send it to me."; hr
