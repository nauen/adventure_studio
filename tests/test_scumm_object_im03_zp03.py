"""Independent IM03/ZP03 authoring and export contract."""
from dataclasses import replace
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from adventure_studio.scumm_assets import scrolling_fixture, destination_fixture, scummc_room_source, write_room_sources
from adventure_studio.scumm_project import GameDocument, canonical_json, parse_document
from adventure_studio.studio_sequences import import_object_third_image, import_object_zplane

@unittest.skipUnless(find_spec("PIL"), "PNG authoring requires Pillow")
class IM03ZP03Tests(unittest.TestCase):
    def test_independent_third_mask_roundtrip(self):
        from PIL import Image
        with TemporaryDirectory() as d:
            folder = Path(d)
            image, mask = folder/"image.png", folder/"mask.png"
            Image.new("RGB", (16,16), (70,130,190)).save(image)
            Image.new("L", (16,16), 255).save(mask)
            raw = canonical_json(GameDocument("IM03Mask3", (scrolling_fixture(), destination_fixture())))
            raw = import_object_third_image(raw, "Harbor", "Door", str(image))
            with self.assertRaises(ValueError):
                import_object_zplane(raw, "Harbor", "Door", str(mask), 3, 3)
            raw = import_object_zplane(raw, "Harbor", "Door", str(mask), 1, 1)
            Image.new("L", (16,16), 0).save(mask)
            for state in (2,3):
                raw = import_object_zplane(raw, "Harbor", "Door", str(mask), state, 1)
            with self.assertRaises(ValueError):
                import_object_zplane(raw, "Harbor", "Door", str(mask), 3, 3)
            raw = import_object_zplane(raw, "Harbor", "Door", str(mask), 3, 2)
            Image.new("L", (16,16), 255).save(mask)
            raw = import_object_zplane(raw, "Harbor", "Door", str(mask), 3, 3)
            doc = parse_document(raw)
            self.assertEqual(canonical_json(doc), raw)
            door = next(h for h in doc.rooms[0].hotspots if h.id == "Door")
            self.assertEqual(door.object_zplane_pixels, bytes([1])*256)
            self.assertEqual(door.open_object_zplane_pixels, bytes(256))
            self.assertEqual(door.third_object_zplane_pixels, bytes(256))
            self.assertEqual(door.third_object_zplane2_pixels, bytes(256))
            self.assertEqual(door.third_object_zplane3_pixels, bytes([1])*256)
            self.assertIn('"DoorThird.bmp", { "DoorThirdZ01.bmp", "DoorThirdZ02.bmp", "DoorThirdZ03.bmp" }',
                          scummc_room_source(doc.rooms[0]))
            write_room_sources(doc.rooms[0], folder)
            self.assertTrue((folder/"DoorThirdZ03.bmp").is_file())
            for layer in (4,5):
                with self.assertRaises(ValueError):
                    import_object_zplane(raw, "Harbor", "Door", str(mask), 3, layer)
            for bad in (replace(door, third_object_zplane2_pixels=None),
                        replace(door, third_object_zplane3_pixels=bytes([2])*256),
                        replace(door, third_object_zplane3_pixels=bytes(255))):
                room = replace(doc.rooms[0], hotspots=tuple(bad if h.id=="Door" else h
                                                          for h in doc.rooms[0].hotspots))
                with self.assertRaises(ValueError):
                    scummc_room_source(room)
