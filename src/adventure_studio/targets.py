"""Export target policy. No target is considered working without runtime tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Target:
    id: str
    format: Literal["scumm-v6"]
    runtime: Literal["scummvm", "dos"]
    baseline_width: int
    baseline_height: int
    validated: bool = False


SCUMMVM_TARGET = Target("scummvm-scumm6", "scumm-v6", "scummvm", 320, 200)
DOS_TARGET = Target("dos-scumm6", "scumm-v6", "dos", 320, 200)
DEFAULT_TARGET = SCUMMVM_TARGET


@dataclass(frozen=True)
class RoomGeometry:
    room_width: int
    room_height: int
    viewport_width: int
    viewport_height: int


def validate_geometry(room: RoomGeometry, target: Target = DEFAULT_TARGET) -> None:
    """Only engine-independent checks. SCUMM limits need empirical verification."""
    if any(type(value) is not int or value <= 0 for value in (
        room.room_width, room.room_height, room.viewport_width, room.viewport_height
    )):
        raise ValueError("All dimensions must be positive integers")
    if room.room_width < room.viewport_width or room.room_height < room.viewport_height:
        raise ValueError("Viewport cannot be larger than room")
    if room.viewport_width != target.baseline_width or room.viewport_height != target.baseline_height:
        raise ValueError("Viewport incompatible with selected SCUMM v6 baseline")


def export_ready(target: Target = DEFAULT_TARGET) -> None:
    """Fail closed until the real compiler and emulator integration is proven."""
    if not target.validated:
        raise RuntimeError(f"Export target {target.id} is not integration-tested")
