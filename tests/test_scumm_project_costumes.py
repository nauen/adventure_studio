"""Project-level native COST resources: typed JSON and deterministic export."""

import json
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from adventure_studio.scumm_costume_probe import gesture_fixture
from adventure_studio.scumm_project import GameDocument, canonical_json, export_document, parse_document
from adventure_studio.scumm_assets import destination_fixture, scrolling_fixture


class ProjectCostumeTests(unittest.TestCase):
    def document(self):
        return GameDocument("NativeAdventure", (scrolling_fixture(), destination_fixture()),
                            (gesture_fixture(),))

    def test_round_trip_preserves_count_frames_and_indices(self):
        game = self.document()
        encoded = canonical_json(game)
        self.assertEqual(parse_document(encoded), game)
        self.assertEqual(canonical_json(parse_document(encoded)), encoded)
        self.assertIn('"COUNT"', encoded)
        self.assertIn('"index":24', encoded)

    def test_exports_compiler_inputs_from_project_document(self):
        with TemporaryDirectory() as tmp:
            game = parse_document(canonical_json(self.document()))
            export_document(game, Path(tmp))
            script = (Path(tmp) / "NativeGesture.scost").read_text(encoding="utf-8")
            self.assertIn("anim gesture @ 24", script)
            self.assertEqual(len(list(Path(tmp).glob("NativeGesture_*.bmp"))), 3)

    def test_legacy_document_has_no_costume_field(self):
        game = self.document()
        legacy = GameDocument(game.id, game.rooms)
        self.assertNotIn("costumes", json.loads(canonical_json(legacy)))
        self.assertEqual(parse_document(canonical_json(legacy)), legacy)

    def test_rejects_duplicate_costumes_and_unknown_commands(self):
        game = self.document()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            canonical_json(replace(game, costumes=(game.costumes[0], game.costumes[0])))
        data = json.loads(canonical_json(game))
        data["costumes"][0]["animations"][0]["directions"][0]["commands"].append("NOT_A_FRAME")
        with self.assertRaisesRegex(ValueError, "Unknown native costume"):
            parse_document(json.dumps(data))

    def test_rejects_unknown_costume_fields(self):
        data = json.loads(canonical_json(self.document()))
        data["costumes"][0]["frames"][0]["runtime_script"] = "malicious()"
        with self.assertRaises(ValueError):
            parse_document(json.dumps(data))


if __name__ == "__main__":
    unittest.main()
