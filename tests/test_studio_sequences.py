"""The editor changes the same native project that its compiler consumes."""

import unittest
import tempfile
import importlib.util
from pathlib import Path
from zipfile import ZipFile

from adventure_studio.scumm_assets import scrolling_fixture, destination_fixture
from adventure_studio.music_demo import original_midi_theme
from adventure_studio.scumm_voc_fixture import original_voc_effect
from adventure_studio.scumm_costume_probe import gesture_fixture
from adventure_studio.scumm_project import ActorAsset, GameDocument, canonical_json, parse_document
from adventure_studio.story_document import canonical_story_json, parse_story_document
from adventure_studio.studio_sequences import (append_sequence_step, append_selected_sequence_step,
                                                modify_sequence_step,
                                                replace_sequence_step, sequence_step_fields,
                                                sequence_condition_fields, set_sequence_condition,
                                                duplicate_sequence_variant,
                                                project_choices, sequence_choices, sequence_steps,
                                                compose_story_project)
from adventure_studio.studio_sequences import (import_room_music, import_room_sound,
                                                set_sequence_skippable)
from adventure_studio.studio_export import export_native_project
from adventure_studio.studio_project import canonical_studio_project, parse_studio_project
from adventure_studio.studio_actors import (add_actor, create_costume, move_actor,
                                           add_costume_frame, set_costume_animation,
                                           costume_timeline_images, edit_costume_timeline,
                                           render_costume_preview, set_actor_initial_animation)
from test_scumm_toolchain import fake_upstream


