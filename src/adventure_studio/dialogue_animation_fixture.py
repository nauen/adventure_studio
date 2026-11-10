"""Native two-frame NPC speaking gesture built through Studio's authored cue path."""

from dataclasses import replace
from pathlib import Path
import sys

from .scumm_costume import CostumeAnimation, CostumeDirection, CostumeFrame
from .scumm_project import canonical_json, export_document, parse_document
from .studio_sequences import (dialogue_animation_lines, edit_dialogue_animation,
                               assign_dialogue_speaking_frame)


def build(directory: Path, two_poses: bool = False) -> None:
    project = directory / "project.json"
    document = parse_document(project.read_text(encoding="utf-8"))
    costume = next(item for item in document.costumes if item.name == "DialogueFigure")
    palette = list(costume.palette)
    palette[18] = (220, 80, 80)
    if two_poses:
        palette[19] = (35, 225, 35)
    gesture = CostumeAnimation("gesture", tuple(
        CostumeDirection(direction, ("Speak",), True)
        for direction in ("N", "E", "S", "W")), 24)
    talk_start = CostumeAnimation("talk_start", tuple(
        CostumeDirection(direction, ("Speak",), True)
        for direction in ("N", "E", "S", "W")), 16)
    talk_stop = CostumeAnimation("talk_stop", tuple(
        CostumeDirection(direction, ("Pose",), True)
        for direction in ("N", "E", "S", "W")), 20)
    additional = (CostumeFrame("SpeakAlt", 8, 8, bytes([3] * 64), -4, -8),) if two_poses else ()
    updated = replace(costume, palette=tuple(palette),
                      frames=(*costume.frames, CostumeFrame("Speak", 8, 8, bytes([2] * 64), -4, -8),
                              *additional),
                      animations=tuple(replace(animation, index=12)
                                       if animation.name == "stand" else animation
                                       for animation in costume.animations)
                                 + (talk_start, talk_stop, gesture))
    document = replace(document,
                       costumes=tuple(updated if item.name == costume.name else item
                                      for item in document.costumes),
                       # Keep NPC costumes away from the talk hotspot and
                       # from Ego, who walks onto that hotspot before speech.
                       actors=tuple(replace(actor, initial_animation="stand",
                                            x=280 if actor.id == "SpeakerWitness" else 135,
                                            y=100)
                                    if actor.costume == costume.name else actor
                                    for actor in document.actors))
    if two_poses:
        # The editor forbids mutating an asset shared by distinct actors.
        # Give the Witness its own real Costume before authoring two poses.
        document = replace(document,
            costumes=(*document.costumes, replace(updated, name="WitnessCostume")),
            actors=tuple(replace(actor, costume="WitnessCostume")
                         if actor.id == "SpeakerWitness" else actor
                         for actor in document.actors))
        # Two consecutive lines are spoken by the same native actor.
        rooms = tuple(replace(room,
            talk_rules=tuple(replace(rule, actor_lines=tuple(
                (key, "SpeakerWitness") for key, _actor in rule.actor_lines))
                for rule in room.talk_rules),
            hotspots=tuple(replace(hotspot, talk_actor_lines=tuple(
                "SpeakerWitness" for _actor in hotspot.talk_actor_lines))
                if hotspot.talk_actor_lines else hotspot for hotspot in room.hotspots))
            for room in document.rooms)
        document = replace(document, rooms=rooms)
    raw = canonical_json(document)
    if two_poses:
        lines = tuple(identity for label, identity in dialogue_animation_lines(raw)
                      if label.startswith("SpeakerWitness"))
        if len(lines) < 2:
            raise ValueError("Two-pose fixture needs two authored lines for one actor")
        raw = assign_dialogue_speaking_frame(raw, lines[0], "Speak", True)
        raw = assign_dialogue_speaking_frame(raw, lines[1], "SpeakAlt", True)
    else:
        line = next(identity for label, identity in dialogue_animation_lines(raw)
                    if label.startswith("SpeakerWitness"))
        raw = edit_dialogue_animation(raw, line, "gesture", True)
    project.write_text(raw, encoding="utf-8")
    export_document(parse_document(raw), directory / "resources")


def main() -> int:
    if len(sys.argv) not in (2, 3) or (len(sys.argv) == 3 and sys.argv[2] != "--two-poses"):
        print("Usage: python -m adventure_studio.dialogue_animation_fixture BUILD_DIRECTORY [--two-poses]")
        return 2
    build(Path(sys.argv[1]), two_poses=len(sys.argv) == 3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
