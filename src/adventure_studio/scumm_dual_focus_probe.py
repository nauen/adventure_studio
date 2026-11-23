"""R06 #294: native camera focus transfers from A to B during both retargets.

Author two independent interrupted native WalkActorStep routes and a real
FollowActorCameraStep(A)→FollowActorCameraStep(B) transition. Visual evidence
is always measured from stock-ScummVM screenshot tracks, never scripted Xs.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_dual_retarget_probe import (
    author_native_dual_retarget, assert_native_dual_retarget,
    verify_native_dual_retarget,
)
from .scumm_camera_resume_probe import verify_native_camera_follow_resume
from .scumm_meeting_camera_probe import verify_native_meeting_camera_tour
from .scumm_meeting_release_probe import verify_native_rendezvous_release
from .scumm_opposing_actor_probe import ACTOR_IDS
from .scumm_project import (
    FollowActorCameraStep, WalkActorStep, canonical_json, parse_document, export_document,
)
from .scumm_two_actor_four_mask_probe import (
    track_native_actor_lanes, measure_two_actor_native_camera_trace,
    verify_two_actor_native_camera_roundtrip, measure_two_actor_native_mask_comparison,
)


def author_native_dual_retarget_focus(output: Path, *, variant: str = "masked") -> str:
    """Follow Actor A while it reverses; hand camera to B when B reverses."""
    document = parse_document(author_native_dual_retarget(output, variant=variant))
    costume = document.costumes[-1]
    costume_name = "R06DualFocusSwitch" + variant.replace("-", "").title() + "Costume"
    document = replace(
        document,
        costumes=(*document.costumes[:-1], replace(costume, name=costume_name)),
        actors=tuple(replace(a, costume=costume_name)
                     if a.id in ACTOR_IDS else a for a in document.actors),
    )
    sequences = []
    for s in document.interaction_sequences:
        if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close"):
            # Dual-retarget parent: A's second WalkActorStep at index 27;
            # B's second WalkActorStep at 31 and follow-B already at 32.
            # Insert follow-A only after the actual A reversal command.
            sequences.append(replace(s, steps=(
                *s.steps[:29], FollowActorCameraStep(ACTOR_IDS[0]), *s.steps[29:],
            )))
        else:
            sequences.append(s)
    changed = replace(document, interaction_sequences=tuple(sequences))
    assert_native_dual_retarget_focus(changed, variant=variant)
    return canonical_json(changed)


def assert_native_dual_retarget_focus(document, *, variant: str = "masked") -> dict:
    """Reject wrong-order, missing or premature native camera-follow commands."""
    matches = [s for s in document.interaction_sequences
               if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")]
    if len(matches) != 1:
        raise RuntimeError("R06 dual retarget focus requires one native Key interaction")
    steps = matches[0].steps
    if (len(steps) != 42
            or steps[28] != WalkActorStep(ACTOR_IDS[0], 260, 85)
            or steps[29] != FollowActorCameraStep(ACTOR_IDS[0])
            or steps[33] != WalkActorStep(ACTOR_IDS[1], 545, 135)
            or steps[34] != FollowActorCameraStep(ACTOR_IDS[1])):
        raise RuntimeError("Both native focus commands must follow each Actor's retarget")
    parent = replace(document, interaction_sequences=tuple(
        replace(s, steps=(*s.steps[:29], *s.steps[30:]))
        if s is matches[0] else s for s in document.interaction_sequences
    ))
    assert_native_dual_retarget(parent, variant=variant)
    return {"native_dual_retarget_camera_handoff_authored": True,
            "native_dual_retarget_camera_handoff_pixels_verified": False}


def verify_native_dual_retarget_focus(traces: dict, camera_frames: list[dict]) -> dict:
    """Prove distinct A-turn and B-turn camera-focused motion from actual pixels."""
    dual = verify_native_dual_retarget(traces, camera_frames)
    if set(traces) != set(ACTOR_IDS):
        raise RuntimeError("Native focus transfer requires two Actor screenshot tracks")
    actors = {actor: {row["frame"]: row for row in traces[actor]}
              for actor in ACTOR_IDS}
    cameras = {row["frame"]: row for row in camera_frames}
    shared = sorted(set(actors[ACTOR_IDS[0]]) & set(actors[ACTOR_IDS[1]])
                    & set(cameras), key=lambda f: cameras[f]["seconds"])
    frames = []
    for start, end in zip(shared, shared[1:]):
        a0, a1 = actors[ACTOR_IDS[0]][start], actors[ACTOR_IDS[0]][end]
        b0, b1 = actors[ACTOR_IDS[1]][start], actors[ACTOR_IDS[1]][end]
        if not 0 < cameras[end]["seconds"] - cameras[start]["seconds"] <= 1.5:
            continue
        frames.append({
            "frame": end, "seconds": cameras[end]["seconds"],
            "camera_x": cameras[end]["camera_x"],
            "a_dx": a1["world_x"] - a0["world_x"],
            "b_dx": b1["world_x"] - b0["world_x"],
            "a_center_distance": abs(a1["screen_x"] - 512),
            "b_center_distance": abs(b1["screen_x"] - 512),
        })
    focused_a = [r for r in frames
                 if -55 <= r["a_dx"] <= -5
                 and r["a_center_distance"] + 30 < r["b_center_distance"]]
    if len(focused_a) < 2:
        raise RuntimeError("Native camera never focused Actor A during its real reversal")
    focused_b = [r for r in frames
                 if r["seconds"] > focused_a[1]["seconds"]
                 and 5 <= r["b_dx"] <= 55
                 and r["b_center_distance"] + 30 < r["a_center_distance"]]
    if len(focused_b) < 2:
        raise RuntimeError("Native camera never switched focus to reversing Actor B")
    a_first = focused_a[0]
    b_after = next((r for r in focused_b
                    if abs(r["camera_x"] - a_first["camera_x"]) >= 24), None)
    if b_after is None:
        raise RuntimeError("No measured native camera displacement across retarget focus handoff")
    return {
        "native_dual_retarget_camera_handoff_verified": True,
        "actor_a_focused_frames": focused_a,
        "actor_b_focused_frames": focused_b,
        "camera_x_shift": abs(b_after["camera_x"] - a_first["camera_x"]),
        "dual_native_retarget": dual,
    }


def run_native_dual_retarget_focus(upstream: Path, output: Path) -> dict:
    """Build all native control variants and refuse scripted-only acceptance."""
    from .scumm_launch import launch_smoke
    from .scumm_toolchain import compile_story_game

    output.mkdir(parents=True, exist_ok=True)
    report = {"variants": {}, "complete_r06_294_acceptance": False}
    evidence = output / "native-r06-dual-focus-report.json"

    def persist():
        evidence.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                            encoding="utf-8")

    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        authored = author_native_dual_retarget_focus(root, variant=variant)
        (build / "project.json").write_text(authored, encoding="utf-8")
        doc = parse_document(authored)
        assert_native_dual_retarget_focus(doc, variant=variant)
        export_document(doc, resources)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(game, root / "screenshots", seconds=6,
                     scene_only=True, allow_static_scene=True,
                     native_two_actor_walk_probe=True,
                     native_two_actor_capture_frames=300)
        report["variants"][variant] = {"stock_scummvm_started": True}
        persist()

    transparent = output / "transparent" / "screenshots"
    tracks = track_native_actor_lanes(transparent)
    camera = measure_two_actor_native_camera_trace(transparent)
    report["dual_retarget_focus"] = verify_native_dual_retarget_focus(tracks, camera)
    report["native_resume"] = verify_native_camera_follow_resume(tracks, camera)
    report["native_meeting_tour"] = verify_native_meeting_camera_tour(tracks, camera)
    report["native_release"] = verify_native_rendezvous_release(tracks)
    report["native_camera_roundtrip"] = {
        variant: verify_two_actor_native_camera_roundtrip(
            measure_two_actor_native_camera_trace(output / variant / "screenshots"),
            expected_start=400, prepan_direction="either")
        for variant in ("masked", "transparent", "wrong-box")
    }
    report["native_four_mask_controls"] = measure_two_actor_native_mask_comparison(
        output, tracks)
    report["complete_r06_294_acceptance"] = True
    persist()
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_dual_focus_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_native_dual_retarget_focus(
        Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
