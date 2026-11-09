"""An authored NPC line triggers its actor's indexed native COST animation."""

from dataclasses import replace
from pathlib import Path
import unittest

from adventure_studio.dialogue_demo import dialogue_fixture
from adventure_studio.scumm_assets import scummc_room_source
from adventure_studio.scumm_costume import CostumeAnimation, CostumeDirection
from adventure_studio.scumm_project import canonical_json, parse_document
from adventure_studio.scumm_toolchain import dialogue_animation_bindings
from adventure_studio.studio_project import canonical_studio_project, parse_studio_project
from adventure_studio.studio_sequences import (compose_story_project, dialogue_animation_lines,
                                                dialogue_animation_choices, edit_dialogue_animation)


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "mini_story.json"


class DialogueAnimationTests(unittest.TestCase):
    def fixture(self, branching=False):
        story = dialogue_fixture(EXAMPLE.read_text(encoding="utf-8"),
                                 choices=branching, multispeaker=True)
        document = parse_document(compose_story_project(story))
        costume = document.costumes[0]
        gesture = CostumeAnimation("gesture", tuple(
            CostumeDirection(direction, ("Pose",), False)
            for direction in ("N", "E", "S", "W")), 24)
        document = replace(document, costumes=(replace(
            costume, animations=(*costume.animations, gesture)),))
        return story, canonical_json(document)

    def test_linear_speaker_cue_survives_project_and_compiles_actor_command(self):
        story, raw = self.fixture()
        lines = dialogue_animation_lines(raw)
        self.assertEqual(len(lines), 2)
        witness = next(key for label, key in lines if label.startswith("SpeakerWitness"))
        self.assertEqual(dialogue_animation_choices(raw, witness), (("gesture",), None))
        raw = edit_dialogue_animation(raw, witness, "gesture")
        self.assertEqual(dialogue_animation_choices(raw, witness), (("gesture",), "gesture"))
        document = parse_document(raw)
        self.assertEqual(canonical_json(document), raw)
        saved = canonical_studio_project(story, raw)
        loaded_story, loaded_native = parse_studio_project(saved)
        rebuilt = parse_document(compose_story_project(loaded_story, loaded_native))
        self.assertEqual(rebuilt.dialogue_animation_cues, document.dialogue_animation_cues)
        source = scummc_room_source(rebuilt.rooms[0],
                                   dialogue_animation_cues=dialogue_animation_bindings(
                                       rebuilt, rebuilt.rooms[0]))
        self.assertIn("animateActor(SpeakerWitness,24);", source)
        self.assertLess(source.index("animateActor(SpeakerWitness,24);"),
                        source.index('actorSay(SpeakerWitness,"Der Schluessel liegt am Boden.")'))
        self.assertEqual(parse_document(edit_dialogue_animation(raw, witness, None)).dialogue_animation_cues, ())

    def test_branching_reply_and_invalid_costume_fail_closed(self):
        story, raw = self.fixture(branching=True)
        reply = next(key for _label, key in dialogue_animation_lines(raw) if ".reply." in key)
        bound = edit_dialogue_animation(raw, reply, "gesture")
        self.assertEqual(parse_document(bound).dialogue_animation_cues[0].line_id, reply)
        with self.assertRaisesRegex(ValueError, "indexed COST"):
            edit_dialogue_animation(raw, reply, "missing")
        with self.assertRaisesRegex(ValueError, "Sprecher"):
            edit_dialogue_animation(raw, "room.harbor.dialogue.100.opening.0", "gesture")
        changed_story = story.replace("Der Schluessel liegt am Boden.", "Der Weg liegt am Boden.")
        with self.assertRaisesRegex(ValueError, "Stale dialogue animation"):
            compose_story_project(changed_story, bound)


if __name__ == "__main__":
    unittest.main()
