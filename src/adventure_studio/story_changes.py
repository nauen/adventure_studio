"""Validated, all-or-nothing edits to the author's story model."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from .story import Chapter, Character, Item, Puzzle, Recipe, Scene, Story, consolidate_story, validate_story, verify_story


StoryEntity = Chapter | Scene | Character | Item | Puzzle | Recipe
EntityKind = Literal["chapter", "scene", "character", "item", "puzzle", "recipe"]

_COLLECTIONS: dict[str, tuple[str, type]] = {
    "chapter": ("chapters", Chapter),
    "scene": ("scenes", Scene),
    "character": ("characters", Character),
    "item": ("items", Item),
    "puzzle": ("puzzles", Puzzle),
    "recipe": ("recipes", Recipe),
}


@dataclass(frozen=True)
class PutEntity:
    kind: EntityKind
    entity: StoryEntity


@dataclass(frozen=True)
class DeleteEntity:
    kind: EntityKind
    id: str


@dataclass(frozen=True)
class StoryDiff:
    kind: EntityKind
    id: str
    before: StoryEntity | None
    after: StoryEntity | None


@dataclass(frozen=True)
class StoryChangeReport:
    changes: tuple[StoryDiff, ...]
    playable_path: tuple[str, ...]
    consolidated: tuple[str, ...] = ()


def edit_story(story: Story, operations: tuple[PutEntity | DeleteEntity, ...]) -> tuple[Story, StoryChangeReport]:
    """Apply a proposal to memory, then validate and solve before returning it.

    Deleting a referenced item/scene fails: the author/AI must explicitly repair
    affected narrative dependencies within the *same* proposal. This prevents
    surprising automatic story rewrites while preserving atomicity.
    """
    validate_story(story)
    collections = {kind: {entity.id: entity for entity in getattr(story, attr)}
                   for kind, (attr, _) in _COLLECTIONS.items()}
    touched = set()
    for op in operations:
        if op.kind not in _COLLECTIONS:
            raise ValueError(f"Unsupported kind: {op.kind}")
        _, cls = _COLLECTIONS[op.kind]
        id_ = op.entity.id if isinstance(op, PutEntity) else op.id
        key = (op.kind, id_)
        if not id_ or key in touched:
            raise ValueError(f"Empty ID or repeated operation: {key}")
        touched.add(key)
        if isinstance(op, PutEntity):
            if type(op.entity) is not cls:
                raise ValueError(f"Wrong entity type for {op.kind}")
            collections[op.kind][id_] = op.entity
        elif isinstance(op, DeleteEntity):
            if id_ not in collections[op.kind]:
                raise ValueError(f"Unknown {op.kind}: {id_}")
            del collections[op.kind][id_]
        else:
            raise TypeError(f"Unsupported story operation: {type(op).__name__}")
    candidate = replace(story, **{attr: tuple(collections[kind].values())
                                  for kind, (attr, _) in _COLLECTIONS.items()})
    candidate, removed = consolidate_story(candidate)
    collections["item"] = {item.id: item for item in candidate.items}
    playable_path = verify_story(candidate)
    diffs = []
    for kind, (attr, _) in _COLLECTIONS.items():
        before = {entity.id: entity for entity in getattr(story, attr)}
        after = collections[kind]
        for id_ in sorted(before.keys() | after.keys()):
            if before.get(id_) != after.get(id_):
                diffs.append(StoryDiff(kind, id_, before.get(id_), after.get(id_)))
    return candidate, StoryChangeReport(tuple(diffs), playable_path, removed)
