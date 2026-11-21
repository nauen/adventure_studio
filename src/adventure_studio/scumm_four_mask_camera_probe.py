"""R06: four simultaneous room Z-planes stay world-anchored through native camera travel.

The existing product path already authors four PNG Z-planes and the camera
cue sequence independently. This probe verifies their combined behavior in
unmodified stock ScummVM. Each target plane is tested with the complete
four-mask room active, plus transparent and wrong-walkbox controls.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .scumm_assets import destination_fixture, scrolling_fixture
from .scumm_project import GameDocument, canonical_json, parse_document
from .scumm_room_visual_probe import render_native_room
from .scumm_camera_zp01_probe import read_frames
from .studio_sequences import (
    author_room_box_connections,
    author_room_camera_plan,
    author_room_walkbox,
    author_room_walkbox_zplane,
    compose_story_project,
    import_room_zplane,
)

_TARGETS = (
    (1, 2, 240, 380, 380),
    (2, 3, 380, 380, 380),
    (3, 4, 480, 380, 380),
    (4, 5, 540, 400, 400),
)
_CAMERA_CUES = "set:160;hold:360;pan:480;wait;hold:120;pan:160;wait"
_EXPECTED_CUES = (
    ("set", 160, None), ("hold", None, 360), ("pan", 480, None),
    ("wait", None, None), ("hold", None, 120), ("pan", 160, None),
    ("wait", None, None),
)
_MASK_REGIONS = ((160, 320), (320, 400), (400, 500), (500, 640))


def select_actor_phases(rows: list[dict], world_x: int,
                        outgoing_x: int, returning_x: int) -> dict:
    """Select camera phases by observed world X, not assumed elapsed time."""
    if not rows:
        raise RuntimeError("No identifiable native camera frames")
    far_index = next((i for i, row in enumerate(rows)
                      if row["camera_x"] >= 475), None)
    if far_index is None:
        raise RuntimeError("Outgoing native camera pan never reached the far side")
    pre = next((row for row in rows[:far_index]
                if row["camera_x"] <= 165), None)
    far = rows[far_index]
    returned = next((row for row in rows[far_index + 1:]
                     if row["camera_x"] <= 165), None)

    def nearest(candidates: list[dict], target: int, phase: str) -> dict:
        row = min(candidates, key=lambda item: abs(item["camera_x"] - target),
                  default=None)
        if row is None or abs(row["camera_x"] - target) > 16:
            raise RuntimeError(f"Missing camera sample for {phase} at X={target}")
        if row["world_x"] != world_x or not 192 <= row["screen_x"] <= 831:
            raise RuntimeError(f"Actor is not visible at the {phase} camera phase")
        return row

    if pre is None or returned is None:
        raise RuntimeError("Missing initial or completed camera-return endpoint")
    outgoing = nearest(rows[:far_index], outgoing_x, "outgoing")
    returning = nearest(rows[far_index + 1:], returning_x, "returning")
    phases = {
        "before": pre, "outgoing": outgoing, "far": far,
        "returning": returning, "returned": returned,
    }
    ordered = [phases[name]["seconds"] for name in
               ("before", "outgoing", "far", "returning", "returned")]
    if ordered != sorted(ordered) or len(set(ordered)) != len(ordered):
        raise RuntimeError("Camera round-trip phases are not strictly time-ordered")
    if (pre["camera_x"] > 165 or far["camera_x"] < 475
            or returned["camera_x"] > 165):
        raise RuntimeError("Native camera missed authored 160→480→160 endpoints")
    for phase in ("outgoing", "returning"):
        if abs(phases[phase]["screen_x"] - far["screen_x"]) <= 110:
            raise RuntimeError(
                f"Visible Actor positions do not disprove a screen-fixed mask on {phase}")
    return phases


def verify_four_mask_camera(groups: dict[int, dict]) -> dict:
    """Every independent plane must occlude its own Actor through both pan directions."""
    if set(groups) != {1, 2, 3, 4}:
        raise ValueError("Need native camera evidence for all four room Z-planes")
    comparisons = {}
    for plane, box, world_x, outgoing_x, returning_x in _TARGETS:
        variants = groups[plane]
        if set(variants) != {"masked", "transparent", "wrong-box"}:
            raise ValueError(f"ZP{plane:02d} needs masked, transparent and wrong-box games")
        expected_masks = [0, 1, 2, 3, 4]
        wrong_masks = list(expected_masks)
        wrong_masks[box - 1] = 0
        wrong_masks[0] = plane
        for name, expected in (("masked", expected_masks),
                               ("transparent", expected_masks),
                               ("wrong-box", wrong_masks)):
            row = variants[name]
            if row["walkbox_masks"] != expected:
                raise RuntimeError(f"Native BOXD assignments changed: ZP{plane:02d}/{name}")
            if not row["frame_report"]["scroll_color_signature_passed"]:
                raise RuntimeError(f"Native camera did not render the scrolling room: ZP{plane:02d}/{name}")
            if row["world_x"] != world_x:
                raise RuntimeError(f"Wrong Actor world position: ZP{plane:02d}/{name}")
        phase_rows = {
            name: select_actor_phases(row["frames"], world_x, outgoing_x, returning_x)
            for name, row in variants.items()
        }
        phase_comparisons = {}
        for phase in ("outgoing", "returning"):
            masked = phase_rows["masked"][phase]
            transparent = phase_rows["transparent"][phase]
            wrong = phase_rows["wrong-box"][phase]
            for name, control in (("transparent", transparent), ("wrong-box", wrong)):
                if abs(control["camera_x"] - masked["camera_x"]) > 16:
                    raise RuntimeError(f"Camera phase mismatch for ZP{plane:02d}/{name}/{phase}")
                if control["actor_dark_pixels"] < 100:
                    raise RuntimeError(f"Actor is not visible in ZP{plane:02d}/{name}/{phase} control")
            if masked["actor_dark_pixels"] > transparent["actor_dark_pixels"] // 3:
                raise RuntimeError(f"ZP{plane:02d} did not occlude its Actor on {phase}")
            if masked["actor_dark_pixels"] > wrong["actor_dark_pixels"] // 3:
                raise RuntimeError(f"ZP{plane:02d} wrong-box control did not isolate the mask on {phase}")
            phase_comparisons[phase] = {
                "camera_x": masked["camera_x"],
                "screen_x": masked["screen_x"],
                "masked_pixels": masked["actor_dark_pixels"],
                "transparent_pixels": transparent["actor_dark_pixels"],
                "wrong_box_pixels": wrong["actor_dark_pixels"],
            }
        comparisons[f"ZP{plane:02d}"] = {
            "walkbox": box,
            "actor_world_x": world_x,
            "camera_phases": {
                name: {key: phase[name][key] for key in
                       ("camera_x", "screen_x", "seconds", "frame")}
                for name in ("before", "outgoing", "far", "returning", "returned")
                for phase in [phase_rows["masked"]]
            },
            "pixel_comparisons": phase_comparisons,
        }
    return {
        "native_four_masks_world_anchored_camera_pan_and_return_passed": True,
        "camera_cues": _CAMERA_CUES,
        "four_independent_planes_tested": True,
        "pixel_comparisons": comparisons,
    }


def _mask_pixels(width: int, height: int, start: int, end: int) -> bytes:
    return bytes(255 if start <= x < end and 60 < y < 110 else 0
                 for y in range(height) for x in range(width))


def _save_phase_crops(directory: Path, rows: list[dict],
                      phases: dict) -> dict:
    from PIL import Image

    crops = {}
    for name, frame in phases.items():
        source = directory / f"scummvm-{frame['frame']}.png"
        target = directory / f"scummvm-phase-{name}-actor.png"
        center = frame["screen_x"]
        if center > 831:
            left, right = 772, 831
        elif center < 192:
            left, right = 192, 251
        else:
            left, right = max(192, center - 30), min(831, center + 30)
        with Image.open(source) as screenshot:
            screenshot.convert("RGB").crop((left, 300, right + 1, 388)).save(target)
        crops[name] = {
            "screenshot": source.name, "actor_crop": target.name,
            "camera_x": frame["camera_x"], "screen_x": center,
            "world_x": frame["world_x"], "actor_dark_pixels": frame["actor_dark_pixels"],
            "elapsed_seconds": frame["seconds"],
        }
    return crops


def _author_project(output: Path, plane: int, variant: str,
                    world_x: int) -> tuple[str, list[int], dict]:
    from PIL import Image

    base = scrolling_fixture()
    width, height = base.geometry.room_width, base.geometry.room_height
    project = canonical_json(GameDocument(
        "R06FourMaskCamera", (base, destination_fixture())))
    project = author_room_camera_plan(
        project, "Harbor", world_x, 100, _CAMERA_CUES, stationary_actor=True)
    for index, corners in (
        (1, "0,70; 160,70; 160,150; 0,150"),
        (2, "160,70; 320,70; 320,150; 160,150"),
        (3, "320,70; 400,70; 400,150; 320,150"),
        (4, "400,70; 500,70; 500,150; 400,150"),
        (5, "500,70; 639,70; 639,150; 500,150"),
    ):
        project = author_room_walkbox(project, "Harbor", index, corners)
    project = author_room_box_connections(project, "Harbor", "1-2; 2-3; 3-4; 4-5")

    expected_masks = [0, 1, 2, 3, 4]
    if variant == "wrong-box":
        target_box = plane + 1
        expected_masks[target_box - 1] = 0
        expected_masks[0] = plane

    mask_files = []
    mask_bounds = {}
    for index, (start, end) in enumerate(_MASK_REGIONS, 1):
        pixels = (_mask_pixels(width, height, start, end)
                  if variant != "transparent" else bytes(width * height))
        path = output / f"zp{plane:02d}-{variant}-zp{index:02d}.png"
        Image.frombytes("L", (width, height), pixels).save(path)
        mask_files.append(path.name)
        project = import_room_zplane(project, "Harbor", index, str(path))
        occupied = [position for position, value in enumerate(pixels) if value]
        mask_bounds[f"ZP{index:02d}"] = {
            "opaque_pixels": len(occupied),
            "world_bounds": ([min(pos % width for pos in occupied),
                              min(pos // width for pos in occupied),
                              max(pos % width for pos in occupied),
                              max(pos // width for pos in occupied)]
                             if occupied else None),
        }
    for index in range(1, 5):
        project = author_room_walkbox_zplane(project, "Harbor", index + 1, index)
    if variant == "wrong-box":
        project = author_room_walkbox_zplane(project, "Harbor", plane + 1, 0)
        project = author_room_walkbox_zplane(project, "Harbor", 1, plane)

    story = (Path(__file__).resolve().parents[2] / "examples" /
             "mini_story_chain.json").read_text(encoding="utf-8")
    project = compose_story_project(story, project)
    parsed = parse_document(project)
    if canonical_json(parsed) != project:
        raise RuntimeError("Four-mask camera project changed during JSON-v1 roundtrip")
    room = next(item for item in parsed.rooms if item.name == "Harbor")
    actual_cues = tuple((cue.operation, cue.x, cue.ticks) for cue in room.camera_cues)
    if actual_cues != _EXPECTED_CUES:
        raise RuntimeError("Story composition changed the native camera cue sequence")
    if len(room.zplanes) != 4 or len(room.walkboxes) != 5:
        raise RuntimeError("Story composition lost four Z-planes or five walkboxes")
    expected_planes = tuple(
        bytes(1 if value else 0 for value in (
            _mask_pixels(width, height, start, end)
            if variant != "transparent" else bytes(width * height)))
        for start, end in _MASK_REGIONS)
    if tuple(plane.pixels for plane in room.zplanes) != expected_planes:
        raise RuntimeError("Studio PNG pixels changed during JSON-v1/Story composition")
    if (room.ego_start_x, room.ego_start_y) != (world_x, 100) or room.demo_walk_to_x is not None:
        raise RuntimeError("Story composition lost the authored stationary Actor/world position")
    if [box.mask for box in room.walkboxes] != expected_masks:
        raise RuntimeError("Story composition changed four independent BOXD mask assignments")
    return project, expected_masks, {
        "mask_files": mask_files, "mask_bounds": mask_bounds,
        "camera_cues": [cue.operation for cue in room.camera_cues],
        "walkbox_masks": expected_masks,
    }


def run(upstream: Path, generated: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    groups = {}
    report = {
        "product_path": "Studio PNG + BOXD + native camera cues → RoomAsset/JSON-v1 → Story → ScummC-v6 → stock ScummVM",
        "targets": {},
        "comparison": {"status": "in_progress"},
    }
    for plane, box, world_x, outgoing_x, returning_x in _TARGETS:
        group = {}
        for variant in ("masked", "transparent", "wrong-box"):
            label = f"zp{plane:02d}-{variant}"
            project, assignments, authoring = _author_project(output, plane, variant, world_x)
            project_path = output / f"{label}-project.json"
            project_path.write_text(project, encoding="utf-8")
            room = next(item for item in parse_document(project).rooms if item.name == "Harbor")
            try:
                render = render_native_room(
                    room, upstream, generated, output, label,
                    allow_static_scene=True, camera_pan_capture=True)
                frames = read_frames(output / f"{label}-screenshots", world_x)
                phases = select_actor_phases(frames, world_x, outgoing_x, returning_x)
                crops = _save_phase_crops(output / f"{label}-screenshots", frames, phases)
                group[variant] = {
                    "render": render, "frames": frames, "world_x": world_x,
                    "walkbox_masks": assignments, "frame_report": render["frame_report"],
                    "phase_actor_crops": crops, "authoring": authoring,
                }
            except Exception as error:
                images = output / f"{label}-screenshots"
                times = images / "camera-frame-times.json"
                if times.is_file():
                    try:
                        frames = read_frames(images, world_x)
                        group[variant] = {
                            "frames": frames, "world_x": world_x,
                            "walkbox_masks": assignments, "authoring": authoring,
                            "capture_incomplete": True,
                            "failure": str(error),
                        }
                    except (OSError, ValueError, RuntimeError) as capture_error:
                        group[variant] = {
                            "walkbox_masks": assignments, "authoring": authoring,
                            "capture_incomplete": True,
                            "failure": str(error), "frame_read_error": str(capture_error),
                        }
                report["targets"][f"ZP{plane:02d}"] = group
                report["failed_variant"] = label
                report["comparison"] = {"status": "failed", "reason": str(error)}
                (output / "native-r06-four-mask-camera-report.json").write_text(
                    json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                raise
        groups[plane] = group
        report["targets"][f"ZP{plane:02d}"] = group
        report["comparison"] = {"status": "in_progress"}
        (output / "native-r06-four-mask-camera-report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        report["comparison"] = verify_four_mask_camera(groups)
    except (RuntimeError, ValueError) as error:
        report["comparison"] = {"status": "failed", "reason": str(error)}
        (output / "native-r06-four-mask-camera-report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise
    (output / "native-r06-four-mask-camera-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_four_mask_camera_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])), indent=2))
