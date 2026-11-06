"""Exercise ScummVM's native save dialog and independently reload a saved room."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from adventure_studio.scumm_language_runtime_probe import (
    compare_screenshots, verify_capture_visible, verify_room_transition,
)


def verify_save_menu_open(before: Path, after: Path) -> dict:
    """Require a substantial visual change; does not recognize menu labels."""
    menu_change = compare_screenshots(before, after)
    if menu_change["changed_ratio"] < 0.02:
        raise ValueError("Ctrl+F5 did not visibly open a menu; refusing Save/Load claims")
    return menu_change


def verify_global_menu_ready(path: Path) -> dict:
    """Recognize the actual ScummVM 2.8 main menu, not a transient overlay."""
    from PIL import Image

    with Image.open(path) as screenshot:
        rgb = screenshot.convert("RGB")
        if rgb.size != (1024, 768):
            raise ValueError("Unexpected ScummVM menu display dimensions")
        # The left half of the orange GMM panel covers this rectangle.
        # The game background here is blue, so it cannot satisfy the gate.
        crop = rgb.crop((395, 210, 500, 550))
        pixels = (crop.get_flattened_data() if hasattr(crop, "get_flattened_data")
                  else crop.getdata())
        orange = sum(1 for r, g, b in pixels if 170 <= r <= 240 and 60 <= g <= 160 and b < 40)
        if orange < 12000:
            raise ValueError("ScummVM global main menu not fully rendered")
        return {"orange_panel_pixels": orange, "menu_rendered": True}


def verify_loaded_room(reference: Path, initial: Path, loaded: Path) -> dict:
    """Require the loaded screenshot to resemble the saved room, not the bootstrap."""
    saved_comparison = compare_screenshots(reference, loaded)
    initial_comparison = compare_screenshots(initial, loaded)
    if saved_comparison["changed_ratio"] > 0.08:
        raise ValueError("Loaded room differs substantially from saved room")
    if initial_comparison["changed_ratio"] < 0.05:
        raise ValueError("Loaded room still resembles the initial bootstrap")
    return {"saved_room_pixel_difference": saved_comparison,
            "initial_room_pixel_difference": initial_comparison,
            "load_restored_room_verified": True}


def save_load_menu_probe(game: Path, output: Path, select_polish: bool = True) -> dict:
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("Save/load probe requires Xvfb DISPLAY")
    if any(not (game / f"tentacle.{suffix}").is_file() for suffix in ("000", "001")):
        raise ValueError("Missing SCUMM game data")

    output.mkdir(parents=True, exist_ok=True)
    save_path = output / "isolated-saves"
    save_path.mkdir(exist_ok=True)
    config_path = output / "isolated-scummvm.ini"
    log_path = output / "scummvm-save-menu.log"
    environment = {**os.environ, "SDL_AUDIODRIVER": "dummy"}

    def capture(name: str, require_global_menu: bool = False) -> None:
        raw = output / f"{name}.xwd"
        png = output / f"{name}.png"
        for attempt in range(4):
            subprocess.run(["xwd", "-root", "-silent", "-out", str(raw)],
                           check=True, timeout=10)
            subprocess.run(["convert", str(raw), str(png)], check=True, timeout=10)
            try:
                verify_capture_visible(png)
                if require_global_menu:
                    verify_global_menu_ready(png)
                return
            except ValueError:
                if attempt == 3:
                    raise
                time.sleep(2)

    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen([
            "scummvm", f"--config={config_path.resolve()}",
            f"--savepath={save_path.resolve()}", f"--path={game.resolve()}", "tentacle",
        ], stdout=log, stderr=subprocess.STDOUT, env=environment)
        try:
            time.sleep(5)
            if process.poll() is not None:
                raise RuntimeError("ScummVM exited before save-menu probe")
            if select_polish:
                subprocess.run(["xdotool", "key", "5"], check=True, timeout=10)
                time.sleep(2)
                capture("polish-in-initial-room")
                subprocess.run(["xdotool", "key", "0"], check=True, timeout=10)
                time.sleep(2)
            capture("polish-before-menu")
            for menu_attempt in range(3):
                subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+F5"],
                               check=True, timeout=10)
                time.sleep(2)
                if process.poll() is not None:
                    raise RuntimeError("ScummVM exited after Ctrl+F5")
                try:
                    capture("save-menu-after-ctrl-f5", require_global_menu=True)
                    break
                except ValueError:
                    if menu_attempt == 2:
                        raise RuntimeError("Native ScummVM menu unavailable after three openings")
                    subprocess.run(["xdotool", "key", "Escape"], check=True, timeout=10)
                    time.sleep(2)
            # Coordinates measured from the real ScummVM 2.8 GMM capture.
            subprocess.run(["xdotool", "mousemove", "512", "367", "click", "1"],
                           check=True, timeout=10)
            time.sleep(2)
            if process.poll() is not None:
                raise RuntimeError("ScummVM exited after Save button click")
            capture("save-dialog-after-click")
            # The real ScummVM 2.8 save picker shows a New Save tile at
            # x=215..382, y=224..350 on our fixed 1024x768 Xvfb display.
            subprocess.run(["xdotool", "mousemove", "298", "285", "click", "1"],
                           check=True, timeout=10)
            time.sleep(2)
            if process.poll() is not None:
                raise RuntimeError("ScummVM exited after selecting New Save")
            capture("after-new-save-click")
            subprocess.run(["xdotool", "type", "--clearmodifiers", "--delay", "60",
                            "Adventure Studio CI"], check=True, timeout=15)
            subprocess.run(["xdotool", "mousemove", "618", "414", "click", "1"],
                           check=True, timeout=10)
            time.sleep(3)
            if process.poll() is not None:
                raise RuntimeError("ScummVM exited after confirming save name")
            capture("after-save-confirmation")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    menu_change = verify_save_menu_open(output / "polish-before-menu.png",
                                        output / "save-menu-after-ctrl-f5.png")
    room_change = (verify_room_transition(output / "polish-in-initial-room.png",
                                          output / "polish-before-menu.png") if select_polish else None)
    ready = verify_global_menu_ready(output / "save-menu-after-ctrl-f5.png")
    save_dialog_change = verify_save_menu_open(output / "save-menu-after-ctrl-f5.png",
                                               output / "save-dialog-after-click.png")
    saves = sorted(path.name for path in save_path.iterdir()
                   if path.is_file() and path.stat().st_size > 0)
    slot_one = save_path / "tentacle.s01"
    load_evidence = None
    load_error = None
    if select_polish and slot_one.is_file() and slot_one.stat().st_size > 0:
        load_log_path = output / "scummvm-load.log"
        with load_log_path.open("w", encoding="utf-8") as load_log:
            load_process = subprocess.Popen([
                "scummvm", f"--config={config_path.resolve()}",
                f"--savepath={save_path.resolve()}", "--save-slot=1",
                f"--path={game.resolve()}", "tentacle",
            ], stdout=load_log, stderr=subprocess.STDOUT, env=environment)
            try:
                time.sleep(6)
                if load_process.poll() is not None:
                    raise RuntimeError("ScummVM exited before saved slot could be inspected")
                capture("after-loading-slot-1")
                load_evidence = verify_loaded_room(
                    output / "polish-before-menu.png",
                    output / "polish-in-initial-room.png",
                    output / "after-loading-slot-1.png")
            except (RuntimeError, ValueError) as error:
                load_error = str(error)
            finally:
                load_process.terminate()
                try:
                    load_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    load_process.kill()
                    load_process.wait(timeout=5)
    report = {
        "isolated_config": config_path.name,
        "isolated_save_directory": save_path.name,
        "polish_key_sent_before_menu": select_polish,
        "save_attempted_after_room_transition": select_polish,
        "room_transition_evidence": room_change,
        "polish_selection_visually_verified": False,
        "ctrl_f5_sent": True,
        "menu_visibly_changed": True,
        "global_menu_ready": ready,
        "menu_pixel_difference": menu_change,
        "save_button_clicked": True,
        "new_save_clicked": True,
        "save_description_entered": "Adventure Studio CI",
        "save_confirmation_clicked": True,
        "save_dialog_pixel_difference": save_dialog_change,
        "nonblank_screenshots": ["polish-before-menu.png", "save-menu-after-ctrl-f5.png",
                                  "save-dialog-after-click.png", "after-new-save-click.png",
                                  "after-save-confirmation.png"]
                                 + (["polish-in-initial-room.png"] if select_polish else []),
        "save_files_observed": saves,
        "save_created_verified": slot_one.is_file() and slot_one.stat().st_size > 0,
        "load_restored_room_verified": bool(load_evidence),
        "load_room_evidence": load_evidence,
        "load_error": load_error,
        "load_restored_language_verified": False,
        "status": ("save-and-load-room-verified" if load_evidence else
                   "save-created-load-unverified" if slot_one.is_file() else
                   "save-dialog-discovery-only"),
    }
    (output / "save-load-menu-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    if len(sys.argv) not in (3, 4) or (len(sys.argv) == 4 and sys.argv[3] != "--no-polish"):
        print("Usage: python -m adventure_studio.scumm_save_load_probe GAME OUTPUT [--no-polish]")
        return 2
    print(json.dumps(save_load_menu_probe(Path(sys.argv[1]), Path(sys.argv[2]),
                                          select_polish="--no-polish" not in sys.argv[3:]),
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
