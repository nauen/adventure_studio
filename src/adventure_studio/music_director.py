"""Deterministic, declarative music direction for future SCUMM/iMUSE export.

This is intentionally not an iMUSE opcode emitter. iMUSE MIDI resources,
hooks and soundKludge semantics require independent ScummC/ScummVM tests.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")


@dataclass(frozen=True)
class MusicTrack:
    id: str
    asset_id: str


@dataclass(frozen=True)
class MusicTransition:
    """Select a track after a semantic story event.

    A target of None means silence. The engine-facing transition strategy is
    chosen later, after iMUSE hook support has been demonstrated in ScummVM.
    """

    event_id: str
    target_track_id: str | None
    mode: str = "immediate"


@dataclass(frozen=True)
class MusicPlan:
    tracks: tuple[MusicTrack, ...]
    transitions: tuple[MusicTransition, ...]
    initial_track_id: str | None = None


@dataclass(frozen=True)
class MusicCommand:
    """A backend-neutral command, never an unverified SCUMM opcode."""

    operation: str
    asset_id: str | None = None


@dataclass(frozen=True)
class MusicConsolidation:
    plan: MusicPlan
    removed_track_ids: tuple[str, ...]
    removed_asset_ids: tuple[str, ...]


def validate_music_plan(plan: MusicPlan) -> None:
    if len(plan.tracks) > 64 or len(plan.transitions) > 256:
        raise ValueError("Music plan exceeds bounded resource limits")
    tracks: set[str] = set()
    assets: set[str] = set()
    for track in plan.tracks:
        if not _ID.fullmatch(track.id) or not _ID.fullmatch(track.asset_id):
            raise ValueError("Invalid music track or asset ID")
        if track.id in tracks or track.asset_id in assets:
            raise ValueError("Duplicate music track or asset")
        tracks.add(track.id)
        assets.add(track.asset_id)
    if plan.initial_track_id is not None and plan.initial_track_id not in tracks:
        raise ValueError("Unknown initial music track")
    events: set[str] = set()
    for transition in plan.transitions:
        if not _ID.fullmatch(transition.event_id) or transition.event_id in events:
            raise ValueError("Invalid or ambiguous music event")
        if transition.target_track_id is not None and transition.target_track_id not in tracks:
            raise ValueError("Unknown transition target music track")
        if transition.mode not in ("immediate", "beat", "bar"):
            raise ValueError("Unsupported music transition mode")
        events.add(transition.event_id)


def resolve_music_event(plan: MusicPlan, current_track_id: str | None,
                        event_id: str) -> tuple[str | None, str]:
    """Resolve an event without side effects or generated executable scripts.

    Returns (next track, requested transition mode); actual iMUSE scheduling
    must not silently degrade beat/bar alignment to an immediate jump.
    """
    validate_music_plan(plan)
    if current_track_id is not None and current_track_id not in {t.id for t in plan.tracks}:
        raise ValueError("Unknown current music track")
    if not _ID.fullmatch(event_id):
        raise ValueError("Invalid music event ID")
    for transition in plan.transitions:
        if transition.event_id == event_id:
            return transition.target_track_id, transition.mode
    return current_track_id, "unchanged"


def orphan_music_tracks(plan: MusicPlan) -> tuple[str, ...]:
    """List unreferenced music tracks for consolidation, never delete blindly."""
    validate_music_plan(plan)
    used = {plan.initial_track_id} | {t.target_track_id for t in plan.transitions}
    return tuple(sorted(track.id for track in plan.tracks if track.id not in used))


def compile_immediate_music_event(plan: MusicPlan, current_track_id: str | None,
                                  event_id: str) -> tuple[str | None, MusicCommand | None]:
    """Lower supported events to explicit actions; reject unproven sync modes.

    This prepares a backend adapter without pretending to implement iMUSE's
    beat/bar synchronisation.  An unchanged track emits no redundant command.
    """
    target, mode = resolve_music_event(plan, current_track_id, event_id)
    if mode in ("beat", "bar") and target != current_track_id:
        raise ValueError(f"Music transition {event_id} needs unverified {mode} synchronisation")
    if target == current_track_id:
        return target, None
    if target is None:
        return None, MusicCommand("stop")
    track = next(track for track in plan.tracks if track.id == target)
    return target, MusicCommand("play", track.asset_id)


def consolidate_music_plan(plan: MusicPlan) -> MusicConsolidation:
    """Return a cleaned copy and an exact removal report; never mutate input."""
    dead = set(orphan_music_tracks(plan))
    removed = tuple(track for track in plan.tracks if track.id in dead)
    cleaned = MusicPlan(
        tracks=tuple(track for track in plan.tracks if track.id not in dead),
        transitions=plan.transitions,
        initial_track_id=plan.initial_track_id,
    )
    validate_music_plan(cleaned)
    return MusicConsolidation(cleaned, tuple(sorted(dead)),
                              tuple(sorted(track.asset_id for track in removed)))
