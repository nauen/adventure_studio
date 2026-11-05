"""Opt-in two-theme room-transition experiment for stock SCUMM v6.

Entering the cellar after using the key causes a room entry event and starts
the second original MIDI theme. This is an immediate switch, not beat sync.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

from .music_demo import original_midi_theme
from .scumm_project import GameDocument, canonical_json, export_document
from .story_document import parse_story_document
from .story_to_scumm import compile_story_to_scumm


TRACKS = (("HarborTheme", 0), ("CellarTheme", -5))


def add_room_music_switch(game: GameDocument) -> GameDocument:
    if len(game.rooms) < 2:
        raise ValueError("Music transition fixture needs two rooms")
    if any(room.music_id is not None for room in game.rooms):
        raise ValueError("Music transition fixture must not overwrite existing music")
    rooms = list(game.rooms)
    for index, (track_id, _) in enumerate(TRACKS):
        rooms[index] = replace(rooms[index], music_id=track_id)
    return replace(game, rooms=tuple(rooms))


def build(story_path: Path, directory: Path) -> GameDocument:
    story = parse_story_document(story_path.read_text(encoding="utf-8"))
    game = add_room_music_switch(compile_story_to_scumm(story))
    resources = directory / "resources"
    export_document(game, resources)
    for track_id, transpose in TRACKS:
        (resources / f"{track_id}.mid").write_bytes(original_midi_theme(transpose))
    (directory / "project.json").write_text(canonical_json(game), encoding="utf-8")
    return game


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.music_transition_demo STORY.json OUTPUT_DIRECTORY")
        return 2
    build(Path(sys.argv[1]), Path(sys.argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
