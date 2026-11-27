"""Synthetic measurement contracts only; ScummVM CI supplies the actual evidence."""
import unittest
from importlib.util import find_spec


@unittest.skipUnless(find_spec("PIL"), "Pixel measurement requires Pillow")
class NativeStandPosePixelTests(unittest.TestCase):
    def test_sparse_ego_palette_pixels_do_not_change_pose(self):
        from PIL import Image, ImageDraw
        from adventure_studio.scumm_actor_stand_animation_probe import COLORS, measure_pose
        lane = Image.new("RGB", (640, 85), (70,130,190))
        draw = ImageDraw.Draw(lane)
        draw.rectangle((224,28,255,75), fill=COLORS[0])
        draw.rectangle((310,68,319,69), fill=COLORS[0])
        draw.rectangle((318,70,319,71), fill=COLORS[1])
        draw.rectangle((302,80,329,84), fill=COLORS[2])
        self.assertEqual(measure_pose(lane), (239.5, [1536,0,0]))
        draw.rectangle((224,28,255,75), fill=COLORS[1])
        self.assertEqual(measure_pose(lane), (239.5, [0,1536,0]))

    def test_missing_and_ambiguous_costumes_fail_closed(self):
        from PIL import Image, ImageDraw
        from adventure_studio.scumm_actor_stand_animation_probe import COLORS, measure_pose
        lane = Image.new("RGB", (640,85))
        self.assertIsNone(measure_pose(lane)[0])
        draw = ImageDraw.Draw(lane)
        draw.rectangle((224,28,255,75), fill=COLORS[0])
        draw.rectangle((320,28,351,75), fill=COLORS[1])
        self.assertIsNone(measure_pose(lane)[0])
