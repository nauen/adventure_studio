"""Readiness guard for the native IM03 probe, not gameplay evidence."""
import unittest
from importlib.util import find_spec


@unittest.skipUnless(find_spec("PIL"), "Pixel measurement requires Pillow")
class NativeIM03ReadinessTests(unittest.TestCase):
    def test_partial_room_entry_is_not_an_interactive_scene(self):
        from PIL import Image, ImageDraw
        from adventure_studio.scumm_object_third_image_probe import native_verbs_visible
        image = Image.new("RGB", (1024, 768))
        draw = ImageDraw.Draw(image)
        draw.rectangle((192,184,831,471), fill=(65,129,189))
        draw.rectangle((704,334,767,375), fill=(246,32,123))
        self.assertFalse(native_verbs_visible(image))
        draw.rectangle((204,540,264,556), fill=(255,220,75))
        self.assertTrue(native_verbs_visible(image))

    def test_wrong_viewport_is_not_accepted(self):
        from PIL import Image
        from adventure_studio.scumm_object_third_image_probe import native_verbs_visible
        self.assertFalse(native_verbs_visible(Image.new("RGB",(640,480),(255,255,255))))
