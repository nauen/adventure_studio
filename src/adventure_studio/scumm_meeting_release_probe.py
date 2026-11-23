"""R06 #284: native dwell at rendezvous and staggered Actor release.

All temporal claims require time-stamped pixel tracks from stock ScummVM;
authoring alone never passes the native proof.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_rendezvous_probe import (
    author_two_actor_rendezvous_project, assert_two_actor_rendezvous,
    verify_native_rendezvous, MEETING_X,
)
from .scumm_opposing_actor_probe import ACTOR_IDS
from .scumm_project import (
    DelayStep, WalkActorStep, canonical_json, parse_document, export_document,
)
from .scumm_two_actor_four_mask_probe import (
    track_native_actor_lanes, measure_two_actor_native_camera_trace,
    verify_two_actor_native_camera_roundtrip, measure_two_actor_native_mask_comparison,
)


def author_native_staggered_departure(output: Path, *, variant: str = "masked") -> str:
    """At X=395 both Actors dwell, then A departs two seconds before B."""
    original = parse_document(author_two_actor_rendezvous_project(output, variant=variant))
    costume = original.costumes[-1]
    name = "R06MeetingRelease" + variant.replace("-", "").title() + "Costume"
    original = replace(
        original,
        costumes=(*original.costumes[:-1], replace(costume, name=name)),
        actors=tuple(replace(a, costume=name) if a.id in ACTOR_IDS else a
                     for a in original.actors),
    )
    sequences = []
    for s in original.interaction_sequences:
        if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close"):
            sequences.append(replace(s, steps=(
                *s.steps[:19], DelayStep(2), *s.steps[19:],
            )))
        else:
            sequences.append(s)
    changed = replace(original, interaction_sequences=tuple(sequences))
    assert_native_staggered_departure(changed, variant=variant)
    return canonical_json(changed)


def assert_native_staggered_departure(document, *, variant: str = "masked") -> dict:
    """Ensure the second native return starts only after a genuine delay."""
    matches = [s for s in document.interaction_sequences
               if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")]
    if len(matches) != 1:
        raise RuntimeError("R06 staggered release needs one native interaction")
    steps = matches[0].steps
    if len(steps) != 28 or steps[17:21] != (
            DelayStep(2),
            WalkActorStep(ACTOR_IDS[0], 260, 85),
            DelayStep(2),
            WalkActorStep(ACTOR_IDS[1], 545, 135)):
        raise RuntimeError("R06 native rendezvous hold and staggered release missing")
    parent = replace(document, interaction_sequences=tuple(
        replace(s, steps=(*s.steps[:19], *s.steps[20:]))
        if s is matches[0] else s for s in document.interaction_sequences
    ))
    assert_two_actor_rendezvous(parent, variant=variant)
    return {"native_staggered_release_authored": True,
            "native_staggered_release_pixels_verified": False}


def verify_native_rendezvous_release(traces: dict) -> dict:
    """Prove stillness at joint X=395 then A's departure before B's."""
    meeting = verify_native_rendezvous(traces)
    if set(traces) != set(ACTOR_IDS):
        raise RuntimeError("Two independent Actor tracks required for native release")
    by_id = {actor: {row["frame"]: row for row in traces[actor]}
             for actor in ACTOR_IDS}
    shared = sorted(set(by_id[ACTOR_IDS[0]]) & set(by_id[ACTOR_IDS[1]]),
                    key=lambda f: by_id[ACTOR_IDS[0]][f]["seconds"])
    measured = []
    for left, right in zip(shared, shared[1:]):
        a0, a1 = by_id[ACTOR_IDS[0]][left], by_id[ACTOR_IDS[0]][right]
        b0, b1 = by_id[ACTOR_IDS[1]][left], by_id[ACTOR_IDS[1]][right]
        dt = a1["seconds"] - a0["seconds"]
        if not 0 < dt <= 1.5:
            continue
        measured.append({
            "frame": right, "seconds": a1["seconds"],
            "a_x": a1["world_x"], "b_x": b1["world_x"],
            "a_delta": a1["world_x"] - a0["world_x"],
            "b_delta": b1["world_x"] - b0["world_x"],
        })
    still = [
        row for row in measured
        if abs(row["a_x"] - MEETING_X) <= 25
        and abs(row["b_x"] - MEETING_X) <= 25
        and abs(row["a_delta"]) <= 8 and abs(row["b_delta"]) <= 8
    ]
    if len(still) < 2:
        raise RuntimeError("No two genuine native frames with both Actors stopped at meeting")
    a_departing = [
        row for row in measured
        if row["seconds"] > still[-1]["seconds"]
        and -55 <= row["a_delta"] <= -5
        and abs(row["b_delta"]) <= 8
        and abs(row["b_x"] - MEETING_X) <= 25
    ]
    if len(a_departing) < 3:
        raise RuntimeError("Native Actor A did not visibly depart before stationary B")
    b_departing = [
        row for row in measured
        if row["seconds"] > a_departing[-1]["seconds"]
        and 5 <= row["b_delta"] <= 55
    ]
    if len(b_departing) < 3:
        raise RuntimeError("Native Actor B did not subsequently depart from meeting")
    return {"native_rendezvous_staggered_release_verified": True,
            "meeting": meeting, "joint_still_frames": still,
            "a_first_frames": a_departing, "b_after_frames": b_departing}


def run_native_staggered_departure(upstream: Path, output: Path) -> dict:
    """Build three independent SCUMM-v6 games and verify actual captured pixels."""
    from .scumm_launch import launch_smoke
    from .scumm_toolchain import compile_story_game
    output.mkdir(parents=True, exist_ok=True)
    report = {"variants": {}, "complete_r06_284_acceptance": False}
    file = output / "native-r06-meeting-release-report.json"

    def persist():
        file.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        build = root / "build"
        resource = build / "resources"
        resource.mkdir(parents=True, exist_ok=True)
        data = author_native_staggered_departure(root, variant=variant)
        (build / "project.json").write_text(data, encoding="utf-8")
        doc = parse_document(data)
        assert_native_staggered_departure(doc, variant=variant)
        export_document(doc, resource)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(game, root / "screenshots", seconds=6,
                     scene_only=True, allow_static_scene=True,
                     native_two_actor_walk_probe=True)
        report["variants"][variant] = {"stock_scummvm_started": True}
        persist()

    transparent = output / "transparent" / "screenshots"
    traces = track_native_actor_lanes(transparent)
    report["native_meeting_release"] = verify_native_rendezvous_release(traces)
    report["native_camera_roundtrip"] = {
        variant: verify_two_actor_native_camera_roundtrip(
            measure_two_actor_native_camera_trace(output / variant / "screenshots"),
            expected_start=400, prepan_direction="either")
        for variant in ("masked", "transparent", "wrong-box")
    }
    report["native_zmask_controls"] = measure_two_actor_native_mask_comparison(
        output, traces)
    report["complete_r06_284_acceptance"] = True
    persist()
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_meeting_release_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_native_staggered_departure(
        Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
