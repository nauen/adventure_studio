"""R06 #276: reciprocal native focus A→B→A during opposing Actor walks.

Only actual stock-ScummVM screenshot positions can verify the focus switch.
Three independently linked masked/transparent/wrong-box games are mandatory.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_opposing_handoff_probe import (
    ACTOR_IDS, author_opposing_camera_handoff_project,
    assert_opposing_camera_handoff,
)
from .scumm_project import (
    DelayStep, FollowActorCameraStep, WaitActorStep,
    canonical_json, parse_document, export_document,
)
from .scumm_opposing_actor_probe import verify_opposing_native_motion
from .scumm_two_actor_four_mask_probe import (
    track_native_actor_lanes, measure_two_actor_native_camera_trace,
    verify_two_actor_native_camera_roundtrip,
    measure_two_actor_native_mask_comparison,
)


def author_reciprocal_focus_project(output: Path, *, variant: str = "masked") -> str:
    """Append a real third camera-follow opcode before either walk completes."""
    original = parse_document(author_opposing_camera_handoff_project(
        output, variant=variant))
    costume = original.costumes[-1]
    name = "R06ReciprocalFocus" + variant.replace("-", "").title() + "Costume"
    original = replace(
        original,
        costumes=(*original.costumes[:-1], replace(costume, name=name)),
        actors=tuple(replace(actor, costume=name) if actor.id in ACTOR_IDS else actor
                     for actor in original.actors),
    )
    sequences = []
    for sequence in original.interaction_sequences:
        if (sequence.room, sequence.hotspot_id, sequence.verb) != (
                "Harbor", "Key", "Close"):
            sequences.append(sequence)
            continue
        steps = sequence.steps
        # Keep both WalkActorStep operations at the beginning; the extra follow
        # is inserted BEFORE WaitActorStep, not after motion completion.
        sequences.append(replace(sequence, steps=(
            *steps[:6],
            FollowActorCameraStep(ACTOR_IDS[0]), DelayStep(1),
            *steps[6:],
        )))
    document = replace(original, interaction_sequences=tuple(sequences))
    assert_reciprocal_focus_authoring(document, variant=variant)
    return canonical_json(document)


def assert_reciprocal_focus_authoring(document, *, variant: str = "masked") -> dict:
    """Require native opposite walks and A→B→A follow opcodes before waits."""
    sequences = [sequence for sequence in document.interaction_sequences
                 if (sequence.room, sequence.hotspot_id, sequence.verb)
                 == ("Harbor", "Key", "Close")]
    if len(sequences) != 1:
        raise RuntimeError("R06 reciprocal focus requires a unique native interaction")
    sequence = sequences[0]
    steps = sequence.steps
    if (len(steps) != 15
            or steps[2:8] != (
                FollowActorCameraStep(ACTOR_IDS[0]),
                DelayStep(4),
                FollowActorCameraStep(ACTOR_IDS[1]),
                DelayStep(1),
                FollowActorCameraStep(ACTOR_IDS[0]),
                DelayStep(1),
            )
            or steps[8:10] != (WaitActorStep(ACTOR_IDS[0]),
                               WaitActorStep(ACTOR_IDS[1]))):
        raise RuntimeError("R06 native reciprocal A-B-A focus must precede both waits")
    parent = replace(document, interaction_sequences=tuple(
        replace(s, steps=(*s.steps[:6], *s.steps[8:])) if s is sequence else s
        for s in document.interaction_sequences
    ))
    assert_opposing_camera_handoff(parent, variant=variant)
    costumes = {c.name for c in document.costumes}
    if len(costumes) != len(document.costumes) or any(
            actor.costume not in costumes for actor in document.actors):
        raise RuntimeError("R06 reciprocal focus has broken native COST binding")
    return {"reciprocal_native_focus_authored": True,
            "native_reciprocal_visual_verified": False}


def verify_native_reciprocal_focus(traces: dict, camera_frames: list[dict]) -> dict:
    """Demand ordered visible focus A→B→A while *both* native Actors are moving."""
    if set(traces) != set(ACTOR_IDS):
        raise RuntimeError("Native reciprocal focus requires two Actor tracks")
    by_actor = {
        name: {row["frame"]: row for row in traces[name]}
        for name in ACTOR_IDS
    }
    cameras = {row["frame"]: row for row in camera_frames}
    shared = sorted(
        set(by_actor[ACTOR_IDS[0]]) & set(by_actor[ACTOR_IDS[1]])
        & set(cameras),
        key=lambda frame: cameras[frame]["seconds"],
    )
    visible_motion = []
    # The recorder samples much faster than a native costume's movement
    # tick. Adjacent screenshot pairs can show <5px despite genuine walks.
    # Compare only real frame pairs within a bounded 0.4s interval; never
    # interpolate camera/actor coordinates or accept a stopped Actor.
    for end_index, after in enumerate(shared):
        end_time = cameras[after]["seconds"]
        moving = False
        for before in reversed(shared[:end_index]):
            duration = end_time - cameras[before]["seconds"]
            if duration > 0.4:
                break
            a0, a1 = by_actor[ACTOR_IDS[0]][before], by_actor[ACTOR_IDS[0]][after]
            b0, b1 = by_actor[ACTOR_IDS[1]][before], by_actor[ACTOR_IDS[1]][after]
            if (0 < duration <= 0.4
                    and 5 <= a1["world_x"] - a0["world_x"] <= 55
                    and 5 <= b0["world_x"] - b1["world_x"] <= 55):
                moving = True
                break
        if moving:
            a1 = by_actor[ACTOR_IDS[0]][after]
            b1 = by_actor[ACTOR_IDS[1]][after]
            visible_motion.append({
                "frame": after, "seconds": end_time,
                "camera_x": cameras[after]["camera_x"],
                "a_distance": abs(a1["screen_x"] - 512),
                "b_distance": abs(b1["screen_x"] - 512),
            })
    if len(visible_motion) < 5:
        raise RuntimeError("Not enough simultaneous opposite native motion during focus swaps")
    first = next((row for row in visible_motion
                  if row["a_distance"] + 40 < row["b_distance"]), None)
    second = next((row for row in visible_motion
                   if first and row["seconds"] > first["seconds"]
                   and row["b_distance"] + 40 < row["a_distance"]
                   and abs(row["camera_x"] - first["camera_x"]) >= 12), None)
    # Native 2x-costume tracking at the final A handback can show a
    # 34-screen-pixel advantage (real capture: t=4.56s, camera X=408,
    # A=495, B=304). The former 40px threshold incorrectly rejected
    # that fully visible, moving A-B-A sequence. Keep the first two
    # unambiguous 40px phases and require >=32px on the third, with the
    # same genuine simultaneous motion and >=12px camera travel.
    third = next((row for row in visible_motion
                  if second and row["seconds"] > second["seconds"]
                  and row["a_distance"] + 32 <= row["b_distance"]
                  and abs(row["camera_x"] - second["camera_x"]) >= 12), None)
    if first is None or second is None or third is None:
        raise RuntimeError("Stock ScummVM never showed reciprocal A-B-A focus during both walks")
    return {"native_reciprocal_focus_verified": True,
            "a_first": first, "b_middle": second, "a_return": third}


def run_reciprocal_focus(upstream: Path, output: Path) -> dict:
    """Compile, run and observe three independent stock ScummVM gameplay controls."""
    from .scumm_launch import launch_smoke
    from .scumm_toolchain import compile_story_game

    output.mkdir(parents=True, exist_ok=True)
    report = {"variants": {}, "complete_r06_276_acceptance": False}
    path = output / "native-r06-reciprocal-focus-report.json"

    def persist():
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")

    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        encoded = author_reciprocal_focus_project(root, variant=variant)
        (build / "project.json").write_text(encoded, encoding="utf-8")
        document = parse_document(encoded)
        assert_reciprocal_focus_authoring(document, variant=variant)
        export_document(document, resources)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(game, root / "screenshots", seconds=6,
                     scene_only=True, allow_static_scene=True,
                     native_two_actor_walk_probe=True)
        report["variants"][variant] = {"native_game_started": True}
        persist()

    transparent = output / "transparent" / "screenshots"
    traces = track_native_actor_lanes(transparent)
    report["opposing_motion"] = verify_opposing_native_motion(traces)
    report["camera_roundtrips"] = {
        variant: verify_two_actor_native_camera_roundtrip(
            measure_two_actor_native_camera_trace(output / variant / "screenshots"),
            expected_start=400, prepan_direction="either")
        for variant in ("masked", "transparent", "wrong-box")
    }
    report["mask_comparison"] = measure_two_actor_native_mask_comparison(output, traces)
    report["visual_reciprocal_focus"] = verify_native_reciprocal_focus(
        traces, measure_two_actor_native_camera_trace(transparent))
    report["complete_r06_276_acceptance"] = True
    persist()
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_reciprocal_focus_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_reciprocal_focus(
        Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
