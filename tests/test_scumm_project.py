"""Deterministic document-to-SCUMM adapter tests."""

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from adventure_studio.scumm_assets import destination_fixture, scrolling_fixture
from adventure_studio.scumm_project import GameDocument, canonical_json, export_document, parse_document


def files_at(directory: Path) -> dict[str, bytes]:
    return {p.relative_to(directory).as_posix(): p.read_bytes()
            for p in sorted(directory.rglob("*")) if p.is_file()}


class ScummProjectTests(unittest.TestCase):
    def setUp(self):
        self.game = GameDocument("HarborAdventure", (scrolling_fixture(), destination_fixture()))

    def test_round_trip_is_canonical_and_lossless(self):
        encoded = canonical_json(self.game)
        self.assertEqual(parse_document(encoded), self.game)
        self.assertEqual(canonical_json(parse_document(encoded)), encoded)
        self.assertIn('"format_version":1', encoded)

    def test_two_different_projects_compile_without_project_script_code(self):
        original = self.game
        alternate = GameDocument("AnotherAdventure", (
            replace(scrolling_fixture(), name="Beach",
                    hotspots=tuple(replace(h, exit_destination="Basement") if h.id == "Door" else h
                                   for h in scrolling_fixture().hotspots)),
            replace(destination_fixture(), name="Basement",
                    hotspots=tuple(replace(h, exit_destination="Beach") for h in destination_fixture().hotspots)),
        ))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b, c = root / "a", root / "b", root / "c"
            export_document(parse_document(canonical_json(original)), a)
            export_document(parse_document(canonical_json(original)), b)
            export_document(parse_document(canonical_json(alternate)), c)
            self.assertEqual(files_at(a), files_at(b))
            self.assertNotEqual(files_at(a), files_at(c))
            self.assertIn("Cellar.scc", files_at(a))
            self.assertIn("Basement.scc", files_at(c))

    def test_unknown_fields_and_version_fail_closed(self):
        data = json.loads(canonical_json(self.game))
        for edit in (
            lambda d: d.update({"execute": "rm -rf anything"}),
            lambda d: d.update({"format_version": 99}),
            lambda d: d.update({"id": 123}),
            lambda d: d["rooms"][0]["geometry"].update({"width": "640"}),
            lambda d: d["rooms"][0].update({"script": "startRoom(Evil)"}),
            lambda d: d["rooms"][0]["hotspots"][0].update({"script": "evil()"}),
            lambda d: d["rooms"][0].update({"pixels": "!!!"}),
        ):
            candidate = json.loads(json.dumps(data))
            edit(candidate)
            with self.subTest(candidate=list(candidate)), self.assertRaises(ValueError):
                parse_document(json.dumps(candidate))

    def test_cross_room_references_checked_before_output(self):
        data = json.loads(canonical_json(self.game))
        data["rooms"].pop()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "compiled"
            with self.assertRaisesRegex(ValueError, "Unknown exit destination"):
                export_document(parse_document(json.dumps(data)), out)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
