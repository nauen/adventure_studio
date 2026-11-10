"""Native two-frame NPC speaking gesture built through Studio's authored cue path."""

from dataclasses import replace
from pathlib import Path
import sys

from .scumm_costume import CostumeAnimation, CostumeDirection, CostumeFrame
from .scumm_project import canonical_json, export_document, parse_document
from .studio_sequences import (dialogue_animation_lines, edit_dialogue_animation,
                               assign_dialogue_speaking_frame,
                               assign_dialogue_speaking_sequence,
                               assign_dialogue_direction_speaking_sequence,
                               edit_dialogue_animation_phases,
                               assign_dialogue_ending_sequence)
from .studio_actors import (set_costume_direction_speaking_pose,
                            set_costume_direction_speaking_sequence)


def build(directory: Path, two_poses: bool = False, four_facing: bool = False,
          animated: bool = False, line_sequences: bool = False,
          line_directions: bool = False) -> None:
    project = directory / "project.json"
    document = parse_document(project.read_text(encoding="utf-8"))
    costume = next(item for item in document.costumes if item.name == "DialogueFigure")
    palette = list(costume.palette)
    palette[18] = (220, 80, 80)
    if two_poses or four_facing or animated or line_sequences or line_directions:
        palette[19] = (35, 225, 35)
    if four_facing or line_sequences or line_directions:
        palette[20] = (70, 70, 230)
        palette[21] = (240, 220, 30)
    if line_directions:
        palette[22] = (200, 45, 205)
    gesture = CostumeAnimation("gesture", tuple(
        CostumeDirection(direction, ("Speak",), True)
        for direction in ("N", "E", "S", "W")), 24)
    talk_start = CostumeAnimation("talk_start", tuple(
        CostumeDirection(direction, ("Speak",), True)
        for direction in ("N", "E", "S", "W")), 16)
    talk_stop = CostumeAnimation("talk_stop", tuple(
        CostumeDirection(direction, ("Pose",), True)
        for direction in ("N", "E", "S", "W")), 20)
    additional = ((CostumeFrame("SpeakAlt", 8, 8, bytes([3] * 64), -4, -8),)
                  if two_poses or four_facing or animated or line_sequences or line_directions else ())
    if four_facing or line_sequences or line_directions:
        additional += (CostumeFrame("SpeakBlue", 8, 8, bytes([4] * 64), -4, -8),
                       CostumeFrame("SpeakYellow", 8, 8, bytes([5] * 64), -4, -8))
    if line_directions:
        additional += (CostumeFrame("SpeakMagenta", 8, 8, bytes([6] * 64), -4, -8),)
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
    if two_poses or four_facing or animated or line_sequences or line_directions:
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
    if line_directions:
        lines = tuple(identity for label, identity in dialogue_animation_lines(raw)
                      if label.startswith("SpeakerWitness"))
        if len(lines) < 2:
            raise ValueError("Directional speaking lines require two native lines")
        # The authored linear story faces the first speaker West, the second
        # East. Other directions intentionally remain on the old red pose.
        raw = assign_dialogue_direction_speaking_sequence(
            raw, lines[0], "W", "Speak, SpeakAlt")
        raw = assign_dialogue_direction_speaking_sequence(
            raw, lines[1], "E", "SpeakBlue, SpeakYellow")
        # Exercise authored native script phases in the same playable game:
        # the first line waits 12 ticks before its W gesture and at least 90
        # ticks after starting it; the second retains legacy 1/60 ticks.
        raw = edit_dialogue_animation_phases(raw, lines[0], 12, 90)
        # The very same direct PNG ending-authoring function as the Studio UI
        # must produce the magenta native gameplay frame, not a hand-built slot.
        raw = assign_dialogue_ending_sequence(raw, lines[0], "W", "SpeakMagenta", 45)
    elif line_sequences:
        lines = tuple(identity for label, identity in dialogue_animation_lines(raw)
                      if label.startswith("SpeakerWitness"))
        if len(lines) < 2:
            raise ValueError("Two independent speaking sequences require two native lines")
        raw = assign_dialogue_speaking_sequence(raw, lines[0], "Speak, SpeakAlt")
        raw = assign_dialogue_speaking_sequence(raw, lines[1], "SpeakBlue, SpeakYellow")
    elif four_facing:
        for direction, frame in (("N", "Speak"), ("E", "SpeakAlt"),
                                 ("S", "SpeakBlue"), ("W", "SpeakYellow")):
            raw = set_costume_direction_speaking_pose(raw, "WitnessCostume", direction, frame)
        lines = tuple(identity for label, identity in dialogue_animation_lines(raw)
                      if label.startswith("SpeakerWitness"))
        if len(lines) != 4:
            raise ValueError("Four-facing fixture requires four native lines for one actor")
        for line in lines:
            raw = edit_dialogue_animation(raw, line, "gesture", True)
    elif animated:
        for direction in ("N", "E", "S", "W"):
            raw = set_costume_direction_speaking_sequence(
                raw, "WitnessCostume", direction, "Speak, SpeakAlt")
        lines = tuple(identity for label, identity in dialogue_animation_lines(raw)
                      if label.startswith("SpeakerWitness"))
        if len(lines) < 2:
            raise ValueError("Animated speaking fixture requires native lines")
        for line in lines:
            raw = edit_dialogue_animation(raw, line, "gesture", True)
    elif two_poses:
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
    if len(sys.argv) not in (2, 3) or (len(sys.argv) == 3 and sys.argv[2] not in ("--two-poses", "--four-facing", "--animated", "--line-sequences", "--line-directions")):
        print("Usage: python -m adventure_studio.dialogue_animation_fixture BUILD_DIRECTORY [--two-poses|--four-facing|--animated|--line-sequences|--line-directions]")
        return 2
    build(Path(sys.argv[1]), two_poses=len(sys.argv) == 3 and sys.argv[2] == "--two-poses",
          four_facing=len(sys.argv) == 3 and sys.argv[2] == "--four-facing",
          animated=len(sys.argv) == 3 and sys.argv[2] == "--animated",
          line_sequences=len(sys.argv) == 3 and sys.argv[2] == "--line-sequences",
          line_directions=len(sys.argv) == 3 and sys.argv[2] == "--line-directions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
