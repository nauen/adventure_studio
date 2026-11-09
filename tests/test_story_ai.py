import json
import unittest
from pathlib import Path

from adventure_studio.story_ai import (preview_ai_response, proposal_messages,
                                       propose_story_change)
from adventure_studio.studio_service import accept_proposal, report_text
from adventure_studio.story_document import parse_story_document


SAMPLE = (Path(__file__).resolve().parents[1] / "examples/mini_story_chain.json").read_text(encoding="utf-8")


class StoryAITests(unittest.TestCase):
    def test_prompt_contains_canonical_story_and_request(self):
        system, user = proposal_messages(SAMPLE, "Ein Kühlschrank steht links")
        self.assertIn("operations", system)
        data = json.loads(user)
        self.assertEqual(data["request"], "Ein Kühlschrank steht links")
        self.assertIn("scenes", data["story"]["story"])

    def test_preview_adds_fridge_and_position_without_committing(self):
        operations = json.dumps({"operations": [
            {"op": "put", "kind": "item", "entity": {
                "id": "Fridge", "name": "Kaputter Kühlschrank", "description": "Leer",
                "scene_id": "Harbor", "role": "decoration"}},
            {"op": "put", "kind": "placement", "entity": {
                "item_id": "Fridge", "x": 34, "y": 108}},
        ]})
        calls = []

        def fake_provider(system, user):
            calls.append(json.loads(user)["request"])
            return operations

        proposal = propose_story_change(SAMPLE, "Füge Kühlschrank hinzu", fake_provider)
        self.assertEqual(calls, ["Füge Kühlschrank hinzu"])
        self.assertNotIn("Fridge", {i.id for i in parse_story_document(SAMPLE).items})
        updated = parse_story_document(accept_proposal(SAMPLE, proposal))
        self.assertEqual(next(p for p in updated.placements if p.item_id == "Fridge").x, 34)
        self.assertIn("hinzugefügt: item Fridge", report_text(proposal.edit.report))
        self.assertIn("hinzugefügt: placement Fridge", report_text(proposal.edit.report))

    def test_invalid_proposal_is_never_accepted(self):
        for text in (
            '{"operations":[{"op":"put","kind":"unknown","entity":{}}]}',
            '{"operations":[{"op":"put","kind":"placement","entity":{"item_id":"Key","x":true,"y":0}}]}',
            '{"operations":[{"op":"put","kind":"placement","entity":{"item_id":"NoSuchItem","x":10,"y":10}}]}',
            '{"operations":[]}',
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                preview_ai_response(SAMPLE, text)

    def test_input_bounding_and_stale_preview(self):
        with self.assertRaisesRegex(ValueError, "8000"):
            proposal_messages(SAMPLE, "x" * 8001)
        with self.assertRaises(ValueError):
            propose_story_change(SAMPLE, " ", lambda *_: '{"operations":[]}')
        proposal = preview_ai_response(SAMPLE, json.dumps({"operations": [
            {"op": "put", "kind": "item", "entity": {
                "id": "Fridge", "name": "Kühlschrank", "description": "Kaputt",
                "scene_id": "Harbor", "role": "decoration"}}
        ]}))
        with self.assertRaisesRegex(ValueError, "changed since preview"):
            accept_proposal(proposal.edit.story_json, proposal)


if __name__ == "__main__":
    unittest.main()
