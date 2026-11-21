"""Guard the native ScummVM matrix so no gameplay gate is silently skipped.

Keep this stdlib-only: Adventure core tests run without third-party YAML parsers.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/scummc-experiment.yml"
STEP = re.compile(r"^      - name: (.+)$", re.MULTILINE)
SHARDS = ("mask", "geometry", "actors", "story")


class NativeScummVMShardingTests(unittest.TestCase):
    def test_all_native_steps_have_exactly_one_expected_shard(self):
        contents = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("fail-fast: false", contents)
        self.assertIn("shard: [mask, geometry, actors, story]", contents)
        matches = list(STEP.finditer(contents))
        self.assertEqual(len(matches), 114)
        for index, match in enumerate(matches, 1):
            end = matches[index].start() if index < len(matches) else len(contents)
            block = contents[match.start():end]
            expected = (
                "actors" if index in (7, 8) or 41 <= index <= 64 else
                "mask" if 19 <= index <= 20 else
                "geometry" if 13 <= index <= 42 else
                "actors" if 43 <= index <= 66 else
                "story" if 67 <= index <= 114 else None
            )
            with self.subTest(step=index, name=match.group(1)):
                found = re.findall(r"matrix\.shard == '([^']+)'", block)
                if expected is None:
                    self.assertEqual(found, [], "Shared setup step was incorrectly gated")
                else:
                    self.assertEqual(found, [expected], "A native gate was moved or lost")
                    if "if: always()" in block:
                        self.fail("A gated artifact job must use always() with its shard")

    def test_shards_keep_native_artifacts_and_independent_failures(self):
        contents = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("name: Native ScummVM – ${{ matrix.shard }}", contents)
        self.assertIn("if: ${{ always() && matrix.shard == 'mask' }}", contents)
        self.assertIn("if: ${{ always() && matrix.shard == 'actors' }}", contents)
        self.assertIn("if: ${{ always() && matrix.shard == 'story' }}", contents)
        self.assertIn("if: ${{ always() && matrix.shard == 'geometry' }}", contents)
        self.assertIn("ubuntu-24.04-scumm-experimental-apt-${{ github.run_id }}-${{ github.run_attempt }}-${{ matrix.shard }}", contents)
        self.assertIn("python -m adventure_studio.scumm_object_zmask_probe", contents)
        self.assertIn("python -m adventure_studio.scumm_studio_png_probe", contents)


if __name__ == "__main__":
    unittest.main()
