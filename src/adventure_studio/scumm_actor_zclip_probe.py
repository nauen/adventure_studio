"""Stock-v6 Actor Z-clipping: real verb input, fixed camera and two stationary Actors."""
from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_project import canonical_json, parse_document, export_document
from .scumm_two_actor_four_mask_probe import (
    ACTOR_IDS, author_two_actor_four_mask_project, track_native_actor_lanes,
)
from .studio_sequences import append_sequence_step, author_room_walkbox_zplane
from .scumm_launch import launch_smoke
from .scumm_toolchain import compile_story_game


def author_project(root, variant, initial=False):
    doc = parse_document(author_two_actor_four_mask_project(root, variant=variant))
    costume = doc.costumes[-1]
    name = ("R06InitialZClip" if initial else "R06ZClip") + variant.title() + "Costume"
    # Both figures stand in ZP01's opaque region, but their walkbox uses 0.
    actors = tuple(replace(a, costume=name, x=240) if a.id in ACTOR_IDS else a
                   for a in doc.actors)
    doc = replace(doc, actors=actors,
                  costumes=(*doc.costumes[:-1], replace(costume, name=name)),
                  interaction_sequences=tuple(s for s in doc.interaction_sequences
                      if (s.room, s.hotspot_id, s.verb) != ("Harbor", "Key", "Close")))
    raw = canonical_json(doc)
    for box in range(1, 6):
        raw = author_room_walkbox_zplane(raw, "Harbor", box, 0)
    if initial:
        from .studio_actors import set_actor_initial_zclip
        raw = set_actor_initial_zclip(raw, ACTOR_IDS[0], 1)
        return append_sequence_step(raw, "Harbor", "Key", "Close",
                                    "Warten", None, None, None, 1)
    for kind, actor, amount in (
        ("Warten", None, 3),
        ("Actor Z-Clipping", ACTOR_IDS[0], 1),
        ("Warten", None, 5),
        ("Actor Z-Clipping", ACTOR_IDS[0], 0),
        ("Warten", None, 3),
    ):
        raw = append_sequence_step(raw, "Harbor", "Key", "Close",
                                   kind, actor, None, None, amount)
    return raw


def measure(root, initial=False):
    tracks = track_native_actor_lanes(root, include_before=initial)
    capture = json.loads((root / "r06-two-actor-walk-capture.json").read_text())
    frames = capture["captured_frames"]
    a, b = ({row["frame"]: row for row in tracks[actor]} for actor in ACTOR_IDS)
    # Only frames with the unaffected second Actor visible and stable count.
    samples = [{"frame": f["frame"], "seconds": f["seconds_since_native_input"],
                "a_visible": f["frame"] in a}
               for f in frames if f["frame"] in b
               and abs(b[f["frame"]]["world_x"] - 240) <= 8]
    if initial:
        before = "r06-two-actor-before"
        if before not in b or abs(b[before]["world_x"] - 240) > 8:
            raise RuntimeError("Reference Actor missing before first native input")
        samples.insert(0, {"frame": before, "seconds": -1, "a_visible": before in a})
    if len(samples) < 15:
        raise RuntimeError("Unchanged reference Actor not visible")
    if any(abs(row["world_x"] - 240) > 8 for row in a.values()):
        raise RuntimeError("Clipping Actor moved from authored position")
    return samples


def verify(masked, clear):
    if sum(s["a_visible"] for s in clear) < len(clear) * .85:
        raise RuntimeError("Transparent control Actor not continuously visible")
    # Require contiguous runs, not isolated animation or capture gaps.
    phases = []
    for row in masked:
        visible = row["a_visible"]
        if not phases or phases[-1]["visible"] != visible:
            phases.append({"visible": visible, "frames": 0, "start": row["seconds"]})
        phases[-1]["frames"] += 1
        phases[-1]["end"] = row["seconds"]
    stable = [p for p in phases if p["frames"] >= 4 and p["end"] - p["start"] >= .3]
    if [p["visible"] for p in stable] != [True, False, True]:
        raise RuntimeError(f"Native clipping/restoration not observed: {stable}")
    return {"native_actor_zclip_verified": True, "phases": stable,
            "reference_actor_stationary": True}


def run(upstream, output, initial=False):
    output.mkdir(parents=True, exist_ok=True)
    report = {"native_actor_zclip_verified": False}
    for variant in ("masked", "transparent"):
        root = output / variant
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        raw = author_project(root, variant, initial=initial)
        (build / "project.json").write_text(raw, encoding="utf-8")
        export_document(parse_document(raw), resources)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(game, root / "screenshots", seconds=6, scene_only=True,
                     allow_static_scene=True, native_two_actor_walk_probe=True,
                     native_two_actor_capture_frames=210)
        report[variant] = measure(root / "screenshots", initial=initial)
        (output / "report.json").write_text(json.dumps(report, indent=2))
    if initial:
        if not report["transparent"][0]["a_visible"]:
            raise RuntimeError("Transparent control Actor missing before first native input")
        if any(s["a_visible"] for s in report["masked"]):
            raise RuntimeError("Initially clipped Actor visible in opaque mask")
        if sum(s["a_visible"] for s in report["transparent"]) < len(report["transparent"]) * .85:
            raise RuntimeError("Initially clipped Actor missing in transparent control")
        report["native_initial_actor_zclip_verified"] = True
    else:
        report.update(verify(report["masked"], report["transparent"]))
    (output / "report.json").write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2]), initial='--initial' in sys.argv[3:]), indent=2))
