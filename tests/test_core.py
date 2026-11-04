import unittest
from dataclasses import replace

from adventure_studio.core import Action, Condition, Effect, Object, Project, analyze, consolidate, execute, propose


def example() -> Project:
    return Project(
        objects=(Object("key", "Schlüssel", "fridge", "required"), Object("pineapple", "Ananas", "fridge")),
        actions=(
            Action("open_fridge", "Kühlschrank öffnen", (), (Effect("fridge.open", True),)),
            Action("take_key", "Schlüssel nehmen", (Condition("fridge.open"),), (Effect("key.owned", True),)),
            Action("unlock_door", "Tür öffnen", (Condition("key.owned"),), (Effect("door.open", True),)),
        ),
        initial=(("fridge.open", False), ("key.owned", False), ("door.open", False)),
        goals=(Condition("door.open"),),
    )


class CoreTests(unittest.TestCase):
    def test_solution_and_consolidation(self):
        project = example()
        self.assertEqual(analyze(project).winning_path, ("open_fridge", "take_key", "unlock_door"))
        cleaned, removed = consolidate(project)
        self.assertEqual(removed, ("pineapple",))
        self.assertEqual(consolidate(cleaned), (cleaned, ()))

    def test_unavailable_action_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unavailable"):
            execute(example(), example().initial, "take_key")

    def test_broken_proposal_is_rejected_and_original_is_unchanged(self):
        original = example()
        broken = replace(original, actions=tuple(a for a in original.actions if a.id != "take_key"))
        with self.assertRaisesRegex(ValueError, "Invalid proposal"):
            propose(original, broken)
        self.assertTrue(analyze(original).solvable)

    def test_change_report(self):
        original = example()
        candidate = replace(original, objects=original.objects + (Object("cup", "Becher", "tavern", "decoration"),))
        updated, report = propose(original, candidate)
        self.assertEqual(report["added"], ["cup"])
        self.assertEqual(report["removed"], ["pineapple"])
        self.assertEqual([obj.id for obj in updated.objects], ["key", "cup"])

    def test_unknown_key_is_invalid(self):
        project = replace(example(), goals=(Condition("missing.flag"),))
        with self.assertRaisesRegex(ValueError, "Unknown state key"):
            analyze(project)

    def test_unwinnable_loop_is_dead_end(self):
        original = example()
        candidate = replace(original, actions=(
            Action("toggle_open", "Öffnen", (), (Effect("fridge.open", True),)),
            Action("toggle_closed", "Schließen", (Condition("fridge.open"),), (Effect("fridge.open", False),)),
        ))
        analysis = analyze(candidate)
        self.assertFalse(analysis.solvable)
        self.assertEqual(analysis.dead_ends, analysis.explored_states)


if __name__ == "__main__":
    unittest.main()
