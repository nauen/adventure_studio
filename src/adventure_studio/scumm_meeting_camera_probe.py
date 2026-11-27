"""R06 #286: native camera inspection tour while both Actors wait at rendezvous.

Author SCUMM-v6 PanCameraStep/WaitCameraStep during a real two-Actor hold.
Visual acceptance uses only timestamp-aligned stock-ScummVM pixel captures.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_meeting_release_probe import (
    author_native_staggered_departure, assert_native_staggered_departure,
    verify_native_rendezvous_release,
)
from .scumm_opposing_actor_probe import ACTOR_IDS
from .scumm_rendezvous_probe import MEETING_X
from .scumm_project import (
    PanCameraStep, WaitCameraStep, DelayStep, canonical_json, parse_document, export_document,
)
from .scumm_two_actor_four_mask_probe import (
    track_native_actor_lanes, measure_two_actor_native_camera_trace,
    verify_two_actor_native_camera_roundtrip, measure_two_actor_native_mask_comparison,
)


CAMERA_TOUR = (
    PanCameraStep(480), WaitCameraStep(), DelayStep(1),
    PanCameraStep(MEETING_X), WaitCameraStep(), DelayStep(2),
)


def author_native_meeting_camera_tour(output: Path, *, variant: str = "masked") -> str:
    """Hold both native Actors at X395; inspect X480 and return before release."""
    document = parse_document(author_native_staggered_departure(output, variant=variant))
    previous = document.costumes[-1]
    costume_name = "R06MeetingCamera" + variant.replace("-", "").title() + "Costume"
    document = replace(
        document,
        costumes=(*document.costumes[:-1],
                  replace(previous, name=costume_name)),
        actors=tuple(replace(a, costume=costume_name)
                     if a.id in ACTOR_IDS else a for a in document.actors),
    )
    sequences = []
    for s in document.interaction_sequences:
        if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close"):
            # Current #284 parent: both native WaitActor arrivals and
            # the final joint hold precede index 20. Actor A departs at 20;
            # the entire camera tour must finish before either departure.
            sequences.append(replace(s, steps=(
                *s.steps[:20], *CAMERA_TOUR, *s.steps[20:],
            )))
        else:
            sequences.append(s)
    result = replace(document, interaction_sequences=tuple(sequences))
    assert_native_meeting_camera_tour(result, variant=variant)
    return canonical_json(result)


def assert_native_meeting_camera_tour(document, *, variant: str = "masked") -> dict:
    """Fail if the native camera tour is not between hold and Actor departures."""
    matches = [s for s in document.interaction_sequences
               if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")]
    if len(matches) != 1:
        raise RuntimeError("Native meeting camera tour requires one interaction")
    steps = matches[0].steps
    if len(steps) != 36 or steps[20:26] != CAMERA_TOUR:
        raise RuntimeError("Native meeting camera inspection pan and wait commands missing")
    parent = replace(document, interaction_sequences=tuple(
        replace(s, steps=(*s.steps[:20], *s.steps[26:]))
        if s is matches[0] else s for s in document.interaction_sequences
    ))
    assert_native_staggered_departure(parent, variant=variant)
    return {"native_meeting_camera_tour_authored": True,
            "native_meeting_camera_tour_pixels_verified": False}


def verify_native_meeting_camera_tour(traces: dict, camera_frames: list[dict]) -> dict:
    """Check real camera X480→X395 while two real Actors are immobile at X395."""
    if set(traces) != set(ACTOR_IDS):
        raise RuntimeError("Both independent native Actors required for camera tour")
    by_actor = {actor: {r["frame"]: r for r in traces[actor]}
                for actor in ACTOR_IDS}
    cameras = {r["frame"]: r for r in camera_frames}
    shared = sorted(
        set(by_actor[ACTOR_IDS[0]]) & set(by_actor[ACTOR_IDS[1]]) & set(cameras),
        key=lambda frame: cameras[frame]["seconds"],
    )
    if len(shared) < 8:
        raise RuntimeError("Too few real aligned frames for meeting camera tour")
    stationary = []
    for before, after in zip(shared, shared[1:]):
        ca, cb = cameras[before], cameras[after]
        if not 0 < cb["seconds"] - ca["seconds"] <= 1.5:
            continue
        actor_positions = [
            (by_actor[actor][before]["world_x"],
             by_actor[actor][after]["world_x"]) for actor in ACTOR_IDS
        ]
        if all(abs(before_x - MEETING_X) <= 25
               and abs(after_x - MEETING_X) <= 25
               and abs(after_x - before_x) <= 8
               for before_x, after_x in actor_positions):
            stationary.append({
                "frame": after, "seconds": cb["seconds"],
                "camera_x": cb["camera_x"],
                "camera_delta": cb["camera_x"] - ca["camera_x"],
            })
    if len(stationary) < 5:
        raise RuntimeError("Both native Actors did not visibly remain at meeting during tour")
    far = next((i for i, row in enumerate(stationary)
                if row["camera_x"] >= 475), None)
    if far is None:
        raise RuntimeError("Native camera inspection never reached X480 during Actor hold")
    returned = next((i for i in range(far + 1, len(stationary))
                     if abs(stationary[i]["camera_x"] - MEETING_X) <= 12), None)
    if returned is None:
        raise RuntimeError("Native camera inspection never returned to X395 during Actor hold")
    outbound = [r for r in stationary[:far + 1] if r["camera_delta"] >= 12]
    inbound = [r for r in stationary[far + 1:returned + 1]
               if r["camera_delta"] <= -12]
    if len(outbound) < 2 or len(inbound) < 2:
        raise RuntimeError("Missing consecutive real native camera pan frames during stationary Actors")
    return {"native_meeting_camera_tour_verified": True,
            "far": stationary[far], "returned": stationary[returned],
            "outward_frames": len(outbound), "inward_frames": len(inbound)}


def run_native_meeting_camera_tour(upstream: Path, output: Path) -> dict:
    """Three separately linked stock-ScummVM control games with screenshot V."""
    from .scumm_launch import launch_smoke
    from .scumm_toolchain import compile_story_game

    output.mkdir(parents=True, exist_ok=True)
    report = {"variants": {}, "complete_r06_286_acceptance": False}
    report_path = output / "native-r06-meeting-camera-report.json"

    def persist():
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        authored = author_native_meeting_camera_tour(root, variant=variant)
        (build / "project.json").write_text(authored, encoding="utf-8")
        project = parse_document(authored)
        assert_native_meeting_camera_tour(project, variant=variant)
        export_document(project, resources)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(game, root / "screenshots", seconds=6,
                     scene_only=True, allow_static_scene=True,
                     native_two_actor_walk_probe=True,
                     # Keep the planned 36 seconds of capture sleeps within
                     # play_two_actor_walk's existing 210–480 frame contract.
                     # Actual framebuffer acquisition adds to this duration.
                     native_two_actor_capture_frames=480,
                     native_two_actor_capture_interval=0.075,
                     native_two_actor_defer_preview=True)
        report["variants"][variant] = {"stock_scummvm_started": True}
        persist()

    screenshots = output / "transparent" / "screenshots"
    traces = track_native_actor_lanes(screenshots)
    camera_frames = measure_two_actor_native_camera_trace(screenshots)
    report["native_actor_tracks"] = traces
    report["native_camera_frames"] = camera_frames
    persist()
    report["native_camera_meeting_tour"] = verify_native_meeting_camera_tour(
        traces, camera_frames,
    )
    report["native_meeting_release"] = verify_native_rendezvous_release(traces)
    report["native_full_camera_roundtrip"] = {
        variant: verify_two_actor_native_camera_roundtrip(
            measure_two_actor_native_camera_trace(output / variant / "screenshots"),
            expected_start=400, prepan_direction="either",
        )
        for variant in ("masked", "transparent", "wrong-box")
    }
    report["four_mask_controls"] = measure_two_actor_native_mask_comparison(
        output, traces,
    )
    report["complete_r06_286_acceptance"] = True
    persist()
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: python -m adventure_studio.scumm_meeting_camera_probe SCUMMC_DIR OUTPUT"
        )
    print(json.dumps(run_native_meeting_camera_tour(
        Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
