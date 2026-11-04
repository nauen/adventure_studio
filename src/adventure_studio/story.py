"""Author-facing story bible and deterministic story-to-game compilation.

The story model contains no executable scripts, coordinates or engine-specific
assets. It can be proposed by a language model and validated without trusting it.
"""

from __future__ import annotations

from dataclasses import dataclass

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
class Story:
    chapters: tuple[Chapter, ...]
    scenes: tuple[Scene, ...]
    characters: tuple[Character, ...]
    items: tuple[Item, ...]
    puzzles: tuple[Puzzle, ...]
    starting_scene_id: str
    final_puzzle_id: str


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
        if item.role not in ("pickup", "decoration"):
            raise ValueError(f"Unknown item role: {item.role}")
    for puzzle in story.puzzles:
        if puzzle.scene_id not in scenes:
            raise ValueError(f"Unknown puzzle scene: {puzzle.scene_id}")
        if puzzle.opens_scene_id is not None and puzzle.opens_scene_id not in scenes:
            raise ValueError(f"Unknown unlocked scene: {puzzle.opens_scene_id}")
        if len(set(puzzle.requires)) != len(puzzle.requires):
            raise ValueError(f"Duplicate requirements: {puzzle.id}")
        for item_id in puzzle.requires:
            if item_id not in items or items[item_id].role != "pickup":
                raise ValueError(f"Missing pickup requirement: {item_id}")


def compile_story(story: Story) -> Project:
    """Compile a small, deterministic puzzle subset into the generic engine.

    Scene access is a Boolean precondition. Visual layout, dialogues and
    animation are intentionally outside this compiler stage.
    """
    validate_story(story)
    state: dict[str, bool] = {f"scene.{s.id}": s.id == story.starting_scene_id for s in story.scenes}
    state.update({f"item.{i.id}": False for i in story.items if i.role == "pickup"})
    state.update({f"puzzle.{p.id}": False for p in story.puzzles})
    actions = []
    for item in story.items:
        if item.role == "pickup":
            actions.append(Action(f"take:{item.id}", f"Nimm {item.name}",
                                  (Condition(f"scene.{item.scene_id}"), Condition(f"item.{item.id}", False)),
                                  (Effect(f"item.{item.id}", True),)))
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
