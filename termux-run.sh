#!/data/data/com.termux/files/usr/bin/bash
# Start (or restart) the bot in a background tmux session with a wake lock.
#   bash ~/Animefilter_psychi/termux-run.sh
DIR="$HOME/Animefilter_psychi"
SESSION="animebot"
LOG="$HOME/animebot.log"

cd "$DIR" || { echo "Run termux-setup.sh first"; exit 1; }
# shellcheck disable=SC1091
source .venv/bin/activate

# stop an older copy so Telegram does not complain about two pollers
tmux kill-session -t "$SESSION" 2>/dev/null || true
pkill -f "python -m animebot" 2>/dev/null || true
sleep 1

# keep the CPU awake while the screen is off (termux-api)
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock

# APPEND to the log so we do not lose the previous run's tail
echo "── start $(date) ──" >> "$LOG"
tmux new-session -d -s "$SESSION" -c "$DIR" \
  "source .venv/bin/activate && while true; do python -m animebot >> $LOG 2>&1; echo \"── crash $(date), restarting in 5s ──\" >> $LOG; sleep 5; done"

sleep 3
echo "Started. Last log lines:"
tail -n 12 "$LOG"
echo
echo "Live log:  tail -f $LOG"
echo "Stop bot:  pkill -f 'python -m animebot' && tmux kill-session -t $SESSION"
