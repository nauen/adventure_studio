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
from .scumm_costume import CostumeDirection
from .scumm_camera_zp01_probe import camera_from_sky
from .scumm_launch import close_rgb, colored_item_center, colored_item_pixels, launch_smoke, scene_pixel
from .scumm_project import canonical_json, export_document, parse_document, InteractionSequence
from .scumm_toolchain import compile_story_game
from .scumm_two_actor_four_mask_probe import ACTOR_IDS
from .studio_sequences import append_sequence_step, import_room_zplane, set_sequence_skippable

VARIANTS = ("masked", "transparent")
RETURN_RGB = (175, 60, 210)
REVEAL_RGB = (60, 210, 175)
RESTORE_RGB = (210, 175, 60)


def author_transfer_project(root, variant, profiles=False, entry_restore=False, dynamic=False, restore_profile=False, walk=False, animation=False, facing=False):
    if walk or animation or facing:
        dynamic = True
    if variant not in VARIANTS:
        raise ValueError("Unknown transfer mask control")
    doc = parse_document(author_project(root, "transparent", initial=False))
    name = ("R06FacingTransfer" if facing else "R06AnimationTransfer" if animation else "R06WalkTransfer" if walk else "R06RestoreProfile" if restore_profile else "R06DynamicTransfer" if dynamic else "R06EntryProfile" if entry_restore else "R06Profile" if profiles else "R06Transfer") + variant.title() + "Costume"
    previous = doc.costumes[-1].name
    rooms = []
    for room in doc.rooms:
        if room.name == "Harbor":
            room = replace(room, camera_cues=(CameraCue("set", x=320),))
        elif room.name == "Cellar":
            # Story composition replaces the original fixture hotspots.
            # Author a dedicated, independently coloured return interaction.
            return_color = len(room.palette)
            stairs = RoomHotspot("R06TransferReturn", "Return to harbor", "Return to harbor.",
                                 285, 100, 16, 16,
                                 sprite_pixels=bytes([return_color]) * 256)
            room = replace(room, palette=(*room.palette, RETURN_RGB),
                           hotspots=(*room.hotspots, stairs),
                           camera_cues=(CameraCue("set", x=160),),
                           walkboxes=next(r.walkboxes for r in doc.rooms if r.name == "Harbor"),
                           box_routes=next(r.box_routes for r in doc.rooms if r.name == "Harbor"),
                           demo_walk_to_x=None, demo_walk_to_y=None)
            if dynamic or restore_profile:
                for ident, color, x in (("R06Reveal", REVEAL_RGB, 250),
                                        ("R06Restore", RESTORE_RGB, 180)):
                    if ident == "R06Restore" and not (restore_profile or facing):
                        continue
                    hotspot = RoomHotspot(ident, ident, ident, x, 100, 16, 16,
                                          sprite_pixels=bytes([len(room.palette)]) * 256)
                    room = replace(room, palette=(*room.palette, color),
                                   hotspots=(*room.hotspots, hotspot))
        rooms.append(room)
    rooms = tuple(rooms)
    costume = replace(doc.costumes[-1], name=name)
    if animation:
        # Native gesture frames have distinct silhouettes; standing/walking
        # resources stay unchanged. A persistent final pose is observable.
        base = costume.frames[0]
        poses = tuple(replace(base, id=f"ActionPose{i}", pixels=bytes(
            1 if left <= x < right else 0
            for y in range(base.height) for x in range(base.width)))
            for i, (left, right) in enumerate(((0, 8), (8, 16))))
        gesture = next(item for item in costume.animations if item.name == "gesture")
        gesture = replace(gesture, directions=(CostumeDirection(
            "S", ("ActionPose0", "ActionPose1"), loop=True),))
        costume = replace(costume, frames=(*costume.frames, *poses),
            animations=tuple(gesture if item.name == "gesture" else item
                             for item in costume.animations))
    if facing:
        # Four cardinal stand frames with direction-specific silhouettes.
        base = costume.frames[0]
        directions = ("N", "E", "S", "W")
        frames = tuple(replace(base, id=f"Facing{d}", pixels=bytes(
            1 if (d == "N" and y < 12 or d == "S" and y >= 12
                  or d == "W" and x < 8 or d == "E" and x >= 8) else 0
            for y in range(base.height) for x in range(base.width)))
            for d in directions)
        stand = tuple(CostumeDirection(d, (f"Facing{d}",)) for d in directions)
        costume = replace(costume, frames=(*costume.frames, *frames),
            animations=tuple(replace(item, directions=stand)
                             if item.name in ("stand", "init") else item
                             for item in costume.animations))
    doc = replace(doc, rooms=rooms,
        costumes=(*doc.costumes[:-1], costume),
        actors=tuple(replace(a, costume=name, initial_zclip=0) if a.costume == previous else a
                     for a in doc.actors),
        interaction_sequences=tuple(s for s in doc.interaction_sequences
                    if (s.room, s.hotspot_id, s.verb) != ("Harbor", "Key", "Close")))
    # Real destination PNG, not a source-room mask or mocked runtime.
    root.mkdir(parents=True, exist_ok=True)
    png = root / "cellar-zp01.png"
    cellar = next(room for room in doc.rooms if room.name == "Cellar")
    width, height = cellar.geometry.room_width, cellar.geometry.room_height
    Image.frombytes("L", (width, height), bytes(
        255 if variant == "masked" and 180 <= x < 260 and 45 <= y < 110 else 0
        for y in range(height) for x in range(width))).save(png)
    raw = import_room_zplane(canonical_json(doc), "Cellar", 1, str(png))
    profiles = profiles or restore_profile
    if profiles:
        from .studio_actors import set_actor_room_zclip
        raw = set_actor_room_zclip(raw, ACTOR_IDS[0], "Cellar", 1, entry_restore)
        if entry_restore:
            # The second Actor remains in Harbor; its destination entry policy
            # must not make it appear in Cellar or disturb the reference lane.
            raw = set_actor_room_zclip(raw, ACTOR_IDS[1], "Cellar", 1, True)
    raw = append_sequence_step(raw, "Harbor", "Key", "Close",
        "Actor-Raumtransfer mit Z-Clipping", ACTOR_IDS[0], None, "Cellar", -1 if profiles else 1, 220, 85)
    raw = append_sequence_step(raw, "Harbor", "Key", "Close",
        "Raum wechseln", None, None, "Cellar", None)
    raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Close",
        "Actor-Raumtransfer mit Z-Clipping", ACTOR_IDS[0], None, "Harbor", -1 if profiles else 0, 240, 85)
    raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Close",
        "Raum wechseln", None, None, "Harbor", None)
    if dynamic or restore_profile:
        raw = append_sequence_step(raw, "Cellar", "R06Reveal", "Close",
            "Actor Z-Clipping", ACTOR_IDS[0], None, None, 0)
    if facing:
        raw = append_sequence_step(raw, "Cellar", "R06Reveal", "Close",
            "Actor drehen", ACTOR_IDS[0], None, None, None, direction="W")
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Warten", None, None, None, 5)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Actor drehen", ACTOR_IDS[0], None, None, None, direction="E")
        raw = set_sequence_skippable(raw, "Cellar|R06Restore|Close", True)
    if animation:
        raw = append_sequence_step(raw, "Cellar", "R06Reveal", "Close",
            "Actor animieren", ACTOR_IDS[0], "gesture", None, None)
    if walk:
        raw = append_sequence_step(raw, "Cellar", "R06Reveal", "Close",
            "Actor laufen lassen", ACTOR_IDS[0], None, None, None, 140, 85)
        raw = append_sequence_step(raw, "Cellar", "R06Reveal", "Close",
            "Auf Actor warten", ACTOR_IDS[0], None, None, None)
    if restore_profile:
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Warten", None, None, None, 5)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Actor Z-Clipping", ACTOR_IDS[0], None, None, -1)
        raw = set_sequence_skippable(raw, "Cellar|R06Restore|Close", True)
    return raw


