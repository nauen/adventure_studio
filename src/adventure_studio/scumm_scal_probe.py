"""Native SCUMM-v6 perspective scaling evidence over several Y destinations."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .scumm_room_fixture import perspective_room
from .scumm_room_visual_probe import render_native_room


def expected_vertical_scale(y: int, *, y1: int = 70, scale1: int = 80,
                            y2: int = 155, scale2: int = 255) -> int:
    """ScummVM boxes.cpp getScaleFromSlot integer interpolation for x1 == x2."""
    if type(y) is not int or not y1 < y2:
        raise ValueError("Invalid perspective sample")
    return max(1, min(255, int((scale2 - scale1) * (y - y1) / (y2 - y1)) + scale1))


def verify_perspective_progression(counts: tuple[int, int, int]) -> dict:
    """Require a clearly visible native costume expansion at increasing depths."""
    if len(counts) != 3 or any(type(v) is not int or v < 0 for v in counts):
        raise ValueError("Three nonnegative costume pixel counts are required")
    near, middle, far = counts
    if near < 300 or middle < near + 100 or far < middle + 75:
        raise RuntimeError(f"Native SCAL perspective silhouette did not grow: {counts}")
    return {"count_sequence": list(counts), "perspective_scaling_passed": True}


def run_scale_probe(upstream: Path, generated: Path, destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    results = {}
    # Crop includes the complete character across the chosen walk Y range,
    # while excluding the verb UI and black virtual-screen borders.
    crop = "170x155+480+310"
    for target_y in (100, 125, 145):
        name = f"y{target_y}"
        results[name] = {
            "target_y": target_y,
            "expected_scale_at_target": expected_vertical_scale(target_y),
            **render_native_room(perspective_room(target_y=target_y), upstream,
                                 generated, destination, name, crop=crop),
        }
    results["comparison"] = verify_perspective_progression(
        tuple(results[f"y{y}"]["dark_costume_pixels"] for y in (100, 125, 145))
    )
    (destination / "native-scal-perspective-report.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return results


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_scal_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run_scale_probe(Path(sys.argv[1]), Path(sys.argv[2]),
                                     Path(sys.argv[3])), indent=2))
