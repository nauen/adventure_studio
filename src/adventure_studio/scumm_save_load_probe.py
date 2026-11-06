"""Collect real ScummVM save-menu evidence without claiming a save/load pass.

The first gate discovers the menu layout in an isolated ScummVM session.
It intentionally does not guess save-slot click coordinates.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from adventure_studio.scumm_language_runtime_probe import (
    compare_screenshots, verify_capture_visible,
)


def verify_save_menu_open(before: Path, after: Path) -> dict:
    """Require a substantial visual change; does not recognize menu labels."""
    menu_change = compare_screenshots(before, after)
    if menu_change["changed_ratio"] < 0.02:
        raise ValueError("Ctrl+F5 did not visibly open a menu; refusing Save/Load claims")
    return menu_change


def save_load_menu_probe(game: Path, output: Path) -> dict:
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

    def capture(name: str) -> None:
        raw = output / f"{name}.xwd"
        png = output / f"{name}.png"
        for attempt in range(4):
            subprocess.run(["xwd", "-root", "-silent", "-out", str(raw)],
                           check=True, timeout=10)
            subprocess.run(["convert", str(raw), str(png)], check=True, timeout=10)
            try:
                verify_capture_visible(png)
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
            subprocess.run(["xdotool", "key", "5"], check=True, timeout=10)
            time.sleep(2)
            capture("polish-before-menu")
            subprocess.run(["xdotool", "key", "ctrl+F5"], check=True, timeout=10)
            time.sleep(2)
            if process.poll() is not None:
                raise RuntimeError("ScummVM exited after Ctrl+F5")
            capture("save-menu-after-ctrl-f5")
            # Inspect the alternative engine menu independently. Do not
            # infer controls from the broken-font Ctrl+F5 screenshot.
            subprocess.run(["xdotool", "key", "Escape"], check=True, timeout=10)
            time.sleep(1)
            capture("after-escape")
            subprocess.run(["xdotool", "key", "F5"], check=True, timeout=10)
            time.sleep(2)
            if process.poll() is not None:
                raise RuntimeError("ScummVM exited after F5")
            capture("menu-after-f5")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    menu_change = verify_save_menu_open(output / "polish-before-menu.png",
                                        output / "save-menu-after-ctrl-f5.png")
    alternative_menu = compare_screenshots(output / "after-escape.png",
                                           output / "menu-after-f5.png")
    saves = sorted(path.name for path in save_path.iterdir() if path.is_file())
    report = {
        "isolated_config": config_path.name,
        "isolated_save_directory": save_path.name,
        "polish_key_sent_before_menu": True,
        "polish_selection_visually_verified": False,
        "ctrl_f5_sent": True,
        "menu_visibly_changed": True,
        "menu_pixel_difference": menu_change,
        "f5_menu_pixel_difference": alternative_menu,
        "f5_menu_legibility_verified": False,
        "nonblank_screenshots": ["polish-before-menu.png", "save-menu-after-ctrl-f5.png",
                                  "after-escape.png", "menu-after-f5.png"],
        "save_files_observed": saves,
        "save_created_verified": False,
        "load_restored_room_verified": False,
        "load_restored_language_verified": False,
        "status": "menu-discovery-only",
    }
    (output / "save-load-menu-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.scumm_save_load_probe GAME OUTPUT")
        return 2
    print(json.dumps(save_load_menu_probe(Path(sys.argv[1]), Path(sys.argv[2])),
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
