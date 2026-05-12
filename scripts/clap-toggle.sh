#!/bin/zsh

# Jarvis — Clap Trigger Toggle
# Toggles the clap trigger LaunchAgent daemon on/off.

PLIST="$HOME/Library/LaunchAgents/com.jarvis.claptrigger.plist"

if ps aux | grep -q "[c]lap-trigger.py"; then
    launchctl unload "$PLIST"
    echo "Jarvis clap trigger OFF"
else
    launchctl load "$PLIST"
    echo "Jarvis clap trigger ON"
fi
