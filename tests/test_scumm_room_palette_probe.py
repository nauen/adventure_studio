"""Deterministic checks for native room palette verification."""
import tempfile
import unittest
from importlib.util import find_spec
from pathlib import Path

from adventure_studio.scumm_room_palette_probe import (
    authored_palette_room, room_palette_256, verify_palette_screenshot,
    _sample_location,
)


class NativeRoomPaletteTests(unittest.TestCase):
    def test_room_uses_all_256_unique_palette_entries(self):
        room = authored_palette_room()
        self.assertEqual(len(room.palette), 256)
        self.assertEqual(len(set(room.palette)), 256)
        minimum_distance = min(
            max(abs(a - b) for a, b in zip(room.palette[left], room.palette[right]))
            for left in range(256) for right in range(left + 1, 256)
        )
        self.assertGreater(minimum_distance, 24)
        width = room.geometry.room_width
        grid_pixels = {
            room.pixels[(16 + row * 8 + y) * width + 16 + column * 8 + x]
            for row in range(16) for column in range(16)
            for y in range(8) for x in range(8)
        }
        self.assertEqual(grid_pixels, set(range(256)))

    def test_swapped_and_duplicate_palette_controls_change_native_pixels(self):
        expected = room_palette_256()
        swapped = authored_palette_room("swapped")
        duplicate = authored_palette_room("duplicate")
        self.assertNotEqual(swapped.palette[16], expected[16])
        self.assertEqual(duplicate.palette[255], duplicate.palette[254])

    @unittest.skipUnless(find_spec("PIL"), "Native screenshot verification requires Pillow")
    def test_screenshot_verifier_accepts_all_256_and_rejects_bad_mapping(self):
        from PIL import Image
        expected = room_palette_256()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "palette.png"
            image = Image.new("RGB", (1024, 768), (0, 0, 0))
            for index, rgb in enumerate(expected):
                quantized = tuple(max(0, channel - 7) for channel in rgb)
                for ox, oy in ((2, 2), (4, 4), (6, 6)):
                    image.putpixel(_sample_location(index, ox, oy), quantized)
            image.save(path)
            result = verify_palette_screenshot(path, expected)
            self.assertEqual(result["verified_indices"], 256)
            image.putpixel(_sample_location(17, 2, 2), expected[16])
            image.putpixel(_sample_location(17, 4, 4), expected[16])
            image.save(path)
            with self.assertRaisesRegex(RuntimeError, "palette mismatch"):
                verify_palette_screenshot(path, expected)
