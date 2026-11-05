import unittest
import tempfile
from pathlib import Path

from adventure_studio.scumm_bootstrap import inject_inventory_declarations, inject_inventory_objects, read_icon_ids, retarget_upstream_bootstrap


class BootstrapTests(unittest.TestCase):
    def test_inventory_ids_can_be_read_from_generated_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "inventory-ids.txt"
            manifest.write_text("Badge,Key\n", encoding="ascii")
            self.assertEqual(read_icon_ids(f"@{manifest}"), ("Badge", "Key"))
            self.assertEqual(read_icon_ids(""), ())
            with self.assertRaisesRegex(ValueError, "duplicated"):
                read_icon_ids("Key,Key")
    def test_inventory_resource_is_declared_and_injected(self):
        source = 'room ResRoom {\n    // the inventory icons\n    object axe {}\n}'
        header = 'room ResRoom {\n    // Inventory objects\n    object axe;\n}'
        self.assertIn('states = { { 0, 0, "Inv_Key.bmp" } };', inject_inventory_objects(source, ('Key',)))
        self.assertIn('object KeyIcon;', inject_inventory_declarations(header, ('Key',)))

    def test_inventory_patch_rejects_unknown_layout_and_names(self):
        with self.assertRaisesRegex(ValueError, 'upstream inventory layout'):
            inject_inventory_objects('room ResRoom {}', ('Key',))
        with self.assertRaisesRegex(ValueError, 'identifier'):
            inject_inventory_objects('    // the inventory icons\n', ('Bad;code',))
    def test_retarget_without_touching_other_logic(self):
        source = "room Road;\nloadRoom(Road);\nlockRoom(Road);\nstartRoom(Road);\nint untouched;\n"
        result = retarget_upstream_bootstrap(source, "Harbor")
        self.assertIn("startRoom(Harbor);", result)
        self.assertIn("int untouched;", result)
        self.assertNotIn("Road", result)

    def test_upstream_drift_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Unexpected upstream"):
            retarget_upstream_bootstrap("room Road;", "Harbor")

    def test_invalid_name_rejected(self):
        with self.assertRaisesRegex(ValueError, "Invalid room"):
            retarget_upstream_bootstrap("", "Harbor); evil()")


if __name__ == "__main__":
    unittest.main()
