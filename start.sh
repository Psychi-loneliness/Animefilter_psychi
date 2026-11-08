#!/data/data/com.termux/files/usr/bin/bash
# Start the bot IN THE FOREGROUND so you see every message on screen.
# Use this to find out why it is silent. Press Ctrl+C to stop.
#
#   bash ~/Animefilter_psychi/start.sh
DIR="$HOME/Animefilter_psychi"

r() { printf "\033[1;33m%s\033[0m\n" "$*"; }
g() { printf "\033[1;32m%s\033[0m\n" "$*"; }
bad() { printf "\033[1;31m%s\033[0m\n" "$*"; }

cd "$DIR" 2>/dev/null || {
  bad "✗ $DIR not found — the bot is not installed."
  echo "  Do Step 4 again (the curl one-liner in MOBILE.md)."
  exit 1
}

# 1. interpreter that actually has the packages
if [ -x .venv/bin/python ] && .venv/bin/python -c "import telegram" 2>/dev/null; then
  PY="$DIR/.venv/bin/python"
elif python -c "import telegram" 2>/dev/null; then
  PY="$(command -v python)"
else
  bad "✗ python-telegram-bot is not installed."
  echo "  Run: bash ~/Animefilter_psychi/termux-setup.sh"
  echo "  and if that fails, send me the file: ~/animebot-setup.log"
  exit 1
fi

# 2. token present?
if [ ! -f .env ]; then
  bad "✗ .env missing → there is no token."
  echo "  Run: cp .env.example .env && nano .env   (paste BOT_TOKEN and ADMIN_IDS)"
  exit 1
fi
TOKEN="$(grep -E '^BOT_TOKEN=' .env | cut -d= -f2- | tr -d '[:space:]')"
case "$TOKEN" in
  ""|*xxxxx*|*AAH…*|111*)
    bad "✗ BOT_TOKEN in .env is empty or still the example value."
    echo "  Fix: nano .env   → BOT_TOKEN=<token from @BotFather> → Ctrl+O, Enter, Ctrl+X"
    exit 1
    ;;
esac
g "✓ token looks set (${TOKEN:0:8}…)"

# 3. no second copy (Telegram allows only one poller)
if pgrep -f "python -m animebot" >/dev/null 2>&1; then
  r "! another copy is already running — stopping it first"
  pkill -f "python -m animebot" 2>/dev/null || true
  tmux kill-session -t animebot 2>/dev/null || true
  sleep 1
fi

# 4. run, and translate the common errors for you
g "──────────────────────────────────────────────"
g "Starting… keep this window open."
g "When you read “Running as @yourbot”, open Telegram and send /start to your bot."
g "Stop with Ctrl+C.  (To run in the background: bash $DIR/termux-run.sh)"
g "──────────────────────────────────────────────"
set -o pipefail
"$PY" -m animebot 2>&1 | while IFS= read -r line; do
  case "$line" in
    *"Unauthorized"*|*"InvalidToken"*)
      bad "$line"
      r "  → The token is wrong. Re-copy it from @BotFather into .env (bash $DIR/start.sh again)."
      ;;
    *"Conflict: terminated by other getUpdates"*)
      bad "$line"
      r "  → Two copies run at once. Run: pkill -f 'python -m animebot'"
      ;;
    *"ModuleNotFoundError"*|*"No module named"*)
      bad "$line"
      r "  → Packages missing. Run: bash ~/Animefilter_psychi/termux-setup.sh"
      ;;
    *"NetworkError"*|*"ConnectError"*|*"getaddrinfo"*)
      bad "$line"
      r "  → No internet for Termux. Switch Wi-Fi/mobile data and try again."
      ;;
    *"Running as @"*)
      g "$line"
      ;;
    *)
      printf '%s\n' "$line"
      ;;
  esac
done

bad "The bot stopped. If you did not press Ctrl+C, copy the lines above and send them to me."
