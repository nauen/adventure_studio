"""R06 acceptance: world-anchored ZP01 occlusion through a native camera round-trip.

Produce three separately linked SCUMM-v6 games and inspect timestamped stock
ScummVM frames. This is one combined product-path acceptance, not a test of
new interpreter primitives.
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

from .scumm_assets import CameraCue, destination_fixture, scrolling_fixture
from .scumm_project import GameDocument, canonical_json, parse_document
from .scumm_room_visual_probe import render_native_room
from .studio_sequences import (
    author_room_box_connections, author_room_camera_plan, author_room_walkbox, author_room_walkbox_zplane,
    compose_story_project, import_room_zplane,
)


def camera_from_sky(image: Image.Image) -> float | None:
    """Infer camera world X from the known blue/orange boundary, not elapsed time."""
    if image.size != (1024, 768):
        raise ValueError("Expected the 1024x768 stock-ScummVM display")
    rgb = image.convert("RGB")
    blue, orange = 0, 0
    for x in range(192, 832, 2):
        r, g, b = rgb.getpixel((x, 280))
        if max(abs(r - 70), abs(g - 130), abs(b - 190)) <= 18:
            blue += 1
        elif max(abs(r - 240), abs(g - 175), abs(b - 95)) <= 18:
            orange += 1
    if blue + orange < 300:
        return None
    return 480 - blue


def costume_pixels(image: Image.Image, world_x: int, camera_x: float) -> int:
    """Dark pixels around the actor's projected position, inside the game viewport."""
    rgb = image.convert("RGB")
    center_x = round(192 + 2 * (world_x - camera_x + 160))
    left, right = max(192, center_x - 30), min(831, center_x + 30)
    if left > right:
        return 0
    return sum(1 for y in range(300, 388) for x in range(left, right + 1)
               if max(rgb.getpixel((x, y))) <= 12)


def read_frames(directory: Path, world_x: int = 390) -> list[dict]:
    from PIL import Image
    frames = json.loads((directory / "camera-frame-times.json").read_text(encoding="utf-8"))
    rows = []
    for entry in frames:
        image = Image.open(directory / f"scummvm-{entry['frame']}.png")
        camera = camera_from_sky(image)
        if camera is None:
            continue
        rows.append({
            "frame": entry["frame"],
            "seconds": entry["elapsed_seconds"],
            "camera_x": camera,
            "world_x": world_x,
            "screen_x": round(192 + 2 * (world_x - camera + 160)),
            "actor_dark_pixels": costume_pixels(image, world_x, camera),
        })
    if not rows:
        raise RuntimeError("No identifiable native camera frames")
    return rows


def select_phases(rows: list[dict]) -> dict:
    """Use camera travel direction and observed world X, never guessed delays."""
    # waitForCamera() must complete the authored X=480 destination;
    # getting merely near the far side does not establish a full pan.
    far = next((i for i, row in enumerate(rows) if row["camera_x"] >= 475), None)
    if far is None:
        raise RuntimeError("Outgoing native camera pan never reached the far side")
    pre = next((r for r in rows[:far] if r["camera_x"] <= 165), None)
    outward = next((r for r in rows[:far] if 330 <= r["camera_x"] <= 430), None)
    # On the return pan choose the last observed in-range frame (near 330),
    # not the first (near 430). Only widely separated *visible* positions
    # can distinguish a world-fixed occlusion from a screen-fixed overlay.
    inbound = next((r for r in reversed(rows[far + 1:])
                    if 330 <= r["camera_x"] <= 430), None)
    returned = next((r for r in rows[far + 1:] if r["camera_x"] <= 165), None)
    if pre is None or outward is None or inbound is None or returned is None:
        raise RuntimeError("Missing before/outgoing/returning/completed-return camera frame")
    return {"before": pre, "outgoing": outward, "far": rows[far],
            "returning": inbound, "returned": returned}


