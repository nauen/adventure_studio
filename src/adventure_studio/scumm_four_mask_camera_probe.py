"""R06: four simultaneous room Z-planes stay world-anchored through native camera travel.

The existing product path already authors four PNG Z-planes and the camera
cue sequence independently. This probe verifies their combined behavior in
unmodified stock ScummVM. Each target plane is tested with the complete
four-mask room active, plus transparent and wrong-walkbox controls.
"""
from __future__ import annotations

import json
import sys
from dataclasses import replace
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
    (1, 2, 240, 380, 280),
    (2, 3, 380, 420, 320),
    (3, 4, 479, 420, 352),
    (4, 5, 505, 460, 380),
)
_CAMERA_CUES = "set:160;hold:360;pan:480;wait;hold:120;pan:160;wait"
# Native moving-Actor variant: follow the Actor while crossing all Z-planes,
# then explicitly pan out and back to verify camera independence.
_MOVING_CAMERA_CUES = "set:160;follow_ego;hold:700;pan:480;wait;hold:120;pan:160;wait"
_EXPECTED_CUES = (
    ("set", 160, None), ("hold", None, 360), ("pan", 480, None),
    ("wait", None, None), ("hold", None, 120), ("pan", 160, None),
    ("wait", None, None),
)
_MOVING_EXPECTED_CUES = (
    ("set", 160, None), ("follow_ego", None, None),
    ("hold", None, 700), ("pan", 480, None),
    ("wait", None, None), ("hold", None, 120),
    ("pan", 160, None), ("wait", None, None),
)
_MASK_REGIONS = ((160, 320), (320, 400), (400, 500), (500, 640))


def track_native_actor(directory: Path) -> list[dict]:
    """Locate the dark costume from actual native screenshots, not scripted X.

    Only a visible costume can be tracked: run this on the transparent-control
    game. Consecutive frames are not interpolated or assigned guessed X.
    """
    from PIL import Image
    from .scumm_camera_zp01_probe import camera_from_sky

    entries = json.loads(
        (directory / "camera-frame-times.json").read_text(encoding="utf-8"))
    rows = []
    for entry in entries:
        with Image.open(directory / f"scummvm-{entry['frame']}.png") as image:
            camera_x = camera_from_sky(image)
            if camera_x is None:
                continue
            rgb = image.convert("RGB")
            # Count dark pixels in each viewport column at costume height.
            # Require a compact high-density peak; reject loading screens,
            # text, or scattered background artifacts rather than guessing.
            columns = [
                sum(1 for y in range(305, 388)
                    if max(rgb.getpixel((x, y))) <= 12)
                for x in range(192, 832)
            ]
        peaks = []
        for center in range(15, len(columns) - 15):
            score = sum(columns[center - 15:center + 16])
            if score >= 100:
                peaks.append((score, center))
        if not peaks:
            continue
        peak, center = max(peaks)
        # Reject equally strong, spatially separated costume candidates.
        if any(score >= peak * 0.85 and abs(other - center) > 50
               for score, other in peaks):
            continue
        screen_x = 192 + center
        world_x = round((screen_x - 192) / 2 + camera_x - 160)
        rows.append({
            "frame": entry["frame"], "seconds": entry["elapsed_seconds"],
            "camera_x": camera_x, "screen_x": screen_x,
            "world_x": world_x, "actor_dark_pixels": peak,
        })
    if not rows:
        raise RuntimeError("No independently identifiable native Actor pixels")
    return rows


def track_native_camera(directory: Path) -> list[dict]:
    """Measure native camera position even when the walking Actor is offscreen."""
    from PIL import Image
    from .scumm_camera_zp01_probe import camera_from_sky

    entries = json.loads(
        (directory / "camera-frame-times.json").read_text(encoding="utf-8"))
    rows = []
    for entry in entries:
        with Image.open(directory / f"scummvm-{entry['frame']}.png") as image:
            camera_x = camera_from_sky(image)
        if camera_x is not None:
            rows.append({
                "seconds": entry["elapsed_seconds"],
                "camera_x": camera_x,
                "frame": entry["frame"],
            })
    if not rows:
        raise RuntimeError("No measurable native camera frames")
    return rows


