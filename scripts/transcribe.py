"""
Transcribe any audio file using local Whisper (runs offline, no API key needed).

Usage:
    python transcribe.py <audio_file>
    python transcribe.py <audio_file> --model medium
    python transcribe.py <audio_file> --output C:\some\folder

Models (speed vs accuracy tradeoff):
    tiny   — fastest, least accurate
    base   — fast, decent
    small  — good balance
    medium — high accuracy, ~5 min for 1hr audio  (default)
    large  — best accuracy, slow

Output: saves a .txt transcript next to the audio file (or in --output folder).
"""

import argparse
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio with Whisper")
    parser.add_argument("audio", help="Path to audio file (.m4a, .mp3, .wav, .mp4, etc.)")
    parser.add_argument("--model", default="medium", choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper model size (default: medium)")
    parser.add_argument("--output", default=None, help="Output folder (default: same as audio file)")
    args = parser.parse_args()

    audio_path = Path(args.audio).resolve()
    if not audio_path.exists():
        print(f"ERROR: File not found: {audio_path}")
        sys.exit(1)

    try:
        import whisper
    except ImportError:
        print("Whisper not installed. Run: pip install openai-whisper")
        sys.exit(1)

    print(f"Loading model: {args.model}")
    print("(First run downloads the model — subsequent runs are instant)")
    model = whisper.load_model(args.model)

    print(f"Transcribing: {audio_path.name}")
    result = model.transcribe(str(audio_path), fp16=False)

    transcript = result["text"].strip()

    out_dir = Path(args.output).resolve() if args.output else audio_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / (audio_path.stem + "_transcript.txt")

    out_file.write_text(transcript, encoding="utf-8")

    print(f"\nDone. Transcript saved to:\n  {out_file}")
    print(f"\n--- Preview (first 500 chars) ---\n{transcript[:500]}")


if __name__ == "__main__":
    main()
