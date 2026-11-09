import unittest
from dataclasses import replace

from adventure_studio.story import Item, Puzzle, Recipe
from adventure_studio.story_changes import DeleteEntity, PutEntity, edit_story
from test_story import pirate_story


class StoryChangeTests(unittest.TestCase):
    def test_orphan_pickup_is_removed_and_shown_in_consolidation_report(self):
        original = pirate_story()
        changed, report = edit_story(original, (
            PutEntity("item", Item("old_pineapple", "Ananas", "Alt", "tavern")),
        ))
        self.assertEqual(changed, original)
        self.assertEqual(report.consolidated, ("old_pineapple",))
        self.assertEqual(report.changes, ())
        self.assertEqual(original.items[1].id, "pineapple")  # Decorations are retained.

    def test_recipe_addition_and_removal_requires_consistent_atomic_edits(self):
        original = pirate_story()
        with self.assertRaisesRegex(ValueError, "Recipe"):
            edit_story(original, (PutEntity("recipe", Recipe("Mix", "Mischen", ("key", "bottle"), "mixture")),))
        revised, report = edit_story(original, (
            PutEntity("item", Item("bottle", "Flasche", "Leer", "tavern")),
            PutEntity("item", Item("mixture", "Trank", "Gemischt", "tavern", "crafted")),
            PutEntity("recipe", Recipe("Mix", "Mischen", ("key", "bottle"), "mixture")),
            PutEntity("puzzle", replace(original.puzzles[0], requires=("mixture",))),
        ))
        self.assertEqual(report.playable_path,
                         ("take:key", "take:bottle", "combine:Mix", "solve:unlock", "solve:escape"))
        self.assertIn(("recipe", "Mix"), [(change.kind, change.id) for change in report.changes])
        with self.assertRaisesRegex(ValueError, "Missing pickup requirement"):
            edit_story(revised, (DeleteEntity("item", "mixture"),))

    def test_add_and_remove_unneeded_story_detail(self):
        original = pirate_story()
        added, report = edit_story(original, (PutEntity("item", Item("cup", "Tasse", "Zerbrochen", "tavern", "decoration")),))
        self.assertEqual([(d.kind, d.id) for d in report.changes], [("item", "cup")])
        self.assertEqual(len(added.items), 3)
        cleaned, report = edit_story(added, (DeleteEntity("item", "cup"),))
        self.assertEqual(cleaned, original)
        self.assertIsNone(report.changes[0].after)

    def test_referenced_item_requires_explicit_puzzle_repair(self):
        original = pirate_story()
        with self.assertRaisesRegex(ValueError, "Missing pickup requirement"):
            edit_story(original, (DeleteEntity("item", "key"),))
        revised, report = edit_story(original, (
            PutEntity("item", Item("rum", "Rum", "Flasche", "tavern")),
            PutEntity("puzzle", replace(original.puzzles[0], requires=("rum",))),
            DeleteEntity("item", "key"),
        ))
        self.assertEqual(report.playable_path, ("take:rum", "solve:unlock", "solve:escape"))
        self.assertEqual([d.id for d in report.changes], ["key", "rum", "unlock"])
        self.assertEqual(original.items[0].id, "key")

    def test_duplicate_edits_rejected(self):
        with self.assertRaisesRegex(ValueError, "repeated operation"):
            edit_story(pirate_story(), (DeleteEntity("item", "pineapple"), DeleteEntity("item", "pineapple")))

    def test_wrong_kind_rejected(self):
        with self.assertRaisesRegex(ValueError, "Wrong entity type"):
            edit_story(pirate_story(), (PutEntity("scene", pirate_story().items[0]),))


if __name__ == "__main__":
    unittest.main()
