"""Pure, deterministic game-state transitions and finite-state exploration."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from typing import Literal


@dataclass(frozen=True)
class Object:
    id: str
    name: str
    location: str
    purpose: Literal["required", "optional", "decoration"] = "optional"


@dataclass(frozen=True)
class Condition:
    key: str
    equals: bool = True


@dataclass(frozen=True)
class Effect:
    key: str
    value: bool


@dataclass(frozen=True)
class Action:
    id: str
    name: str
    requires: tuple[Condition, ...]
    effects: tuple[Effect, ...]


@dataclass(frozen=True)
class Project:
    objects: tuple[Object, ...]
    actions: tuple[Action, ...]
    initial: tuple[tuple[str, bool], ...]
    goals: tuple[Condition, ...]


@dataclass(frozen=True)
class Analysis:
    solvable: bool
    winning_path: tuple[str, ...] | None
    explored_states: int
    dead_ends: int


def _state_tuple(values: dict[str, bool]) -> tuple[tuple[str, bool], ...]:
    return tuple(sorted(values.items()))


def validate(project: Project) -> None:
    object_ids = [obj.id for obj in project.objects]
    action_ids = [action.id for action in project.actions]
    if len(object_ids) != len(set(object_ids)) or len(action_ids) != len(set(action_ids)):
        raise ValueError("Duplicate object or action ID")
    state = dict(project.initial)
    if len(state) != len(project.initial):
        raise ValueError("Duplicate state key")
    keys = set(state)
    for condition in (*project.goals, *(c for a in project.actions for c in a.requires)):
        if condition.key not in keys:
            raise ValueError(f"Unknown state key: {condition.key}")
    for action in project.actions:
        if len({effect.key for effect in action.effects}) != len(action.effects):
            raise ValueError(f"Conflicting effects in action: {action.id}")
        for effect in action.effects:
            if effect.key not in keys:
                raise ValueError(f"Unknown state key: {effect.key}")


def _matches(state: dict[str, bool], conditions: tuple[Condition, ...]) -> bool:
    return all(state[c.key] == c.equals for c in conditions)


def execute(project: Project, state: tuple[tuple[str, bool], ...], action_id: str) -> tuple[tuple[str, bool], ...]:
    action = next((a for a in project.actions if a.id == action_id), None)
    if action is None:
        raise ValueError(f"Unknown action: {action_id}")
    values = dict(state)
    if not _matches(values, action.requires):
        raise ValueError(f"Action unavailable: {action_id}")
    for effect in action.effects:
        values[effect.key] = effect.value
    return _state_tuple(values)


def analyze(project: Project, max_states: int = 100_000) -> Analysis:
    validate(project)
    start = _state_tuple(dict(project.initial))
    queue = deque([(start, ())])
    visited = {start}
    first_win: tuple[str, ...] | None = None
    edges: dict[tuple[tuple[str, bool], ...], set[tuple[tuple[str, bool], ...]]] = {}
    wins: set[tuple[tuple[str, bool], ...]] = set()
    while queue:
        state, path = queue.popleft()
        values = dict(state)
        if _matches(values, project.goals):
            wins.add(state)
            if first_win is None:
                first_win = path
            continue
        neighbors = []
        for action in project.actions:
            if _matches(values, action.requires):
                result = execute(project, state, action.id)
                if result != state:
                    neighbors.append((result, path + (action.id,)))
        edges[state] = {next_state for next_state, _ in neighbors}
        for next_state, next_path in neighbors:
            if next_state not in visited:
                visited.add(next_state)
                if len(visited) > max_states:
                    raise RuntimeError("State limit reached; analysis incomplete")
                queue.append((next_state, next_path))
    reverse: dict[tuple[tuple[str, bool], ...], set[tuple[tuple[str, bool], ...]]] = {}
    for source, targets in edges.items():
        for target in targets:
            reverse.setdefault(target, set()).add(source)
    can_win = set(wins)
    frontier = deque(wins)
    while frontier:
        for predecessor in reverse.get(frontier.popleft(), ()):
            if predecessor not in can_win:
                can_win.add(predecessor)
                frontier.append(predecessor)
    return Analysis(first_win is not None, first_win, len(visited), len(visited - can_win))


def consolidate(project: Project) -> tuple[Project, tuple[str, ...]]:
    """Remove unreferenced optional objects; preserve explicitly retained content."""
    referenced = {key.split(".", 1)[0] for key, _ in project.initial}
    referenced.update(c.key.split(".", 1)[0] for c in project.goals)
    for action in project.actions:
        referenced.update(c.key.split(".", 1)[0] for c in action.requires)
        referenced.update(e.key.split(".", 1)[0] for e in action.effects)
    removed = tuple(obj.id for obj in project.objects if obj.purpose == "optional" and obj.id not in referenced)
    result = replace(project, objects=tuple(obj for obj in project.objects if obj.id not in removed))
    return result, removed


def propose(project: Project, candidate: Project) -> tuple[Project, dict[str, object]]:
    """Return a validated candidate and change report; never mutate the original."""
    validate(project)
    consolidated, removed = consolidate(candidate)
    analysis = analyze(consolidated)
    if not analysis.solvable or analysis.dead_ends:
        raise ValueError(f"Invalid proposal: solvable={analysis.solvable}, dead_ends={analysis.dead_ends}")
    old = {obj.id: obj for obj in project.objects}
    new = {obj.id: obj for obj in consolidated.objects}
    report = {
        "added": sorted(new.keys() - old.keys()),
        "removed": sorted(old.keys() - new.keys()),
        "modified": sorted(k for k in old.keys() & new.keys() if old[k] != new[k]),
        "consolidated": list(removed),
        "winning_path": list(analysis.winning_path or ()),
        "explored_states": analysis.explored_states,
    }
    return consolidated, report
