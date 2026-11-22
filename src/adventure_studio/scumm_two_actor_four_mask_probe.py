"""R06 #268: stock-ScummVM smoke for two authored Actors and four room Z-planes.

This is the first native integration stage, NOT proof that both Actors move
independently or that each is occluded throughout a camera round-trip.
Those additional gameplay conditions require separate captured evidence.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

from .scumm_costume_probe import gesture_fixture
from .scumm_four_mask_camera_probe import _author_project, _MASK_REGIONS
from .studio_sequences import (author_room_camera_plan, import_room_zplane,
                               author_room_walkbox_zplane)
from .scumm_launch import launch_smoke
from .scumm_project import (ActorAsset, InteractionSequence, WalkActorStep, WaitActorStep,
                            canonical_json, export_document, parse_document)
from .scumm_toolchain import compile_story_game


ACTOR_IDS = ("ForegroundWalker", "BackgroundWalker")
ACTOR_STARTS = ((190, 85), (220, 135))


def author_two_actor_four_mask_project(output: Path, *, variant: str = "masked") -> str:
    """Use productive Studio Z-plane/camera authoring, then add typed Actors."""
    output.mkdir(parents=True, exist_ok=True)
    if variant not in ("masked", "transparent", "wrong-box"):
        raise ValueError("R06 only allows independent native masked/transparent/wrong-box games")
    raw, assignments, _ = _author_project(output, 1, variant, 170,
                                          moving_actor=True)
    # Stabilize the click target before the later native camera round-trip.
    # Follow-Ego during the click previously moved the target out of view.
    # Both distinct costume lanes must intersect every Z-plane: the original
    # single-Ego R06 mask ends at Y=110 and cannot occlude our second Actor.
    # Re-author taller masks as real Studio PNGs through the production API.
    if variant == "masked":
        from PIL import Image
        for plane, (left, right) in enumerate(_MASK_REGIONS, 1):
            pixels = bytes(255 if left <= x < right and 60 < y < 140 else 0
                           for y in range(200) for x in range(640))
            png = output / f"r06-two-actor-zp{plane:02d}.png"
            Image.frombytes("L", (640, 200), pixels).save(png)
            raw = import_room_zplane(raw, "Harbor", plane, str(png))
    if variant == "wrong-box":
        # Keep four real opaque PNGs, but disconnect all four relevant boxes
        # from their Z-planes. The first plane is assigned to wrong box 1.
        for box_index in (3, 4, 5):
            raw = author_room_walkbox_zplane(raw, "Harbor", box_index, 0)
        assignments = [1, 0, 0, 0, 0]
    raw = author_room_camera_plan(
        raw, "Harbor", 170, 100,
        "set:320;hold:30;pan:480;wait;hold:120;pan:160;wait;set:320",
        stationary_actor=True)
    document = parse_document(raw)
    costume = replace(gesture_fixture(), name="R06TwoActor" + variant.replace("-", "").title() + "Costume")
    actors = tuple(ActorAsset(name, costume.name, "Harbor", x, y, "S", name)
                   for name, (x, y) in zip(ACTOR_IDS, ACTOR_STARTS))
    choreography = InteractionSequence(
        "Harbor", "Key", "Close", (
            WalkActorStep(ACTOR_IDS[0], 530, 85),
            WalkActorStep(ACTOR_IDS[1], 540, 135),
            WaitActorStep(ACTOR_IDS[0]),
            WaitActorStep(ACTOR_IDS[1]),
        ))
    document = replace(document, costumes=(*document.costumes, costume),
                       actors=(*document.actors, *actors),
                       interaction_sequences=(*document.interaction_sequences, choreography))
    result = canonical_json(document)
    parsed = parse_document(result)
    assert_native_two_actor_authoring(parsed, assignments, variant=variant)
    return result


def assert_native_two_actor_authoring(document, expected_masks=(0, 1, 2, 3, 4),
                                      *, variant: str = "masked") -> dict:
    """Fail closed before export if the independent actor bindings are lost."""
    room = next((room for room in document.rooms if room.name == "Harbor"), None)
    if room is None or len(room.zplanes) != 4 or len(room.walkboxes) != 5:
        raise RuntimeError("R06 requires four Z-planes and five connected walkboxes")
    if [box.mask for box in room.walkboxes] != list(expected_masks):
        raise RuntimeError("R06 four native BOXD mask assignments changed")
    if variant not in ("masked", "transparent", "wrong-box"):
        raise ValueError("Unknown R06 native mask-control variant")
    if variant != "transparent":
        for plane, (left, right) in zip(room.zplanes, _MASK_REGIONS):
            center_x = (left + right) // 2
            if any(plane.pixels[y * 640 + center_x] == 0 for y in (80, 125)):
                raise RuntimeError("R06 mask does not cover both Actor costume lanes")
    elif any(any(plane.pixels) for plane in room.zplanes):
        raise RuntimeError("Transparent two-Actor control still contains opaque masks")
    by_id = {actor.id: actor for actor in document.actors}
    if any(name not in by_id for name in ACTOR_IDS):
        raise RuntimeError("R06 independent Actors missing from JSON-v1")
    if len(set(ACTOR_IDS)) != 2 or any(
            (by_id[name].room, by_id[name].x, by_id[name].y) !=
            ("Harbor", x, y)
            for name, (x, y) in zip(ACTOR_IDS, ACTOR_STARTS)):
        raise RuntimeError("R06 independent Actor world positions changed")
    if len({(by_id[name].x, by_id[name].y) for name in ACTOR_IDS}) != 2:
        raise RuntimeError("R06 Actors are not independently positioned")
    names = {costume.name for costume in document.costumes}
    if any(by_id[name].costume not in names for name in ACTOR_IDS):
        raise RuntimeError("R06 Actors have unresolved native COST bindings")
    operations = tuple(cue.operation for cue in room.camera_cues)
    if room.demo_walk_to_x is not None or operations != (
            "set", "hold", "pan", "wait", "hold", "pan", "wait", "set"):
        raise RuntimeError("R06 stable-click camera round-trip plan was lost")
    choreography = [sequence for sequence in document.interaction_sequences
                    if (sequence.room, sequence.hotspot_id, sequence.verb) ==
                    ("Harbor", "Key", "Close")]
    expected_steps = (
        WalkActorStep(ACTOR_IDS[0], 530, 85),
        WalkActorStep(ACTOR_IDS[1], 540, 135),
        WaitActorStep(ACTOR_IDS[0]),
        WaitActorStep(ACTOR_IDS[1]),
    )
    if len(choreography) != 1 or choreography[0].steps != expected_steps:
        raise RuntimeError("Independent native Actor walk commands missing")
    if any(not (160 <= by_id[name].x < 320 and 500 <= target.x < 640)
           for name, target in zip(ACTOR_IDS, expected_steps[:2])):
        raise RuntimeError("Each Actor must walk through all four Z-plane regions")
    return {"four_zplanes": True, "native_actor_count": len(ACTOR_IDS),
            "actor_ids": list(ACTOR_IDS), "distinct_actor_positions": True,
            "camera_roundtrip_authored": True,
            "two_native_actor_walks_authored": True,
            "both_actor_routes_span_all_four_masks": True,
            "independent_actor_motion_verified": False,
            "per_actor_native_occlusion_verified": False}



def play_two_actor_walk(output: Path, capture_frame, process) -> dict:
    """Click real native Close/Key action; retain every frame without faking motion."""
    from .scumm_launch import colored_item_center

    # The native room entry runs the camera cues before showing verbs.
    # Wait for actual toolbar pixels rather than an elapsed-time guess.
    from PIL import Image
    toolbar_deadline = time.monotonic() + 20
    while True:
        if process.poll() is not None:
            raise RuntimeError("ScummVM exited before native verbs were visible")
        capture_frame("r06-two-actor-before")
        with Image.open(output / "scummvm-r06-two-actor-before.png") as image:
            pixels = image.convert("RGB")
            toolbar_pixels = sum(1 for y in range(535, 635, 4)
                                 for x in range(200, 820, 4)
                                 if max(pixels.getpixel((x, y))) > 35)
        if toolbar_pixels >= 15:
            break
        if time.monotonic() >= toolbar_deadline:
            raise RuntimeError("Native verbs never appeared after camera entry sequence")
        time.sleep(0.25)
    key_x, key_y = colored_item_center(
        output, "r06-two-actor-before", (255, 220, 75))
    if not (192 <= key_x <= 831 and 184 <= key_y <= 471):
        raise RuntimeError("Authored Key is not visible for native R06 Actor input")
    initiated = time.monotonic()
    for x, y in ((234, 563), (key_x, key_y)):
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                       check=True, timeout=10)
        time.sleep(0.15)
    captured = []
    for index in range(80):
        if process.poll() is not None:
            raise RuntimeError("Stock ScummVM quit during two-Actor native walk")
        label = f"r06-two-actor-walk-{index:02d}"
        capture_frame(label)
        captured.append({"frame": label,
                         "seconds_since_native_input": round(time.monotonic() - initiated, 3)})
        time.sleep(0.3)
    result = {"click_verb": "Close", "click_hotspot": "Key",
              "native_hotspot_screen_position": [key_x, key_y],
              "captured_frames": captured,
              "independent_actor_motion_verified": False,
              "four_mask_per_actor_occlusion_verified": False}
    (output / "r06-two-actor-walk-capture.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def track_native_actor_lanes(screenshots: Path) -> dict:
    """Measure both costumes in separate vertical lanes of stock ScummVM frames.

    This uses actual costume pixels, not the authored Actor destination.
    The upper/lower ROIs exclude Ego and the toolbar by construction.
    """
    from PIL import Image
    from .scumm_camera_zp01_probe import camera_from_sky
    metadata = json.loads((screenshots / "r06-two-actor-walk-capture.json").read_text())
    bands = {"ForegroundWalker": (312, 343),
             "BackgroundWalker": (418, 448)}
    observations = {name: [] for name in ACTOR_IDS}
    for entry in metadata["captured_frames"]:
        with Image.open(screenshots / f"scummvm-{entry['frame']}.png") as frame:
            rgb = frame.convert("RGB")
            camera_x = camera_from_sky(rgb)
            if camera_x is None:
                continue
            for name, (top, bottom) in bands.items():
                counts = [sum(1 for y in range(top, bottom)
                              if max(rgb.getpixel((x, y))) <= 24)
                          for x in range(192, 832)]
                clusters = []
                begin = None
                for index, count in enumerate((*counts, 0)):
                    # Studio COST renders an opaque vertical costume rectangle;
                    # Ego is a scattered silhouette in the same upper lane.
                    active = count >= 22
                    if active and begin is None:
                        begin = index
                    elif not active and begin is not None:
                        end = index
                        total = sum(counts[begin:end])
                        if end - begin >= 5 and total >= 60:
                            clusters.append((total, (begin + end) // 2))
                        begin = None
                if len(clusters) != 1:
                    continue
                _, screen = clusters[0]
                screen_x = 192 + screen
                world_x = round((screen_x - 192) / 2 + camera_x - 160)
                observations[name].append({
                    "frame": entry["frame"],
                    "seconds": entry["seconds_since_native_input"],
                    "camera_x": camera_x, "world_x": world_x,
                    "screen_x": screen_x})
    return observations


def verify_two_actor_native_walks(traces: dict) -> dict:
    """Reject stationary actors, camera-only motion and missing Z-mask zones."""
    if set(traces) != set(ACTOR_IDS):
        raise RuntimeError("Missing independently tracked native Actors")
    zones = ((160, 320), (320, 400), (400, 500), (500, 640))
    results = {}
    for actor in ACTOR_IDS:
        trace = sorted(traces[actor], key=lambda row: row["seconds"])
        if len(trace) < 8 or len({row["frame"] for row in trace}) != len(trace):
            raise RuntimeError(f"{actor} has too few native costume frames")
        distinct_world = {row["world_x"] for row in trace}
        if max(distinct_world) - min(distinct_world) < 250:
            raise RuntimeError(f"{actor} did not independently walk across room")
        visited = [next((row["seconds"] for row in trace
                         if left <= row["world_x"] < right), None)
                   for left, right in zones]
        if any(value is None for value in visited):
            raise RuntimeError(f"{actor} did not cross every native mask zone")
        if visited != sorted(visited):
            raise RuntimeError(f"{actor} visited native mask zones out of order")
        results[actor] = {"observed_frame_count": len(trace),
                          "world_x_bounds": [min(distinct_world), max(distinct_world)],
                          "zone_first_seconds": visited}
    if traces[ACTOR_IDS[0]] == traces[ACTOR_IDS[1]]:
        raise RuntimeError("Two Actor traces are not independently measured")
    return {"two_independent_native_actor_walks_verified": True,
            "tracks": results}


def run(upstream: Path, output: Path) -> dict:
    """Run separate masked and transparent stock-ScummVM gameplay controls."""
    output.mkdir(parents=True, exist_ok=True)
    report = {"product_path": "Studio PNG -> JSON-v1/Story -> ScummC-v6 -> stock ScummVM",
              "variants": {}, "independent_actor_motion_verified": False,
              "per_actor_native_occlusion_verified": False,
              "complete_r06_268_acceptance": False}
    report_path = output / "native-r06-two-actor-four-mask-report.json"
    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        root.mkdir(parents=True, exist_ok=True)
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        project = author_two_actor_four_mask_project(root, variant=variant)
        (build / "project.json").write_text(project, encoding="utf-8")
        document = parse_document(project)
        expected_masks = ([1, 0, 0, 0, 0] if variant == "wrong-box"
                          else [0, 1, 2, 3, 4])
        authoring = assert_native_two_actor_authoring(
            document, expected_masks=expected_masks, variant=variant)
        export_document(document, resources)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(game, root / "screenshots", seconds=6,
                     scene_only=True, allow_static_scene=True,
                     native_two_actor_walk_probe=True)
        native_input = json.loads((root / "screenshots" /
            "r06-two-actor-walk-capture.json").read_text(encoding="utf-8"))
        report["variants"][variant] = {
            "native_link_and_launch_passed": True,
            "native_input_capture": native_input, "authoring": authoring}
        report_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                               encoding="utf-8")
    observed = track_native_actor_lanes(output / "transparent" / "screenshots")
    report["native_actor_tracks"] = observed
    report_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    report["motion_comparison"] = verify_two_actor_native_walks(observed)
    report["independent_actor_motion_verified"] = True
    report_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_two_actor_four_mask_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
