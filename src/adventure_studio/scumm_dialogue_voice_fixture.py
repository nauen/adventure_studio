"""Attach real authored VOC recordings to a branching Story dialogue fixture."""

from __future__ import annotations

import sys
from pathlib import Path

from .scumm_project import parse_document, export_document
from .scumm_voc_fixture import original_voc_effect
from .studio_sequences import (dialogue_voice_lines, edit_dialogue_voice,
                               import_room_sound)


def prepare(build: Path) -> None:
    path = build / "project.json"
    raw = path.read_text(encoding="utf-8")
    resource = build / "resources"
    for identity, frequency in (("KeeperEnglish", 440), ("KeeperGerman", 330)):
        voc = resource / f"{identity}.voc"
        voc.write_bytes(original_voc_effect(frequency=frequency, duration_ms=5000))
        raw = import_room_sound(raw, "Harbor", identity, str(voc))
    lines = dialogue_voice_lines(raw)
    opening = next(identifier for _label, identifier in lines if ".opening." in identifier)
    reply = next(identifier for _label, identifier in lines if ".reply." in identifier)
    raw = edit_dialogue_voice(raw, opening, "en", "KeeperEnglish")
    raw = edit_dialogue_voice(raw, opening, "de", "KeeperGerman")
    raw = edit_dialogue_voice(raw, reply, "en", "KeeperEnglish")
    raw = edit_dialogue_voice(raw, reply, "de", "KeeperGerman")
    path.write_text(raw, encoding="utf-8")
    export_document(parse_document(raw), resource)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m adventure_studio.scumm_dialogue_voice_fixture BUILD_DIRECTORY")
    prepare(Path(sys.argv[1]))
