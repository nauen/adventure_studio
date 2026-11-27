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
                                                set_sequence_skippable,
                                                edit_voice_variant, set_default_voice_language)
from adventure_studio.studio_export import export_native_project
from adventure_studio.studio_project import canonical_studio_project, parse_studio_project
from adventure_studio.studio_actors import (add_actor, create_costume, move_actor,
                                           add_costume_frame, set_costume_animation,
                                           costume_frame_names, set_costume_speaking_pose,
                                           set_costume_direction_speaking_pose,
                                           set_costume_direction_speaking_sequence,
                                           costume_direction_speaking_frame,
                                           costume_timeline_images, edit_costume_timeline,
                                           render_costume_preview, set_actor_initial_animation)
from test_scumm_toolchain import fake_upstream


class NativeSequenceEditorTests(unittest.TestCase):
    def test_directional_png_speaking_pose_preserves_other_directions_and_native_slots(self):
        if importlib.util.find_spec("PIL") is None:
            self.skipTest("PNG import requires the optional Studio Pillow dependency")
        from PIL import Image
        from adventure_studio.scumm_costume import costume_source
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "stand.png"
            second = Path(directory) / "north.png"
            Image.new("RGBA", (8, 8), (20, 70, 160, 255)).save(first)
            Image.new("RGBA", (8, 8), (220, 40, 30, 255)).save(second)
            raw = canonical_json(GameDocument("Facing", (scrolling_fixture(), destination_fixture())))
            raw = create_costume(raw, str(first), "Speaker")
            raw = add_costume_frame(raw, "Speaker", str(second), "NorthPose")
            raw = set_costume_speaking_pose(raw, "Speaker", "Pose0")
            raw = set_costume_direction_speaking_pose(raw, "Speaker", "N", "NorthPose")
            costume = parse_document(raw).costumes[0]
            for name, index in (("stand", 12), ("talk_start", 16),
                                ("talk_stop", 20), ("gesture", 24)):
                animation = next(item for item in costume.animations if item.name == name)
                self.assertEqual(animation.index, index)
                frames = {item.direction: item.commands for item in animation.directions}
                self.assertEqual(frames["N"], ("NorthPose",) if name in ("gesture", "talk_start")
                                 else ("Pose0",))
                self.assertEqual(frames["S"], ("Pose0",))
            self.assertEqual(costume_direction_speaking_frame(raw, "Speaker", "N"), "NorthPose")
            self.assertEqual(costume_direction_speaking_frame(raw, "Speaker", "E"), "Pose0")

            self.assertIn("NorthPose", costume_source(costume))
            self.assertEqual(parse_document(canonical_json(parse_document(raw))).costumes[0], costume)
            with self.assertRaisesRegex(ValueError, "vorhandenes Costume-Frame"):
                set_costume_direction_speaking_pose(raw, "Speaker", "W", "Missing")

            animated = set_costume_direction_speaking_sequence(
                raw, "Speaker", "N", "NorthPose, Pose0, NorthPose")
            asset = parse_document(animated).costumes[0]
            for animation_name in ("gesture", "talk_start"):
                animation = next(item for item in asset.animations if item.name == animation_name)
                directions = {item.direction: item for item in animation.directions}
                self.assertEqual(directions["N"].commands, ("NorthPose", "Pose0", "NorthPose"))
                self.assertTrue(directions["N"].loop)
                self.assertEqual(directions["E"].commands, ("Pose0",))
            self.assertIsNone(costume_direction_speaking_frame(animated, "Speaker", "N"))
            for animation_name in ("stand", "talk_stop"):
                self.assertEqual(next(item for item in asset.animations if item.name == animation_name),
                                 next(item for item in costume.animations if item.name == animation_name))
            self.assertIn("N = { body(NorthPose, Pose0, NorthPose) }", costume_source(asset))
            self.assertEqual(parse_document(canonical_json(parse_document(animated))).costumes[0], asset)
            for invalid in ("", "NorthPose, Missing", "NorthPose, "):
                with self.assertRaises(ValueError):
                    set_costume_direction_speaking_sequence(raw, "Speaker", "N", invalid)

    def test_transfer_gameplay_modes_use_distinct_costume_resource_names(self):
        from adventure_studio.scumm_actor_zclip_transfer_probe import author_transfer_project
        from adventure_studio.scumm_two_actor_four_mask_probe import ACTOR_IDS
        modes = ({}, {"profiles": True}, {"profiles": True, "entry_restore": True},
                 {"dynamic": True}, {"restore_profile": True}, {"walk": True}, {"animation": True}, {"facing": True}, {"camera": True}, {"position": True}, {"elevation": True}, {"scale": True}, {"costume_change": True}, {"walk_speed": True})
        names = set()
        with tempfile.TemporaryDirectory() as directory:
            for variant in ("masked", "transparent"):
                for index, mode in enumerate(modes):
                    root = Path(directory) / f"{variant}-{index}"
                    doc = parse_document(author_transfer_project(root, variant, **mode))
                    actor = next(a for a in doc.actors if a.id == ACTOR_IDS[0])
                    self.assertNotIn(actor.costume, names)
                    names.add(actor.costume)
        self.assertEqual(len(names), 28)





    def test_transferred_actor_elevation_roundtrip_and_escape(self):
        from adventure_studio.scumm_assets import scummc_room_source
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        from adventure_studio.scumm_actor_zclip_transfer_probe import author_transfer_project
        from adventure_studio.scumm_two_actor_four_mask_probe import ACTOR_IDS
        with tempfile.TemporaryDirectory() as directory:
            raw = author_transfer_project(Path(directory), "masked")
            actor = ACTOR_IDS[0]
            identity = "Cellar|R06TransferReturn|Open"
            raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                       "Actor Höhe", actor, None, None, 24)
            raw = set_sequence_skippable(raw, identity, True)
            doc = parse_document(raw)
            self.assertEqual(canonical_json(doc), raw)
            self.assertEqual(sequence_step_fields(raw, identity, 0)[:5],
                             ("Actor Höhe", actor, None, None, 24))
            room = next(r for r in doc.rooms if r.name == "Cellar")
            seq = next(s for s in doc.interaction_sequences
                       if (s.room, s.hotspot_id, s.verb) == ("Cellar", "R06TransferReturn", "Open"))
            native = inject_interaction_sequences(scummc_room_source(room), "Cellar",
                                                   (seq,), doc.actors, doc.costumes, room)
            for code in native.split("} override {", 1):
                self.assertIn(f"if (getActorRoom({actor}) == VAR_ROOM)", code)
                self.assertIn("setActorElevation(24);", code)
            for invalid_actor, elevation in ((ACTOR_IDS[1], 24), (actor, 128), (actor, -128)):
                with self.assertRaises(ValueError):
                    append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                         "Actor Höhe", invalid_actor, None, None, elevation)

    def test_transferred_actor_walk_speed_roundtrip_and_escape(self):
        from adventure_studio.scumm_assets import scummc_room_source
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        from adventure_studio.scumm_actor_zclip_transfer_probe import author_transfer_project
        from adventure_studio.scumm_two_actor_four_mask_probe import ACTOR_IDS
        with tempfile.TemporaryDirectory() as directory:
            raw = author_transfer_project(Path(directory), "masked")
            actor = ACTOR_IDS[0]
            identity = "Cellar|R06TransferReturn|Open"
            raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                       "Actor Laufgeschwindigkeit", actor, None, None, 1, 8, 3)
            raw = set_sequence_skippable(raw, identity, True)
            doc = parse_document(raw)
            self.assertEqual(canonical_json(doc), raw)
            self.assertEqual(sequence_step_fields(raw, identity, 0),
                             ("Actor Laufgeschwindigkeit", actor, None, None, 1, 8, 3, "S"))
            room = next(r for r in doc.rooms if r.name == "Cellar")
            seq = next(s for s in doc.interaction_sequences
                       if (s.room, s.hotspot_id, s.verb) == ("Cellar", "R06TransferReturn", "Open"))
            native = inject_interaction_sequences(scummc_room_source(room), "Cellar",
                                                   (seq,), doc.actors, doc.costumes, room)
            for code in native.split("} override {", 1):
                self.assertIn(f"if (getActorRoom({actor}) == VAR_ROOM)", code)
                self.assertIn("setActorWalkSpeed(8,3);", code)
            restored = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                            "Actor Laufgeschwindigkeit", actor, None, None, 1, 2, 1)
            restored_doc = parse_document(restored)
            restored_seq = next(s for s in restored_doc.interaction_sequences
                if (s.room, s.hotspot_id, s.verb) == ("Cellar", "R06TransferReturn", "Open"))
            restored_native = inject_interaction_sequences(scummc_room_source(room), "Cellar",
                (restored_seq,), restored_doc.actors, restored_doc.costumes, room)
            override = restored_native.split("} override {", 1)[1]
            self.assertIn("setActorWalkSpeed(2,1);", override)
            self.assertNotIn("setActorWalkSpeed(8,3);", override)
            for invalid_actor, x, y in ((ACTOR_IDS[1], 8, 3), (actor, 0, 3),
                                         (actor, 17, 3), (actor, 8, 0), (actor, 8, 17),
                                         (actor, 2.5, 3)):
                with self.assertRaises(ValueError):
                    append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                         "Actor Laufgeschwindigkeit", invalid_actor, None, None, 1, x, y)

    def test_transferred_actor_scale_roundtrip_and_escape(self):
        from adventure_studio.scumm_assets import scummc_room_source
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        from adventure_studio.scumm_actor_zclip_transfer_probe import author_transfer_project
        from adventure_studio.scumm_two_actor_four_mask_probe import ACTOR_IDS
        with tempfile.TemporaryDirectory() as directory:
            raw = author_transfer_project(Path(directory), "masked")
            actor = ACTOR_IDS[0]
            identity = "Cellar|R06TransferReturn|Open"
            raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                       "Actor Skalierung", actor, None, None, 128)
            raw = set_sequence_skippable(raw, identity, True)
            doc = parse_document(raw)
            self.assertEqual(canonical_json(doc), raw)
            self.assertEqual(sequence_step_fields(raw, identity, 0)[:5],
                             ("Actor Skalierung", actor, None, None, 128))
            room = next(r for r in doc.rooms if r.name == "Cellar")
            seq = next(s for s in doc.interaction_sequences
                       if (s.room, s.hotspot_id, s.verb) == ("Cellar", "R06TransferReturn", "Open"))
            native = inject_interaction_sequences(scummc_room_source(room), "Cellar",
                                                   (seq,), doc.actors, doc.costumes, room)
            for code in native.split("} override {", 1):
                self.assertIn(f"if (getActorRoom({actor}) == VAR_ROOM)", code)
                self.assertIn("setActorScale(128);", code)
                self.assertIn("setActorIgnoreBoxes();", code)
            restored = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                            "Actor Skalierung", actor, None, None, 0)
            restored_doc = parse_document(restored)
            restored_seq = next(s for s in restored_doc.interaction_sequences
                if (s.room, s.hotspot_id, s.verb) == ("Cellar", "R06TransferReturn", "Open"))
            restored_native = inject_interaction_sequences(scummc_room_source(room), "Cellar",
                (restored_seq,), restored_doc.actors, restored_doc.costumes, room)
            self.assertIn("setActorFollowBoxes();", restored_native.split("} override {", 1)[1])
            for invalid_actor, scale in ((ACTOR_IDS[1], 128), (actor, 256), (actor, -1)):
                with self.assertRaises(ValueError):
                    append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                         "Actor Skalierung", invalid_actor, None, None, scale)

    def test_transferred_actor_voice_uses_native_room_presence(self):
        from dataclasses import replace
        from adventure_studio.scumm_assets import scummc_room_source
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        from adventure_studio.scumm_project import SoundAsset
        from adventure_studio.scumm_actor_zclip_transfer_probe import author_transfer_project
        from adventure_studio.scumm_two_actor_four_mask_probe import ACTOR_IDS
        with tempfile.TemporaryDirectory() as directory:
            raw = author_transfer_project(Path(directory), "masked")
            doc = parse_document(raw)
            raw = canonical_json(replace(doc, sound_assets=(*doc.sound_assets,
                SoundAsset("CellarGreeting", "Cellar", original_voc_effect()),
                SoundAsset("CellarGreetingDE", "Cellar", original_voc_effect(330)))))
            actor = ACTOR_IDS[0]
            raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                       "Gesprochene Zeile", actor, None, "CellarGreeting", None,
                                       subtitle="Hello from the cellar.")
            identity = "Cellar|R06TransferReturn|Open"
            raw = edit_voice_variant(raw, identity, 0, "de", "CellarGreetingDE", "Hallo aus dem Keller.")
            raw = set_sequence_skippable(raw, identity, True)
            doc = parse_document(raw)
            self.assertEqual(canonical_json(doc), raw)
            room = next(r for r in doc.rooms if r.name == "Cellar")
            seq = next(s for s in doc.interaction_sequences
                       if (s.room, s.hotspot_id, s.verb) == ("Cellar", "R06TransferReturn", "Open"))
            native = inject_interaction_sequences(scummc_room_source(room), "Cellar",
                                                   (seq,), doc.actors, doc.costumes, room)
            normal, override = native.split("} override {", 1)
            guard = f"if (getActorRoom({actor}) == VAR_ROOM)"
            self.assertLess(normal.index(guard), normal.index("startSound(CellarGreeting"))
            self.assertIn(f"actorSay({actor},", normal)
            self.assertIn("waitForMessage();", normal)
            for sound in ("CellarGreeting", "CellarGreetingDE"):
                self.assertIn(f"startSound({sound});", normal)
                self.assertIn(f"stopSound({sound});", normal)
                self.assertIn(f"stopSound({sound});", override)
            with self.assertRaises(ValueError):
                append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                     "Gesprochene Zeile", ACTOR_IDS[1], None, "CellarGreeting", None,
                                     subtitle="Not present.")

    def test_transferred_actor_position_uses_native_room_presence(self):
        from adventure_studio.scumm_assets import scummc_room_source
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        from adventure_studio.scumm_actor_zclip_transfer_probe import author_transfer_project
        from adventure_studio.scumm_two_actor_four_mask_probe import ACTOR_IDS
        with tempfile.TemporaryDirectory() as directory:
            raw = author_transfer_project(Path(directory), "masked")
            actor = ACTOR_IDS[0]
            raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                       "Actor versetzen", actor, None, None, None, 140, 85)
            raw = set_sequence_skippable(raw, "Cellar|R06TransferReturn|Open", True)
            doc = parse_document(raw)
            self.assertEqual(canonical_json(doc), raw)
            room = next(r for r in doc.rooms if r.name == "Cellar")
            seq = next(s for s in doc.interaction_sequences
                       if (s.room, s.hotspot_id, s.verb) == ("Cellar", "R06TransferReturn", "Open"))
            native = inject_interaction_sequences(scummc_room_source(room), "Cellar",
                                                   (seq,), doc.actors, doc.costumes, room)
            for code in native.split("} override {", 1):
                self.assertIn(f"if (getActorRoom({actor}) == VAR_ROOM)", code)
                self.assertIn(f"putActorAt({actor}, 140, 85, Cellar);", code)
            with self.assertRaises(ValueError):
                append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                     "Actor versetzen", ACTOR_IDS[1], None, None, None, 140, 85)

    def test_transferred_actor_camera_authoring_roundtrip(self):
        from adventure_studio.scumm_assets import scummc_room_source
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        from adventure_studio.scumm_actor_zclip_transfer_probe import author_transfer_project
        from adventure_studio.scumm_two_actor_four_mask_probe import ACTOR_IDS
        from adventure_studio.studio_sequences import sequence_step_fields, sequence_steps
        with tempfile.TemporaryDirectory() as directory:
            raw = author_transfer_project(Path(directory), "masked")
            actor = ACTOR_IDS[0]
            for kind, actor_id, x in (("Kamera folgt Actor", actor, None),
                                       ("Auf Kamera warten", None, None),
                                       ("Kamera schwenken", None, 160),
                                       ("Auf Kamera warten", None, None)):
                raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                           kind, actor_id, None, None, None, x)
            raw = set_sequence_skippable(raw, "Cellar|R06TransferReturn|Open", True)
            doc = parse_document(raw)
            self.assertEqual(canonical_json(doc), raw)
            identity = "Cellar|R06TransferReturn|Open"
            self.assertEqual(sequence_step_fields(raw, identity, 0)[:2], ("Kamera folgt Actor", actor))
            self.assertEqual(sequence_step_fields(raw, identity, 2)[5], 160)
            self.assertEqual(len(sequence_steps(raw, identity)), 4)
            room = next(r for r in doc.rooms if r.name == "Cellar")
            seq = next(s for s in doc.interaction_sequences
                       if (s.room, s.hotspot_id, s.verb) == ("Cellar", "R06TransferReturn", "Open"))
            native = inject_interaction_sequences(scummc_room_source(room), "Cellar",
                                                   (seq,), doc.actors, doc.costumes, room)
            normal, override = native.split("} override {", 1)
            self.assertIn(f"if (getActorRoom({actor}) == VAR_ROOM)", normal)
            self.assertIn(f"cameraFollowActor({actor});", normal)
            self.assertIn("panCameraTo(160);", normal)
            self.assertEqual(normal.count("waitForCamera();"), 2)
            self.assertIn("panCameraTo(160);", override)
            self.assertIn("waitForCamera();", override)
            self.assertNotIn("cameraFollowActor(", override)
            from dataclasses import replace
            # A final follow plus an authored camera wait must also settle
            # on Escape, while a follow without a wait remains asynchronous.
            for steps, expect_wait in ((seq.steps[:2], True), (seq.steps[:1], False)):
                follow_native = inject_interaction_sequences(
                    scummc_room_source(room), "Cellar",
                    (replace(seq, steps=steps),), doc.actors, doc.costumes, room)
                _, follow_override = follow_native.split("} override {", 1)
                self.assertIn(f"if (getActorRoom({actor}) == VAR_ROOM)", follow_override)
                self.assertIn(f"cameraFollowActor({actor});", follow_override)
                self.assertEqual("waitForCamera();" in follow_override, expect_wait)
            with self.assertRaises(ValueError):
                append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                     "Kamera folgt Actor", ACTOR_IDS[1], None, None, None)

    def test_transferred_actor_facing_uses_native_room_presence(self):
        from adventure_studio.scumm_assets import scummc_room_source
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        from adventure_studio.scumm_actor_zclip_transfer_probe import author_transfer_project
        from adventure_studio.scumm_two_actor_four_mask_probe import ACTOR_IDS
        with tempfile.TemporaryDirectory() as directory:
            raw = author_transfer_project(Path(directory), "masked")
            raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                       "Actor drehen", ACTOR_IDS[0], None, None, None, direction="W")
            raw = set_sequence_skippable(raw, "Cellar|R06TransferReturn|Open", True)
            doc = parse_document(raw)
            self.assertEqual(canonical_json(doc), raw)
            room = next(r for r in doc.rooms if r.name == "Cellar")
            sequence = next(s for s in doc.interaction_sequences
                            if (s.room, s.hotspot_id, s.verb) == ("Cellar", "R06TransferReturn", "Open"))
            native = inject_interaction_sequences(scummc_room_source(room), "Cellar",
                                                   (sequence,), doc.actors, doc.costumes, room)
            normal, override = native.split("} override {", 1)
            actor = ACTOR_IDS[0]
            for code in (normal, override):
                self.assertIn(f"if (getActorRoom({actor}) == VAR_ROOM)", code)
                self.assertIn("setActorDirection(270);", code)
                self.assertIn("setCurrentActor(VAR_EGO);", code)
            with self.assertRaises(ValueError):
                append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                     "Actor drehen", ACTOR_IDS[1], None, None, None, direction="W")
            with self.assertRaises(ValueError):
                append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                     "Actor drehen", actor, None, None, None, direction="NW")

    def test_transferred_actor_animation_uses_native_room_presence(self):
        from adventure_studio.scumm_assets import scummc_room_source
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        from adventure_studio.scumm_actor_zclip_transfer_probe import author_transfer_project
        from adventure_studio.scumm_two_actor_four_mask_probe import ACTOR_IDS
        with tempfile.TemporaryDirectory() as directory:
            raw = author_transfer_project(Path(directory), "masked")
            raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                       "Actor animieren", ACTOR_IDS[0], "gesture", None, None)
            doc = parse_document(raw)
            self.assertEqual(canonical_json(doc), raw)
            room = next(r for r in doc.rooms if r.name == "Cellar")
            sequence = next(s for s in doc.interaction_sequences
                            if (s.room, s.hotspot_id, s.verb) == ("Cellar", "R06TransferReturn", "Open"))
            native = inject_interaction_sequences(scummc_room_source(room), "Cellar",
                                                   (sequence,), doc.actors, doc.costumes, room)
            actor = ACTOR_IDS[0]
            self.assertIn(f"if (getActorRoom({actor}) == VAR_ROOM) {{\n"
                          f"                animateActor({actor},24);", native)
            with self.assertRaises(ValueError):
                append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                     "Actor animieren", ACTOR_IDS[1], "gesture", None, None)
            with self.assertRaises(ValueError):
                append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                     "Actor animieren", actor, "MissingAnimation", None, None)

    def test_transferred_actor_walk_and_wait_use_native_room_presence(self):
        from adventure_studio.scumm_assets import scummc_room_source
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        from adventure_studio.scumm_actor_zclip_transfer_probe import author_transfer_project
        from adventure_studio.scumm_two_actor_four_mask_probe import ACTOR_IDS
        with tempfile.TemporaryDirectory() as directory:
            raw = author_transfer_project(Path(directory), "masked")
            raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                       "Actor laufen lassen", ACTOR_IDS[0], None, None, None, 240, 85)
            raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                       "Auf Actor warten", ACTOR_IDS[0], None, None, None)
            raw = set_sequence_skippable(raw, "Cellar|R06TransferReturn|Open", True)
            doc = parse_document(raw)
            self.assertEqual(canonical_json(doc), raw)
            room = next(r for r in doc.rooms if r.name == "Cellar")
            sequence = next(s for s in doc.interaction_sequences
                            if (s.room, s.hotspot_id, s.verb) == ("Cellar", "R06TransferReturn", "Open"))
            native = inject_interaction_sequences(scummc_room_source(room), "Cellar",
                                                   (sequence,), doc.actors, doc.costumes, room)
            normal, override = native.split("} override {", 1)
            actor = ACTOR_IDS[0]
            guard = f"if (getActorRoom({actor}) == VAR_ROOM)"
            self.assertEqual(normal.count(guard), 2)
            self.assertIn(f"walkActorTo({actor}, 240, 85);", normal)
            self.assertIn(f"waitForActor({actor});", normal)
            self.assertEqual(override.count(guard), 1)
            self.assertIn(f"putActorAt({actor}, 240, 85, Cellar);", override)
            with self.assertRaises(ValueError):
                append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                     "Actor laufen lassen", ACTOR_IDS[1], None, None, None, 240, 85)

    def test_transferred_actor_restores_authored_room_profile_in_native_interaction(self):
        from adventure_studio.scumm_assets import scummc_room_source
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        from adventure_studio.scumm_actor_zclip_transfer_probe import author_transfer_project
        from adventure_studio.scumm_two_actor_four_mask_probe import ACTOR_IDS
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = author_transfer_project(root, "masked")
            with self.assertRaises(ValueError):
                append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                     "Actor Z-Clipping", ACTOR_IDS[0], None, None, -1)
            raw = author_transfer_project(root, "masked", profiles=True)
            raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                       "Actor Z-Clipping", ACTOR_IDS[0], None, None, 0)
            raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                       "Warten", None, None, None, 2)
            raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                       "Actor Z-Clipping", ACTOR_IDS[0], None, None, -1)
            raw = set_sequence_skippable(raw, "Cellar|R06TransferReturn|Open", True)
            doc = parse_document(raw)
            self.assertEqual(canonical_json(doc), raw)
            room = next(room for room in doc.rooms if room.name == "Cellar")
            sequence = next(s for s in doc.interaction_sequences
                            if (s.room, s.hotspot_id, s.verb) == ("Cellar", "R06TransferReturn", "Open"))
            native = inject_interaction_sequences(scummc_room_source(room), "Cellar",
                                                   (sequence,), doc.actors, doc.costumes, room)
            normal, override = native.split("} override {", 1)
            self.assertLess(normal.index("setActorZClip(0);"), normal.index("setActorZClip(1);"))
            self.assertIn("setActorZClip(1);", override)
            self.assertNotIn("setActorZClip(-1);", native)
            guard = f"if (getActorRoom({ACTOR_IDS[0]}) == VAR_ROOM)"
            self.assertEqual(normal.count(guard), 2)
            self.assertEqual(override.count(guard), 1)
            for operator in ("+", "-"):
                redraw = f"setActorElevation(getActorElevation({ACTOR_IDS[0]}) {operator} 1);"
                self.assertEqual(normal.count(redraw), 2)
                self.assertEqual(override.count(redraw), 1)

    def test_restore_profile_probe_rearms_native_start_marker(self):
        from adventure_studio.scumm_actor_zclip_transfer_probe import author_transfer_project
        from adventure_studio.scumm_project import ObjectStateStep, DelayStep
        with tempfile.TemporaryDirectory() as directory:
            raw = author_transfer_project(Path(directory), "masked", restore_profile=True)
            doc = parse_document(raw)
            sequences = {seq.hotspot_id: seq for seq in doc.interaction_sequences
                         if seq.room == "Cellar" and seq.verb == "Close"}
            self.assertEqual(sequences["R06Reveal"].steps[-1], ObjectStateStep("R06Restore", 1))
            self.assertEqual(sequences["R06Restore"].steps[0], ObjectStateStep("R06Restore", 0))
            self.assertEqual(sequences["R06Restore"].steps[1], DelayStep(12))
            room = next(room for room in doc.rooms if room.name == "Cellar")
            restore = next(hotspot for hotspot in room.hotspots if hotspot.id == "R06Restore")
            self.assertEqual((restore.x, restore.y), (180, 100))

    def test_transferred_actor_zclip_requires_native_presence_in_both_paths(self):
        from adventure_studio.scumm_assets import scummc_room_source
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        from adventure_studio.scumm_actor_zclip_transfer_probe import author_transfer_project
        from adventure_studio.scumm_two_actor_four_mask_probe import ACTOR_IDS
        with tempfile.TemporaryDirectory() as directory:
            raw = author_transfer_project(Path(directory), "masked")
            raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                       "Actor Z-Clipping", ACTOR_IDS[0], None, None, 0)
            raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                       "Warten", None, None, None, 2)
            raw = append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                       "Actor Z-Clipping", ACTOR_IDS[0], None, None, 1)
            raw = set_sequence_skippable(raw, "Cellar|R06TransferReturn|Open", True)
            doc = parse_document(raw)
            self.assertEqual(canonical_json(doc), raw)
            room = next(room for room in doc.rooms if room.name == "Cellar")
            sequence = next(s for s in doc.interaction_sequences
                            if (s.room, s.hotspot_id, s.verb) == ("Cellar", "R06TransferReturn", "Open"))
            native = inject_interaction_sequences(scummc_room_source(room), "Cellar",
                                                   (sequence,), doc.actors, doc.costumes, room)
            normal, override = native.split("} override {", 1)
            guard = f"if (getActorRoom({ACTOR_IDS[0]}) == VAR_ROOM)"
            self.assertEqual(normal.count(guard), 2)
            self.assertEqual(override.count(guard), 1)
            for operator in ("+", "-"):
                redraw = f"setActorElevation(getActorElevation({ACTOR_IDS[0]}) {operator} 1);"
                self.assertEqual(normal.count(redraw), 2)
                self.assertEqual(override.count(redraw), 1)
            self.assertIn("setActorZClip(1);", override)
            self.assertNotIn("setActorZClip(0);", override)
            with self.assertRaises(ValueError):
                append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                     "Actor Z-Clipping", ACTOR_IDS[1], None, None, 0)
            with self.assertRaises(ValueError):
                append_sequence_step(raw, "Cellar", "R06TransferReturn", "Open",
                                     "Actor Z-Clipping", ACTOR_IDS[0], None, None, 5)

    def test_actor_zclip_roundtrip_native_export_and_escape(self):
        from dataclasses import replace
        from adventure_studio.scumm_assets import ZPlane, scummc_room_source
        from adventure_studio.scumm_project import ActorZClipStep
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        room = scrolling_fixture()
        width, height = room.geometry.room_width, room.geometry.room_height
        room = replace(room, zplanes=(ZPlane(1, bytes(
            int(x == 400 and y == 100)
            for y in range(height) for x in range(width))),))
        document = GameDocument("ClipProject", (room, destination_fixture()),
                                (gesture_fixture(),),
                                (ActorAsset("Guide", "NativeGesture", "Harbor", 400, 110),))
        raw = canonical_json(document)
        identity = "Harbor|Key|Close"
        for kind, actor, amount in (("Actor Z-Clipping", "Guide", 1),
                                    ("Warten", None, 2),
                                    ("Actor Z-Clipping", "Guide", 0)):
            raw = append_sequence_step(raw, "Harbor", "Key", "Close",
                                       kind, actor, None, None, amount)
        raw = set_sequence_skippable(raw, identity, True)
        parsed = parse_document(raw)
        self.assertEqual(canonical_json(parsed), raw)
        self.assertEqual(parsed.interaction_sequences[0].steps[0], ActorZClipStep("Guide", 1))
        self.assertEqual(parsed.interaction_sequences[0].steps[2], ActorZClipStep("Guide", 0))
        self.assertEqual(sequence_step_fields(raw, identity, 0)[:5],
                         ("Actor Z-Clipping", "Guide", None, None, 1))
        native = inject_interaction_sequences(scummc_room_source(parsed.rooms[0]), "Harbor",
                                               parsed.interaction_sequences, parsed.actors,
                                               parsed.costumes, parsed.rooms[0])
        normal, override = native.split("} override {", 1)
        self.assertLess(normal.index("setActorZClip(1);"), normal.index("setActorZClip(0);"))
        self.assertIn("setCurrentActor(Guide);", normal)
        self.assertIn("setCurrentActor(VAR_EGO);", normal)
        self.assertIn("setActorZClip(0);", override)
        self.assertNotIn("setActorZClip(1);", override)
        restored = replace_sequence_step(raw, identity, 2, "Actor Z-Clipping",
                                         "Guide", None, None, -1)
        restored_doc = parse_document(restored)
        restored_native = inject_interaction_sequences(scummc_room_source(restored_doc.rooms[0]), "Harbor",
                                                         restored_doc.interaction_sequences, restored_doc.actors,
                                                         restored_doc.costumes, restored_doc.rooms[0])
        self.assertIn("setActorZClip(0);", restored_native.split("} override {", 1)[1])
        self.assertNotIn("setActorZClip(-1);", restored_native)
        for plane in (-2, 2, 5, 1.5, True):
            with self.assertRaises(ValueError):
                replace_sequence_step(raw, identity, 0, "Actor Z-Clipping",
                                      "Guide", None, None, plane)
        with self.assertRaises(ValueError):
            replace_sequence_step(raw, identity, 0, "Actor Z-Clipping",
                                  "Missing", None, None, 1)

    def test_story_linked_export_retains_authored_room_zplane(self):
        story = (Path(__file__).resolve().parents[1] / "examples" /
                 "mini_story_chain.json").read_text(encoding="utf-8")
        room = scrolling_fixture()
        width, height = room.geometry.room_width, room.geometry.room_height
        from dataclasses import replace
        from adventure_studio.scumm_assets import ZPlane
        masked = replace(room, zplanes=(ZPlane(1, bytes(
            1 if x == 30 and y == 40 else 0
            for y in range(height) for x in range(width))),))
        native = canonical_json(GameDocument("linked_mask", (masked, destination_fixture())))
        combined = parse_document(compose_story_project(story, native))
        harbor = next(room for room in combined.rooms if room.name == "Harbor")
        self.assertEqual(harbor.zplanes, masked.zplanes)

    def test_spoken_line_language_variants_and_escape_stop_all_sounds(self):
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        from adventure_studio.scumm_project import SoundAsset, VoiceVariant
        from adventure_studio.localization import LanguageCatalog, LocalizedLine, charset_plan
        from adventure_studio.scumm_assets import scummc_room_source
        document = GameDocument("Languages", (scrolling_fixture(), destination_fixture()),
                                sound_assets=(SoundAsset("EnglishVoice", "Harbor", original_voc_effect()),
                                              SoundAsset("GermanVoice", "Harbor", original_voc_effect(330))))
        raw = append_sequence_step(canonical_json(document), "Harbor", "Key", "Close",
                                   "Gesprochene Zeile", None, None, "EnglishVoice", None,
                                   subtitle="I hear a bell.")
        raw = edit_voice_variant(raw, "Harbor|Key|Close", 0, "de", "GermanVoice",
                                 "Ich höre eine Glocke.")
        raw = set_sequence_skippable(raw, "Harbor|Key|Close", True)
        parsed = parse_document(raw)
        voice = parsed.interaction_sequences[0].steps[0]
        self.assertEqual(voice.variants, (VoiceVariant("de", "GermanVoice",
                                                       "Ich höre eine Glocke."),))
        self.assertEqual(canonical_json(parsed), raw)
        revised = replace_sequence_step(raw, "Harbor|Key|Close", 0, "Gesprochene Zeile",
                                        None, None, "EnglishVoice", None,
                                        subtitle="A different bell.")
        self.assertEqual(parse_document(revised).interaction_sequences[0].steps[0].variants,
                         voice.variants)
        plan = charset_plan(LanguageCatalog("en", ("de", "en"), (
            LocalizedLine("voice", (("de", "Ich höre eine Glocke."),
                                     ("en", "I hear a bell."))),)))
        native = inject_interaction_sequences(scummc_room_source(parsed.rooms[0]), "Harbor",
                                              parsed.interaction_sequences, (), (), parsed.rooms[0],
                                              parsed.sound_assets, plan)
        self.assertIn("if(GameLanguage == 25701)", native)
        self.assertIn(r'egoSay("Ich h\x80re eine Glocke.");', native)
        self.assertIn('egoSay("I hear a bell.");', native)
        self.assertEqual(native.count("stopSound(EnglishVoice);"), 2)
        self.assertEqual(native.count("stopSound(GermanVoice);"), 2)
        with self.assertRaisesRegex(ValueError, "unique language"):
            edit_voice_variant(raw, "Harbor|Key|Close", 0, "en", "GermanVoice", "Hello")
        with self.assertRaisesRegex(ValueError, "room VOC"):
            edit_voice_variant(raw, "Harbor|Key|Close", 0, "fr", "Unknown", "Bonjour")
        removed = edit_voice_variant(raw, "Harbor|Key|Close", 0, "de", None, None, True)
        self.assertEqual(parse_document(removed).interaction_sequences[0].steps[0].variants, ())
        other_default = set_default_voice_language(removed, "de")
        self.assertEqual(parse_document(other_default).default_voice_language, "de")
        self.assertEqual(canonical_json(parse_document(other_default)), other_default)

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
        with self.assertRaisesRegex(ValueError, "safe subtitle"):
            append_sequence_step(raw, "Harbor", "Key", "Open", "Gesprochene Zeile",
                                 None, None, "Greeting", None, subtitle='Say "hello"')
        with self.assertRaisesRegex(ValueError, "room VOC"):
            append_sequence_step(raw, "Cellar", "Stairs", "Close", "Gesprochene Zeile",
                                 None, None, "Greeting", None, subtitle="Hello")

    def test_german_voice_subtitle_uses_verified_charset_plan(self):
        from adventure_studio.localization import (LanguageCatalog, LocalizedLine, charset_plan)
        from adventure_studio.scumm_bootstrap import inject_interaction_sequences
        from adventure_studio.scumm_project import SoundAsset
        document = GameDocument("GermanVoice", (scrolling_fixture(), destination_fixture()),
                                sound_assets=(SoundAsset("Greeting", "Harbor", original_voc_effect()),))
        raw = append_sequence_step(canonical_json(document), "Harbor", "Key", "Close",
                                   "Gesprochene Zeile", None, None, "Greeting", None,
                                   subtitle="Ich höre die Glocke.")
        parsed = parse_document(raw)
        self.assertEqual(canonical_json(parsed), raw)
        catalog = LanguageCatalog("en", ("en",),
                                  (LocalizedLine("voice_glyphs", (("en", "ö"),)),))
        from adventure_studio.scumm_assets import scummc_room_source
        source = scummc_room_source(parsed.rooms[0])
        native = inject_interaction_sequences(source, "Harbor", parsed.interaction_sequences,
                                              (), (), parsed.rooms[0], parsed.sound_assets,
                                              charset_plan(catalog))
        self.assertIn(r'egoSay("Ich h\x80re die Glocke.");', native)

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
            self.assertEqual(costume_frame_names(raw, "PixelCostume"), ("Pose0", "Pose1"))
            with self.assertRaisesRegex(ValueError, "vorhandenes Costume-Frame"):
                set_costume_speaking_pose(raw, "PixelCostume", "NotImported")
            raw = set_costume_speaking_pose(raw, "PixelCostume", "Pose1")
            speaking = next(animation for animation in parse_document(raw).costumes[-1].animations
                            if animation.name == "gesture")
            self.assertEqual(speaking.index, 24)
            self.assertEqual({direction.direction for direction in speaking.directions},
                             {"N", "E", "S", "W"})
            self.assertTrue(all(direction.commands == ("Pose1",) and direction.loop
                                for direction in speaking.directions))
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
