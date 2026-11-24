"""R06 native opt-in Z-clipping reset on genuine room reentry."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image

from .scumm_actor_zclip_probe import author_project
from .scumm_assets import RoomHotspot, CameraCue
from .scumm_camera_zp01_probe import camera_from_sky
from .scumm_launch import close_rgb, colored_item_center, colored_item_pixels, launch_smoke, scene_pixel
from .scumm_project import canonical_json, export_document, parse_document, ActorZClipStep
from .scumm_toolchain import compile_story_game
from .scumm_two_actor_four_mask_probe import ACTOR_IDS, track_native_actor_lanes
from .studio_actors import set_actor_initial_zclip
from .studio_sequences import append_sequence_step

PORTAL_RGB = (175, 60, 210)
RETURN_RGB = (60, 210, 175)
VARIANTS = ("masked-reset", "transparent-reset", "masked-persistent")


def author_return_project(root, variant):
    if variant not in VARIANTS:
        raise ValueError("Unknown Z-clipping return control")
    raw = author_project(root, "transparent" if variant == "transparent-reset" else "masked", initial=True)
    raw = set_actor_initial_zclip(raw, ACTOR_IDS[0], 1, variant != "masked-persistent")
    doc = parse_document(raw)
    name = "R06Return" + variant.replace("-", "").title() + "Costume"
    previous = doc.costumes[-1].name
    rooms = []
    for room in doc.rooms:
        if room.name == "Harbor":
            portal = RoomHotspot("Passage", "cellar passage", "Go downstairs.",
                                 300, 100, 16, 16, sprite_pixels=bytes([len(room.palette)]) * 256)
            room = replace(room, palette=(*room.palette, PORTAL_RGB),
                           hotspots=(*room.hotspots, portal),
                           camera_cues=(CameraCue("set", x=320),))
        elif room.name == "Cellar":
            portal = RoomHotspot("R06Return", "return passage", "Go upstairs.",
                                 285, 100, 16, 16, sprite_pixels=bytes([len(room.palette)]) * 256)
            room = replace(room, palette=(*room.palette, RETURN_RGB),
                           hotspots=(*room.hotspots, portal),
                           camera_cues=(CameraCue("set", x=320),),
                           demo_walk_to_x=None, demo_walk_to_y=None)
        rooms.append(room)
    sequences = tuple(replace(s, steps=(ActorZClipStep(ACTOR_IDS[0], 0),))
                      if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")
                      else s for s in doc.interaction_sequences)
    raw = canonical_json(replace(doc, rooms=tuple(rooms),
        costumes=(*doc.costumes[:-1], replace(doc.costumes[-1], name=name)),
        actors=tuple(replace(a, costume=name) if a.costume == previous else a for a in doc.actors),
        interaction_sequences=sequences))
    raw = append_sequence_step(raw, "Harbor", "Passage", "Close", "Raum wechseln", None, None, "Cellar", None)
    return append_sequence_step(raw, "Cellar", "R06Return", "Close", "Raum wechseln", None, None, "Harbor", None)


def play_room_return(output, capture, process):
    def click(x, y):
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                       check=True, timeout=5)
        time.sleep(.2)

    def await_frame(label, predicate):
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("ScummVM exited during clipping room return")
            capture(label)
            if predicate(label):
                return
            time.sleep(.3)
        raise RuntimeError(f"Native scene not observed: {label}")

    def harbor(label):
        with Image.open(output / f"scummvm-{label}.png") as img:
            camera = camera_from_sky(img)
        return camera is not None and abs(camera - 320) <= 5 and colored_item_pixels(output, label, PORTAL_RGB) >= 40

    def samples(phase):
        labels = []
        for i in range(8):
            label = f"zclip-{phase}-{i:02d}"
            capture(label)
            labels.append(label)
            time.sleep(.15)
        return labels

    await_frame("zclip-ready", harbor)
    time.sleep(1)
    before = samples("before")
    key = colored_item_center(output, before[-1], (255, 220, 75))
    click(234, 563)
    click(*key)
    def revealed_at_expected_position(label):
        if not harbor(label):
            return False
        with Image.open(output / f"scummvm-{label}.png") as img:
            rgb = img.convert("RGB")
            camera = camera_from_sky(rgb)
            center = round(192 + 2 * (240 - camera + 160))
            # Require the same opaque costume geometry as the lane tracker.
            columns = [sum(max(rgb.getpixel((x, y))) <= 24
                           for y in range(312, 343))
                       for x in range(center - 8, center + 9)]
            return sum(c >= 22 for c in columns) >= 5 and sum(columns) >= 60

    # The native interaction can finish after the initial two-second delay.
    # Wait for actual rendered pixels, then take eight independent frames.
    await_frame("zclip-reveal-ready", revealed_at_expected_position)
    revealed = samples("revealed")
    click(234, 563)
    click(*colored_item_center(output, revealed[-1], PORTAL_RGB, fuzz_percent=4))
    await_frame("zclip-cellar", lambda label: colored_item_pixels(output, label, RETURN_RGB) >= 40 and colored_item_pixels(output, label, PORTAL_RGB) < 40)
    time.sleep(2)
    click(234, 563)
    click(*colored_item_center(output, "zclip-cellar", RETURN_RGB, fuzz_percent=4))
    await_frame("zclip-back", harbor)
    time.sleep(1)
    returned = samples("returned")
    frames = before + revealed + returned
    (output / "r06-two-actor-walk-capture.json").write_text(json.dumps({
        "captured_frames": [{"frame": label, "seconds_since_native_input": i}
                            for i, label in enumerate(frames)]}))
    tracks = track_native_actor_lanes(output)
    report = {}
    for phase, labels in (("before", before), ("revealed", revealed), ("returned", returned)):
        visible = [{row["frame"] for row in tracks[a] if abs(row["world_x"] - 240) <= 8}
                   for a in ACTOR_IDS]
        report[phase] = {"a_visible": len(set(labels) & visible[0]),
                         "b_visible": len(set(labels) & visible[1]), "frames": labels}
    (output / "room-return-report.json").write_text(json.dumps(report, indent=2))


def verify_return(report, variant):
    expected = {"masked-reset": (False, True, False),
                "transparent-reset": (True, True, True),
                "masked-persistent": (False, True, True)}[variant]
    for phase, visible in zip(("before", "revealed", "returned"), expected):
        row = report[phase]
        if len(row["frames"]) != 8 or row["b_visible"] < 6:
            raise RuntimeError(f"Missing stable reference Actor: {variant} {phase}: {row}")
        if (visible and row["a_visible"] < 6) or (not visible and row["a_visible"] != 0):
            raise RuntimeError(f"Unexpected native clipping: {variant} {phase}: {row}")


def run(upstream, output):
    output.mkdir(parents=True, exist_ok=True)
    result = {}
    for variant in VARIANTS:
        root = output / variant
        resources = root / "build" / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        raw = author_return_project(root, variant)
        (root / "build" / "project.json").write_text(raw)
        export_document(parse_document(raw), resources)
        game = compile_story_game(root / "build", upstream, root / "game")
        launch_smoke(game, root / "screenshots", scene_only=True, allow_static_scene=True,
                     native_actor_zclip_return_probe=True)
        report = json.loads((root / "screenshots" / "room-return-report.json").read_text())
        verify_return(report, variant)
        result[variant] = report
    result["native_actor_zclip_room_return_verified"] = True
    (output / "report.json").write_text(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
