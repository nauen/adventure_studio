"""R06 #302: two independent native Actors cross while camera stays on stage.

Accept only timestamp-aligned stock-ScummVM screenshot tracks. Independent
masked, transparent and wrong-box games preserve the native four-Z-mask test.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_free_camera_probe import (
    author_native_camera_release, assert_native_camera_release,
    verify_native_camera_release,
)
from .scumm_opposing_actor_probe import ACTOR_IDS
from .scumm_rendezvous_probe import MEETING_X
from .scumm_project import (
    WalkActorStep, WaitActorStep, canonical_json, parse_document, export_document,
)
from .scumm_two_actor_four_mask_probe import (
    track_native_actor_lanes, measure_two_actor_native_camera_trace,
    verify_two_actor_native_camera_roundtrip, measure_two_actor_native_mask_comparison,
)

NATIVE_CROSSOVER = (
    WalkActorStep(ACTOR_IDS[0], 545, 85),
    WalkActorStep(ACTOR_IDS[1], 260, 135),
    WaitActorStep(ACTOR_IDS[0]),
    WaitActorStep(ACTOR_IDS[1]),
)


def author_native_stage_crossover(output: Path, *, variant: str = "masked") -> str:
    """After the fixed camera shot, send A right and B left without serial wait."""
    document = parse_document(author_native_camera_release(output, variant=variant))
    old = document.costumes[-1]
    costume = "R06StageCrossover" + variant.replace("-", "").title() + "Costume"
    document = replace(
        document,
        costumes=(*document.costumes[:-1], replace(old, name=costume)),
        actors=tuple(replace(a, costume=costume) if a.id in ACTOR_IDS else a
                     for a in document.actors),
    )
    sequences = tuple(
        replace(s, steps=(*s.steps[:45], *NATIVE_CROSSOVER, *s.steps[45:]))
        if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")
        else s for s in document.interaction_sequences
    )
    result = replace(document, interaction_sequences=sequences)
    assert_native_stage_crossover(result, variant=variant)
    return canonical_json(result)


def assert_native_stage_crossover(document, *, variant: str = "masked") -> dict:
    """Reject missing, serial or incorrectly targeted native crossing walks."""
    matches = [s for s in document.interaction_sequences
               if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")]
    if len(matches) != 1:
        raise RuntimeError("Native stage crossover requires one Key interaction")
    steps = matches[0].steps
    if len(steps) != 56 or steps[45:49] != NATIVE_CROSSOVER:
        raise RuntimeError("Both native Actors must cross before either WaitActor")
    parent = replace(document, interaction_sequences=tuple(
        replace(s, steps=(*s.steps[:45], *s.steps[49:]))
        if s is matches[0] else s for s in document.interaction_sequences
    ))
    assert_native_camera_release(parent, variant=variant)
    return {"two_native_stage_crossing_walks_authored": True,
            "two_native_stage_crossing_walks_pixels_verified": False}


def verify_native_stage_crossover(traces: dict, camera_frames: list[dict]) -> dict:
    """Demand independently observed opposing walks crossing with camera X395."""
    if set(traces) != set(ACTOR_IDS):
        raise RuntimeError("Two independently tracked native Actors required")
    # Establish preceding A-B-A-B and free-camera evidence before the new
    # crossing. Later actor motion must not masquerade as the old A focus.
    ordered = sorted(camera_frames, key=lambda r: r["seconds"])
    last_far = next((i for i in reversed(range(len(ordered)))
                     if ordered[i]["camera_x"] >= 475), None)
    if last_far is None:
        raise RuntimeError("Fourth native B camera focus never reached far side")
    stage = [r for r in ordered[last_far + 1:]
             if abs(r["camera_x"] - MEETING_X) <= 5]
    if len(stage) < 2:
        raise RuntimeError("Missing genuine camera return-to-stage frames")
    cutoff = stage[1]["seconds"]
    prior = verify_native_camera_release(
        {actor: [r for r in traces[actor] if r["seconds"] <= cutoff]
         for actor in ACTOR_IDS},
        [r for r in ordered if r["seconds"] <= cutoff])
    cameras = {row["frame"]: row for row in camera_frames}
    by_actor = {actor: {r["frame"]: r for r in traces[actor]}
                for actor in ACTOR_IDS}
    start = prior["free_stage_frames"][0]["seconds"]
    frames = sorted(
        ({"frame": frame, "seconds": cameras[frame]["seconds"],
          "camera_x": cameras[frame]["camera_x"],
          "a_x": by_actor[ACTOR_IDS[0]][frame]["world_x"],
          "b_x": by_actor[ACTOR_IDS[1]][frame]["world_x"]}
         for frame in set(cameras) & set(by_actor[ACTOR_IDS[0]])
                      & set(by_actor[ACTOR_IDS[1]])
         if cameras[frame]["seconds"] >= start
         and abs(cameras[frame]["camera_x"] - MEETING_X) <= 5),
        key=lambda r: r["seconds"],
    )
    if len(frames) < 10:
        raise RuntimeError("Too few real stationary-camera crossover frames")
    initial = next((r for r in frames if r["a_x"] + 40 < r["b_x"]), None)
    if initial is None:
        raise RuntimeError("Native Actors did not start crossing from opposite sides")
    crossed = [
        r for r in frames
        if r["seconds"] > initial["seconds"]
        and r["a_x"] > r["b_x"] + 40
        and r["a_x"] - initial["a_x"] >= 140
        and initial["b_x"] - r["b_x"] >= 140
    ]
    if len(crossed) < 2:
        raise RuntimeError("Both native Actors did not cross 140px in opposite directions")
    simultaneous = []
    for before, after in zip(frames, frames[1:]):
        delta_t = after["seconds"] - before["seconds"]
        if 0 < delta_t <= 1.5 and after["a_x"] > before["a_x"] + 3 and after["b_x"] < before["b_x"] - 3:
            simultaneous.append(after)
    if len(simultaneous) < 2:
        raise RuntimeError("Native Actors did not walk simultaneously in opposite directions")
    return {"native_stage_crossover_verified": True,
            "fixed_camera_x": MEETING_X,
            "crossing_frames": crossed,
            "simultaneous_actor_frames": simultaneous,
            "prior_camera_release": prior}


def run_native_stage_crossover(upstream: Path, output: Path) -> dict:
    """Run three real games, retain native screenshots, fail closed on missing motion."""
    from .scumm_launch import launch_smoke
    from .scumm_toolchain import compile_story_game

    output.mkdir(parents=True, exist_ok=True)
    report = {"variants": {}, "complete_r06_302_acceptance": False}
    evidence = output / "native-r06-stage-crossover-report.json"

    def persist():
        evidence.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")

    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        authored = author_native_stage_crossover(root, variant=variant)
        (build / "project.json").write_text(authored, encoding="utf-8")
        doc = parse_document(authored)
        assert_native_stage_crossover(doc, variant=variant)
        export_document(doc, resources)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(game, root / "screenshots", seconds=6,
                     scene_only=True, allow_static_scene=True,
                     native_two_actor_walk_probe=True,
                     native_two_actor_capture_frames=480)
        report["variants"][variant] = {"stock_scummvm_started": True}
        persist()

    transparent = output / "transparent" / "screenshots"
    tracks = track_native_actor_lanes(transparent)
    camera = measure_two_actor_native_camera_trace(transparent)
    report["stage_crossing"] = verify_native_stage_crossover(tracks, camera)
    report["native_camera_roundtrip"] = {
        variant: verify_two_actor_native_camera_roundtrip(
            measure_two_actor_native_camera_trace(output / variant / "screenshots"),
            expected_start=400, prepan_direction="either")
        for variant in ("masked", "transparent", "wrong-box")
    }
    report["native_four_mask_controls"] = measure_two_actor_native_mask_comparison(
        output, tracks)
    report["complete_r06_302_acceptance"] = True
    persist()
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_stage_crossover_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_native_stage_crossover(
        Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
