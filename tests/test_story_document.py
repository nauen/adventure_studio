"""The complete story JSON -> project -> SCUMM source-asset contract."""

import json
import tempfile
import unittest
from pathlib import Path

from adventure_studio.story_document import (
    build_story_document, canonical_story_json, parse_story_document,
)


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "mini_story.json"


class StoryDocumentTests(unittest.TestCase):
    def test_round_trip_and_complete_export(self):
        story = parse_story_document(EXAMPLE.read_text(encoding="utf-8"))
        self.assertEqual(parse_story_document(canonical_story_json(story)), story)
        with tempfile.TemporaryDirectory() as tmp:
            result = build_story_document(canonical_story_json(story), Path(tmp))
            self.assertTrue(result.project_json.is_file())
            self.assertTrue((result.resource_directory / "Harbor.scc").exists())
            self.assertTrue((result.resource_directory / "Cellar.scc").exists())
            self.assertTrue((result.resource_directory / "Key.bmp").exists())
            self.assertTrue((result.resource_directory / "Inv_Key.bmp").exists())
            self.assertTrue((result.resource_directory / "DoorOpen.bmp").exists())
            self.assertTrue((result.resource_directory / "game-goal.json").exists())

    def test_invalid_input_never_creates_project_output(self):
        data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        cases = [
            lambda d: d.update({"scripts": ["injected"]}),
            lambda d: d.update({"format_version": 2}),
            lambda d: d["story"]["puzzles"][0].update({"requires": ["Unknown"]}),
            lambda d: d["story"]["items"][0].update({"role": "executable"}),
            lambda d: d["story"]["scenes"][0].update({"scene_script": "evil()"}),
        ]
        for mutate in cases:
            candidate = json.loads(json.dumps(data))
            mutate(candidate)
            with tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp) / "output"
                with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                    build_story_document(json.dumps(candidate), directory)
                self.assertFalse(directory.exists())

    def test_canonical_build_is_byte_reproducible(self):
        source = EXAMPLE.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first"
            second = Path(tmp) / "second"
            build_story_document(source, first)
            build_story_document(source, second)
            files = lambda base: {
                p.relative_to(base).as_posix(): p.read_bytes()
                for p in sorted(base.rglob("*")) if p.is_file()
            }
            self.assertEqual(files(first), files(second))


if __name__ == "__main__":
    unittest.main()
