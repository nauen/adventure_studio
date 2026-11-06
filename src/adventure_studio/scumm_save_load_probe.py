"""Exercise ScummVM's native save dialog and independently reload a saved room."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
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


def verify_loaded_language_selection(default: Path, selected: Path, loaded: Path) -> dict:
    """Compare the active-language highlight in ScummVM's fixed verb strip."""
    from PIL import Image

    region = (192, 460, 480, 490)
    with tempfile.TemporaryDirectory() as directory:
        crops = []
        for index, screenshot in enumerate((default, selected, loaded)):
            with Image.open(screenshot) as image:
                if image.size != (1024, 768):
                    raise ValueError("Unexpected screenshot size for language selection")
                crop = Path(directory) / f"language-{index}.png"
                image.convert("RGB").crop(region).save(crop)
                crops.append(crop)
        selection_change = compare_screenshots(crops[0], crops[1])
        restored_change = compare_screenshots(crops[1], crops[2])
    if selection_change["changed_pixels"] < 20:
        raise ValueError("Language highlight did not visibly change from default")
    if restored_change["changed_pixels"] > 20:
        raise ValueError("Language highlight not restored after loading")
    return {"language_selection_pixel_difference": selection_change,
            "language_restore_pixel_difference": restored_change,
            "load_restored_language_verified": True}


def save_load_menu_probe(game: Path, output: Path, select_polish: bool = True,
                         debug_save_state: bool = False) -> dict:
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
                capture("before-polish-selection")
                subprocess.run(["xdotool", "key", "5"], check=True, timeout=10)
                time.sleep(2)
                capture("polish-in-initial-room")
                subprocess.run(["xdotool", "key", "0"], check=True, timeout=10)
                time.sleep(2)
            capture("polish-before-menu")
            if debug_save_state:
                # ScummVM 2.8 registers these two read-only debugger queries.
                # For v6, scumm_vars[65] is VAR_MAINMENU_KEY (expected 319).
                subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+alt+d"],
                               check=True, timeout=10)
                time.sleep(2)
                for command in ("scumm_room", "scumm_vars[65]"):
                    subprocess.run(["xdotool", "type", "--clearmodifiers",
                                    "--delay", "80", command], check=True, timeout=15)
                    subprocess.run(["xdotool", "key", "Return"], check=True, timeout=10)
                    time.sleep(1)
                capture("scumm-save-gate-debugger")
                subprocess.run(["xdotool", "type", "--clearmodifiers", "exit"],
                               check=True, timeout=10)
                subprocess.run(["xdotool", "key", "Return"], check=True, timeout=10)
                time.sleep(2)
            save_attempts = 0
            save_attempt_screenshots = []
            for save_attempt in range(3 if select_polish else 1):
                save_attempts += 1
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
                attempt_image = f"after-save-confirmation-attempt-{save_attempts}.png"
                shutil.copyfile(output / "after-save-confirmation.png", output / attempt_image)
                save_attempt_screenshots.append(attempt_image)
                slot = save_path / "tentacle.s01"
                if slot.is_file() and slot.stat().st_size > 0:
                    break
                if save_attempt < 2 and select_polish:
                    # The engine may temporarily reject saves during scripted
                    # transitions. Dismiss its warning and retry after settling.
                    subprocess.run(["xdotool", "mousemove", "512", "396", "click", "1"],
                                   check=True, timeout=10)
                    time.sleep(1)
                    subprocess.run(["xdotool", "key", "Escape"], check=True, timeout=10)
                    time.sleep(6)
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
    language_load_evidence = None
    language_load_error = None
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
                try:
                    language_load_evidence = verify_loaded_language_selection(
                        output / "before-polish-selection.png",
                        output / "polish-before-menu.png",
                        output / "after-loading-slot-1.png")
                except ValueError as error:
                    language_load_error = str(error)
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
        "debug_save_state_requested": debug_save_state,
        "debug_save_state_screenshot": ("scumm-save-gate-debugger.png"
                                         if debug_save_state else None),
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
        "save_attempts": save_attempts,
        "save_attempt_screenshots": save_attempt_screenshots,
        "save_attempts_without_slot": (save_attempts - 1 if slot_one.is_file() else
                                       save_attempts),
        "save_dialog_pixel_difference": save_dialog_change,
        "nonblank_screenshots": ["polish-before-menu.png", "save-menu-after-ctrl-f5.png",
                                  "save-dialog-after-click.png", "after-new-save-click.png",
                                  "after-save-confirmation.png"]
                                 + (["before-polish-selection.png", "polish-in-initial-room.png"]
                                    if select_polish else [])
                                 + (["after-loading-slot-1.png"] if load_evidence else []),
        "save_files_observed": saves,
        "save_created_verified": slot_one.is_file() and slot_one.stat().st_size > 0,
        "load_restored_room_verified": bool(load_evidence),
        "load_room_evidence": load_evidence,
        "load_error": load_error,
        "load_restored_language_verified": bool(language_load_evidence),
        "load_language_evidence": language_load_evidence,
        "load_language_error": language_load_error,
        "status": ("save-load-room-and-language-verified" if language_load_evidence else
                   "save-and-load-room-verified" if load_evidence else
                   "save-created-load-unverified" if slot_one.is_file() else
                   "save-dialog-discovery-only"),
    }
    (output / "save-load-menu-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    options = sys.argv[3:]
    if len(sys.argv) < 3 or len(set(options)) != len(options) or any(
            option not in ("--no-polish", "--debug-save-state") for option in options):
        print("Usage: python -m adventure_studio.scumm_save_load_probe GAME OUTPUT [--no-polish] [--debug-save-state]")
        return 2
    print(json.dumps(save_load_menu_probe(Path(sys.argv[1]), Path(sys.argv[2]),
                                          select_polish="--no-polish" not in options,
                                          debug_save_state="--debug-save-state" in options),
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
