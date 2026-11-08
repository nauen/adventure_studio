"""Exercise an authored VOC sound cue and Escape stop in stock ScummVM."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from .scumm_assets import destination_fixture, scrolling_fixture
from .scumm_launch import colored_item_center
from .scumm_project import GameDocument, canonical_json, export_document, parse_document
from .scumm_toolchain import compile_story_game
from .scumm_voc_fixture import original_voc_effect
from .studio_sequences import append_sequence_step, set_sequence_skippable
from .scumm_project import SoundAsset


def run_sound_effect_probe(upstream: Path, destination: Path,
                           voice_line: bool = False) -> dict:
    """A real hotspot click plays a VOC; Escape applies the final stop cue."""
    document = GameDocument("SoundEffects", (scrolling_fixture(), destination_fixture()),
                            sound_assets=(SoundAsset("BellSound", "Harbor",
                                                     original_voc_effect(duration_ms=5000)),))
    raw = canonical_json(document)
    if voice_line:
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Gesprochene Zeile",
                                   None, None, "BellSound", None,
                                   subtitle="I can hear the bell.")
    else:
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Sound starten",
                                   None, None, "BellSound", None)
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Warten",
                                   None, None, None, 6)
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Sound stoppen",
                                   None, None, "BellSound", None)
    raw = set_sequence_skippable(raw, "Harbor|Key|Close", True)
    build = destination / "build"
    resources = build / "resources"
    resources.mkdir(parents=True, exist_ok=True)
    (build / "project.json").write_text(raw, encoding="utf-8")
    export_document(parse_document(raw), resources)
    game_dir = compile_story_game(build, upstream, destination / "game")
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("Sound effect gameplay requires Xvfb")
    frames = destination / "screenshots"
    frames.mkdir(parents=True, exist_ok=True)

    def frame(name: str) -> None:
        screenshot = frames / f"scummvm-{name}.png"
        xwd = frames / f"scummvm-{name}.xwd"
        subprocess.run(["xwd", "-root", "-silent", "-out", str(xwd)],
                       check=True, timeout=10, stdout=subprocess.DEVNULL)
        subprocess.run(["convert", str(xwd), str(screenshot)], check=True, timeout=10,
                       stdout=subprocess.DEVNULL)

    pcm_path = destination / "sound-effect.raw"
    with (frames / "scummvm.log").open("w", encoding="utf-8") as log:
        game = subprocess.Popen(["scummvm", f"--path={game_dir.resolve()}", "tentacle"],
                                stdout=log, stderr=subprocess.STDOUT,
                                env={**os.environ, "SDL_AUDIODRIVER": "disk",
                                     "SDL_DISKAUDIOFILE": str(pcm_path)})
        epoch = time.monotonic()
        try:
            time.sleep(6)
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited before sound interaction")
            frame("before")
            key_x, key_y = colored_item_center(frames, "before", (255, 220, 75))
            for x, y in ((234, 563), (key_x, key_y)):
                subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                               check=True, timeout=10)
            start_at = time.monotonic()
            # The actor first walks to the clicked hotspot (~1.5 s), then
            # the sequence starts. Skip only after native sound is playing.
            time.sleep(2.4 if voice_line else 3.1)
            if voice_line:
                frame("speaking")
            subprocess.run(["xdotool", "key", "Escape"], check=True, timeout=10)
            stop_at = time.monotonic()
            time.sleep(3)
            frame("after")
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited after skipped sound interaction")
        finally:
            game.terminate()
            try:
                game.wait(timeout=5)
            except subprocess.TimeoutExpired:
                game.kill()
                game.wait(timeout=5)

    duration = time.monotonic() - epoch
    pcm = pcm_path.read_bytes() if pcm_path.exists() else b""

    def activity(start: float, end: float) -> float:
        if duration <= 0 or len(pcm) < 8192 or end <= start:
            return 0.0
        first = int(max(0, start - epoch) / duration * len(pcm))
        last = int(min(duration, end - epoch) / duration * len(pcm))
        sample = pcm[first:last]
        return sum(value not in (0, 128) for value in sample) / len(sample) if sample else 0.0

    report = {
        "native_sound_id": "BellSound",
        "voice_line": voice_line,
        "escape_sent": True,
        "pcm_bytes": len(pcm),
        "before_click": round(activity(start_at - 1.4, start_at - 0.2), 4),
        "during_sound": round(activity(start_at + 1.8, stop_at - 0.15), 4)
        if voice_line else round(activity(start_at + 2.0, stop_at - 0.15), 4),
        "after_escape": round(activity(stop_at + 1.0, stop_at + 2.6), 4),
    }
    report["sound_effect_audible_and_stopped"] = bool(
        report["pcm_bytes"] >= 8192
        and report["during_sound"] > report["before_click"] + 0.1
        and report["during_sound"] > report["after_escape"] + 0.1)
    (destination / "sound-effect-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["sound_effect_audible_and_stopped"]:
        raise RuntimeError(f"Native VOC sound did not start/stop audibly: {report}")
    return report


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--voice":
        print(run_sound_effect_probe(Path(sys.argv[2]), Path(sys.argv[3]), voice_line=True))
    elif len(sys.argv) == 3:
        print(run_sound_effect_probe(Path(sys.argv[1]), Path(sys.argv[2])))
    else:
        raise SystemExit("Usage: python -m adventure_studio.scumm_sound_effect_probe [--voice] SCUMMC DESTINATION")
