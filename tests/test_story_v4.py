import json
import unittest
from dataclasses import replace
from pathlib import Path

from adventure_studio.story import (AssetRef, Character, Dialogue, DialogueChoice,
                                    DialogueNode, Item, Placement, validate_story)
from adventure_studio.story_changes import PutEntity, edit_story
from adventure_studio.story_document import canonical_story_json, parse_story_document
from adventure_studio.story_protocol import parse_operations
from adventure_studio.story_to_scumm import compile_story_to_scumm
from adventure_studio.studio_gradio import catalog_view, safe_render_scene
from adventure_studio.story_ai import preview_ai_response
from adventure_studio.studio_service import change_dialogue_line, change_scene, report_text


SAMPLE = (Path(__file__).resolve().parents[1] / "examples/mini_story_chain.json").read_text(encoding="utf-8")
DIGEST = "a" * 64


def dialogue_story():
    story = parse_story_document(SAMPLE)
    return replace(story,
        characters=(Character("Keeper", "Wächter", "Spricht über die Tür", "Harbor"),),
        dialogues=(Dialogue("Greeting", "Harbor", "Hello"),),
        dialogue_nodes=(
            DialogueNode("Hello", "Greeting", "Keeper", "Wer bist du?"),
            DialogueNode("Response", "Greeting", "Keeper", "Na dann.")),
        dialogue_choices=(DialogueChoice("Ask", "Hello", "Ich suche den Schlüssel.", "Response"),
                          DialogueChoice("Bye", "Hello", "Auf Wiedersehen.", None)),
        assets=(AssetRef("KeeperPortrait", "character", "Keeper", "portrait", "fixture:keeper", DIGEST),
                AssetRef("KeeperVoice", "dialogue_node", "Hello", "voice", "fixture:hello", DIGEST)))


