"""An authored NPC line triggers its actor's indexed native COST animation."""

from dataclasses import replace
import importlib.util
from pathlib import Path
import tempfile
import unittest

from adventure_studio.dialogue_demo import dialogue_fixture
from adventure_studio.scumm_assets import scummc_room_source
from adventure_studio.scumm_costume import CostumeAnimation, CostumeDirection
from adventure_studio.scumm_project import canonical_json, export_document, parse_document
from adventure_studio.scumm_toolchain import dialogue_animation_bindings
from adventure_studio.studio_actors import (add_costume_frame, set_costume_speaking_pose,
                                           set_costume_animation)
from adventure_studio.studio_project import canonical_studio_project, parse_studio_project
from adventure_studio.studio_sequences import (compose_story_project, dialogue_animation_lines,
                                                dialogue_animation_choices, edit_dialogue_animation,
                                                dialogue_speaking_frames,
                                                dialogue_speaking_frame_selection,
                                                dialogue_speaking_frame_preview,
                                                dialogue_direction_animation_preview,
                                                assign_dialogue_speaking_frame,
                                                assign_dialogue_speaking_sequence,
    save_dialogue_speaking_template, apply_dialogue_speaking_template,
    dialogue_speaking_template_choices, dialogue_speaking_template_preview,
    dialogue_speaking_template_animation_preview,
    dialogue_speaking_draft_animation_preview,
    edit_dialogue_speaking_draft,
    dialogue_speaking_draft_step_preview,
    rename_dialogue_speaking_template, delete_dialogue_speaking_template,
    update_dialogue_speaking_template,
    load_dialogue_speaking_template_for_editing,
                                                assign_dialogue_direction_speaking_sequence,
                                                dialogue_speaking_sequence_selection,
                                                dialogue_speaking_timeline,
                                                edit_dialogue_speaking_timeline,
                                                dialogue_speaking_timeline_preview)
from adventure_studio.studio_sequences import (
    dialogue_animation_phase_selection, edit_dialogue_animation_phases,
    dialogue_ending_animation_selection, edit_dialogue_ending_animation,
    dialogue_ending_timeline, assign_dialogue_ending_sequence,
    edit_dialogue_ending_timeline, dialogue_ending_timeline_preview,
    import_dialogue_png_frame, dialogue_costume_isolation_preview,
    isolate_dialogue_speaker_costume, dialogue_png_batch_preview,
    import_dialogue_png_batch, dialogue_png_batch_order,
    move_dialogue_png_batch_frame, remove_dialogue_png_batch_frame,
    dialogue_png_batch_excluded, restore_dialogue_png_batch_frame,
    dialogue_png_batch_thumbnails, dialogue_png_batch_animation_preview,
    dialogue_png_batch_preflight, dialogue_png_batch_image_diagnostics,
    dialogue_png_batch_frame_preview, step_dialogue_png_batch_frame)
from adventure_studio.studio_sequences import (
    replace_dialogue_png_batch_frame, set_dialogue_png_batch_frame_id,
    dialogue_png_batch_selected_frame_id, dialogue_png_batch_entries,
    suggest_dialogue_png_batch_frame_id, resolve_dialogue_png_batch_frame_ids,
    stage_dialogue_png_sprite_sheet, dialogue_png_sprite_sheet_preview,
    dialogue_png_sprite_sheet_animation_preview,
    dialogue_png_sprite_sheet_order, move_dialogue_png_sprite_sheet_cell)
from adventure_studio.studio_sequences import (
    dialogue_png_sprite_sheet_sequence, change_dialogue_png_sprite_sheet_repetition,
    edit_dialogue_png_sprite_sheet_sequence, dialogue_png_sprite_sheet_playback_frames,
    track_dialogue_png_sprite_sheet_undo, undo_dialogue_png_sprite_sheet_edit,
    redo_dialogue_png_sprite_sheet_edit,
    dialogue_png_sprite_sheet_history_choices,
    jump_dialogue_png_sprite_sheet_history)


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "mini_story.json"


class DialogueAnimationTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("PIL"), "PNG-Test benötigt Pillow")
    def test_named_speaking_templates_reuse_validated_native_frames(self):
        from PIL import Image

        _story, raw = self.fixture()
        original = parse_document(raw)
        costume = replace(original.costumes[0], name="WitnessCostume")
        actors = tuple(replace(actor, costume="WitnessCostume")
                       if actor.id == "SpeakerWitness" else actor
                       for actor in original.actors)
        room = original.rooms[0]
        rules = tuple(replace(rule, actor_lines=tuple(
            (key, "SpeakerWitness") for key, _actor in rule.actor_lines))
            for rule in room.talk_rules)
        hotspots = tuple(replace(hotspot, talk_actor_lines=tuple(
            "SpeakerWitness" for _actor in hotspot.talk_actor_lines))
            if hotspot.talk_actor_lines else hotspot for hotspot in room.hotspots)
        raw = canonical_json(replace(
            original, actors=actors, costumes=(*original.costumes, costume),
            rooms=(replace(room, talk_rules=rules, hotspots=hotspots),
                   *original.rooms[1:])))
        first, second = (key for _label, key in dialogue_animation_lines(raw))
        with tempfile.TemporaryDirectory() as directory:
            for name, color in (("Speak", (225, 35, 35, 255)),
                                ("SpeakAlt", (35, 225, 35, 255))):
                path = Path(directory) / (name + ".png")
                Image.new("RGBA", (8, 8), color).save(path)
                raw = add_costume_frame(raw, "WitnessCostume", str(path), name)
        # The picker shows the exact same native pixel poses before a step is added.
        before_picker = parse_document(raw)
        red_pose = dialogue_speaking_frame_preview(raw, first, "Speak")
        green_pose = dialogue_speaking_frame_preview(raw, first, "SpeakAlt")
        self.assertIsNotNone(red_pose)
        self.assertIsNotNone(green_pose)
        self.assertGreater(red_pose.convert("RGB").getpixel((128, 128))[0], 180)
        self.assertGreater(green_pose.convert("RGB").getpixel((128, 128))[1], 180)
        self.assertEqual(parse_document(raw), before_picker)
        # Inspect any numbered draft step without changing its target animation.
        step_image = dialogue_speaking_draft_step_preview(
            raw, first, "Speak, SpeakAlt, Speak", 1)
        self.assertGreater(step_image.getpixel((128, 128))[1], 180)
        self.assertGreater(dialogue_speaking_draft_step_preview(
            raw, first, "Speak, SpeakAlt, Speak", 2).getpixel((128, 128))[0], 180)
        self.assertIsNone(dialogue_speaking_draft_step_preview(
            raw, first, "Speak", None))
        with self.assertRaisesRegex(ValueError, "gültigen Sprechschritt"):
            dialogue_speaking_draft_step_preview(raw, first, "Speak", 2)
        with self.assertRaisesRegex(ValueError, "Frame-ID"):
            dialogue_speaking_draft_step_preview(raw, first, "Speak, ", 1)
        before_draft = parse_document(raw)
        draft, step = edit_dialogue_speaking_draft(
            raw, first, "", "Hinzufügen", "Speak")
        self.assertEqual((draft, step), ("Speak", 0))
        draft, step = edit_dialogue_speaking_draft(
            raw, first, draft, "Hinzufügen", "SpeakAlt")
        self.assertEqual((draft, step), ("Speak, SpeakAlt", 1))
        draft, step = edit_dialogue_speaking_draft(
            raw, first, draft, "Hinzufügen", "SpeakAlt")
        self.assertEqual((draft, step), ("Speak, SpeakAlt, SpeakAlt", 2))
        draft, step = edit_dialogue_speaking_draft(
            raw, first, draft, "Nach oben", step_index=2)
        self.assertEqual((draft, step), ("Speak, SpeakAlt, SpeakAlt", 1))
        draft, step = edit_dialogue_speaking_draft(
            raw, first, draft, "Entfernen", step_index=1)
        self.assertEqual((draft, step), ("Speak, SpeakAlt", 1))
        draft, step = edit_dialogue_speaking_draft(
            raw, first, draft, "Nach oben", step_index=1)
        self.assertEqual((draft, step), ("SpeakAlt, Speak", 0))
        draft, step = edit_dialogue_speaking_draft(
            raw, first, draft, "Nach unten", step_index=0)
        self.assertEqual((draft, step), ("Speak, SpeakAlt", 1))
        draft, step = edit_dialogue_speaking_draft(
            raw, first, draft, "Entfernen", step_index=1)
        self.assertEqual((draft, step), ("Speak", 0))
        draft, step = edit_dialogue_speaking_draft(
            raw, first, draft, "Entfernen", step_index=0)
        self.assertEqual((draft, step), ("", None))
        self.assertEqual(parse_document(raw), before_draft)
        with self.assertRaisesRegex(ValueError, "vorhandenen PNG-Frame"):
            edit_dialogue_speaking_draft(raw, first, "", "Hinzufügen", "Missing")
        with self.assertRaisesRegex(ValueError, "vorhandene PNG-Frames"):
            edit_dialogue_speaking_draft(raw, first, "Speak, Missing", "Hinzufügen", "Speak")
        with self.assertRaisesRegex(ValueError, "Sprechschritt"):
            edit_dialogue_speaking_draft(raw, first, "Speak", "Entfernen", step_index=3)
        with self.assertRaisesRegex(ValueError, "am Rand"):
            edit_dialogue_speaking_draft(raw, first, "Speak", "Nach oben", step_index=0)
        with self.assertRaisesRegex(ValueError, "Sprecher-Dialogzeile"):
            edit_dialogue_speaking_draft(raw, "unknown", "", "Hinzufügen", "Speak")
        with tempfile.TemporaryDirectory() as directory:
            draft_path = Path(directory) / "unsaved.gif"
            before = parse_document(raw)
            rendered = dialogue_speaking_draft_animation_preview(
                raw, first, "Speak, SpeakAlt, Speak", 260, draft_path)
            self.assertEqual(rendered, draft_path)
            with Image.open(draft_path) as gif:
                self.assertEqual(gif.format, "GIF")
                self.assertEqual(gif.n_frames, 3)
                self.assertEqual(gif.info["duration"], 260)
                for index, channel in enumerate((0, 1, 0)):
                    gif.seek(index)
                    self.assertGreater(gif.convert("RGB").getpixel((128, 128))[channel], 180)
            self.assertEqual(parse_document(raw), before)
            self.assertEqual(dialogue_speaking_sequence_selection(raw, first),
                             dialogue_speaking_sequence_selection(
                                 canonical_json(before), first))
            with self.assertRaisesRegex(ValueError, "Sprechfolge eingeben"):
                dialogue_speaking_draft_animation_preview(
                    raw, first, "", 260, draft_path)
            with self.assertRaisesRegex(ValueError, "vorhandene PNG-Frames"):
                dialogue_speaking_draft_animation_preview(
                    raw, first, "Speak, Unbekannt", 260, draft_path)
            with self.assertRaisesRegex(ValueError, "Sprecher-Dialogzeile"):
                dialogue_speaking_draft_animation_preview(
                    raw, "falsche-Zeile", "Speak", 260, draft_path)
            with self.assertRaisesRegex(ValueError, "Millisekunden"):
                dialogue_speaking_draft_animation_preview(
                    raw, first, "Speak", 15, draft_path)
        self.assertEqual(dialogue_speaking_template_choices(raw), [])
        saved = save_dialogue_speaking_template(
            raw, first, "Begrüßung", "Speak, SpeakAlt, Speak")
        self.assertEqual(dialogue_speaking_template_choices(saved), ["Begrüßung"])
        template = parse_document(saved).speaking_sequence_templates[0]
        self.assertEqual(template.frames, ("Speak", "SpeakAlt", "Speak"))
        summary, can_apply = dialogue_speaking_template_preview(
            saved, second, "Begrüßung")
        self.assertTrue(can_apply)
        self.assertIn("Costume: WitnessCostume", summary)
        self.assertIn("Abspielbilder: 3", summary)
        self.assertIn("1. Speak\n2. SpeakAlt\n3. Speak", summary)
        with tempfile.TemporaryDirectory() as directory:
            gif = Path(directory) / "template.gif"
            before = parse_document(saved)
            rendered = dialogue_speaking_template_animation_preview(
                saved, second, "Begrüßung", 240, gif)
            self.assertEqual(rendered, gif)
            with Image.open(gif) as animation:
                self.assertEqual(animation.format, "GIF")
                self.assertEqual(animation.n_frames, 3)
                self.assertEqual(animation.info["duration"], 240)
                for index, channel in enumerate((0, 1, 0)):
                    animation.seek(index)
                    color = animation.convert("RGB").getpixel((128, 128))
                    self.assertGreater(color[channel], 180)
            self.assertEqual(parse_document(saved), before)
            with self.assertRaisesRegex(ValueError, "Millisekunden"):
                dialogue_speaking_template_animation_preview(
                    saved, second, "Begrüßung", 20, gif)
            with self.assertRaisesRegex(ValueError, "gespeicherte"):
                dialogue_speaking_template_animation_preview(
                    saved, second, "Unbekannt", 240, gif)
        self.assertEqual(dialogue_speaking_template_preview(
            saved, second, "Unbekannt")[1], False)
        self.assertEqual(dialogue_speaking_template_preview(
            saved, None, "Begrüßung")[1], False)
        self.assertEqual(
            load_dialogue_speaking_template_for_editing(
                saved, second, "Begrüßung"),
            "Speak, SpeakAlt, Speak")
        with self.assertRaisesRegex(ValueError, "gespeicherte"):
            load_dialogue_speaking_template_for_editing(
                saved, second, "Unbekannt")
        self.assertEqual(parse_document(canonical_json(parse_document(saved))),
                         parse_document(saved))
        with self.assertRaisesRegex(ValueError, "existiert bereits"):
            save_dialogue_speaking_template(
                saved, first, "begrüßung", "SpeakAlt")
        with self.assertRaisesRegex(ValueError, "vorhandene PNG-Frames"):
            save_dialogue_speaking_template(
                saved, first, "Ungültig", "NotAFrame")
        copied = apply_dialogue_speaking_template(
            saved, second, "Begrüßung")
        self.assertEqual(dialogue_speaking_sequence_selection(copied, second),
                         "Speak, SpeakAlt, Speak")
        self.assertEqual(dialogue_speaking_sequence_selection(raw, second), "")
        self.assertEqual(dialogue_speaking_template_choices(copied), ["Begrüßung"])
        renamed = rename_dialogue_speaking_template(
            copied, second, "Begrüßung", "Antwort")
        self.assertEqual(dialogue_speaking_template_choices(renamed), ["Antwort"])
        self.assertEqual(dialogue_speaking_sequence_selection(renamed, second),
                         "Speak, SpeakAlt, Speak")
        with self.assertRaisesRegex(ValueError, "existiert bereits"):
            two_templates = save_dialogue_speaking_template(
                renamed, first, "Zweite", "Speak")
            rename_dialogue_speaking_template(
                two_templates, second, "Antwort", "zweite")
        deleted = delete_dialogue_speaking_template(
            renamed, second, "Antwort")
        self.assertEqual(dialogue_speaking_template_choices(deleted), [])
        self.assertEqual(dialogue_speaking_sequence_selection(deleted, second),
                         "Speak, SpeakAlt, Speak")
        with self.assertRaisesRegex(ValueError, "vorhandene"):
            delete_dialogue_speaking_template(deleted, second, "Antwort")
        revised = update_dialogue_speaking_template(
            saved, first, "Begrüßung", "SpeakAlt, Speak")
        self.assertEqual(
            parse_document(revised).speaking_sequence_templates[0].frames,
            ("SpeakAlt", "Speak"))
        self.assertEqual(dialogue_speaking_sequence_selection(revised, second), "")
        reapplied = apply_dialogue_speaking_template(
            revised, second, "Begrüßung")
        self.assertEqual(dialogue_speaking_sequence_selection(reapplied, second),
                         "SpeakAlt, Speak")
        with self.assertRaisesRegex(ValueError, "vorhandene PNG-Frames"):
            update_dialogue_speaking_template(
                revised, first, "Begrüßung", "NotAFrame")
        with self.assertRaisesRegex(ValueError, "Sprechfolge eingeben"):
            update_dialogue_speaking_template(
                revised, first, "Begrüßung", "")
        with self.assertRaisesRegex(ValueError, "vorhandene"):
            update_dialogue_speaking_template(
                revised, first, "Unbekannt", "Speak")
        with self.assertRaisesRegex(ValueError, "gespeicherte"):
            apply_dialogue_speaking_template(saved, second, "Unbekannt")
        document = parse_document(saved)
        different_costume = canonical_json(replace(
            document, actors=tuple(
                replace(actor, costume=original.costumes[0].name)
                if actor.id == "SpeakerWitness" else actor
                for actor in document.actors)))
        with self.assertRaisesRegex(ValueError, "anderen Costume"):
            apply_dialogue_speaking_template(
                different_costume, second, "Begrüßung")
        with self.assertRaisesRegex(ValueError, "anderen Costume"):
            update_dialogue_speaking_template(
                different_costume, second, "Begrüßung", "Speak")
        with self.assertRaisesRegex(ValueError, "anderen Costume"):
            load_dialogue_speaking_template_for_editing(
                different_costume, second, "Begrüßung")
        summary, can_apply = dialogue_speaking_template_preview(
            different_costume, second, "Begrüßung")
        self.assertFalse(can_apply)
        self.assertIn("nicht kompatibel", summary)
        # The optional field does not change the v1 format or legacy files.
        self.assertNotIn('"speaking_sequence_templates"', raw)
        self.assertIn('"format_version":1', saved)

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "PNG-Import benötigt Pillow")
    def test_ordered_png_batch_import_is_atomic_and_native(self):
        from PIL import Image

        _story, raw = self.fixture()
        first, second = (key for _label, key in dialogue_animation_lines(raw))
        raw = isolate_dialogue_speaker_costume(raw, first)
        raw = edit_dialogue_animation(raw, first, "gesture")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = [root / "01-red.png", root / "02-green.png", root / "03-magenta.png"]
            for path, color in zip(files, ((220, 80, 80), (35, 225, 35), (200, 45, 205))):
                Image.new("RGBA", (8, 8), (*color, 255)).save(path)
            paths = [str(path) for path in files]
            ready, status = dialogue_png_batch_preflight(
                raw, first, "W", paths, "Sprechfolge")
            self.assertTrue(ready, status)
            self.assertIn("Importbereit: 3 PNG-Frame(s)", status)
            gallery, issues = dialogue_png_batch_image_diagnostics(
                raw, first, "W", paths, "Sprechfolge")
            self.assertEqual([path for path, _caption in gallery], paths)
            self.assertEqual(issues, "Keine bildbezogenen Konflikte erkannt")
            self.assertFalse(any("⚠️" in caption for _path, caption in gallery))
            duplicated, issues = dialogue_png_batch_image_diagnostics(
                raw, first, "W", [paths[0], paths[0]], "Sprechfolge")
            self.assertNotIn("⚠️", duplicated[0][1])
            self.assertIn("⚠️", duplicated[1][1])
            self.assertIn("2. 01-red.png", issues)
            self.assertEqual(dialogue_png_batch_preflight(
                raw, first, "W", paths, "Sprechfolge", order=())[0], False)
            bad = root / "broken.png"
            bad.write_bytes(b"not a png")
            self.assertIn("broken.png", dialogue_png_batch_preflight(
                raw, first, "W", [str(bad)], "Sprechfolge")[1])
            gallery, issues = dialogue_png_batch_image_diagnostics(
                raw, first, "W", [str(bad)], "Sprechfolge")
            self.assertIn("⚠️", gallery[0][1])
            self.assertIn("broken.png", issues)
            crowded = root / "crowded.png"
            image = Image.new("RGBA", (31, 1))
            image.putdata([((index * 7 + 3) % 256, (index * 5 + 2) % 256,
                            (index * 9 + 4) % 256, 255) for index in range(31)])
            image.save(crowded)
            ready, status = dialogue_png_batch_preflight(
                raw, first, "W", [str(crowded)], "Sprechfolge")
            self.assertFalse(ready)
            self.assertIn("crowded.png", status)
            self.assertIn("Palette", status)
            gallery, issues = dialogue_png_batch_image_diagnostics(
                raw, first, "W", [str(crowded)], "Sprechfolge")
            self.assertIn("⚠️", gallery[0][1])
            self.assertIn("Palette", issues)
            plan = dialogue_png_batch_preview(raw, first, paths)
            self.assertIn("1. 01-red.png → Frame_01_red", plan)
            self.assertIn("3. 03-magenta.png → Frame_03_magenta", plan)
            self.assertEqual(dialogue_png_batch_thumbnails(paths), [
                (paths[0], "1. Frame_01_red"), (paths[1], "2. Frame_02_green"),
                (paths[2], "3. Frame_03_magenta")])
            self.assertEqual(dialogue_png_batch_thumbnails(None), [])
            self.assertEqual(dialogue_png_batch_frame_preview(paths, (2, 0), 0),
                             (paths[2], "Bild 1 von 2 · Frame_03_magenta · noch nicht importiert"))
            self.assertEqual(step_dialogue_png_batch_frame(paths, (2, 0), 0, 1), 1)
            self.assertEqual(dialogue_png_batch_frame_preview(paths, (2, 0), 1)[0], paths[0])
            self.assertEqual(step_dialogue_png_batch_frame(paths, (2, 0), 1, 1), 1)
            self.assertEqual(dialogue_png_batch_frame_preview(paths, (), None)[0], None)
            with self.assertRaisesRegex(ValueError, "zuerst ein PNG"):
                step_dialogue_png_batch_frame(paths, (), None, 1)
            animation = root / "staged.gif"
            dialogue_png_batch_animation_preview(paths, (2, 0), 180, animation)
            with Image.open(animation) as preview_image:
                self.assertEqual(preview_image.n_frames, 2)
                self.assertEqual(preview_image.info["duration"], 180)
                preview_image.seek(0)
                self.assertEqual(preview_image.convert("RGB").getpixel((4, 4)),
                                 (200, 45, 205))
                preview_image.seek(1)
                self.assertEqual(preview_image.convert("RGB").getpixel((4, 4)),
                                 (220, 80, 80))
            with self.assertRaisesRegex(ValueError, "mindestens eine"):
                dialogue_png_batch_animation_preview(paths, (), 180, animation)
            with self.assertRaisesRegex(ValueError, "Reihenfolge passt nicht"):
                dialogue_png_batch_animation_preview(paths, (0, 0), 180, animation)
            with self.assertRaisesRegex(ValueError, "Framezeit"):
                dialogue_png_batch_animation_preview(paths, None, 12, animation)
            order, selected = move_dialogue_png_batch_frame(paths, None, 2, -1)
            self.assertEqual((order, selected), ((0, 2, 1), 1))
            order, selected = move_dialogue_png_batch_frame(paths, order, selected, -1)
            self.assertEqual((order, selected), ((2, 0, 1), 0))
            self.assertEqual(dialogue_png_batch_order(paths, order),
                             (paths[2], paths[0], paths[1]))
            self.assertEqual(dialogue_png_batch_thumbnails(paths, order)[0],
                             (paths[2], "1. Frame_03_magenta"))
            self.assertIn("1. 03-magenta.png → Frame_03_magenta",
                          dialogue_png_batch_preview(raw, first, paths, order))
            with self.assertRaisesRegex(ValueError, "Reihenfolge passt nicht"):
                dialogue_png_batch_order(paths, (0, 0, 1))
            replacement = root / "04-repaired.png"
            Image.new("RGBA", (8, 8), (55, 155, 205, 255)).save(replacement)
            replaced = replace_dialogue_png_batch_frame(paths, (2, 1), 0, str(replacement))
            self.assertEqual(replaced, (paths[0], paths[1], str(replacement)))
            self.assertEqual(dialogue_png_batch_order(replaced, (2, 1)),
                             (str(replacement), paths[1]))
            self.assertEqual(dialogue_png_batch_excluded(replaced, (2, 1)),
                             (("1. 01-red.png", 0),))
            self.assertEqual(dialogue_png_batch_preflight(
                raw, first, "W", [paths[0], paths[0]], "Sprechfolge")[0], False)
            repaired_duplicate = replace_dialogue_png_batch_frame(
                [paths[0], paths[0]], None, 1, str(replacement))
            self.assertTrue(dialogue_png_batch_preflight(
                raw, first, "W", repaired_duplicate, "Sprechfolge")[0])
            imported_repair = import_dialogue_png_batch(
                raw, first, "W", replaced, "Sprechfolge", order=(2, 1))
            self.assertEqual(dialogue_speaking_sequence_selection(imported_repair, first, "W"),
                             "Pose, Frame_04_repaired, Frame_02_green")
            overrides = set_dialogue_png_batch_frame_id(
                replaced, (2, 1), 0, "CustomGesture")
            self.assertEqual(overrides, {2: "CustomGesture"})
            self.assertEqual(dialogue_png_batch_selected_frame_id(
                replaced, (1, 2), 1, overrides), "CustomGesture")
            self.assertEqual(dialogue_png_batch_entries(replaced, (2, 1), overrides),
                             ((str(replacement), "CustomGesture"), (paths[1], "Frame_02_green")))
            self.assertIn("1. 04-repaired.png → CustomGesture",
                          dialogue_png_batch_preview(raw, first, replaced, (2, 1), overrides))
            self.assertEqual(dialogue_png_batch_thumbnails(replaced, (2, 1), overrides)[0],
                             (str(replacement), "1. CustomGesture"))
            self.assertTrue(dialogue_png_batch_preflight(
                raw, first, "W", replaced, "Sprechfolge", order=(2, 1), frame_ids=overrides)[0])
            native_override = import_dialogue_png_batch(
                raw, first, "W", replaced, "Sprechfolge", order=(2, 1), frame_ids=overrides)
            self.assertEqual(dialogue_speaking_sequence_selection(native_override, first, "W"),
                             "Pose, CustomGesture, Frame_02_green")
            export_document(parse_document(native_override), root / "custom-id-native")
            override_costume = next(actor.costume for actor in parse_document(native_override).actors
                                    if actor.id == "SpeakerHarborKeeper")
            self.assertIn("body(Pose, CustomGesture, Frame_02_green)",
                          (root / "custom-id-native" / f"{override_costume}.scost").read_text())
            collision = set_dialogue_png_batch_frame_id(
                [paths[0], paths[0]], None, 1, "UniqueCopy")
            self.assertTrue(dialogue_png_batch_preflight(
                raw, first, "W", [paths[0], paths[0]], "Sprechfolge", frame_ids=collision)[0])
            with self.assertRaisesRegex(ValueError, "Ungültige native Frame-ID"):
                set_dialogue_png_batch_frame_id(replaced, (2, 1), 0, "3 invalid")
            conflicting = set_dialogue_png_batch_frame_id(
                replaced, (2, 1), 0, "Frame_02_green")
            self.assertFalse(dialogue_png_batch_preflight(
                raw, first, "W", replaced, "Sprechfolge",
                order=(2, 1), frame_ids=conflicting)[0])
            multiple_duplicates = [paths[0], paths[0], paths[0]]
            partially_repaired = set_dialogue_png_batch_frame_id(
                multiple_duplicates, None, 1, "UniqueMiddle")
            self.assertFalse(dialogue_png_batch_preflight(
                raw, first, "W", multiple_duplicates, "Sprechfolge",
                frame_ids=partially_repaired)[0])
            fully_repaired = set_dialogue_png_batch_frame_id(
                multiple_duplicates, None, 2, "UniqueLast", partially_repaired)
            self.assertTrue(dialogue_png_batch_preflight(
                raw, first, "W", multiple_duplicates, "Sprechfolge",
                frame_ids=fully_repaired)[0])
            suggested = suggest_dialogue_png_batch_frame_id(
                raw, first, multiple_duplicates, None, 1)
            self.assertEqual(suggested, {1: "Frame_01_red_2"})
            suggested = suggest_dialogue_png_batch_frame_id(
                raw, first, multiple_duplicates, None, 2, suggested)
            self.assertEqual(suggested, {1: "Frame_01_red_2", 2: "Frame_01_red_3"})
            self.assertTrue(dialogue_png_batch_preflight(
                raw, first, "W", multiple_duplicates, "Sprechfolge",
                frame_ids=suggested)[0])
            already_imported = import_dialogue_png_batch(
                raw, first, "W", [paths[0]], "Sprechfolge")
            suggested_existing = suggest_dialogue_png_batch_frame_id(
                already_imported, first, [paths[0]], None, 0)
            self.assertEqual(suggested_existing, {0: "Frame_01_red_2"})
            self.assertTrue(dialogue_png_batch_preflight(
                already_imported, first, "W", [paths[0]], "Sprechfolge",
                frame_ids=suggested_existing)[0])
            bulk_paths = [paths[0], paths[0], paths[0], paths[1], paths[2]]
            bulk_order = (2, 1, 0, 3)
            bulk_overrides = {0: "Frame_01_red_2", 3: "MyUnique", 4: "ExcludedID"}
            resolved = resolve_dialogue_png_batch_frame_ids(
                already_imported, first, bulk_paths, bulk_order, bulk_overrides)
            self.assertEqual(resolved, {0: "Frame_01_red_2", 1: "Frame_01_red_4",
                                        2: "Frame_01_red_3", 3: "MyUnique", 4: "ExcludedID"})
            self.assertEqual(resolve_dialogue_png_batch_frame_ids(
                already_imported, first, bulk_paths, bulk_order, resolved), resolved)
            self.assertEqual([frame for _path, frame in dialogue_png_batch_entries(
                bulk_paths, bulk_order, resolved)],
                ["Frame_01_red_3", "Frame_01_red_4", "Frame_01_red_2", "MyUnique"])
            self.assertTrue(dialogue_png_batch_preflight(
                already_imported, first, "W", bulk_paths, "Sprechfolge",
                order=bulk_order, frame_ids=resolved)[0])
            imported_bulk = import_dialogue_png_batch(
                already_imported, first, "W", bulk_paths, "Sprechfolge",
                order=bulk_order, frame_ids=resolved)
            self.assertIn("Frame_01_red_3, Frame_01_red_4, Frame_01_red_2, MyUnique",
                          dialogue_speaking_sequence_selection(imported_bulk, first, "W"))
            self.assertEqual(resolve_dialogue_png_batch_frame_ids(
                raw, first, [paths[0]], None), {})
            with self.assertRaisesRegex(ValueError, "keine Bilder"):
                resolve_dialogue_png_batch_frame_ids(raw, first, paths, ())
            sheet = root / "MouthSheet.png"
            artwork = Image.new("RGBA", (16, 16))
            sheet_colors = ((240, 50, 65, 255), (60, 220, 70, 255),
                            (45, 85, 235, 255), (215, 155, 35, 255))
            for position, color in enumerate(sheet_colors):
                artwork.paste(color, ((position % 2) * 8, (position // 2) * 8,
                                      (position % 2 + 1) * 8, (position // 2 + 1) * 8))
            artwork.save(sheet)
            staged, staged_order = stage_dialogue_png_sprite_sheet(
                paths, (2, 0), str(sheet), 2, 2)
            self.assertEqual(staged[:3], tuple(paths))
            self.assertEqual(staged_order, (2, 0, 3, 4, 5, 6))
            self.assertEqual(dialogue_png_batch_excluded(staged, staged_order),
                             (("2. 02-green.png", 1),))
            self.assertEqual([Path(path).name for path in dialogue_png_batch_order(
                staged, staged_order)][2:],
                ["MouthSheet_r1_c1.png", "MouthSheet_r1_c2.png",
                 "MouthSheet_r2_c1.png", "MouthSheet_r2_c2.png"])
            for tile, color in zip(staged[3:], sheet_colors):
                with Image.open(tile) as image:
                    self.assertEqual(image.size, (8, 8))
                    self.assertEqual(image.convert("RGBA").getpixel((4, 4)), color)
            staged_ids = {0: "ExistingCustom"}
            self.assertIn("2. 01-red.png → ExistingCustom",
                          dialogue_png_batch_preview(raw, first, staged,
                                                     staged_order, staged_ids))
            self.assertTrue(dialogue_png_batch_preflight(
                raw, first, "W", staged, "Sprechfolge", order=staged_order,
                frame_ids=staged_ids)[0])
            imported_sheet = import_dialogue_png_batch(
                raw, first, "W", staged, "Sprechfolge",
                order=staged_order, frame_ids=staged_ids)
            self.assertIn("MouthSheet_r2_c1, MouthSheet_r2_c2",
                          dialogue_speaking_sequence_selection(imported_sheet, first, "W"))
            export_document(parse_document(imported_sheet), root / "sheet-native")
            sheet_costume = next(actor.costume for actor in parse_document(imported_sheet).actors
                                 if actor.id == "SpeakerHarborKeeper")
            self.assertIn("MouthSheet_r1_c1, MouthSheet_r1_c2, MouthSheet_r2_c1",
                          (root / "sheet-native" / f"{sheet_costume}.scost").read_text())
            spaced_sheet = root / "SpacedSheet.png"
            spaced = Image.new("RGBA", (24, 24), (245, 10, 245, 255))
            for position, color in enumerate(sheet_colors):
                col, row = position % 2, position // 2
                left, top = 2 + col * 12, 3 + row * 10
                spaced.paste(color, (left, top, left + 8, top + 8))
            spaced.save(spaced_sheet)
            overlay, planned, description = dialogue_png_sprite_sheet_preview(
                str(spaced_sheet), 2, 2, 2, 3, 4, 2)
            self.assertEqual(overlay.size, (24, 24))
            self.assertEqual(overlay.getpixel((2, 3)), (255, 75, 35, 255))
            self.assertEqual(overlay.getpixel((0, 0)), (245, 10, 245, 255))
            self.assertEqual(len(planned), 4)
            self.assertEqual(planned[0][1], "1. Zeile 1, Spalte 1 · ✓ Abspielposition 1")
            self.assertEqual(planned[-1][1], "4. Zeile 2, Spalte 2 · ✓ Abspielposition 4")
            self.assertIn("4 von 4 PNG-Frames ausgewählt", description)
            self.assertIn("8 × 8 Pixel", description)
            selected_overlay, selected_planned, selected_description = (
                dialogue_png_sprite_sheet_preview(
                    str(spaced_sheet), 2, 2, 2, 3, 4, 2, [1, 3]))
            self.assertEqual(selected_overlay.getpixel((14, 3)), (130, 130, 130, 255))
            self.assertIn("⛔ Überspringen", selected_planned[1][1])
            self.assertIn("2 von 4 PNG-Frames ausgewählt", selected_description)
            filtered_sheet, filtered_order = stage_dialogue_png_sprite_sheet(
                paths, (2, 0), str(spaced_sheet), 2, 2, 2, 3, 4, 2, [1, 3])
            self.assertEqual(filtered_order, (2, 0, 3, 4))
            self.assertEqual([Path(path).name for path in filtered_sheet[3:]],
                             ["SpacedSheet_r1_c1.png", "SpacedSheet_r2_c1.png"])
            self.assertEqual(dialogue_png_batch_excluded(filtered_sheet, filtered_order),
                             (("2. 02-green.png", 1),))
            self.assertTrue(dialogue_png_batch_preflight(
                raw, first, "W", filtered_sheet, "Sprechfolge",
                order=filtered_order)[0])
            self.assertEqual(dialogue_png_sprite_sheet_order(4, None), (0, 1, 2, 3))
            reordered = move_dialogue_png_sprite_sheet_cell(4, None, [1], 3, -1)
            self.assertEqual(reordered, (0, 1, 3, 2))
            reordered = move_dialogue_png_sprite_sheet_cell(4, reordered, [1], 3, -1)
            self.assertEqual(reordered, (3, 1, 0, 2))
            self.assertEqual(move_dialogue_png_sprite_sheet_cell(
                4, reordered, [1], 3, -1), reordered)
            reordered_overlay, reordered_tiles, reordered_description = (
                dialogue_png_sprite_sheet_preview(
                    str(spaced_sheet), 2, 2, 2, 3, 4, 2, [1], reordered))
            self.assertEqual(reordered_overlay.getpixel((14, 3)), (130, 130, 130, 255))
            self.assertIn("Abspielposition 1", reordered_tiles[3][1])
            self.assertIn("Abspielposition 2", reordered_tiles[0][1])
            self.assertIn("3 von 4", reordered_description)
            self.assertEqual(dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, {3: 3}), (3, 3, 3, 0, 2))
            free_timeline = "4,1,4,3"
            timeline_cards = dialogue_png_sprite_sheet_playback_frames(
                str(spaced_sheet), 2, 2, 2, 3, 4, 2, [1], reordered,
                {3: 3}, free_timeline)
            self.assertEqual([caption for _image, caption in timeline_cards], [
                "1. Bild · Zelle 4", "2. Bild · Zelle 1",
                "3. Bild · Zelle 4", "4. Bild · Zelle 3"])
            self.assertEqual(timeline_cards[0][0].tobytes(), timeline_cards[2][0].tobytes())
            self.assertNotEqual(timeline_cards[0][0].tobytes(), timeline_cards[1][0].tobytes())
            self.assertEqual(dialogue_png_sprite_sheet_playback_frames(
                str(spaced_sheet), 2, 2, 2, 3, 4, 2, [0, 1, 2, 3]), [])
            self.assertEqual(dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, {3: 3}, free_timeline), (3, 0, 3, 2))
            self.assertEqual(dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, {3: 3}, "  "), (3, 3, 3, 0, 2))
            composed = edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, "", "insert", 2, 3)
            self.assertEqual(composed, "4,1,4,3")
            self.assertEqual(edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, composed, "remove", 3), "4,1,3")
            moved = edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, composed, "move", 3, step=-1)
            self.assertEqual(moved, "4,4,1,3")
            block_moved = edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, composed, "move_block", 2,
                step=1, end_position=3)
            self.assertEqual(block_moved, "4,3,1,4")
            self.assertEqual(edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, block_moved, "move_block", 3,
                step=-1, end_position=4), composed)
            self.assertEqual(edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, composed, "move_block", 1,
                step=-1, end_position=2), composed)
            self.assertEqual(edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, composed, "move_block", 2,
                step=1, end_position=4), composed)
            copied = edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, composed, "copy_block", 2,
                end_position=3, destination_position=4)
            self.assertEqual(copied, "4,1,4,3,1,4")
            self.assertEqual(dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, copied), (3, 0, 3, 2, 0, 3))
            self.assertEqual(edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, composed, "copy_block", 2,
                end_position=3, destination_position=0), "1,4,4,1,4,3")
            self.assertEqual(edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, composed, "copy_block", 2,
                end_position=3, destination_position=2), "4,1,1,4,4,3")
            relocated = edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, composed, "relocate_block", 2,
                end_position=3, destination_position=4)
            self.assertEqual(relocated, "4,3,1,4")
            self.assertEqual(edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, relocated, "relocate_block", 3,
                end_position=4, destination_position=0), "1,4,4,3")
            self.assertEqual(edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, composed, "relocate_block", 2,
                end_position=3, destination_position=2), composed)
            self.assertEqual(edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, composed, "relocate_block", 1,
                end_position=4, destination_position=4), composed)
            with self.assertRaisesRegex(ValueError, "Zielposition"):
                edit_dialogue_png_sprite_sheet_sequence(
                    4, [1], reordered, None, composed, "relocate_block", 2,
                    end_position=3, destination_position=5)
            with self.assertRaisesRegex(ValueError, "gültigen Bildblock"):
                edit_dialogue_png_sprite_sheet_sequence(
                    4, [1], reordered, None, composed, "relocate_block", 3,
                    end_position=2, destination_position=0)
            context = ("sheet.png", 2, 2, (3, 0), ())
            history = track_dialogue_png_sprite_sheet_undo(None, composed, context)
            self.assertEqual(history, (context, ("", composed), 1))
            history = track_dialogue_png_sprite_sheet_undo(
                history, "4,4,1,3", context)
            history = track_dialogue_png_sprite_sheet_undo(
                history, "4,4,3,1", context)
            self.assertEqual(history[2], 3)
            choices = dialogue_png_sprite_sheet_history_choices(history)
            self.assertEqual([value for _label, value in choices], [0, 1, 2, 3])
            self.assertIn("Auf 4 Bilder erweitert", choices[1][0])
            self.assertIn("Folge mit 4 Bildern geändert", choices[3][0])
            selected, history = jump_dialogue_png_sprite_sheet_history(
                history, "4,4,3,1", context, 1)
            self.assertEqual(selected, composed)
            self.assertEqual(history[2], 1)
            selected, history = jump_dialogue_png_sprite_sheet_history(
                history, selected, context, 3)
            self.assertEqual(selected, "4,4,3,1")
            with self.assertRaisesRegex(ValueError, "nicht verfügbar"):
                jump_dialogue_png_sprite_sheet_history(
                    history, selected, context, 9)
            with self.assertRaisesRegex(ValueError, "nicht verfügbar"):
                jump_dialogue_png_sprite_sheet_history(
                    history, selected, context, True)
            with self.assertRaisesRegex(ValueError, "passt nicht"):
                jump_dialogue_png_sprite_sheet_history(
                    history, selected, ("other.png",), 1)
            with self.assertRaisesRegex(ValueError, "passt nicht"):
                jump_dialogue_png_sprite_sheet_history(
                    history, composed, context, 1)
            previous, history = undo_dialogue_png_sprite_sheet_edit(
                history, "4,4,3,1", context)
            self.assertEqual(previous, "4,4,1,3")
            previous, history = undo_dialogue_png_sprite_sheet_edit(
                history, previous, context)
            self.assertEqual(previous, composed)
            restored, history = redo_dialogue_png_sprite_sheet_edit(
                history, previous, context)
            self.assertEqual(restored, "4,4,1,3")
            restored, history = redo_dialogue_png_sprite_sheet_edit(
                history, restored, context)
            self.assertEqual(restored, "4,4,3,1")
            with self.assertRaisesRegex(ValueError, "Keine wiederherstellbare"):
                redo_dialogue_png_sprite_sheet_edit(history, restored, context)
            previous, history = undo_dialogue_png_sprite_sheet_edit(
                history, restored, context)
            history = track_dialogue_png_sprite_sheet_undo(
                history, "4,1,3,4", context)
            self.assertEqual(history[1][-1], "4,1,3,4")
            with self.assertRaisesRegex(ValueError, "Keine wiederherstellbare"):
                redo_dialogue_png_sprite_sheet_edit(history, "4,1,3,4", context)
            changed_context = track_dialogue_png_sprite_sheet_undo(
                history, "4,1,3,4", ("other.png",))
            self.assertEqual(changed_context[1:], (("4,1,3,4",), 0))
            with self.assertRaisesRegex(ValueError, "Keine rückgängig"):
                undo_dialogue_png_sprite_sheet_edit(
                    history, "4,1,3,4", ("other.png",))
            long_history = None
            for number in range(30):
                long_history = track_dialogue_png_sprite_sheet_undo(
                    long_history, f"1,{number}", context)
            self.assertEqual(len(long_history[1]), 21)
            self.assertEqual(long_history[2], 20)
            self.assertEqual(long_history[1][0], "1,9")
            self.assertEqual(long_history[1][-1], "1,29")
            repeated_block = edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, composed, "repeat_block", 2,
                end_position=3, destination_position=4, repetitions=2)
            self.assertEqual(repeated_block, "4,1,4,3,1,4,1,4")
            self.assertEqual(dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, repeated_block), (3, 0, 3, 2, 0, 3, 0, 3))
            self.assertEqual(edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, composed, "repeat_block", 2,
                end_position=3, destination_position=0, repetitions=1), "1,4,4,1,4,3")
            with self.assertRaisesRegex(ValueError, "mindestens eine"):
                edit_dialogue_png_sprite_sheet_sequence(
                    4, [1], reordered, None, composed, "repeat_block", 2,
                    end_position=3, destination_position=4, repetitions=0)
            with self.assertRaisesRegex(ValueError, "temporäres Staging-Limit"):
                edit_dialogue_png_sprite_sheet_sequence(
                    4, [1], reordered, None, composed, "repeat_block", 2,
                    end_position=3, destination_position=4, repetitions=1023)
            with self.assertRaisesRegex(ValueError, "gültigen Bildblock"):
                edit_dialogue_png_sprite_sheet_sequence(
                    4, [1], reordered, None, composed, "repeat_block", 3,
                    end_position=2, destination_position=4, repetitions=2)
            removed_block = edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, copied, "remove_block", 5,
                end_position=6)
            self.assertEqual(removed_block, composed)
            self.assertEqual(edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, "4,1,4,1,3", "remove_block", 2,
                end_position=3), "4,1,3")
            with self.assertRaisesRegex(ValueError, "letzte Kopie"):
                edit_dialogue_png_sprite_sheet_sequence(
                    4, [1], reordered, None, composed, "remove_block", 2,
                    end_position=4)
            with self.assertRaisesRegex(ValueError, "gültigen Bildblock"):
                edit_dialogue_png_sprite_sheet_sequence(
                    4, [1], reordered, None, composed, "remove_block", 3,
                    end_position=2)
            with self.assertRaisesRegex(ValueError, "gültigen Bildblock"):
                edit_dialogue_png_sprite_sheet_sequence(
                    4, [1], reordered, None, composed, "copy_block", 3,
                    end_position=2, destination_position=4)
            with self.assertRaisesRegex(ValueError, "Einfügeposition für den Bildblock"):
                edit_dialogue_png_sprite_sheet_sequence(
                    4, [1], reordered, None, composed, "copy_block", 2,
                    end_position=3, destination_position=9)
            with self.assertRaisesRegex(ValueError, "gültigen Abspielblock"):
                edit_dialogue_png_sprite_sheet_sequence(
                    4, [1], reordered, None, composed, "move_block", 3,
                    step=-1, end_position=2)
            with self.assertRaisesRegex(ValueError, "Ungültige Richtung"):
                edit_dialogue_png_sprite_sheet_sequence(
                    4, [1], reordered, None, composed, "move_block", 2,
                    step=0, end_position=3)
            self.assertEqual(edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, moved, "move", 2, step=1), composed)
            self.assertEqual(edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, composed, "move", 1, step=-1), composed)
            self.assertEqual(edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, {3: 2}, "", "move", 1, step=1), "")
            self.assertEqual(edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, "", "move", 1, step=1), "1,4,3")
            with self.assertRaisesRegex(ValueError, "vorhandenes Abspielbild"):
                edit_dialogue_png_sprite_sheet_sequence(
                    4, [1], reordered, None, composed, "move", 0, step=-1)
            with self.assertRaisesRegex(ValueError, "Ungültige Richtung"):
                edit_dialogue_png_sprite_sheet_sequence(
                    4, [1], reordered, None, composed, "move", 2, step=2)
            self.assertEqual(edit_dialogue_png_sprite_sheet_sequence(
                4, [1], reordered, None, composed, "reset"), "")
            with self.assertRaisesRegex(ValueError, "letzte Kopie"):
                edit_dialogue_png_sprite_sheet_sequence(
                    4, [1], reordered, None, composed, "remove", 2)
            with self.assertRaisesRegex(ValueError, "übernommene"):
                edit_dialogue_png_sprite_sheet_sequence(
                    4, [1], reordered, None, composed, "insert", 0, 1)
            with self.assertRaisesRegex(ValueError, "Einfügeposition"):
                edit_dialogue_png_sprite_sheet_sequence(
                    4, [1], reordered, None, composed, "insert", 99, 3)
            for value, message in (("4,1,3", ""), ("4,1,,3", "mit Kommas"),
                                   ("4,1,5,3", "außerhalb"),
                                   ("4,1,2,3", "ausgeschlossene"),
                                   ("4,1,4", "fehlen")):
                if not message:
                    self.assertEqual(dialogue_png_sprite_sheet_sequence(
                        4, [1], reordered, None, value), (3, 0, 2))
                else:
                    with self.assertRaisesRegex(ValueError, message):
                        dialogue_png_sprite_sheet_sequence(4, [1], reordered, None, value)
            free_overlay, free_planned, free_status = dialogue_png_sprite_sheet_preview(
                str(spaced_sheet), 2, 2, 2, 3, 4, 2, [1], reordered, {3: 3}, free_timeline)
            self.assertEqual(free_overlay.size, (24, 24))
            self.assertIn("Abspielpositionen 1, 3", free_planned[3][1])
            self.assertIn("4 Abspielbilder · Freie Abspielsequenz", free_status)
            free_paths, free_order = stage_dialogue_png_sprite_sheet(
                paths, (2, 0), str(spaced_sheet), 2, 2, 2, 3, 4, 2,
                [1], reordered, {3: 3}, free_timeline)
            self.assertEqual([Path(path).name for path in free_paths[3:]], [
                "SpacedSheet_r2_c2.png", "SpacedSheet_r1_c1.png",
                "SpacedSheet_r2_c2_repeat2.png", "SpacedSheet_r2_c1.png"])
            self.assertTrue(dialogue_png_batch_preflight(
                raw, first, "W", free_paths, "Sprechfolge", order=free_order)[0])
            free_native = import_dialogue_png_batch(
                raw, first, "W", free_paths, "Sprechfolge", order=free_order)
            self.assertIn("SpacedSheet_r2_c2, SpacedSheet_r1_c1, "
                          "SpacedSheet_r2_c2_repeat2, SpacedSheet_r2_c1",
                          dialogue_speaking_sequence_selection(free_native, first, "W"))
            free_gif_path = root / "sheet-free-order.gif"
            dialogue_png_sprite_sheet_animation_preview(
                str(spaced_sheet), 2, 2, 130, free_gif_path,
                2, 3, 4, 2, [1], reordered, {3: 3}, free_timeline)
            with Image.open(free_gif_path) as free_gif:
                self.assertEqual(free_gif.n_frames, 4)
                for position, index in enumerate((3, 0, 3, 2)):
                    free_gif.seek(position)
                    self.assertEqual(free_gif.convert("RGB").getpixel((4, 4)),
                                     sheet_colors[index][:3])
            self.assertEqual(change_dialogue_png_sprite_sheet_repetition(
                4, [1], None, 3, 1), {3: 2})
            self.assertEqual(change_dialogue_png_sprite_sheet_repetition(
                4, [1], {3: 2}, 3, 1), {3: 3})
            self.assertEqual(change_dialogue_png_sprite_sheet_repetition(
                4, [1], {3: 2}, 3, -1), {})
            self.assertEqual(change_dialogue_png_sprite_sheet_repetition(
                4, [1], None, 3, -1), {})
            with self.assertRaisesRegex(ValueError, "übernommene"):
                change_dialogue_png_sprite_sheet_repetition(4, [1], None, 1, 1)
            for invalid_repeats in ({1: 0}, {4: 2}, {False: 2}, {3: 1}, {3: 1.5}):
                with self.assertRaisesRegex(ValueError, "Wiederholungen"):
                    dialogue_png_sprite_sheet_sequence(4, [1], reordered, invalid_repeats)
            hold_overlay, hold_tiles, hold_status = dialogue_png_sprite_sheet_preview(
                str(spaced_sheet), 2, 2, 2, 3, 4, 2, [1], reordered, {3: 3})
            self.assertEqual(hold_overlay.size, (24, 24))
            self.assertIn("3×", hold_tiles[3][1])
            self.assertIn("5 Abspielbilder", hold_status)
            hold_paths, hold_order = stage_dialogue_png_sprite_sheet(
                paths, (2, 0), str(spaced_sheet), 2, 2, 2, 3, 4, 2, [1], reordered, {3: 3})
            self.assertEqual([Path(path).name for path in hold_paths[3:]], [
                "SpacedSheet_r2_c2.png", "SpacedSheet_r2_c2_repeat2.png",
                "SpacedSheet_r2_c2_repeat3.png", "SpacedSheet_r1_c1.png",
                "SpacedSheet_r2_c1.png"])
            self.assertTrue(dialogue_png_batch_preflight(
                raw, first, "W", hold_paths, "Sprechfolge", order=hold_order)[0])
            native_holds = import_dialogue_png_batch(
                raw, first, "W", hold_paths, "Sprechfolge", order=hold_order)
            self.assertIn("SpacedSheet_r2_c2, SpacedSheet_r2_c2_repeat2, "
                          "SpacedSheet_r2_c2_repeat3",
                          dialogue_speaking_sequence_selection(native_holds, first, "W"))
            sheet_holds_gif = root / "sheet-hold.gif"
            dialogue_png_sprite_sheet_animation_preview(
                str(spaced_sheet), 2, 2, 120, sheet_holds_gif,
                2, 3, 4, 2, [1], reordered, {3: 3})
            with Image.open(sheet_holds_gif) as hold_gif:
                self.assertEqual(hold_gif.info["loop"], 0)
                durations = []
                colors = []
                for frame_index in range(hold_gif.n_frames):
                    hold_gif.seek(frame_index)
                    durations.append(hold_gif.info["duration"])
                    colors.append(hold_gif.convert("RGB").getpixel((4, 4)))
                self.assertEqual(sum(durations), 600)
                self.assertEqual(colors, [sheet_colors[i][:3] for i in (3, 0, 2)])
            sheet_animation = root / "sheet-before-import.gif"
            dialogue_png_sprite_sheet_animation_preview(
                str(spaced_sheet), 2, 2, 240, sheet_animation,
                2, 3, 4, 2, [1], reordered)
            with Image.open(sheet_animation) as gif:
                self.assertEqual(gif.format, "GIF")
                self.assertEqual(gif.n_frames, 3)
                self.assertEqual(gif.info["duration"], 240)
                self.assertEqual(gif.info["loop"], 0)
                for position, source_index in enumerate((3, 0, 2)):
                    gif.seek(position)
                    self.assertEqual(gif.convert("RGB").getpixel((4, 4)),
                                     sheet_colors[source_index][:3])
            dialogue_png_sprite_sheet_animation_preview(
                str(spaced_sheet), 2, 2, 100, sheet_animation,
                2, 3, 4, 2, [0, 1, 2], reordered)
            with Image.open(sheet_animation) as single:
                self.assertEqual(single.n_frames, 1)
                self.assertEqual(single.convert("RGB").getpixel((4, 4)),
                                 sheet_colors[3][:3])
            with self.assertRaisesRegex(ValueError, "mindestens eine Sprite-Sheet-Zelle"):
                dialogue_png_sprite_sheet_animation_preview(
                    str(spaced_sheet), 2, 2, 180, sheet_animation,
                    2, 3, 4, 2, [0, 1, 2, 3], reordered)
            for invalid_duration in (39, 2001, 80.5, float("nan"), True):
                with self.assertRaisesRegex(ValueError, "Vorschau-Framezeit"):
                    dialogue_png_sprite_sheet_animation_preview(
                        str(spaced_sheet), 2, 2, invalid_duration, sheet_animation,
                        2, 3, 4, 2, [1], reordered)
            with self.assertRaisesRegex(ValueError, "Abspielreihenfolge"):
                dialogue_png_sprite_sheet_animation_preview(
                    str(spaced_sheet), 2, 2, 180, sheet_animation,
                    2, 3, 4, 2, [1], (0, 0, 2, 3))
            reordered_paths, reordered_order = stage_dialogue_png_sprite_sheet(
                paths, (2, 0), str(spaced_sheet), 2, 2, 2, 3, 4, 2, [1], reordered)
            self.assertEqual([Path(path).name for path in reordered_paths[3:]],
                             ["SpacedSheet_r2_c2.png", "SpacedSheet_r1_c1.png",
                              "SpacedSheet_r2_c1.png"])
            self.assertEqual(reordered_order, (2, 0, 3, 4, 5))
            self.assertTrue(dialogue_png_batch_preflight(
                raw, first, "W", reordered_paths, "Sprechfolge",
                order=reordered_order)[0])
            imported_reordered = import_dialogue_png_batch(
                raw, first, "W", reordered_paths, "Sprechfolge", order=reordered_order)
            self.assertIn("SpacedSheet_r2_c2, SpacedSheet_r1_c1, SpacedSheet_r2_c1",
                          dialogue_speaking_sequence_selection(imported_reordered, first, "W"))
            self.assertEqual(move_dialogue_png_sprite_sheet_cell(
                4, reordered, [1], 0, 1), (3, 1, 2, 0))
            with self.assertRaisesRegex(ValueError, "übernommene"):
                move_dialogue_png_sprite_sheet_cell(4, reordered, [1], 1, -1)
            for invalid in ([0, 0, 2, 3], [0, 2], [0, 1, 2, 4], [True, 1, 2, 3]):
                with self.assertRaisesRegex(ValueError, "Abspielreihenfolge"):
                    stage_dialogue_png_sprite_sheet(
                        None, None, str(spaced_sheet), 2, 2, 2, 3, 4, 2,
                        None, invalid)
            with self.assertRaisesRegex(ValueError, "mindestens eine Sprite-Sheet-Zelle"):
                stage_dialogue_png_sprite_sheet(None, None, str(spaced_sheet),
                                               2, 2, 2, 3, 4, 2, [0, 1, 2, 3])
            with self.assertRaisesRegex(ValueError, "passen nicht mehr"):
                stage_dialogue_png_sprite_sheet(None, None, str(spaced_sheet),
                                               2, 2, 2, 3, 4, 2, [4])
            spaced_paths, spaced_order = stage_dialogue_png_sprite_sheet(
                paths, (2, 0), str(spaced_sheet), 2, 2, 2, 3, 4, 2)
            self.assertEqual(spaced_order, (2, 0, 3, 4, 5, 6))
            for tile, color, (preview_tile, _label) in zip(
                    spaced_paths[3:], sheet_colors, planned):
                with Image.open(tile) as image:
                    self.assertEqual(image.size, (8, 8))
                    self.assertEqual(image.convert("RGBA").getpixel((0, 0)), color)
                    self.assertEqual(image.convert("RGBA").getpixel((7, 7)), color)
                    self.assertEqual(image.convert("RGBA").tobytes(), preview_tile.tobytes())
            imported_spaced = import_dialogue_png_batch(
                raw, first, "W", spaced_paths, "Sprechfolge", order=spaced_order)
            self.assertIn("SpacedSheet_r2_c1, SpacedSheet_r2_c2",
                          dialogue_speaking_sequence_selection(imported_spaced, first, "W"))
            only_sheet, only_order = stage_dialogue_png_sprite_sheet(
                None, None, str(sheet), 1, 1)
            self.assertEqual(len(only_sheet), 1)
            self.assertEqual(only_order, (0,))
            with self.assertRaisesRegex(ValueError, "teilbar"):
                stage_dialogue_png_sprite_sheet(None, None, str(sheet), 3, 2)
            with self.assertRaisesRegex(ValueError, "positive ganze Zahlen"):
                stage_dialogue_png_sprite_sheet(None, None, str(sheet), 0, 2)
            with self.assertRaisesRegex(ValueError, "nichtnegative ganze Pixelzahl"):
                stage_dialogue_png_sprite_sheet(None, None, str(sheet), 2, 2, -1)
            with self.assertRaisesRegex(ValueError, "keinen Platz"):
                stage_dialogue_png_sprite_sheet(None, None, str(sheet), 2, 2, 8, 0)
            with self.assertRaisesRegex(ValueError, "teilbar"):
                stage_dialogue_png_sprite_sheet(None, None, str(sheet), 2, 2, 0, 0, 1, 0)
            with self.assertRaisesRegex(ValueError, "zuerst eine native Sprecher"):
                suggest_dialogue_png_batch_frame_id(None, first, paths, None, 0)
            with self.assertRaisesRegex(ValueError, "zuerst ein PNG"):
                replace_dialogue_png_batch_frame(paths, (2, 1), None, str(replacement))
            with self.assertRaisesRegex(ValueError, "Ersatz"):
                replace_dialogue_png_batch_frame(paths, (2, 1), 0, None)
            with self.assertRaisesRegex(ValueError, "Reihenfolge passt nicht"):
                import_dialogue_png_batch(raw, first, "W", paths, "Sprechfolge",
                                          order=(0, 4))
            remaining, next_selected = remove_dialogue_png_batch_frame(paths, order, 1)
            self.assertEqual((remaining, next_selected), ((2, 1), 1))
            self.assertEqual(dialogue_png_batch_excluded(paths, remaining),
                             (("1. 01-red.png", 0),))
            self.assertEqual([path for path, _caption in
                              dialogue_png_batch_thumbnails(paths, remaining)],
                             [paths[2], paths[1]])
            restored, restored_selected = restore_dialogue_png_batch_frame(
                paths, remaining, 0)
            self.assertEqual((restored, restored_selected), ((2, 1, 0), 2))
            self.assertEqual(dialogue_png_batch_excluded(paths, restored), ())
            self.assertIn("3. 01-red.png → Frame_01_red",
                          dialogue_png_batch_preview(raw, first, paths, restored))
            with self.assertRaisesRegex(ValueError, "ausgeschlossenes PNG"):
                restore_dialogue_png_batch_frame(paths, restored, 0)
            restored_import = import_dialogue_png_batch(raw, first, "W", paths,
                                                         "Sprechfolge", order=restored)
            self.assertEqual(dialogue_speaking_sequence_selection(restored_import, first, "W"),
                             "Pose, Frame_03_magenta, Frame_02_green, Frame_01_red")
            self.assertEqual(dialogue_png_batch_order(paths, remaining),
                             (paths[2], paths[1]))
            self.assertNotIn("01-red.png", dialogue_png_batch_preview(
                raw, first, paths, remaining))
            filtered_import = import_dialogue_png_batch(raw, first, "W", paths,
                                                         "Sprechfolge", order=remaining)
            self.assertEqual(dialogue_speaking_sequence_selection(filtered_import, first, "W"),
                             "Pose, Frame_03_magenta, Frame_02_green")
            export_document(parse_document(filtered_import), root / "filtered-native")
            filtered_costume = next(actor.costume for actor in parse_document(filtered_import).actors
                                    if actor.id == "SpeakerHarborKeeper")
            scost = (root / "filtered-native" / f"{filtered_costume}.scost").read_text()
            self.assertIn("body(Pose, Frame_03_magenta, Frame_02_green)", scost)
            self.assertNotIn("Frame_01_red", scost)
            remaining, next_selected = remove_dialogue_png_batch_frame(paths, remaining, 0)
            self.assertEqual((remaining, next_selected), ((1,), 0))
            remaining, next_selected = remove_dialogue_png_batch_frame(paths, remaining, 0)
            self.assertEqual((remaining, next_selected), ((), None))
            self.assertEqual(dialogue_png_batch_thumbnails(paths, remaining), [])
            self.assertEqual(len(dialogue_png_batch_excluded(paths, remaining)), 3)
            restored_empty, restored_position = restore_dialogue_png_batch_frame(
                paths, remaining, 1)
            self.assertEqual((restored_empty, restored_position), ((1,), 0))
            self.assertEqual(dialogue_png_batch_order(paths, restored_empty), (paths[1],))
            self.assertIn("Alle PNG-Dateien", dialogue_png_batch_preview(raw, first, paths, remaining))
            with self.assertRaisesRegex(ValueError, "mindestens eine"):
                import_dialogue_png_batch(raw, first, "W", paths, "Sprechfolge",
                                          order=remaining)
            with self.assertRaisesRegex(ValueError, "zuerst ein PNG"):
                remove_dialogue_png_batch_frame(paths, remaining, None)
            moved_import = import_dialogue_png_batch(raw, first, "W", paths,
                                                      "Sprechfolge", order=order)
            self.assertEqual(dialogue_speaking_sequence_selection(moved_import, first, "W"),
                             "Pose, Frame_03_magenta, Frame_01_red, Frame_02_green")
            export_document(parse_document(moved_import), root / "reordered-native")
            moved_costume = next(actor.costume for actor in parse_document(moved_import).actors
                                if actor.id == "SpeakerHarborKeeper")
            self.assertIn("body(Pose, Frame_03_magenta, Frame_01_red, Frame_02_green)",
                          (root / "reordered-native" / f"{moved_costume}.scost").read_text())
            with self.assertRaisesRegex(ValueError, "mindestens eine"):
                import_dialogue_png_batch(raw, first, "W", [], "Sprechfolge")
            first_import = import_dialogue_png_batch(
                raw, first, "W", paths[:2], "Sprechfolge")
            ready, status = dialogue_png_batch_preflight(
                first_import, first, "W", paths, "Sprechfolge")
            self.assertFalse(ready)
            self.assertIn("existiert bereits", status)
            gallery, issues = dialogue_png_batch_image_diagnostics(
                first_import, first, "W", paths, "Sprechfolge")
            self.assertIn("⚠️", gallery[0][1])
            self.assertIn("⚠️", gallery[1][1])
            self.assertNotIn("⚠️", gallery[2][1])
            self.assertIn("01-red.png", issues)
            self.assertEqual(dialogue_speaking_sequence_selection(first_import, first, "W"),
                             "Pose, Frame_01_red, Frame_02_green")
            ending = import_dialogue_png_batch(
                first_import, first, "W", paths[2:], "Abschlussfolge", 24)
            self.assertEqual(dialogue_ending_timeline(ending, first, "W")[1][-1][0],
                             "1. Frame_03_magenta")
            self.assertEqual(dialogue_speaking_sequence_selection(ending, second, "W"), "")
            self.assertEqual(canonical_json(parse_document(ending)), ending)
            export_document(parse_document(ending), root / "native")
            costume_name = next(actor.costume for actor in parse_document(ending).actors
                                if actor.id == "SpeakerHarborKeeper")
            scost = (root / "native" / f"{costume_name}.scost").read_text()
            self.assertIn("body(Pose, Frame_01_red, Frame_02_green)", scost)
            self.assertIn("body(Frame_03_magenta)", scost)

            # A late invalid source must never leave the earlier PNG committed.
            bad = root / "04-bad.png"
            bad.write_bytes(b"not a PNG")
            with self.assertRaises((ValueError, OSError)):
                import_dialogue_png_batch(raw, first, "W", [*paths[:2], str(bad)],
                                          "Sprechfolge")
            self.assertNotIn("Frame_01_red", raw)
            duplicate = root / "01_red.png"
            Image.new("RGBA", (8, 8), (5, 10, 15, 255)).save(duplicate)
            with self.assertRaisesRegex(ValueError, "dieselbe Frame-ID"):
                import_dialogue_png_batch(raw, first, "W", [paths[0], str(duplicate)],
                                          "Sprechfolge")
            with self.assertRaisesRegex(ValueError, "existiert bereits"):
                import_dialogue_png_batch(ending, first, "W", paths[:2], "Sprechfolge")

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "PNG-Import benötigt Pillow")
    def test_isolate_shared_speaker_costume_before_dialogue_png_import(self):
        from PIL import Image

        _story, raw = self.fixture()
        first, second = (key for _label, key in dialogue_animation_lines(raw))
        before = parse_document(raw)
        speaker = next(actor for actor in before.actors if actor.id == "SpeakerHarborKeeper")
        witness = next(actor for actor in before.actors if actor.id == "SpeakerWitness")
        self.assertEqual(speaker.costume, witness.costume)
        self.assertIn("SpeakerWitness", dialogue_costume_isolation_preview(raw, first))
        self.assertIn("DialogueFigure_SpeakerHarborKeeper",
                      dialogue_costume_isolation_preview(raw, first))
        isolated = isolate_dialogue_speaker_costume(raw, first)
        document = parse_document(isolated)
        owned = next(actor for actor in document.actors if actor.id == speaker.id)
        untouched = next(actor for actor in document.actors if actor.id == witness.id)
        self.assertEqual(untouched.costume, witness.costume)
        self.assertEqual(owned.costume, "DialogueFigure_SpeakerHarborKeeper")
        assets = {asset.name: asset for asset in document.costumes}
        self.assertEqual(assets[untouched.costume], before.costumes[0])
        self.assertEqual(replace(assets[owned.costume], name=untouched.costume),
                         assets[untouched.costume])
        self.assertIn("bereits nur dieser Figur",
                      dialogue_costume_isolation_preview(isolated, first))
        with self.assertRaisesRegex(ValueError, "bereits exklusiv"):
            isolate_dialogue_speaker_costume(isolated, first)
        with self.assertRaisesRegex(ValueError, "Sprecher-Dialogzeile"):
            isolate_dialogue_speaker_costume(isolated, "missing")
        with tempfile.TemporaryDirectory() as directory:
            png = Path(directory) / "isolated.png"
            Image.new("RGBA", (8, 8), (200, 45, 205, 255)).save(png)
            changed = import_dialogue_png_frame(
                edit_dialogue_animation(isolated, first, "gesture"), first, "W",
                str(png), "OnlyHarbor", "Abschlussfolge", 16)
            result = parse_document(changed)
            original = next(asset for asset in result.costumes
                            if asset.name == untouched.costume)
            private = next(asset for asset in result.costumes
                           if asset.name == owned.costume)
            self.assertEqual(original, before.costumes[0])
            self.assertIn("OnlyHarbor", {frame.id for frame in private.frames})
            self.assertNotIn("OnlyHarbor", {frame.id for frame in original.frames})
            export_document(result, Path(directory) / "native")
            self.assertTrue((Path(directory) / "native" / f"{owned.costume}.scost").is_file())
            self.assertTrue((Path(directory) / "native" / f"{untouched.costume}.scost").is_file())
            self.assertEqual(canonical_json(result), changed)

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "PNG-Import benötigt Pillow")
    def test_import_real_png_directly_into_speaking_and_ending_line(self):
        from PIL import Image

        _story, shared = self.fixture()
        document = parse_document(shared)
        raw = canonical_json(replace(document,
            costumes=(*document.costumes, replace(document.costumes[0], name="WitnessCostume")),
            actors=tuple(replace(actor, costume="WitnessCostume")
                         if actor.id == "SpeakerWitness" else actor
                         for actor in document.actors)))
        first, second = (key for _label, key in dialogue_animation_lines(raw))
        raw = edit_dialogue_animation(raw, first, "gesture")
        raw = edit_dialogue_animation(raw, second, "gesture")
        with tempfile.TemporaryDirectory() as directory:
            red = Path(directory) / "red.png"
            green = Path(directory) / "green.png"
            Image.new("RGBA", (8, 8), (220, 80, 80, 255)).save(red)
            Image.new("RGBA", (8, 8), (35, 225, 35, 255)).save(green)
            with self.assertRaisesRegex(ValueError, "anderen Figuren"):
                import_dialogue_png_frame(shared, first, "W", str(red),
                                          "ImportedRed", "Sprechfolge")
            updated = import_dialogue_png_frame(raw, first, "W", str(red),
                                                "ImportedRed", "Sprechfolge")
            updated = import_dialogue_png_frame(updated, first, "W", str(green),
                                                "ImportedGreen", "Abschlussfolge", 22)
            self.assertIn("ImportedRed", dialogue_speaking_sequence_selection(updated, first, "W"))
            self.assertIn("ImportedGreen", tuple(frame.id for frame in
                          parse_document(updated).costumes[0].frames))
            ending_cue = next(cue for cue in parse_document(updated).dialogue_animation_cues
                              if cue.line_id == first)
            self.assertEqual(ending_cue.ending_animation_ticks, 22)
            self.assertEqual(dialogue_ending_timeline(updated, first, "W")[1][-1][0],
                             "1. ImportedGreen")
            self.assertIsNone(dialogue_ending_animation_selection(updated, second)[1])
            with self.assertRaisesRegex(ValueError, "existiert bereits"):
                import_dialogue_png_frame(updated, first, "W", str(red),
                                          "ImportedRed", "Sprechfolge")
            with self.assertRaisesRegex(ValueError, "gültige Blickrichtung"):
                import_dialogue_png_frame(updated, first, "NW", str(red),
                                          "Bad", "Abschlussfolge")
            with self.assertRaisesRegex(ValueError, "Sprechfolge oder Abschlussfolge"):
                import_dialogue_png_frame(updated, first, "W", str(red),
                                          "Bad", "SomethingElse")
            with self.assertRaisesRegex(ValueError, "mindestens einen"):
                import_dialogue_png_frame(updated, first, "W", str(red),
                                          "Bad", "Abschlussfolge", 0)
            self.assertEqual(canonical_json(parse_document(updated)), updated)
            compiled = parse_document(updated)
            export_document(compiled, Path(directory) / "export")
            scost = (Path(directory) / "export" / "DialogueFigure.scost").read_text()
            self.assertIn("body(ImportedGreen)", scost)
            self.assertIn("body(Pose, ImportedRed)", scost)
            script = scummc_room_source(compiled.rooms[0], dialogue_animation_cues=
                                        dialogue_animation_bindings(compiled, compiled.rooms[0]))
            self.assertIn("delay(22);", script)

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "PNG-Timeline benötigt Pillow")
    def test_png_ending_timeline_owns_native_slot_and_preserves_line_directions(self):
        _story, raw = self.fixture()
        original = parse_document(raw)
        raw = canonical_json(replace(original,
            costumes=(*original.costumes, replace(original.costumes[0], name="WitnessCostume")),
            actors=tuple(replace(actor, costume="WitnessCostume")
                         if actor.id == "SpeakerWitness" else actor
                         for actor in original.actors)))
        first, second = (key for _label, key in dialogue_animation_lines(raw))
        raw = edit_dialogue_animation(raw, first, "gesture")
        raw = edit_dialogue_animation(raw, second, "gesture")
        self.assertEqual(dialogue_ending_timeline(raw, first, "W")[1], ())
        raw = edit_dialogue_ending_timeline(raw, first, "W", None, "Anhängen", "Pose", 18)
        raw = edit_dialogue_ending_timeline(raw, first, "W", 0, "Anhängen", "Pose", 18)
        raw = edit_dialogue_ending_timeline(raw, first, "W", 0, "Nach rechts", ticks=18)
        images, steps, frames = dialogue_ending_timeline(raw, first, "W")
        self.assertEqual(tuple(label for label, _ in steps), ("1. Pose", "2. Pose"))
        self.assertEqual(len(images), 2)
        self.assertIn("Pose", frames)
        raw = edit_dialogue_ending_timeline(raw, first, "W", 0, "Entfernen", ticks=18)
        first_cue = next(cue for cue in parse_document(raw).dialogue_animation_cues
                         if cue.line_id == first)
        self.assertTrue(first_cue.ending_animation.startswith("ending_line_"))
        self.assertEqual(first_cue.ending_animation_ticks, 18)
        self.assertEqual(dialogue_ending_animation_selection(raw, second)[1], None)
        document = parse_document(raw)
        ending = next(a for a in document.costumes[0].animations
                      if a.name == first_cue.ending_animation)
        self.assertGreaterEqual(ending.index, 28)
        self.assertEqual(next(d.commands for d in ending.directions if d.direction == "W"),
                         ("Pose",))
        self.assertEqual(next(d.commands for d in ending.directions if d.direction == "E"),
                         ("Pose",))
        before_index = ending.index
        raw = assign_dialogue_ending_sequence(raw, first, "E", "Pose, Pose, Pose", 24)
        self.assertEqual(dialogue_ending_timeline(raw, first, "W")[1], (("1. Pose", 0),))
        self.assertEqual(len(dialogue_ending_timeline(raw, first, "E")[1]), 3)
        reloaded = canonical_json(parse_document(raw))
        self.assertEqual(raw, reloaded)
        document = parse_document(reloaded)
        self.assertEqual(next(a.index for a in document.costumes[0].animations
                              if a.name == first_cue.ending_animation), before_index)
        script = scummc_room_source(document.rooms[0], dialogue_animation_cues=
                                    dialogue_animation_bindings(document, document.rooms[0]))
        self.assertIn(f"animateActor(SpeakerHarborKeeper,{before_index});\n            delay(24);", script)
        with tempfile.TemporaryDirectory() as directory:
            export_document(document, Path(directory) / "resources")
            source = (Path(directory) / "resources" / "DialogueFigure.scost").read_text()
            self.assertIn(f"anim {first_cue.ending_animation} @ {before_index}", source)
            self.assertIn("body(Pose, Pose, Pose)", source)
            preview = dialogue_ending_timeline_preview(reloaded, first, "E", 180,
                                                       Path(directory) / "ending.gif")
            self.assertTrue(preview.is_file())
        with self.assertRaisesRegex(ValueError, "mindestens ein"):
            assign_dialogue_ending_sequence(raw, first, "W", "")
        with self.assertRaisesRegex(ValueError, "vorhandene PNG"):
            assign_dialogue_ending_sequence(raw, first, "W", "Unknown")
        with self.assertRaisesRegex(ValueError, "gültige Blickrichtung"):
            assign_dialogue_ending_sequence(raw, first, "NW", "Pose")
        with self.assertRaisesRegex(ValueError, "Entfernen"):
            edit_dialogue_ending_timeline(raw, first, "W", 0, "Entfernen")
        removed = edit_dialogue_ending_animation(raw, first, None, 0)
        self.assertIsNone(dialogue_ending_animation_selection(removed, first)[1])
        self.assertEqual(dialogue_ending_timeline(removed, first, "W")[1], ())

    def test_optional_native_ending_animation_is_per_line_after_message(self):
        _story, raw = self.fixture()
        first, second = (key for _label, key in dialogue_animation_lines(raw))
        raw = edit_dialogue_animation(raw, first, "gesture", True)
        raw = edit_dialogue_animation(raw, second, "gesture", True)
        for face in ("N", "E", "S", "W"):
            raw = set_costume_animation(raw, "DialogueFigure", "ending_pose", 28,
                                        face, "Pose", False)
        choices, selected, ticks = dialogue_ending_animation_selection(raw, first)
        self.assertIn("ending_pose", choices)
        self.assertIsNone(selected)
        self.assertEqual(ticks, 12)
        updated = edit_dialogue_ending_animation(raw, first, "ending_pose", 18)
        self.assertEqual(dialogue_ending_animation_selection(updated, first)[1:],
                         ("ending_pose", 18))
        self.assertEqual(dialogue_ending_animation_selection(updated, second)[1:], (None, 12))
        self.assertIn('"ending_animation":"ending_pose"', updated)
        self.assertIn('"ending_animation_ticks":18', updated)
        self.assertEqual(canonical_json(parse_document(updated)), updated)
        document = parse_document(updated)
        room = document.rooms[0]
        script = scummc_room_source(room, dialogue_animation_cues=dialogue_animation_bindings(
            document, room))
        self.assertIn("waitForMessage();\n            animateActor(", script)
        self.assertIn("animateActor(SpeakerHarborKeeper,28);\n            delay(18);", script)
        self.assertLess(script.index("animateActor(SpeakerHarborKeeper,28);"),
                        script.index("setActorStanding();", script.index("animateActor(SpeakerHarborKeeper,28);")))
        again = edit_dialogue_animation(updated, first, "gesture", False)
        self.assertEqual(dialogue_ending_animation_selection(again, first)[1:],
                         ("ending_pose", 18))
        removed = edit_dialogue_ending_animation(updated, first, None, 0)
        self.assertNotIn('"ending_animation"', removed)
        self.assertEqual(dialogue_ending_animation_selection(removed, first)[1:], (None, 12))
        for duration in (0, -1, 2.5, True):
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                edit_dialogue_ending_animation(raw, first, "ending_pose", duration)
        with self.assertRaisesRegex(ValueError, "indexed COST"):
            edit_dialogue_ending_animation(raw, first, "missing", 12)
        with self.assertRaisesRegex(ValueError, "zuerst"):
            edit_dialogue_ending_animation(raw, "missing", "ending_pose", 12)

    def test_native_speaking_phase_ticks_are_per_line_and_backwards_compatible(self):
        _story, raw = self.fixture()
        first, second = (key for _label, key in dialogue_animation_lines(raw))
        raw = edit_dialogue_animation(raw, first, "gesture", True)
        raw = edit_dialogue_animation(raw, second, "gesture", True)
        self.assertEqual(dialogue_animation_phase_selection(raw, first), (1, 60))
        self.assertNotIn('"start_delay_ticks"', raw)
        self.assertNotIn('"minimum_animation_ticks"', raw)
        revised = edit_dialogue_animation_phases(raw, first, 12, 24)
        self.assertEqual(dialogue_animation_phase_selection(revised, first), (12, 24))
        self.assertEqual(dialogue_animation_phase_selection(revised, second), (1, 60))
        rebuilt = canonical_json(parse_document(revised))
        self.assertEqual(rebuilt, revised)
        room = parse_document(revised).rooms[0]
        script = scummc_room_source(room, dialogue_animation_cues=dialogue_animation_bindings(
            parse_document(revised), room))
        self.assertIn("delay(12);\n            animateActor(", script)
        self.assertIn("delay(24);\n            waitForMessage();", script)
        self.assertIn("delay(1);\n            animateActor(", script)
        self.assertIn("delay(60);\n            waitForMessage();", script)
        reassigned = edit_dialogue_animation(revised, first, "gesture", False)
        self.assertEqual(dialogue_animation_phase_selection(reassigned, first), (12, 24))
        zero = edit_dialogue_animation_phases(reassigned, first, 0, 0)
        self.assertEqual(dialogue_animation_phase_selection(zero, first), (0, 0))
        for start, minimum in ((-1, 20), (1.5, 20), (1, -2), (1, 2.2), (True, 1)):
            with self.subTest(start=start, minimum=minimum), self.assertRaises(ValueError):
                edit_dialogue_animation_phases(revised, first, start, minimum)
        with self.assertRaisesRegex(ValueError, "zuerst"):
            edit_dialogue_animation_phases(raw, "room.unknown", 1, 60)

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "Timeline benötigt Pillow")
    def test_dialogue_frame_timeline_edits_one_direction_and_previews_gif(self):
        _story, raw = self.fixture()
        document = parse_document(raw)
        costume = replace(document.costumes[0], name="WitnessCostume", frames=(
            *document.costumes[0].frames,
            replace(document.costumes[0].frames[0], id="Smile"),
            replace(document.costumes[0].frames[0], id="OpenMouth",
                    pixels=bytes(len(document.costumes[0].frames[0].pixels)))))
        actors = tuple(replace(actor, costume="WitnessCostume")
                       if actor.id == "SpeakerWitness" else actor
                       for actor in document.actors)
        room = document.rooms[0]
        rules = tuple(replace(rule, actor_lines=tuple(
            (key, "SpeakerWitness") for key, _actor in rule.actor_lines))
            for rule in room.talk_rules)
        hotspots = tuple(replace(hotspot, talk_actor_lines=tuple(
            "SpeakerWitness" for _actor in hotspot.talk_actor_lines))
            if hotspot.talk_actor_lines else hotspot for hotspot in room.hotspots)
        raw = canonical_json(replace(document, actors=actors,
            costumes=(*document.costumes, costume),
            rooms=(replace(room, talk_rules=rules, hotspots=hotspots), *document.rooms[1:])))
        first, second = (key for _label, key in dialogue_animation_lines(raw))
        fresh = edit_dialogue_speaking_timeline(raw, first, "W", None,
                                                 "Anhängen", "Smile")
        self.assertEqual(dialogue_speaking_sequence_selection(fresh, first, "W"), "Smile")
        self.assertEqual(dialogue_speaking_sequence_selection(fresh, first, "S"), "Pose")
        raw = assign_dialogue_speaking_sequence(raw, first, "Pose, Smile")
        raw = assign_dialogue_speaking_sequence(raw, second, "OpenMouth, Pose")
        images, steps, frames = dialogue_speaking_timeline(raw, first, "N")
        self.assertEqual(len(images), 2)
        self.assertEqual(steps, (("1. Pose", 0), ("2. Smile", 1)))
        self.assertEqual(frames, ("Pose", "Smile", "OpenMouth"))
        raw = edit_dialogue_speaking_timeline(raw, first, "N", None,
                                               "Anhängen", "OpenMouth")
        raw = edit_dialogue_speaking_timeline(raw, first, "N", 2, "Nach links")
        self.assertEqual(dialogue_speaking_sequence_selection(raw, first, "N"),
                         "Pose, OpenMouth, Smile")
        raw = edit_dialogue_speaking_timeline(raw, first, "N", 0, "Nach rechts")
        raw = edit_dialogue_speaking_timeline(raw, first, "N", 2, "Entfernen")
        self.assertEqual(dialogue_speaking_sequence_selection(raw, first, "N"),
                         "OpenMouth, Pose")
        self.assertEqual(dialogue_speaking_sequence_selection(raw, first, "E"), "Pose, Smile")
        self.assertEqual(dialogue_speaking_sequence_selection(raw, second, "N"),
                         "OpenMouth, Pose")
        with tempfile.TemporaryDirectory() as directory:
            gif = dialogue_speaking_timeline_preview(
                raw, first, "N", 180, Path(directory) / "speaking.gif")
            from PIL import Image
            with Image.open(gif) as picture:
                self.assertEqual(picture.format, "GIF")
                self.assertEqual(picture.n_frames, 2)
            with self.assertRaisesRegex(ValueError, "Millisekunden"):
                dialogue_speaking_timeline_preview(
                    raw, first, "N", 10, Path(directory) / "bad.gif")
        with self.assertRaisesRegex(ValueError, "mindestens ein"):
            single = assign_dialogue_direction_speaking_sequence(raw, first, "N", "Pose")
            edit_dialogue_speaking_timeline(single, first, "N", 0, "Entfernen")
        with self.assertRaisesRegex(ValueError, "am Rand"):
            edit_dialogue_speaking_timeline(raw, first, "N", 0, "Nach links")
        with self.assertRaisesRegex(ValueError, "vorhandenes PNG"):
            edit_dialogue_speaking_timeline(raw, first, "N", None, "Anhängen", "missing")

    def test_two_lines_of_one_npc_have_independent_looping_png_sequences(self):
        _story, raw = self.fixture()
        source = parse_document(raw)
        costume = replace(source.costumes[0], name="WitnessCostume",
                          frames=(*source.costumes[0].frames,
                                  replace(source.costumes[0].frames[0], id="OpenMouth"),
                                  replace(source.costumes[0].frames[0], id="Smile")))
        actors = tuple(replace(actor, costume="WitnessCostume")
                       if actor.id == "SpeakerWitness" else actor
                       for actor in source.actors)
        room = source.rooms[0]
        rules = tuple(replace(rule, actor_lines=tuple(
            (key, "SpeakerWitness") for key, _actor in rule.actor_lines))
            for rule in room.talk_rules)
        hotspots = tuple(replace(hotspot, talk_actor_lines=tuple(
            "SpeakerWitness" for _actor in hotspot.talk_actor_lines))
            if hotspot.talk_actor_lines else hotspot for hotspot in room.hotspots)
        raw = canonical_json(replace(source, actors=actors,
            costumes=(*source.costumes, costume),
            rooms=(replace(room, talk_rules=rules, hotspots=hotspots), *source.rooms[1:])))
        lines = tuple(key for _label, key in dialogue_animation_lines(raw))
        self.assertGreaterEqual(len(lines), 2)
        before_assignments = raw
        raw = assign_dialogue_speaking_sequence(raw, lines[0], "Pose, OpenMouth")
        raw = assign_dialogue_speaking_sequence(raw, lines[1], "Smile, Pose, OpenMouth")
        first = parse_document(raw)
        cue_by_line = {cue.line_id: cue.animation for cue in first.dialogue_animation_cues}
        self.assertNotEqual(cue_by_line[lines[0]], cue_by_line[lines[1]])
        saved = {animation.name: animation for animation in first.costumes[-1].animations}
        self.assertEqual(saved["gesture"].directions[0].commands, ("Pose",))
        self.assertEqual(saved["talk_start"].directions[0].commands, ("Pose",))
        self.assertEqual(saved[cue_by_line[lines[0]]].index, 28)
        self.assertEqual(saved[cue_by_line[lines[1]]].index, 32)
        self.assertTrue(all(direction.loop for direction in saved[cue_by_line[lines[1]]].directions))
        self.assertEqual(dialogue_speaking_sequence_selection(raw, lines[0]), "Pose, OpenMouth")
        self.assertEqual(dialogue_speaking_sequence_selection(raw, lines[1]), "Smile, Pose, OpenMouth")
        revised = assign_dialogue_speaking_sequence(raw, lines[0], "Smile, OpenMouth, Smile")
        updated = parse_document(revised)
        new_saved = {animation.name: animation for animation in updated.costumes[-1].animations}
        self.assertEqual(new_saved[cue_by_line[lines[0]]].index, 28)
        self.assertEqual(new_saved[cue_by_line[lines[1]]], saved[cue_by_line[lines[1]]])
        self.assertEqual(dialogue_speaking_sequence_selection(canonical_json(updated), lines[0]),
                         "Smile, OpenMouth, Smile")
        self.assertEqual(assign_dialogue_speaking_sequence(revised, lines[0],
                         "Smile, OpenMouth, Smile"), revised)
        for invalid in ("", "Smile, Unknown", "Pose, "):
            with self.assertRaises(ValueError):
                assign_dialogue_speaking_sequence(revised, lines[0], invalid)
        with self.assertRaisesRegex(ValueError, "Sprecher-Dialogzeile"):
            assign_dialogue_speaking_sequence(revised, "missing", "Pose")
        bindings = dialogue_animation_bindings(updated, updated.rooms[0])
        script = scummc_room_source(updated.rooms[0], dialogue_animation_cues=bindings)
        self.assertIn("animateActor(SpeakerWitness,28);", script)
        self.assertIn("animateActor(SpeakerWitness,32);", script)
        with tempfile.TemporaryDirectory() as directory:
            export_document(updated, Path(directory))
            source_text = (Path(directory) / "WitnessCostume.scost").read_text()
            self.assertIn("body(Smile, OpenMouth, Smile)", source_text)
            self.assertIn("body(Smile, Pose, OpenMouth)", source_text)

        north = assign_dialogue_direction_speaking_sequence(
            revised, lines[0], "N", "Pose, Smile")
        west = assign_dialogue_direction_speaking_sequence(
            north, lines[0], "W", "OpenMouth, Pose, Smile")
        reloaded = canonical_json(parse_document(west))
        self.assertEqual(dialogue_speaking_sequence_selection(reloaded, lines[0], "N"), "Pose, Smile")
        self.assertEqual(dialogue_speaking_sequence_selection(reloaded, lines[0], "W"),
                         "OpenMouth, Pose, Smile")
        self.assertEqual(dialogue_speaking_sequence_selection(reloaded, lines[0], "E"),
                         "Smile, OpenMouth, Smile")
        self.assertEqual(dialogue_speaking_sequence_selection(reloaded, lines[0], "S"),
                         "Smile, OpenMouth, Smile")
        self.assertEqual(dialogue_speaking_sequence_selection(reloaded, lines[0]), "")
        self.assertEqual(dialogue_speaking_sequence_selection(reloaded, lines[1], "N"),
                         "Smile, Pose, OpenMouth")
        edited = parse_document(reloaded)
        face_animation = next(item for item in edited.costumes[-1].animations
                              if item.name == cue_by_line[lines[0]])
        self.assertEqual(face_animation.index, 28)
        self.assertEqual(next(item for item in edited.costumes[-1].animations
                              if item.name == cue_by_line[lines[1]]), saved[cue_by_line[lines[1]]])
        with self.assertRaisesRegex(ValueError, "Blickrichtung"):
            assign_dialogue_direction_speaking_sequence(reloaded, lines[0], "NW", "Pose")

        # First directional edit of a line copies its already authored
        # channels instead of replacing them with the chosen frame.
        fresh = assign_dialogue_direction_speaking_sequence(
            before_assignments, lines[0], "N", "Smile, Pose")
        self.assertEqual(dialogue_speaking_sequence_selection(fresh, lines[0], "N"), "Smile, Pose")
        self.assertEqual(dialogue_speaking_sequence_selection(fresh, lines[0], "S"), "Pose")

    def fixture(self, branching=False):
        story = dialogue_fixture(EXAMPLE.read_text(encoding="utf-8"),
                                 choices=branching, multispeaker=True)
        document = parse_document(compose_story_project(story))
        costume = document.costumes[0]
        gesture = CostumeAnimation("gesture", tuple(
            CostumeDirection(direction, ("Pose",), False)
            for direction in ("N", "E", "S", "W")), 24)
        talk_start = CostumeAnimation("talk_start", gesture.directions, 16)
        talk_stop = CostumeAnimation("talk_stop", tuple(
            CostumeDirection(direction, ("Pose",))
            for direction in ("N", "E", "S", "W")), 20)
        document = replace(document, costumes=(replace(
            costume, animations=tuple(replace(animation, index=12)
                                      if animation.name == "stand" else animation
                                      for animation in costume.animations)
                         + (talk_start, talk_stop, gesture)),))
        return story, canonical_json(document)

    def test_linear_speaker_cue_survives_project_and_compiles_actor_command(self):
        story, raw = self.fixture()
        lines = dialogue_animation_lines(raw)
        self.assertEqual(len(lines), 2)
        witness = next(key for label, key in lines if label.startswith("SpeakerWitness"))
        self.assertEqual(dialogue_animation_choices(raw, witness), (("gesture",), None, True))
        raw = edit_dialogue_animation(raw, witness, "gesture")
        self.assertEqual(dialogue_animation_choices(raw, witness), (("gesture",), "gesture", True))
        document = parse_document(raw)
        self.assertEqual(canonical_json(document), raw)
        saved = canonical_studio_project(story, raw)
        loaded_story, loaded_native = parse_studio_project(saved)
        rebuilt = parse_document(compose_story_project(loaded_story, loaded_native))
        self.assertEqual(rebuilt.dialogue_animation_cues, document.dialogue_animation_cues)
        source = scummc_room_source(rebuilt.rooms[0],
                                   dialogue_animation_cues=dialogue_animation_bindings(
                                       rebuilt, rebuilt.rooms[0]))
        self.assertIn("animateActor(SpeakerWitness,24);", source)
        self.assertIn("delay(1);\n            animateActor(SpeakerWitness,24);", source)
        self.assertIn("animateActor(SpeakerWitness,24);\n            delay(60);", source)
        self.assertGreater(source.index("animateActor(SpeakerWitness,24);"),
                           source.index('actorSay(SpeakerWitness,"Der Schluessel liegt am Boden.")'))
        self.assertLess(source.index("animateActor(SpeakerWitness,24);"),
                        source.index("waitForMessage();", source.index(
                            'actorSay(SpeakerWitness,"Der Schluessel liegt am Boden.")')))
        wait = source.index("waitForMessage();", source.index(
            'actorSay(SpeakerWitness,"Der Schluessel liegt am Boden.")'))
        self.assertIn("setCurrentActor(SpeakerWitness);\n            setActorStanding();\n"
                      "            setActorTalkFrame(4,5);\n            setCurrentActor(VAR_EGO);", source[wait:])
        self.assertIn("animateActor(SpeakerWitness,12);", source[wait:])
        self.assertNotIn("setActorTalkFrame(6,3);", source)
        self.assertIn("setActorTalkFrame(4,5);", source[wait:])
        self.assertEqual(parse_document(edit_dialogue_animation(raw, witness, None)).dialogue_animation_cues, ())

    def test_branching_reply_and_invalid_costume_fail_closed(self):
        story, raw = self.fixture(branching=True)
        reply = next(key for _label, key in dialogue_animation_lines(raw) if ".reply." in key)
        bound = edit_dialogue_animation(raw, reply, "gesture")
        self.assertEqual(parse_document(bound).dialogue_animation_cues[0].line_id, reply)
        with self.assertRaisesRegex(ValueError, "indexed COST"):
            edit_dialogue_animation(raw, reply, "missing")
        with self.assertRaisesRegex(ValueError, "Sprecher"):
            edit_dialogue_animation(raw, "room.harbor.dialogue.100.opening.0", "gesture")
        changed_story = story.replace("Der Schluessel liegt am Boden.", "Der Weg liegt am Boden.")
        with self.assertRaisesRegex(ValueError, "Stale dialogue animation"):
            compose_story_project(changed_story, bound)

    def test_legacy_animation_without_reset_stays_compatible(self):
        story, raw = self.fixture()
        witness = next(key for label, key in dialogue_animation_lines(raw)
                       if label.startswith("SpeakerWitness"))
        legacy = edit_dialogue_animation(raw, witness, "gesture", False)
        self.assertNotIn("reset_to_stand", legacy)
        self.assertEqual(dialogue_animation_choices(legacy, witness), (("gesture",), "gesture", False))
        document = parse_document(legacy)
        source = scummc_room_source(document.rooms[0],
                                   dialogue_animation_cues=dialogue_animation_bindings(
                                       document, document.rooms[0]))
        self.assertIn("animateActor(SpeakerWitness,24);", source)
        self.assertNotIn("setCurrentActor(SpeakerWitness);\n            setActorStanding();", source)
        with self.assertRaisesRegex(ValueError, "Standpose-Einstellung"):
            edit_dialogue_animation(raw, witness, "gesture", 1)

    def test_consecutive_speakers_reset_their_own_costumes(self):
        _story, raw = self.fixture()
        lines = dialogue_animation_lines(raw)
        for _label, line in lines:
            raw = edit_dialogue_animation(raw, line, "gesture", True)
        document = parse_document(raw)
        source = scummc_room_source(document.rooms[0],
                                   dialogue_animation_cues=dialogue_animation_bindings(
                                       document, document.rooms[0]))
        self.assertEqual(source.count("animateActor(SpeakerHarborKeeper,24);"), 1)
        self.assertEqual(source.count("animateActor(SpeakerWitness,24);"), 1)
        for actor in ("SpeakerHarborKeeper", "SpeakerWitness"):
            self.assertIn(f"setCurrentActor({actor});\n            setActorStanding();\n"
                          "            setActorTalkFrame(4,5);\n            setCurrentActor(VAR_EGO);", source)
            self.assertIn(f"animateActor({actor},12);", source)

        missing = replace(document.costumes[0], animations=tuple(
            animation for animation in document.costumes[0].animations
            if animation.name != "stand"))
        with self.assertRaisesRegex(ValueError, "stand pose"):
            parse_document(canonical_json(replace(document, costumes=(missing,))))
        unindexed = replace(document.costumes[0], animations=tuple(
            replace(animation, index=None) if animation.name == "stand" else animation
            for animation in document.costumes[0].animations))
        with self.assertRaisesRegex(ValueError, "indexed stand pose"):
            parse_document(canonical_json(replace(document, costumes=(unindexed,))))
        missing_talk = replace(document.costumes[0], animations=tuple(
            animation for animation in document.costumes[0].animations
            if animation.name != "talk_start"))
        with self.assertRaisesRegex(ValueError, "matching native talk frames"):
            parse_document(canonical_json(replace(document, costumes=(missing_talk,))))

    def test_saved_speaking_frames_are_selected_per_line_after_roundtrip(self):
        _story, raw = self.fixture()
        document = parse_document(raw)
        costume = replace(document.costumes[0], name="WitnessCostume")
        second_frame = replace(costume.frames[0], id="SecondPose")
        costume = replace(costume, frames=(*costume.frames, second_frame))
        actors = tuple(replace(actor, costume="WitnessCostume")
                       if actor.id == "SpeakerWitness" else actor
                       for actor in document.actors)
        room = document.rooms[0]
        rules = tuple(replace(rule, actor_lines=tuple(
            (line_id, "SpeakerWitness") for line_id, _actor in rule.actor_lines))
            for rule in room.talk_rules)
        hotspots = tuple(replace(hotspot, talk_actor_lines=tuple(
            "SpeakerWitness" for _actor in hotspot.talk_actor_lines))
            if hotspot.talk_actor_lines else hotspot for hotspot in room.hotspots)
        raw = canonical_json(replace(document, actors=actors,
            costumes=(*document.costumes, costume),
            rooms=(replace(room, talk_rules=rules, hotspots=hotspots), *document.rooms[1:])))
        lines = tuple(identity for _label, identity in dialogue_animation_lines(raw))
        self.assertEqual(dialogue_speaking_frame_selection(raw, None), ((), None))
        self.assertEqual(dialogue_speaking_frame_selection(raw, "invalid"), ((), None))
        self.assertEqual(dialogue_speaking_frame_selection(raw, lines[0]),
                         (("Pose", "SecondPose"), None))
        raw = assign_dialogue_speaking_frame(raw, lines[0], "Pose", True)
        raw = assign_dialogue_speaking_frame(raw, lines[1], "SecondPose", True)
        reopened = canonical_json(parse_document(raw))
        self.assertEqual(dialogue_speaking_frame_selection(reopened, lines[0]),
                         (("Pose", "SecondPose"), "Pose"))
        self.assertEqual(dialogue_speaking_frame_selection(reopened, lines[1]),
                         (("Pose", "SecondPose"), "SecondPose"))
        self.assertEqual(dialogue_animation_choices(reopened, lines[1])[1],
                         "pose_SecondPose")

        # Editing a cue or removing it must update/clear the saved selection
        # without altering the other line's imported PNG pose.
        changed = assign_dialogue_speaking_frame(reopened, lines[1], "Pose")
        self.assertEqual(dialogue_speaking_frame_selection(changed, lines[1])[1], "Pose")
        self.assertEqual(dialogue_speaking_frame_selection(changed, lines[0])[1], "Pose")
        removed = edit_dialogue_animation(changed, lines[1], None)
        self.assertEqual(dialogue_speaking_frame_selection(removed, lines[1])[1], None)
        self.assertEqual(dialogue_speaking_frame_selection(removed, lines[0])[1], "Pose")

        # Manually authored multi-frame COST timelines are not equivalent
        # to any single PNG frame and must not be displayed as one.
        native = parse_document(removed)
        figure = next(item for item in native.costumes if item.name == "WitnessCostume")
        gesture = next(item for item in figure.animations if item.name == "gesture")
        complex_animation = replace(gesture, name="pose_complex", index=32,
                                    directions=tuple(
            replace(direction, commands=("Pose", "SecondPose"))
            for direction in gesture.directions))
        revised = replace(figure, animations=(*figure.animations, complex_animation))
        document_with_timeline = replace(native, costumes=tuple(
            revised if item.name == figure.name else item for item in native.costumes))
        complex_raw = edit_dialogue_animation(canonical_json(document_with_timeline),
                                              lines[1], "pose_complex", True)
        self.assertEqual(dialogue_speaking_frame_selection(complex_raw, lines[1]),
                         (("Pose", "SecondPose"), None))

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "PNG-Test benötigt Pillow")
    def test_imported_png_speaking_pose_reaches_native_dialogue_and_costume(self):
        from PIL import Image

        _story, raw = self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            png = root / "speaking.png"
            image = Image.new("RGBA", (12, 12), (0, 0, 0, 0))
            for x in range(2, 10):
                for y in range(2, 10):
                    image.putpixel((x, y), (220, 80, 80, 255))
            image.save(png)
            raw = add_costume_frame(raw, "DialogueFigure", str(png), "SpeakImported")
            raw = set_costume_speaking_pose(raw, "DialogueFigure", "SpeakImported")
            line = next(identity for label, identity in dialogue_animation_lines(raw)
                        if label.startswith("SpeakerWitness"))
            raw = edit_dialogue_animation(raw, line, "gesture", True)
            document = parse_document(raw)
            resources = root / "resources"
            export_document(document, resources)
            costume_source = (resources / "DialogueFigure.scost").read_text(encoding="utf-8")
            room_source = scummc_room_source(document.rooms[0],
                                             dialogue_animation_cues=dialogue_animation_bindings(
                                                 document, document.rooms[0]))
            self.assertIn("anim gesture @ 24", costume_source)
            self.assertIn("anim talk_start @ 16", costume_source)
            self.assertIn("anim talk_stop @ 20", costume_source)
            self.assertIn("body(SpeakImported)", costume_source)
            self.assertEqual(costume_source.count("body(SpeakImported)"), 8)
            self.assertTrue((resources / "DialogueFigure_SpeakImported.bmp").is_file())
            self.assertIn("animateActor(SpeakerWitness,24);", room_source)
            self.assertIn("animateActor(SpeakerWitness,12);", room_source)

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "PNG-Test benötigt Pillow")
    def test_speaker_line_assigns_imported_frame_without_changing_other_speaker(self):
        from PIL import Image

        _story, raw = self.fixture()
        original = parse_document(raw)
        witness = next(line for label, line in dialogue_animation_lines(raw)
                       if label.startswith("SpeakerWitness"))
        with self.assertRaisesRegex(ValueError, "auch von anderen Figuren"):
            assign_dialogue_speaking_frame(raw, witness, "Pose")

        # Real authors can give two speaking characters different native costumes.
        costume = replace(original.costumes[0], name="WitnessCostume")
        actors = tuple(replace(actor, costume="WitnessCostume")
                       if actor.id == "SpeakerWitness" else actor
                       for actor in original.actors)
        raw = canonical_json(replace(original, actors=actors,
                                     costumes=(*original.costumes, costume)))
        with tempfile.TemporaryDirectory() as directory:
            png = Path(directory) / "witness.png"
            Image.new("RGBA", (8, 8), (230, 35, 35, 255)).save(png)
            raw = add_costume_frame(raw, "WitnessCostume", str(png), "WitnessSpeaking")
            self.assertIn("WitnessSpeaking", dialogue_speaking_frames(raw, witness))
            with self.assertRaisesRegex(ValueError, "Costume-Frame"):
                assign_dialogue_speaking_frame(raw, witness, "not-imported")
            updated = assign_dialogue_speaking_frame(raw, witness, "WitnessSpeaking")
            document = parse_document(updated)
            self.assertEqual(document.dialogue_animation_cues[0].animation, "gesture")
            self.assertEqual(document.dialogue_animation_cues[0].line_id, witness)
            self.assertIn("WitnessSpeaking", next(animation for animation in
                document.costumes[1].animations if animation.name == "talk_start")
                .directions[0].commands)
            self.assertEqual(document.costumes[0], original.costumes[0])
            source = scummc_room_source(document.rooms[0],
                dialogue_animation_cues=dialogue_animation_bindings(document, document.rooms[0]))
            self.assertIn("animateActor(SpeakerWitness,24);", source)


    @unittest.skipUnless(importlib.util.find_spec("PIL"), "PNG-Test benötigt Pillow")
    def test_two_lines_same_speaker_keep_independent_png_poses(self):
        from PIL import Image

        _story, raw = self.fixture()
        original = parse_document(raw)
        costume = replace(original.costumes[0], name="WitnessCostume")
        actors = tuple(replace(actor, costume="WitnessCostume")
                       if actor.id == "SpeakerWitness" else actor
                       for actor in original.actors)
        room = original.rooms[0]
        rules = tuple(replace(rule, actor_lines=tuple(
            (key, "SpeakerWitness") for key, _actor in rule.actor_lines))
            for rule in room.talk_rules)
        hotspots = tuple(replace(hotspot, talk_actor_lines=tuple(
            "SpeakerWitness" for _actor in hotspot.talk_actor_lines))
            if hotspot.talk_actor_lines else hotspot for hotspot in room.hotspots)
        raw = canonical_json(replace(original, actors=actors,
            costumes=(*original.costumes, costume),
            rooms=(replace(room, talk_rules=rules, hotspots=hotspots), *original.rooms[1:])))
        lines = tuple(key for _label, key in dialogue_animation_lines(raw))
        self.assertGreaterEqual(len(lines), 2)
        with tempfile.TemporaryDirectory() as directory:
            for name, color in (("SpeakA", (225, 35, 35, 255)),
                                ("SpeakB", (35, 225, 35, 255))):
                path = Path(directory) / (name + ".png")
                Image.new("RGBA", (8, 8), color).save(path)
                raw = add_costume_frame(raw, "WitnessCostume", str(path), name)
            raw = assign_dialogue_speaking_frame(raw, lines[0], "SpeakA")
            raw = assign_dialogue_speaking_frame(raw, lines[1], "SpeakB")
            again = assign_dialogue_speaking_frame(raw, lines[1], "SpeakB")
            self.assertEqual(raw, again)
            document = parse_document(raw)
            native = next(item for item in document.costumes
                          if item.name == "WitnessCostume")
            by_name = {animation.name: animation for animation in native.animations}
            self.assertEqual(by_name["gesture"].directions[0].commands, ("SpeakA",))
            self.assertEqual(by_name["talk_start"].directions[0].commands, ("SpeakA",))
            self.assertEqual(by_name["pose_SpeakB"].directions[0].commands, ("SpeakB",))
            # Render native indexed COST pixels, not source PNG color guesses.
            first_preview = dialogue_speaking_frame_preview(raw, lines[0], "SpeakA")
            second_preview = dialogue_speaking_frame_preview(raw, lines[1], "SpeakB")
            self.assertEqual(first_preview.size, (256, 256))
            self.assertEqual(second_preview.size, (256, 256))
            native_frames = {frame.id: frame for frame in native.frames}
            def native_color(frame_id):
                frame = native_frames[frame_id]
                value = next(value for value in frame.pixels if value != 0)
                return native.palette[native.palette_first + value]
            self.assertEqual(first_preview.getpixel((128, 128)), native_color("SpeakA"))
            self.assertEqual(second_preview.getpixel((128, 128)), native_color("SpeakB"))
            self.assertNotEqual(first_preview.getpixel((128, 128)),
                                second_preview.getpixel((128, 128)))
            self.assertIsNone(dialogue_speaking_frame_preview(raw, None, "SpeakA"))
            self.assertIsNone(dialogue_speaking_frame_preview(raw, lines[0], None))
            with self.assertRaisesRegex(ValueError, "Sprecher-Costume"):
                dialogue_speaking_frame_preview(raw, lines[0], "missing")
            # Tentative frame changes display before a cue is saved.
            tentative = dialogue_speaking_frame_preview(raw, lines[0], "SpeakB")
            self.assertEqual(tentative.getpixel((128, 128)), native_color("SpeakB"))
            self.assertEqual(dialogue_speaking_frame_selection(raw, lines[0])[1], "SpeakA")
            # Direction-specific native COST frames can differ even though
            # the single-PNG dropdown rightly has no unified selection.
            split = replace(by_name["pose_SpeakB"], name="pose_directions", index=32,
                directions=tuple(replace(direction, commands=(
                    ("SpeakA",) if direction.direction in ("N", "W") else ("SpeakB",)))
                    for direction in by_name["pose_SpeakB"].directions))
            varied = replace(native, animations=(*native.animations, split))
            varied_document = replace(document, costumes=tuple(
                varied if entry.name == native.name else entry
                for entry in document.costumes))
            varied_raw = canonical_json(varied_document)
            for direction, frame in (("N", "SpeakA"), ("E", "SpeakB"),
                                     ("S", "SpeakB"), ("W", "SpeakA")):
                rendered, label = dialogue_direction_animation_preview(
                    varied_raw, lines[1], "pose_directions", direction)
                self.assertEqual(rendered.size, (304, 320))
                self.assertEqual(rendered.getpixel((152, 168)), native_color(frame))
                self.assertIn(frame, label)
                self.assertIn("statische Editor-Vorschau", label)
            none, reason = dialogue_direction_animation_preview(
                varied_raw, lines[1], None, "N")
            self.assertIsNone(none)
            self.assertIn("Keine Costume", reason)
            none, reason = dialogue_direction_animation_preview(
                varied_raw, lines[1], "pose_directions", "S")
            self.assertIsNotNone(none)
            with self.assertRaisesRegex(ValueError, "Blickrichtung"):
                dialogue_direction_animation_preview(varied_raw, lines[1],
                                                     "pose_directions", "NW")
            multiline = replace(split, name="pose_multiframe", index=36,
                directions=tuple(replace(direction, commands=("SpeakA", "SpeakB"))
                                 for direction in split.directions))
            with_multiline = replace(varied, animations=(*varied.animations, multiline))
            multi_raw = canonical_json(replace(document, costumes=tuple(
                with_multiline if entry.name == native.name else entry
                for entry in document.costumes)))
            no_image, message = dialogue_direction_animation_preview(
                multi_raw, lines[1], "pose_multiframe", "N")
            self.assertIsNone(no_image)
            self.assertIn("mehrere Frames", message)
            self.assertEqual(by_name["pose_SpeakB"].index, 28)
            self.assertEqual(len([a for a in native.animations
                                  if a.name == "pose_SpeakB"]), 1)
            self.assertEqual({cue.line_id: cue.animation for cue in
                              document.dialogue_animation_cues},
                             {lines[0]: "gesture", lines[1]: "pose_SpeakB"})
            source = scummc_room_source(document.rooms[0],
                dialogue_animation_cues=dialogue_animation_bindings(
                    document, document.rooms[0]))
            self.assertIn("animateActor(SpeakerWitness,24);", source)
            self.assertIn("animateActor(SpeakerWitness,28);", source)
            export_document(document, Path(directory) / "resources")
            scost = (Path(directory) / "resources" / "WitnessCostume.scost").read_text()
            self.assertIn("anim pose_SpeakB @ 28", scost)
            self.assertEqual(scost.count("body(SpeakB)"), 4)


if __name__ == "__main__":
    unittest.main()
