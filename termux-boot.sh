#!/data/data/com.termux/files/usr/bin/bash
# Auto-start after a phone reboot.
# Copy this file to ~/.termux/boot/ (Termux:Boot app required) and chmod +x it:
#   mkdir -p ~/.termux/boot && cp ~/Animefilter_psychi/termux-boot.sh ~/.termux/boot/ && chmod +x ~/.termux/boot/termux-boot.sh
sleep 25            # give the phone time to get network
bash "$HOME/Animefilter_psychi/termux-run.sh"
