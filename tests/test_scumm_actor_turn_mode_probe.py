"""Synthetic measurement regression tests; native CI provides gameplay proof."""
import unittest
from importlib.util import find_spec


@unittest.skipUnless(find_spec("PIL"), "Pixel measurement requires Pillow")
class NativeTurnModePixelTests(unittest.TestCase):
    def test_sparse_ego_palette_pixels_do_not_change_native_direction(self):
        from PIL import Image, ImageDraw
        from adventure_studio.scumm_actor_turn_mode_probe import COLORS, measure_direction
        lane = Image.new("RGB", (640,85), (70,130,190))
        draw = ImageDraw.Draw(lane)
        draw.rectangle((224,28,255,75), fill=COLORS[2])
        for i, count in enumerate((20,4,60,24)):
            draw.rectangle((310+i*35,80,310+i*35+count//4-1,83), fill=COLORS[i])
        self.assertEqual(measure_direction(lane), (239.5,[0,0,1536,0]))
        draw.rectangle((224,28,255,75), fill=COLORS[1])
        self.assertEqual(measure_direction(lane), (239.5,[0,1536,0,0]))

    def test_ambiguous_and_missing_costumes_do_not_pass(self):
        from PIL import Image, ImageDraw
        from adventure_studio.scumm_actor_turn_mode_probe import COLORS, measure_direction
        lane = Image.new("RGB", (640,85))
        self.assertIsNone(measure_direction(lane)[0])
        draw = ImageDraw.Draw(lane)
        draw.rectangle((224,28,255,75), fill=COLORS[2])
        draw.rectangle((320,28,351,75), fill=COLORS[1])
        self.assertIsNone(measure_direction(lane)[0])
