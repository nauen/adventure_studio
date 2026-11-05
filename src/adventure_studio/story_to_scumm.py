"""A deliberately bounded, deterministic story-to-SCUMM adapter.

Only bounded linear puzzle routes are supported: one or two consecutive locks,
each requiring one to three local pickup items. Unsupported narrative mechanics
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
            (255, 220, 75), (60, 220, 90), (50, 220, 220), (120, 70, 180),
            (225, 80, 180), (160, 230, 55))
_PICKUP_COLORS = (3, 7, 8)


def _text(value: str) -> str:
    # The current demo character set supports ASCII, not arbitrary Unicode.
    # Keep this deterministic and separate from authored story content.
    value = unicodedata.normalize("NFKD", value.replace("ß", "ss"))
    value = value.encode("ascii", "ignore").decode("ascii")
    value = " ".join(value.replace('"', "'").replace("\\", "-").split())
    if not value:
        raise ValueError("Story text cannot be represented in the demo font")
    if len(value) > 160:
        raise ValueError("Story text exceeds the SCUMM demo text limit")
    return value


def _sprite(index: int, interior: int) -> bytes:
    return bytes(index if x in (0, 15) or y in (0, 15) else interior
                 for y in range(16) for x in range(16))


def _room_pixels(width: int, goal: bool) -> bytes:
    if goal:
        return bytes([6]) * (width * 200)
    return bytes(1 if y >= 150 else (2 if x >= 320 else 0)
                 for y in range(200) for x in range(width))


def compile_story_to_scumm(story: Story) -> GameDocument:
    """Compile bounded linear item-and-door puzzles, never story-authored scripts."""
    verify_story(story)
    if (len(story.chapters) != 1 or not 1 <= len(story.puzzles) <= 2
            or len(story.scenes) != len(story.puzzles) + 1 or story.characters):
        raise ValueError("Exporter supports one chapter, one or two sequential door puzzles, and no custom actors")
    # Follow scene transitions, never incidental input ordering. Acyclic,
    # complete use of all puzzles and scenes is a strict export precondition.
    route = [story.starting_scene_id]
    ordered_puzzles = []
    remaining = {p.id: p for p in story.puzzles}
    while remaining:
        candidates = [p for p in remaining.values() if p.scene_id == route[-1]]
        if len(candidates) != 1:
            raise ValueError("Door puzzles must form one unbranched route")
        puzzle = candidates[0]
        if (puzzle.opens_scene_id is None or puzzle.opens_scene_id in route
                or not 1 <= len(puzzle.requires) <= 3):
            raise ValueError("Each door must unlock a new scene using one to three items")
        ordered_puzzles.append(puzzle)
        route.append(puzzle.opens_scene_id)
        del remaining[puzzle.id]
    if len(set(route)) != len(story.scenes) or ordered_puzzles[-1].id != story.final_puzzle_id:
        raise ValueError("Final puzzle must unlock the last scene in the route")
    if any(not _ID.fullmatch(id_) for id_ in
           [*(c.id for c in story.chapters), *(s.id for s in story.scenes),
            *(i.id for i in story.items), *(p.id for p in story.puzzles)]):
        raise ValueError("Story identifiers must be valid SCUMM identifiers")
    if {"Door", "Door2", "Back2", "Back3"} & {i.id for i in story.items}:
        raise ValueError("Story item conflicts with generated exit identifier")
    pickups_by_puzzle = [tuple(next(i for i in story.items if i.id == required)
                               for required in puzzle.requires) for puzzle in ordered_puzzles]
    if any(item.scene_id != puzzle.scene_id or item.role != "pickup"
           for puzzle, pickups in zip(ordered_puzzles, pickups_by_puzzle) for item in pickups):
        raise ValueError("Each puzzle requires pickups from its own scene")
    if any(i.role == "pickup" and sum(i.id in puzzle.requires for puzzle in ordered_puzzles) != 1
           for i in story.items):
        raise ValueError("Unreferenced pickup mechanics are not yet supported")
    for scene in story.scenes:
        if sum(i.role == "decoration" and i.scene_id == scene.id for i in story.items) > 4:
            raise ValueError("Too many decorations for the current automatic layout")

    result = []
    pickup_number = 0
    for scene_index, scene_id in enumerate(route):
        goal = scene_index == len(ordered_puzzles)
        puzzle = ordered_puzzles[scene_index] if not goal else None
        pickups = pickups_by_puzzle[scene_index] if not goal else ()
        width = 320 if goal else 640
        decorations = [i for i in story.items if i.role == "decoration" and i.scene_id == scene_id]
        hotspots = [RoomHotspot(i.id, _text(i.name), _text(i.description),
                                160 + index * 40, 100, 16, 16,
                                sprite_pixels=_sprite(1, 4))
                    for index, i in enumerate(decorations)]
        if len(route) > 2 and scene_index > 0:
            # Visible, unconditional passage back to the previous story scene.
            # Object ownership and door states belong to the SCUMM engine;
            # revisit tests must prove that they survive these transitions.
            hotspots.append(RoomHotspot(f"Back{scene_index + 1}", "back", "Back to previous room.",
                                        120, 100, 16, 16, False, _sprite(8, 1),
                                        exit_destination=route[scene_index - 1]))
        if not goal:
            for index, item in enumerate(pickups):
                if pickup_number >= len(_PICKUP_COLORS):
                    raise ValueError("Current visual fixture supports at most three pickups across the route")
                hotspots.append(RoomHotspot(item.id, _text(item.name), _text(item.description),
                                            355 + index * 26, 100, 16, 16, True,
                                            _sprite(_PICKUP_COLORS[pickup_number], 2)))
                pickup_number += 1
            door_id = "Door" if scene_index == 0 else f"Door{scene_index + 1}"
            hotspots.append(RoomHotspot(door_id, "the exit", _text(puzzle.title),
                                        450, 100, 16, 16, False, _sprite(4, 1),
                                        open_sprite_pixels=_sprite(5, 2),
                                        exit_destination=puzzle.opens_scene_id))
        result.append(RoomAsset(
            scene_id, RoomGeometry(width, 200, 320, 200), _room_pixels(width, goal), _PALETTE,
            hotspots=tuple(hotspots), demo_walk_to_x=540 if not goal else None,
            use_rules=(UseRule(pickups[0].id, door_id, _text(puzzle.title), open_target=True,
                               requires_inventory=tuple(item.id for item in pickups[1:])),) if not goal else (),
            goal_text=_text(ordered_puzzles[-1].title) if goal else None,
        ))
    return GameDocument(story.chapters[0].id + "Game", tuple(result))
