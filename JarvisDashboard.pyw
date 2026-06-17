"""
JarvisDashboard.pyw — Standalone desktop launcher.

If JARVIS_CLOUD_URL is set (env var or cloud_url.txt), opens that URL directly
in the system browser so laptop and phone use the same cloud app.

Otherwise falls back to launching a local Streamlit server.
"""
import os
import sys
import time
import subprocess
import urllib.request
import urllib.error
import webbrowser
from pathlib import Path

BASE = Path(__file__).parent
PORT = 8765
LOCAL_URL = f"http://localhost:{PORT}"

# ── Cloud URL resolution ──────────────────────────────────────────────────────
def _cloud_url() -> str:
    """Return the Streamlit Cloud URL if configured, else empty string."""
    url = os.getenv("JARVIS_CLOUD_URL", "").strip()
    if url:
        return url
    url_file = BASE / "cloud_url.txt"
    if url_file.exists():
        url = url_file.read_text().strip()
        if url:
            return url
    return ""


# ── Local Streamlit launch ────────────────────────────────────────────────────
def _find_python():
    return sys.executable


def _wait_for_server(timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(LOCAL_URL, timeout=1)
            return True
        except Exception:
            time.sleep(0.4)
    return False


def _start_streamlit():
    app_path = BASE / "dashboard" / "app.py"
    cmd = [
        _find_python(), "-m", "streamlit", "run", str(app_path),
        "--server.port", str(PORT),
        "--server.headless", "true",
        "--server.runOnSave", "false",
        "--browser.gatherUsageStats", "false",
        "--server.address", "localhost",
    ]
    return subprocess.Popen(
        cmd,
        cwd=str(BASE),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )


def _open_in_webview(url: str, proc=None):
    try:
        import webview
    except ImportError:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk(); root.withdraw()
        messagebox.showerror(
            "Jarvis Dashboard",
            "pywebview not installed.\n\nRun: pip install pywebview\nThen relaunch."
        )
        if proc: proc.terminate()
        return

    def on_closed():
        if proc: proc.terminate()

    window = webview.create_window(
        "Jarvis — Trading Intelligence", url,
        width=1440, height=900, min_size=(1100, 700),
        background_color="#0a0a0f",
    )
    window.events.closed += on_closed
    webview.start(debug=False)
    if proc: proc.terminate()


def main():
    cloud = _cloud_url()

    if cloud:
        # Open cloud URL — phone and laptop see the same app
        webbrowser.open(cloud)
        return

    # ── Local fallback ────────────────────────────────────────────────────────
    proc = _start_streamlit()
    ready = _wait_for_server(timeout=40)

    if not ready:
        proc.terminate()
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk(); root.withdraw()
        messagebox.showerror("Jarvis Dashboard", "Dashboard failed to start. Check that streamlit is installed.")
        return

    _open_in_webview(LOCAL_URL, proc)


if __name__ == "__main__":
    main()
