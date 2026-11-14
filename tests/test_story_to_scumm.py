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
        from adventure_studio.story import Character
        game = compile_story_to_scumm(replace(
            story, characters=(Character("hero", "Held", "Steht im Raum", "Tavern"),)))
        self.assertEqual(next(h.id for h in game.rooms[0].hotspots if h.id == "hero"), "hero")
        with self.assertRaisesRegex(ValueError, "Story text"):
            compile_story_to_scumm(replace(
                story, characters=(Character("hero", "Held", "", "Tavern"),)))
        with self.assertRaisesRegex(ValueError, "Unreferenced pickup"):
            compile_story_to_scumm(replace(story, items=story.items +
                                           (Item("Coin", "Münze", "Gold", "Tavern"),)))

    def test_r09_story_owns_two_independent_local_gate_targets(self):
        from adventure_studio.story_document import canonical_story_json
        from adventure_studio.studio_sequences import (
            author_room_box_connections, author_room_walkbox,
            author_room_walkbox_gate, compose_story_project,
        )
        from adventure_studio.scumm_assets import scummc_room_source

        story = small_story()
        story = replace(
            story,
            items=story.items + (Item("LatchKey", "Riegelschluessel",
                                      "Oeffnet die Nebentuer", "Tavern"),),
            puzzles=story.puzzles + (
                Puzzle("Side", "Nebentuer oeffnen", "Tavern", ("LatchKey",), None),),
        )
        story_raw = canonical_story_json(story)
        original = compile_story_to_scumm(story)
        self.assertEqual(
            [(rule.item_id, rule.target_id) for rule in original.rooms[0].use_rules],
            [("Key", "Door"), ("LatchKey", "DoorLocalSide")],
        )
        raw = canonical_json(original)
        for box, corners in (
            (1, "0,70; 110,70; 110,150; 0,150"),
            (2, "110,70; 240,70; 240,108; 110,108"),
            (3, "110,112; 240,112; 240,150; 110,150"),
            (4, "240,70; 639,70; 639,150; 240,150"),
        ):
            raw = author_room_walkbox(raw, "Tavern", box, corners)
        raw = author_room_box_connections(raw, "Tavern",
                                          "1-2; 2-4; 1-3; 3-4")
        raw = author_room_walkbox_gate(raw, "Tavern", "Door", 2, reversible=True)
        raw = author_room_walkbox_gate(raw, "Tavern", "DoorLocalSide", 3, reversible=True)
        composed = parse_document(compose_story_project(story_raw, raw))
        room = composed.rooms[0]
        self.assertEqual(
            [(rule.target_id, rule.unlock_walkbox, rule.reversible_walkbox)
             for rule in room.use_rules],
            [("Door", 2, True), ("DoorLocalSide", 3, True)],
        )
        self.assertEqual(parse_document(canonical_json(composed)), composed)
        source = scummc_room_source(room)
        self.assertIn("getObjectState(DoorLocalSide)", source)
        self.assertIn("setBoxFlags([2],128);", source)
        self.assertIn("setBoxFlags([3],128);", source)
        with tempfile.TemporaryDirectory() as directory:
            export_document(composed, Path(directory))
            self.assertTrue((Path(directory) / "Tavern.scc").is_file())

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
