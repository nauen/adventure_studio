"""No ScummC download required: validate exact toolchain boundaries."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from adventure_studio.scumm_toolchain import compile_story_game
from adventure_studio.scumm_bootstrap import inject_language_keys, inject_multilingual_charset
from adventure_studio.localization import LanguageCatalog, LocalizedLine, canonical_catalog_json, parse_catalog
from adventure_studio.story_document import build_story_document
from adventure_studio.scumm_project import parse_document
from adventure_studio.story_localization import story_text_inventory


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
    def test_language_keyboard_selection_is_global_and_byte_encoded(self):
        catalog = parse_catalog('{"format_version":1,"source_language":"de",'
            '"languages":["de","ja","pl"],"lines":[{"id":"hello",'
            '"translations":{"de":"Grüße","ja":"扉","pl":"Cześć"}}]}')
        source = ('script keyboardHandler(int key) {\n        switch(key) {\n'
                  "        case 'q':\n            shutdown();\n            break;\n        }\n    }\n"
                  '        setupActors();')
        result, header = inject_language_keys(source, '// Dialog string list', catalog)
        self.assertEqual(header.count('int GameLanguage;'), 1)
        self.assertIn("case '1':", result)
        self.assertIn("case '2':", result)
        self.assertIn("case '3':", result)
        self.assertIn('GameLanguage = 25701;', result)  # de, stable ISO pair
        self.assertIn('GameLanguage = 27233;', result)  # ja
        self.assertIn('\\x80', result)
        self.assertNotIn('Grüße', result)

    def test_custom_font_replaces_both_dialogue_fonts_not_gui(self):
        example = ('chset chset1 @ 1 = "vera-gui.char";\n'
                   'chset chtest = "vera.char";\n'
                   'chset dialogCharset = "vera-small.char";\n')
        changed = inject_multilingual_charset(example)
        self.assertIn('chset chset1 @ 1 = "vera-gui.char";', changed)
        self.assertEqual(changed.count('"multilingual-font.char"'), 2)
        self.assertNotIn('"vera-small.char"', changed)
        self.assertEqual(inject_multilingual_charset(example), changed)
        with self.assertRaisesRegex(ValueError, "Unexpected upstream charset layout"):
            inject_multilingual_charset('chset chtest = "vera.char";')

    def test_custom_font_is_validated_and_copied_before_compilation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_story_document(EXAMPLE.read_text(encoding="utf-8"), root / "build")
            fake_upstream(root / "scummc")
            road = root / "scummc" / "examples" / "road"
            source = (road / "common.scc").read_text(encoding="utf-8")
            (road / "common.scc").write_text(source.replace(
                "room ResRoom {", 'chset chtest = "vera.char";\n'
                'chset dialogCharset = "vera-small.char";\nroom ResRoom {'), encoding="utf-8")
            font = root / "build" / "resources" / "multilingual-font.char"
            font.write_bytes(b"not a CHAR")
            with self.assertRaisesRegex(ValueError, "valid CHAR block"):
                compile_story_game(root / "build", root / "scummc", root / "game")
            self.assertFalse((road / "multilingual-font.char").exists())

            slots = 127
            data = bytearray(33 + 4 * slots + 1)
            data[:4] = b"CHAR"
            data[4:8] = len(data).to_bytes(4, "big")
            data[31:33] = slots.to_bytes(2, "little")
            for code in range(32, 127):
                data[33 + 4 * code:37 + 4 * code] = (33 + 4 * slots).to_bytes(4, "little")
            font.write_bytes(data)
            package = font.with_name("language-package.json")
            package.write_text('{"format_version":1,"char_sha256":"wrong"}')
            with self.assertRaisesRegex(ValueError, "Language package checksum mismatch"):
                compile_story_game(root / "build", root / "scummc", root / "game")
            package.unlink()
            calls = []

            def fake_run(args, **kwargs):
                calls.append(args)
                target = Path(args[args.index("-o") + 1])
                if args[0].endswith("/sld"):
                    target.with_suffix(".000").write_bytes(b"index")
                    target.with_suffix(".001").write_bytes(b"data")
                else:
                    target.write_bytes(b"compiled")

            compile_story_game(root / "build", root / "scummc", root / "game", runner=fake_run)
            self.assertEqual((road / "multilingual-font.char").read_bytes(), data)
            bootstrap = (root / "build" / "resources" / "bootstrap.scc").read_text(encoding="utf-8")
            self.assertEqual(bootstrap.count('"multilingual-font.char"'), 2)
            self.assertEqual(len(calls), 4)

    def test_opt_in_story_localization_is_gated_and_generates_scumm_branches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_story_document(EXAMPLE.read_text(encoding="utf-8"), root / "build")
            fake_upstream(root / "scummc")
            resources = root / "build" / "resources"
            with self.assertRaisesRegex(ValueError, "verified language package"):
                compile_story_game(root / "build", root / "scummc", root / "game",
                                   localize_story=True)
            with self.assertRaisesRegex(ValueError, "require --localize-story"):
                compile_story_game(root / "build", root / "scummc", root / "game",
                                   graphical_language_buttons=True)

            road = root / "scummc" / "examples" / "road"
            source = (road / "common.scc").read_text(encoding="utf-8")
            source = source.replace(
                "room ResRoom {",
                'chset chtest = "vera.char";\n'
                'chset dialogCharset = "vera-small.char";\n'
                'script keyboardHandler(int key) {\n        switch(key) {\n        }\n    }\n'
                '        setupActors();\nroom ResRoom {',
            )
            (road / "common.scc").write_text(source, encoding="utf-8")
            with (road / "common.sch").open("a", encoding="utf-8") as header:
                header.write("// Dialog string list\n")

            document = parse_document((root / "build" / "project.json").read_text(encoding="utf-8"))
            lines = tuple(LocalizedLine(key, (("de", value), ("en", value)))
                          for key, value in story_text_inventory(document).items())
            catalog = LanguageCatalog("en", ("de", "en"), lines)
            canonical = canonical_catalog_json(catalog)
            (resources / "language-catalog.json").write_text(canonical, encoding="utf-8")
            slots = 127
            font_bytes = bytearray(33 + 4 * slots + 1)
            font_bytes[:4] = b"CHAR"
            font_bytes[4:8] = len(font_bytes).to_bytes(4, "big")
            font_bytes[31:33] = slots.to_bytes(2, "little")
            for code in range(32, 127):
                font_bytes[33 + 4 * code:37 + 4 * code] = (33 + 4 * slots).to_bytes(4, "little")
            (resources / "multilingual-font.char").write_bytes(font_bytes)
            manifest = {
                "format_version": 1, "languages": ["de", "en"],
                "catalog_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
                "char_sha256": hashlib.sha256(font_bytes).hexdigest(),
                "glyph_map": {f"{code:02X}": chr(code) for code in range(32, 127)},
            }
            (resources / "language-package.json").write_text(json.dumps(manifest), encoding="utf-8")

            def fake_run(args, **kwargs):
                target = Path(args[args.index("-o") + 1])
                if args[0].endswith("/sld"):
                    target.with_suffix(".000").write_bytes(b"index")
                    target.with_suffix(".001").write_bytes(b"data")
                else:
                    target.write_bytes(b"compiled")

            compile_story_game(root / "build", root / "scummc", root / "game",
                               runner=fake_run, localize_story=True)
            localized = (resources / "Harbor.scc").read_text(encoding="utf-8")
            self.assertIn("GameLanguage ==", localized)
            self.assertIn("/* de */", localized)
            self.assertIn("/* en */", localized)
            self.assertTrue((root / "game" / "tentacle.001").is_file())
            compile_story_game(root / "build", root / "scummc", root / "game",
                               runner=fake_run, localize_story=True,
                               graphical_language_buttons=True)
            self.assertIn("object LangDe {",
                          (resources / "Harbor.scc").read_text(encoding="utf-8"))
            self.assertTrue((resources / "HarborLangDe.bmp").is_file())
            self.assertTrue((resources / "CellarLangEnActive.bmp").is_file())

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

