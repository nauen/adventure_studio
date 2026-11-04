import struct
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from adventure_studio.scumm_assets import indexed_bmp, scrolling_fixture, scummc_room_source, write_room_sources


class ScummAssetsTests(unittest.TestCase):
    def test_indexed_bmp_header_and_scroll_width(self):
        bmp = indexed_bmp(scrolling_fixture())
        self.assertEqual(bmp[:2], b"BM")
        self.assertEqual(struct.unpack_from("<ii", bmp, 18), (640, 200))
        self.assertEqual(struct.unpack_from("<H", bmp, 28)[0], 8)
        self.assertEqual(len(bmp), struct.unpack_from("<I", bmp, 2)[0])

    def test_scummc_room_source(self):
        self.assertEqual(scummc_room_source(scrolling_fixture()),
                         '#include <scummVars6.s>\n\nroom Harbor {\n    image = "Harbor.bmp";\n}\n')

    def test_generated_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            bmp, scc = write_room_sources(scrolling_fixture(), Path(tmp))
            self.assertGreater(bmp.stat().st_size, 128_000)
            self.assertIn("room Harbor", scc.read_text(encoding="utf-8"))

    def test_rejects_invalid_dimensions_and_names(self):
        room = scrolling_fixture()
        with self.assertRaisesRegex(ValueError, "identifier"):
            indexed_bmp(replace(room, name='x"; evil()'))
        with self.assertRaisesRegex(ValueError, "Pixel buffer"):
            indexed_bmp(replace(room, pixels=b""))
        with self.assertRaisesRegex(ValueError, "palette"):
            indexed_bmp(replace(room, palette=((1, 2, 3),)))


if __name__ == "__main__":
    unittest.main()