def play_transfer(output, capture, process, dynamic=False, restore_profile=False, walk=False, animation=False, facing=False):
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
    await_frame("transfer-cellar", lambda label: colored_item_pixels(output, label, RETURN_RGB) >= 40
                and colored_item_pixels(output, label, (255, 220, 75)) < 10)
    time.sleep(2)
    destination = sample("destination", 160, 220)
    revealed, restored, motion, revealed_again, restored_escape = [], [], [], [], []
    if walk or animation or facing:
        dynamic = True
    action_frames, facing_west, facing_east = [], [], []
    if dynamic or restore_profile:
        click(234, 563)
        click(*colored_item_center(output, destination[-1]["frame"], REVEAL_RGB, fuzz_percent=4))
        if animation:
            for i in range(60):
                label = f"transfer-action-{i:02d}"
                capture(label)
                with Image.open(output / f"scummvm-{label}.png") as img:
                    rgb = img.convert("RGB")
                    center = 192 + 2 * 220
                    left, right = (sum(max(rgb.getpixel((x, y))) <= 24
                        for y in range(312, 343) for x in range(lo, hi))
                        for lo, hi in ((center-16, center), (center, center+16)))
                action_frames.append({"frame": label, "left": left, "right": right})
                time.sleep(.06)
        elif walk:
            for i in range(60):
                label = f"transfer-walk-{i:02d}"
                capture(label)
                with Image.open(output / f"scummvm-{label}.png") as img:
                    rgb = img.convert("RGB")
                    columns = [(x, sum(max(rgb.getpixel((x, y))) <= 24
                                       for y in range(312, 343)))
                               for x in range(432, 673)]
                pixels = sum(n for _, n in columns)
                if pixels >= 100:
                    motion.append({"frame": label, "world_x": (sum(x*n for x,n in columns)/pixels - 192)/2})
                time.sleep(.06)
        else:
            deadline = time.monotonic() + 20
            stable = 0
            index = 0
            while time.monotonic() < deadline and stable < 3:
                if process.poll() is not None:
                    raise RuntimeError("ScummVM exited during clipping restoration")
                label = f"transfer-reveal-settle-{index:03d}"
                capture(label)
                stable = stable + 1 if lane_pixels(label, 220, 160, 312, 343) >= 100 else 0
                index += 1
                time.sleep(.15)
            if stable < 3:
                raise RuntimeError("Native revealed Actor did not stabilize")
        revealed = sample("revealed", 160, 140 if walk else 220)
    if facing:
        def facing_samples(phase):
            rows = []
            for i in range(8):
                label = f"transfer-facing-{phase}-{i:02d}"
                capture(label)
                with Image.open(output / f"scummvm-{label}.png") as img:
                    rgb = img.convert("RGB")
                    center = 192 + 2 * 220
                    left, right = (sum(max(rgb.getpixel((x, y))) <= 24
                        for y in range(312, 343) for x in range(lo, hi))
                        for lo, hi in ((center-16, center), (center, center+16)))
                rows.append({"frame": label, "left": left, "right": right})
                time.sleep(.15)
            return rows
        facing_west = facing_samples("west")
        click(234, 563)
        click(*colored_item_center(output, facing_west[-1]["frame"], RESTORE_RGB, fuzz_percent=4))
        time.sleep(.6)
        subprocess.run(["xdotool", "key", "Escape"], check=True, timeout=5)
        time.sleep(.4)
        facing_east = facing_samples("east-escape")
    if restore_profile:
        click(234, 563)
        click(*colored_item_center(output, revealed[-1]["frame"], RESTORE_RGB, fuzz_percent=4))
        time.sleep(6)
        restored = sample("restored", 160, 220)
        click(234, 563)
        click(*colored_item_center(output, restored[-1]["frame"], REVEAL_RGB, fuzz_percent=4))
        time.sleep(2)
        revealed_again = sample("revealed-again", 160, 220)
        click(234, 563)
        click(*colored_item_center(output, revealed_again[-1]["frame"], RESTORE_RGB, fuzz_percent=4))
        time.sleep(.6)
        subprocess.run(["xdotool", "key", "Escape"], check=True, timeout=5)
        time.sleep(.4)
        restored_escape = sample("restored-escape", 160, 220)
    click(234, 563)
    click(*colored_item_center(output, destination[-1]["frame"], RETURN_RGB, fuzz_percent=4))
    await_frame("transfer-back", harbor)
    time.sleep(1)
    returned = sample("returned", 320, 240)
    (output / "transfer-report.json").write_text(json.dumps({
        "before": before, "destination": destination, "returned": returned, "revealed": revealed, "restored": restored, "motion": motion, "action_frames": action_frames, "facing_west": facing_west, "facing_east": facing_east, "revealed_again": revealed_again, "restored_escape": restored_escape}, indent=2))