def verify_world_mask(variants: dict[str, dict]) -> dict:
    """A correct BOXD mask occludes only the world actor, in both pan directions."""
    phases = {label: select_phases(row["frames"]) for label, row in variants.items()}
    for label, ordered in phases.items():
        for name, phase in ordered.items():
            if phase["world_x"] != 390 or not 160 <= phase["camera_x"] <= 480:
                raise RuntimeError(f"Invalid world/camera coordinates: {label}/{name}")
        if (ordered["before"]["camera_x"] > 165 or ordered["far"]["camera_x"] < 475
                or ordered["returned"]["camera_x"] > 165):
            raise RuntimeError(f"Native camera missed authored 160->480->160 endpoints: {label}")
        if not (ordered["before"]["seconds"] < ordered["outgoing"]["seconds"]
                < ordered["far"]["seconds"] < ordered["returning"]["seconds"]
                < ordered["returned"]["seconds"]):
            raise RuntimeError(f"Camera round-trip not time-ordered: {label}")
    screen_positions = phases["masked"]
    if abs(screen_positions["before"]["screen_x"] - screen_positions["far"]["screen_x"]) < 400:
        raise RuntimeError("Camera pan did not move the world Actor on screen")
    if abs(screen_positions["returned"]["screen_x"] - screen_positions["far"]["screen_x"]) < 400:
        raise RuntimeError("Camera return did not move the world Actor back on screen")
    # The initial/returned Actor may be outside the viewport. Two visible
    # world-anchored occlusions must instead be sufficiently far apart on
    # screen that a 55-world-pixel (110-screen-pixel) stationary mask could
    # not explain both. Check each travel direction independently.
    for phase in ("outgoing", "returning"):
        if abs(screen_positions[phase]["screen_x"] - screen_positions["far"]["screen_x"]) <= 110:
            raise RuntimeError(
                f"Visible Actor positions too close to disprove a screen-fixed ZP01 mask: {phase}")
    comparisons = {}
    for name in ("outgoing", "far", "returning"):
        desired = phases["masked"][name]
        row = {"camera_x": desired["camera_x"], "screen_x": desired["screen_x"],
               "masked_pixels": desired["actor_dark_pixels"]}
        for label in ("transparent", "wrong-box"):
            available = (r for r in variants[label]["frames"]
                         if (r["seconds"] <= phases[label]["far"]["seconds"]) ==
                            (name != "returning"))
            closest = min(available, key=lambda r: abs(r["camera_x"] - desired["camera_x"]),
                          default=None)
            if closest is None or abs(closest["camera_x"] - desired["camera_x"]) > 16:
                raise RuntimeError(f"No coordinate-aligned {label} control for {name}")
            row[f"{label}_pixels"] = closest["actor_dark_pixels"]
            row[f"{label}_frame"] = closest["frame"]
            if closest["actor_dark_pixels"] < 100:
                raise RuntimeError(f"Native actor invisible in {label} control: {name}")
            if desired["actor_dark_pixels"] > closest["actor_dark_pixels"] // 3:
                raise RuntimeError(f"World ZP01 failed to occlude the actor at {name}")
        comparisons[name] = row
    return {"native_world_anchored_zp01_pan_and_return_passed": True,
            "four_phase_frames": phases, "pixel_comparisons": comparisons}



def export_actor_phase_crops(directory: Path, frames: list[dict]) -> dict:
    """Retain inspectable actor pixels from observed native camera phases."""
    from PIL import Image

    selected = select_phases(frames)
    crops = {}
    for phase, frame in selected.items():
        source = directory / f"scummvm-{frame['frame']}.png"
        target = directory / f"scummvm-phase-{phase}-actor-crop.png"
        # Same viewport projection as costume_pixels(), but preserve RGB
        # evidence so an independently inspected crop explains each count.
        center = frame["screen_x"]
        actor_in_view = 192 <= center <= 831
        if center > 831:
            left, right = 772, 831
        elif center < 192:
            left, right = 192, 251
        else:
            left, right = max(192, center - 30), min(831, center + 30)
        with Image.open(source) as screenshot:
            screenshot.convert("RGB").crop((left, 300, right + 1, 388)).save(target)
        crops[phase] = {
            "screenshot": source.name,
            "actor_crop": target.name,
            "elapsed_seconds": frame["seconds"],
            "world_x": frame["world_x"],
            "camera_x": frame["camera_x"],
            "screen_x": frame["screen_x"],
            "actor_in_viewport": actor_in_view,
            "dark_pixels": frame["actor_dark_pixels"],
        }
    return crops


