#!/bin/zsh

# Jarvis — Launch Session
# Triggered by double clap. Opens VS Code in workspace + Claude Code terminal.
#
# Setup: update WORKSPACE_PATH below to your workspace folder path.

WORKSPACE_PATH="/path/to/your/jarvis_template"

# Open VS Code in workspace
code "$WORKSPACE_PATH"

# Wait for VS Code to fully load
sleep 4

# Open integrated terminal in VS Code and run Claude Code (cr = claude --resume)
osascript <<'EOF'
tell application "Visual Studio Code"
    activate
end tell
delay 2.0
tell application "System Events"
    tell process "Code"
        keystroke "`" using {control down}
        delay 2.5
        keystroke "cr"
        key code 36
    end tell
end tell
EOF
