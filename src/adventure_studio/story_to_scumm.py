"""A deliberately bounded, deterministic story-to-SCUMM adapter.

Only bounded linear puzzle routes are supported: one or two consecutive locks,
each requiring one to three local pickup items. Unsupported narrative mechanics
fail closed instead of silently disappearing from the exported adventure.
"""

from __future__ import annotations

import re
import unicodedata

from .image_pipeline import ImageProvider, ImageRequest, IndexedImage
from .story_fixture_image import DeterministicStoryImageProvider, _PALETTE
from .scumm_assets import CombineRule, RoomAsset, RoomHotspot, TalkChoice, TalkRule, TalkStage, UseRule
from .scumm_project import GameDocument
from .story import Story, verify_story
from .targets import RoomGeometry


_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_PICKUP_COLORS = (3, 7, 8)
_RECIPE_COLORS = (3, 7, 8, 9, 10, 11, 12, 13, 14)
_RECIPE_EXTRA_PALETTE = ((245, 100, 60), (85, 95, 245),
                         (255, 155, 35), (175, 80, 240),
                         (100, 245, 190), (235, 110, 130))


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


def _item_xy(story: Story, item_id: str, default_x: int,
             default_y: int, room_width: int) -> tuple[int, int]:
    placement = next((p for p in story.placements if p.item_id == item_id), None)
    if placement is None:
        return default_x, default_y
    if placement.x + 16 > room_width or placement.y + 16 > 200:
        raise ValueError(f"Item placement exceeds room geometry: {item_id}")
    return placement.x, placement.y


def _room_image(provider: ImageProvider, scene_id: str, width: int, goal: bool) -> IndexedImage:
    request = ImageRequest(f"scene-{scene_id.lower()}-{'goal' if goal else 'main'}",
                           f"Story scene {scene_id}", width, 200)
    image = provider.generate(request)
    if (image.width, image.height) != (width, 200):
        raise ValueError(f"Wrong generated scene dimensions: {scene_id}")
    return image


