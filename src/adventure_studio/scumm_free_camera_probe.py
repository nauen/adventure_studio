"""R06 #300: native camera exits actor follow and returns to composed stage X395.

A genuine stock-ScummVM four-focus trace must precede the free-camera
roundtrip. Pure authoring assertions never claim pixel acceptance.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_four_focus_probe import (
    author_native_four_focus, assert_native_four_focus, verify_native_four_focus,
)
from .scumm_opposing_actor_probe import ACTOR_IDS
from .scumm_rendezvous_probe import MEETING_X
from .scumm_project import (
    DelayStep, PanCameraStep, WaitCameraStep,
    canonical_json, parse_document, export_document,
)
from .scumm_two_actor_four_mask_probe import (
    track_native_actor_lanes, measure_two_actor_native_camera_trace,
    verify_two_actor_native_camera_roundtrip, measure_two_actor_native_mask_comparison,
)

RETURN_TO_STAGE = (DelayStep(2), PanCameraStep(MEETING_X),
                   WaitCameraStep(), DelayStep(1))


def author_native_camera_release(output: Path, *, variant: str = "masked") -> str:
    """Release A/B actor follow, pan to a fixed director-chosen room position."""
    document = parse_document(author_native_four_focus(output, variant=variant))
    old = document.costumes[-1]
    name = "R06FreeCamera" + variant.replace("-", "").title() + "Costume"
    document = replace(
        document,
        costumes=(*document.costumes[:-1], replace(old, name=name)),
        actors=tuple(replace(actor, costume=name) if actor.id in ACTOR_IDS
                     else actor for actor in document.actors),
    )
    sequences = tuple(
        replace(s, steps=(*s.steps[:41], *RETURN_TO_STAGE, *s.steps[41:]))
        if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")
        else s for s in document.interaction_sequences
    )
    result = replace(document, interaction_sequences=sequences)
    assert_native_camera_release(result, variant=variant)
    return canonical_json(result)


def assert_native_camera_release(document, *, variant: str = "masked") -> dict:
    """Require the fixed pan after all four native actor-camera follows."""
    matches = [s for s in document.interaction_sequences
               if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")]
    if len(matches) != 1:
        raise RuntimeError("R06 free camera requires exactly one Key interaction")
    steps = matches[0].steps
    if (len(steps) != 52 or steps[41:45] != RETURN_TO_STAGE):
        raise RuntimeError("Free native camera must pan after fourth Actor focus")
    parent = replace(document, interaction_sequences=tuple(
        replace(s, steps=(*s.steps[:41], *s.steps[45:]))
        if s is matches[0] else s for s in document.interaction_sequences
    ))
    assert_native_four_focus(parent, variant=variant)
    return {"native_follow_release_authored": True,
            "native_follow_release_pixels_verified": False}


def verify_native_camera_release(traces: dict, camera_frames: list[dict]) -> dict:
    """Prove real fourth-B-follow, then distinct centered X395 native frames."""
    prior = verify_native_four_focus(traces, camera_frames)
    last_b = prior["final_b_focus_frames"][-1]
    if set(traces) != set(ACTOR_IDS):
        raise RuntimeError("Both native Actors required for cinematic camera release")
    cameras = {r["frame"]: r for r in camera_frames}
    a = {r["frame"]: r for r in traces[ACTOR_IDS[0]]}
    b = {r["frame"]: r for r in traces[ACTOR_IDS[1]]}
    frames = sorted(
        ({"frame": frame, "seconds": cameras[frame]["seconds"],
          "camera_x": cameras[frame]["camera_x"],
          "a_world_x": a[frame]["world_x"], "b_world_x": b[frame]["world_x"]}
         for frame in set(cameras) & set(a) & set(b)
         if cameras[frame]["seconds"] > last_b["seconds"]),
        key=lambda row: row["seconds"],
    )
    staged = [row for row in frames
              if abs(row["camera_x"] - MEETING_X) <= 5
              and abs(row["camera_x"] - last_b["camera_x"]) >= 48]
    if len(staged) < 2 or staged[-1]["seconds"] <= staged[0]["seconds"]:
        raise RuntimeError("Native follow camera never returned to free stage X395")
    return {"native_follow_camera_released": True,
            "previous_four_focus": prior,
            "free_stage_frames": staged,
            "camera_shift": abs(staged[-1]["camera_x"] - last_b["camera_x"])}


def run_native_camera_release(upstream: Path, output: Path) -> dict:
    """Compile three genuine games and gate release on pixel-measured evidence."""
    from .scumm_launch import launch_smoke
    from .scumm_toolchain import compile_story_game

    output.mkdir(parents=True, exist_ok=True)
    report = {"variants": {}, "complete_r06_300_acceptance": False}
    report_path = output / "native-r06-free-camera-report.json"

    def persist():
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        project = author_native_camera_release(root, variant=variant)
        (build / "project.json").write_text(project, encoding="utf-8")
        document = parse_document(project)
        assert_native_camera_release(document, variant=variant)
        export_document(document, resources)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(game, root / "screenshots", seconds=6,
                     scene_only=True, allow_static_scene=True,
                     native_two_actor_walk_probe=True,
                     native_two_actor_capture_frames=450)
        report["variants"][variant] = {"stock_scummvm_started": True}
        persist()

    transparent = output / "transparent" / "screenshots"
    traces = track_native_actor_lanes(transparent)
    cameras = measure_two_actor_native_camera_trace(transparent)
    report["free_stage_camera"] = verify_native_camera_release(traces, cameras)
    report["native_camera_roundtrip"] = {
        variant: verify_two_actor_native_camera_roundtrip(
            measure_two_actor_native_camera_trace(
                output / variant / "screenshots"),
            expected_start=400, prepan_direction="either")
        for variant in ("masked", "transparent", "wrong-box")
    }
    report["native_four_mask_controls"] = measure_two_actor_native_mask_comparison(
        output, traces)
    report["complete_r06_300_acceptance"] = True
    persist()
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: python -m adventure_studio.scumm_free_camera_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_native_camera_release(
        Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
