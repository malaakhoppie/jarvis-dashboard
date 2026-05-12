# Clap On

Enable the double-clap trigger daemon.

## Run

```bash
launchctl load ~/Library/LaunchAgents/com.jarvis.claptrigger.plist
```

Then verify it's running:

```bash
ps aux | grep clap-trigger | grep -v grep
```

If the process shows up, confirm: "Clap trigger is ON. Double-clap to launch VS Code + Claude."
If it doesn't show up, report the error from `/tmp/clap-trigger-error.log`.
