"""The Story editor preserves explicitly selected speakers across dialogue branches."""

from dataclasses import replace
from pathlib import Path
import unittest

from adventure_studio.dialogue_demo import dialogue_fixture
from adventure_studio.story import Character
from adventure_studio.story_document import canonical_story_json, parse_story_document
from adventure_studio.studio_gradio import dialogue_speaker_fields
from adventure_studio.studio_service import (add_dialogue_choice, change_dialogue_line,
                                             extend_dialogue_choice)


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "mini_story.json"


class DialogueSpeakerAuthoringTests(unittest.TestCase):
    def setUp(self):
        story = parse_story_document(dialogue_fixture(EXAMPLE.read_text(encoding="utf-8"), True))
        self.raw = canonical_story_json(replace(story, characters=(*story.characters,
            Character("Witness", "Zeuge", "Ein Zeuge sieht zu.", story.starting_scene_id))))

    def test_speaker_can_change_on_existing_and_new_response(self):
        first = change_dialogue_line(self.raw, "HarborHint", "Das weiss ich.", "Witness")
        self.assertEqual(next(n.speaker_id for n in parse_story_document(first.story_json).dialogue_nodes
                              if n.id == "HarborHint"), "Witness")
        staged = add_dialogue_choice(first.story_json, "HarborHint", "WitnessAsk", "Warum?", None)
        second = extend_dialogue_choice(staged.story_json, "WitnessAsk", "WitnessReply",
                                        "Der Zeuge antwortet.", "Witness")
        node = next(n for n in parse_story_document(second.story_json).dialogue_nodes
                    if n.id == "WitnessReply")
        self.assertEqual((node.speaker_id, node.text), ("Witness", "Der Zeuge antwortet."))
        self.assertIn(("Zeuge", "Witness"), dialogue_speaker_fields(second.story_json,
                                                                     "WitnessReply")["choices"])

    def test_foreign_scene_speaker_is_rejected(self):
        story = parse_story_document(self.raw)
        other_scene = next(scene.id for scene in story.scenes if scene.id != story.starting_scene_id)
        raw = canonical_story_json(replace(story, characters=(*story.characters,
            Character("Away", "Anderer Ort", "Nicht hier.", other_scene))))
        with self.assertRaisesRegex(ValueError, "same scene"):
            change_dialogue_line(raw, "HarborHint", "Wo bist du?", "Away")
        staged = add_dialogue_choice(raw, "HarborHint", "WitnessAsk", "Warum?", None)
        with self.assertRaisesRegex(ValueError, "same scene"):
            extend_dialogue_choice(staged.story_json, "WitnessAsk", "Other", "Hallo", "Away")


if __name__ == "__main__":
    unittest.main()
