"""Existing dialogue answers remain editable through the production story path."""

from pathlib import Path
import unittest

from adventure_studio.dialogue_demo import dialogue_fixture
from adventure_studio.scumm_assets import scummc_room_source
from adventure_studio.story_document import parse_story_document
from adventure_studio.story_to_scumm import compile_story_to_scumm
from adventure_studio.studio_gradio import dialogue_choice_fields
from adventure_studio.studio_service import add_dialogue_choice, change_dialogue_choice


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "mini_story.json"


class DialogueChoiceEditTests(unittest.TestCase):
    def setUp(self):
        self.raw = dialogue_fixture(EXAMPLE.read_text(encoding="utf-8"), choices=True)
        self.raw = add_dialogue_choice(self.raw, "HarborHello", "KeepHint",
                                       "Noch eine Frage.", "HarborHint").story_json

    def test_edit_text_and_destination_reaches_native_dialogue(self):
        edited = change_dialogue_choice(self.raw, "AskKey", "  Erzähl mir mehr.  ", "HarborBye")
        story = parse_story_document(edited.story_json)
        answer = next(c for c in story.dialogue_choices if c.id == "AskKey")
        self.assertEqual((answer.text, answer.next_node_id), ("Erzähl mir mehr.", "HarborBye"))
        label, target = dialogue_choice_fields(edited.story_json, "AskKey")
        self.assertEqual((label, target["value"]), ("Erzähl mir mehr.", "HarborBye"))
        source = scummc_room_source(compile_story_to_scumm(story).rooms[0])
        self.assertIn("Erzahl mir mehr.", source)
        self.assertIn("Bis bald.", source)

    def test_terminal_answer_and_invalid_target(self):
        edited = change_dialogue_choice(self.raw, "AskKey", "Fertig.", None)
        choice = next(c for c in parse_story_document(edited.story_json).dialogue_choices
                      if c.id == "AskKey")
        self.assertIsNone(choice.next_node_id)
        with self.assertRaisesRegex(ValueError, "same dialogue"):
            change_dialogue_choice(self.raw, "AskKey", "Weiter", "Missing")
        with self.assertRaisesRegex(ValueError, "Answer text"):
            change_dialogue_choice(self.raw, "AskKey", " ", None)
        with self.assertRaisesRegex(ValueError, "Unknown"):
            change_dialogue_choice(self.raw, "Missing", "Weiter", None)


if __name__ == "__main__":
    unittest.main()
