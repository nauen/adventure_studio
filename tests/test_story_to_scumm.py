import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from adventure_studio.scumm_project import canonical_json, export_document, parse_document
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

    def test_unsupported_story_mechanics_fail_closed(self):
        story = small_story()
        with self.assertRaisesRegex(ValueError, "no custom actors"):
            from adventure_studio.story import Character
            compile_story_to_scumm(replace(story, characters=(Character("hero", "Held", "", "Tavern"),)))
        with self.assertRaisesRegex(ValueError, "Additional pickup"):
            compile_story_to_scumm(replace(story, items=story.items +
                                           (Item("Coin", "Münze", "Gold", "Tavern"),)))


if __name__ == "__main__":
    unittest.main()
