"""Pixel detector contract for the native walk-stop probe; not gameplay proof."""
import unittest
from importlib.util import find_spec


@unittest.skipUnless(find_spec("PIL"), "Pixel measurement requires Pillow")
class NativeActorStopPixelTests(unittest.TestCase):
    def test_sparse_same_palette_ego_does_not_shift_costume_center(self):
        from PIL import Image, ImageDraw
        from adventure_studio.scumm_actor_stop_probe import ACTOR, costume_block_center
        scene = Image.new("RGB", (640, 85), (65, 129, 189))
        draw = ImageDraw.Draw(scene)
        quantized = (246, 36, 115)
        draw.rectangle((24, 28, 55, 75), fill=quantized)
        draw.rectangle((360, 46, 361, 47), fill=quantized)
        draw.rectangle((375, 80, 389, 84), fill=quantized)
        self.assertEqual(costume_block_center(scene, ACTOR), 39.5)
        draw.rectangle((400, 28, 431, 75), fill=quantized)
        self.assertIsNone(costume_block_center(scene, ACTOR))

    def test_missing_costume_does_not_pass(self):
        from PIL import Image
        from adventure_studio.scumm_actor_stop_probe import ACTOR, costume_block_center
        self.assertIsNone(costume_block_center(Image.new("RGB", (640, 85)), ACTOR))
