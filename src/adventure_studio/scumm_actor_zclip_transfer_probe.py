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
ESCAPE_RGB = (190, 85, 155)
ACTION_RGB = (95, 225, 135)
NORTH_RGB = (95, 155, 225)
SOUTH_RGB = (225, 95, 135)


def author_transfer_project(root, variant, profiles=False, entry_restore=False, dynamic=False, restore_profile=False, walk=False, animation=False, facing=False, camera=False, position=False, elevation=False, scale=False, costume_change=False):
    if walk or animation or facing or camera or position or elevation or scale or costume_change:
        dynamic = True
    if variant not in VARIANTS:
        raise ValueError("Unknown transfer mask control")
    doc = parse_document(author_project(root, "transparent", initial=False))
    name = ("R06CostumeTransfer" if costume_change else "R06ScaleTransfer" if scale else "R06ElevationTransfer" if elevation else "R06PositionTransfer" if position else "R06CameraTransfer" if camera else "R06FacingTransfer" if facing else "R06AnimationTransfer" if animation else "R06WalkTransfer" if walk else "R06RestoreProfile" if restore_profile else "R06DynamicTransfer" if dynamic else "R06EntryProfile" if entry_restore else "R06Profile" if profiles else "R06Transfer") + variant.title() + "Costume"
    previous = doc.costumes[-1].name
    rooms = []
    for room in doc.rooms:
        if room.name == "Harbor":
            room = replace(room, camera_cues=(CameraCue("set", x=320),))
        elif room.name == "Cellar":
            if camera:
                harbor_room = next(r for r in doc.rooms if r.name == "Harbor")
                # Use the real scrolling background and palette for optical camera measurement.
                room = replace(room, geometry=harbor_room.geometry, pixels=harbor_room.pixels,
                               palette=harbor_room.palette, hotspots=(), use_rules=(),
                               combine_rules=(), talk_rules=(), palette_cycles=(),
                               zplanes=(), scale_slots=None, scale_curves=(),
                               goal_text=None, ego_start_x=160)
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
                                        ("R06Restore", RESTORE_RGB, 180),
                                        ("R06Hide", ESCAPE_RGB, 180),
                                        ("R06Action", ACTION_RGB, 180),
                                        ("R06North", NORTH_RGB, 70),
                                        ("R06South", SOUTH_RGB, 110)):
                    if ident == "R06Restore" and not (restore_profile or walk or facing or camera or position or elevation or scale or costume_change):
                        continue
                    if ident == "R06Hide" and (not dynamic or restore_profile or walk or animation or facing or camera or position or elevation or scale or costume_change):
                        continue
                    if ident == "R06Action" and not animation:
                        continue
                    if ident in ("R06North", "R06South") and not facing:
                        continue
                    # Keep the restore-profile trigger beneath the authored Actor.
                    # Otherwise SCUMM walks Ego to the hotspot before the probe
                    # measures the restored world position, invalidating the
                    # stationary-Actor visibility check.
                    hotspot_x, hotspot_y = ((220, 85)
                        if ident == "R06Restore" and restore_profile
                        and not (walk or facing or camera or position or elevation or scale or costume_change)
                        else (x, 100))
                    hotspot = RoomHotspot(ident, ident, ident, hotspot_x, hotspot_y, 16, 16,
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
    alternative = replace(costume, name=name + "Alt", frames=tuple(
        replace(frame, pixels=bytes(1 if x < frame.width // 2 else 0
                                    for y in range(frame.height) for x in range(frame.width)))
        for frame in costume.frames)) if costume_change else None
    doc = replace(doc, rooms=rooms,
        costumes=(*doc.costumes[:-1], costume, *((alternative,) if alternative else ())),
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
    if dynamic and not restore_profile and not walk and not animation and not facing and not camera and not position and not elevation and not scale and not costume_change:
        raw = append_sequence_step(raw, "Cellar", "R06Hide", "Close",
            "Objektzustand setzen", None, None, "R06Hide", 0)
        raw = append_sequence_step(raw, "Cellar", "R06Hide", "Close",
            "Warten", None, None, None, 12)
        raw = append_sequence_step(raw, "Cellar", "R06Hide", "Close",
            "Actor Z-Clipping", ACTOR_IDS[0], None, None, 1)
        raw = set_sequence_skippable(raw, "Cellar|R06Hide|Close", True)
    if costume_change:
        raw = append_sequence_step(raw, "Cellar", "R06Reveal", "Close",
            "Actor Costume wechseln", ACTOR_IDS[0], None, name + "Alt", None)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Objektzustand setzen", None, None, "R06Restore", 0)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Warten", None, None, None, 12)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Actor Costume wechseln", ACTOR_IDS[0], None, name, None)
        raw = set_sequence_skippable(raw, "Cellar|R06Restore|Close", True)
    if scale:
        raw = append_sequence_step(raw, "Cellar", "R06Reveal", "Close",
            "Actor Skalierung", ACTOR_IDS[0], None, None, 128)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Objektzustand setzen", None, None, "R06Restore", 0)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Warten", None, None, None, 12)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Actor Skalierung", ACTOR_IDS[0], None, None, 0)
        raw = set_sequence_skippable(raw, "Cellar|R06Restore|Close", True)
    if elevation:
        raw = append_sequence_step(raw, "Cellar", "R06Reveal", "Close",
            "Actor Höhe", ACTOR_IDS[0], None, None, 28)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Objektzustand setzen", None, None, "R06Restore", 0)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Warten", None, None, None, 12)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Actor Höhe", ACTOR_IDS[0], None, None, 0)
        raw = set_sequence_skippable(raw, "Cellar|R06Restore|Close", True)
    if position:
        raw = append_sequence_step(raw, "Cellar", "R06Reveal", "Close",
            "Actor versetzen", ACTOR_IDS[0], None, None, None, 140, 85)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Objektzustand setzen", None, None, "R06Restore", 0)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Warten", None, None, None, 12)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Actor versetzen", ACTOR_IDS[0], None, None, None, 220, 85)
        raw = set_sequence_skippable(raw, "Cellar|R06Restore|Close", True)
    if camera:
        for kind, actor, x, amount in (
            # Native follow need not recenter an Actor already inside the viewport.
            ("Kamera schwenken", None, 480, None),
            ("Auf Kamera warten", None, None, None),
            # Keep the reached endpoint observable before native follow changes it.
            ("Warten", None, None, 2),
            ("Kamera folgt Actor", ACTOR_IDS[0], None, None),
            ("Auf Kamera warten", None, None, None),
            ("Warten", None, None, 3),
            ("Kamera schwenken", None, 160, None),
            ("Auf Kamera warten", None, None, None),
        ):
            raw = append_sequence_step(raw, "Cellar", "R06Reveal", "Close",
                kind, actor, None, None, amount, x)
    if camera:
        for kind, actor, x, amount in (
            # Native follow need not recenter an Actor already inside the viewport.
            ("Kamera schwenken", None, 480, None),
            ("Auf Kamera warten", None, None, None),
            # Keep the reached endpoint observable before native follow changes it.
            ("Warten", None, None, 2),
            ("Kamera folgt Actor", ACTOR_IDS[0], None, None),
            ("Auf Kamera warten", None, None, None),
            ("Warten", None, None, 30),
            ("Kamera schwenken", None, 160, None),
            ("Auf Kamera warten", None, None, None),
        ):
            raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
                kind, actor, None, None, amount, x)
        raw = set_sequence_skippable(raw, "Cellar|R06Restore|Close", True)
    if facing:
        for hotspot, direction in (("R06Reveal", "W"), ("R06North", "N"),
                                   ("R06South", "S")):
            raw = append_sequence_step(raw, "Cellar", hotspot, "Close",
                "Actor drehen", ACTOR_IDS[0], None, None, None, direction=direction)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Objektzustand setzen", None, None, "R06Restore", 0)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Warten", None, None, None, 12)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Actor drehen", ACTOR_IDS[0], None, None, None, direction="E")
        raw = set_sequence_skippable(raw, "Cellar|R06Restore|Close", True)
    if animation:
        raw = append_sequence_step(raw, "Cellar", "R06Action", "Close",
            "Actor animieren", ACTOR_IDS[0], "gesture", None, None)
    if walk:
        raw = append_sequence_step(raw, "Cellar", "R06Reveal", "Close",
            "Actor laufen lassen", ACTOR_IDS[0], None, None, None, 140, 85)
        raw = append_sequence_step(raw, "Cellar", "R06Reveal", "Close",
            "Auf Actor warten", ACTOR_IDS[0], None, None, None)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Warten", None, None, None, 12)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Actor laufen lassen", ACTOR_IDS[0], None, None, None, 220, 85)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Auf Actor warten", ACTOR_IDS[0], None, None, None)
        raw = set_sequence_skippable(raw, "Cellar|R06Restore|Close", True)
    if restore_profile:
        # A reusable native object marker proves the delayed script has started.
        raw = append_sequence_step(raw, "Cellar", "R06Reveal", "Close",
            "Objektzustand setzen", None, None, "R06Restore", 1)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Objektzustand setzen", None, None, "R06Restore", 0)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Warten", None, None, None, 12)
        raw = append_sequence_step(raw, "Cellar", "R06Restore", "Close",
            "Actor Z-Clipping", ACTOR_IDS[0], None, None, -1)
        raw = set_sequence_skippable(raw, "Cellar|R06Restore|Close", True)
    return raw


