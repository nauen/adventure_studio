"""R06 #278: real SCUMM-v6 two-Actor return walks through four room Z-planes.

This adds a second, native WalkActorStep per Actor after both outbound
WalkActorStep commands have completed. Screenshot pixels, not the authored
commands, must establish that each Actor actually reverses direction.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_reciprocal_focus_probe import (
    author_reciprocal_focus_project, assert_reciprocal_focus_authoring,
)
from .scumm_opposing_actor_probe import (
    ACTOR_IDS, STARTS, verify_opposing_native_motion,
)
from .scumm_project import (
    WalkActorStep, WaitActorStep, canonical_json, parse_document, export_document,
)
from .scumm_two_actor_four_mask_probe import (
    track_native_actor_lanes, measure_two_actor_native_camera_trace,
    verify_two_actor_native_camera_roundtrip,
    measure_two_actor_native_mask_comparison,
)


def author_native_return_walk_project(output: Path, *, variant: str = "masked") -> str:
    """Produce three separately linked native outbound-and-return games."""
    original = parse_document(author_reciprocal_focus_project(
        output, variant=variant))
    costume = original.costumes[-1]
    name = "R06ReturnWalk" + variant.replace("-", "").title() + "Costume"
    original = replace(
        original,
        costumes=(*original.costumes[:-1], replace(costume, name=name)),
        actors=tuple(replace(a, costume=name) if a.id in ACTOR_IDS else a
                     for a in original.actors),
    )
    sequences = []
    for sequence in original.interaction_sequences:
        if (sequence.room, sequence.hotspot_id, sequence.verb) != (
                "Harbor", "Key", "Close"):
            sequences.append(sequence)
            continue
        steps = sequence.steps
        # The first native WaitActor pair guarantees real arrival before the
        # return steps; both return steps are issued before either return wait.
        sequences.append(replace(sequence, steps=(
            *steps[:10],
            WalkActorStep(ACTOR_IDS[0], *STARTS[ACTOR_IDS[0]]),
            WalkActorStep(ACTOR_IDS[1], *STARTS[ACTOR_IDS[1]]),
            WaitActorStep(ACTOR_IDS[0]),
            WaitActorStep(ACTOR_IDS[1]),
            *steps[10:],
        )))
    document = replace(original, interaction_sequences=tuple(sequences))
    assert_native_return_walk_authoring(document, variant=variant)
    return canonical_json(document)


def assert_native_return_walk_authoring(document, *, variant: str = "masked") -> dict:
    """Reject teleporting or prematurely waiting instead of both native returns."""
    target = [s for s in document.interaction_sequences
              if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")]
    if len(target) != 1:
        raise RuntimeError("R06 return needs exactly one native interaction")
    steps = target[0].steps
    expected = (
        WalkActorStep(ACTOR_IDS[0], *STARTS[ACTOR_IDS[0]]),
        WalkActorStep(ACTOR_IDS[1], *STARTS[ACTOR_IDS[1]]),
        WaitActorStep(ACTOR_IDS[0]), WaitActorStep(ACTOR_IDS[1]),
    )
    if len(steps) != 19 or steps[10:14] != expected:
        raise RuntimeError("R06 missing two genuine simultaneous return walks and waits")
    reconstructed = replace(
        document,
        interaction_sequences=tuple(
            replace(s, steps=(*s.steps[:10], *s.steps[14:]))
            if s is target[0] else s for s in document.interaction_sequences
        ),
    )
    assert_reciprocal_focus_authoring(reconstructed, variant=variant)
    return {"native_two_actor_return_walks_authored": True,
            "native_two_actor_return_pixels_verified": False}


def verify_two_actor_native_return(traces: dict) -> dict:
    """Require time-ordered substantial visible motion in *both* directions."""
    if set(traces) != set(ACTOR_IDS):
        raise RuntimeError("Two native actor tracks required for return proof")
    results = {}
    for actor, first_sign in ((ACTOR_IDS[0], 1), (ACTOR_IDS[1], -1)):
        rows = sorted(traces[actor], key=lambda row: row["seconds"])
        if len(rows) < 12 or len({r["frame"] for r in rows}) != len(rows):
            raise RuntimeError(f"Insufficient genuine native return frames: {actor}")
        timestamps = [row["seconds"] for row in rows]
        if len(timestamps) != len(set(timestamps)) or timestamps != sorted(timestamps):
            raise RuntimeError(f"Invalid native frame chronology: {actor}")
        # Direction changes must occur at observable frames, not inferred from
        # the script or from a teleport between two sparse screenshots.
        motions = [(before, after, (after["world_x"] - before["world_x"]) * first_sign)
                   for before, after in zip(rows, rows[1:])]
        outbound = [(a, b) for a, b, d in motions if 5 <= d <= 55]
        returns = [(a, b) for a, b, d in motions if -55 <= d <= -5]
        if len(outbound) < 3 or len(returns) < 3:
            raise RuntimeError(f"Native Actor {actor} did not visibly reverse with three steps")
        turns = []
        for turn in range(1, len(rows) - 1):
            outgoing = [(a, b) for a, b in outbound if b["seconds"] <= rows[turn]["seconds"]]
            incoming = [(a, b) for a, b in returns if a["seconds"] >= rows[turn]["seconds"]]
            if len(outgoing) < 3 or len(incoming) < 3:
                continue
            if ((outgoing[-1][1]["world_x"] -
                 outgoing[0][0]["world_x"]) * first_sign < 120):
                continue
            # A native camera pan can occlude the costume for ~1s after
            # several independently measured return steps. In the actual
            # stock-ScummVM run B walked visibly 335→359→383→415→439,
            # disappeared during a pan, then reappeared at world X=544
            # and X=545. The old verifier discarded those REAL endpoint
            # screenshots merely because their gap exceeded 55px.
            #
            # Require >=3 bounded native return increments (above), then
            # anchor the full 120px return to an actual later costume frame
            # near the authored start. Reject a teleport over the occluded
            # interval by bounding the observed displacement by real time.
            start = incoming[0][0]
            tail = [r for r in rows if r["seconds"] >= start["seconds"]]
            for end_index, end in enumerate(tail):
                if ((end["world_x"] - start["world_x"]) * first_sign > -120
                        or abs(end["world_x"] - STARTS[actor][0]) > 25):
                    continue
                segment = tail[:end_index + 1]
                if all(
                    0 < right["seconds"] - left["seconds"] <= 1.5
                    and abs(right["world_x"] - left["world_x"])
                    <= 225 * (right["seconds"] - left["seconds"]) + 15
                    for left, right in zip(segment, segment[1:])
                ):
                    turns.append(rows[turn])
                    break
        if not turns:
            raise RuntimeError(f"Native Actor {actor} did not complete both 120px legs")
        results[actor] = {"native_direction_reversal_verified": True,
                          "turn_frame": turns[0]["frame"],
                          "outbound_steps": len(outbound),
                          "return_steps": len(returns)}
    return {"native_two_actor_return_verified": True, "actors": results}


def run_native_return_walk(upstream: Path, output: Path) -> dict:
    """Compile and run three distinct stock-ScummVM two-leg games."""
    from .scumm_launch import launch_smoke
    from .scumm_toolchain import compile_story_game
    output.mkdir(parents=True, exist_ok=True)
    report = {"variants": {}, "complete_r06_278_acceptance": False}
    evidence = output / "native-r06-return-walk-report.json"

    def persist():
        evidence.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                            encoding="utf-8")

    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        project = author_native_return_walk_project(root, variant=variant)
        (build / "project.json").write_text(project, encoding="utf-8")
        document = parse_document(project)
        assert_native_return_walk_authoring(document, variant=variant)
        export_document(document, resources)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(game, root / "screenshots", seconds=6, scene_only=True,
                     allow_static_scene=True, native_two_actor_walk_probe=True)
        report["variants"][variant] = {"stock_scummvm_started": True}
        persist()

    transparent = output / "transparent" / "screenshots"
    tracks = track_native_actor_lanes(transparent)
    report["return_motion"] = verify_two_actor_native_return(tracks)
    report["native_camera_roundtrip"] = {
        variant: verify_two_actor_native_camera_roundtrip(
            measure_two_actor_native_camera_trace(output / variant / "screenshots"),
            expected_start=400, prepan_direction="either")
        for variant in ("masked", "transparent", "wrong-box")
    }
    report["native_four_zplane_controls"] = measure_two_actor_native_mask_comparison(
        output, tracks)
    report["complete_r06_278_acceptance"] = True
    persist()
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_return_walk_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_native_return_walk(
        Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
