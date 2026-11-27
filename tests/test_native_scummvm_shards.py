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
        # Counts include real gameplay and evidence-retention steps. New native
        # capabilities change the matrix length; preserve the per-shard gates.
        self.assertEqual(len(matches), 172)
        expected_counts = {"actors": 26, "mask": 2, "geometry": 86, "story": 48}
        observed_counts = {shard: 0 for shard in SHARDS}
        shared = {
            "Restore previously downloaded Ubuntu packages",
            "Install compiler dependencies and stock ScummVM",
            "Save downloaded Ubuntu packages even when install times out",
            "Fetch unmodified ScummC",
            "Fix legacy ScummC tool help paths in ephemeral checkout",
            "Build ScummC tools",
            "Build upstream road example",
            "Generate Adventure Studio 640x200 room source",
            "Compile generated room with ScummC",
            "Link generated room with upstream game bootstrap",
        }
        required = {
            "Verify native transferred Actor elevation and Escape": "geometry",
            "Retain native transferred Actor elevation evidence": "geometry",
            "Verify native transferred Actor VOC playback and Escape": "geometry",
            "Retain native transferred Actor voice evidence": "geometry",
            "Verify native transferred Actor positioning in destination room": "geometry",
            "Retain native transferred Actor position evidence": "geometry",
            "Verify native transferred Actor camera follow and return": "geometry",
            "Retain native transferred Actor camera evidence": "geometry",
            "Verify native 256-color room bitmap palette in stock ScummVM": "geometry",
            "Retain native 256-color room palette evidence": "geometry",
            "Verify native transferred Actor facing in destination room": "geometry",
            "Retain native transferred Actor facing evidence": "geometry",
            "Verify native transferred Actor action animation in destination room": "geometry",
            "Retain native transferred Actor animation evidence": "geometry",
            "Verify native transferred Actor walks in destination room": "geometry",
            "Retain native transferred Actor walk evidence": "geometry",
            "Verify native room clipping profile restoration in interaction": "geometry",
            "Retain native interaction clipping profile evidence": "geometry",
            "Verify dynamic native Actor clipping after room transfer": "geometry",
            "Retain native transferred Actor dynamic clipping evidence": "geometry",
            "Compile and play native presence-guarded Actor entry profiles": "geometry",
            "Retain native presence-guarded Actor entry profile evidence": "geometry",
            "Verify reusable native Actor destination clipping profiles": "geometry",
            "Retain native Actor destination profile evidence": "geometry",
            "Verify native Actor transfer with destination Z-clipping": "geometry",
            "Retain native Actor transfer Z-clipping evidence": "geometry",
            "Verify native Actor Z-clipping reset after real room return": "geometry",
            "Retain native Actor Z-clipping room-return evidence": "geometry",
            "Verify sequence-driven native Actor Z-clipping and restoration": "geometry",
            "Retain native Actor Z-clipping screenshots and report": "geometry",
            "Compile and play native R06 camera handoff to second moving Actor": "geometry",
            "Retain three genuine ScummVM camera-handoff control games and frames": "geometry",
            "Build and launch two authored native Actors with four room Z-masks (R06 stage 1)": "geometry",
            "Prove opposite-direction native Actor movement behind four Z-masks": "geometry",
            "Verify R06 native focus handoff during opposite-direction Actor walks": "geometry",
            "Prove reciprocal A-B-A native camera focus during opposite walks": "geometry",
            "Prove two native Actors walk both outbound and return Z-mask routes": "geometry",
            "Prove staggered native two-Actor return with one Actor temporarily stopped": "geometry",
            "Prove native two-Actor rendezvous at common X and separate return routes": "geometry",
            "Prove native rendezvous stillness and A-first B-second Actor release": "geometry",
            "Prove native camera inspection panorama while two Actors wait at meeting": "geometry",
            "Prove native Actor B camera follow resumes after scripted meeting inspection": "geometry",
            "Prove stock ScummVM Actor B mid-walk destination retarget without wait": "geometry",
            "Retain native mid-walk retarget games and mask-control screenshots": "geometry",
            "Retain native camera reacquisition ScummVM gameplay and mask controls": "geometry",
            "Retain native meeting camera tour and ScummVM controls": "geometry",
            "Retain native meeting and delayed release masked and control games": "geometry",
            "Retain rendezvous native ScummVM games and all mask controls": "geometry",
            "Retain staggered Actor return game and native positive-negative controls": "geometry",
            "Retain two-Actor return gameplay and all stock ScummVM mask controls": "geometry",
            "Retain reciprocal A-B-A masked and control native ScummVM gameplay": "geometry",
            "Retain R06 opposing-focus masked and native control games": "geometry",
            "Retain actual opposing-Actor masked and control ScummVM gameplay frames": "geometry",
            "Play both doors and reach final room of chained adventure in stock ScummVM": "story",
        }
        seen = set()
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(contents)
            block = contents[match.start():end]
            name = match.group(1)
            found = re.findall(r"matrix\.shard == '([^']+)'", block)
            self.assertNotIn(name, seen, "Duplicate native CI step name")
            seen.add(name)
            with self.subTest(step=index + 1, name=name):
                if name in shared:
                    self.assertEqual(found, [], "Shared setup step was incorrectly gated")
                else:
                    self.assertEqual(len(found), 1, "Native gate must have exactly one shard")
                    self.assertIn(found[0], SHARDS)
                    observed_counts[found[0]] += 1
                    if "if: always()" in block:
                        self.fail("A gated artifact job must use always() with its shard")
                if name in required:
                    self.assertEqual(found, [required[name]])
        self.assertEqual(observed_counts, expected_counts)
        self.assertTrue(set(required).issubset(seen))

    def test_active_palette_gate_runs_before_legacy_geometry(self):
        contents = WORKFLOW.read_text(encoding="utf-8")
        names = [match.group(1) for match in STEP.finditer(contents)]
        self.assertEqual(names.index("Verify native 256-color room bitmap palette in stock ScummVM"),
                         names.index("Link generated room with upstream game bootstrap") + 1)
        self.assertEqual(names.index("Retain native 256-color room palette evidence"),
                         names.index("Verify native 256-color room bitmap palette in stock ScummVM") + 1)
        self.assertEqual(names.index("Verify native transferred Actor elevation and Escape"),
                         names.index("Retain native 256-color room palette evidence") + 1)
        self.assertEqual(names.index("Retain native transferred Actor elevation evidence"),
                         names.index("Verify native transferred Actor elevation and Escape") + 1)
        self.assertEqual(names.index("Verify native transferred Actor VOC playback and Escape"),
                         names.index("Retain native transferred Actor elevation evidence") + 1)
        self.assertEqual(names.index("Retain native transferred Actor voice evidence"),
                         names.index("Verify native transferred Actor VOC playback and Escape") + 1)
        self.assertEqual(names.index("Verify native transferred Actor positioning in destination room"),
                         names.index("Retain native transferred Actor voice evidence") + 1)
        self.assertEqual(names.index("Retain native transferred Actor position evidence"),
                         names.index("Verify native transferred Actor positioning in destination room") + 1)
        self.assertEqual(names.index("Verify native transferred Actor camera follow and return"),
                         names.index("Retain native transferred Actor position evidence") + 1)
        self.assertEqual(names.index("Retain native transferred Actor camera evidence"),
                         names.index("Verify native transferred Actor camera follow and return") + 1)
        self.assertEqual(names.index("Verify native transferred Actor facing in destination room"),
                         names.index("Retain native transferred Actor camera evidence") + 1)
        self.assertEqual(names.index("Retain native transferred Actor facing evidence"),
                         names.index("Verify native transferred Actor facing in destination room") + 1)

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
