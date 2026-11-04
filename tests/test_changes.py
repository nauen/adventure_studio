import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from adventure_studio.changes import DeleteAction, DeleteObject, PutAction, PutObject, apply_changes, report_dict
from adventure_studio.core import Action, Condition, Effect, Object
from adventure_studio.storage import from_bytes, load, save, to_bytes
from test_core import example


class ChangeTests(unittest.TestCase):
    def test_cascade_and_deterministic_diff(self):
        old = example()
        updated, report = apply_changes(old, (DeleteObject("pineapple"),
                                               PutObject(Object("cup", "Becher", "tavern", "decoration"))))
        self.assertEqual([c.id for c in report.changes], ["cup", "pineapple"])
        self.assertEqual([c.reason for c in report.changes], ["requested", "requested"])
        self.assertEqual(report.winning_path, ("open_fridge", "take_key", "unlock_door"))
        self.assertEqual(old.objects[1].id, "pineapple")
        second, report2 = apply_changes(updated, ())
        self.assertEqual(second, updated)
        self.assertEqual(report2.changes, ())
        self.assertEqual(report_dict(report)["changes"][0]["id"], "cup")

    def test_orphan_cleanup(self):
        project = replace(example(), objects=example().objects + (Object("leaf", "Blatt", "forest"),))
        result, report = apply_changes(project, ())
        self.assertEqual([c.id for c in report.changes], ["leaf", "pineapple"])
        self.assertTrue(all(c.reason == "consolidated" for c in report.changes))
        self.assertEqual([o.id for o in result.objects], ["key"])

    def test_required_object_preserves_optional_container(self):
        project = replace(example(), objects=(
            Object("fridge", "Kühlschrank", "tavern"), *example().objects))
        updated, _ = apply_changes(project, ())
        self.assertEqual([o.id for o in updated.objects], ["fridge", "key"])

    def test_invalid_operation_preserves_input(self):
        original = example()
        with self.assertRaisesRegex(ValueError, "Unsafe change"):
            apply_changes(original, (DeleteAction("take_key"),))
        self.assertEqual(original, example())

    def test_cascade_deletion_of_required_object_rejected(self):
        with self.assertRaises(ValueError):
            apply_changes(example(), (DeleteObject("key"),))

    def test_duplicate_operations_rejected(self):
        with self.assertRaisesRegex(ValueError, "Repeated"):
            apply_changes(example(), (DeleteObject("pineapple"), DeleteObject("pineapple")))

    def test_atomic_storage_and_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "game.json"
            revision = save(path, example(), None)
            stored, current = load(path)
            self.assertEqual(stored, example())
            self.assertEqual(current, revision)
            updated, _ = apply_changes(stored, (PutObject(Object("sign", "Schild", "tavern", "decoration")),))
            new_revision = save(path, updated, revision)
            self.assertNotEqual(revision, new_revision)
            original_bytes = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "revision conflict"):
                save(path, stored, revision)
            self.assertEqual(path.read_bytes(), original_bytes)

    def test_json_round_trip(self):
        self.assertEqual(from_bytes(to_bytes(example())), example())
        with self.assertRaises(ValueError):
            from_bytes(b'{"objects":[],"actions":[],"initial":[],"goals":[],"evil":true}')


if __name__ == "__main__":
    unittest.main()
