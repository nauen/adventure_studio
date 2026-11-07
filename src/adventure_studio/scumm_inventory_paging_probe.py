"""Exercise both SCUMM inventory arrows with nine real collected objects."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from .scumm_inventory_paging_demo import INVENTORY_COLORS
from .scumm_launch import (close_rgb, colored_item_center, colored_item_pixels,
                           scene_pixel)


def verify_inventory_paging(game: Path, output: Path) -> None:
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("Inventory paging probe needs a virtual X display")
    output.mkdir(parents=True, exist_ok=True)

    def capture(label: str) -> None:
        raw = output / f"scummvm-{label}.xwd"
        png = output / f"scummvm-{label}.png"
        subprocess.run(["xwd", "-root", "-silent", "-out", str(raw)],
                       check=True, timeout=10, capture_output=True)
        subprocess.run(["convert", str(raw), str(png)],
                       check=True, timeout=10, capture_output=True)

    def click(x: int, y: int) -> None:
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                       check=True, timeout=5, capture_output=True)

    with (output / "scummvm.log").open("w", encoding="utf-8") as logfile:
        process = subprocess.Popen(["scummvm", f"--path={game.resolve()}", "tentacle"],
                                   stdout=logfile, stderr=subprocess.STDOUT,
                                   env={**os.environ, "SDL_AUDIODRIVER": "dummy"})
        try:
            ready_by = time.monotonic() + 25
            while time.monotonic() < ready_by:
                if process.poll() is not None:
                    raise RuntimeError("ScummVM exited before inventory probe started")
                capture("start")
                if close_rgb(scene_pixel(output, "start"), (70, 130, 190)):
                    break
                time.sleep(0.4)
            else:
                raise RuntimeError("Inventory probe room did not become visible")
            time.sleep(8)
            pickup_history = []
            for index, color in enumerate(INVENTORY_COLORS):
                rgb = tuple(color)
                click(328, 506)  # Stock PickUp verb.
                time.sleep(0.3)
                frame = f"paging-before-{index}"
                capture(frame)
                if colored_item_pixels(output, frame, rgb) < 40:
                    raise RuntimeError(f"Inventory item {index} not visible in the room")
                x, y = colored_item_center(output, frame, rgb, fuzz_percent=0)
                click(x, y)
                acquired = False
                pickup_started = time.monotonic()
                retried = False
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    frame = f"paging-picked-{index}"
                    capture(frame)
                    if colored_item_pixels(output, frame, rgb) < 10:
                        acquired = True
                        break
                    if not retried and time.monotonic() - pickup_started >= 7:
                        retried = True
                        click(328, 506)
                        time.sleep(0.35)
                        capture(frame)
                        retry_x, retry_y = colored_item_center(output, frame, rgb, fuzz_percent=0)
                        click(retry_x, retry_y)
                    time.sleep(0.35)
                if not acquired:
                    (output / "scummvm-pickup-history.json").write_text(
                        json.dumps({"completed": pickup_history, "failed_index": index,
                                    "last_click": [x, y], "retried": retried,
                                    "remaining_pixels": colored_item_pixels(output, frame, rgb)},
                                   indent=2) + "\n", encoding="utf-8")
                    raise RuntimeError(f"Inventory item {index} was not picked up")
                pickup_history.append({"item": index, "click": [x, y], "retried": retried})
                # The SCUMM sentence thread and actor movement may still be
                # finishing even after the object has left the room image.
                time.sleep(2)
            capture("paging-first-page")
            first_visible = colored_item_pixels(output, "paging-first-page", INVENTORY_COLORS[0],
                                                inventory=True) >= 40
            ninth_hidden = colored_item_pixels(output, "paging-first-page", INVENTORY_COLORS[8],
                                               inventory=True) < 10
            click(478, 558)  # Stock inventory Down arrow, logical (135,182).
            time.sleep(0.8)
            capture("paging-next-page")
            ninth_visible = colored_item_pixels(output, "paging-next-page", INVENTORY_COLORS[8],
                                                inventory=True) >= 40
            click(478, 514)  # Stock inventory Up arrow, logical (135,160).
            time.sleep(0.8)
            capture("paging-return-page")
            first_restored = colored_item_pixels(output, "paging-return-page", INVENTORY_COLORS[0],
                                                 inventory=True) >= 40
            checks = {"picked_up": len(INVENTORY_COLORS), "first_visible": first_visible,
                      "ninth_hidden_on_first_page": ninth_hidden, "ninth_visible_after_down": ninth_visible,
                      "first_restored_after_up": first_restored}
            (output / "scummvm-inventory-paging-report.json").write_text(
                json.dumps(checks, indent=2) + "\n", encoding="utf-8")
            if not all((first_visible, ninth_hidden, ninth_visible, first_restored)):
                raise RuntimeError(f"Inventory arrow paging failed: {checks}")
            print("Nine inventory objects collected; both native inventory page arrows worked")
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.scumm_inventory_paging_probe GAME_DIRECTORY OUTPUT_DIRECTORY")
        return 2
    verify_inventory_paging(Path(sys.argv[1]), Path(sys.argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
