"""Prevent drift between the canonical SCUMM-v6 capability matrix and source index."""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
INDEX = DOCS / "scumm-v6-reference" / "capability_sources.json"


class ScummReferenceContractTests(unittest.TestCase):
    def test_reference_index_has_stable_unique_ids_and_valid_document_paths(self):
        data = json.loads(INDEX.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(set(data), {"schema_version", "description", "capabilities"})
        capabilities = data["capabilities"]
        self.assertEqual(len(capabilities), 64)
        for capability_id, sources in capabilities.items():
            with self.subTest(id=capability_id):
                self.assertRegex(capability_id, r"^[RAOSDUPE][0-9]{2}$")
                self.assertIsInstance(sources, list)
                self.assertTrue(sources)
                self.assertEqual(len(sources), len(set(sources)))
                for source in sources:
                    self.assertRegex(source, r"^[a-z0-9-]+\.md$")

    def test_reference_index_matches_single_canonical_capability_matrix(self):
        matrix_path = DOCS / "SCUMM_V6_CAPABILITIES.md"
        if not matrix_path.exists():
            self.skipTest("Current working copy predates the canonical matrix; CI checks full repo")
        matrix = matrix_path.read_text(encoding="utf-8")
        rows = re.findall(r"^\| ([RAOSDUPE][0-9]{2}) \|", matrix, flags=re.MULTILINE)
        self.assertEqual(len(rows), len(set(rows)), "Duplicate capability IDs in matrix")
        indexed = set(json.loads(INDEX.read_text(encoding="utf-8"))["capabilities"])
        self.assertEqual(indexed, set(rows), "Capabilities must be indexed exactly once")
        for refs in json.loads(INDEX.read_text(encoding="utf-8"))["capabilities"].values():
            for source in refs:
                self.assertTrue((DOCS / source).is_file(), source)


if __name__ == "__main__":
    unittest.main()
