"""Native two-frame NPC speaking gesture built through Studio's authored cue path."""

from dataclasses import replace
from pathlib import Path
import sys

from .scumm_costume import CostumeAnimation, CostumeDirection, CostumeFrame
from .scumm_project import canonical_json, export_document, parse_document
from .studio_sequences import dialogue_animation_lines, edit_dialogue_animation


def build(directory: Path) -> None:
    project = directory / "project.json"
    document = parse_document(project.read_text(encoding="utf-8"))
    costume = next(item for item in document.costumes if item.name == "DialogueFigure")
    palette = list(costume.palette)
    palette[18] = (220, 80, 80)
    gesture = CostumeAnimation("gesture", tuple(
        CostumeDirection(direction, ("Pose", "Speak"), True)
        for direction in ("N", "E", "S", "W")), 24)
    updated = replace(costume, palette=tuple(palette),
                      frames=(*costume.frames, CostumeFrame("Speak", 8, 8, bytes([2] * 64), -4, -8)),
                      animations=tuple(replace(animation, index=20)
                                       if animation.name == "stand" else animation
                                       for animation in costume.animations) + (gesture,))
    document = replace(document, costumes=tuple(
        updated if item.name == costume.name else item for item in document.costumes))
    raw = canonical_json(document)
    line = next(identity for label, identity in dialogue_animation_lines(raw)
                if label.startswith("SpeakerWitness"))
    raw = edit_dialogue_animation(raw, line, "gesture")
    project.write_text(raw, encoding="utf-8")
    export_document(parse_document(raw), directory / "resources")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m adventure_studio.dialogue_animation_fixture BUILD_DIRECTORY")
        return 2
    build(Path(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