def _character_dialogue_objects(story: Story, scene_id: str, room_width: int
                                ) -> tuple[tuple[RoomHotspot, ...], tuple[TalkRule, ...]]:
    """Compile reachable branching dialogue stages into native answer hotspots.

    The authored graph may loop through a choice point; each stage owns distinct
    clickable objects, and the room script changes their visibility natively.
    """
    result = []
    rules = []
    for index, actor in enumerate(c for c in story.characters if c.scene_id == scene_id):
        if not _ID.fullmatch(actor.id):
            raise ValueError("Character ID is not a valid SCUMM identifier")
        dialogues = [d for d in story.dialogues if d.scene_id == scene_id and any(
            n.dialogue_id == d.id and n.speaker_id == actor.id for n in story.dialogue_nodes)]
        if len(dialogues) > 1:
            raise ValueError(f"Only one dialogue per character is supported: {actor.id}")
        lines = []
        if dialogues:
            dialogue = dialogues[0]
            nodes = {n.id: n for n in story.dialogue_nodes if n.dialogue_id == dialogue.id}
            by_node = {node_id: [c for c in story.dialogue_choices if c.node_id == node_id]
                       for node_id in nodes}
            entry_choice_node = None

            def follow(start: str | None) -> tuple[tuple[str, ...], str | None]:
                collected = []
                visited = set()
                current = start
                while current is not None:
                    if current in visited:
                        raise ValueError("Dialogue line cycle without choice point")
                    visited.add(current)
                    node = nodes[current]
                    if node.speaker_id != actor.id:
                        raise ValueError("Current SCUMM compiler requires one speaker per dialogue")
                    if by_node[current]:
                        return tuple(collected), current
                    collected.append(_text(node.text))
                    if len(collected) > 16:
                        raise ValueError("Dialogue text chain exceeds sixteen lines")
                    current = node.next_node_id
                return tuple(collected), None

            current = dialogue.entry_node_id
            visited = set()
            while current is not None and not by_node[current]:
                if current in visited:
                    raise ValueError("Dialogue line cycle without choices")
                visited.add(current)
                node = nodes[current]
                if node.speaker_id != actor.id:
                    raise ValueError("Current SCUMM compiler requires one speaker per dialogue")
                lines.append(_text(node.text))
                current = node.next_node_id
            if current is not None:
                entry_choice_node = current
                lines.append(_text(nodes[current].text))
                if len(lines) > 16:
                    raise ValueError("Dialogue opening exceeds sixteen lines")
                stages = []
                pending = [current]
                processed = set()
                stage_numbers = {node_id: number + 1 for number, node_id in enumerate(
                    sorted(node_id for node_id in nodes if by_node[node_id]))}
                while pending:
                    node_id = pending.pop(0)
                    if node_id in processed:
                        continue
                    processed.add(node_id)
                    source_choices = by_node[node_id]
                    if len(source_choices) > 3:
                        raise ValueError("SCUMM dialogue UI supports at most three answers per stage")
                    stage_choices = []
                    for choice_index, choice in enumerate(source_choices):
                        response, target = follow(choice.next_node_id)
                        if target is not None:
                            pending.append(target)
                        answer_id = (f"Answer{actor.id}{choice_index + 1}" if node_id == entry_choice_node
                                     else f"Answer{actor.id}N{stage_numbers[node_id]}C{choice_index + 1}")
                        answer_x = 240 + choice_index * 24
                        # SCUMM v6's room viewport ends at y=144. A second
                        # row below the entry answers would crash ScummVM.
                        answer_y = 130 if node_id == entry_choice_node else 100
                        if answer_x + 16 > room_width or not _ID.fullmatch(answer_id):
                            raise ValueError("Dialogue answer hotspot exceeds room exporter limits")
                        result.append(RoomHotspot(answer_id, _text(choice.text), _text(choice.text),
                                                  answer_x, answer_y, 16, 16,
                                                  sprite_pixels=_sprite(7, 3)))
                        stage_choices.append(TalkChoice(answer_id, _text(choice.text), response,
                                                        "Entry" if target == entry_choice_node else
                                                        f"Stage{target}" if target is not None else None))
                    if node_id == entry_choice_node:
                        root_choices = tuple(stage_choices)
                    else:
                        stages.append(TalkStage(f"Stage{node_id}", (_text(nodes[node_id].text),),
                                                tuple(stage_choices)))
                rules.append(TalkRule(actor.id, tuple(lines), root_choices, tuple(stages)))
            elif len(lines) > 16:
                raise ValueError("Dialogue opening exceeds sixteen lines")
        x = 185 + index * 35
        if x + 16 > room_width:
            raise ValueError("Too many characters for automatic room layout")
        result.append(RoomHotspot(actor.id, _text(actor.name), _text(actor.description),
                                  x, 110, 16, 16, sprite_pixels=_sprite(6, 3),
                                  talk_lines=tuple(lines) if not rules or rules[-1].speaker_id != actor.id else ()))
    return tuple(result), tuple(rules)


