"""Author-facing story bible and deterministic story-to-game compilation.

The story model contains no executable scripts or engine-specific assets.
Optional versioned placements are semantic authoring data, validated before
the SCUMM exporter converts them into room coordinates.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import re

from .core import Action, Condition, Effect, Object, Project, analyze


@dataclass(frozen=True)
class Chapter:
    id: str
    title: str
    synopsis: str


@dataclass(frozen=True)
class Scene:
    id: str
    chapter_id: str
    title: str
    description: str


@dataclass(frozen=True)
class Character:
    id: str
    name: str
    description: str
    scene_id: str


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    description: str
    scene_id: str
    # Decor items are deliberately retained story content, not solver pickups.
    role: str = "pickup"


@dataclass(frozen=True)
class Puzzle:
    id: str
    title: str
    scene_id: str
    requires: tuple[str, ...]
    opens_scene_id: str | None = None


@dataclass(frozen=True)
class Recipe:
    id: str
    title: str
    ingredients: tuple[str, str]
    result_item_id: str


@dataclass(frozen=True)
class Placement:
    item_id: str
    x: int
    y: int

    @property
    def id(self) -> str:
        return self.item_id


@dataclass(frozen=True)
class Dialogue:
    id: str
    scene_id: str
    entry_node_id: str


@dataclass(frozen=True)
class DialogueNode:
    id: str
    dialogue_id: str
    speaker_id: str
    text: str
    next_node_id: str | None = None
    face_direction: str | None = None


@dataclass(frozen=True)
class DialogueChoice:
    id: str
    node_id: str
    text: str
    next_node_id: str | None = None


@dataclass(frozen=True)
class AssetRef:
    id: str
    target_kind: str
    target_id: str
    asset_kind: str
    source_id: str
    digest: str


@dataclass(frozen=True)
class Story:
    chapters: tuple[Chapter, ...]
    scenes: tuple[Scene, ...]
    characters: tuple[Character, ...]
    items: tuple[Item, ...]
    puzzles: tuple[Puzzle, ...]
    starting_scene_id: str
    final_puzzle_id: str
    recipes: tuple[Recipe, ...] = ()
    placements: tuple[Placement, ...] = ()
    dialogues: tuple[Dialogue, ...] = ()
    dialogue_nodes: tuple[DialogueNode, ...] = ()
    dialogue_choices: tuple[DialogueChoice, ...] = ()
    assets: tuple[AssetRef, ...] = ()


def _indexed(items: tuple) -> dict:
    ids = [item.id for item in items]
    if any(not id_ for id_ in ids) or len(set(ids)) != len(ids):
        raise ValueError("Empty or duplicated story ID")
    return {item.id: item for item in items}


def validate_story(story: Story) -> None:
    chapters = _indexed(story.chapters)
    scenes = _indexed(story.scenes)
    _indexed(story.characters)
    items = _indexed(story.items)
    puzzles = _indexed(story.puzzles)
    recipes = _indexed(story.recipes)
    placements = _indexed(story.placements)
    dialogues = _indexed(story.dialogues)
    dialogue_nodes = _indexed(story.dialogue_nodes)
    dialogue_choices = _indexed(story.dialogue_choices)
    assets = _indexed(story.assets)
    if story.starting_scene_id not in scenes:
        raise ValueError("Missing starting scene")
    if story.final_puzzle_id not in puzzles:
        raise ValueError("Missing final puzzle")
    for scene in story.scenes:
        if scene.chapter_id not in chapters:
            raise ValueError(f"Unknown chapter: {scene.chapter_id}")
    for actor in story.characters:
        if actor.scene_id not in scenes:
            raise ValueError(f"Unknown character scene: {actor.scene_id}")
    for item in story.items:
        if item.scene_id not in scenes:
            raise ValueError(f"Unknown item scene: {item.scene_id}")
        if item.role not in ("pickup", "decoration", "crafted"):
            raise ValueError(f"Unknown item role: {item.role}")
    for placement in placements.values():
        if placement.item_id not in items or items[placement.item_id].role == "crafted":
            raise ValueError(f"Placement needs a physical item: {placement.item_id}")
        # Story coordinates are authored in world/room space. The current
        # fixture's 640x200 raster and 16px hotspot are export constraints,
        # not limits on the authoring model.
        if (type(placement.x) is not int or type(placement.y) is not int
                or placement.x < 0 or placement.y < 0):
            raise ValueError(f"Placement needs non-negative integer coordinates: {placement.item_id}")
    for puzzle in story.puzzles:
        if puzzle.scene_id not in scenes:
            raise ValueError(f"Unknown puzzle scene: {puzzle.scene_id}")
        if puzzle.opens_scene_id is not None and puzzle.opens_scene_id not in scenes:
            raise ValueError(f"Unknown unlocked scene: {puzzle.opens_scene_id}")
        if len(set(puzzle.requires)) != len(puzzle.requires):
            raise ValueError(f"Duplicate requirements: {puzzle.id}")
        for item_id in puzzle.requires:
            if item_id not in items or items[item_id].role not in ("pickup", "crafted"):
                raise ValueError(f"Missing pickup requirement: {item_id}")
    produced = set()
    for recipe in recipes.values():
        if len(recipe.ingredients) != 2 or len(set(recipe.ingredients)) != 2:
            raise ValueError(f"Recipe needs two distinct ingredients: {recipe.id}")
        if recipe.result_item_id not in items or items[recipe.result_item_id].role != "crafted":
            raise ValueError(f"Recipe result must be a crafted item: {recipe.result_item_id}")
        if recipe.result_item_id in produced or recipe.result_item_id in recipe.ingredients:
            raise ValueError(f"Duplicate or self-referential recipe result: {recipe.id}")
        produced.add(recipe.result_item_id)
        for ingredient in recipe.ingredients:
            if ingredient not in items or items[ingredient].role == "decoration":
                raise ValueError(f"Unknown or non-inventory recipe ingredient: {ingredient}")
    crafted = {item.id for item in items.values() if item.role == "crafted"}
    if crafted != produced:
        raise ValueError(f"Every crafted item needs exactly one producing recipe: {sorted(crafted ^ produced)}")
    used = {item_id for puzzle in puzzles.values() for item_id in puzzle.requires}
    used.update(ingredient for recipe in recipes.values() for ingredient in recipe.ingredients)
    if produced - used:
        raise ValueError(f"Unused crafted item: {sorted(produced - used)}")

    characters = {c.id: c for c in story.characters}
    for dialogue in dialogues.values():
        if dialogue.scene_id not in scenes:
            raise ValueError(f"Unknown dialogue scene: {dialogue.id}")
        if dialogue.entry_node_id not in dialogue_nodes:
            raise ValueError(f"Unknown dialogue entry: {dialogue.id}")
    for node in dialogue_nodes.values():
        dialogue = dialogues.get(node.dialogue_id)
        if dialogue is None:
            raise ValueError(f"Unknown dialogue for node: {node.id}")
        speaker = characters.get(node.speaker_id)
        if speaker is None or speaker.scene_id != dialogue.scene_id:
            raise ValueError(f"Invalid dialogue speaker: {node.id}")
        if node.face_direction is not None and node.face_direction not in ("N", "E", "S", "W"):
            raise ValueError(f"Invalid dialogue facing direction: {node.id}")
        if node.next_node_id is not None and (node.next_node_id not in dialogue_nodes
                or dialogue_nodes[node.next_node_id].dialogue_id != node.dialogue_id):
            raise ValueError(f"Unknown dialogue successor: {node.id}")
    by_node: dict[str, list[DialogueChoice]] = {}
    for choice in dialogue_choices.values():
        parent = dialogue_nodes.get(choice.node_id)
        if parent is None:
            raise ValueError(f"Unknown dialogue choice node: {choice.id}")
        if choice.next_node_id is not None and (choice.next_node_id not in dialogue_nodes
                or dialogue_nodes[choice.next_node_id].dialogue_id != parent.dialogue_id):
            raise ValueError(f"Invalid dialogue choice target: {choice.id}")
        by_node.setdefault(choice.node_id, []).append(choice)
    for node in dialogue_nodes.values():
        if node.next_node_id is not None and node.id in by_node:
            raise ValueError(f"Dialogue node cannot have both automatic next and choices: {node.id}")
    for dialogue in dialogues.values():
        if dialogue_nodes[dialogue.entry_node_id].dialogue_id != dialogue.id:
            raise ValueError(f"Dialogue entry belongs to another dialogue: {dialogue.id}")
        group = {node.id for node in dialogue_nodes.values() if node.dialogue_id == dialogue.id}
        outgoing = {id_: (([dialogue_nodes[id_].next_node_id]
                            if dialogue_nodes[id_].next_node_id is not None else
                            [choice.next_node_id for choice in by_node.get(id_, [])]))
                    for id_ in group}
        reachable = {dialogue.entry_node_id}
        frontier = [dialogue.entry_node_id]
        while frontier:
            for target in outgoing[frontier.pop()]:
                if target is not None and target not in reachable:
                    reachable.add(target)
                    frontier.append(target)
        if reachable != group:
            raise ValueError(f"Unreachable dialogue nodes: {dialogue.id}")
        endings = {id_ for id_, transitions in outgoing.items() if not transitions or None in transitions}
        can_end = set(endings)
        while True:
            extra = {id_ for id_, transitions in outgoing.items() if any(t in can_end for t in transitions)}
            if extra <= can_end:
                break
            can_end.update(extra)
        if can_end != group:
            raise ValueError(f"Dialogue dead end: {dialogue.id}")

    asset_targets = {"scene": scenes, "character": characters, "item": items,
                     "dialogue_node": dialogue_nodes}
    asset_kinds = {"scene": {"background"},
                   "character": {"portrait", "walk_sprite"},
                   "item": {"object_sprite"},
                   "dialogue_node": {"voice"}}
    slots = set()
    for asset in assets.values():
        if (asset.target_kind not in asset_targets
                or asset.target_id not in asset_targets[asset.target_kind]
                or asset.asset_kind not in asset_kinds[asset.target_kind]):
            raise ValueError(f"Invalid asset target or role: {asset.id}")
        slot = (asset.target_kind, asset.target_id, asset.asset_kind)
        if slot in slots:
            raise ValueError(f"Duplicate asset assignment: {slot}")
        slots.add(slot)
        if not re.fullmatch(r"[0-9a-f]{64}", asset.digest):
            raise ValueError(f"Invalid asset digest: {asset.id}")


def compile_story(story: Story) -> Project:
    """Compile a small, deterministic puzzle subset into the generic engine.

    Scene access is a Boolean precondition. Visual layout, dialogues and
    animation are intentionally outside this compiler stage.
    """
    validate_story(story)
    state: dict[str, bool] = {f"scene.{s.id}": s.id == story.starting_scene_id for s in story.scenes}
    state.update({f"item.{i.id}": False for i in story.items if i.role in ("pickup", "crafted")})
    state.update({f"picked.{i.id}": False for i in story.items if i.role == "pickup"})
    state.update({f"puzzle.{p.id}": False for p in story.puzzles})
    state.update({f"recipe.{r.id}": False for r in story.recipes})
    actions = []
    for item in story.items:
        if item.role == "pickup":
            actions.append(Action(f"take:{item.id}", f"Nimm {item.name}",
                                  (Condition(f"scene.{item.scene_id}"), Condition(f"picked.{item.id}", False)),
                                  (Effect(f"item.{item.id}", True), Effect(f"picked.{item.id}", True))))
    for recipe in story.recipes:
        actions.append(Action(f"combine:{recipe.id}", recipe.title,
                              (Condition(f"item.{recipe.ingredients[0]}"),
                               Condition(f"item.{recipe.ingredients[1]}"),
                               Condition(f"recipe.{recipe.id}", False)),
                              (Effect(f"item.{recipe.ingredients[0]}", False),
                               Effect(f"item.{recipe.ingredients[1]}", False),
                               Effect(f"item.{recipe.result_item_id}", True),
                               Effect(f"recipe.{recipe.id}", True))))
    for puzzle in story.puzzles:
        effects = [Effect(f"puzzle.{puzzle.id}", True)]
        if puzzle.opens_scene_id is not None:
            effects.append(Effect(f"scene.{puzzle.opens_scene_id}", True))
        actions.append(Action(f"solve:{puzzle.id}", puzzle.title,
                              (Condition(f"scene.{puzzle.scene_id}"), Condition(f"puzzle.{puzzle.id}", False),
                               *(Condition(f"item.{item_id}") for item_id in puzzle.requires)),
                              tuple(effects)))
    objects = tuple(Object(i.id, i.name, i.scene_id,
                           "decoration" if i.role == "decoration" else "required") for i in story.items)
    return Project(objects, tuple(actions), tuple(sorted(state.items())),
                   (Condition(f"puzzle.{story.final_puzzle_id}"),))


def verify_story(story: Story) -> tuple[str, ...]:
    """Reject unreachable goals and all reachable softlocks."""
    result = analyze(compile_story(story))
    if not result.solvable or result.dead_ends:
        raise ValueError(f"Unplayable story: solvable={result.solvable}, dead_ends={result.dead_ends}")
    return result.winning_path or ()


def consolidate_story(story: Story) -> tuple[Story, tuple[str, ...]]:
    """Prune unused mechanical pickups; keep authored decorative details.

    This is explicit and deterministic, never performed during plain parsing.
    In the current bounded model a pickup not referenced by any puzzle or
    recipe cannot affect gameplay; intentional flavor belongs to decoration.
    """
    validate_story(story)
    required = {item for puzzle in story.puzzles for item in puzzle.requires}
    required.update(item for recipe in story.recipes for item in recipe.ingredients)
    removed = tuple(sorted(item.id for item in story.items
                           if item.role == "pickup" and item.id not in required))
    return replace(story,
                   items=tuple(item for item in story.items if item.id not in removed),
                   placements=tuple(p for p in story.placements if p.item_id not in removed),
                   assets=tuple(a for a in story.assets if not (
                       a.target_kind == "item" and a.target_id in removed))), removed
