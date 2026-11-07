"""Small deterministic SCUMM-v6 room for native mask/walkbox experiments."""

from dataclasses import replace

from .scumm_assets import Walkbox, ZPlane, scrolling_fixture


def native_room(*, occlusion: bool = True, far_scale: int = 180):
    original = scrolling_fixture()
    width, height = original.geometry.room_width, original.geometry.room_height
    # Room coordinates are magnified by the ScummVM output viewport.  The
    # costume at walking baseline y=100 occupies approximately y=65..100,
    # so this band intersects its torso rather than the ground below it.
    mask = bytes(1 if occlusion and x > width // 2 and 60 < y < 110 else 0
                 for y in range(height) for x in range(width))
    boxes = (
        Walkbox(((0, 70), (120, 70), (120, 150), (0, 150))),
        Walkbox(((120, 70), (width - 1, 70), (width - 1, 150), (120, 150)),
                mask=1, scale=far_scale),
    )
    routes = ((0, None, None), (None, 1, 2), (None, 1, 2))
    return replace(original, zplanes=(ZPlane(1, mask),), walkboxes=boxes,
                   box_routes=routes, scale_slots=bytes(32))
