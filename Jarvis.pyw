"""
Jarvis Desktop Launcher
Double-click to open the Jarvis trading dashboard as a standalone app window.
- Starts the Streamlit server (hidden) if not already running
- Shows a loading splash while it boots
- Opens Edge or Chrome in --app mode (no address bar, no tabs)
"""
import os
import sys
import subprocess
import time
import threading
import urllib.request
import tkinter as tk
from pathlib import Path

BASE          = Path(__file__).parent
DASHBOARD_DIR = BASE / "dashboard"
PORT          = 8501
URL           = f"http://localhost:{PORT}"
ICON          = str(BASE / "jarvis.ico")

# ── Browser search order ──────────────────────────────────────────────────────
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def _server_ready() -> bool:
    try:
        urllib.request.urlopen(URL, timeout=1)
        return True
    except Exception:
        return False


def _start_server():
    flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
    subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--server.port", str(PORT),
         "--server.headless", "true",
         "--browser.gatherUsageStats", "false",
         "--theme.base", "dark"],
        cwd=str(DASHBOARD_DIR),
        creationflags=flags,
    )


def _launch_browser():
    for path in BROWSERS:
        if os.path.exists(path):
            subprocess.Popen([path, f"--app={URL}", "--window-size=1380,920",
                              "--window-position=0,0"])
            return
    # Fallback — default browser (will have tabs/address bar)
    import webbrowser
    webbrowser.open(URL)


# ── Splash window ─────────────────────────────────────────────────────────────
class Splash(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Jarvis")
        self.resizable(False, False)
        self.configure(bg="#09090f")
        self.overrideredirect(True)   # borderless
        self.attributes("-topmost", True)

        w, h = 320, 160
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        if os.path.exists(ICON):
            try:
                self.iconbitmap(ICON)
            except Exception:
                pass

        tk.Label(self, text="JARVIS", font=("Segoe UI", 22, "bold"),
                 fg="#f0b429", bg="#09090f").pack(pady=(30, 4))
        self.status = tk.StringVar(value="Starting server…")
        tk.Label(self, textvariable=self.status, font=("Segoe UI", 10),
                 fg="#7777aa", bg="#09090f").pack()
        self.dots = tk.Label(self, text="", font=("Segoe UI", 10),
                             fg="#f0b429", bg="#09090f")
        self.dots.pack(pady=(2, 0))
        self._dot_count = 0
        self._animate()

    def _animate(self):
        self._dot_count = (self._dot_count + 1) % 4
        self.dots.config(text="●" * self._dot_count + "○" * (3 - self._dot_count))
        self.after(400, self._animate)

    def set_status(self, msg: str):
        self.status.set(msg)


def _boot(splash: Splash):
    """Runs in a background thread — starts server, waits, launches browser."""
    if _server_ready():
        splash.set_status("Dashboard already running…")
    else:
        splash.set_status("Starting Jarvis server…")
        _start_server()
        for i in range(40):           # wait up to 40 seconds
            time.sleep(1)
            if _server_ready():
                break
            if i > 5:
                splash.set_status(f"Waiting for server… ({i}s)")

    splash.set_status("Opening dashboard…")
    time.sleep(0.4)
    _launch_browser()
    time.sleep(0.6)
    splash.quit()   # close splash → mainloop exits → script ends


def main():
    splash = Splash()
    t = threading.Thread(target=_boot, args=(splash,), daemon=True)
    t.start()
    splash.mainloop()
    try:
        splash.destroy()
    except Exception:
        pass


if __name__ == "__main__":
    main()
