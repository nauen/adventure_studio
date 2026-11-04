import unittest
from dataclasses import replace

from adventure_studio.story import Item, Puzzle
from adventure_studio.story_changes import DeleteEntity, PutEntity, edit_story
from test_story import pirate_story


class StoryChangeTests(unittest.TestCase):
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
