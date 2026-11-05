import unittest
from dataclasses import replace

from adventure_studio.story import Chapter, Character, Item, Puzzle, Recipe, Scene, Story, compile_story, validate_story, verify_story


def pirate_story() -> Story:
    return Story(
        chapters=(Chapter("first", "Die Insel", "Der Pirat sucht einen Ausgang"),),
        scenes=(Scene("tavern", "first", "Taverne", "Alte Kneipe mit kaputtem Kühlschrank"),
                Scene("shed", "first", "Schuppen", "Eine verschlossene Hütte")),
        characters=(Character("barkeep", "Wirt", "Misstrauisch", "tavern"),),
        items=(Item("key", "Schlüssel", "Rostig", "tavern"),
               Item("pineapple", "Ananas", "Verschimmelt", "tavern", "decoration")),
        puzzles=(Puzzle("unlock", "Öffne den Schuppen", "tavern", ("key",), "shed"),
                 Puzzle("escape", "Verlasse die Insel", "shed", ())),
        starting_scene_id="tavern", final_puzzle_id="escape",
    )


class StoryTests(unittest.TestCase):
    def test_story_compiles_and_solves(self):
        story = pirate_story()
        self.assertEqual(verify_story(story), ("take:key", "solve:unlock", "solve:escape"))
        project = compile_story(story)
        self.assertIn("puzzle.escape", dict(project.initial))
        self.assertEqual(len(project.actions), 3)

    def test_dangling_scene_reference_rejected(self):
        story = pirate_story()
        broken = replace(story, items=(replace(story.items[0], scene_id="ocean"), story.items[1]))
        with self.assertRaisesRegex(ValueError, "Unknown item scene"):
            validate_story(broken)

    def test_missing_required_item_rejected(self):
        story = pirate_story()
        broken = replace(story, items=(story.items[1],))
        with self.assertRaisesRegex(ValueError, "Missing pickup requirement"):
            verify_story(broken)

    def test_unreachable_chapter_goal_rejected(self):
        story = pirate_story()
        blocked = replace(story, puzzles=(Puzzle("unlock", "Tür", "shed", ("key",), "shed"), story.puzzles[1]))
        with self.assertRaisesRegex(ValueError, "Unplayable story"):
            verify_story(blocked)

    def test_flavor_item_not_forced_into_puzzle(self):
        story = pirate_story()
        self.assertFalse(any(a.id == "take:pineapple" for a in compile_story(story).actions))
        self.assertEqual(story.items[1].role, "decoration")

    def test_duplicate_item_id_rejected(self):
        story = pirate_story()
        with self.assertRaisesRegex(ValueError, "duplicated"):
            validate_story(replace(story, items=(story.items[0], story.items[0])))

    def test_recipe_cycle_and_unused_product_rejected(self):
        base = pirate_story()
        with self.assertRaisesRegex(ValueError, "result must be a crafted item"):
            validate_story(replace(base, recipes=(Recipe("bad", "Make", ("key", "pineapple"), "key"),)))
        crafted = Item("medicine", "Trank", "Ein Ergebnis", "tavern", "crafted")
        bottle = Item("bottle", "Flasche", "Leer", "tavern")
        with self.assertRaisesRegex(ValueError, "Unused crafted item"):
            validate_story(replace(base, items=base.items + (crafted, bottle),
                                   recipes=(Recipe("combine", "Make", ("key", "bottle"), "medicine"),)))


if __name__ == "__main__":
    unittest.main()
