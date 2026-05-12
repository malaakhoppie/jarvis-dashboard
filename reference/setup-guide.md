# Jarvis Setup Guide

Complete these steps once and Jarvis is ready to use.

**Total time:** ~20 minutes

---

## Step 1: Install Dependencies

Jarvis needs Python and one audio library for the clap trigger.

```bash
pip3 install sounddevice numpy
```

If you don't have pip3:
```bash
brew install python3
pip3 install sounddevice numpy
```

---

## Step 2: Update Workspace Paths

Two scripts need to know where this workspace lives. Open each file and replace `/path/to/your/jarvis_template` with the actual path to this folder.

**Find your path:**
```bash
pwd
# Run this from inside the jarvis_template folder
```

**Files to update:**
1. `scripts/clap-trigger.py` — line 14: `WORKSPACE_PATH = "/path/to/your/jarvis_template"`
2. `scripts/launch-session.sh` — line 8: `WORKSPACE_PATH="/path/to/your/jarvis_template"`
3. `scripts/startup.sh` — line 9: `WORKSPACE_PATH="/path/to/your/jarvis_template"`

---

## Step 3: Make Scripts Executable

```bash
chmod +x scripts/launch-session.sh
chmod +x scripts/startup.sh
chmod +x scripts/clap-toggle.sh
```

---

## Step 4: Install the LaunchAgent (Auto-start on Login)

This makes the clap trigger start automatically every time you log into your Mac.

**a) Create the plist file:**

```bash
cat > ~/Library/LaunchAgents/com.jarvis.claptrigger.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jarvis.claptrigger</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/your/jarvis_template/scripts/clap-trigger.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardErrorPath</key>
    <string>/tmp/clap-trigger-error.log</string>
    <key>StandardOutPath</key>
    <string>/tmp/clap-trigger-out.log</string>
</dict>
</plist>
EOF
```

**b) Replace the path in the plist:**

Open the file you just created and replace `/path/to/your/jarvis_template` with your actual path.

```bash
open ~/Library/LaunchAgents/com.jarvis.claptrigger.plist
```

**c) Load it:**

```bash
launchctl load ~/Library/LaunchAgents/com.jarvis.claptrigger.plist
```

**d) Verify it's running:**

```bash
ps aux | grep clap-trigger | grep -v grep
```

You should see a Python process. If you do — the clap trigger is live.

---

## Step 5: Test the Clap Trigger

1. Make sure the clap trigger is running (Step 4d above)
2. Clap twice quickly near your Mac's mic (within ~0.8 seconds)
3. VS Code should open in the jarvis_template workspace and Claude Code should launch

If it doesn't work:
- Check the log: `cat /tmp/clap-trigger-error.log`
- Make sure mic permissions are granted: System Settings → Privacy & Security → Microphone → Terminal

---

## Step 6: Set Up Telegram Bot (Optional)

See `reference/telegram-n8n-setup-guide.md` for the full Telegram bot setup.

Once set up, you can message your Jarvis bot from anywhere on your phone.

---

## Step 7: Fill In Your Context

Open these files and fill in your information:
- `context/personal-info.md` — who you are
- `context/strategy.md` — what you're working toward

Jarvis reads these at the start of every session via `/prime`.

---

## Step 8: First Session

Open Claude Code in this workspace:

```bash
cd /path/to/your/jarvis_template
claude
```

Then run:
```
/prime
```

Jarvis will read your context and confirm it's ready.

---

## Enable / Disable Clap Trigger

From within Claude Code, run:
- `/clap-on` — enable the clap daemon
- `/clap-off` — disable the clap daemon

Or use the shell script directly:
```bash
./scripts/clap-toggle.sh
```
