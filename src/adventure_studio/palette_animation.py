"""Pure, deterministic palette-cycle model and preview transformation.

This module is not yet SCUMM runtime emission.  A separate integration test
must verify the equivalent cycle behavior in real ScummVM before enabling it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PaletteCycle:
    name: str
    first: int
    last: int
    period_ticks: int
    reverse: bool = False


def validate_cycles(
    palette: tuple[tuple[int, int, int], ...],
    cycles: tuple[PaletteCycle, ...],
    protected_indices: frozenset[int] = frozenset(),
) -> None:
    """Reject ambiguous cycles, protected colors and invalid timing."""
    if not 1 <= len(palette) <= 256:
        raise ValueError("Palette size must be 1..256")
    if len(cycles) > 16:
        raise ValueError("Too many palette cycles")
    if any(type(i) is not int or not 0 <= i < len(palette) for i in protected_indices):
        raise ValueError("Invalid protected palette index")
    used: set[int] = set()
    names: set[str] = set()
    for cycle in cycles:
        if (not cycle.name or cycle.name in names or
                any(type(i) is not int for i in (cycle.first, cycle.last, cycle.period_ticks)) or
                type(cycle.reverse) is not bool or
                not 0 <= cycle.first < cycle.last < len(palette) or
                not 1 <= cycle.period_ticks <= 65535):
            raise ValueError("Invalid palette cycle")
        indices = set(range(cycle.first, cycle.last + 1))
        if used & indices or protected_indices & indices:
            raise ValueError("Overlapping or protected palette cycle")
        used.update(indices)
        names.add(cycle.name)


def palette_at_tick(
    palette: tuple[tuple[int, int, int], ...],
    cycles: tuple[PaletteCycle, ...],
    tick: int,
    protected_indices: frozenset[int] = frozenset(),
) -> tuple[tuple[int, int, int], ...]:
    """Preview each independent cycle from the *original* palette at tick."""
    if type(tick) is not int or tick < 0:
        raise ValueError("Tick must be a non-negative integer")
    validate_cycles(palette, cycles, protected_indices)
    result = list(palette)
    for cycle in cycles:
        ramp = palette[cycle.first:cycle.last + 1]
        steps = (tick // cycle.period_ticks) % len(ramp)
        if cycle.reverse:
            steps = -steps
        for offset, color in enumerate(ramp):
            result[cycle.first + (offset + steps) % len(ramp)] = color
    return tuple(result)