def run(upstream: Path, generated: Path, output: Path) -> dict:
    from PIL import Image
    output.mkdir(parents=True, exist_ok=True)
    base = scrolling_fixture()
    expected_cues = (CameraCue("set", 160), CameraCue("hold", ticks=120), CameraCue("pan", 480),
                     CameraCue("wait"), CameraCue("pan", 160), CameraCue("wait"))
    story = (Path(__file__).resolve().parents[2] / "examples" /
             "mini_story_chain.json").read_text(encoding="utf-8")
    width, height = base.geometry.room_width, base.geometry.room_height
    variants = {}
    for name in ("masked", "transparent", "wrong-box"):
        project = canonical_json(GameDocument("R06CameraWorldMask",
                              (base, destination_fixture())))
        project = author_room_camera_plan(
            project, "Harbor", 390, 100,
            "set:160;hold:120;pan:480;wait;pan:160;wait", stationary_actor=True)
        project = author_room_walkbox(project, "Harbor", 1,
                                      "0,70; 320,70; 320,150; 0,150")
        project = author_room_walkbox(project, "Harbor", 2,
                                      "320,70; 639,70; 639,150; 320,150")
        project = author_room_box_connections(project, "Harbor", "1-2")
        pixels = bytes(255 if name != "transparent" and 365 <= x < 420
                       and 60 < y < 110 else 0
                       for y in range(height) for x in range(width))
        png = output / f"{name}-zp01.png"
        Image.frombytes("L", (width, height), pixels).save(png)
        project = import_room_zplane(project, "Harbor", 1, str(png))
        project = author_room_walkbox_zplane(
            project, "Harbor", 1 if name == "wrong-box" else 2, 1)
        project = compose_story_project(story, project)
        (output / f"{name}-project.json").write_text(project, encoding="utf-8")
        parsed = parse_document(project)
        if canonical_json(parsed) != project:
            raise RuntimeError("Studio native project changed on JSON roundtrip")
        room = next(r for r in parsed.rooms if r.name == "Harbor")
        if (room.ego_start_x, room.ego_start_y) != (390, 100) or room.camera_cues != expected_cues:
            raise RuntimeError("Story composition dropped authorable actor/camera fields")
        if room.demo_walk_to_x is not None:
            raise RuntimeError("Story composition changed world-anchored Ego into a walking actor")
        if len(room.zplanes) != 1 or len(room.walkboxes) != 2:
            raise RuntimeError("Story composition dropped ZP01/BOXD")
        # A retained ZP01 slot is not enough: the authored PNG's actual
        # world-space pixels must survive JSON-v1 and Story composition.
        expected_mask = bytes(1 if pixel else 0 for pixel in pixels)
        if room.zplanes[0].index != 1 or room.zplanes[0].pixels != expected_mask:
            raise RuntimeError("Studio PNG ZP01 pixels changed during JSON/Story export")
        expected = [1, 0] if name == "wrong-box" else [0, 1]
        if [box.mask for box in room.walkboxes] != expected:
            raise RuntimeError("Wrong product-exported Z-plane assignment")
        try:
            render = render_native_room(room, upstream, generated, output, name,
                                        allow_static_scene=True, camera_pan_capture=True)
            frames = read_frames(output / f"{name}-screenshots")
            # Keep measurable native samples even if phase selection fails.
            # A missing return is a failed acceptance, not missing evidence.
            variants[name] = {"render": render, "frames": frames,
                              "walkbox_masks": expected}
            crops = export_actor_phase_crops(output / f"{name}-screenshots", frames)
        except Exception as error:
            # ScummVM can quit after recording useful native frames but
            # before render_native_room returns. Retain those measured
            # screenshots in the readable report without accepting a
            # partial camera round-trip.
            images = output / f"{name}-screenshots"
            times = images / "camera-frame-times.json"
            if name not in variants and times.is_file():
                try:
                    partial_frames = read_frames(images)
                    variants[name] = {
                        "frames": partial_frames,
                        "walkbox_masks": expected,
                        "capture_incomplete": True,
                    }
                except (OSError, ValueError, RuntimeError) as capture_error:
                    variants[name] = {
                        "walkbox_masks": expected,
                        "capture_incomplete": True,
                        "frame_read_error": str(capture_error),
                    }
            # Compilation/launch may fail before a complete three-game
            # comparison exists. Preserve the reached product path and
            # failure in CI, while keeping the native acceptance gate red.
            failure = {
                "product_path": "Studio PNG/Walkbox/Camera/Actor -> JSON-v1 -> Story -> ScummC-v6 -> stock ScummVM",
                "variants": variants,
                "failed_variant": name,
                "comparison": {"status": "failed", "reason": str(error)},
            }
            (output / "native-r06-camera-zp01-report.json").write_text(
                json.dumps(failure, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            raise
        variants[name] = {"render": render, "frames": frames,
                          "phase_actor_crops": crops,
                          "walkbox_masks": expected}
    report = {
        "product_path": "Studio PNG/Walkbox/Camera/Actor -> JSON-v1 -> Story -> ScummC-v6 -> stock ScummVM",
        "variants": variants,
        "comparison": {"status": "not_yet_verified"},
    }
    report_path = output / "native-r06-camera-zp01-report.json"
    try:
        report["comparison"] = verify_world_mask(variants)
    except (RuntimeError, ValueError) as error:
        report["comparison"] = {"status": "failed", "reason": str(error)}
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_camera_zp01_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])), indent=2))