class NativeSequenceEditorTests(unittest.TestCase):
    def test_spoken_voc_line_binds_subtitle_and_stops_on_escape(self):
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        from adventure_studio.scumm_project import SoundAsset, VoiceLineStep, export_document
        document = GameDocument("VoiceProject", (scrolling_fixture(), destination_fixture()),
                                sound_assets=(SoundAsset("Greeting", "Harbor", original_voc_effect()),))
        raw = append_sequence_step(canonical_json(document), "Harbor", "Key", "Close",
                                   "Gesprochene Zeile", None, None, "Greeting", None,
                                   subtitle="The door is open.")
        raw = set_sequence_skippable(raw, "Harbor|Key|Close", True)
        parsed = parse_document(raw)
        self.assertEqual(parsed.interaction_sequences[0].steps,
                         (VoiceLineStep("Greeting", "The door is open."),))
        self.assertEqual(canonical_json(parsed), raw)
        self.assertEqual(sequence_step_fields(raw, "Harbor|Key|Close", 0)[8],
                         "The door is open.")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            export_document(parsed, root)
            native = inject_interaction_sequences((root / "Harbor.scc").read_text(),
                                                  "Harbor", parsed.interaction_sequences,
                                                  (), (), parsed.rooms[0], parsed.sound_assets)
            self.assertIn('egoSay("The door is open.");', native)
            self.assertIn("waitForMessage();", native)
            self.assertEqual(native.count("startSound(Greeting);"), 1)
            self.assertEqual(native.count("stopSound(Greeting);"), 2)
        with self.assertRaisesRegex(ValueError, "safe ASCII subtitle"):
            append_sequence_step(raw, "Harbor", "Key", "Open", "Gesprochene Zeile",
                                 None, None, "Greeting", None, subtitle='Say "hello"')
        with self.assertRaisesRegex(ValueError, "room VOC"):
            append_sequence_step(raw, "Cellar", "Stairs", "Close", "Gesprochene Zeile",
                                 None, None, "Greeting", None, subtitle="Hello")

    def test_voc_sound_effects_reference_room_assets_and_skip_last_state(self):
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        from adventure_studio.scumm_project import export_document
        document = GameDocument("VocProject", (scrolling_fixture(), destination_fixture()))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            voc = original_voc_effect()
            (root / "effect.voc").write_bytes(voc)
            raw = canonical_json(document)
            raw = import_room_sound(raw, "Harbor", "BellSound", str(root / "effect.voc"))
            raw = import_room_sound(raw, "Harbor", "WindSound", str(root / "effect.voc"))
            raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Sound starten",
                                       None, None, "BellSound", None)
            raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Sound starten",
                                       None, None, "WindSound", None)
            raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Warten",
                                       None, None, None, 2)
            raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Sound stoppen",
                                       None, None, "BellSound", None)
            raw = set_sequence_skippable(raw, "Harbor|Key|Close", True)
            self.assertEqual(canonical_json(parse_document(raw)), raw)
            self.assertEqual(parse_document(raw).sound_assets[0].voc, voc)
            export_document(parse_document(raw), root / "resources")
            self.assertEqual((root / "resources" / "BellSound.voc").read_bytes(), voc)
            source = (root / "resources" / "Harbor.scc").read_text(encoding="utf-8")
            native = inject_interaction_sequences(source, "Harbor",
                                                  parse_document(raw).interaction_sequences,
                                                  (), (), parse_document(raw).rooms[0],
                                                  parse_document(raw).sound_assets)
            self.assertIn('sound BellSound = "BellSound.soun";', native)
            self.assertIn('sound WindSound = "WindSound.soun";', native)
            self.assertLess(native.index('image = "Harbor.bmp";'),
                            native.index('sound BellSound = "BellSound.soun";'))
            self.assertLess(native.index('sound BellSound = "BellSound.soun";'),
                            native.index('object Key {'))
            self.assertEqual(native.count("startSound(BellSound);"), 1)
            self.assertEqual(native.count("stopSound(BellSound);"), 2)
            self.assertEqual(native.count("startSound(WindSound);"), 2)
            fake_upstream(root / "scummc")
            soun = root / "scummc" / "soun"
            soun.write_text("fake executable", encoding="utf-8")
            soun.chmod(0o755)
            calls = []

            def fake_runner(args, **_kwargs):
                calls.append(args)
                target = Path(args[args.index("-o") + 1])
                if args[0].endswith("/sld"):
                    target.with_suffix(".000").write_bytes(b"index")
                    target.with_suffix(".001").write_bytes(b"data")
                else:
                    target.write_bytes(b"SOUN" if args[0].endswith("/soun") else b"compiled")

            export_native_project(raw, root / "scummc", root / "sounds.zip", fake_runner)
            self.assertEqual(sum("-voc" in args for args in calls), 2)
            with self.assertRaisesRegex(ValueError, "room VOC resource"):
                append_sequence_step(raw, "Cellar", "Stairs", "Close", "Sound starten",
                                     None, None, "BellSound", None)
            with self.assertRaisesRegex(ValueError, "Sound-ID existiert"):
                import_room_sound(raw, "Cellar", "BellSound", str(root / "effect.voc"))
            story = (Path(__file__).resolve().parents[1] / "examples" /
                     "mini_story_chain.json").read_text(encoding="utf-8")
            composed = parse_document(compose_story_project(story, raw))
            self.assertEqual(composed.sound_assets, parse_document(raw).sound_assets)

    def test_imported_midi_controls_skippable_music_cue_and_survives_story_composition(self):
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        from adventure_studio.scumm_project import export_document
        document = GameDocument("MusicProject", (scrolling_fixture(), destination_fixture()))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            midi = original_midi_theme()
            (root / "theme.mid").write_bytes(midi)
            raw = import_room_music(canonical_json(document), "Harbor", "HarborTheme",
                                    str(root / "theme.mid"))
            raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Musik stoppen",
                                       None, None, None, None)
            raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Warten",
                                       None, None, None, 2)
            raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Musik starten",
                                       None, None, None, None)
            identity = "Harbor|Key|Close"
            raw = set_sequence_skippable(raw, identity, True)
            self.assertEqual(canonical_json(parse_document(raw)), raw)
            self.assertEqual(parse_document(raw).music_assets[0].midi, midi)
            export_document(parse_document(raw), root / "resources")
            self.assertEqual((root / "resources" / "HarborTheme.mid").read_bytes(), midi)
            source = (root / "resources" / "Harbor.scc").read_text(encoding="utf-8")
            native = inject_interaction_sequences(source, "Harbor",
                                                  parse_document(raw).interaction_sequences,
                                                  (), (), parse_document(raw).rooms[0])
            self.assertIn("stopMusic();", native)
            self.assertEqual(native.count("startMusic(HarborTheme);"), 3)  # room entry, normal, skip
            self.assertIn("if(VAR_OVERRIDE)", native)
            with self.assertRaisesRegex(ValueError, "requires music"):
                append_sequence_step(canonical_json(document), "Harbor", "Key", "Close",
                                     "Musik starten", None, None, None, None)
            with self.assertRaisesRegex(ValueError, "Musik-ID existiert"):
                import_room_music(raw, "Cellar", "HarborTheme", str(root / "theme.mid"))
            with self.assertRaisesRegex(ValueError, "conflicts with hotspot"):
                import_room_music(canonical_json(document), "Harbor", "Key",
                                  str(root / "theme.mid"))
            fake_upstream(root / "scummc")
            executable = root / "scummc" / "soun"
            executable.write_text("fake executable", encoding="utf-8")
            executable.chmod(0o755)
            calls = []

            def fake_runner(args, **_kwargs):
                calls.append(args)
                target = Path(args[args.index("-o") + 1])
                if args[0].endswith("/sld"):
                    target.with_suffix(".000").write_bytes(b"index")
                    target.with_suffix(".001").write_bytes(b"data")
                else:
                    target.write_bytes(b"SOUN" if args[0].endswith("/soun") else b"compiled")

            archive = export_native_project(raw, root / "scummc", root / "music.zip",
                                            fake_runner)
            self.assertTrue(archive.is_file())
            self.assertEqual(sum(args[0].endswith("/soun") for args in calls), 1)
            self.assertTrue(any("-gmd" in args for args in calls))
            story = (Path(__file__).resolve().parents[1] / "examples" /
                     "mini_story_chain.json").read_text(encoding="utf-8")
            composed = parse_document(compose_story_project(story, raw))
            self.assertEqual(composed.rooms[0].music_id, "HarborTheme")
            self.assertEqual(composed.music_assets[0].midi, midi)

    def test_terminal_room_transition_survives_json_editor_and_native_export(self):
        document = GameDocument("RoomChange", (scrolling_fixture(), destination_fixture()))
        raw = canonical_json(document)
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Warten",
                                   None, None, None, 2)
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Gegenstand aufnehmen",
                                   None, None, "Key", None)
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Raum wechseln",
                                   None, None, "Cellar", None)
        identity = "Harbor|Key|Close"
        self.assertEqual(sequence_steps(raw, identity)[-1], "Raumwechsel: Cellar")
        self.assertEqual(sequence_step_fields(raw, identity, 2)[3], "Cellar")
        self.assertEqual(canonical_json(parse_document(raw)), raw)
        from adventure_studio.studio_sequences import set_sequence_skippable
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        source = ('    object Key {\n        verb(int vrb, int objA, int objB) {\n'
                  '        }\n    }\n    local script entry() {\n    }\n')
        for skippable in (False, True):
            authored = set_sequence_skippable(raw, identity, skippable)
            result = inject_interaction_sequences(source, "Harbor",
                                                  parse_document(authored).interaction_sequences,
                                                  (), (), document.rooms[0])
            self.assertEqual(result.count("startRoom(Cellar);"), 1)
            self.assertLess(result.index("delaySeconds(2);"), result.index("startRoom(Cellar);"))
            self.assertLess(result.rindex("pickupObject(Key,VAR_ROOM);"),
                            result.index("startRoom(Cellar);"))
            if skippable:
                self.assertLess(result.index("} override {"), result.index("startRoom(Cellar);"))
                self.assertLess(result.index("if(VAR_OVERRIDE)"), result.index("startRoom(Cellar);"))
        with self.assertRaisesRegex(ValueError, "final step"):
            append_sequence_step(raw, "Harbor", "Key", "Close", "Warten",
                                 None, None, None, 1)
        with self.assertRaisesRegex(ValueError, "destination room"):
            replace_sequence_step(raw, identity, 2, "Raum wechseln", None, None,
                                  "Unknown", None)
        with self.assertRaisesRegex(ValueError, "final step"):
            modify_sequence_step(raw, identity, 2, "Nach oben")

    def test_edit_existing_step_in_place_without_changing_trigger_or_order(self):
        document = GameDocument("EditorProject", (scrolling_fixture(), destination_fixture()),
                                (gesture_fixture(),),
                                (ActorAsset("Guide", "NativeGesture", "Harbor", 400, 110),))
        raw = canonical_json(document)
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Warten",
                                   None, None, None, 2)
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Auf Actor warten",
                                   "Guide", None, None, None)
        identity = "Harbor|Key|Close"
        self.assertEqual(sequence_step_fields(raw, identity, 0)[4], 2)
        raw = replace_sequence_step(raw, identity, 0, "Actor laufen lassen", "Guide",
                                    None, None, None, 450, 112)
        self.assertEqual(sequence_step_fields(raw, identity, 0)[:2],
                         ("Actor laufen lassen", "Guide"))
        self.assertEqual(sequence_step_fields(raw, identity, 0)[5:7], (450, 112))
        self.assertEqual(sequence_steps(raw, identity),
                         ("Actor Guide: zu (450, 112) laufen lassen", "Auf Actor Guide warten"))
        self.assertEqual(len(parse_document(raw).interaction_sequences), 1)
        raw = set_sequence_condition(raw, identity, "Door", 1)
        guarded_identity = identity + "|Door|1"
        self.assertEqual(sequence_condition_fields(raw, guarded_identity), ("Door", 1))
        raw = duplicate_sequence_variant(raw, guarded_identity, "Door", 2)
        variant_identity = identity + "|Door|2"
        raw = replace_sequence_step(raw, variant_identity, 0, "Warten", None, None, None, 1)
        raw = append_selected_sequence_step(raw, variant_identity, "Gegenstand aufnehmen",
                                            None, None, "Key", None)
        self.assertEqual(sequence_steps(raw, variant_identity)[0], "Warten: 1 s")
        self.assertEqual(sequence_steps(raw, variant_identity)[-1], "Inventar: Key aufnehmen")
        self.assertEqual(len(sequence_choices(raw)), 2)
        with self.assertRaisesRegex(ValueError, "distinct states"):
            duplicate_sequence_variant(raw, guarded_identity, "Door", 2)
        raw = set_sequence_condition(raw, guarded_identity, None, 0)
        self.assertEqual(sequence_condition_fields(raw, identity), (None, 0))
        with self.assertRaisesRegex(ValueError, "Schritt existiert nicht"):
            replace_sequence_step(raw, identity, 3, "Warten", None, None, None, 2)

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
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Actor versetzen", "Guide",
                                   None, None, None, 420, 112)
        self.assertEqual(sequence_steps(raw, identity)[-1], "Actor Guide: zu (420, 112) setzen")
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Actor laufen lassen", "Guide",
                                   None, None, None, 450, 112)
        self.assertEqual(sequence_steps(raw, identity)[-1], "Actor Guide: zu (450, 112) laufen lassen")
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Auf Actor warten", "Guide",
                                   None, None, None)
        self.assertEqual(sequence_steps(raw, identity)[-1], "Auf Actor Guide warten")
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Actor drehen", "Guide",
                                   None, None, None, direction="N")
        self.assertEqual(sequence_steps(raw, identity)[-1], "Actor Guide: Richtung N")
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
                             .interaction_sequences[0].steps), 7)
        self.assertEqual(canonical_studio_project(*parse_studio_project(saved_again)), saved_again)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            if importlib.util.find_spec("PIL") is None:
                return  # The Studio CI runs this PNG path with its optional Pillow dependency.
            from PIL import Image
            sprite = root / "hero.png"
            image = Image.new("RGBA", (8, 12), (0, 0, 0, 0))
            for x in range(2, 6):
                for y in range(2, 11):
                    image.putpixel((x, y), (40, 130, 220, 255))
            image.save(sprite)
            raw = create_costume(raw, str(sprite), "PixelCostume")
            raw = add_actor(raw, "PixelHero", "PixelCostume", "Harbor", 220, 100, "S", "Pixel Hero")
            raw = move_actor(raw, "PixelHero", "Harbor", 240, 106, "E")
            second = root / "hero-wave.png"
            wave = Image.new("RGBA", (8, 12), (0, 0, 0, 0))
            for x in range(1, 7):
                for y in range(1, 9):
                    wave.putpixel((x, y), (40, 130, 220, 255) if x < 4 else (220, 60, 80, 255))
            wave.save(second)
            raw = add_costume_frame(raw, "PixelCostume", str(second), "Pose1")
            raw = set_costume_animation(raw, "PixelCostume", "wave", 28, "E",
                                        "Pose0, COUNT, Pose1", False)
            raw = set_actor_initial_animation(raw, "PixelHero", "wave")
            self.assertEqual(parse_document(raw).actors[-1].initial_animation, "wave")
            gallery = costume_timeline_images(raw, "PixelCostume", "wave", "E")
            self.assertEqual([label for _, label in gallery],
                             ["1. Pose0", "2. COUNT", "3. Pose1"])
            self.assertEqual(gallery[0][0].size, (112, 112))
            raw = edit_costume_timeline(raw, "PixelCostume", "wave", "E", 2, "Nach oben")
            raw = edit_costume_timeline(raw, "PixelCostume", "wave", "E", None,
                                        "Anhängen", "Pose0")
            preview = render_costume_preview(raw, "PixelCostume", "wave", "E", 180,
                                             root / "wave-preview.gif")
            with Image.open(preview) as animation_preview:
                self.assertEqual(animation_preview.format, "GIF")
                self.assertEqual(animation_preview.n_frames, 3)
                self.assertEqual(animation_preview.info["duration"], 180)
            raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Actor animieren",
                                       "PixelHero", "wave", None, None)
            created = parse_document(raw)
            self.assertEqual((created.actors[-1].x, created.actors[-1].direction), (240, "E"))
            self.assertEqual(created.costumes[-1].frames[0].pixels.count(1), 36)
            self.assertEqual(len(created.costumes[-1].frames), 2)
            self.assertEqual(created.costumes[-1].animations[-1].directions[0].commands,
                             ("Pose0", "Pose1", "COUNT", "Pose0"))
            self.assertEqual(created.costumes[-1].animations[-1].index, 28)
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
                        self.assertIn("animateActor(PixelHero,28);", source)
                    if target.name == "PixelCostume.cost":
                        script = Path(args[-1]).read_text(encoding="utf-8")
                        self.assertIn("anim gesture @ 24", script)
                        self.assertIn("anim wave @ 28", script)
                        self.assertIn("body(Pose0, Pose1, COUNT, Pose0)", script)
                    target.write_bytes(b"COST" if target.suffix == ".cost" else b"compiled")

            result = export_native_project(raw, root / "scummc", root / "game.zip", fake_runner,
                                           story_raw=story)
            with ZipFile(result) as archive:
                restored = parse_document(archive.read("project.json").decode("utf-8"))
                self.assertEqual(restored.interaction_sequences, parse_document(raw).interaction_sequences)
                self.assertEqual(archive.read("story.json").decode("utf-8"),
                                 canonical_story_json(parse_story_document(story)))
