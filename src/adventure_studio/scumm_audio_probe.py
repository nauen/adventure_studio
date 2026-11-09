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


def compare_audio_activity(music: dict, control: dict) -> bool:
    """Require a large additional audio signal relative to a silent game."""
    if music["bytes"] < 8192 or control["bytes"] < 8192:
        return False
    music_fraction = music["active_bytes"] / music["bytes"]
    control_fraction = control["active_bytes"] / control["bytes"]
    return bool(music["pcm_activity_detected"] and music_fraction > control_fraction + 0.02)


def _capture(game_directory: Path, output_directory: Path, soundfont: Path,
             label: str, seconds: float) -> dict:
    if not all((game_directory / f"tentacle.{part}").is_file() for part in ("000", "001")):
        raise ValueError("Linked SCUMM fixture is missing")
    raw = output_directory / f"{label}-audio.raw"
    environment = {**os.environ, "SDL_AUDIODRIVER": "disk", "SDL_DISKAUDIOFILE": str(raw)}
    with (output_directory / f"{label}-scummvm.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(["scummvm", f"--path={game_directory.resolve()}",
                                    "--music-driver=fluidsynth", f"--soundfont={soundfont}",
                                    "--music-volume=255", "tentacle"],
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
    return summarize_audio_bytes(raw.read_bytes() if raw.exists() else b"")


def run(game_directory: Path, output_directory: Path, control_game_directory: Path | None = None,
        seconds: float = 8.0) -> None:
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("X display required for ScummVM")
    output_directory.mkdir(parents=True, exist_ok=True)
    # A GM-only resource must not be tested with ScummVM's automatic driver
    # selection: older DOTT-compatible games may default to an AdLib driver.
    soundfonts = sorted(Path("/usr/share/sounds").rglob("*.sf2"))
    if not soundfonts:
        raise RuntimeError("No system SoundFont available for General MIDI playback")
    report = _capture(game_directory, output_directory, soundfonts[0], "music", seconds)
    if control_game_directory is not None:
        control = _capture(control_game_directory, output_directory, soundfonts[0], "control", seconds)
        report["control"] = control
        report["music_signal_above_control"] = compare_audio_activity(report, control)
    report["capture_backend"] = "SDL_DISK"
    report["music_driver"] = "fluidsynth"
    report["soundfont"] = str(soundfonts[0])
    (output_directory / "audio-report.json").write_text(json.dumps(report, indent=2) + "\n",
                                                         encoding="utf-8")
    if not report["pcm_activity_detected"] or (control_game_directory is not None
                                              and not report["music_signal_above_control"]):
        raise RuntimeError(f"No audible PCM activity proven: {report}")
    print(f"Captured {report['bytes']} bytes of non-silent PCM from ScummVM; "
          f"control comparison: {report.get('music_signal_above_control', 'not supplied')}")


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print("Usage: python -m adventure_studio.scumm_audio_probe GAME_DIRECTORY OUTPUT_DIRECTORY [CONTROL_GAME_DIRECTORY]")
        return 2
    run(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]) if len(sys.argv) == 4 else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
