# Clap Off

Disable the double-clap trigger daemon.

## Run

```bash
launchctl unload ~/Library/LaunchAgents/com.jarvis.claptrigger.plist
```

Then verify it's stopped:

```bash
ps aux | grep clap-trigger | grep -v grep
```

If no process shows up, confirm: "Clap trigger is OFF."
If it's still running, kill it directly: `pkill -f clap-trigger.py`
