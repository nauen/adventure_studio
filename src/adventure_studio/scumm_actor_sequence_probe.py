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
from .music_demo import original_midi_theme
from .scumm_launch import (close_rgb, colored_item_center, colored_item_pixels,
                           door_center, scene_pixel)
from .scumm_project import MusicAsset, canonical_json, export_document, parse_document
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
    harbor = replace(harbor, music_id="StudioSequenceTheme", hotspots=(
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
                      animation_rules=(), interaction_sequences=(),
                      music_assets=(MusicAsset("StudioSequenceTheme", original_midi_theme()),))
    raw = canonical_json(project)
    actions = (
        ("Actor versetzen", "Guide", None, None, None, 425, 110, None),
        ("Actor laufen lassen", "Guide", None, None, None, 505, 110, None),
        ("Auf Actor warten", "Guide", None, None, None, None, None, None),
        ("Actor drehen", "Guide", None, None, None, None, None, "W"),
        ("Actor animieren", "Guide", "gesture", None, None, None, None, None),
        ("Warten", None, None, None, 6, None, None, None),
        ("Musik stoppen", None, None, None, None, None, None, None),
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
    raw = append_selected_sequence_step(raw, alternate, "Musik starten",
                                        None, None, None, None)
    raw = set_sequence_skippable(raw, alternate, True)
    # A separate real Door/Close interaction demonstrates a terminal scene
    # change after Escape, without altering the three existing Key variants.
    raw = append_sequence_step(raw, "Harbor", "Door", "Close", "Warten",
                               None, None, None, 6)
    raw = append_sequence_step(raw, "Harbor", "Door", "Close", "Objektzustand setzen",
                               None, None, "Door", 2)
    raw = append_sequence_step(raw, "Harbor", "Door", "Close", "Musik stoppen",
                               None, None, None, None)
    raw = append_sequence_step(raw, "Harbor", "Door", "Close", "Raum wechseln",
                               None, None, "Cellar", None)
    raw = set_sequence_skippable(raw, "Harbor|Door|Close", True)
    build = destination / "build"
    build.mkdir(parents=True, exist_ok=True)
    (build / "project.json").write_text(raw, encoding="utf-8")
    export_document(parse_document(raw), build / "resources")
    # The ordinary compiler path builds this MIDI into a native SOUN resource.
    # The real UI uses import_room_music rather than constructing this fixture.
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

    soundfonts = sorted(Path("/usr/share/sounds").rglob("*.sf2"))
    if not soundfonts:
        raise RuntimeError("Native music cue probe needs a system SoundFont")
    pcm_path = destination / "sequence-audio.raw"
    with (screenshot_dir / "scummvm.log").open("w", encoding="utf-8") as log:
        game = subprocess.Popen(["scummvm", f"--path={game_dir.resolve()}",
                                 "--music-driver=fluidsynth", f"--soundfont={soundfonts[0]}",
                                 "--music-volume=255", "tentacle"],
                                stdout=log, stderr=subprocess.STDOUT,
                                env={**os.environ, "SDL_AUDIODRIVER": "disk",
                                     "SDL_DISKAUDIOFILE": str(pcm_path)})
        audio_epoch = time.monotonic()
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
            first_click_at = time.monotonic()
            started = time.monotonic()
            time.sleep(1)
            subprocess.run(["xdotool", "key", "Escape"], check=True, timeout=10)
            first_skip_at = time.monotonic()
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
            second_click_at = time.monotonic()
            time.sleep(1)
            subprocess.run(["xdotool", "key", "Escape"], check=True, timeout=10)
            second_skip_at = time.monotonic()
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
            third_click_at = time.monotonic()
            reopened = False
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                frame("third")
                if colored_item_pixels(screenshot_dir, "third", (50, 220, 220)) >= 40:
                    reopened = True
                    break
                time.sleep(0.25)
            if not reopened:
                raise RuntimeError("Third Key interaction did not reopen Door")
            # Trigger the newly authored terminal transition through a real
            # Close/ Door click. Escape must jump past the six-second wait,
            # finish the override and only then invoke startRoom(Cellar).
            frame("before-room-change")
            door_x, door_y = colored_item_center(screenshot_dir, "before-room-change",
                                                  (50, 220, 220))
            for x, y in ((234, 563), (door_x - 12, door_y - 12)):
                subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                               check=True, timeout=10)
            time.sleep(1)
            subprocess.run(["xdotool", "key", "Escape"], check=True, timeout=10)
            cellar_after_escape = False
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if game.poll() is not None:
                    raise RuntimeError("ScummVM quit during skipped room transition")
                frame("cellar-after-escape")
                if close_rgb(scene_pixel(screenshot_dir, "cellar-after-escape"),
                             (120, 70, 180)):
                    cellar_after_escape = True
                    break
                time.sleep(0.3)
            if not cellar_after_escape:
                raise RuntimeError("Escape did not switch to Cellar")
            # The regular Stairs/WalkTo route proves that the native scene
            # remains playable after the overridden local object script.
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                frame("stairs-after-escape")
                try:
                    stairs_x, stairs_y = door_center(screenshot_dir, "stairs-after-escape")
                    break
                except ValueError:
                    time.sleep(0.4)
            else:
                raise RuntimeError("Cellar stairs not visible after Escape")
            subprocess.run(["xdotool", "mousemove", str(stairs_x), str(stairs_y),
                            "click", "1"], check=True, timeout=10)
            returned_to_harbor = False
            deadline = time.monotonic() + 16
            while time.monotonic() < deadline:
                frame("harbor-after-return")
                if close_rgb(scene_pixel(screenshot_dir, "harbor-after-return"),
                             (240, 175, 95)):
                    returned_to_harbor = True
                    break
                time.sleep(0.3)
            if not returned_to_harbor:
                raise RuntimeError("Stairs did not return to Harbor after Escape")
            time.sleep(3)
            frame("harbor-after-return")
            door_persisted = (colored_item_pixels(screenshot_dir, "harbor-after-return",
                                                  (50, 220, 220)) >= 40)
            badge_persisted = (colored_item_pixels(screenshot_dir, "harbor-after-return",
                                                   (50, 220, 220), inventory=True) >= 5)
            report = {
                "studio_interaction": "Harbor / Key / Close",
                "actions": [action[0] for action in actions],
                "door_closed_before_click": closed_door < 40,
                "door_open_after_click": open_pixels >= 40,
                "first_sequence_skipped_with_escape": True,
                "door_closed_after_second_click": closed_again,
                "badge_owned_after_second_escape": badge_in_inventory,
                "door_reopened_after_third_click": reopened,
                "cellar_reached_after_escape": cellar_after_escape,
                "returned_to_harbor": returned_to_harbor,
                "door_state_survived_room_return": door_persisted,
                "badge_survived_room_return": badge_persisted,
                "audio_event_seconds": {
                    "first_click": round(first_click_at - audio_epoch, 2),
                    "first_skip": round(first_skip_at - audio_epoch, 2),
                    "second_click": round(second_click_at - audio_epoch, 2),
                    "second_skip": round(second_skip_at - audio_epoch, 2),
                    "third_click": round(third_click_at - audio_epoch, 2),
                },
                "response_seconds": round(time.monotonic() - started, 2),
            }
            if not (report["door_open_after_click"] and closed_again and
                    badge_in_inventory and reopened and cellar_after_escape and
                    returned_to_harbor and door_persisted and badge_persisted):
                raise RuntimeError(f"Studio native Actor choreography did not finish: {report}")
        finally:
            game.terminate()
            try:
                game.wait(timeout=5)
            except subprocess.TimeoutExpired:
                game.kill()
                game.wait(timeout=5)
    audio_duration = time.monotonic() - audio_epoch
    pcm = pcm_path.read_bytes() if pcm_path.exists() else b""
    def activity(start: float, end: float) -> float:
        if end <= start or audio_duration <= 0 or len(pcm) < 8192:
            return 0.0
        first = int(max(0, start - audio_epoch) / audio_duration * len(pcm))
        last = int(min(audio_duration, end - audio_epoch) / audio_duration * len(pcm))
        segment = pcm[first:last]
        return sum(value not in (0, 128) for value in segment) / len(segment) if segment else 0.0

    report["audio_pcm"] = {
        "bytes": len(pcm),
        "before_stop": round(activity(first_click_at - 1.8, first_click_at - 0.2), 4),
        "after_stop": round(activity(first_skip_at + 0.4, second_click_at - 0.2), 4),
        "after_restart": round(activity(second_skip_at + 0.4, third_click_at - 0.2), 4),
    }
    (destination / "actor-sequence-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_actor_sequence_probe SCUMMC_DIR ACTOR_BUILD OUTPUT_DIR")
    print(run_actor_sequence_probe(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])))