def play_transfer(output, capture, process, dynamic=False, restore_profile=False, walk=False, animation=False, facing=False, camera=False, position=False, elevation=False, scale=False, costume_change=False):
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
                and (camera or colored_item_pixels(output, label, (255, 220, 75)) < 10))
    time.sleep(2)
    destination = sample("destination", 160, 220)
    revealed, restored, revealed_again, restored_escape, escaped = [], [], [], [], []
    escape_elapsed = None
    motion, walk_escape = [], []
    action_frames, idle_frames = [], []
    facing_frames = {}
    camera_frames, camera_escape_frames = [], []
    position_normal, position_escape = [], []
    elevation_raised, elevation_restored = [], []
    scale_small, scale_full = [], []
    costume_alternate, costume_original = [], []
    if walk or animation or facing or camera or position or elevation or scale or costume_change:
        dynamic = True
    if dynamic or restore_profile:
        click(234, 563)
        click(*colored_item_center(output, destination[-1]["frame"], REVEAL_RGB, fuzz_percent=4))
        if costume_change:
            def costume_samples(phase, alternate):
                rows = []
                def measure(label):
                    with Image.open(output / f"scummvm-{label}.png") as img:
                        rgb = img.convert("RGB")
                        return {"frame": label,
                                "left": sum(max(rgb.getpixel((x,y))) <= 24 for x in range(616,632) for y in range(308,343)),
                                "right": sum(max(rgb.getpixel((x,y))) <= 24 for x in range(632,648) for y in range(308,343)),
                                "reference": lane_pixels(label, 240, 160, 418,448)}
                stable = 0
                index = 0
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline and stable < 3:
                    label = f"transfer-costume-{phase}-settle-{index:03d}"
                    capture(label)
                    row = measure(label)
                    matches = row["left"] >= 100 and (row["right"] < 50 if alternate else row["right"] >= 100)
                    stable = stable + 1 if matches else 0
                    index += 1
                    time.sleep(.15)
                if stable < 3:
                    raise RuntimeError(f"Native costume did not settle: {phase}: {row}")
                for i in range(8):
                    label = f"transfer-costume-{phase}-{i:02d}"
                    capture(label)
                    rows.append(measure(label))
                    time.sleep(.15)
                return rows
            costume_alternate = costume_samples("alternate", True)
        elif scale:
            def scale_measure(label):
                with Image.open(output / f"scummvm-{label}.png") as img:
                    rgb = img.convert("RGB")
                    coords = [(x, y) for y in range(286, 355) for x in range(610, 653)
                              if max(rgb.getpixel((x, y))) <= 24]
                if not coords:
                    return {"frame": label, "pixels": 0, "width": 0, "height": 0, "center": 0, "bottom": 0}
                xs, ys = zip(*coords)
                return {"frame": label, "pixels": len(coords), "width": max(xs)-min(xs)+1,
                        "height": max(ys)-min(ys)+1, "center": (min(xs)+max(xs))/2, "bottom": max(ys),
                        "reference": lane_pixels(label, 240, 160, 418, 448)}
            def scale_samples(phase, small):
                rows = []
                stable = 0
                deadline = time.monotonic() + 20
                index = 0
                while time.monotonic() < deadline and stable < 3:
                    label = f"transfer-scale-{phase}-settle-{index:03d}"
                    capture(label)
                    row = scale_measure(label)
                    matches = (12 <= row["width"] <= 20 and 16 <= row["height"] <= 28) if small else (26 <= row["width"] <= 36 and 34 <= row["height"] <= 52)
                    stable = stable + 1 if matches else 0
                    index += 1
                    time.sleep(.15)
                if stable < 3:
                    raise RuntimeError(f"Native scale did not settle: {phase}: {row}")
                for i in range(8):
                    label = f"transfer-scale-{phase}-{i:02d}"
                    capture(label)
                    rows.append(scale_measure(label))
                    time.sleep(.15)
                return rows
            scale_small = scale_samples("small", True)
        elif elevation:
            def elevation_samples(phase, raised):
                rows = []
                stable = 0
                index = 0
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline and stable < 3:
                    label = f"transfer-elevation-{phase}-settle-{index:03d}"
                    capture(label)
                    high = lane_pixels(label, 220, 160, 256, 287)
                    low = lane_pixels(label, 220, 160, 312, 343)
                    matches = (high >= 100 and low < 25) if raised else (low >= 100 and high < 25)
                    stable = stable + 1 if matches else 0
                    index += 1
                    time.sleep(.15)
                if stable < 3:
                    raise RuntimeError(f"Native elevation did not settle: {phase}")
                for i in range(8):
                    label = f"transfer-elevation-{phase}-{i:02d}"
                    capture(label)
                    rows.append({"frame": label,
                        "high": lane_pixels(label, 220, 160, 256, 287),
                        "low": lane_pixels(label, 220, 160, 312, 343),
                        "reference": lane_pixels(label, 240, 160, 418, 448)})
                    time.sleep(.15)
                return rows
            elevation_raised = elevation_samples("raised", True)
        elif position:
            stable = 0
            index = 0
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline and stable < 3:
                if process.poll() is not None:
                    raise RuntimeError("ScummVM exited during native positioning")
                label = f"transfer-position-settle-{index:03d}"
                capture(label)
                matches = (lane_pixels(label, 140, 160, 312, 343) >= 100
                           and lane_pixels(label, 220, 160, 312, 343) < 25)
                stable = stable + 1 if matches else 0
                index += 1
                time.sleep(.15)
            if stable < 3:
                raise RuntimeError("Native Actor position did not stabilize")
        elif camera:
            deadline = time.monotonic() + 25
            index = 0
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("ScummVM exited during native camera interaction")
                label = f"transfer-camera-{index:03d}"
                capture(label)
                with Image.open(output / f"scummvm-{label}.png") as img:
                    observed = camera_from_sky(img)
                if observed is not None:
                    camera_frames.append({"frame": label, "camera_x": observed,
                        "a_pixels": lane_pixels(label, 220, round(observed), 312, 343)})
                index += 1
                time.sleep(.15)
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
        if not elevation and not scale and not costume_change:
            revealed = sample("revealed", 160, 140 if walk or position else 220)
    if camera:
        # A camera shift to the Actor proves that the delayed cutscene
        # actually started before Escape; a fixed sleep alone cannot.
        click(234, 563)
        capture("transfer-camera-escape-click")
        started = time.monotonic()
        click(*colored_item_center(output, "transfer-camera-escape-click", RESTORE_RGB, fuzz_percent=4))
        def focused(label):
            with Image.open(output / f"scummvm-{label}.png") as img:
                x = camera_from_sky(img)
            return x is not None and abs(x-220) <= 8 and lane_pixels(label, 220, round(x), 312, 343) >= 100
        await_frame("transfer-camera-before-escape", focused)
        if time.monotonic() - started >= 18:
            raise RuntimeError("Camera focus too late for bounded Escape evidence")
        subprocess.run(["xdotool", "key", "Escape"], check=True, timeout=5)
        deadline = min(started + 26, time.monotonic() + 8)
        index = 0
        while time.monotonic() < deadline:
            label = f"transfer-camera-escape-{index:03d}"
            capture(label)
            with Image.open(output / f"scummvm-{label}.png") as img:
                observed = camera_from_sky(img)
            if observed is not None:
                camera_escape_frames.append({"frame": label, "camera_x": observed,
                    "a_pixels": lane_pixels(label, 220, round(observed), 312, 343)})
                if len(camera_escape_frames) >= 3 and all(
                    abs(row["camera_x"]-160) <= 5 and row["a_pixels"] >= 100
                    for row in camera_escape_frames[-3:]):
                    break
            index += 1
            time.sleep(.15)
        escape_elapsed = time.monotonic() - started
    if facing:
        def facing_measurement(label):
            capture(label)
            with Image.open(output / f"scummvm-{label}.png") as img:
                rgb = img.convert("RGB")
                center = 192 + 2 * 220
                # Full authored costume height at native scale two.
                top, bottom = 184 + 2 * (85 - 23), 184 + 2 * (85 + 1)
                middle = (top + bottom) // 2
                def dark(x0, x1, y0, y1):
                    return sum(max(rgb.getpixel((x, y))) <= 24
                               for y in range(y0, y1) for x in range(x0, x1))
                return {"frame": label,
                        "left": dark(center-16, center, top, bottom),
                        "right": dark(center, center+16, top, bottom),
                        "top": dark(center-16, center+16, top, middle),
                        "bottom": dark(center-16, center+16, middle, bottom)}

        def facing_samples(phase):
            rows = []
            for i in range(8):
                rows.append(facing_measurement(f"transfer-facing-{phase}-{i:02d}"))
                time.sleep(.15)
            return rows

        # The reveal establishes visibility before the native turn completes.
        # Retain the transition frames, then measure eight consecutive frames
        # independently; never discard or replace a failed acceptance frame.
        west_settle = []
        stable = 0
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and stable < 3:
            if process.poll() is not None:
                raise RuntimeError("ScummVM exited during native west turn")
            row = facing_measurement(f"transfer-facing-west-settle-{len(west_settle):03d}")
            west_settle.append(row)
            stable = stable + 1 if row["left"] >= 100 and row["right"] < 50 else 0
            time.sleep(.15)
        (output / "facing-west-transition.json").write_text(json.dumps(west_settle, indent=2))
        if stable < 3:
            raise RuntimeError(f"Native west turn did not settle: {west_settle}")
        facing_frames["W"] = facing_samples("west")
        for direction, color in (("N", NORTH_RGB), ("S", SOUTH_RGB)):
            previous = facing_frames[next(reversed(facing_frames))][-1]["frame"]
            click(234, 563)
            click(*colored_item_center(output, previous, color, fuzz_percent=4))
            time.sleep(3)
            facing_frames[direction] = facing_samples(direction)
        click(234, 563)
        click(*colored_item_center(output, facing_frames["S"][-1]["frame"], RESTORE_RGB, fuzz_percent=4))
        started = time.monotonic()
        # Close may first walk Ego to the hotspot. Do not send Escape until
        # the native script has actually started (its marker disappears).
        await_frame("transfer-facing-cutscene-start", lambda label:
                    colored_item_pixels(output, label, RESTORE_RGB) < 40)
        started = time.monotonic()
        subprocess.run(["xdotool", "keydown", "Escape"], check=True, timeout=5)
        try:
            time.sleep(.25)
        finally:
            subprocess.run(["xdotool", "keyup", "Escape"], check=True, timeout=5)
        facing_frames["E"] = facing_samples("east-escape")
        escape_elapsed = time.monotonic() - started
        if escape_elapsed >= 10:
            raise RuntimeError("Facing Escape overlapped ordinary delay completion")
    if animation:
        def pose_samples(phase, count):
            rows = []
            for i in range(count):
                label = f"transfer-{phase}-{i:02d}"
                capture(label)
                with Image.open(output / f"scummvm-{label}.png") as img:
                    rgb = img.convert("RGB")
                    center = 192 + 2 * 220
                    left, right = (sum(max(rgb.getpixel((x, y))) <= 24
                        for y in range(312, 343) for x in range(lo, hi))
                        for lo, hi in ((center-16, center), (center, center+16)))
                rows.append({"frame": label, "left": left, "right": right})
                time.sleep(.06)
            return rows
        idle_frames = pose_samples("idle-control", 12)
        click(234, 563)
        click(*colored_item_center(output, idle_frames[-1]["frame"], ACTION_RGB, fuzz_percent=4))
        action_frames = pose_samples("action", 90)
    def bounded_escape(label, previous_x=220, target_x=220, start_marker=None, masked_target=False):
        started = time.monotonic()
        if start_marker is not None:
            # Native object state zero removes the trigger sprite. Its disappearance
            # proves the interaction was accepted before sending Escape.
            deadline = started + 20
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("ScummVM exited before native Escape interaction")
                capture("transfer-before-escape")
                if colored_item_pixels(output, "transfer-before-escape", start_marker) < 40:
                    break
                time.sleep(.15)
            else:
                raise RuntimeError("Native Escape interaction did not start: marker still visible")
            started = time.monotonic()
        else:
            time.sleep(1)
            capture("transfer-before-escape")
        if lane_pixels("transfer-before-escape", previous_x, 160, 312, 343) < 100:
            raise RuntimeError("Actor not visible before native Escape")
        # Hold Escape across a native input tick and observe the committed
        # state before collecting the eight acceptance frames. A short key
        # pulse can fall between event polls on a loaded runner.
        subprocess.run(["xdotool", "keydown", "Escape"], check=True, timeout=5)
        try:
            time.sleep(.25)
        finally:
            subprocess.run(["xdotool", "keyup", "Escape"], check=True, timeout=5)
        stable = 0
        index = 0
        while time.monotonic() < started + 7:
            frame = f"transfer-{label}-settle-{index:02d}"
            capture(frame)
            pixels = lane_pixels(frame, target_x, 160, 312, 343)
            matches = pixels < 25 if masked_target else pixels >= 100
            if previous_x != target_x:
                matches = matches and lane_pixels(frame, previous_x, 160, 312, 343) < 25
            stable = stable + 1 if matches else 0
            if stable >= 3:
                break
            index += 1
            time.sleep(.15)
        else:
            raise RuntimeError(f"Native Escape target not observed before ordinary delay: {label}, pixels={pixels}")
        rows = sample(label, 160, target_x)
        elapsed = time.monotonic() - started
        if elapsed >= 10:
            raise RuntimeError("Escape observation overlapped ordinary delay completion")
        return rows, elapsed

    if costume_change:
        click(234, 563)
        click(*colored_item_center(output, costume_alternate[-1]["frame"], RESTORE_RGB, fuzz_percent=4))
        started = time.monotonic()
        await_frame("transfer-costume-cutscene-start", lambda label:
                    colored_item_pixels(output, label, RESTORE_RGB) < 40)
        subprocess.run(["xdotool", "keydown", "Escape"], check=True, timeout=5)
        try:
            time.sleep(.25)
        finally:
            subprocess.run(["xdotool", "keyup", "Escape"], check=True, timeout=5)
        costume_original = costume_samples("original", False)
        escape_elapsed = time.monotonic() - started
    if scale:
        click(234, 563)
        click(*colored_item_center(output, scale_small[-1]["frame"], RESTORE_RGB, fuzz_percent=4))
        started = time.monotonic()
        await_frame("transfer-scale-cutscene-start", lambda label:
                    colored_item_pixels(output, label, RESTORE_RGB) < 40)
        subprocess.run(["xdotool", "keydown", "Escape"], check=True, timeout=5)
        try:
            time.sleep(.25)
        finally:
            subprocess.run(["xdotool", "keyup", "Escape"], check=True, timeout=5)
        scale_full = scale_samples("full", False)
        escape_elapsed = time.monotonic() - started
    if elevation:
        click(234, 563)
        click(*colored_item_center(output, elevation_raised[-1]["frame"], RESTORE_RGB, fuzz_percent=4))
        started = time.monotonic()
        await_frame("transfer-elevation-cutscene-start", lambda label:
                    colored_item_pixels(output, label, RESTORE_RGB) < 40)
        subprocess.run(["xdotool", "keydown", "Escape"], check=True, timeout=5)
        try:
            time.sleep(.25)
        finally:
            subprocess.run(["xdotool", "keyup", "Escape"], check=True, timeout=5)
        elevation_restored = elevation_samples("restored", False)
        escape_elapsed = time.monotonic() - started
    if position:
        def position_samples(phase):
            rows = []
            for i in range(8):
                label = f"transfer-position-{phase}-{i:02d}"
                capture(label)
                rows.append({"frame": label,
                    "x140": lane_pixels(label, 140, 160, 312, 343),
                    "x220": lane_pixels(label, 220, 160, 312, 343),
                    "reference": lane_pixels(label, 240, 160, 418, 448)})
                time.sleep(.15)
            return rows
        position_normal = position_samples("normal")
        click(234, 563)
        click(*colored_item_center(output, position_normal[-1]["frame"], RESTORE_RGB, fuzz_percent=4))
        _, escape_elapsed = bounded_escape("position-escape", previous_x=140, target_x=220, start_marker=RESTORE_RGB)
        position_escape = position_samples("escape")
    if dynamic and not restore_profile and not walk and not animation and not facing and not camera and not position and not elevation and not scale and not costume_change:
        click(234, 563)
        click(*colored_item_center(output, revealed[-1]["frame"], ESCAPE_RGB, fuzz_percent=4))
        if colored_item_pixels(output, revealed[-1]["frame"], ESCAPE_RGB) < 40:
            raise RuntimeError("Native Escape start marker absent before interaction")
        escaped, escape_elapsed = bounded_escape("escaped", start_marker=ESCAPE_RGB,
                                                  masked_target=all(row["a_pixels"] < 25 for row in destination))
    if walk:
        click(234, 563)
        click(*colored_item_center(output, revealed[-1]["frame"], RESTORE_RGB, fuzz_percent=4))
        walk_escape, escape_elapsed = bounded_escape("walk-escape", previous_x=140, target_x=220)
    if restore_profile:
        click(234, 563)
        click(*colored_item_center(output, revealed[-1]["frame"], RESTORE_RGB, fuzz_percent=4))
        await_frame("transfer-restore-start", lambda label:
                    colored_item_pixels(output, label, RESTORE_RGB) < 40)
        time.sleep(12)
        masked = all(row["a_pixels"] < 25 for row in destination)
        stable = 0
        index = 0
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and stable < 3:
            label = f"transfer-restored-settle-{index:02d}"
            capture(label)
            pixels = lane_pixels(label, 220, 160, 312, 343)
            matches = pixels < 25 if masked else pixels >= 100
            stable = stable + 1 if matches else 0
            index += 1
            time.sleep(.15)
        if stable < 3:
            raise RuntimeError("Native restored clipping profile did not stabilize")
        restored = sample("restored", 160, 220)
        click(234, 563)
        click(*colored_item_center(output, restored[-1]["frame"], REVEAL_RGB, fuzz_percent=4))
        await_frame("transfer-restore-rearmed", lambda label:
                    colored_item_pixels(output, label, RESTORE_RGB) >= 40
                    and lane_pixels(label, 220, 160, 312, 343) >= 100)
        revealed_again = sample("revealed-again", 160, 220)
        click(234, 563)
        click(*colored_item_center(output, revealed_again[-1]["frame"], RESTORE_RGB, fuzz_percent=4))
        restored_escape, escape_elapsed = bounded_escape("restored-escape",
            start_marker=RESTORE_RGB,
            masked_target=all(row["a_pixels"] < 25 for row in destination))
    # The prior cutscene can still own native input. Wait for the live
    # hotspot and retry only while still in the destination room.
    deadline = time.monotonic() + 45
    returned_to_harbor = False
    attempt = 0
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("ScummVM exited before native return")
        label = f"transfer-return-attempt-{attempt:03d}"
        capture(label)
        if harbor(label) and colored_item_pixels(output, label, RETURN_RGB) < 40:
            returned_to_harbor = True
            break
        if colored_item_pixels(output, label, RETURN_RGB) >= 40:
            click(234, 563)
            capture(label + "-verb")
            if colored_item_pixels(output, label + "-verb", RETURN_RGB) >= 40:
                click(*colored_item_center(output, label + "-verb", RETURN_RGB, fuzz_percent=4))
            # Allow the native interaction to finish before retrying.
            time.sleep(3)
        else:
            time.sleep(.3)
        attempt += 1
    if not returned_to_harbor:
        raise RuntimeError("Native return interaction did not reach Harbor")
    await_frame("transfer-back", harbor)
    time.sleep(1)
    returned = sample("returned", 320, 240)
    (output / "transfer-report.json").write_text(json.dumps({
        "before": before, "destination": destination, "returned": returned, "revealed": revealed, "restored": restored, "revealed_again": revealed_again,
        "restored_escape": restored_escape, "escaped": escaped,
        "escape_elapsed": escape_elapsed, "motion": motion, "walk_escape": walk_escape,
        "idle_frames": idle_frames, "action_frames": action_frames, "facing_frames": facing_frames, "camera_frames": camera_frames, "camera_escape_frames": camera_escape_frames, "position_normal": position_normal, "position_escape": position_escape, "elevation_raised": elevation_raised, "elevation_restored": elevation_restored, "scale_small": scale_small, "scale_full": scale_full, "costume_alternate": costume_alternate, "costume_original": costume_original}, indent=2))


