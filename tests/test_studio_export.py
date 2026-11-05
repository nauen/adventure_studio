import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from adventure_studio.studio_export import export_playable
from adventure_studio.story_document import parse_story_document
from test_scumm_toolchain import fake_upstream


SAMPLE = (Path(__file__).resolve().parents[1] / "examples/mini_story.json").read_text(encoding="utf-8")


class StudioExportTests(unittest.TestCase):
    def test_reproducible_playable_zip_and_unmodified_upstream(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake_upstream(root / "scummc")
            calls = []

            def fake_runner(args, **kwargs):
                calls.append(args)
                target = Path(args[args.index("-o") + 1])
                if args[0].endswith("/sld"):
                    target.with_suffix(".000").write_bytes(b"index")
                    target.with_suffix(".001").write_bytes(b"data")
                else:
                    target.write_bytes(b"compiled")

            first = export_playable(SAMPLE, root / "scummc", root / "first.zip", fake_runner)
            second = export_playable(SAMPLE, root / "scummc", root / "second.zip", fake_runner)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(len(calls), 8)
            self.assertFalse((root / "scummc/examples/road/Inv_Key.bmp").exists())
            with ZipFile(first) as archive:
                self.assertEqual(sorted(archive.namelist()),
                                 ["README.txt", "story.json", "tentacle.000", "tentacle.001"])
                self.assertEqual(parse_story_document(archive.read("story.json").decode("utf-8")),
                                 parse_story_document(SAMPLE))

    def test_invalid_input_and_existing_output_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake_upstream(root / "scummc")
            output = root / "game.zip"
            with self.assertRaises(ValueError):
                export_playable("{}", root / "scummc", output)
            self.assertFalse(output.exists())
            output.write_bytes(b"untouched")
            with self.assertRaisesRegex(ValueError, "already exists"):
                export_playable(SAMPLE, root / "scummc", output)
            self.assertEqual(output.read_bytes(), b"untouched")


if __name__ == "__main__":
    unittest.main()