def verify_transfer(report, variant, dynamic=False, restore_profile=False, walk=False, animation=False, facing=False):
    if walk:
        dynamic = True
        xs = [row["world_x"] for row in report["motion"]]
        if len(xs) < 5 or sum(155 < x < 205 for x in xs) < 2 or not all(abs(x-140) <= 12 for x in xs[-3:]):
            raise RuntimeError(f"Native transferred Actor intermediate movement and destination missing: {xs}")
        if not any(a-b >= 45 for i,a in enumerate(xs) for b in xs[i+1:]):
            raise RuntimeError("Native transferred Actor did not walk left")
    if animation:
        dynamic = True
        frames = report["action_frames"]
        sides = ["left" if f["left"] >= 100 and f["right"] < 50 else
                 "right" if f["right"] >= 100 and f["left"] < 50 else None
                 for f in frames]
        observed = [side for side in sides if side is not None]
        if observed.count("left") < 2 or observed.count("right") < 2 or sum(
                a != b for a, b in zip(observed, observed[1:])) < 2:
            raise RuntimeError(f"Native transferred Actor animation poses missing: {frames}")
    if facing:
        dynamic = True
        for phase, dominant, other in (("facing_west", "left", "right"),
                                       ("facing_east", "right", "left")):
            rows = report[phase]
            if len(rows) != 8 or sum(r[dominant] >= 100 and r[other] < 50
                                     for r in rows) < 6:
                raise RuntimeError(f"Native transferred Actor facing missing: {phase}: {rows}")
    phases = ["before", "destination"]
    if dynamic or restore_profile:
        phases.append("revealed")
    if restore_profile:
        phases.extend(("restored", "revealed_again", "restored_escape"))
    phases.append("returned")
    for phase in phases:
        rows = report[phase]
        if len(rows) != 8:
            raise RuntimeError(f"Missing native transfer screenshots: {phase}")
        visible = phase not in ("destination", "restored", "restored_escape") or variant == "transparent"
        count = sum(row["a_pixels"] >= 100 for row in rows)
        if (visible and count < 6) or (not visible and any(row["a_pixels"] >= 25 for row in rows)):
            raise RuntimeError(f"Unexpected transferred Actor visibility: {variant} {phase}: {rows}")
        if phase in ("before", "returned") and sum(row["b_pixels"] >= 100 for row in rows) < 6:
            raise RuntimeError(f"Reference Actor changed in Harbor: {phase}")
        if phase in ("destination", "revealed", "restored", "revealed_again", "restored_escape") and any(row["b_pixels"] >= 100 for row in rows):
            raise RuntimeError("Non-transferred reference Actor appeared in Cellar")


