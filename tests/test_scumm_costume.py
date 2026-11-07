import unittest
import struct
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from adventure_studio.scumm_costume import (CostumeAnimation, CostumeDirection,
                                           CostumeFrame, costume_source,
                                           validate_costume, write_costume_sources)
from adventure_studio.scumm_costume_probe import gesture_fixture


class NativeCostumeTests(unittest.TestCase):
    def test_source_contains_explicit_count_command_and_native_animation(self):
        source = costume_source(gesture_fixture())
        self.assertIn("anim gesture @ 24", source)
        self.assertIn("body(Pose0, COUNT, Pose1, COUNT, Pose2) !LOOP", source)
        self.assertEqual(source.count("picture "), 3)

    def test_bmp_and_source_export(self):
        with TemporaryDirectory() as tmp:
            script, images = write_costume_sources(gesture_fixture(), Path(tmp))
            self.assertTrue(script.read_text().startswith("palette([16-47]);"))
            self.assertEqual(len(images), 3)
            self.assertTrue(all(path.read_bytes().startswith(b"BM") for path in images))
            self.assertTrue(all(struct.unpack_from("<I", path.read_bytes(), 46)[0] == 32
                                for path in images))

    def test_invalid_frames_and_native_commands_are_rejected(self):
        base = gesture_fixture()
        for changed in (
            replace(base, frames=()),
            replace(base, frames=base.frames + (base.frames[0],)),
            replace(base, frames=(replace(base.frames[0], pixels=b""),) + base.frames[1:]),
            replace(base, frames=(replace(base.frames[0], pixels=bytes([32]) * 384),) + base.frames[1:]),
            replace(base, animations=(replace(base.animations[1], index=23),)),
            replace(base, animations=(CostumeAnimation("bad", (CostumeDirection("S", ("Unknown",)),)),)),
            replace(base, animations=(CostumeAnimation("bad", (CostumeDirection("S", ("Pose0",)),
                                                             CostumeDirection("S", ("Pose1",)))),)),
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                validate_costume(changed)

