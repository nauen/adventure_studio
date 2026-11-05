"""Opt-in original MIDI fixture for the first SCUMM v6/iMUSE audio gate.

The MIDI file is generated with Python's standard library. ScummC's `soun`
tool must wrap it as a GMD resource before the project is compiled.
Normal story builds contain no music and remain bit-for-bit unchanged.
"""

from __future__ import annotations

import struct
import sys
from dataclasses import replace
from pathlib import Path

from .scumm_project import GameDocument, canonical_json, export_document
from .story_document import parse_story_document
from .story_to_scumm import compile_story_to_scumm


def _vlq(value: int) -> bytes:
    if type(value) is not int or value < 0 or value > 0x0FFFFFFF:
        raise ValueError("Invalid MIDI delta-time")
    data = [value & 0x7F]
    value >>= 7
    while value:
        data.insert(0, (value & 0x7F) | 0x80)
        value >>= 7
    return bytes(data)


def original_midi_theme() -> bytes:
    """Create a short 8-second single-track GM melody, no copyrighted samples."""
    track = bytearray()

    def event(delta: int, message: bytes) -> None:
        track.extend(_vlq(delta))
        track.extend(message)

    event(0, b"\xff\x51\x03\x07\xa1\x20")  # 120 BPM
    event(0, b"\xc0\x0a")  # GM Music Box (zero-based program 10)
    for note in (60, 64, 67, 72, 67, 64, 62, 60, 60, 64, 67, 72, 74, 72, 67, 64):
        event(0, bytes((0x90, note, 100)))
        event(480, bytes((0x80, note, 0)))
    event(0, b"\xff\x2f\x00")
    return b"MThd" + struct.pack(">IHHH", 6, 0, 1, 480) + b"MTrk" + struct.pack(">I", len(track)) + track


def add_music_entry(game: GameDocument) -> GameDocument:
    if not game.rooms or any(room.music_id == "HarborTheme" for room in game.rooms):
        raise ValueError("Fixture needs a new music resource")
    first = replace(game.rooms[0], music_id="HarborTheme")
    return replace(game, rooms=(first, *game.rooms[1:]))


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.music_demo STORY.json OUTPUT_DIRECTORY")
        return 2
    story = parse_story_document(Path(sys.argv[1]).read_text(encoding="utf-8"))
    game = add_music_entry(compile_story_to_scumm(story))
    directory = Path(sys.argv[2])
    resources = directory / "resources"
    export_document(game, resources)
    (resources / "HarborTheme.mid").write_bytes(original_midi_theme())
    (directory / "project.json").write_text(canonical_json(game), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
