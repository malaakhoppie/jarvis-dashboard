#!/usr/bin/env python3
"""
Jarvis — Double Clap Trigger
Listens to MacBook mic. Detects two claps within 0.8s, min 0.15s apart.
On trigger: runs scripts/launch-session.sh then exits.

Setup: update WORKSPACE_PATH below to your workspace folder path.
"""

import sounddevice as sd
import numpy as np
import subprocess
import time
import os

# --- CONFIGURE THIS ---
WORKSPACE_PATH = "/path/to/your/jarvis_template"
# ----------------------

SCRIPT_PATH = os.path.join(WORKSPACE_PATH, "scripts", "launch-session.sh")

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024
THRESHOLD = 0.25       # RMS volume spike threshold (0.0–1.0)
MIN_GAP = 0.15         # Minimum seconds between claps
MAX_GAP = 0.8          # Maximum seconds between claps for double-clap
COOLDOWN = 3.0         # Seconds to ignore after trigger fires

last_clap_time = 0.0
triggered = False

def audio_callback(indata, frames, time_info, status):
    global last_clap_time, triggered

    if triggered:
        return

    now = time.time()
    rms = float(np.sqrt(np.mean(indata ** 2)))

    if rms > THRESHOLD:
        gap = now - last_clap_time

        if gap >= MIN_GAP:
            if gap <= MAX_GAP and last_clap_time > 0:
                # Second clap — fire trigger and shut down
                print(f"[jarvis] Double clap detected! Firing launch script. Shutting down.", flush=True)
                triggered = True
                last_clap_time = 0.0
                subprocess.Popen(["zsh", SCRIPT_PATH])
            else:
                # First clap
                print(f"[jarvis] First clap detected (rms={rms:.3f})", flush=True)
                last_clap_time = now

with sd.InputStream(
    samplerate=SAMPLE_RATE,
    blocksize=BLOCK_SIZE,
    channels=1,
    dtype="float32",
    callback=audio_callback,
):
    print("[jarvis] Listening for double clap...", flush=True)
    while not triggered:
        time.sleep(0.1)
    print("[jarvis] Trigger fired — stopped listening.", flush=True)
