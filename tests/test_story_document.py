"""The complete story JSON -> project -> SCUMM source-asset contract."""

import json
import tempfile
import unittest
from pathlib import Path

from adventure_studio.story_document import (
    build_story_document, canonical_story_json, parse_story_document,
)


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "mini_story.json"
THREE_ITEMS = EXAMPLE.with_name("mini_story_three_items.json")
CHAIN = EXAMPLE.with_name("mini_story_chain.json")
RECIPE = EXAMPLE.with_name("recipe_story.json")


class StoryDocumentTests(unittest.TestCase):
    def test_recipe_story_v2_exports_bounded_inventory_combination(self):
        from adventure_studio.story import compile_story, verify_story
        from adventure_studio.core import execute
        from adventure_studio.story_to_scumm import compile_story_to_scumm
        story = parse_story_document(RECIPE.read_text(encoding="utf-8"))
        self.assertEqual(verify_story(story),
                         ("take:Pineapple", "take:Bottle", "combine:MakeMixture", "solve:OpenLaboratory"))
        self.assertEqual(parse_story_document(canonical_story_json(story)), story)
        project = compile_story(story)
        state = project.initial
        for action in ("take:Pineapple", "take:Bottle", "combine:MakeMixture"):
            state = execute(project, state, action)
        values = dict(state)
        self.assertFalse(values["item.Pineapple"])
        self.assertFalse(values["item.Bottle"])
        self.assertTrue(values["item.Mixture"])
        self.assertTrue(values["picked.Pineapple"])
        with self.assertRaisesRegex(ValueError, "unavailable"):
            execute(project, state, "take:Pineapple")
        game = compile_story_to_scumm(story)
        self.assertEqual(game.rooms[0].combine_rules[0].result_id, "Mixture")
        from adventure_studio.scumm_project import canonical_json, parse_document
        self.assertEqual(parse_document(canonical_json(game)), game)
        with tempfile.TemporaryDirectory() as tmp:
            result = build_story_document(RECIPE.read_text(encoding="utf-8"), Path(tmp))
            source = (result.resource_directory / "Kitchen.scc").read_text()
            self.assertIn("setObjectOwner(Pineapple, 0)", source)
            self.assertLess(source.index("object Pineapple;"), source.index("script combine_0()"))
            self.assertIn("setObjectOwner(Bottle, 0)", source)
            self.assertIn("pickupObject(Mixture, VAR_ROOM)", source)
            self.assertIn("combine_0();", source)
            self.assertIn("state = 0;", source)
            self.assertTrue((result.resource_directory / "Inv_Mixture.bmp").is_file())

    def test_recipe_that_consumes_a_required_key_creates_a_detected_softlock(self):
        from dataclasses import replace
        from adventure_studio.story import Puzzle, verify_story
        story = parse_story_document(RECIPE.read_text(encoding="utf-8"))
        unsafe = replace(story,
                         puzzles=(Puzzle("OpenLab", "Oeffne Labor", "Kitchen", ("Pineapple",), "Laboratory"),
                                  Puzzle("Finish", "Fertig", "Laboratory", ("Mixture",))),
                         final_puzzle_id="Finish")
        with self.assertRaisesRegex(ValueError, "dead_ends"):
            verify_story(unsafe)

    def test_two_puzzles_form_three_sequential_rooms(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build_story_document(CHAIN.read_text(encoding="utf-8"), Path(tmp))
            rooms = result.resource_directory
            self.assertEqual(json.loads(result.project_json.read_text())["rooms"][2]["name"], "Archive")
            self.assertIn("startRoom(Cellar)", (rooms / "Harbor.scc").read_text())
            self.assertIn("startRoom(Archive)", (rooms / "Cellar.scc").read_text())
            self.assertIn("object Door2", (rooms / "Cellar.scc").read_text())
            self.assertIn("object Back2", (rooms / "Cellar.scc").read_text())
            self.assertIn("startRoom(Harbor)", (rooms / "Cellar.scc").read_text())
            self.assertIn("object Back3", (rooms / "Archive.scc").read_text())
            self.assertIn("startRoom(Cellar)", (rooms / "Archive.scc").read_text())
            self.assertTrue((rooms / "Inv_Badge.bmp").is_file())
            goal = json.loads((rooms / "game-goal.json").read_text())
            self.assertEqual(goal["fixture_route"], [
                {"room_id": "Harbor", "item_id": "Key", "rgb": [255, 220, 75], "next_room_id": "Cellar"},
                {"room_id": "Cellar", "item_id": "Badge", "rgb": [225, 80, 180], "next_room_id": "Archive"},
            ])

    def test_three_required_items_generate_distinct_verifiable_icons(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build_story_document(THREE_ITEMS.read_text(encoding="utf-8"), Path(tmp))
            source = (result.resource_directory / "Harbor.scc").read_text(encoding="utf-8")
            self.assertIn("getObjectOwner(Badge) == VAR_EGO", source)
            self.assertIn("getObjectOwner(Coin) == VAR_EGO", source)
            manifest = json.loads((result.resource_directory / "game-goal.json").read_text())
            self.assertEqual(manifest["fixture_inventory_gates"], [
                {"item_id": "Badge", "rgb": [225, 80, 180]},
                {"item_id": "Coin", "rgb": [160, 230, 55]},
            ])
            self.assertEqual((result.resource_directory / "inventory-ids.txt").read_text().strip(),
                             "Badge,Coin,Key")

    def test_round_trip_and_complete_export(self):
        story = parse_story_document(EXAMPLE.read_text(encoding="utf-8"))
        self.assertEqual(parse_story_document(canonical_story_json(story)), story)
        with tempfile.TemporaryDirectory() as tmp:
            result = build_story_document(canonical_story_json(story), Path(tmp))
            self.assertTrue(result.project_json.is_file())
            self.assertTrue((result.resource_directory / "Harbor.scc").exists())
            self.assertTrue((result.resource_directory / "Cellar.scc").exists())
            self.assertTrue((result.resource_directory / "Key.bmp").exists())
            self.assertTrue((result.resource_directory / "Inv_Key.bmp").exists())
            self.assertTrue((result.resource_directory / "DoorOpen.bmp").exists())
            self.assertTrue((result.resource_directory / "game-goal.json").exists())

    def test_invalid_input_never_creates_project_output(self):
        data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        cases = [
            lambda d: d.update({"scripts": ["injected"]}),
            lambda d: d.update({"format_version": 2}),
            lambda d: d["story"]["puzzles"][0].update({"requires": ["Unknown"]}),
            lambda d: d["story"]["items"][0].update({"role": "executable"}),
            lambda d: d["story"]["scenes"][0].update({"scene_script": "evil()"}),
        ]
        for mutate in cases:
            candidate = json.loads(json.dumps(data))
            mutate(candidate)
            with tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp) / "output"
                with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                    build_story_document(json.dumps(candidate), directory)
                self.assertFalse(directory.exists())

    def test_canonical_build_is_byte_reproducible(self):
        source = EXAMPLE.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first"
            second = Path(tmp) / "second"
            build_story_document(source, first)
            build_story_document(source, second)
            files = lambda base: {
                p.relative_to(base).as_posix(): p.read_bytes()
                for p in sorted(base.rglob("*")) if p.is_file()
            }
            self.assertEqual(files(first), files(second))


if __name__ == "__main__":
    unittest.main()
