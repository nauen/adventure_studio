"""R09: native Save/Load must preserve the *reopened* authored door route.

Uses a stock ScummVM save slot made after three real inventory Use operations,
then starts a fresh stock interpreter. No edits to saves, game files or engine.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

from .scumm_launch import (close_rgb, door_pixels, open_door_center,
                           door_center, scene_pixel)


def verify_loaded_gate_routes(loaded_open: list[float], loaded_closed: list[float],
                              reference_open: list[float], reference_closed: list[float],
                              always_open: list[float]) -> dict:
    """Reject stale/default BOX flags even when the door sprite was restored."""
    groups = (loaded_open, loaded_closed, reference_open, reference_closed, always_open)
    if any(len(group) != 9 for group in groups):
        raise ValueError("Native gate Save/Load needs nine aligned Actor samples per route")
    loaded_open_deltas = [abs(a - b) for a, b in zip(loaded_open, reference_open)]
    control_deltas = [abs(a - b) for a, b in zip(loaded_open, always_open)]
    closed_deltas = [abs(a - b) for a, b in zip(loaded_closed, reference_closed)]
    detour = [a - b for a, b in zip(loaded_closed, always_open)]
    if max(loaded_open_deltas) > 22 or max(control_deltas) > 22:
        raise RuntimeError("Loaded open gate did not preserve native shortcut: "
                           f"{loaded_open_deltas}, control={control_deltas}")
    # The first six frames capture the same routed detour in both native
    # runs. The final frames can diverge after reaching different camera
    # positions, so their absolute Y values are not time-aligned evidence.
    # The open control must still be distinctly lower in at least five
    # measured frames; never accept a post-load shortcut as a detour.
    if max(closed_deltas[:6]) > 22 or sum(x >= 18 for x in detour[:6]) < 5:
        raise RuntimeError("Post-load Use did not restore blocked native detour: "
                           f"closed={closed_deltas}, control={detour}")
    return {"native_gate_save_load_routes_passed": True,
            "loaded_open_vs_reopened_deltas": loaded_open_deltas,
            "loaded_open_vs_always_open_deltas": control_deltas,
            "loaded_closed_vs_initial_closed_deltas": closed_deltas,
            "loaded_closed_vs_always_open_deltas": detour}


def verify_reversible_gate_save_load(game: Path, original: Path,
                                     control: Path, output: Path) -> dict:
    # Pillow is required only for the native screenshot probe, not core tests.
    from .scumm_dynamic_walkbox_gate_probe import actor_y_in_native_frame
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("Native R09 Save/Load requires Xvfb DISPLAY")
    save_report = original / "scummvm-native-gate-save-report.json"
    if not save_report.is_file():
        raise RuntimeError("No save created by the real reversible-gate gameplay")
    save = json.loads(save_report.read_text(encoding="utf-8"))
    if (save.get("saved_gate_state") != "open-after-reopen"
            or save.get("saved_actor_endpoint") != "left"):
        raise RuntimeError("Save is not the third-Use reopened native gate")
    saves = original / "native-gate-saves"
    slot = saves / "tentacle.s01"
    if not slot.is_file() or slot.stat().st_size == 0:
        raise RuntimeError("Native ScummVM save slot not found")
    if any(not (game / f"tentacle.{part}").is_file() for part in ("000", "001")):
        raise RuntimeError("Missing exported native reversible-gate game")

    output.mkdir(parents=True, exist_ok=True)
    environment = {**os.environ, "SDL_AUDIODRIVER": "dummy"}
    log = (output / "scummvm-load.log").open("w", encoding="utf-8")
    try:
        process = subprocess.Popen(
            ["scummvm", "--debuglevel=3", f"--savepath={saves.resolve()}",
             f"--path={game.resolve()}", "--save-slot=1", "tentacle"],
            env=environment, stdout=log, stderr=subprocess.STDOUT)
    finally:
        log.close()

    def capture(label: str) -> Path:
        raw = output / f"scummvm-{label}.xwd"
        png = output / f"scummvm-{label}.png"
        subprocess.run(["xwd", "-root", "-silent", "-out", str(raw)],
                       check=True, timeout=10)
        subprocess.run(["convert", str(raw), str(png)], check=True, timeout=10)
        return png

    def click(x: int, y: int) -> None:
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                       check=True, timeout=10)

    def travel_left() -> None:
        for _ in range(3):
            click(220, 390)
            time.sleep(5)

    def measure_route(prefix: str) -> list[float]:
        click(790, 390)
        samples = []
        for index in range(9):
            time.sleep(0.4)
            samples.append(actor_y_in_native_frame(
                capture(f"{prefix}-{index:02d}")))
        time.sleep(5)
        capture(f"{prefix}-far")
        return samples

    try:
        time.sleep(6)
        if process.poll() is not None:
            raise RuntimeError("Stock ScummVM exited while loading R09 save")
        capture("after-load")
        if not close_rgb(scene_pixel(output, "after-load"), (70, 130, 190)):
            raise RuntimeError("R09 Save/Load failed to restore the Harbor room")
        # Native gameplay proof: loaded open shortcut, not only an open sprite.
        loaded_open = measure_route("loaded-open")
        # The actor is still travelling toward the far target when the
        # nine route samples finish. The Door is then beyond the camera edge,
        # so probing the far-route screenshot reports zero pixels for both
        # states. Finish the same genuine in-game approach used in the
        # reversible R09 probe; only inspect the Door once it is on screen.
        for _ in range(3):
            click(790, 390)
            time.sleep(5)
        capture("loaded-open-door-approach")
        opened_pixels = door_pixels(output, "loaded-open-door-approach", open_state=True)
        closed_pixels = door_pixels(output, "loaded-open-door-approach")
        if opened_pixels < 40 or closed_pixels >= 10:
            raise RuntimeError(
                "Saved reopened gate did not restore its visible door object state: "
                f"open={opened_pixels}, closed={closed_pixels}")

        # The inventory key must still be usable after a fresh interpreter load.
        # Toggle that restored state to CLOSED, then measure its real detour.
        x, y = open_door_center(output, "loaded-open-door-approach")
        for cx, cy in ((408, 506), (552, 520), (x, y)):
            click(cx, cy)
            time.sleep(0.3)
        deadline = time.monotonic() + 14
        while time.monotonic() < deadline:
            capture("post-load-close")
            if (door_pixels(output, "post-load-close") >= 40
                    and door_pixels(output, "post-load-close", open_state=True) < 10):
                break
            time.sleep(0.35)
        else:
            raise RuntimeError("Use Key with Door failed after loading saved open gate")
        travel_left()
        loaded_closed = measure_route("loaded-closed")
        if process.poll() is not None:
            raise RuntimeError("Stock ScummVM exited before post-load detour completed")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    reference_open = [
        actor_y_in_native_frame(original / f"scummvm-gate-open-2-sample-{i:02d}.png")
        for i in range(9)]
    reference_closed = [
        actor_y_in_native_frame(original / f"scummvm-sample-{i:02d}.png")
        for i in range(9, 18)]
    always_open = [
        actor_y_in_native_frame(control / f"scummvm-sample-{i:02d}.png")
        for i in range(9, 18)]
    metrics = verify_loaded_gate_routes(loaded_open, loaded_closed, reference_open,
                                        reference_closed, always_open)
    report = {"native_save_slot": "tentacle.s01",
              "stock_scummvm_restarted_with_save_slot": True,
              "saved_object_state": "reopened", "loaded_object_state": "open",
              "loaded_inventory_use_closes_gate": True,
              "route_metrics": metrics}
    (output / "native-r09-gate-save-load-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