def run(upstream, output, profiles=False, entry_restore=False, dynamic=False, restore_profile=False, walk=False, animation=False, facing=False):
    output.mkdir(parents=True, exist_ok=True)
    result = {}
    for variant in VARIANTS:
        root = output / variant
        resources = root / "build" / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        raw = author_transfer_project(root, variant, profiles=profiles or entry_restore, entry_restore=entry_restore, dynamic=dynamic, restore_profile=restore_profile, walk=walk, animation=animation, facing=facing)
        (root / "build" / "project.json").write_text(raw)
        export_document(parse_document(raw), resources)
        game = compile_story_game(root / "build", upstream, root / "game")
        launch_smoke(game, root / "screenshots", scene_only=True, allow_static_scene=True,
                     native_actor_zclip_transfer_probe=True, native_actor_zclip_dynamic_probe=dynamic, native_actor_zclip_profile_restore_probe=restore_profile, native_transferred_actor_walk_probe=walk, native_transferred_actor_animation_probe=animation, native_transferred_actor_facing_probe=facing)
        report = json.loads((root / "screenshots" / "transfer-report.json").read_text())
        verify_transfer(report, variant, dynamic=dynamic, restore_profile=restore_profile, walk=walk, animation=animation, facing=facing)
        result[variant] = report
    result["native_actor_zclip_transfer_verified"] = True
    if dynamic:
        result["native_transferred_actor_dynamic_zclip_verified"] = True
    if restore_profile:
        result["native_interaction_room_zclip_profile_verified"] = True
    if walk:
        result["native_transferred_actor_walk_verified"] = True
    if animation:
        result["native_transferred_actor_animation_verified"] = True
    if facing:
        result["native_transferred_actor_facing_verified"] = True
    if entry_restore:
        result["native_present_actor_entry_profile_smoke_passed"] = True
    (output / "report.json").write_text(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2]), profiles="--profiles" in sys.argv[3:], entry_restore="--entry-restore" in sys.argv[3:], dynamic="--dynamic" in sys.argv[3:], restore_profile="--restore-profile" in sys.argv[3:], walk="--walk" in sys.argv[3:], animation="--animation" in sys.argv[3:], facing="--facing" in sys.argv[3:]), indent=2))
