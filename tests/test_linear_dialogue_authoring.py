"""Authoring a sequential two-speaker conversation reaches native SCUMM."""

from pathlib import Path
import unittest

from adventure_studio.dialogue_demo import dialogue_fixture
from adventure_studio.scumm_assets import scummc_room_source
from adventure_studio.story_document import parse_story_document
from adventure_studio.story_to_scumm import compile_story_to_scumm
from adventure_studio.studio_service import extend_dialogue_line
from adventure_studio.studio_service import add_dialogue_choice


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "mini_story.json"


class LinearDialogueAuthoringTests(unittest.TestCase):
    def setUp(self):
        self.raw = dialogue_fixture(EXAMPLE.read_text(encoding="utf-8"), multispeaker=True)

    def test_append_two_lines_with_different_speakers_and_export(self):
        first = extend_dialogue_line(self.raw, "HarborHint", "ReplyWitness",
                                     "Der Schluessel liegt am Boden.", "Witness")
        second = extend_dialogue_line(first.story_json, "ReplyWitness", "KeeperAgain",
                                      "Danke fuer den Hinweis.", "HarborKeeper")
        story = parse_story_document(second.story_json)
        self.assertEqual([node.id for node in story.dialogue_nodes],
                         ["HarborHello", "HarborHint", "ReplyWitness", "KeeperAgain"])
        game = compile_story_to_scumm(story)
        hotspot = next(h for h in game.rooms[0].hotspots if h.id == "HarborKeeper")
        self.assertEqual(hotspot.talk_actor_lines,
                         ("SpeakerHarborKeeper", "SpeakerWitness", "SpeakerWitness", "SpeakerHarborKeeper"))
        source = scummc_room_source(game.rooms[0])
        self.assertLess(source.index('actorSay(SpeakerHarborKeeper,"Was suchst du hier?")'),
                        source.index('actorSay(SpeakerWitness,"Der Schluessel liegt am Boden.")'))
        self.assertIn('actorSay(SpeakerHarborKeeper,"Danke fuer den Hinweis.")', source)

    def test_single_speaker_default_preserves_story_contract(self):
        single = dialogue_fixture(EXAMPLE.read_text(encoding="utf-8"))
        edit = extend_dialogue_line(single, "HarborHint", "More", "Noch etwas.")
        story = parse_story_document(edit.story_json)
        self.assertEqual(story.dialogue_nodes[-1].speaker_id, "HarborKeeper")
        source = scummc_room_source(compile_story_to_scumm(story).rooms[0])
        self.assertIn('egoSay("Noch etwas.")', source)

    def test_reject_invalid_target_duplicate_and_foreign_speaker(self):
        with self.assertRaisesRegex(ValueError, "Unknown dialogue"):
            extend_dialogue_line(self.raw, "Missing", "New", "Text")
        with self.assertRaisesRegex(ValueError, "unique ASCII"):
            extend_dialogue_line(self.raw, "HarborHint", "HarborHint", "Text")
        with self.assertRaisesRegex(ValueError, "same scene"):
            extend_dialogue_line(self.raw, "HarborHint", "Other", "Text", "Missing")
        existing = extend_dialogue_line(self.raw, "HarborHint", "Next", "Text")
        with self.assertRaisesRegex(ValueError, "terminal"):
            extend_dialogue_line(existing.story_json, "HarborHint", "Other", "Text")
        branched = add_dialogue_choice(self.raw, "HarborHint", "AskAgain", "Nochmal?")
        with self.assertRaisesRegex(ValueError, "terminal"):
            extend_dialogue_line(branched.story_json, "HarborHint", "Other", "Text")


if __name__ == "__main__":
    unittest.main()
