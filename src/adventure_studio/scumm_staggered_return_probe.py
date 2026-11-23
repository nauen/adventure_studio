"""R06 #280: native staggered Actor reversals proven from stock-ScummVM frames."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_return_walk_probe import (
    author_native_return_walk_project, assert_native_return_walk_authoring,
    verify_two_actor_native_return,
)
from .scumm_opposing_actor_probe import ACTOR_IDS
from .scumm_project import (
    DelayStep, WalkActorStep, WaitActorStep, canonical_json, parse_document,
    export_document,
)
from .scumm_two_actor_four_mask_probe import (
    track_native_actor_lanes, measure_two_actor_native_camera_trace,
    verify_two_actor_native_camera_roundtrip, measure_two_actor_native_mask_comparison,
)


def author_staggered_native_return(output: Path, *, variant: str = "masked") -> str:
    """Start A's native return first, then B's, retaining all original V6 assets."""
    document = parse_document(author_native_return_walk_project(output, variant=variant))
    costume = document.costumes[-1]
    name = "R06StaggeredReturn" + variant.replace("-", "").title() + "Costume"
    document = replace(
        document,
        costumes=(*document.costumes[:-1], replace(costume, name=name)),
        actors=tuple(replace(actor, costume=name) if actor.id in ACTOR_IDS else actor
                     for actor in document.actors),
    )
    sequences = []
    for sequence in document.interaction_sequences:
        if (sequence.room, sequence.hotspot_id, sequence.verb) == (
                "Harbor", "Key", "Close"):
            steps = sequence.steps
            # Native 2-second delay while Actor A has already been issued
            # walkActorTo(); Actor B's return only begins after the delay.
            sequences.append(replace(sequence, steps=(
                *steps[:11], DelayStep(2), *steps[11:],
            )))
        else:
            sequences.append(sequence)
    changed = replace(document, interaction_sequences=tuple(sequences))
    assert_staggered_native_return(changed, variant=variant)
    return canonical_json(changed)


def assert_staggered_native_return(document, *, variant: str = "masked") -> dict:
    """Reject a missing real delay or delayed Actor B command in productive Story."""
    sequences = [s for s in document.interaction_sequences if (
        s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")]
    if len(sequences) != 1:
        raise RuntimeError("R06 staggered return requires one native interaction")
    steps = sequences[0].steps
    if (len(steps) != 20 or steps[10:15] != (
            WalkActorStep(ACTOR_IDS[0], 260, 85), DelayStep(2),
            WalkActorStep(ACTOR_IDS[1], 545, 135),
            WaitActorStep(ACTOR_IDS[0]), WaitActorStep(ACTOR_IDS[1]))):
        raise RuntimeError("R06 staggered native Actor A return must precede B by two seconds")
    reconstructed = replace(document, interaction_sequences=tuple(
        replace(s, steps=(*s.steps[:11], *s.steps[12:])) if s is sequences[0] else s
        for s in document.interaction_sequences
    ))
    assert_native_return_walk_authoring(reconstructed, variant=variant)
    return {"staggered_native_return_authored": True,
            "staggered_native_return_pixels_verified": False}


def verify_staggered_native_return(traces: dict) -> dict:
    """Fail closed unless genuine pixel tracks show A returning before B."""
    baseline = verify_two_actor_native_return(traces)
    a = {row["frame"]: row for row in traces[ACTOR_IDS[0]]}
    b = {row["frame"]: row for row in traces[ACTOR_IDS[1]]}
    shared = sorted(set(a) & set(b), key=lambda frame: a[frame]["seconds"])
    stages = []
    for first, second in zip(shared, shared[1:]):
        left_a = a[first]["world_x"] - a[second]["world_x"]
        right_b = b[second]["world_x"] - b[first]["world_x"]
        duration = a[second]["seconds"] - a[first]["seconds"]
        if (0 < duration <= 1.5 and 15 <= left_a <= 55
                and abs(right_b) <= 8):
            stages.append({
                "frame": second, "seconds": a[second]["seconds"],
                "a_return_pixels": left_a, "b_stationary_pixels": abs(right_b),
            })
    if len(stages) < 2:
        raise RuntimeError("No native frames show Actor A returning while B remains stopped")
    if not all(stages[i]["seconds"] < stages[i + 1]["seconds"]
               for i in range(len(stages) - 1)):
        raise RuntimeError("Invalid chronological staggered native return frames")
    return {"staggered_native_return_verified": True,
            "a_before_b_frames": stages, "both_return": baseline}


def run_staggered_native_return(upstream: Path, output: Path) -> dict:
    """Demand independent stock ScummVM visual evidence in three control games."""
    from .scumm_launch import launch_smoke
    from .scumm_toolchain import compile_story_game
    output.mkdir(parents=True, exist_ok=True)
    report = {"variants": {}, "complete_r06_280_acceptance": False}
    evidence = output / "native-r06-staggered-return-report.json"

    def persist():
        evidence.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")

    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        authored = author_staggered_native_return(root, variant=variant)
        (build / "project.json").write_text(authored, encoding="utf-8")
        document = parse_document(authored)
        assert_staggered_native_return(document, variant=variant)
        export_document(document, resources)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(game, root / "screenshots", seconds=6,
                     scene_only=True, allow_static_scene=True,
                     native_two_actor_walk_probe=True)
        report["variants"][variant] = {"stock_scummvm_started": True}
        persist()

    transparent = output / "transparent" / "screenshots"
    traces = track_native_actor_lanes(transparent)
    report["staggered_motion"] = verify_staggered_native_return(traces)
    report["native_camera_roundtrips"] = {
        variant: verify_two_actor_native_camera_roundtrip(
            measure_two_actor_native_camera_trace(output / variant / "screenshots"),
            expected_start=400, prepan_direction="either")
        for variant in ("masked", "transparent", "wrong-box")
    }
    report["native_mask_controls"] = measure_two_actor_native_mask_comparison(output, traces)
    report["complete_r06_280_acceptance"] = True
    persist()
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_staggered_return_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_staggered_native_return(
        Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