def verify_moving_actor_crosses_four_masks(
        frames: list[dict], camera_frames: list[dict] | None = None) -> dict:
    """Fail closed unless *observed* native frames prove walking through four zones.

    Camera movement alone is insufficient: unlike the earlier stationary-actor
    probe, actor world X must change while the camera traverses both directions.
    """
    if not frames:
        raise RuntimeError("Missing native moving-actor screenshots")
    ordered = sorted(frames, key=lambda row: row["seconds"])
    if len({row["seconds"] for row in ordered}) != len(ordered):
        raise RuntimeError("Native moving-actor frame timestamps are not unique")
    zones = ((160, 320), (320, 400), (400, 500), (500, 640))
    visited = []
    moving = 0
    for previous, current in zip(ordered, ordered[1:]):
        if current["seconds"] <= previous["seconds"]:
            raise RuntimeError("Native moving-actor frames are not time ordered")
        if current["world_x"] != previous["world_x"]:
            moving += 1
        if not 0 <= current["camera_x"] <= 640:
            raise RuntimeError("Invalid measured native camera X")
    for index, (left, right) in enumerate(zones, 1):
        observations = [row for row in ordered
                        if left <= row["world_x"] < right]
        if not observations:
            raise RuntimeError(f"Moving Actor never entered ZP{index:02d} region")
        visited.append({"zplane": index,
                        "first_seconds": observations[0]["seconds"],
                        "world_x": observations[0]["world_x"]})
    if moving < 4:
        raise RuntimeError("Stationary Actor cannot establish four-zone walking")
    if [row["first_seconds"] for row in visited] != sorted(
            row["first_seconds"] for row in visited):
        raise RuntimeError("Actor did not cross the four mask regions in order")
    camera = [row["camera_x"] for row in (
        camera_frames if camera_frames is not None else ordered)]
    far = next((i for i, x in enumerate(camera) if x >= 475), None)
    if (far is None or not any(x <= 165 for x in camera[:far])
            or not any(x <= 165 for x in camera[far + 1:])):
        raise RuntimeError("Native camera did not complete 160→480→160")
    return {"native_moving_actor_four_mask_path_observed": True,
            "moving_frame_transitions": moving,
            "visited_zplanes": visited,
            "camera_far_frame_index": far}


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

    def nearest(candidates: list[dict], target: int, phase: str,
                separated_from: float | None = None) -> dict:
        # Stock ScummVM captures advance by up to 40 world units per frame.
        # Select among actually observed positions, never synthesize frames.
        eligible = [row for row in candidates
                    if abs(row["camera_x"] - target) <= 40]
        if not eligible:
            raise RuntimeError(f"Missing camera sample for {phase} at X={target}")
        if separated_from is not None:
            # At 2x screen scale, >55 camera units establish >110 pixels
            # of parallax. Independent games can sample different steps.
            separated = [row for row in eligible
                         if abs(row["camera_x"] - separated_from) > 55]
            if not separated:
                raise RuntimeError(
                    "Visible Actor positions do not disprove a screen-fixed mask")
            eligible = separated
        row = min(eligible, key=lambda item: abs(item["camera_x"] - target))
        if row["world_x"] != world_x or not 192 <= row["screen_x"] <= 831:
            raise RuntimeError(f"Actor is not visible at the {phase} camera phase")
        return row

    if pre is None or returned is None:
        raise RuntimeError("Missing initial or completed camera-return endpoint")
    outgoing = nearest(rows[:far_index], outgoing_x, "outgoing")
    returning = nearest(rows[far_index + 1:], returning_x, "returning",
                        separated_from=outgoing["camera_x"])
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
    if abs(outgoing["screen_x"] - returning["screen_x"]) <= 110:
        raise RuntimeError("Visible Actor positions do not disprove a screen-fixed mask")
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
            # render_native_room compares the *first and last* scene frames.
            # This authored pan deliberately returns to camera X=160, so the
            # two sky colors must be identical (scroll_expected=False).
            # Require real frame variation here; select_actor_phases below
            # independently proves the entire observed 160→480→160 journey.
            frame_report = row["frame_report"]
            if (not frame_report["frame_variation_passed"]
                    or frame_report["changed_pixels"] <= 0):
                raise RuntimeError(
                    f"Native room has no rendered frame variation: ZP{plane:02d}/{name}")
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
                # Independent ScummVM runs are captured asynchronously.
                # Their nearest frames can be one native camera step apart.
                if abs(control["camera_x"] - masked["camera_x"]) > 40:
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
                    world_x: int, *, moving_actor: bool = False) -> tuple[str, list[int], dict]:
    from PIL import Image

    base = scrolling_fixture()
    width, height = base.geometry.room_width, base.geometry.room_height
    project = canonical_json(GameDocument(
        "R06FourMaskCamera", (base, destination_fixture())))
    project = author_room_camera_plan(
        project, "Harbor", world_x, 100,
        _MOVING_CAMERA_CUES if moving_actor else _CAMERA_CUES,
        stationary_actor=not moving_actor)
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
    if moving_actor:
        # Use the product's existing demo-walk SCUMM opcode, not a probe-only
        # scripted Actor teleport or a second runtime.
        document = parse_document(project)
        rooms = tuple(
            replace(room, demo_walk_to_x=535) if room.name == "Harbor" else room
            for room in document.rooms)
        project = canonical_json(replace(document, rooms=rooms))
    parsed = parse_document(project)
    if canonical_json(parsed) != project:
        raise RuntimeError("Four-mask camera project changed during JSON-v1 roundtrip")
    room = next(item for item in parsed.rooms if item.name == "Harbor")
    actual_cues = tuple((cue.operation, cue.x, cue.ticks) for cue in room.camera_cues)
    if actual_cues != (_MOVING_EXPECTED_CUES if moving_actor else _EXPECTED_CUES):
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
    if ((room.ego_start_x, room.ego_start_y) != (world_x, 100)
            or room.demo_walk_to_x != (535 if moving_actor else None)):
        raise RuntimeError("Story composition lost the authored Actor walk/world position")
    if [box.mask for box in room.walkboxes] != expected_masks:
        raise RuntimeError("Story composition changed four independent BOXD mask assignments")
    return project, expected_masks, {
        "mask_files": mask_files, "mask_bounds": mask_bounds,
        "camera_cues": [cue.operation for cue in room.camera_cues],
        "walkbox_masks": expected_masks,
    }



