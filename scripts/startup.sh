#!/bin/zsh

# Jarvis — Startup Script
# Opens clap trigger + Telegram listener in separate terminal windows.
# Run this once on login, or set it to run automatically via LaunchAgent.
#
# Setup: update WORKSPACE_PATH below to your workspace folder path.

WORKSPACE_PATH="/path/to/your/jarvis_template"

# Terminal 1: clap trigger listener
osascript -e "tell application \"Terminal\" to do script \"python3 $WORKSPACE_PATH/scripts/clap-trigger.py\""

sleep 0.4

# Terminal 2: Telegram listener (Claude Code with Telegram plugin)
osascript -e 'tell application "Terminal" to do script "claude --channels plugin:telegram@claude-plugins-official --dangerously-skip-permissions"'
