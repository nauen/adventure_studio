"""R06 #298: four real native A->B->A->B camera focus phases.

The fourth handoff runs in stock ScummVM, never in a synthetic game.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_dual_focus_return_probe import (
    author_native_dual_focus_return, assert_native_dual_focus_return,
    verify_native_dual_focus_return,
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

FINAL_FOCUS_B = (DelayStep(2), FollowActorCameraStep(ACTOR_IDS[1]), WaitCameraStep())


def author_native_four_focus(output: Path, *, variant: str = "masked") -> str:
    """Issue a fourth native FollowActor command after completing return-to-A."""
    document = parse_document(author_native_dual_focus_return(
        output, variant=variant))
    costume = document.costumes[-1]
    name = "R06FourFocus" + variant.replace("-", "").title() + "Costume"
    document = replace(
        document,
        costumes=(*document.costumes[:-1], replace(costume, name=name)),
        actors=tuple(replace(a, costume=name) if a.id in ACTOR_IDS else a
                     for a in document.actors),
    )
    sequences = tuple(
        replace(s, steps=(*s.steps[:38], *FINAL_FOCUS_B, *s.steps[38:]))
        if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")
        else s for s in document.interaction_sequences
    )
    result = replace(document, interaction_sequences=sequences)
    assert_native_four_focus(result, variant=variant)
    return canonical_json(result)


def assert_native_four_focus(document, *, variant: str = "masked") -> dict:
    """Require ordered B follow after an actual native A reacquisition."""
    matches = [s for s in document.interaction_sequences
               if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")]
    if len(matches) != 1:
        raise RuntimeError("Native fourth-focus requires one Key interaction")
    steps = matches[0].steps
    if (len(steps) != 48
            or steps[35:38] != (
                DelayStep(3), FollowActorCameraStep(ACTOR_IDS[0]), WaitCameraStep())
            or steps[38:41] != FINAL_FOCUS_B):
        raise RuntimeError("Fourth native B focus must follow the A reacquisition")
    parent = replace(document, interaction_sequences=tuple(
        replace(s, steps=(*s.steps[:38], *s.steps[41:]))
        if s is matches[0] else s for s in document.interaction_sequences
    ))
    assert_native_dual_focus_return(parent, variant=variant)
    return {"native_four_focus_authored": True,
            "native_four_focus_pixels_verified": False}


def verify_native_four_focus(traces: dict, cameras: list[dict]) -> dict:
    """Prove A/B/A/B time order and final camera motion from native screenshots."""
    prior = verify_native_dual_focus_return(traces, cameras)
    last_a = prior["observed_return_a_frames"][-1]
    cam = {r["frame"]: r for r in cameras}
    b = {r["frame"]: r for r in traces[ACTOR_IDS[1]]}
    after = sorted(
        ({"frame": frame, "seconds": cam[frame]["seconds"],
          "camera_x": cam[frame]["camera_x"],
          "actor_b_screen_x": row["screen_x"]}
         for frame, row in b.items()
         if frame in cam and cam[frame]["seconds"] > last_a["seconds"]),
        key=lambda row: row["seconds"],
    )
    focus_b_again = [r for r in after
                     if abs(r["actor_b_screen_x"] - 512) <= 80
                     and abs(r["camera_x"] - last_a["camera_x"]) >= 48]
    if len(focus_b_again) < 2:
        raise RuntimeError("Native camera never returned to Actor B after A")
    if focus_b_again[-1]["seconds"] <= last_a["seconds"]:
        raise RuntimeError("Fourth native camera phase is not time ordered")
    return {"native_a_b_a_b_focus_verified": True,
            "prior_a_b_a_evidence": prior,
            "final_b_focus_frames": focus_b_again,
            "camera_shift_from_a": abs(
                focus_b_again[-1]["camera_x"] - last_a["camera_x"])}


def run_native_four_focus(upstream: Path, output: Path) -> dict:
    """Compile all three native control games and inspect their real frames."""
    from .scumm_launch import launch_smoke
    from .scumm_toolchain import compile_story_game

    output.mkdir(parents=True, exist_ok=True)
    report = {"variants": {}, "complete_r06_298_acceptance": False}
    report_path = output / "native-r06-four-focus-report.json"

    def persist():
        report_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                               encoding="utf-8")

    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        authored = author_native_four_focus(root, variant=variant)
        (build / "project.json").write_text(authored, encoding="utf-8")
        document = parse_document(authored)
        assert_native_four_focus(document, variant=variant)
        export_document(document, resources)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(game, root / "screenshots", seconds=6,
                     scene_only=True, allow_static_scene=True,
                     native_two_actor_walk_probe=True,
                     native_two_actor_capture_frames=420)
        report["variants"][variant] = {"stock_scummvm_started": True}
        persist()

    transparent = output / "transparent" / "screenshots"
    traces = track_native_actor_lanes(transparent)
    cameras = measure_two_actor_native_camera_trace(transparent)
    report["native_four_focus"] = verify_native_four_focus(traces, cameras)
    report["native_camera_roundtrip"] = {
        variant: verify_two_actor_native_camera_roundtrip(
            measure_two_actor_native_camera_trace(output / variant / "screenshots"),
            expected_start=400, prepan_direction="either")
        for variant in ("masked", "transparent", "wrong-box")
    }
    report["native_four_mask_controls"] = measure_two_actor_native_mask_comparison(
        output, traces)
    report["complete_r06_298_acceptance"] = True
    persist()
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_four_focus_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_native_four_focus(
        Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