def verify_moving_actor_native_occlusion(
        control: list[dict], masked: list[dict],
        wrong_box: dict[int, list[dict]]) -> dict:
    """Compare observed native costume pixels at matching times/camera/positions."""
    if set(wrong_box) != {1, 2, 3, 4}:
        raise ValueError("Every Z-plane needs its own wrong-box native game")
    regions = ((160, 320), (320, 400), (400, 500), (500, 640))
    results = {}
    for plane, (left, right) in enumerate(regions, 1):
        matches = []
        for reference in control:
            if not left <= reference["world_x"] < right:
                continue
            def nearest(rows):
                eligible = [
                    row for row in rows
                    if abs(row["seconds"] - reference["seconds"]) <= 0.3
                    and abs(row["camera_x"] - reference["camera_x"]) <= 40
                    and abs(row["world_x"] - reference["world_x"]) <= 12
                ]
                return min(eligible, key=lambda row: (
                    abs(row["seconds"] - reference["seconds"]),
                    abs(row["world_x"] - reference["world_x"]))) if eligible else None
            actual = nearest(masked)
            wrong = nearest(wrong_box[plane])
            if actual is None or wrong is None:
                continue
            if (reference["actor_dark_pixels"] >= 100
                    and wrong["actor_dark_pixels"] >= 100
                    and actual["actor_dark_pixels"] <= reference["actor_dark_pixels"] // 3
                    and actual["actor_dark_pixels"] <= wrong["actor_dark_pixels"] // 3):
                matches.append({
                    "frame": reference["frame"], "world_x": reference["world_x"],
                    "seconds": reference["seconds"],
                    "masked_pixels": actual["actor_dark_pixels"],
                    "transparent_pixels": reference["actor_dark_pixels"],
                    "wrong_box_pixels": wrong["actor_dark_pixels"],
                })
        if not matches:
            raise RuntimeError(
                f"ZP{plane:02d} lacks synchronized native masked/transparent/wrong-box occlusion")
        results[f"ZP{plane:02d}"] = matches
    return {"native_moving_actor_four_zplanes_occlusion_passed": True,
            "per_plane": results}


def measure_native_costume_at_control_positions(
        directory: Path, control: list[dict]) -> list[dict]:
    """Sample a masked game where the transparent game actually saw the Actor."""
    from PIL import Image
    from .scumm_camera_zp01_probe import camera_from_sky, costume_pixels

    entries = json.loads(
        (directory / "camera-frame-times.json").read_text(encoding="utf-8"))
    rows = []
    for entry in entries:
        reference = min(control, key=lambda row: abs(
            row["seconds"] - entry["elapsed_seconds"]))
        if abs(reference["seconds"] - entry["elapsed_seconds"]) > 0.3:
            continue
        with Image.open(directory / f"scummvm-{entry['frame']}.png") as image:
            camera_x = camera_from_sky(image)
            if camera_x is None or abs(camera_x - reference["camera_x"]) > 40:
                continue
            pixels = costume_pixels(image, reference["world_x"], camera_x)
        rows.append({
            "frame": entry["frame"], "seconds": entry["elapsed_seconds"],
            "camera_x": camera_x, "world_x": reference["world_x"],
            "screen_x": round(192 + 2 * (reference["world_x"] - camera_x + 160)),
            "actor_dark_pixels": pixels,
        })
    if not rows:
        raise RuntimeError("No synchronized native costume samples")
    return rows


def run_moving_actor(upstream: Path, generated: Path, output: Path) -> dict:
    """Run native moving-Actor export, with independent control per Z-plane."""
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "product_path": "Studio PNG → RoomAsset/JSON-v1/Story → ScummC-v6 → stock ScummVM",
        "actor_start_x": 170,
        "actor_walk_goal_x": 535,
        "status": "in_progress",
        "variants": {},
    }
    report_path = output / "native-r06-moving-four-mask-report.json"
    variants = [("transparent", 1), ("masked", 1)] + [
        (f"wrong-box-zp{plane:02d}", plane) for plane in range(1, 5)]
    try:
        for variant, plane in variants:
            label = f"moving-four-{variant}"
            authored_variant = "wrong-box" if variant.startswith("wrong-box") else variant
            project, assignments, authoring = _author_project(
                output, plane, authored_variant, 170, moving_actor=True)
            (output / f"{label}-project.json").write_text(project, encoding="utf-8")
            room = next(item for item in parse_document(project).rooms
                        if item.name == "Harbor")
            render = render_native_room(
                room, upstream, generated, output, label,
                allow_static_scene=True, camera_pan_capture=True)
            screenshots = output / f"{label}-screenshots"
            report["variants"][variant] = {
                "walkbox_masks": assignments,
                "authoring": authoring,
                "frame_report": render["frame_report"],
                "screenshot_directory": str(screenshots),
            }
            report_path.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8")
        control = track_native_actor(
            output / "moving-four-transparent-screenshots")
        report["actor_tracking"] = {
            "source": "transparent stock-ScummVM screenshot pixels",
            "observations": control,
            "world_x_range": [
                min(row["world_x"] for row in control),
                max(row["world_x"] for row in control),
            ],
            "camera_x_range": [
                min(row["camera_x"] for row in control),
                max(row["camera_x"] for row in control),
            ],
        }
        # Persist raw observations *before* the fail-closed motion assertion.
        # Otherwise a red CI job hides whether the native Actor did not walk
        # or the screenshot detector rejected valid positions.
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        camera_observations = track_native_camera(
            output / "moving-four-transparent-screenshots")
        report["camera_tracking"] = camera_observations
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        report["motion"] = verify_moving_actor_crosses_four_masks(
            control, camera_observations)
        masked = measure_native_costume_at_control_positions(
            output / "moving-four-masked-screenshots", control)
        wrong = {
            plane: measure_native_costume_at_control_positions(
                output / f"moving-four-wrong-box-zp{plane:02d}-screenshots",
                control)
            for plane in range(1, 5)
        }
        report["comparison"] = verify_moving_actor_native_occlusion(
            control, masked, wrong)
        report["status"] = "passed"
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        return report
    except Exception as error:
        report["status"] = "failed"
        report["failure"] = str(error)
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        raise


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
    if len(sys.argv) == 5 and sys.argv[1] == "--moving":
        result = run_moving_actor(
            Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
    elif len(sys.argv) == 4:
        result = run(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        raise SystemExit(
            "Usage: python -m adventure_studio.scumm_four_mask_camera_probe "
            "[--moving] UPSTREAM GENERATED OUTPUT")
    print(json.dumps(result, indent=2))