class StoryV4Tests(unittest.TestCase):
    def test_v4_roundtrip_preserves_dialogue_and_provenance(self):
        story = dialogue_story()
        raw = canonical_story_json(story)
        self.assertEqual(json.loads(raw)["format_version"], 4)
        self.assertEqual(parse_story_document(raw), story)
        self.assertEqual(canonical_story_json(parse_story_document(raw)), raw)

    def test_v1_v2_v3_inputs_cannot_smuggle_v4_fields(self):
        base = json.loads(SAMPLE)
        base["story"]["dialogues"] = []
        with self.assertRaisesRegex(ValueError, "Invalid story fields"):
            parse_story_document(json.dumps(base))

    def test_v4_rejects_executable_fields_and_invalid_types(self):
        base = json.loads(canonical_story_json(dialogue_story()))
        illegal = json.loads(json.dumps(base))
        illegal["story"]["dialogue_nodes"][0]["javascript"] = "alert(1)"
        with self.assertRaisesRegex(ValueError, "Invalid DialogueNode fields"):
            parse_story_document(json.dumps(illegal))
        illegal = json.loads(json.dumps(base))
        illegal["story"]["dialogue_choices"][0]["next_node_id"] = 4
        with self.assertRaisesRegex(ValueError, "Invalid story text"):
            parse_story_document(json.dumps(illegal))

    def test_invalid_dialogue_graphs_are_rejected(self):
        story = dialogue_story()
        invalid = [
            replace(story, dialogue_nodes=story.dialogue_nodes + (
                DialogueNode("Stray", "Greeting", "Keeper", "Nie erreichbar"),)),
            replace(story, dialogue_nodes=(replace(story.dialogue_nodes[0], next_node_id="Response"),
                                          story.dialogue_nodes[1])),
            replace(story, dialogue_choices=(DialogueChoice("Ask", "Hello", "Text", "Unknown"),)),
            replace(story, dialogue_nodes=(replace(story.dialogue_nodes[0], speaker_id="Missing"),
                                          story.dialogue_nodes[1])),
            replace(story, assets=(replace(story.assets[0], digest="notahash"),)),
            replace(story, assets=(replace(story.assets[0], target_id="Missing"),)),
        ]
        for candidate in invalid:
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                validate_story(candidate)

    def test_circular_dialogue_without_exit_is_rejected(self):
        story = dialogue_story()
        stuck = replace(story, dialogue_choices=(DialogueChoice("Loop", "Hello", "Noch mal", "Response"),),
                        dialogue_nodes=(story.dialogue_nodes[0], replace(story.dialogue_nodes[1], next_node_id="Hello")))
        with self.assertRaisesRegex(ValueError, "dead end"):
            validate_story(stuck)

    def test_scumm_export_fails_closed_for_new_unimplemented_content(self):
        with self.assertRaisesRegex(ValueError, "dialogue or versioned asset"):
            compile_story_to_scumm(dialogue_story())

    def test_authoring_remains_possible_with_explicit_export_warning(self):
        raw = canonical_story_json(dialogue_story())
        preview = catalog_view(raw)
        self.assertEqual(len(preview[7]), 1)  # dialogue list
        self.assertEqual(len(preview[9]), 2)  # asset references
        self.assertEqual(preview[10], [])  # no fake game frame
        self.assertIsNone(safe_render_scene(raw, "Harbor"))
        edit = change_scene(raw, "Harbor", "Neuer Hafen", "Andere Beschreibung")
        self.assertIn("SCUMM-Export noch nicht möglich", report_text(edit.report))
        self.assertEqual(parse_story_document(edit.story_json).scenes[0].title, "Neuer Hafen")

    def test_ai_can_propose_dialogue_without_silently_exporting_it(self):
        base = parse_story_document(SAMPLE)
        ops = {"operations": [
            {"op": "put", "kind": "character", "entity": {
                "id": "Keeper", "name": "Wächter", "description": "Steht am Tor", "scene_id": "Harbor"}},
            {"op": "put", "kind": "dialogue", "entity": {
                "id": "Greeting", "scene_id": "Harbor", "entry_node_id": "Hello"}},
            {"op": "put", "kind": "dialogue_node", "entity": {
                "id": "Hello", "dialogue_id": "Greeting", "speaker_id": "Keeper",
                "text": "Hallo!", "next_node_id": None}},
        ]}
        # Existing compiler rejects custom characters: preview still allows
        # authoring the versioned model while reporting the export gate.
        proposal = preview_ai_response(canonical_story_json(base), json.dumps(ops))
        self.assertIn("SCUMM-Export noch nicht möglich", report_text(proposal.edit.report))
        self.assertEqual(len(parse_story_document(proposal.edit.story_json).dialogues), 1)

    def test_direct_dialogue_text_edit_is_atomic_and_bounded(self):
        raw = canonical_story_json(dialogue_story())
        edit = change_dialogue_line(raw, "Hello", "Ein neuer Hinweis.")
        self.assertIn("geändert: dialogue_node Hello", report_text(edit.report))
        self.assertEqual(parse_story_document(edit.story_json).dialogue_nodes[0].text, "Ein neuer Hinweis.")
        with self.assertRaises(ValueError):
            change_dialogue_line(raw, "Hello", "")
        with self.assertRaises(ValueError):
            change_dialogue_line(raw, "Missing", "Text")

    def test_v4_operations_are_strict_and_atomic(self):
        base = dialogue_story()
        raw = json.dumps({"operations": [{"op": "put", "kind": "dialogue_node", "entity": {
            "id": "Response", "dialogue_id": "Greeting", "speaker_id": "Keeper",
            "text": "Der Schlüssel liegt neben der Tür.", "next_node_id": None}}]})
        changed, report = edit_story(base, parse_operations(raw))
        self.assertEqual(changed.dialogue_nodes[1].text, "Der Schlüssel liegt neben der Tür.")
        self.assertEqual(report.changes[0].kind, "dialogue_node")

    def test_orphan_asset_is_consolidated_with_orphan_pickup(self):
        base = dialogue_story()
        extra = replace(base, items=base.items + (Item("Extra", "Extra", "Lose", "Harbor"),),
                        placements=(Placement("Extra", 80, 80),),
                        assets=base.assets + (AssetRef("ExtraSprite", "item", "Extra", "object_sprite", "fixture:extra", DIGEST),))
        changed, report = edit_story(extra, (PutEntity("scene", base.scenes[0]),))
        self.assertFalse(any(a.id == "ExtraSprite" for a in changed.assets))
        self.assertIn("Extra", report.consolidated)
        self.assertTrue(any(d.kind == "asset" and d.id == "ExtraSprite" and d.after is None for d in report.changes))


if __name__ == "__main__":
    unittest.main()
