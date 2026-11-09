"""Authored facing cues are scoped to their SCUMM dialogue speaker."""

from pathlib import Path
import unittest

from adventure_studio.dialogue_demo import dialogue_fixture
from adventure_studio.scumm_assets import scummc_room_source
from adventure_studio.scumm_project import canonical_json, parse_document
from adventure_studio.story_document import canonical_story_json, parse_story_document
from adventure_studio.story_to_scumm import compile_story_to_scumm
from adventure_studio.studio_service import change_dialogue_facing


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "mini_story.json"


class DialogueFacingTests(unittest.TestCase):
    def setUp(self):
        self.raw = dialogue_fixture(EXAMPLE.read_text(encoding="utf-8"), multispeaker=True)

    def test_two_speakers_face_differently_before_their_lines(self):
        first = change_dialogue_facing(self.raw, "HarborHello", "W")
        second = change_dialogue_facing(first.story_json, "HarborHint", "E")
        game = compile_story_to_scumm(parse_story_document(second.story_json))
        hotspot = next(h for h in game.rooms[0].hotspots if h.id == "HarborKeeper")
        self.assertEqual(hotspot.talk_face_directions, ("W", "E"))
        source = scummc_room_source(game.rooms[0])
        self.assertLess(source.index("setCurrentActor(SpeakerHarborKeeper);"),
                        source.index('actorSay(SpeakerHarborKeeper,"Was suchst du hier?")'))
        self.assertIn("setActorDirection(WEST);", source)
        self.assertIn("setActorDirection(EAST);", source)
        self.assertLess(source.index("setCurrentActor(SpeakerWitness);"),
                        source.index('actorSay(SpeakerWitness,"Der Schluessel liegt am Boden.")'))
        self.assertEqual(canonical_json(parse_document(canonical_json(game))), canonical_json(game))

    def test_branching_facing_keeps_assigned_speaker(self):
        raw = dialogue_fixture(EXAMPLE.read_text(encoding="utf-8"), choices=True, multispeaker=True)
        edit = change_dialogue_facing(raw, "HarborHint", "N")
        game = compile_story_to_scumm(parse_story_document(edit.story_json))
        rule = game.rooms[0].talk_rules[0]
        self.assertEqual(len(rule.actor_directions), 1)
        source = scummc_room_source(game.rooms[0])
        self.assertIn("setCurrentActor(SpeakerWitness);", source)
        self.assertIn("setActorDirection(NORTH);", source)

    def test_legacy_story_unchanged_and_invalid_cues_rejected(self):
        story = parse_story_document(self.raw)
        self.assertNotIn('"face_direction"', canonical_story_json(story))
        original = scummc_room_source(compile_story_to_scumm(story).rooms[0])
        self.assertNotIn("setActorDirection(", original)
        with self.assertRaisesRegex(ValueError, "facing"):
            change_dialogue_facing(self.raw, "HarborHint", "NW")
        with self.assertRaisesRegex(ValueError, "Unknown"):
            change_dialogue_facing(self.raw, "Missing", "E")
        disabled = change_dialogue_facing(change_dialogue_facing(self.raw, "HarborHint", "S").story_json,
                                          "HarborHint", None)
        self.assertNotIn('"face_direction"', disabled.story_json)


if __name__ == "__main__":
    unittest.main()
