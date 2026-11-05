import tempfile
import json
import unittest
from dataclasses import replace
from pathlib import Path

from adventure_studio.scumm_project import canonical_json, export_document, parse_document
from adventure_studio.image_pipeline import FixtureImageProvider, IndexedImage
from adventure_studio.story import Chapter, Item, Puzzle, Scene, Story
from adventure_studio.story_to_scumm import compile_story_to_scumm


def small_story() -> Story:
    return Story(
        chapters=(Chapter("intro", "Insel", "Ein Ausweg muss gefunden werden."),),
        scenes=(Scene("Tavern", "intro", "Taverne", "Ein kaputter Kuehlschrank"),
                Scene("Shed", "intro", "Schuppen", "Ein sicherer Unterschlupf")),
        characters=(),
        items=(Item("Key", "Schlüssel", "Ein rostiger Schlüssel", "Tavern"),
               Item("Pineapple", "Ananas", "Verschimmelte Ananas", "Tavern", "decoration")),
        puzzles=(Puzzle("Unlock", "Öffne den Schuppen", "Tavern", ("Key",), "Shed"),),
        starting_scene_id="Tavern", final_puzzle_id="Unlock",
    )


class StoryToScummTests(unittest.TestCase):
    def test_default_provider_preserves_fixture_pixels_and_palette(self):
        game = compile_story_to_scumm(small_story())
        self.assertEqual(game.rooms[0].pixels[:2], bytes((0, 0)))
        self.assertEqual(game.rooms[0].pixels[320], 2)
        self.assertEqual(game.rooms[1].pixels[:2], bytes((6, 6)))
        self.assertEqual(game.rooms[0].palette[0], (70, 130, 190))

    def test_custom_provider_can_supply_room_images_without_new_build_path(self):
        current = compile_story_to_scumm(small_story())
        provider = FixtureImageProvider({
            f"scene-{room.name.lower()}-{'goal' if room.goal_text else 'main'}":
                IndexedImage(room.pixels, room.palette, room.geometry.room_width,
                             room.geometry.room_height, "cache:fixture-v1")
            for room in current.rooms
        })
        self.assertEqual(canonical_json(current),
                         canonical_json(compile_story_to_scumm(small_story(), provider)))

    def test_invalid_external_provider_dimensions_fail_before_scumm_export(self):
        sample = IndexedImage(b"\x00", ((0, 0, 0),), 1, 1, "cache:test")
        provider = FixtureImageProvider({"scene-tavern-main": sample})
        with self.assertRaisesRegex(ValueError, "dimensions disagree"):
            compile_story_to_scumm(small_story(), provider)

    def test_story_generates_complete_room_resources_and_goal(self):
        game = compile_story_to_scumm(small_story())
        self.assertEqual(tuple(r.name for r in game.rooms), ("Tavern", "Shed"))
        self.assertEqual(game.rooms[0].use_rules[0].item_id, "Key")
        self.assertEqual(game.rooms[0].use_rules[0].target_id, "Door")
        self.assertEqual(game.rooms[0].hotspots[0].id, "Pineapple")
        self.assertEqual(game.rooms[1].goal_text, "Offne den Schuppen")
        with tempfile.TemporaryDirectory() as tmp:
            game = parse_document(canonical_json(game))
            export_document(game, Path(tmp))
            self.assertIn("object Pineapple", (Path(tmp) / "Tavern.scc").read_text())
            self.assertIn("startRoom(Shed)", (Path(tmp) / "Tavern.scc").read_text())
            self.assertTrue((Path(tmp) / "game-goal.json").exists())

    def test_second_story_generates_different_resources(self):
        first = small_story()
        second = replace(first, chapters=(Chapter("seaside", "Hafen", "Neue Geschichte"),),
                         scenes=(replace(first.scenes[0], chapter_id="seaside", title="Altes Haus"),
                                 replace(first.scenes[1], chapter_id="seaside", title="Leuchtturm")),
                         items=(replace(first.items[0], name="Messingschlüssel"), first.items[1]))
        self.assertNotEqual(canonical_json(compile_story_to_scumm(first)),
                            canonical_json(compile_story_to_scumm(second)))

    def test_two_required_inventory_items_produce_guarded_use_rule(self):
        story = small_story()
        story = replace(story,
                        items=story.items + (Item("Badge", "Abzeichen", "Wichtig", "Tavern"),),
                        puzzles=(replace(story.puzzles[0], requires=("Key", "Badge")),))
        game = compile_story_to_scumm(story)
        self.assertEqual(game.rooms[0].use_rules[0].requires_inventory, ("Badge",))
        with tempfile.TemporaryDirectory() as tmp:
            export_document(game, Path(tmp))
            room_source = (Path(tmp) / "Tavern.scc").read_text(encoding="utf-8")
            self.assertIn("if(objB == Key && getObjectOwner(Badge) == VAR_EGO)", room_source)
            self.assertEqual((Path(tmp) / "inventory-ids.txt").read_text().strip(), "Badge,Key")
            self.assertTrue((Path(tmp) / "Inv_Badge.bmp").is_file())
            goal = json.loads((Path(tmp) / "game-goal.json").read_text())
            self.assertEqual(goal["fixture_inventory_gates"],
                             [{"item_id": "Badge", "rgb": [225, 80, 180]}])
            self.assertNotEqual(game.rooms[0].hotspots[1].sprite_pixels,
                                game.rooms[0].hotspots[2].sprite_pixels)

    def test_unsupported_story_mechanics_fail_closed(self):
        story = small_story()
        with self.assertRaisesRegex(ValueError, "no custom actors"):
            from adventure_studio.story import Character
            compile_story_to_scumm(replace(story, characters=(Character("hero", "Held", "", "Tavern"),)))
        with self.assertRaisesRegex(ValueError, "Unreferenced pickup"):
            compile_story_to_scumm(replace(story, items=story.items +
                                           (Item("Coin", "Münze", "Gold", "Tavern"),)))

    def test_branching_and_cross_room_pickups_fail_closed(self):
        from adventure_studio.story import verify_story
        story = small_story()
        extra = Puzzle("Other", "Another lock", "Tavern", ("Key",), "Shed")
        with self.assertRaisesRegex(ValueError, "unbranched route"):
            compile_story_to_scumm(replace(story, puzzles=story.puzzles + (extra,),
                                           scenes=story.scenes + (Scene("Final", "intro", "Final", "Final room"),)))
        other = Puzzle("Other", "Another lock", "Shed", ("Key",), "Final")
        with self.assertRaisesRegex(ValueError, "own scene"):
            compile_story_to_scumm(replace(story, puzzles=story.puzzles + (other,),
                                           scenes=story.scenes + (Scene("Final", "intro", "Final", "Final room"),),
                                           final_puzzle_id="Other"))


if __name__ == "__main__":
    unittest.main()
