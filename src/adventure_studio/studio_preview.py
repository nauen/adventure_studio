"""Authoring-only room preview; deliberately not a SCUMM resource exporter.

Coordinates and text are read directly from the validated story. Fixture
backgrounds give immediate visual feedback even for features the bounded
native compiler cannot yet represent. The preview does not prove playability.
"""

from __future__ import annotations

import unicodedata

from .story import Story
from .story_fixture_image import DeterministicStoryImageProvider
from .image_pipeline import ImageRequest


def _label(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.replace("ß", "ss"))
    return normalized.encode("ascii", "ignore").decode("ascii") or text


def preview_room_width(story: Story, scene_id: str) -> int:
    if scene_id not in {scene.id for scene in story.scenes}:
        raise ValueError(f"Unknown scene ID: {scene_id}")
    final = next((p for p in story.puzzles if p.id == story.final_puzzle_id), None)
    return 320 if final is not None and final.opens_scene_id == scene_id else 640


def preview_positions(story: Story, scene_id: str) -> dict[str, tuple[int, int]]:
    explicit = {p.item_id: (p.x, p.y) for p in story.placements}
    decorations = [i for i in story.items if i.scene_id == scene_id and i.role == "decoration"]
    pickups = [i for i in story.items if i.scene_id == scene_id and i.role == "pickup"]
    positions = {item.id: explicit.get(item.id, (160 + index * 40, 100))
                 for index, item in enumerate(decorations)}
    positions.update({item.id: explicit.get(item.id, (355 + index * 26, 100))
                      for index, item in enumerate(pickups)})
    return positions


def authoring_scene_preview(story: Story, scene_id: str
                            ) -> tuple[int, int, bytes, tuple[tuple[int, int, int], ...], tuple[tuple[str, int, int, int, int], ...]]:
    width = preview_room_width(story, scene_id)
    height = 200
    is_goal = width == 320
    request = ImageRequest(f"scene-{scene_id.lower()}-{'goal' if is_goal else 'main'}",
                           f"Story scene {scene_id}", width, height)
    image = DeterministicStoryImageProvider().generate(request)
    positions = preview_positions(story, scene_id)
    hotspots: list[tuple[str, int, int, int, int]] = []

    def marker(label: str, x: int, y: int) -> None:
        out_of_bounds = x + 16 > width or y + 16 > height
        # In an authoring preview even an invalid *export* placement must be
        # visible and repositionable. Preserve its real coordinates in Story.
        visible_x, visible_y = min(x, width - 16), min(y, height - 16)
        suffix = " (outside export room)" if out_of_bounds else ""
        hotspots.append((_label(label) + suffix, visible_x, visible_y, 16, 16))

    for item in story.items:
        if item.id in positions:
            x, y = positions[item.id]
            marker(item.name, x, y)

    for index, actor in enumerate(c for c in story.characters if c.scene_id == scene_id):
        marker(actor.name, 185 + index * 35, 110)

    for index, choice in enumerate(c for c in story.dialogue_choices
                                   if any(n.id == c.node_id and any(
                                       d.id == n.dialogue_id and d.scene_id == scene_id
                                       for d in story.dialogues) for n in story.dialogue_nodes)):
        marker(choice.text, 240 + index * 24, 130)

    # Exits are editor annotations, not a compiled/simulated game state.
    for puzzle in story.puzzles:
        if puzzle.scene_id == scene_id and puzzle.opens_scene_id is not None:
            marker("the exit", 450, 100)

    return width, height, image.pixels, image.palette, tuple(hotspots)
