"""Typed, declarative project changes and deterministic consolidation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Literal, TypeAlias

from .core import Action, Object, Project, analyze, validate


@dataclass(frozen=True)
class PutObject:
    object: Object
    type: Literal["put_object"] = "put_object"


@dataclass(frozen=True)
class DeleteObject:
    id: str
    type: Literal["delete_object"] = "delete_object"


@dataclass(frozen=True)
class PutAction:
    action: Action
    type: Literal["put_action"] = "put_action"


@dataclass(frozen=True)
class DeleteAction:
    id: str
    type: Literal["delete_action"] = "delete_action"


Operation: TypeAlias = PutObject | DeleteObject | PutAction | DeleteAction


@dataclass(frozen=True)
class Change:
    kind: Literal["object", "action", "state"]
    id: str
    before: object | None
    after: object | None
    reason: Literal["requested", "consolidated"]


@dataclass(frozen=True)
class ChangeReport:
    changes: tuple[Change, ...]
    winning_path: tuple[str, ...]
    explored_states: int
    safe_states: int


def _mapping(items: tuple[Object, ...] | tuple[Action, ...]) -> dict[str, Object] | dict[str, Action]:
    return {item.id: item for item in items}


def _diff(kind: Literal["object", "action", "state"], before: dict, after: dict,
          requested: set[tuple[str, str]]) -> list[Change]:
    changes = []
    for key in sorted(before.keys() | after.keys()):
        if before.get(key) != after.get(key):
            changes.append(Change(kind, key, before.get(key), after.get(key),
                                  "requested" if (kind, key) in requested else "consolidated"))
    return changes


def apply_changes(project: Project, operations: tuple[Operation, ...]) -> tuple[Project, ChangeReport]:
    """Compute a candidate without mutating input; accept only fully safe projects.

    Unknown and repeated operations are errors. An object deletion cascades only
    through state/action records owned by its namespace. The solver checks that
    this does not destroy the game's goals or create a softlock.
    """
    validate(project)
    objects: dict[str, Object] = _mapping(project.objects)  # type: ignore[assignment]
    actions: dict[str, Action] = _mapping(project.actions)  # type: ignore[assignment]
    state = dict(project.initial)
    requested: set[tuple[str, str]] = set()
    for op in operations:
        if isinstance(op, (PutObject, DeleteObject)):
            target = ("object", op.object.id if isinstance(op, PutObject) else op.id)
        elif isinstance(op, (PutAction, DeleteAction)):
            target = ("action", op.action.id if isinstance(op, PutAction) else op.id)
        else:
            raise TypeError(f"Unsupported operation: {type(op).__name__}")
        if target in requested:
            raise ValueError(f"Repeated operation: {target}")
        if isinstance(op, PutObject):
            if not op.object.id:
                raise ValueError("Empty object ID")
            objects[op.object.id] = op.object
        elif isinstance(op, DeleteObject):
            if op.id not in objects:
                raise ValueError(f"Unknown object: {op.id}")
            del objects[op.id]
        elif isinstance(op, PutAction):
            if not op.action.id:
                raise ValueError("Empty action ID")
            actions[op.action.id] = op.action
        elif isinstance(op, DeleteAction):
            if op.id not in actions:
                raise ValueError(f"Unknown action: {op.id}")
            del actions[op.id]
        requested.add(target)

    # A referenced object retains its containing object as well. This protects
    # optional cabinets/fridges holding required items without retaining junk.
    while True:
        referenced = {c.key.split(".", 1)[0] for c in project.goals}
        for action in actions.values():
            referenced.update(c.key.split(".", 1)[0] for c in action.requires)
            referenced.update(e.key.split(".", 1)[0] for e in action.effects)
        referenced.update(o.id for o in objects.values() if o.purpose != "optional")
        while True:
            parents = {objects[obj_id].location for obj_id in referenced if obj_id in objects}
            expanded = referenced | (parents & objects.keys())
            if expanded == referenced:
                break
            referenced = expanded
        orphan_ids = {o.id for o in objects.values() if o.purpose == "optional" and o.id not in referenced}
        if not orphan_ids:
            break
        for obj_id in orphan_ids:
            del objects[obj_id]

    removed_ids = set(_mapping(project.objects)) - set(objects)
    if removed_ids:
        state = {k: v for k, v in state.items() if k.split(".", 1)[0] not in removed_ids}
        actions = {k: a for k, a in actions.items()
                   if not any(c.key.split(".", 1)[0] in removed_ids for c in a.requires)
                   and not any(e.key.split(".", 1)[0] in removed_ids for e in a.effects)}

    candidate = replace(project, objects=tuple(objects.values()), actions=tuple(actions.values()),
                        initial=tuple(sorted(state.items())))
    result = analyze(candidate)
    if not result.solvable or result.dead_ends:
        raise ValueError(f"Unsafe change: solvable={result.solvable}, dead_end_states={result.dead_ends}")
    before_objects = _mapping(project.objects)
    before_actions = _mapping(project.actions)
    changes = (
        _diff("object", before_objects, objects, requested)
        + _diff("action", before_actions, actions, requested)
        + _diff("state", dict(project.initial), state, requested)
    )
    changes.sort(key=lambda c: (c.kind, c.id))
    return candidate, ChangeReport(tuple(changes), result.winning_path or (), result.explored_states,
                                   result.explored_states - result.dead_ends)


def report_dict(report: ChangeReport) -> dict:
    """Stable JSON-compatible report for a GUI or MCP tool."""
    return asdict(report)
