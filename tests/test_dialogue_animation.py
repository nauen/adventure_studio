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
            costume, animations=tuple(replace(animation, index=20)
                                      if animation.name == "stand" else animation
                                      for animation in costume.animations) + (gesture,)),))
        return story, canonical_json(document)

    def test_linear_speaker_cue_survives_project_and_compiles_actor_command(self):
        story, raw = self.fixture()
        lines = dialogue_animation_lines(raw)
        self.assertEqual(len(lines), 2)
        witness = next(key for label, key in lines if label.startswith("SpeakerWitness"))
        self.assertEqual(dialogue_animation_choices(raw, witness), (("stand", "gesture"), None, True))
        raw = edit_dialogue_animation(raw, witness, "gesture")
        self.assertEqual(dialogue_animation_choices(raw, witness), (("stand", "gesture"), "gesture", True))
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
        self.assertGreater(source.index("animateActor(SpeakerWitness,24);"),
                           source.index('actorSay(SpeakerWitness,"Der Schluessel liegt am Boden.")'))
        self.assertLess(source.index("animateActor(SpeakerWitness,24);"),
                        source.index("waitForMessage();", source.index(
                            'actorSay(SpeakerWitness,"Der Schluessel liegt am Boden.")')))
        wait = source.index("waitForMessage();", source.index(
            'actorSay(SpeakerWitness,"Der Schluessel liegt am Boden.")'))
        self.assertIn("setCurrentActor(SpeakerWitness);\n            setActorStanding();\n"
                      "            setCurrentActor(VAR_EGO);", source[wait:])
        self.assertIn("animateActor(SpeakerWitness,20);", source[wait:])
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

    def test_legacy_animation_without_reset_stays_compatible(self):
        story, raw = self.fixture()
        witness = next(key for label, key in dialogue_animation_lines(raw)
                       if label.startswith("SpeakerWitness"))
        legacy = edit_dialogue_animation(raw, witness, "gesture", False)
        self.assertNotIn("reset_to_stand", legacy)
        self.assertEqual(dialogue_animation_choices(legacy, witness), (("stand", "gesture"), "gesture", False))
        document = parse_document(legacy)
        source = scummc_room_source(document.rooms[0],
                                   dialogue_animation_cues=dialogue_animation_bindings(
                                       document, document.rooms[0]))
        self.assertIn("animateActor(SpeakerWitness,24);", source)
        self.assertNotIn("setCurrentActor(SpeakerWitness);\n            setActorStanding();", source)
        with self.assertRaisesRegex(ValueError, "Standpose-Einstellung"):
            edit_dialogue_animation(raw, witness, "gesture", 1)

    def test_consecutive_speakers_reset_their_own_costumes(self):
        _story, raw = self.fixture()
        lines = dialogue_animation_lines(raw)
        for _label, line in lines:
            raw = edit_dialogue_animation(raw, line, "gesture", True)
        document = parse_document(raw)
        source = scummc_room_source(document.rooms[0],
                                   dialogue_animation_cues=dialogue_animation_bindings(
                                       document, document.rooms[0]))
        self.assertEqual(source.count("animateActor(SpeakerHarborKeeper,24);"), 1)
        self.assertEqual(source.count("animateActor(SpeakerWitness,24);"), 1)
        for actor in ("SpeakerHarborKeeper", "SpeakerWitness"):
            self.assertIn(f"setCurrentActor({actor});\n            setActorStanding();\n"
                          "            setCurrentActor(VAR_EGO);", source)
            self.assertIn(f"animateActor({actor},20);", source)

        missing = replace(document.costumes[0], animations=tuple(
            animation for animation in document.costumes[0].animations
            if animation.name != "stand"))
        with self.assertRaisesRegex(ValueError, "stand pose"):
            parse_document(canonical_json(replace(document, costumes=(missing,))))
        unindexed = replace(document.costumes[0], animations=tuple(
            replace(animation, index=None) if animation.name == "stand" else animation
            for animation in document.costumes[0].animations))
        with self.assertRaisesRegex(ValueError, "indexed stand pose"):
            parse_document(canonical_json(replace(document, costumes=(unindexed,))))


if __name__ == "__main__":
    unittest.main()
