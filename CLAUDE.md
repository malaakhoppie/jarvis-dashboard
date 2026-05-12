# CLAUDE.md

This file provides guidance to Claude Code when working in this workspace.

---

## What This Is

This is **Jarvis** — a Claude Code workspace template with two core features:

1. **Double Clap Trigger** — Clap twice near your MacBook mic and it automatically opens VS Code, Claude Code, and your Telegram listener.
2. **Telegram Bot** — Message your AI agent from anywhere on your phone via Telegram.

---

## Agent Name

This agent's name is **Jarvis**. When the user says "Jarvis wake up" or "Jarvis" in conversation, respond accordingly.

---

## Workspace Structure

```
.
├── CLAUDE.md                          # This file
├── .claude/
│   └── commands/
│       ├── prime.md                   # /prime — session init
│       ├── clap-on.md                 # /clap-on — enable clap trigger daemon
│       └── clap-off.md                # /clap-off — disable clap trigger daemon
├── context/
│   ├── personal-info.md               # Who you are — fill this in
│   └── strategy.md                    # Your goals — fill this in
├── scripts/
│   ├── clap-trigger.py               # Mic listener — detects double clap, fires launch-session.sh
│   ├── launch-session.sh             # Opens VS Code + Claude terminals on double clap
│   ├── startup.sh                    # Opens clap trigger + Telegram listener in two terminal windows
│   ├── clap-toggle.sh                # Toggle clap trigger daemon on/off
│   └── agent-system-prompt.md       # System prompt for your Telegram bot — paste into n8n
└── reference/
    ├── setup-guide.md                 # Full setup walkthrough for this template
    └── telegram-n8n-setup-guide.md   # Telegram bot + n8n setup
```

---

## Commands

### /prime
Initialize a new session. Claude reads CLAUDE.md and context files, then summarizes understanding and confirms readiness.

### /clap-on
Enable the double-clap trigger daemon. After running, a double clap near your Mac mic will automatically open VS Code, Claude Code, and your Telegram terminal.

### /clap-off
Disable the double-clap trigger daemon.

### /backtest
Start a Mr. Casino reflection task backtesting session. Send your marked chart screenshots and Jarvis reviews them against the task criteria, tracks your rep count, and tells you exactly what's right or wrong.

---

## How the Clap System Works

1. `startup.sh` runs on login (or manually) — opens two terminal windows:
   - Terminal 1: `clap-trigger.py` — listens to your mic 24/7
   - Terminal 2: Telegram listener (Claude Code with Telegram plugin)

2. When you double-clap, `clap-trigger.py` fires `launch-session.sh`, which:
   - Opens VS Code in this workspace
   - Opens the Claude Code terminal

3. To always have clap trigger running on startup: install the LaunchAgent plist (see `reference/setup-guide.md`)

---

## Setup

Before using this workspace, complete the setup in `reference/setup-guide.md`. Key steps:
1. Update workspace paths in `scripts/clap-trigger.py` and `scripts/launch-session.sh`
2. Install the LaunchAgent plist
3. Fill in `context/personal-info.md` and `context/strategy.md`
4. Set up your Telegram bot via `reference/telegram-n8n-setup-guide.md`

---

## Auto-Start Behavior

**Every new session, automatically run the /prime routine without being asked.** Do not wait for the user to type /prime. On session start:
1. Read `context/personal-info.md` and `context/strategy.md`
2. Greet Mala by name
3. Give a brief summary: who she is, current priorities, available commands
4. Confirm readiness

---

## Session Workflow

1. **Start**: Jarvis auto-primes on launch — no command needed
2. **Enable clap**: Run `/clap-on` to enable the clap daemon
3. **Work**: Use Claude Code directly or message your Telegram bot from your phone
