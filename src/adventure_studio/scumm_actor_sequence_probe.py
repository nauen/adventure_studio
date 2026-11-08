"""Play a Studio-authored multi-step Actor interaction in stock ScummVM."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

from .scumm_assets import RoomHotspot, CombineRule
from .scumm_launch import colored_item_center, colored_item_pixels
from .scumm_project import canonical_json, export_document, parse_document
from .scumm_toolchain import compile_story_game
from .studio_sequences import (append_sequence_step, set_sequence_condition,
                               duplicate_sequence_variant, modify_sequence_step,
                               replace_sequence_step, set_sequence_skippable,
                               append_selected_sequence_step)


def run_actor_sequence_probe(upstream: Path, actor_build: Path, destination: Path) -> dict:
    """A real Close/Key click drives walk -> wait -> turn -> animate -> door."""
    original = parse_document((actor_build / "build" / "project.json").read_text(encoding="utf-8"))
    # The upstream Road checkout already contains the preceding Actor probe's
    # COST. A separate playable game must have its own resource identity.
    costume = replace(original.costumes[0], name="StudioSequenceCostume")
    # Two pickups feed an existing room recipe. Their result starts hidden;
    # the skipped second variant must still produce its cyan inventory icon.
    token_sprite = bytes(4 if (3 <= x <= 12 and 3 <= y <= 12) else 2
                         for y in range(16) for x in range(16))
    badge_sprite = bytes(5 if (3 <= x <= 12 and 3 <= y <= 12) else 2
                         for y in range(16) for x in range(16))
    harbor = original.rooms[0]
    harbor = replace(harbor, hotspots=(
        *harbor.hotspots,
        RoomHotspot("Token", "the token", "A small token.", 610, 100, 16, 16, True, token_sprite),
        RoomHotspot("Shard", "the shard", "A small shard.", 585, 100, 16, 16, True, token_sprite),
        RoomHotspot("Badge", "the badge", "A fused badge.", 560, 100, 16, 16, True, badge_sprite)),
        combine_rules=(*harbor.combine_rules,
                       CombineRule("Token", "Shard", "Badge", "The badge is complete.")))
    project = replace(original, rooms=(harbor, *original.rooms[1:]), costumes=(costume,),
                      actors=tuple(replace(actor, costume=costume.name)
                                   for actor in original.actors),
                      animation_input_rules=(), animation_triggers=(),
                      animation_rules=(), interaction_sequences=())
    raw = canonical_json(project)
    actions = (
        ("Actor versetzen", "Guide", None, None, None, 425, 110, None),
        ("Actor laufen lassen", "Guide", None, None, None, 505, 110, None),
        ("Auf Actor warten", "Guide", None, None, None, None, None, None),
        ("Actor drehen", "Guide", None, None, None, None, None, "W"),
        ("Actor animieren", "Guide", "gesture", None, None, None, None, None),
        ("Warten", None, None, None, 6, None, None, None),
        ("Objektzustand setzen", None, None, "Door", 2, None, None, None),
    )
    for kind, actor, animation, target, amount, x, y, direction in actions:
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", kind, actor,
                                   animation, target, amount, x, y, direction)
    raw = set_sequence_condition(raw, "Harbor|Key|Close", "Door", 1)
    raw = set_sequence_skippable(raw, "Harbor|Key|Close|Door|1", True)
    raw = duplicate_sequence_variant(raw, "Harbor|Key|Close|Door|1", "Door", 2)
    alternate = "Harbor|Key|Close|Door|2"
    for _ in range(len(actions) - 1):
        raw = modify_sequence_step(raw, alternate, 0, "Entfernen")
    raw = replace_sequence_step(raw, alternate, 0, "Objektzustand setzen",
                                None, None, "Door", 1)
    raw = append_selected_sequence_step(raw, alternate, "Warten", None, None, None, 6)
    raw = append_selected_sequence_step(raw, alternate, "Gegenstand aufnehmen",
                                        None, None, "Token", None)
    raw = append_selected_sequence_step(raw, alternate, "Gegenstand aufnehmen",
                                        None, None, "Shard", None)
    raw = append_selected_sequence_step(raw, alternate, "Inventar kombinieren",
                                        None, None, "Badge", None)
    raw = set_sequence_skippable(raw, alternate, True)
    build = destination / "build"
    build.mkdir(parents=True, exist_ok=True)
    (build / "project.json").write_text(raw, encoding="utf-8")
    export_document(parse_document(raw), build / "resources")
    game_dir = compile_story_game(build, upstream, destination / "game")
    screenshot_dir = destination / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("Native Actor interaction needs Xvfb")

    def frame(name: str) -> Path:
        path = screenshot_dir / f"scummvm-{name}.png"
        xwd = screenshot_dir / f"scummvm-{name}.xwd"
        subprocess.run(["xwd", "-root", "-silent", "-out", str(xwd)],
                       check=True, stdout=subprocess.DEVNULL, timeout=10)
        subprocess.run(["convert", str(xwd), str(path)],
                       check=True, stdout=subprocess.DEVNULL, timeout=10)
        return path

    with (screenshot_dir / "scummvm.log").open("w", encoding="utf-8") as log:
        game = subprocess.Popen(["scummvm", f"--path={game_dir.resolve()}", "tentacle"],
                                stdout=log, stderr=subprocess.STDOUT,
                                env={**os.environ, "SDL_AUDIODRIVER": "dummy"})
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if game.poll() is not None:
                    raise RuntimeError("ScummVM quit before Actor interaction")
                frame("before")
                try:
                    key_center = colored_item_center(screenshot_dir, "before", (255, 220, 75))
                    closed_door = colored_item_pixels(screenshot_dir, "before", (50, 220, 220))
                    if closed_door < 40:
                        break
                except ValueError:
                    pass
                time.sleep(0.25)
            else:
                raise RuntimeError("Key and initially closed Door not visible")

            # The key can become visible while the opening camera pan is
            # still in progress, before the fixed verb UI accepts clicks.
            time.sleep(4)
            frame("before")
            key_center = colored_item_center(screenshot_dir, "before", (255, 220, 75))
            closed_door = colored_item_pixels(screenshot_dir, "before", (50, 220, 220))

            # Road's native Close verb is at (10,184); Xvfb scales the game 2x.
            def click_close_key(sample: str) -> None:
                frame(sample)
                current_key = colored_item_center(screenshot_dir, sample, (255, 220, 75))
                for x, y in ((234, 563), current_key):
                    subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                                   check=True, timeout=10)

            click_close_key("before")
            started = time.monotonic()
            time.sleep(1)
            subprocess.run(["xdotool", "key", "Escape"], check=True, timeout=10)
            open_pixels = 0
            while time.monotonic() - started < 15:
                if game.poll() is not None:
                    raise RuntimeError("ScummVM quit during Actor choreography")
                frame("after")
                open_pixels = colored_item_pixels(screenshot_dir, "after", (50, 220, 220))
                if open_pixels >= 40:
                    break
                time.sleep(0.25)
            if open_pixels < 40:
                raise RuntimeError("First conditional branch did not open Door")
            time.sleep(2)
            click_close_key("before-second")
            time.sleep(1)
            subprocess.run(["xdotool", "key", "Escape"], check=True, timeout=10)
            closed_again = False
            badge_in_inventory = False
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                frame("second")
                key_visible = colored_item_pixels(screenshot_dir, "second", (255, 220, 75)) >= 5
                if (key_visible and
                        colored_item_pixels(screenshot_dir, "second", (50, 220, 220)) < 40):
                    closed_again = True
                    badge_in_inventory = (colored_item_pixels(screenshot_dir, "second",
                                                              (50, 220, 220), inventory=True) >= 5
                                          and colored_item_pixels(screenshot_dir, "second",
                                                                  (60, 220, 90), inventory=True) < 5)
                    if badge_in_inventory:
                        break
                time.sleep(0.25)
            if not (closed_again and badge_in_inventory):
                raise RuntimeError("Skipped second branch did not close Door and combine Badge")
            time.sleep(2)
            click_close_key("before-third")
            reopened = False
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                frame("third")
                if colored_item_pixels(screenshot_dir, "third", (50, 220, 220)) >= 40:
                    reopened = True
                    break
                time.sleep(0.25)
            report = {
                "studio_interaction": "Harbor / Key / Close",
                "actions": [action[0] for action in actions],
                "door_closed_before_click": closed_door < 40,
                "door_open_after_click": open_pixels >= 40,
                "first_sequence_skipped_with_escape": True,
                "door_closed_after_second_click": closed_again,
                "badge_owned_after_second_escape": badge_in_inventory,
                "door_reopened_after_third_click": reopened,
                "response_seconds": round(time.monotonic() - started, 2),
            }
            (destination / "actor-sequence-report.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8")
            if not (report["door_open_after_click"] and closed_again and
                    badge_in_inventory and reopened):
                raise RuntimeError(f"Studio native Actor choreography did not finish: {report}")
            return report
        finally:
            game.terminate()
            try:
                game.wait(timeout=5)
            except subprocess.TimeoutExpired:
                game.kill()
                game.wait(timeout=5)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_actor_sequence_probe SCUMMC_DIR ACTOR_BUILD OUTPUT_DIR")
    print(run_actor_sequence_probe(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])))
