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
from .scumm_project import ActorAsset, GameDocument
from .scumm_costume import CostumeAsset, CostumeFrame, CostumeDirection, CostumeAnimation
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
        dialogues = [d for d in story.dialogues if d.scene_id == scene_id and
                     next(n for n in story.dialogue_nodes if n.id == d.entry_node_id).speaker_id == actor.id]
        if len(dialogues) > 1:
            raise ValueError(f"Only one dialogue per character is supported: {actor.id}")
        lines = []
        line_speakers = []
        if dialogues:
            dialogue = dialogues[0]
            nodes = {n.id: n for n in story.dialogue_nodes if n.dialogue_id == dialogue.id}
            by_node = {node_id: [c for c in story.dialogue_choices if c.node_id == node_id]
                       for node_id in nodes}
            entry_choice_node = None

            multi = len({n.speaker_id for n in nodes.values()}) > 1
            actor_lines = []
            base = f"room.{scene_id.lower()}.dialogue.{len(rules)}"

            def bind(key: str, speaker: str) -> None:
                if multi:
                    actor_lines.append((key, f"Speaker{speaker}"))

            def follow(start: str | None) -> tuple[tuple[str, ...], str | None, tuple[str, ...]]:
                collected = []
                speakers = []
                visited = set()
                current = start
                while current is not None:
                    if current in visited:
                        raise ValueError("Dialogue line cycle without choice point")
                    visited.add(current)
                    node = nodes[current]
                    if by_node[current]:
                        return tuple(collected), current, tuple(speakers)
                    collected.append(_text(node.text))
                    speakers.append(node.speaker_id)
                    if len(collected) > 16:
                        raise ValueError("Dialogue text chain exceeds sixteen lines")
                    current = node.next_node_id
                return tuple(collected), None, tuple(speakers)

            current = dialogue.entry_node_id
            visited = set()
            while current is not None and not by_node[current]:
                if current in visited:
                    raise ValueError("Dialogue line cycle without choices")
                visited.add(current)
                node = nodes[current]
                lines.append(_text(node.text))
                line_speakers.append(node.speaker_id)
                current = node.next_node_id
            if current is not None:
                entry_choice_node = current
                lines.append(_text(nodes[current].text))
                line_speakers.append(nodes[current].speaker_id)
                for line_index, speaker in enumerate(line_speakers):
                    bind(f"{base}.opening.{line_index}", speaker)
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
                        response, target, response_speakers = follow(choice.next_node_id)
                        if target is not None:
                            pending.append(target)
                        answer_id = (f"Answer{actor.id}{choice_index + 1}" if node_id == entry_choice_node
                                     else f"Answer{actor.id}N{stage_numbers[node_id]}C{choice_index + 1}")
                        answer_x = 240 + choice_index * 24
                        # Preserve the proven flat-dialogue layout. Nested
                        # stages must fit both rows inside the 144px viewport.
                        answer_y = (120 if len(stage_numbers) > 1 else 130) if node_id == entry_choice_node else 100
                        if answer_x + 16 > room_width or not _ID.fullmatch(answer_id):
                            raise ValueError("Dialogue answer hotspot exceeds room exporter limits")
                        result.append(RoomHotspot(answer_id, _text(choice.text), _text(choice.text),
                                                  answer_x, answer_y, 16, 16,
                                                  sprite_pixels=_sprite(7, 3)))
                        stage_choices.append(TalkChoice(answer_id, _text(choice.text), response,
                                                        "Entry" if target == entry_choice_node else
                                                        f"Stage{target}" if target is not None else None))
                        prefix = (base if node_id == entry_choice_node else
                                  f"{base}.stage.{len(stages)}")
                        for line_index, speaker in enumerate(response_speakers):
                            bind(f"{prefix}.choice.{choice_index}.reply.{line_index}", speaker)
                    if node_id == entry_choice_node:
                        root_choices = tuple(stage_choices)
                    else:
                        stages.append(TalkStage(f"Stage{node_id}", (_text(nodes[node_id].text),),
                                                tuple(stage_choices)))
                        bind(f"{base}.stage.{len(stages) - 1}.opening.0", nodes[node_id].speaker_id)
                rules.append(TalkRule(actor.id, tuple(lines), root_choices, tuple(stages),
                                      tuple(actor_lines)))
            elif multi:
                raise ValueError("Multispeaker dialogue currently requires at least one answer stage")
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
            *(i.id for i in story.items), *(p.id for p in story.puzzles),
            *(c.id for c in story.characters)]):
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
                                *_item_xy(story, i.id, 160 + index * 40, 100, width), 16, 16,
                                sprite_pixels=_sprite(1, 4))
                    for index, i in enumerate(decorations)]
        actors, talk_rules = _character_dialogue_objects(story, scene_id, width)
        hotspots.extend(actors)
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
                                            *_item_xy(story, item.id, 355 + index * 26, 100, width), 16, 16, True,
                                            _sprite(_PICKUP_COLORS[pickup_number], 2)))
                pickup_number += 1
            door_id = "Door" if scene_index == 0 else f"Door{scene_index + 1}"
            hotspots.append(RoomHotspot(door_id, "the exit", _text(puzzle.title),
                                        450, 100, 16, 16, False, _sprite(4, 1),
                                        open_sprite_pixels=_sprite(5, 2),
                                        exit_destination=puzzle.opens_scene_id))
        image = _room_image(provider, scene_id, width, goal)
        result.append(RoomAsset(
            scene_id, RoomGeometry(width, 200, 320, 200), image.pixels, image.palette,
            hotspots=tuple(hotspots), demo_walk_to_x=540 if not goal and not actors else None,
            use_rules=(UseRule(pickups[0].id, door_id, _text(puzzle.title), open_target=True,
                               requires_inventory=tuple(item.id for item in pickups[1:])),) if not goal else (),
            goal_text=_text(ordered_puzzles[-1].title) if goal else None,
            talk_rules=talk_rules,
        ))
    active_speakers = {actor for room in result for dialogue in room.talk_rules
                       for _line, actor in dialogue.actor_lines}
    if not active_speakers:
        return GameDocument(story.chapters[0].id + "Game", tuple(result))
    palette = [(0, 0, 0)] * 48
    palette[17] = (230, 80, 180)
    figure = CostumeAsset("DialogueFigure", tuple(palette),
                          (CostumeFrame("Pose", 8, 8, bytes([1] * 64), -4, -8),),
                          (CostumeAnimation("stand", tuple(
                              CostumeDirection(direction, ("Pose",))
                              for direction in ("N", "E", "S", "W"))),))
    speaker_actors = []
    for scene_id in route:
        characters = [char for char in story.characters if char.scene_id == scene_id]
        for index, character in enumerate(characters):
            actor_id = f"Speaker{character.id}"
            if actor_id in active_speakers:
                speaker_actors.append(ActorAsset(actor_id, figure.name, scene_id,
                                                 185 + index * 35, 110,
                                                 display_name=_text(character.name)))
    return GameDocument(story.chapters[0].id + "Game", tuple(result),
                        costumes=(figure,), actors=tuple(speaker_actors))
