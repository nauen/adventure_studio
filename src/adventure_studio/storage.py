"""Atomic, optimistic-concurrency project storage (JSON, no executable code)."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from .core import Action, Condition, Effect, Object, Project, validate


def to_bytes(project: Project) -> bytes:
    validate(project)
    return (json.dumps(asdict(project), ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def from_bytes(raw: bytes) -> Project:
    data = json.loads(raw)
    if set(data) != {"objects", "actions", "initial", "goals"}:
        raise ValueError("Unexpected project fields")
    objects = tuple(Object(**o) for o in data["objects"])
    actions = tuple(Action(a["id"], a["name"],
                           tuple(Condition(**c) for c in a["requires"]),
                           tuple(Effect(**e) for e in a["effects"])) for a in data["actions"])
    initial = tuple((k, v) for k, v in data["initial"])
    if any(type(v) is not bool for _, v in initial):
        raise ValueError("State values must be Boolean")
    goals = tuple(Condition(**g) for g in data["goals"])
    project = Project(objects, actions, initial, goals)
    validate(project)
    return project


def fingerprint(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load(path: Path) -> tuple[Project, str]:
    raw = path.read_bytes()
    return from_bytes(raw), fingerprint(raw)


def save(path: Path, project: Project, expected_revision: str | None) -> str:
    """Atomic replace after revision check; caller serializes writers per project.

    This is not a multi-process locking mechanism. The future repository layer
    must serialize concurrent writes before the compare-and-swap check.
    """
    raw = to_bytes(project)
    if path.exists():
        if expected_revision is None or fingerprint(path.read_bytes()) != expected_revision:
            raise ValueError("Project revision conflict")
    elif expected_revision is not None:
        raise ValueError("Project revision conflict")
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=".project-",
                                         suffix=".tmp", delete=False) as stream:
            name = stream.name
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        name = None
    finally:
        if name is not None:
            os.unlink(name)
    return fingerprint(raw)
