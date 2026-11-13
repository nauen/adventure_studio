"""Native R09: a reversible door route survives real room exit and reentry.

All game resources originate in the Studio room model and productive ScummC
export. The probe only drives an unchanged stock ScummVM game with real clicks.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from .scumm_launch import (close_rgb, colored_item_center, colored_item_pixels,
                           door_pixels, open_door_center, scene_pixel)


def verify_return_routes(open_route: list[float], closed_route: list[float],
                         opened_reference: list[float], closed_reference: list[float],
                         always_open: list[float]) -> dict:
    """Reject a sprite-only return or a route that silently resets BOXM flags."""
    paths = (open_route, closed_route, opened_reference, closed_reference, always_open)
    if any(len(path) != 9 for path in paths):
        raise ValueError("Native room-return routes require nine aligned actor frames")
    open_diffs = [abs(a - b) for a, b in zip(open_route, opened_reference)]
    control_diffs = [abs(a - b) for a, b in zip(open_route, always_open)]
    closed_diffs = [abs(a - b) for a, b in zip(closed_route, closed_reference)]
    detour = [a - b for a, b in zip(closed_route, always_open)]
    # After six frames the native camera can reach a different scroll phase.
    if max(open_diffs[:6]) > 22 or max(control_diffs[:6]) > 22:
        raise RuntimeError(f"Open gate shortcut lost on room return: {open_diffs}, {control_diffs}")
    if max(closed_diffs[:6]) > 22 or sum(delta >= 18 for delta in detour[:6]) < 5:
        raise RuntimeError(f"Closed gate detour lost on room return: {closed_diffs}, {detour}")
    return {"native_gate_room_return_routes_passed": True,
            "open_vs_reopened": open_diffs,
            "open_vs_always_open": control_diffs,
            "closed_vs_reclosed": closed_diffs,
            "closed_vs_always_open": detour}


def verify_native_gate_room_return(report: dict, frames: Path, control: Path) -> dict:
    from .scumm_dynamic_walkbox_gate_probe import actor_y_in_native_frame
    if report.get("native_room_transitions") != [
            "Harbor->Cellar->Harbor (open)",
            "Harbor->Cellar->Harbor (closed)"]:
        raise RuntimeError("Two native room exit/reentry cycles are required")
    if not all(report.get(key) is True for key in (
            "returned_open_door_verified", "returned_closed_door_verified",
            "post_return_use_closed_gate")):
        raise RuntimeError("Native returned gate object state or Use interaction missing")
    for key, prefix in (("open_samples", "room-open-sample-"),
                        ("closed_samples", "room-closed-sample-")):
        if report.get(key) != [f"{prefix}{i:02d}" for i in range(9)]:
            raise RuntimeError(f"Missing ordered native {key} screenshots")
    return verify_return_routes(
        [actor_y_in_native_frame(frames / f"scummvm-{name}.png")
         for name in report["open_samples"]],
        [actor_y_in_native_frame(frames / f"scummvm-{name}.png")
         for name in report["closed_samples"]],
        [actor_y_in_native_frame(frames / f"scummvm-gate-open-2-sample-{i:02d}.png")
         for i in range(9)],
        [actor_y_in_native_frame(frames / f"scummvm-gate-closed-1-sample-{i:02d}.png")
         for i in range(9)],
        [actor_y_in_native_frame(control / f"scummvm-sample-{i:02d}.png")
         for i in range(9, 18)])


def play_native_gate_room_return(output: Path, capture, process,
                                 inventory_center: tuple[int, int]) -> None:
    """Use ordinary Passage/Stairs WalkTo hotspots twice, then measure routes."""
    portal_rgb = (175, 60, 210)
    cellar_rgb = (120, 70, 180)
    stairs_rgb = (60, 220, 90)

    def click(x: int, y: int) -> None:
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                       check=True, timeout=5)

    def change_room(state: str) -> None:
        capture(f"room-{state}-before-exit")
        if colored_item_pixels(output, f"room-{state}-before-exit", portal_rgb) < 40:
            for _ in range(3):
                click(790, 390)
                time.sleep(5)
            capture(f"room-{state}-before-exit")
        x, y = colored_item_center(output, f"room-{state}-before-exit",
                                   portal_rgb, fuzz_percent=4)
        click(x, y)
        for _ in range(45):
            label = f"room-{state}-cellar"
            capture(label)
            if close_rgb(scene_pixel(output, label), cellar_rgb):
                break
            if process.poll() is not None:
                raise RuntimeError("Stock ScummVM exited during room transition")
            time.sleep(0.4)
        else:
            raise RuntimeError(f"Passage did not enter Cellar: {state}")
        capture(f"room-{state}-stairs")
        x, y = colored_item_center(output, f"room-{state}-stairs",
                                   stairs_rgb, fuzz_percent=4)
        click(x, y)
        for _ in range(45):
            label = f"room-{state}-back"
            capture(label)
            if close_rgb(scene_pixel(output, label), (70, 130, 190)):
                break
            if process.poll() is not None:
                raise RuntimeError("Stock ScummVM exited on return to Harbor")
            time.sleep(0.4)
        else:
            raise RuntimeError(f"Stairs did not return to Harbor: {state}")

    def sample_route(state: str) -> list[str]:
        for _ in range(3):
            click(220, 390)
            time.sleep(5)
        capture(f"room-{state}-left")
        click(790, 390)
        labels = []
        for i in range(9):
            time.sleep(0.4)
            label = f"room-{state}-sample-{i:02d}"
            capture(label)
            labels.append(label)
        for _ in range(3):
            click(790, 390)
            time.sleep(5)
        label = f"room-{state}-door"
        capture(label)
        opened = door_pixels(output, label, open_state=True)
        closed = door_pixels(output, label)
        if state == "open" and (opened < 40 or closed >= 10):
            raise RuntimeError("Open Door object state lost on native room reentry")
        if state == "closed" and (closed < 40 or opened >= 10):
            raise RuntimeError("Closed Door object state lost on native room reentry")
        return labels

    change_room("open")
    open_samples = sample_route("open")
    door_x, door_y = open_door_center(output, "room-open-door")
    for x, y in ((408, 506), inventory_center, (door_x, door_y)):
        click(x, y)
        time.sleep(0.3)
    for _ in range(40):
        capture("room-close-action")
        if (door_pixels(output, "room-close-action") >= 40
                and door_pixels(output, "room-close-action", open_state=True) < 10):
            break
        time.sleep(0.35)
    else:
        raise RuntimeError("Real Use Key with Door failed after room return")
    change_room("closed")
    closed_samples = sample_route("closed")
    (output / "scummvm-native-gate-room-return-report.json").write_text(
        json.dumps({"native_room_transitions": [
                        "Harbor->Cellar->Harbor (open)",
                        "Harbor->Cellar->Harbor (closed)"],
                    "returned_open_door_verified": True,
                    "returned_closed_door_verified": True,
                    "post_return_use_closed_gate": True,
                    "open_samples": open_samples, "closed_samples": closed_samples},
                   indent=2) + "\n", encoding="utf-8")
