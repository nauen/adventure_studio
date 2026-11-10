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
                                                assign_dialogue_direction_speaking_sequence,
                                                dialogue_speaking_sequence_selection,
                                                dialogue_speaking_timeline,
                                                edit_dialogue_speaking_timeline,
                                                dialogue_speaking_timeline_preview)
from adventure_studio.studio_sequences import (
    dialogue_animation_phase_selection, edit_dialogue_animation_phases,
    dialogue_ending_animation_selection, edit_dialogue_ending_animation,
    dialogue_ending_timeline, assign_dialogue_ending_sequence,
    edit_dialogue_ending_timeline, dialogue_ending_timeline_preview)


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "mini_story.json"


class DialogueAnimationTests(unittest.TestCase):
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
