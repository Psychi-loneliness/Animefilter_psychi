#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Anime filter bot — one-shot installer for Android (Termux). Costs nothing.
#
# Run it like this (NOT with a pipe):
#
#   curl -sLo ~/animebot-setup.sh \
#     https://raw.githubusercontent.com/Psychi-loneliness/Animefilter_psychi/arena/a2e62907-animefilter-psychi/termux-setup.sh \
#     && bash ~/animebot-setup.sh
#
# Fully hands-off (no editor):
#
#   BOT_TOKEN="8123:AA…" ADMIN_IDS="123456789" bash ~/animebot-setup.sh
# ─────────────────────────────────────────────────────────────────────────────
set -u

REPO="https://github.com/Psychi-loneliness/Animefilter_psychi.git"
BRANCH="arena/a2e62907-animefilter-psychi"
DIR="$HOME/Animefilter_psychi"
TOKEN="${BOT_TOKEN:-}"
ADMINS="${ADMIN_IDS:-}"

say() { printf "\n\033[1;36m▸ %s\033[0m\n" "$*"; }
warn() { printf "\033[1;33m!  %s\033[0m\n" "$*"; }
die() { printf "\033[1;31m✗  %s\033[0m\n" "$*" >&2; exit 1; }

# If someone still pipes the script (`curl … | bash`), stdin is not a terminal and
# the token editor/`read` would break. Re-attach to the real terminal when we can.
if [ ! -t 0 ]; then
  if [ -e /dev/tty ] && [ -t 2 ]; then
    exec </dev/tty
  elif [ -z "$TOKEN" ]; then
    die "Run it as:  curl -sLo ~/animebot-setup.sh <raw-url> && bash ~/animebot-setup.sh"
  fi
fi

# ── Step 1: packages ─────────────────────────────────────────────────────────
say "Step 1/5 · Installing packages (1–3 min, ignore warnings)"
pkg update -y >/dev/null 2>&1 || warn "pkg update had warnings — continuing"
pkg upgrade -y >/dev/null 2>&1 || true
pkg install -y python git termux-api tmux >/dev/null 2>&1 \
  || die "pkg install failed. Run: pkg update && pkg install python git termux-api tmux"

command -v python >/dev/null 2>&1 || die "python is missing after install"
say "python $(python -V 2>&1 | awk '{print $2}') ready"

# ── Step 2: get the code ─────────────────────────────────────────────────────
say "Step 2/5 · Downloading the bot"
if [ -d "$DIR/.git" ]; then
  git -C "$DIR" fetch -q origin "$BRANCH" || die "git fetch failed (no internet?)"
  git -C "$DIR" checkout -q "$BRANCH"
  git -C "$DIR" pull -q --ff-only || warn "could not fast-forward — using local copy"
else
  rm -rf "$DIR"
  git clone -q --branch "$BRANCH" --single-branch "$REPO" "$DIR" \
    || die "git clone failed — check your internet connection"
fi
cd "$DIR" || die "could not enter $DIR"

# ── Step 3: python packages ──────────────────────────────────────────────────
say "Step 3/5 · Installing Python packages (2–4 min)"
install_deps() {  # $1 = python interpreter
  "$1" -m pip install --upgrade pip >>"$HOME/animebot-setup.log" 2>&1 || true
  "$1" -m pip install -r requirements.txt >>"$HOME/animebot-setup.log" 2>&1
}

USE_VENV=0
if python -m venv .venv >>"$HOME/animebot-setup.log" 2>&1 && [ -x .venv/bin/python ]; then
  USE_VENV=1
  PYTHON="$DIR/.venv/bin/python"
  say "   using a private environment (.venv)"
  if ! install_deps "$PYTHON"; then
    warn "venv install failed on this device — falling back to Termux python"
    USE_VENV=0
  fi
fi

if [ "$USE_VENV" = "0" ]; then
  # Termux: install straight into its own python (no venv needed)
  PYTHON="$(command -v python)"
  say "   installing into Termux python ($PYTHON)"
  pkg install -y python-pip >>"$HOME/animebot-setup.log" 2>&1 || true
  install_deps "$PYTHON" || die "pip install failed — see $HOME/animebot-setup.log"
fi

"$PYTHON" -c "import telegram, aiosqlite, dotenv" 2>/dev/null \
  || die "packages did not import — see $HOME/animebot-setup.log"

# ── Step 4: token + id ───────────────────────────────────────────────────────
say "Step 4/5 · Configuration"
[ -f .env ] || cp .env.example .env

write_env() {  # $1 = token, $2 = admins
  "$PYTHON" - "$1" "$2" <<'PY'
import pathlib, re, sys
token, admins = sys.argv[1], sys.argv[2]
p = pathlib.Path(".env")
text = p.read_text()
text = re.sub(r"(?m)^BOT_TOKEN=.*$", f"BOT_TOKEN={token}", text)
text = re.sub(r"(?m)^ADMIN_IDS=.*$", f"ADMIN_IDS={admins}", text)
p.write_text(text)
PY
}

if [ -n "$TOKEN" ]; then
  write_env "$TOKEN" "$ADMINS"
  echo "   wrote BOT_TOKEN and ADMIN_IDS from the environment"
else
  cat <<'TXT'

   ─────────────────────────────────────────────────────────────
   The editor opens next. Do exactly two edits:

     BOT_TOKEN=…    ← paste the token from @BotFather
     ADMIN_IDS=…    ← paste your id from @userinfobot

   Save: Ctrl+O  then Enter      Exit: Ctrl+X
   (Use the Termux extra-key row for Ctrl.)

TXT
  read -r -p "   Press Enter to open the editor … " _ || true
  if command -v nano >/dev/null 2>&1; then
    nano .env
  else
    pkg install -y nano >/dev/null 2>&1 && nano .env
  fi
fi

# ── Step 5: check ────────────────────────────────────────────────────────────
say "Step 5/5 · Checking everything"
"$PYTHON" -m scripts.doctor || warn "self-check reported problems (see above)"

cat <<TXT

\033[1;32m──────────────────────────────────────────────────────────────
Install finished.
──────────────────────────────────────────────────────────────\033[0m

Next, in this same Termux window:

  1) Start the bot (background + auto-restart):
       bash $DIR/termux-run.sh

  2) Let Android keep it alive (one time):
       Settings → Apps → Termux → Battery → Unrestricted
       (Xiaomi/Realme/Oppo/Vivo: also Battery saver → No restrictions)

  3) Start after a phone reboot (one time):
       mkdir -p ~/.termux/boot
       cp $DIR/termux-boot.sh ~/.termux/boot/
       chmod +x ~/.termux/boot/termux-boot.sh

Useful commands:
   tail -f ~/animebot.log                    live log (Ctrl+C stops watching)
   pkill -f "python -m animebot"             stop the bot
   bash $DIR/termux-run.sh                   start / restart it
   bash $DIR/termux-setup.sh                 update to the newest version
   bash $DIR/scripts/termux-check.sh         broken? run this and share the output
   ~/animebot-setup.log                      installer log (if setup failed)
TXT
