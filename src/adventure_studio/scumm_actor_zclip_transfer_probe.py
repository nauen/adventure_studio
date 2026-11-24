"""R06: real native transfer to a destination mask and return to automatic clipping."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image

from .scumm_actor_zclip_probe import author_project
from .scumm_assets import CameraCue, RoomHotspot
from .scumm_camera_zp01_probe import camera_from_sky
from .scumm_launch import close_rgb, colored_item_center, colored_item_pixels, launch_smoke, scene_pixel
from .scumm_project import canonical_json, export_document, parse_document, InteractionSequence
from .scumm_toolchain import compile_story_game
from .scumm_two_actor_four_mask_probe import ACTOR_IDS
from .studio_sequences import append_sequence_step, import_room_zplane

VARIANTS = ("masked", "transparent")
RETURN_RGB = (60, 220, 90)


def author_transfer_project(root, variant, profiles=False):
    if variant not in VARIANTS:
        raise ValueError("Unknown transfer mask control")
    doc = parse_document(author_project(root, "transparent", initial=False))
    name = ("R06Profile" if profiles else "R06Transfer") + variant.title() + "Costume"
    previous = doc.costumes[-1].name
    rooms = tuple(replace(room, camera_cues=(CameraCue("set", x=320),))
                  if room.name == "Harbor" else room for room in doc.rooms)
    doc = replace(doc, rooms=rooms,
        costumes=(*doc.costumes[:-1], replace(doc.costumes[-1], name=name)),
        actors=tuple(replace(a, costume=name, initial_zclip=0) if a.costume == previous else a
                     for a in doc.actors),
        interaction_sequences=tuple(s for s in doc.interaction_sequences
                    if (s.room, s.hotspot_id, s.verb) != ("Harbor", "Key", "Close")))
    # Real destination PNG, not a source-room mask or mocked runtime.
    png = root / "cellar-zp01.png"
    cellar = next(room for room in doc.rooms if room.name == "Cellar")
    width, height = cellar.geometry.room_width, cellar.geometry.room_height
    Image.frombytes("L", (width, height), bytes(
        255 if variant == "masked" and 180 <= x < 260 and 45 <= y < 110 else 0
        for y in range(height) for x in range(width))).save(png)
    raw = import_room_zplane(canonical_json(doc), "Cellar", 1, str(png))
    if profiles:
        from .studio_actors import set_actor_room_zclip
        raw = set_actor_room_zclip(raw, ACTOR_IDS[0], "Cellar", 1)
    raw = append_sequence_step(raw, "Harbor", "Key", "Close",
        "Actor-Raumtransfer mit Z-Clipping", ACTOR_IDS[0], None, "Cellar", -1 if profiles else 1, 220, 85)
    raw = append_sequence_step(raw, "Harbor", "Key", "Close",
        "Raum wechseln", None, None, "Cellar", None)
    raw = append_sequence_step(raw, "Cellar", "Stairs", "Close",
        "Actor-Raumtransfer mit Z-Clipping", ACTOR_IDS[0], None, "Harbor", -1 if profiles else 0, 240, 85)
    return append_sequence_step(raw, "Cellar", "Stairs", "Close",
        "Raum wechseln", None, None, "Harbor", None)


def play_transfer(output, capture, process):
    def click(x, y):
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                       check=True, timeout=5)
        time.sleep(.2)

    def await_frame(label, predicate):
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("ScummVM exited during native Actor transfer")
            capture(label)
            if predicate(label):
                return
            time.sleep(.3)
        raise RuntimeError(f"Native room not observed: {label}")

    def harbor(label):
        with Image.open(output / f"scummvm-{label}.png") as img:
            x = camera_from_sky(img)
        return x is not None and abs(x - 320) <= 5 and colored_item_pixels(output, label, (255, 220, 75)) >= 10

    def lane_pixels(label, world_x, camera_x, top, bottom):
        with Image.open(output / f"scummvm-{label}.png") as img:
            rgb = img.convert("RGB")
            center = 192 + 2 * (world_x - camera_x + 160)
            return sum(max(rgb.getpixel((x, y))) <= 24
                       for y in range(top, bottom) for x in range(center-20, center+21))

    def sample(phase, camera, world_x):
        rows = []
        for i in range(8):
            label = f"transfer-{phase}-{i:02d}"
            capture(label)
            rows.append({"frame": label,
                         "a_pixels": lane_pixels(label, world_x, camera, 312, 343),
                         "b_pixels": lane_pixels(label, 240, camera, 418, 448)})
            time.sleep(.15)
        return rows

    await_frame("transfer-ready", harbor)
    time.sleep(1)
    before = sample("before", 320, 240)
    click(234, 563)
    click(*colored_item_center(output, before[-1]["frame"], (255, 220, 75)))
    await_frame("transfer-cellar", lambda label: close_rgb(scene_pixel(output, label), (120, 70, 180)))
    time.sleep(2)
    destination = sample("destination", 160, 220)
    click(234, 563)
    click(*colored_item_center(output, destination[-1]["frame"], RETURN_RGB, fuzz_percent=4))
    await_frame("transfer-back", harbor)
    time.sleep(1)
    returned = sample("returned", 320, 240)
    (output / "transfer-report.json").write_text(json.dumps({
        "before": before, "destination": destination, "returned": returned}, indent=2))


def verify_transfer(report, variant):
    for phase in ("before", "destination", "returned"):
        rows = report[phase]
        if len(rows) != 8:
            raise RuntimeError(f"Missing native transfer screenshots: {phase}")
        visible = phase != "destination" or variant == "transparent"
        count = sum(row["a_pixels"] >= 100 for row in rows)
        if (visible and count < 6) or (not visible and any(row["a_pixels"] >= 25 for row in rows)):
            raise RuntimeError(f"Unexpected transferred Actor visibility: {variant} {phase}: {rows}")
        if phase != "destination" and sum(row["b_pixels"] >= 100 for row in rows) < 6:
            raise RuntimeError(f"Reference Actor changed in Harbor: {phase}")
        if phase == "destination" and any(row["b_pixels"] >= 100 for row in rows):
            raise RuntimeError("Non-transferred reference Actor appeared in Cellar")


def run(upstream, output, profiles=False):
    output.mkdir(parents=True, exist_ok=True)
    result = {}
    for variant in VARIANTS:
        root = output / variant
        resources = root / "build" / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        raw = author_transfer_project(root, variant, profiles=profiles)
        (root / "build" / "project.json").write_text(raw)
        export_document(parse_document(raw), resources)
        game = compile_story_game(root / "build", upstream, root / "game")
        launch_smoke(game, root / "screenshots", scene_only=True, allow_static_scene=True,
                     native_actor_zclip_transfer_probe=True)
        report = json.loads((root / "screenshots" / "transfer-report.json").read_text())
        verify_transfer(report, variant)
        result[variant] = report
    result["native_actor_zclip_transfer_verified"] = True
    (output / "report.json").write_text(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2]), profiles="--profiles" in sys.argv[3:]), indent=2))
