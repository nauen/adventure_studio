import unittest

from adventure_studio.targets import DEFAULT_TARGET, DOS_TARGET, RoomGeometry, SCUMMVM_TARGET, export_ready, validate_geometry


class TargetTests(unittest.TestCase):
    def test_scumm_vm_is_default(self):
        self.assertEqual(DEFAULT_TARGET, SCUMMVM_TARGET)
        self.assertEqual(DEFAULT_TARGET.format, "scumm-v6")
        self.assertEqual(DEFAULT_TARGET.runtime, "scummvm")

    def test_scrolling_room_is_valid_geometry(self):
        validate_geometry(RoomGeometry(640, 200, 320, 200))

    def test_invalid_viewport(self):
        with self.assertRaisesRegex(ValueError, "Viewport cannot"):
            validate_geometry(RoomGeometry(160, 200, 320, 200))
        with self.assertRaisesRegex(ValueError, "incompatible"):
            validate_geometry(RoomGeometry(640, 200, 640, 200))

    def test_no_unverified_export_claim(self):
        for target in (SCUMMVM_TARGET, DOS_TARGET):
            with self.assertRaisesRegex(RuntimeError, "not integration-tested"):
                export_ready(target)


if __name__ == "__main__":
    unittest.main()
