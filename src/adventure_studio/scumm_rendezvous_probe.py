"""R06 #282: native two-Actor rendezvous, wait and diverging return routes.

The authored SCUMM-v6 commands are not gameplay evidence. Acceptance requires
genuine screenshot-derived Actor tracks in unmodified stock ScummVM.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_staggered_return_probe import (
    author_staggered_native_return, assert_staggered_native_return,
)
from .scumm_opposing_actor_probe import ACTOR_IDS, STARTS
from .scumm_project import (
    DelayStep, PanCameraStep, WaitCameraStep, WalkActorStep, WaitActorStep,
    canonical_json, parse_document, export_document,
)
from .scumm_two_actor_four_mask_probe import (
    track_native_actor_lanes, measure_two_actor_native_camera_trace,
    verify_two_actor_native_camera_roundtrip,
    measure_two_actor_native_mask_comparison,
)


MEETING_X = 395


def author_two_actor_rendezvous_project(output: Path, *, variant: str = "masked") -> str:
    """Both native Actors meet at X=395 on separate Walkbox Y lanes, then depart."""
    original = parse_document(author_staggered_native_return(
        output, variant=variant))
    costume = original.costumes[-1]
    unique_name = "R06Rendezvous" + variant.replace("-", "").title() + "Costume"
    original = replace(
        original,
        costumes=(*original.costumes[:-1],
                  replace(costume, name=unique_name)),
        actors=tuple(replace(actor, costume=unique_name)
                     if actor.id in ACTOR_IDS else actor
                     for actor in original.actors),
    )
    sequences = []
    for sequence in original.interaction_sequences:
        if (sequence.room, sequence.hotspot_id, sequence.verb) != (
                "Harbor", "Key", "Close"):
            sequences.append(sequence)
            continue
        steps = sequence.steps
        # Keep the prior A→B→A native focus and independent outward walks.
        # A's native return starts first, B starts 2 seconds later; each
        # reaches the rendezvous before the second leg starts.
        meet = (
            WalkActorStep(ACTOR_IDS[0], MEETING_X, 85),
            DelayStep(2),
            WalkActorStep(ACTOR_IDS[1], MEETING_X, 135),
            WaitActorStep(ACTOR_IDS[0]),
            WaitActorStep(ACTOR_IDS[1]),
            DelayStep(2),
            # After the simultaneous X=395 meeting, frame both return
            # destinations: camera X=400 sees world X=240..560. Actual
            # stock-ScummVM frames at X=320 clipped B at world X>480
            # before three visible departure steps could be measured.
            PanCameraStep(400), WaitCameraStep(),
            WalkActorStep(ACTOR_IDS[0], *STARTS[ACTOR_IDS[0]]),
            WalkActorStep(ACTOR_IDS[1], *STARTS[ACTOR_IDS[1]]),
            WaitActorStep(ACTOR_IDS[0]),
            WaitActorStep(ACTOR_IDS[1]),
        )
        sequences.append(replace(sequence, steps=(
            *steps[:12], *meet, *steps[17:],
        )))
    document = replace(original, interaction_sequences=tuple(sequences))
    assert_two_actor_rendezvous(document, variant=variant)
    return canonical_json(document)


def assert_two_actor_rendezvous(document, *, variant: str = "masked") -> dict:
    """Require actual consecutive two-Actor approach, pause and depart opcodes."""
    target = [s for s in document.interaction_sequences
              if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")]
    if len(target) != 1:
        raise RuntimeError("R06 rendezvous requires one native Key interaction")
    steps = target[0].steps
    expected = (
        WalkActorStep(ACTOR_IDS[0], MEETING_X, 85),
        DelayStep(2),
        WalkActorStep(ACTOR_IDS[1], MEETING_X, 135),
        WaitActorStep(ACTOR_IDS[0]), WaitActorStep(ACTOR_IDS[1]),
        DelayStep(2),
        PanCameraStep(400), WaitCameraStep(),
        WalkActorStep(ACTOR_IDS[0], *STARTS[ACTOR_IDS[0]]),
        WalkActorStep(ACTOR_IDS[1], *STARTS[ACTOR_IDS[1]]),
        WaitActorStep(ACTOR_IDS[0]), WaitActorStep(ACTOR_IDS[1]),
    )
    if len(steps) != 29 or steps[12:24] != expected:
        raise RuntimeError("R06 native rendezvous meet, wait or depart commands missing")
    parent = replace(document, interaction_sequences=tuple(
        replace(s, steps=(
            *s.steps[:12],
            WalkActorStep(ACTOR_IDS[0], *STARTS[ACTOR_IDS[0]]),
            DelayStep(2),
            WalkActorStep(ACTOR_IDS[1], *STARTS[ACTOR_IDS[1]]),
            WaitActorStep(ACTOR_IDS[0]), WaitActorStep(ACTOR_IDS[1]),
            *s.steps[24:],
        )) if s is target[0] else s for s in document.interaction_sequences
    ))
    assert_staggered_native_return(parent, variant=variant)
    return {"two_actor_native_rendezvous_authored": True,
            "two_actor_native_rendezvous_pixels_verified": False}


def verify_native_rendezvous(traces: dict) -> dict:
    """Require distinct real Actor tracks approaching, meeting and separating."""
    if set(traces) != set(ACTOR_IDS):
        raise RuntimeError("R06 native rendezvous requires two independent Actor tracks")
    rows = {actor: {row["frame"]: row for row in traces[actor]}
            for actor in ACTOR_IDS}
    common = sorted(set(rows[ACTOR_IDS[0]]) & set(rows[ACTOR_IDS[1]]),
                    key=lambda frame: rows[ACTOR_IDS[0]][frame]["seconds"])
    if len(common) < 16:
        raise RuntimeError("Insufficient native rendezvous screenshot frames")
    meeting = [
        index for index, frame in enumerate(common)
        if all(abs(rows[actor][frame]["world_x"] - MEETING_X) <= 25
               for actor in ACTOR_IDS)
    ]
    if len(meeting) < 2:
        raise RuntimeError("Both Actors never met at native X=395 together")
    for index in meeting:
        frame = common[index]
        if index < 4 or index > len(common) - 5:
            continue
        # Both Actors must have walked toward X=395 from different sides,
        # and afterwards *both* must walk away from the meeting point.
        # Reject one-frame teleports and static Actor impostors by demanding
        # three separate sub-55px genuine native frame increments each way.
        segments = {}
        for actor, approach_sign, depart_sign in (
                (ACTOR_IDS[0], -1, -1),
                (ACTOR_IDS[1], 1, 1)):
            # The meeting must be simultaneously visible in both lanes.
            # Native camera scroll and occlusion can hide the OTHER actor
            # during a valid walking leg, so do not throw away real costume
            # frames that are unique to this actor's own timestamped track.
            meeting_time = rows[actor][frame]["seconds"]
            trace = sorted(traces[actor], key=lambda row: row["seconds"])
            before = [row for row in trace
                      if row["seconds"] <= meeting_time]
            after = [row for row in trace
                     if row["seconds"] >= meeting_time]
            def movements(part, sign):
                return [
                    (a, b) for a, b in zip(part, part[1:])
                    if 5 <= (b["world_x"] - a["world_x"]) * sign <= 55
                ]
            incoming = movements(before, approach_sign)
            outgoing = movements(after, depart_sign)
            if len(incoming) < 3 or len(outgoing) < 3:
                break
            if (abs(incoming[-1][1]["world_x"] -
                    incoming[0][0]["world_x"]) < 90
                    or abs(outgoing[-1][1]["world_x"] -
                           outgoing[0][0]["world_x"]) < 90):
                break
            segments[actor] = {
                "inbound_steps": len(incoming),
                "outbound_steps": len(outgoing),
            }
        if len(segments) == 2:
            return {"native_two_actor_rendezvous_verified": True,
                    "meeting_frame": frame,
                    "meeting_seconds": rows[ACTOR_IDS[0]][frame]["seconds"],
                    "actor_legs": segments}
    raise RuntimeError(
        "Native Actors did not visibly approach and depart X=395 in both lanes")


def run_native_rendezvous(upstream: Path, output: Path) -> dict:
    """Compile/play three genuine native games, persist fail-closed evidence."""
    from .scumm_launch import launch_smoke
    from .scumm_toolchain import compile_story_game

    output.mkdir(parents=True, exist_ok=True)
    report = {"variants": {}, "complete_r06_282_acceptance": False}
    evidence = output / "native-r06-rendezvous-report.json"

    def persist():
        evidence.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                            encoding="utf-8")

    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        authored = author_two_actor_rendezvous_project(root, variant=variant)
        (build / "project.json").write_text(authored, encoding="utf-8")
        document = parse_document(authored)
        assert_two_actor_rendezvous(document, variant=variant)
        export_document(document, resources)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(game, root / "screenshots", seconds=6,
                     scene_only=True, allow_static_scene=True,
                     native_two_actor_walk_probe=True,
                     native_two_actor_capture_frames=300)
        report["variants"][variant] = {"stock_scummvm_started": True}
        persist()

    transparent = output / "transparent" / "screenshots"
    traces = track_native_actor_lanes(transparent)
    report["native_rendezvous"] = verify_native_rendezvous(traces)
    report["native_camera_roundtrip"] = {
        variant: verify_two_actor_native_camera_roundtrip(
            measure_two_actor_native_camera_trace(output / variant / "screenshots"),
            expected_start=400, prepan_direction="either")
        for variant in ("masked", "transparent", "wrong-box")
    }
    report["native_zplane_controls"] = measure_two_actor_native_mask_comparison(
        output, traces)
    report["complete_r06_282_acceptance"] = True
    persist()
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: python -m adventure_studio.scumm_rendezvous_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_native_rendezvous(
        Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
