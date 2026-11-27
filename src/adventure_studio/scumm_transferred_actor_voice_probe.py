"""Native transferred Actor VOC playback: room transfer, real click, PCM, Escape."""
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from .scumm_actor_zclip_transfer_probe import author_transfer_project, RETURN_RGB, REVEAL_RGB
from .scumm_launch import colored_item_center, colored_item_pixels
from .scumm_project import SoundAsset, canonical_json, export_document, parse_document
from .scumm_toolchain import compile_story_game
from .scumm_two_actor_four_mask_probe import ACTOR_IDS
from .scumm_voc_fixture import original_voc_effect
from .studio_sequences import append_sequence_step, set_sequence_skippable


def run(upstream, destination):
    destination.mkdir(parents=True, exist_ok=True)
    build = destination / "build"
    resources = build / "resources"
    resources.mkdir(parents=True, exist_ok=True)
    raw = author_transfer_project(destination, "transparent", dynamic=True)
    doc = parse_document(raw)
    costume = doc.costumes[-1]
    name = "R06TransferredVoiceCostume"
    doc = replace(doc, costumes=(*doc.costumes[:-1], replace(costume, name=name)),
                  actors=tuple(replace(a, costume=name) if a.costume == costume.name else a
                               for a in doc.actors),
                  sound_assets=(*doc.sound_assets, SoundAsset("CellarVoice", "Cellar",
                      original_voc_effect(duration_ms=8000))))
    raw = canonical_json(doc)
    raw = append_sequence_step(raw, "Cellar", "R06Reveal", "Close",
        "Gesprochene Zeile", ACTOR_IDS[0], None, "CellarVoice", None,
        subtitle="I am speaking from the cellar. Listen to my voice.")
    raw = set_sequence_skippable(raw, "Cellar|R06Reveal|Close", True)
    (build / "project.json").write_text(raw, encoding="utf-8")
    export_document(parse_document(raw), resources)
    game_dir = compile_story_game(build, upstream, destination / "game")
    frames = destination / "screenshots"
    frames.mkdir(exist_ok=True)
    pcm_path = destination / "voice.raw"

    def frame(name):
        xwd = frames / f"scummvm-{name}.xwd"
        subprocess.run(["xwd", "-root", "-silent", "-out", str(xwd)], check=True, timeout=10)
        subprocess.run(["convert", str(xwd), str(frames / f"scummvm-{name}.png")],
                       check=True, timeout=10)
        xwd.unlink()

    def click(x, y):
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                       check=True, timeout=10)
        time.sleep(.2)

    def await_color(name, color):
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited before native interaction")
            frame(name)
            if colored_item_pixels(frames, name, color) >= 40:
                return
            time.sleep(.3)
        raise RuntimeError(f"Native hotspot not observed: {name}")

    def offset():
        return pcm_path.stat().st_size if pcm_path.exists() else 0

    def activity(data):
        return sum(value not in (0, 128) for value in data) / len(data) if data else 0

    with (frames / "scummvm.log").open("w", encoding="utf-8") as log:
        game = subprocess.Popen(["scummvm", f"--path={game_dir.resolve()}", "tentacle"],
            stdout=log, stderr=subprocess.STDOUT,
            env={**os.environ, "SDL_AUDIODRIVER": "disk", "SDL_DISKAUDIOFILE": str(pcm_path)})
        try:
            await_color("harbor", (255, 220, 75))
            time.sleep(2)
            frame("harbor")
            click(234, 563)
            click(*colored_item_center(frames, "harbor", (255, 220, 75)))
            await_color("cellar", RETURN_RGB)
            time.sleep(2)
            frame("cellar")
            baseline_start = offset()
            time.sleep(1)
            baseline_end = offset()
            baseline = activity(pcm_path.read_bytes()[baseline_start:baseline_end])

            def play_voice(label):
                frame("cellar")
                click(234, 563)
                click(*colored_item_center(frames, "cellar", REVEAL_RGB, fuzz_percent=4))
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    if game.poll() is not None:
                        raise RuntimeError("ScummVM exited during native voice")
                    first = offset()
                    time.sleep(.4)
                    last = offset()
                    data = pcm_path.read_bytes() if pcm_path.exists() else b""
                    if last-first >= 8192 and activity(data[first:last]) > baseline + .1:
                        frame(label)
                        return first, last
                raise RuntimeError("No native VOC PCM activity after destination click")

            # First finish the authored interaction without Escape. Require
            # a sustained quiet PCM window, then exercise the same native
            # interaction again to prove it is available after completion.
            normal_heard = play_voice("speaking-normal")
            deadline = time.monotonic() + 25
            normal_quiet = None
            while time.monotonic() < deadline:
                if game.poll() is not None:
                    raise RuntimeError("ScummVM exited during normal native voice completion")
                first = offset()
                time.sleep(1.5)
                last = offset()
                data = pcm_path.read_bytes()
                if last-first >= 8192 and activity(data[first:last]) <= baseline + .05:
                    normal_quiet = (first, last)
                    break
            if normal_quiet is None:
                raise RuntimeError("Native VOC did not return to silence without Escape")
            frame("after-normal")
            heard = play_voice("speaking")
            subprocess.run(["xdotool", "key", "Escape"], check=True, timeout=10)
            time.sleep(1)
            after_start = offset()
            time.sleep(1.5)
            after_end = offset()
            frame("after-escape")
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited after Escape")
        finally:
            game.terminate()
            try:
                game.wait(timeout=5)
            except subprocess.TimeoutExpired:
                game.kill()
                game.wait(timeout=5)
    pcm = pcm_path.read_bytes()
    report = {"before": activity(pcm[baseline_start:baseline_end]),
              "during_normal": activity(pcm[normal_heard[0]:normal_heard[1]]),
              "after_normal": activity(pcm[normal_quiet[0]:normal_quiet[1]]),
              "normal_completed_without_escape": True,
              "replayed_after_normal_completion": True,
              "during": activity(pcm[heard[0]:heard[1]]),
              "after_escape": activity(pcm[after_start:after_end]),
              "pcm_bytes": len(pcm), "escape_sent": True,
              "subtitle_frame": "scummvm-speaking.png"}
    report["native_transferred_actor_voice_audio_verified"] = (
        baseline_end-baseline_start >= 8192 and after_end-after_start >= 8192
        and report["during_normal"] > report["before"] + .1
        and report["during_normal"] > report["after_normal"] + .1
        and report["during"] > report["before"] + .1
        and report["during"] > report["after_escape"] + .1)
    (destination / "report.json").write_text(json.dumps(report, indent=2))
    if not report["native_transferred_actor_voice_audio_verified"]:
        raise RuntimeError(f"Native transferred Actor VOC not audible/stopped: {report}")
    return report


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