def _compile_recipe_story(story: Story, provider: ImageProvider) -> GameDocument:
    """Compile an acyclic inventory-recipe graph into a bounded room."""
    if (len(story.chapters) != 1 or len(story.scenes) != 2 or len(story.puzzles) != 1
            or not story.recipes or story.characters):
        raise ValueError("Recipe SCUMM adapter supports one chapter, one door and two scenes")
    puzzle = story.puzzles[0]
    recipes = story.recipes
    produced = {recipe.result_item_id for recipe in recipes}
    if (puzzle.id != story.final_puzzle_id or puzzle.scene_id != story.starting_scene_id
            or puzzle.opens_scene_id is None or puzzle.opens_scene_id == story.starting_scene_id
            or len(puzzle.requires) != 1 or puzzle.requires[0] not in produced):
        raise ValueError("One crafted recipe result must unlock the final door")
    if any(not _ID.fullmatch(v) for v in
           [*(c.id for c in story.chapters), *(s.id for s in story.scenes),
            *(i.id for i in story.items), puzzle.id, *(r.id for r in recipes)]):
        raise ValueError("Story identifiers must be valid SCUMM identifiers")
    by_id = {i.id: i for i in story.items}
    ingredients = {item_id for recipe in recipes for item_id in recipe.ingredients}
    if any(by_id[item_id].role not in ("pickup", "crafted")
           or by_id[item_id].scene_id != story.starting_scene_id
           or (by_id[item_id].role == "crafted") != (item_id in produced)
           for item_id in ingredients):
        raise ValueError("Recipe ingredients must be local pickups or crafted recipe results")
    if any(by_id[item_id].scene_id != story.starting_scene_id for item_id in produced):
        raise ValueError("Crafted results must belong to starting scene")
    if any(i.role in ("pickup", "crafted") and i.id not in ingredients | produced
           for i in story.items):
        raise ValueError("Recipe fixture has an unreferenced mechanical item")
    # A consumed ingredient may participate in only one recipe; otherwise the
    # generated adventure would expose a choice with a dead-end branch.
    inputs = [item for recipe in recipes for item in recipe.ingredients]
    if len(inputs) != len(set(inputs)):
        raise ValueError("A recipe ingredient cannot be consumed by multiple recipes")
    if any(result != puzzle.requires[0] and result not in ingredients for result in produced):
        raise ValueError("Every intermediate recipe result must feed another recipe")
    if "Door" in by_id:
        raise ValueError("Story item conflicts with generated Door")
    decorations = [i for i in story.items if i.role == "decoration" and i.scene_id == story.starting_scene_id]
    if len(decorations) > 4:
        raise ValueError("Too many decorations for automatic layout")
    hotspots = [RoomHotspot(i.id, _text(i.name), _text(i.description),
                            *_item_xy(story, i.id, 160 + index * 40, 100, 640), 16, 16, sprite_pixels=_sprite(1, 4))
                for index, i in enumerate(decorations)]
    inventory_items = [i.id for i in story.items if i.role in ("pickup", "crafted")]
    if len(inventory_items) > len(_RECIPE_COLORS):
        raise ValueError("Too many recipe inventory objects for the fixed palette")
    for index, item_id in enumerate(inventory_items):
        item = by_id[item_id]
        hotspots.append(RoomHotspot(item.id, _text(item.name), _text(item.description),
                                    *_item_xy(story, item.id, 355 + index * 26, 100, 640), 16, 16, True,
                                    _sprite(_RECIPE_COLORS[index], 2)))
    hotspots.append(RoomHotspot("Door", "the exit", _text(puzzle.title),
                                500 if len(inventory_items) > 5 else 450, 100, 16, 16, False, _sprite(4, 1),
                                open_sprite_pixels=_sprite(5, 2),
                                exit_destination=puzzle.opens_scene_id))
    start_image = _room_image(provider, story.starting_scene_id, 640, False)
    goal_image = _room_image(provider, puzzle.opens_scene_id, 320, True)
    if len(inventory_items) > len(_PICKUP_COLORS):
        if len(start_image.palette) != len(_PALETTE):
            raise ValueError("Chained recipe rooms require the nine-color base palette")
        start_palette = start_image.palette + _RECIPE_EXTRA_PALETTE[:len(inventory_items) - len(_PICKUP_COLORS)]
    else:
        start_palette = start_image.palette
    start_room = RoomAsset(story.starting_scene_id, RoomGeometry(640, 200, 320, 200),
                           start_image.pixels, start_palette, tuple(hotspots), 540,
                           (UseRule(puzzle.requires[0], "Door", _text(puzzle.title), open_target=True),),
                           combine_rules=tuple(CombineRule(recipe.ingredients[0], recipe.ingredients[1],
                                                           recipe.result_item_id, _text(recipe.title))
                                               for recipe in recipes))
    goal_room = RoomAsset(puzzle.opens_scene_id, RoomGeometry(320, 200, 320, 200),
                          goal_image.pixels, goal_image.palette,
                          goal_text=_text(puzzle.title))
    return GameDocument(story.chapters[0].id + "Game", (start_room, goal_room))


def compile_story_to_scumm(story: Story, image_provider: ImageProvider | None = None) -> GameDocument:
    """Compile bounded linear item-and-door puzzles, never story-authored scripts."""
    verify_story(story)
    if story.assets:
        raise ValueError("SCUMM exporter does not yet support versioned asset references")
    provider = image_provider if image_provider is not None else DeterministicStoryImageProvider()
    if story.recipes:
        return _compile_recipe_story(story, provider)
    if (len(story.chapters) != 1 or not 1 <= len(story.puzzles) <= 2
            or len(story.scenes) != len(story.puzzles) + 1):
        raise ValueError("Exporter supports one chapter and one or two sequential door puzzles")
    # Follow scene transitions, never incidental input ordering. Acyclic,
