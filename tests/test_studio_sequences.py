"""The editor changes the same native project that its compiler consumes."""

import unittest
import tempfile
from pathlib import Path
from zipfile import ZipFile

from adventure_studio.scumm_assets import scrolling_fixture, destination_fixture
from adventure_studio.scumm_costume_probe import gesture_fixture
from adventure_studio.scumm_project import ActorAsset, GameDocument, canonical_json, parse_document
from adventure_studio.story_document import canonical_story_json, parse_story_document
from adventure_studio.studio_sequences import (append_sequence_step, modify_sequence_step,
                                                project_choices, sequence_choices, sequence_steps,
                                                compose_story_project)
from adventure_studio.studio_export import export_native_project
from adventure_studio.studio_project import canonical_studio_project, parse_studio_project
from test_scumm_toolchain import fake_upstream


class NativeSequenceEditorTests(unittest.TestCase):
    def test_author_reorder_and_remove_native_actions_in_project_json(self):
        document = GameDocument("EditorProject", (scrolling_fixture(), destination_fixture()),
                                (gesture_fixture(),),
                                (ActorAsset("Guide", "NativeGesture", "Harbor", 400, 110),))
        raw = canonical_json(document)
        rooms, objects, actors = project_choices(raw, "Harbor")
        self.assertIn("Harbor", rooms)
        self.assertIn("Key", objects)
        self.assertIn("Guide", actors)
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Actor animieren", "Guide",
                                   "gesture", None, None)
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Warten", None, None, None, 2)
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Objektzustand setzen",
                                   None, None, "Door", 2)
        identity = "Harbor|Key|Close"
        self.assertEqual(len(sequence_choices(raw)), 1)
        self.assertEqual(len(sequence_steps(raw, identity)), 3)
        raw = modify_sequence_step(raw, identity, 2, "Nach oben")
        steps = parse_document(raw).interaction_sequences[0].steps
        self.assertEqual(steps[1].hotspot_id, "Door")
        raw = modify_sequence_step(raw, identity, 2, "Entfernen")
        self.assertEqual(len(parse_document(raw).interaction_sequences[0].steps), 2)
        with self.assertRaisesRegex(ValueError, "Interaction state step"):
            append_sequence_step(raw, "Harbor", "Key", "Pull", "Objektzustand setzen",
                                 None, None, "MissingObject", 2)

        story = (Path(__file__).resolve().parents[1] / "examples" /
                 "mini_story_chain.json").read_text(encoding="utf-8")
        combined = parse_document(compose_story_project(story, raw))
        self.assertEqual(combined.actors, document.actors)
        self.assertEqual(combined.interaction_sequences, parse_document(raw).interaction_sequences)
        self.assertEqual(len(combined.rooms), 3)
        self.assertTrue(combined.rooms[0].use_rules)
        with self.assertRaisesRegex(ValueError, "Interaction sequence requires an existing room hotspot"):
            compose_story_project(story.replace('"Key"', '"NewKey"'), raw)

        studio_file = canonical_studio_project(story, raw)
        restored_story, restored_native = parse_studio_project(studio_file)
        self.assertEqual(restored_story, canonical_story_json(parse_story_document(story)))
        self.assertEqual(parse_document(restored_native).interaction_sequences,
                         parse_document(raw).interaction_sequences)
        restored_native = append_sequence_step(restored_native, "Harbor", "Key", "Close",
                                               "Warten", None, None, None, 3)
        saved_again = canonical_studio_project(restored_story, restored_native)
        self.assertEqual(len(parse_document(parse_studio_project(saved_again)[1])
                             .interaction_sequences[0].steps), 3)
        self.assertEqual(canonical_studio_project(*parse_studio_project(saved_again)), saved_again)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake_upstream(root / "scummc")
            road = root / "scummc" / "examples" / "road"
            source = road / "common.scc"
            source.write_text(source.read_text(encoding="utf-8").replace(
                "room ResRoom {\n", 'room ResRoom {\n    cost egoCost = "devil.cost";\n'
                '    script setupActors() {\n'
                '        // set VAR_EGO so we can use the *Ego* functions\n'
                '    }\n'), encoding="utf-8")
            header = road / "common.sch"
            header.write_text("// define an actor for our hero\nactor hero;\n" +
                              header.read_text(encoding="utf-8"), encoding="utf-8")
            compiler = root / "scummc" / "cost"
            compiler.write_text("fake executable", encoding="utf-8")
            compiler.chmod(0o755)

            def fake_runner(args, **_kwargs):
                target = Path(args[args.index("-o") + 1])
                if args[0].endswith("/sld"):
                    target.with_suffix(".000").write_bytes(b"index")
                    target.with_suffix(".001").write_bytes(b"data")
                else:
                    if target.name == "Harbor.roobj":
                        source = Path(args[-1]).read_text(encoding="utf-8")
                        self.assertIn("case Close:", source)
                        self.assertLess(source.index("animateActor(Guide,24);"),
                                        source.index("setObjectState(Door,2);"))
                    target.write_bytes(b"COST" if target.suffix == ".cost" else b"compiled")

            result = export_native_project(raw, root / "scummc", root / "game.zip", fake_runner,
                                           story_raw=story)
            with ZipFile(result) as archive:
                restored = parse_document(archive.read("project.json").decode("utf-8"))
                self.assertEqual(restored.interaction_sequences, parse_document(raw).interaction_sequences)
                self.assertEqual(archive.read("story.json").decode("utf-8"),
                                 canonical_story_json(parse_story_document(story)))
