"""Shared deterministic placeholder backgrounds for authoring and exporter tests.

These images are fixtures, not evidence that any native SCUMM room can be
rendered or that arbitrary art has been exported.
"""

from __future__ import annotations

from .image_pipeline import ImageRequest, IndexedImage


_PALETTE = ((70, 130, 190), (95, 60, 35), (240, 175, 95),
            (255, 220, 75), (60, 220, 90), (50, 220, 220), (120, 70, 180),
            (225, 80, 180), (160, 230, 55))


def _room_pixels(width: int, goal: bool) -> bytes:
    if goal:
        return bytes([6]) * (width * 200)
    return bytes(1 if y >= 150 else (2 if x >= 320 else 0)
                 for y in range(200) for x in range(width))


class DeterministicStoryImageProvider:
    """Offline source preserving existing fixture bytes and palettes."""

    def generate(self, request: ImageRequest) -> IndexedImage:
        if request.height != 200 or request.width not in (320, 640):
            raise ValueError("Unsupported fixture room geometry")
        is_goal = request.asset_id.endswith("-goal")
        return IndexedImage(_room_pixels(request.width, is_goal), _PALETTE,
                            request.width, request.height, "story-fixture:v1")
