"""Experimental audible-audio check via SDL's disk audio backend.

This is an evidence gate, not a claim of universal iMUSE compatibility.
SCUMM compilation and this runtime audio capture are independent checks.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path


def summarize_audio_bytes(raw: bytes) -> dict:
    """Recognize non-silent PCM without assuming SDL output channel layout."""
    if not isinstance(raw, bytes):
        raise ValueError("Audio capture must be bytes")
    # Avoid a few sporadic non-zero header bytes or a single startup click.
    active = sum(value not in (0, 128) for value in raw)
    return {"bytes": len(raw), "active_bytes": active,
            "pcm_activity_detected": len(raw) >= 8192 and active >= 1024}


def run(game_directory: Path, output_directory: Path, seconds: float = 8.0) -> None:
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("X display required for ScummVM")
    if not all((game_directory / f"tentacle.{part}").is_file() for part in ("000", "001")):
        raise ValueError("Linked SCUMM fixture is missing")
    output_directory.mkdir(parents=True, exist_ok=True)
    raw = output_directory / "scummvm-audio.raw"
    environment = {**os.environ, "SDL_AUDIODRIVER": "disk", "SDL_DISKAUDIOFILE": str(raw)}
    with (output_directory / "scummvm.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(["scummvm", f"--path={game_directory.resolve()}", "tentacle"],
                                   stdout=log, stderr=subprocess.STDOUT, env=environment)
        try:
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("ScummVM exited during sound test")
                time.sleep(0.2)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
    report = summarize_audio_bytes(raw.read_bytes() if raw.exists() else b"")
    report["capture_backend"] = "SDL_DISK"
    (output_directory / "audio-report.json").write_text(json.dumps(report, indent=2) + "\n",
                                                         encoding="utf-8")
    if not report["pcm_activity_detected"]:
        raise RuntimeError(f"No audible PCM activity proven: {report}")
    print(f"Captured {report['bytes']} bytes of non-silent PCM from ScummVM")


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.scumm_audio_probe GAME_DIRECTORY OUTPUT_DIRECTORY")
        return 2
    run(Path(sys.argv[1]), Path(sys.argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
