"""R06 #296: native A->B->A camera reacquisition after dual Actor retargeting.

Acceptance requires timestamped pixels from three independently linked stock
ScummVM games. Scripted focus cues alone never count as visual verification.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_dual_focus_probe import (
    author_native_dual_retarget_focus, assert_native_dual_retarget_focus,
    verify_native_dual_retarget_focus,
)
from .scumm_opposing_actor_probe import ACTOR_IDS
from .scumm_project import (
    DelayStep, FollowActorCameraStep, WaitCameraStep,
    canonical_json, parse_document, export_document,
)
from .scumm_two_actor_four_mask_probe import (
    track_native_actor_lanes, measure_two_actor_native_camera_trace,
    verify_two_actor_native_camera_roundtrip, measure_two_actor_native_mask_comparison,
)


RETURN_TO_A = (DelayStep(3), FollowActorCameraStep(ACTOR_IDS[0]), WaitCameraStep())


def author_native_dual_focus_return(output: Path, *, variant: str = "masked") -> str:
    """After B has moved with camera follow, reacquire A in the native engine."""
    document = parse_document(author_native_dual_retarget_focus(
        output, variant=variant))
    costume = document.costumes[-1]
    unique = "R06DualFocusReturn" + variant.replace("-", "").title() + "Costume"
    document = replace(
        document,
        costumes=(*document.costumes[:-1], replace(costume, name=unique)),
        actors=tuple(replace(a, costume=unique) if a.id in ACTOR_IDS else a
                     for a in document.actors),
    )
    sequences = tuple(
        replace(s, steps=(*s.steps[:35], *RETURN_TO_A, *s.steps[35:]))
        if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")
        else s for s in document.interaction_sequences
    )
    result = replace(document, interaction_sequences=sequences)
    assert_native_dual_focus_return(result, variant=variant)
    return canonical_json(result)


def assert_native_dual_focus_return(document, *, variant: str = "masked") -> dict:
    """Require the third camera focus after B's real return-walk follow command."""
    matches = [s for s in document.interaction_sequences
               if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")]
    if len(matches) != 1:
        raise RuntimeError("Native triple-focus requires one Key interaction")
    steps = matches[0].steps
    if (len(steps) != 45 or steps[35:38] != RETURN_TO_A
            or steps[34] != FollowActorCameraStep(ACTOR_IDS[1])):
        raise RuntimeError("Native camera must follow B before returning to A")
    parent = replace(document, interaction_sequences=tuple(
        replace(s, steps=(*s.steps[:35], *s.steps[38:]))
        if s is matches[0] else s for s in document.interaction_sequences
    ))
    assert_native_dual_retarget_focus(parent, variant=variant)
    return {"native_triple_focus_authored": True,
            "native_triple_focus_pixels_verified": False}


def verify_native_dual_focus_return(traces: dict, camera_frames: list[dict]) -> dict:
    """Require observed A->B motion focus and a subsequent B->A camera transition."""
    result = verify_native_dual_retarget_focus(traces, camera_frames)
    a = {r["frame"]: r for r in traces[ACTOR_IDS[0]]}
    camera = {r["frame"]: r for r in camera_frames}
    b_phase = result["actor_b_focused_frames"]
    if len(b_phase) < 2:
        raise RuntimeError("Native B focus phase is missing")
    last_b = b_phase[-1]
    after = sorted(
        ({"frame": f, "seconds": camera[f]["seconds"],
          "camera_x": camera[f]["camera_x"],
          "actor_a_screen_x": row["screen_x"]}
         for f, row in a.items()
         if f in camera and camera[f]["seconds"] > last_b["seconds"]),
        key=lambda r: r["seconds"],
    )
    focused_a_again = [
        row for row in after
        if abs(row["actor_a_screen_x"] - 512) <= 80
        and abs(row["camera_x"] - last_b["camera_x"]) >= 48
    ]
    if len(focused_a_again) < 2:
        raise RuntimeError("Native camera did not reacquire Actor A after following B")
    if focused_a_again[-1]["seconds"] <= last_b["seconds"]:
        raise RuntimeError("Native A-B-A camera phases not in order")
    return {"native_a_b_a_focus_verified": True,
            "prior_a_b_handoff": result,
            "observed_return_a_frames": focused_a_again,
            "camera_shift_from_b": abs(
                focused_a_again[-1]["camera_x"] - last_b["camera_x"])}


def run_native_dual_focus_return(upstream: Path, output: Path) -> dict:
    """Compile three complete games, record real native frames, reject missing evidence."""
    from .scumm_launch import launch_smoke
    from .scumm_toolchain import compile_story_game

    output.mkdir(parents=True, exist_ok=True)
    report = {"variants": {}, "complete_r06_296_acceptance": False}
    report_path = output / "native-r06-triple-focus-report.json"

    def persist() -> None:
        report_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                               encoding="utf-8")

    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        project = author_native_dual_focus_return(root, variant=variant)
        (build / "project.json").write_text(project, encoding="utf-8")
        document = parse_document(project)
        assert_native_dual_focus_return(document, variant=variant)
        export_document(document, resources)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(
            game, root / "screenshots", seconds=6,
            scene_only=True, allow_static_scene=True,
            native_two_actor_walk_probe=True,
            native_two_actor_capture_frames=360,
        )
        report["variants"][variant] = {"stock_scummvm_started": True}
        persist()

    transparent = output / "transparent" / "screenshots"
    tracks = track_native_actor_lanes(transparent)
    cameras = measure_two_actor_native_camera_trace(transparent)
    report["native_a_b_a_camera_focus"] = verify_native_dual_focus_return(
        tracks, cameras)
    report["native_camera_roundtrip"] = {
        variant: verify_two_actor_native_camera_roundtrip(
            measure_two_actor_native_camera_trace(
                output / variant / "screenshots"),
            expected_start=400, prepan_direction="either")
        for variant in ("masked", "transparent", "wrong-box")
    }
    report["native_four_mask_controls"] = measure_two_actor_native_mask_comparison(
        output, tracks)
    report["complete_r06_296_acceptance"] = True
    persist()
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: python -m adventure_studio.scumm_dual_focus_return_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_native_dual_focus_return(
        Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