def verify_transfer(report, variant, dynamic=False, restore_profile=False, walk=False, animation=False, facing=False, camera=False, position=False, elevation=False, scale=False, costume_change=False):
    if walk:
        dynamic = True
        xs = [row["world_x"] for row in report["motion"]]
        if len(xs) < 5 or sum(155 < x < 205 for x in xs) < 2 or not all(abs(x-140) <= 12 for x in xs[-3:]):
            raise RuntimeError(f"Native transferred Actor intermediate movement and destination missing: {xs}")
        if not any(a-b >= 45 for i,a in enumerate(xs) for b in xs[i+1:]):
            raise RuntimeError("Native transferred Actor did not walk left")
    if animation:
        dynamic = True
        def side(row):
            if row["left"] >= 100 and row["right"] < 50:
                return "left"
            if row["right"] >= 100 and row["left"] < 50:
                return "right"
            return None
        idle = report["idle_frames"]
        if len(idle) != 12 or sum(r["left"] >= 100 and r["right"] >= 100 for r in idle) < 10 or any(side(r) for r in idle):
            raise RuntimeError(f"Native idle control is not distinct from action: {idle}")
        observed = [value for row in report["action_frames"] if (value := side(row))]
        if observed.count("left") < 2 or observed.count("right") < 2 or sum(
                a != b for a, b in zip(observed, observed[1:])) < 2:
            raise RuntimeError(f"Native transferred Actor animation poses missing: {observed}")
    if facing:
        dynamic = True
        for direction, dominant, other in (("W", "left", "right"),
                ("N", "top", "bottom"), ("S", "bottom", "top"), ("E", "right", "left")):
            rows = report["facing_frames"][direction]
            if len(rows) != 8 or sum(r[dominant] >= 100 and r[other] < 50 for r in rows) < 6:
                raise RuntimeError(f"Native transferred Actor facing missing: {direction}: {rows}")
    if camera:
        dynamic = True
        rows = report["camera_frames"]
        away = next((i for i, row in enumerate(rows)
                     if abs(row["camera_x"] - 480) <= 5), None)
        focused = next((i for i, row in enumerate(rows)
                        if away is not None and i > away
                        and abs(row["camera_x"] - 220) <= 8 and row["a_pixels"] >= 100), None)
        if focused is None or not any(abs(row["camera_x"] - 160) <= 5
                                       and row["a_pixels"] >= 100 for row in rows[focused+1:]):
            raise RuntimeError(f"Native transferred Actor camera focus/return missing: {rows}")
        if len(rows) < 3 or not all(abs(row["camera_x"] - 160) <= 5 for row in rows[-3:]):
            raise RuntimeError("Native camera did not settle at the authored return position")
        escaped = report["camera_escape_frames"]
        if not (0 < report["escape_elapsed"] < 28) or len(escaped) < 3 or not all(
                abs(row["camera_x"]-160) <= 5 and row["a_pixels"] >= 100 for row in escaped[-3:]):
            raise RuntimeError(f"Native camera Escape return not observed: {escaped}")
    if costume_change:
        dynamic = True
        for phase, alternate in (("costume_alternate", True), ("costume_original", False)):
            rows = report[phase]
            if len(rows) != 8 or sum(r["left"] >= 100 and
                (r["right"] < 50 if alternate else r["right"] >= 100)
                and r["reference"] < 100 for r in rows) < 6:
                raise RuntimeError(f"Native costume change missing: {phase}: {rows}")
    if scale:
        dynamic = True
        small = report["scale_small"]
        full = report["scale_full"]
        for rows, wmin, wmax, hmin, hmax in ((small, 12, 20, 16, 28), (full, 26, 36, 34, 52)):
            if len(rows) != 8 or sum(wmin <= r["width"] <= wmax and hmin <= r["height"] <= hmax
                                     and abs(r["center"] - 632) <= 12 and r.get("reference", 0) < 100
                                     for r in rows) < 6:
                raise RuntimeError(f"Native Actor scale missing: {rows}")
        if abs(sorted(r["bottom"] for r in small)[4] - sorted(r["bottom"] for r in full)[4]) > 5:
            raise RuntimeError("Native scale changed the Actor foot position")
    if elevation:
        dynamic = True
        for phase, target, other in (("elevation_raised", "high", "low"),
                                     ("elevation_restored", "low", "high")):
            rows = report[phase]
            if len(rows) != 8 or sum(r[target] >= 100 and r[other] < 25
                                     for r in rows) < 6:
                raise RuntimeError(f"Native Actor elevation missing: {phase}: {rows}")
            if any(r["reference"] >= 100 for r in rows):
                raise RuntimeError("Reference Actor unexpectedly appeared in destination")
    if position:
        dynamic = True
        for phase, target, previous in (("position_normal", "x140", "x220"),
                                        ("position_escape", "x220", "x140")):
            rows = report[phase]
            if len(rows) != 8 or sum(r[target] >= 100 and r[previous] < 25
                                     for r in rows) < 6:
                raise RuntimeError(f"Native transferred Actor position missing: {phase}: {rows}")
            if any(r["reference"] >= 100 for r in rows):
                raise RuntimeError("Reference Actor unexpectedly appeared in destination")
    if (dynamic or restore_profile) and not animation and not camera and not (0 < report["escape_elapsed"] < 10):
        raise RuntimeError("Missing bounded native Escape evidence")
    phases = ["before", "destination"]
    if (dynamic or restore_profile) and not elevation and not scale and not costume_change:
        phases.append("revealed")
    if dynamic and not restore_profile and not walk and not animation and not facing and not camera and not position and not elevation and not scale and not costume_change:
        phases.append("escaped")
    if walk:
        phases.append("walk_escape")
    if restore_profile:
        phases.extend(("restored", "revealed_again", "restored_escape"))
    phases.append("returned")
    for phase in phases:
        rows = report[phase]
        if len(rows) != 8:
            raise RuntimeError(f"Missing native transfer screenshots: {phase}")
        visible = phase not in ("destination", "restored", "restored_escape", "escaped") or variant == "transparent"
        count = sum(row["a_pixels"] >= 100 for row in rows)
        if (visible and count < 6) or (not visible and any(row["a_pixels"] >= 25 for row in rows)):
            raise RuntimeError(f"Unexpected transferred Actor visibility: {variant} {phase}: {rows}")
        if phase in ("before", "returned") and sum(row["b_pixels"] >= 100 for row in rows) < 6:
            raise RuntimeError(f"Reference Actor changed in Harbor: {phase}")
        if phase in ("destination", "revealed", "restored", "revealed_again", "restored_escape", "escaped", "walk_escape") and any(row["b_pixels"] >= 100 for row in rows):
            raise RuntimeError("Non-transferred reference Actor appeared in Cellar")


