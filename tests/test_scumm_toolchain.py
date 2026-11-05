"""No ScummC download required: validate exact toolchain boundaries."""

import tempfile
import unittest
from pathlib import Path

from adventure_studio.scumm_toolchain import compile_story_game
from adventure_studio.story_document import build_story_document


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "mini_story.json"


def fake_upstream(path: Path):
    road = path / "examples" / "road"
    road.mkdir(parents=True)
    (road / "common.scc").write_text(
        "room Road;\nloadRoom(Road);\nlockRoom(Road);\nstartRoom(Road);\n"
        "room ResRoom {\n    // the inventory icons\n}\n", encoding="utf-8")
    (road / "common.sch").write_text(
        "room ResRoom {\n    // Inventory objects\n}\n", encoding="utf-8")
    for name in ("scc", "sld"):
        tool = path / name
        tool.write_text("fake executable", encoding="utf-8")
        tool.chmod(0o755)


class ToolchainTests(unittest.TestCase):
    def test_story_names_determine_compiler_inputs_and_linker_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_story_document(EXAMPLE.read_text(encoding="utf-8"), root / "build")
            fake_upstream(root / "scummc")
            calls = []

            def fake_run(args, **kwargs):
                calls.append((args, kwargs))
                target = Path(args[args.index("-o") + 1])
                if args[0].endswith("/sld"):
                    target.with_suffix(".000").write_bytes(b"index")
                    target.with_suffix(".001").write_bytes(b"data")
                else:
                    target.write_bytes(b"compiled")

            output = compile_story_game(root / "build", root / "scummc", root / "game", runner=fake_run)
            self.assertEqual(len(calls), 4)
            self.assertIn("Harbor.scc", calls[0][0][-1])
            self.assertIn("Cellar.scc", calls[1][0][-1])
            self.assertIn("bootstrap.scc", calls[2][0][-1])
            self.assertTrue(calls[3][0][0].endswith("/sld"))
            self.assertTrue((output / "tentacle.000").is_file())
            self.assertTrue((output / "game-goal.json").is_file())
            self.assertTrue((root / "scummc" / "examples" / "road" / "Inv_Key.bmp").is_file())

    def test_corrupt_inventory_manifest_is_rejected_before_compilation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_story_document(EXAMPLE.read_text(encoding="utf-8"), root / "build")
            fake_upstream(root / "scummc")
            (root / "build" / "resources" / "inventory-ids.txt").write_text("Injected\n")
            with self.assertRaisesRegex(ValueError, "Inventory manifest"):
                compile_story_game(root / "build", root / "scummc", root / "game")
            self.assertFalse((root / "game").exists())


if __name__ == "__main__":
    unittest.main()
