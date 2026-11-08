#!/data/data/com.termux/files/usr/bin/bash
# Start (or restart) the bot in the background, with a wake lock and auto-restart.
#   bash ~/Animefilter_psychi/termux-run.sh
# Works with either a .venv (PC/older Termux) or Termux's own python.
DIR="$HOME/Animefilter_psychi"
SESSION="animebot"
LOG="$HOME/animebot.log"
SELF="$(cd "$(dirname "$0")" && pwd)/termux-run.sh"

cd "$DIR" 2>/dev/null || { echo "✗ $DIR not found — run termux-setup.sh first"; exit 1; }

# pick the interpreter we actually have packages in
if [ -x .venv/bin/python ] && .venv/bin/python -c "import telegram" 2>/dev/null; then
  PY="$DIR/.venv/bin/python"
elif python -c "import telegram" 2>/dev/null; then
  PY="$(command -v python)"
else
  echo "✗ python-telegram-bot is not installed."
  echo "  Fix: bash ~/Animefilter_psychi/termux-setup.sh   (or: pip install -r requirements.txt)"
  exit 1
fi
echo "interpreter: $PY"

# stop an older copy so Telegram does not complain about two pollers
tmux kill-session -t "$SESSION" 2>/dev/null || true
pkill -f "python -m animebot" 2>/dev/null || true
sleep 1

# keep the CPU awake while the screen is off (termux-api package)
if command -v termux-wake-lock >/dev/null 2>&1; then
  termux-wake-lock 2>/dev/null || true
else
  echo "· tip: pkg install termux-api  → keeps the bot awake with the screen off"
fi

echo "── start $(date) ──" >> "$LOG"

# run directly if tmux is not installed — simpler and always works
if ! command -v tmux >/dev/null 2>&1; then
  echo "· tmux not installed — running in this window (press Ctrl+C to stop)"
  exec "$PY" -m animebot
fi

# a tiny loop script keeps the quoting simple and survives crashes
cat > "$DIR/.run-loop.sh" <<LOOP
#!/usr/bin/env bash
cd "$DIR"
while true; do
  "$PY" -m animebot >> "$LOG" 2>&1
  echo "── exit \$? at \$(date), restarting in 5s ──" >> "$LOG"
  sleep 5
done
LOOP
chmod +x "$DIR/.run-loop.sh"

tmux new-session -d -s "$SESSION" -c "$DIR" "bash $DIR/.run-loop.sh"

sleep 4
echo
echo "Last log lines:"
tail -n 15 "$LOG"
echo
if grep -q "Running as @" "$LOG"; then
  echo "✓ Looks alive.  Live log: tail -f $LOG"
else
  echo "✗ No 'Running as @…' yet. See the log above, or run:"
  echo "  bash $DIR/scripts/termux-check.sh"
fi
echo "Stop:  pkill -f 'python -m animebot'; tmux kill-session -t $SESSION"