def run(upstream, output, profiles=False, entry_restore=False, dynamic=False, restore_profile=False, walk=False, animation=False, facing=False, camera=False, position=False, elevation=False, scale=False, costume_change=False):
    output.mkdir(parents=True, exist_ok=True)
    result = {}
    for variant in VARIANTS:
        root = output / variant
        resources = root / "build" / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        raw = author_transfer_project(root, variant, profiles=profiles or entry_restore, entry_restore=entry_restore, dynamic=dynamic, restore_profile=restore_profile, walk=walk, animation=animation, facing=facing, camera=camera, position=position, elevation=elevation, scale=scale, costume_change=costume_change)
        (root / "build" / "project.json").write_text(raw)
        export_document(parse_document(raw), resources)
        game = compile_story_game(root / "build", upstream, root / "game")
        launch_smoke(game, root / "screenshots", scene_only=True, allow_static_scene=True,
                     native_actor_zclip_transfer_probe=True, native_actor_zclip_dynamic_probe=dynamic, native_actor_zclip_profile_restore_probe=restore_profile, native_transferred_actor_walk_probe=walk, native_transferred_actor_animation_probe=animation, native_transferred_actor_facing_probe=facing, native_transferred_actor_camera_probe=camera, native_transferred_actor_position_probe=position, native_transferred_actor_elevation_probe=elevation, native_transferred_actor_scale_probe=scale, native_transferred_actor_costume_probe=costume_change)
        report = json.loads((root / "screenshots" / "transfer-report.json").read_text())
        verify_transfer(report, variant, dynamic=dynamic, restore_profile=restore_profile, walk=walk, animation=animation, facing=facing, camera=camera, position=position, elevation=elevation, scale=scale, costume_change=costume_change)
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
    if camera:
        result["native_transferred_actor_camera_verified"] = True
    if position:
        result["native_transferred_actor_position_verified"] = True
    if costume_change:
        result["native_transferred_actor_costume_verified"] = True
    if scale:
        result["native_transferred_actor_scale_verified"] = True
    if elevation:
        result["native_transferred_actor_elevation_verified"] = True
    if entry_restore:
        result["native_present_actor_entry_profile_smoke_passed"] = True
    (output / "report.json").write_text(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2]), profiles="--profiles" in sys.argv[3:], entry_restore="--entry-restore" in sys.argv[3:], dynamic="--dynamic" in sys.argv[3:], restore_profile="--restore-profile" in sys.argv[3:], walk="--walk" in sys.argv[3:], animation="--animation" in sys.argv[3:], facing="--facing" in sys.argv[3:], camera="--camera" in sys.argv[3:], position="--position" in sys.argv[3:], elevation="--elevation" in sys.argv[3:], scale="--scale" in sys.argv[3:], costume_change="--costume" in sys.argv[3:]), indent=2))
