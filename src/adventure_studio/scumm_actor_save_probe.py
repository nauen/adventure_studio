"""Native ScummVM save/reload acceptance for an authored Actor COUNT puzzle."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from .scumm_launch import (close_rgb, colored_item_center, colored_item_pixels,
                           door_center, scene_pixel)
from .scumm_save_load_probe import open_native_global_menu, verify_global_menu_ready


def verify_actor_state(state: dict, phase: str) -> None:
    """Fail closed if a saved puzzle state or COUNT replay differs."""
    if state["key_pixels"] >= 10 or state["open_door_pixels"] < 40:
        raise RuntimeError(f"Actor puzzle state differs at {phase}: {state}")


def run_actor_save_probe(game: Path, output: Path) -> dict:
    """Save the late-input outcome, restart ScummVM and prove restored state."""
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("Actor save probe requires Xvfb DISPLAY")
    if any(not (game / f"tentacle.{part}").is_file() for part in ("000", "001")):
        raise ValueError("Missing native Actor game")
    output.mkdir(parents=True, exist_ok=True)
    saves = output / "saves"
    saves.mkdir(exist_ok=True)
    environment = {**os.environ, "SDL_AUDIODRIVER": "dummy"}

    def capture(name: str) -> None:
        raw = output / f"{name}.xwd"
        subprocess.run(["xwd", "-root", "-silent", "-out", str(raw)],
                       check=True, stdout=subprocess.DEVNULL, timeout=10)
        subprocess.run(["convert", str(raw), str(output / f"{name}.png")],
                       check=True, stdout=subprocess.DEVNULL, timeout=10)

    def click(x: int, y: int) -> None:
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                       check=True, timeout=10)

    def start(slot: int | None = None) -> subprocess.Popen:
        args = ["scummvm", f"--savepath={saves.resolve()}",
                f"--path={game.resolve()}"]
        if slot is not None:
            args.append(f"--save-slot={slot}")
        args.append("tentacle")
        log = (output / ("load.log" if slot else "save.log")).open("w", encoding="utf-8")
        # The subprocess owns its log descriptor after Popen duplicates it.
        try:
            return subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT,
                                    env=environment)
        finally:
            log.close()

    def stop(process: subprocess.Popen) -> None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    def state(name: str) -> dict:
        capture(name)
        return {"key_pixels": colored_item_pixels(output, name, (255, 220, 75)),
                "open_door_pixels": colored_item_pixels(output, name, (50, 220, 220))}

    process = start()
    try:
        deadline = time.monotonic() + 18
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("ScummVM exited before Actor COUNT")
            capture("initial")
            if colored_item_pixels(output, "initial", (50, 220, 220)) >= 40:
                break
            time.sleep(0.15)
        else:
            raise RuntimeError("Actor COUNT never opened the door")
        key_x, key_y = colored_item_center(output, "initial", (255, 220, 75))
        time.sleep(6)
        click(392, 524)  # Native Road Push verb.
        click(key_x, key_y)
        time.sleep(3)
        before = state("before-save")
        verify_actor_state(before, "before save")

        open_native_global_menu()
        time.sleep(2)
        capture("save-menu")
        verify_global_menu_ready(output / "save-menu.png")
        click(512, 367)  # Native ScummVM Save button.
        time.sleep(2)
        click(298, 285)  # New Save tile.
        time.sleep(2)
        subprocess.run(["xdotool", "type", "--clearmodifiers", "--delay", "60",
                        "Actor COUNT persistence"], check=True, timeout=15)
        click(618, 414)  # Confirm save name.
        time.sleep(3)
        slot = saves / "tentacle.s01"
        if not slot.is_file() or slot.stat().st_size == 0:
            raise RuntimeError("Native ScummVM save slot was not created")
    finally:
        stop(process)

    process = start(slot=1)
    try:
        time.sleep(6)
        if process.poll() is not None:
            raise RuntimeError("ScummVM exited before Actor save could load")
        loaded = state("after-load")
        verify_actor_state(loaded, "after load")
        door_x, door_y = colored_item_center(output, "after-load", (50, 220, 220))
        click(door_x - 12, door_y - 12)
        deadline = time.monotonic() + 16
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("ScummVM stopped before loaded-state Cellar transition")
            capture("cellar-after-load")
            if close_rgb(scene_pixel(output, "cellar-after-load"), (120, 70, 180)):
                break
            time.sleep(0.3)
        else:
            raise RuntimeError("Loaded door did not lead to Cellar")
        time.sleep(1)
        capture("stairs-after-load")
        stairs_x, stairs_y = door_center(output, "stairs-after-load")
        click(stairs_x, stairs_y)
        deadline = time.monotonic() + 16
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("ScummVM stopped before loaded-state Harbor return")
            capture("harbor-after-load")
            if close_rgb(scene_pixel(output, "harbor-after-load"), (240, 175, 95)):
                break
            time.sleep(0.3)
        else:
            raise RuntimeError("Loaded Stairs did not lead to Harbor")
        time.sleep(5)
        returned = state("after-loaded-return")
        verify_actor_state(returned, "after loaded room return")
    finally:
        stop(process)
    report = {"native_actor_save_created": True,
              "native_actor_state_restored": True,
              "native_actor_initial_guard_survives_save_load": True,
              "before_save": before, "after_load": loaded,
              "after_loaded_return": returned}
    (output / "actor-save-report.json").write_text(json.dumps(report, indent=2) + "\n",
                                                   encoding="utf-8")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_actor_save_probe GAME OUTPUT")
    print(json.dumps(run_actor_save_probe(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
