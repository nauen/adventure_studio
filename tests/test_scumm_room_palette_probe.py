"""Deterministic checks for native room palette verification."""
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from adventure_studio.scumm_room_palette_probe import (
    authored_palette_room, room_palette_256, verify_palette_screenshot,
    _sample_location,
)


class NativeRoomPaletteTests(unittest.TestCase):
    def test_room_uses_all_256_unique_palette_entries(self):
        room = authored_palette_room()
        self.assertEqual(len(room.palette), 256)
        self.assertEqual(len(set(room.palette)), 256)
        self.assertEqual(set(room.pixels[16 * room.geometry.room_width + 16:
                                        16 * room.geometry.room_width + 16 + 128]),
                         set(range(16)))

    def test_swapped_and_duplicate_palette_controls_change_native_pixels(self):
        expected = room_palette_256()
        swapped = authored_palette_room("swapped")
        duplicate = authored_palette_room("duplicate")
        self.assertNotEqual(swapped.palette[16], expected[16])
        self.assertEqual(duplicate.palette[255], duplicate.palette[254])

    def test_screenshot_verifier_accepts_all_256_and_rejects_bad_mapping(self):
        expected = room_palette_256()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "palette.png"
            image = Image.new("RGB", (1024, 768), (0, 0, 0))
            for index, rgb in enumerate(expected):
                for ox, oy in ((2, 2), (4, 4), (6, 6)):
                    image.putpixel(_sample_location(index, ox, oy), rgb)
            image.save(path)
            result = verify_palette_screenshot(path, expected)
            self.assertEqual(result["verified_indices"], 256)
            image.putpixel(_sample_location(17, 4, 4), expected[16])
            image.save(path)
            with self.assertRaisesRegex(RuntimeError, "palette mismatch"):
                verify_palette_screenshot(path, expected)
