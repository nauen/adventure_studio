"""R10: stock-ScummVM perspective proof from a Studio-authored JSON project."""

from __future__ import annotations

from dataclasses import replace
import json
import struct
import sys
from pathlib import Path

from .scumm_assets import _native_box_file, destination_fixture
from .scumm_project import GameDocument, canonical_json, parse_document
from .scumm_room_fixture import native_room
from .scumm_room_visual_probe import render_native_room
from .studio_sequences import author_room_scale_curve


def verify_authored_scal_growth(counts: tuple[int, int, int]) -> dict:
    """Require ordered visible actor-size growth without overfitting one frame."""
    if (len(counts) != 3 or any(type(v) is not int or v < 300 for v in counts)
        or counts[1] < counts[0] + 100 or counts[2] < counts[1] + 25
        or counts[2] < counts[0] * 1.3):
        raise RuntimeError(f"Studio-authored SCAL perspective not visible in ScummVM: {counts}")
    return {"count_sequence": list(counts), "native_authored_scal_passed": True}


def run_authored_scal_probe(upstream: Path, generated: Path, destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    base = native_room(occlusion=False, far_scale=255)
    original = canonical_json(GameDocument("studio_scal", (base, destination_fixture())))
    authored_json = author_room_scale_curve(original, "Harbor", 1, 80, 70, 255, 155, "1,2")
    project_file = destination / "authored-scal-project.json"
    project_file.write_text(authored_json, encoding="utf-8")
    harbor = next(room for room in parse_document(project_file.read_text(encoding="utf-8")).rooms
                  if room.name == "Harbor")
    data = _native_box_file(harbor)
    offset = data.index(b"SCAL")
    if (struct.unpack_from("<HHHH", data, offset + 8) != (80, 70, 255, 155)
        or tuple(box.scale_slot for box in harbor.walkboxes) != (1, 1)):
        raise RuntimeError("SCAL project → native box encoding differs from Studio inputs")
    results = {"authoring": "Studio author function → project JSON → SCAL → stock ScummVM",
               "curve": {"slot": 1, "scale1": 80, "y1": 70, "scale2": 255, "y2": 155},
               "samples": {}}
    for y in (100, 125, 145):
        results["samples"][str(y)] = render_native_room(
            replace(harbor, demo_walk_to_y=y), upstream, generated, destination,
            f"authored-y{y}", crop="170x155+480+310")
    counts = tuple(results["samples"][str(y)]["dark_costume_pixels"]
                   for y in (100, 125, 145))
    results["comparison"] = verify_authored_scal_growth(counts)
    report = destination / "native-authored-scal-report.json"
    report.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    return results


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_authored_scal_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run_authored_scal_probe(Path(sys.argv[1]), Path(sys.argv[2]),
                                              Path(sys.argv[3])), indent=2))
