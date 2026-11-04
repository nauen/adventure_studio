import unittest

from adventure_studio.scumm_bootstrap import retarget_upstream_bootstrap


class BootstrapTests(unittest.TestCase):
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
