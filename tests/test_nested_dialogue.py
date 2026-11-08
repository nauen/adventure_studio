"""Characterize nested NPC choices and a native return to the entry menu."""

import unittest
from pathlib import Path

from adventure_studio.dialogue_demo import dialogue_fixture
from adventure_studio.localization import LanguageCatalog, LocalizedLine
from adventure_studio.scumm_assets import scummc_room_source
from adventure_studio.scumm_project import canonical_json, parse_document
from adventure_studio.story_document import parse_story_document
from adventure_studio.story_localization import story_text_inventory
from adventure_studio.story_to_scumm import compile_story_to_scumm
from adventure_studio.studio_sequences import dialogue_voice_lines
from adventure_studio.studio_service import add_dialogue_choice, extend_dialogue_choice


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "mini_story.json"


class NestedDialogueTests(unittest.TestCase):
    def test_studio_authors_nested_return_and_further_response(self):
        initial = dialogue_fixture(EXAMPLE.read_text(encoding="utf-8"), True)
        first = add_dialogue_choice(initial, "HarborHint", "AskAgain",
                                    "Nochmal fragen.", "HarborHello")
        second = add_dialogue_choice(first.story_json, "HarborHint", "More",
                                     "Noch mehr?", None)
        extended = extend_dialogue_choice(second.story_json, "More", "HarborExtra",
                                          "Noch eine Information.")
        generated = compile_story_to_scumm(parse_story_document(extended.story_json))
        stage = generated.rooms[0].talk_rules[0].stages[0]
        self.assertEqual(stage.choices[0].next_stage_id, "Entry")
        self.assertIn("Noch eine Information.", stage.choices[1].reply_lines)
        self.assertEqual(canonical_json(parse_document(canonical_json(generated))),
                         canonical_json(generated))
        with self.assertRaisesRegex(ValueError, "same dialogue"):
            add_dialogue_choice(first.story_json, "HarborHint", "Bad", "Frage", "Unknown")

    def test_nested_answer_opens_new_choices_and_returns_to_entry(self):
        raw = dialogue_fixture(EXAMPLE.read_text(encoding="utf-8"), True, True)
        document = compile_story_to_scumm(parse_story_document(raw))
        room = document.rooms[0]
        rule = room.talk_rules[0]
        self.assertEqual(len(rule.stages), 1)
        self.assertEqual(rule.choices[0].next_stage_id, "StageHarborHint")
        self.assertEqual(rule.stages[0].choices[0].next_stage_id, "Entry")
        self.assertEqual(rule.stages[0].choices[1].next_stage_id, None)
        source = scummc_room_source(room)
        self.assertIn("setObjectState(AnswerHarborKeeperN2C1,1);", source)
        self.assertIn("setObjectState(AnswerHarborKeeper1,1);", source)
        self.assertIn("setObjectState(AnswerHarborKeeper2,0);", source)
        self.assertEqual(canonical_json(parse_document(canonical_json(document))),
                         canonical_json(document))
        keys = story_text_inventory(document)
        self.assertIn("room.harbor.dialogue.0.stage.0.opening.0", keys)
        self.assertIn("room.harbor.dialogue.0.stage.0.choice.0.caption", keys)
        self.assertTrue(any(".stage.0.opening" in identity
                            for _label, identity in dialogue_voice_lines(canonical_json(document))))
        catalog = LanguageCatalog("en", ("de", "en"), tuple(
            LocalizedLine(key, (("de", value), ("en", value))) for key, value in keys.items()))
        native = scummc_room_source(room, catalog)
        self.assertIn("GameLanguage == 25701", native)


if __name__ == "__main__":
    unittest.main()
