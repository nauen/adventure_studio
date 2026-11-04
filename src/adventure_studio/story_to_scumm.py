"""A deliberately bounded, deterministic story-to-SCUMM adapter.

Only the first fully implemented puzzle pattern is supported: one pickup item
unlocks a visible exit into the final scene. Unsupported narrative mechanics
fail closed instead of silently disappearing from the exported adventure.
"""

from __future__ import annotations

import re
import unicodedata

from .scumm_assets import RoomAsset, RoomHotspot, UseRule
from .scumm_project import GameDocument
from .story import Story, verify_story
from .targets import RoomGeometry


_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_PALETTE = ((70, 130, 190), (95, 60, 35), (240, 175, 95),
            (255, 220, 75), (60, 220, 90), (50, 220, 220), (120, 70, 180))


def _text(value: str) -> str:
    # The current demo character set supports ASCII, not arbitrary Unicode.
    # Keep this deterministic and separate from authored story content.
    value = unicodedata.normalize("NFKD", value.replace("ß", "ss"))
    value = value.encode("ascii", "ignore").decode("ascii")
    value = " ".join(value.replace('"', "'").replace("\\", "-").split())
    if not value:
        raise ValueError("Story text cannot be represented in the demo font")
    return value[:160]


def _sprite(index: int, interior: int) -> bytes:
    return bytes(index if x in (0, 15) or y in (0, 15) else interior
                 for y in range(16) for x in range(16))


def _room_pixels(width: int, goal: bool) -> bytes:
    if goal:
        return bytes([6]) * (width * 200)
    return bytes(1 if y >= 150 else (2 if x >= 320 else 0)
                 for y in range(200) for x in range(width))


def compile_story_to_scumm(story: Story) -> GameDocument:
    """Compile the supported one-item, one-lock, two-scene story subset."""
    verify_story(story)
    if (len(story.chapters) != 1 or len(story.scenes) != 2 or len(story.puzzles) != 1
            or story.characters):
        raise ValueError("Exporter currently supports one chapter, two scenes, one puzzle and no custom actors")
    if story.final_puzzle_id != story.puzzles[0].id:
        raise ValueError("Final goal must be the room-unlocking puzzle")
    puzzle = story.puzzles[0]
    if (puzzle.scene_id != story.starting_scene_id or puzzle.opens_scene_id is None
            or puzzle.opens_scene_id == story.starting_scene_id or len(puzzle.requires) != 1):
        raise ValueError("Final puzzle must unlock the second scene using exactly one item")
    if any(not _ID.fullmatch(id_) for id_ in
           [*(c.id for c in story.chapters), *(s.id for s in story.scenes),
            *(i.id for i in story.items), puzzle.id]):
        raise ValueError("Story identifiers must be valid SCUMM identifiers")
    if "Door" in {i.id for i in story.items}:
        raise ValueError("Story item conflicts with generated exit identifier")
    key = next(i for i in story.items if i.id == puzzle.requires[0])
    if key.scene_id != story.starting_scene_id or key.role != "pickup":
        raise ValueError("Required item must be a pickup in the initial room")
    if any(i.role == "pickup" and i.id != key.id for i in story.items):
        raise ValueError("Additional pickup mechanics are not yet supported")
    for scene in story.scenes:
        if sum(i.role == "decoration" and i.scene_id == scene.id for i in story.items) > 4:
            raise ValueError("Too many decorations for the current automatic layout")

    scenes = {s.id: s for s in story.scenes}
    start = story.starting_scene_id
    target = puzzle.opens_scene_id
    result = []
    for scene_id in (start, target):
        goal = scene_id == target
        width = 320 if goal else 640
        decorations = [i for i in story.items if i.role == "decoration" and i.scene_id == scene_id]
        hotspots = [RoomHotspot(i.id, _text(i.name), _text(i.description),
                                160 + index * 40, 100, 16, 16,
                                sprite_pixels=_sprite(1, 4))
                    for index, i in enumerate(decorations)]
        if not goal:
            hotspots.extend([
                RoomHotspot(key.id, _text(key.name), _text(key.description),
                            355, 100, 16, 16, True, _sprite(3, 2)),
                RoomHotspot("Door", "the exit", _text(puzzle.title),
                            450, 100, 16, 16, False, _sprite(4, 1),
                            open_sprite_pixels=_sprite(5, 2), exit_destination=target),
            ])
        result.append(RoomAsset(
            scene_id, RoomGeometry(width, 200, 320, 200), _room_pixels(width, goal), _PALETTE,
            hotspots=tuple(hotspots), demo_walk_to_x=540 if not goal else None,
            use_rules=(UseRule(key.id, "Door", _text(puzzle.title), open_target=True),) if not goal else (),
            goal_text=_text(puzzle.title) if goal else None,
        ))
    return GameDocument(story.chapters[0].id + "Game", tuple(result))
