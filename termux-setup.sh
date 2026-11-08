#!/data/data/com.termux/files/usr/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Run the anime filter bot ON YOUR ANDROID PHONE (Termux) — completely free.
#
#   1. Install Termux from F-Droid (NOT the Play Store version)
#      https://f-droid.org/packages/com.termux/
#   2. Open Termux and paste (one line, whole thing):
#      curl -sL https://raw.githubusercontent.com/Psychi-loneliness/Animefilter_psychi/arena/a2e62907-animefilter-psychi/termux-setup.sh | bash
#
# Install Termux:Boot too (same F-Droid page) so the bot starts after a reboot.
# ─────────────────────────────────────────────────────────────────────────────
set -e

REPO="https://github.com/Psychi-loneliness/Animefilter_psychi.git"
BRANCH="arena/a2e62907-animefilter-psychi"
DIR="$HOME/Animefilter_psychi"

say() { printf "\n\033[1;36m▸ %s\033[0m\n" "$*"; }

say "Updating Termux packages (1–3 min)"
pkg update -y >/dev/null 2>&1 || true
pkg upgrade -y >/dev/null 2>&1 || true
pkg install -y python git termux-api tmux >/dev/null 2>&1

say "Fetching the bot"
if [ -d "$DIR/.git" ]; then
  cd "$DIR" && git fetch -q origin "$BRANCH" && git checkout -q "$BRANCH" && git pull -q
else
  git clone -q --branch "$BRANCH" "$REPO" "$DIR"
  cd "$DIR"
fi

say "Installing Python packages (2–4 min)"
python -m venv .venv 2>/dev/null || true
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
fi

cat <<'TXT'

──────────────────────────────────────────────────────────────
Now paste your bot token and your Telegram id.

Open the editor, then:
  • replace the BOT_TOKEN line with the token from @BotFather
  • replace the ADMIN_IDS line with your id from @userinfobot
  • save:  Ctrl+O then Enter,  exit:  Ctrl+X

TXT
read -r -p "Press Enter to open .env …" _
nano .env

say "Checking the setup"
python -m scripts.doctor || true

cat <<'TXT'

──────────────────────────────────────────────────────────────
Last steps:

1) Keep Android from killing Termux
   • Settings → Apps → Termux → Battery → Unrestricted / Allow background
   • Also disable battery optimisation for Termux and Termux:Boot

2) Start the bot in a background session:
     bash ~/Animefilter_psychi/termux-run.sh

3) After a phone reboot it auto-starts (Termux:Boot must be installed).

Health check anytime:
     tmux ls                  # session "animebot" should exist
     tail -f ~/animebot.log   # live log, Ctrl+C to stop watching
     pkill -f "python -m animebot"     # stop the bot
──────────────────────────────────────────────────────────────
TXT
