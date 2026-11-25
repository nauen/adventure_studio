"""R06 #274: native focus handoff while two Actors walk in opposite directions.

No scripted positions are used to pass visual acceptance: actor and camera
samples must come from screenshots of independently linked stock-ScummVM games.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_opposing_actor_probe import (
    ACTOR_IDS, author_opposing_native_actor_project,
    assert_opposing_native_actor_project, verify_opposing_native_motion,
)
from .scumm_project import (
    FollowActorCameraStep, DelayStep, WalkActorStep, WaitActorStep,
    PanCameraStep, WaitCameraStep, canonical_json, parse_document, export_document,
)
from .scumm_two_actor_four_mask_probe import (
    track_native_actor_lanes, measure_two_actor_native_camera_trace,
    verify_two_actor_native_camera_roundtrip, measure_two_actor_native_mask_comparison,
)


def author_opposing_camera_handoff_project(output: Path, *, variant: str = "masked") -> str:
    """Author genuine SCUMM-v6 follow-A / follow-B while both walk oppositely."""
    original = parse_document(author_opposing_native_actor_project(output, variant=variant))
    # Sharing the CI ScummC upstream directory requires a unique COST per game
    # even when the animation pixels intentionally match a previous probe.
    costume = original.costumes[-1]
    unique_costume = "R06OppositeFocus" + variant.replace("-", "").title() + "Costume"
    original = replace(
        original,
        costumes=(*original.costumes[:-1], replace(costume, name=unique_costume)),
        actors=tuple(replace(a, costume=unique_costume) if a.id in ACTOR_IDS else a
                     for a in original.actors),
    )
    sequences = []
    for sequence in original.interaction_sequences:
        if (sequence.room, sequence.hotspot_id, sequence.verb) != ("Harbor", "Key", "Close"):
            sequences.append(sequence)
            continue
        first, second, *_ = sequence.steps
        sequences.append(replace(sequence, steps=(
            first, second,
            FollowActorCameraStep(ACTOR_IDS[0]),
            DelayStep(4),
            FollowActorCameraStep(ACTOR_IDS[1]),
            DelayStep(1),
            WaitActorStep(ACTOR_IDS[0]),
            WaitActorStep(ACTOR_IDS[1]),
            PanCameraStep(480), WaitCameraStep(), DelayStep(2),
            PanCameraStep(160), WaitCameraStep(),
        )))
    document = replace(original, interaction_sequences=tuple(sequences))
    assert_opposing_camera_handoff(document, variant=variant)
    return canonical_json(document)


def assert_opposing_camera_handoff(document, *, variant: str = "masked") -> dict:
    """Fail if either opposite route, focus switch or native mask binding is lost."""
    # Strict parent verification of all native BOXD/Actor/camera fields applies
    # except the intentionally expanded interaction sequence.
    if variant not in ("masked", "transparent", "wrong-box"):
        raise ValueError("Unknown R06 opposite-camera control")
    sequences = [
        s for s in document.interaction_sequences
        if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")
    ]
    if len(sequences) != 1:
        raise RuntimeError("R06 opposite-focus requires a single native Key interaction")
    steps = sequences[0].steps
    expected = (
        WalkActorStep(ACTOR_IDS[0], 530, 85),
        WalkActorStep(ACTOR_IDS[1], 175, 135),
        FollowActorCameraStep(ACTOR_IDS[0]),
        DelayStep(4),
        FollowActorCameraStep(ACTOR_IDS[1]),
        DelayStep(1),
        WaitActorStep(ACTOR_IDS[0]),
        WaitActorStep(ACTOR_IDS[1]),
        PanCameraStep(480), WaitCameraStep(), DelayStep(2),
        PanCameraStep(160), WaitCameraStep(),
    )
    if steps != expected:
        raise RuntimeError("R06 simultaneous opposite walks or native focus switch missing")
    # The parent authoring guard needs the original unmodified sequence;
    # temporarily reconstruct only that for the native model checks.
    parent_steps = (
        steps[0], steps[1], steps[2], steps[6], steps[7],
        steps[8], steps[9], steps[10], steps[11], steps[12],
    )
    parent = replace(document, interaction_sequences=tuple(
        replace(s, steps=parent_steps) if s is sequences[0] else s
        for s in document.interaction_sequences
    ))
    assert_opposing_native_actor_project(parent, variant=variant)
    return {"opposing_native_walks_and_handoff_authored": True,
            "focus_handoff_visual_verified": False}


def verify_opposing_focus_switch(traces: dict, camera_frames: list[dict]) -> dict:
    """Detect A-to-B viewport focus from genuine simultaneous opposite movement."""
    if set(traces) != set(ACTOR_IDS):
        raise RuntimeError("Missing independent native Actor tracks for focus handoff")
    by_actor = {
        actor: {row["frame"]: row for row in traces[actor]} for actor in ACTOR_IDS
    }
    camera = {row["frame"]: row for row in camera_frames}
    shared = sorted(set(by_actor[ACTOR_IDS[0]]) & set(by_actor[ACTOR_IDS[1]])
                    & set(camera), key=lambda f: camera[f]["seconds"])
    phases = []
    for before, after in zip(shared, shared[1:]):
        a0, a1 = by_actor[ACTOR_IDS[0]][before], by_actor[ACTOR_IDS[0]][after]
        b0, b1 = by_actor[ACTOR_IDS[1]][before], by_actor[ACTOR_IDS[1]][after]
        if (a1["world_x"] - a0["world_x"] >= 5
                and b0["world_x"] - b1["world_x"] >= 5):
            phases.append({
                "frame": after, "seconds": camera[after]["seconds"],
                "camera_x": camera[after]["camera_x"],
                "a_distance": abs(a1["screen_x"] - 512),
                "b_distance": abs(b1["screen_x"] - 512),
            })
    if len(phases) < 3:
        raise RuntimeError("No simultaneous native opposite-direction walking at handoff")
    first = next((row for row in phases
                  if row["a_distance"] + 40 < row["b_distance"]), None)
    visible_b_focus = [
        row for row in phases
        if first and row["seconds"] > first["seconds"]
        and row["b_distance"] + 40 < row["a_distance"]
    ]
    if first is None or not visible_b_focus:
        raise RuntimeError("Native camera did not visibly switch focus A to B")
    # The first B-centered frame may still share A's old camera X: native
    # scrolling has inertia. Require a *later genuine B-centered frame* with
    # measured camera displacement rather than failing on that first sample.
    second = next((row for row in visible_b_focus
                   if abs(row["camera_x"] - first["camera_x"]) >= 12), None)
    if second is None:
        raise RuntimeError("Camera did not actually move during opposite Actor handoff")
    return {"opposing_native_focus_handoff_verified": True,
            "focus_before": first, "focus_after": second}


def run_opposing_camera_handoff(upstream: Path, output: Path) -> dict:
    """Compile three distinct stock-v6 games and demand screenshot-based proof."""
    from .scumm_launch import launch_smoke
    from .scumm_toolchain import compile_story_game
    output.mkdir(parents=True, exist_ok=True)
    report = {"variants": {}, "complete_r06_274_acceptance": False}
    report_file = output / "native-r06-opposing-handoff-report.json"
    def persist():
        report_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        project = author_opposing_camera_handoff_project(root, variant=variant)
        (build / "project.json").write_text(project, encoding="utf-8")
        document = parse_document(project)
        assert_opposing_camera_handoff(document, variant=variant)
        export_document(document, resources)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(game, root / "screenshots", seconds=6, scene_only=True,
                     allow_static_scene=True, native_two_actor_walk_probe=True,
                     native_two_actor_capture_frames=480,
                     native_two_actor_capture_interval=0.02)
        report["variants"][variant] = {"native_game_started": True}
        persist()
    transparent = output / "transparent" / "screenshots"
    tracks = track_native_actor_lanes(transparent)
    report["opposing_motion"] = verify_opposing_native_motion(tracks)
    report["camera_roundtrip"] = {
        variant: verify_two_actor_native_camera_roundtrip(
            measure_two_actor_native_camera_trace(output / variant / "screenshots"),
            expected_start=400, prepan_direction="either")
        for variant in ("masked", "transparent", "wrong-box")
    }
    report["native_masks"] = measure_two_actor_native_mask_comparison(output, tracks)
    report["visual_focus_handoff"] = verify_opposing_focus_switch(
        tracks, measure_two_actor_native_camera_trace(transparent))
    report["complete_r06_274_acceptance"] = True
    persist()
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_opposing_handoff_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_opposing_camera_handoff(
        Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
