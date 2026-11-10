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
from adventure_studio.studio_actors import add_costume_frame, set_costume_speaking_pose
from adventure_studio.studio_project import canonical_studio_project, parse_studio_project
from adventure_studio.studio_sequences import (compose_story_project, dialogue_animation_lines,
                                                dialogue_animation_choices, edit_dialogue_animation,
                                                dialogue_speaking_frames,
                                                dialogue_speaking_frame_selection,
                                                assign_dialogue_speaking_frame)


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "mini_story.json"


class DialogueAnimationTests(unittest.TestCase):
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
        raw = canonical_json(replace(document, actors=actors,
            costumes=(*document.costumes, costume),
            rooms=(replace(room, talk_rules=rules), *document.rooms[1:])))
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
        complex_gesture = next(item for item in figure.animations if item.name == "gesture")
        complex_gesture = replace(complex_gesture, directions=tuple(
            replace(direction, commands=("Pose", "SecondPose"))
            for direction in complex_gesture.directions))
        revised = replace(figure, animations=tuple(
            complex_gesture if anim.name == "gesture" else anim for anim in figure.animations))
        document_with_timeline = replace(native, costumes=tuple(
            revised if item.name == figure.name else item for item in native.costumes))
        complex_raw = edit_dialogue_animation(canonical_json(document_with_timeline),
                                              lines[1], "gesture", False)
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
        raw = canonical_json(replace(original, actors=actors,
            costumes=(*original.costumes, costume),
            rooms=(replace(room, talk_rules=rules), *original.rooms[1:])))
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
