import json
import unittest

from adventure_studio.story_changes import edit_story
from adventure_studio.story_protocol import parse_operations
from test_story import pirate_story


class StoryProtocolTests(unittest.TestCase):
    def test_recipe_operations_are_declarative_and_strict(self):
        raw = json.dumps({"operations": [{"op": "put", "kind": "recipe", "entity": {
            "id": "Mix", "title": "Mischen", "ingredients": ["Pineapple", "Bottle"],
            "result_item_id": "Mixture"}}]})
        operations = parse_operations(raw)
        self.assertEqual(operations[0].entity.ingredients, ("Pineapple", "Bottle"))
        illegal = json.loads(raw)
        illegal["operations"][0]["entity"]["source_code"] = "eval('payload')"
        with self.assertRaisesRegex(ValueError, "Unexpected or missing"):
            parse_operations(json.dumps(illegal))

    def test_model_json_edits_story(self):
        raw = json.dumps({"operations": [
            {"op": "put", "kind": "item", "entity": {
                "id": "rum", "name": "Rum", "description": "Flasche", "scene_id": "tavern"}},
            {"op": "put", "kind": "puzzle", "entity": {
                "id": "unlock", "title": "Öffne den Schuppen", "scene_id": "tavern",
                "requires": ["rum"], "opens_scene_id": "shed"}},
            {"op": "delete", "kind": "item", "id": "key"},
        ]})
        updated, report = edit_story(pirate_story(), parse_operations(raw))
        self.assertEqual(report.playable_path, ("take:rum", "solve:unlock", "solve:escape"))
        self.assertEqual({i.id for i in updated.items}, {"rum", "pineapple"})

    def test_unknown_fields_rejected(self):
        raw = json.dumps({"operations": [{"op": "put", "kind": "item", "entity": {
            "id": "a", "name": "A", "description": "x", "scene_id": "tavern", "execute": "rm -rf /"}}]})
        with self.assertRaisesRegex(ValueError, "Unexpected or missing"):
            parse_operations(raw)

    def test_unbounded_input_rejected(self):
        with self.assertRaisesRegex(ValueError, "too large"):
            parse_operations(" " * 200001)


if __name__ == "__main__":
    unittest.main()
