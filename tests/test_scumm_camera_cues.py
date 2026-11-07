"""Native SCUMM-v6 horizontal camera source operations and project roundtrip."""

import unittest
from dataclasses import replace

from adventure_studio.scumm_assets import CameraCue, _validate, scummc_room_source
from adventure_studio.scumm_project import GameDocument, canonical_json, parse_document
from adventure_studio.scumm_room_fixture import native_room
from adventure_studio.scumm_camera_probe import verify_camera_pan


class CameraCueTests(unittest.TestCase):
    def test_native_camera_sequence_is_emitted_in_given_order(self):
        room = replace(native_room(), camera_cues=(
            CameraCue("set", 160), CameraCue("pan", 480), CameraCue("wait"),
            CameraCue("set", 240), CameraCue("follow_ego"),
        ))
        src = scummc_room_source(room)
        expected = ("setCameraAt(160);", "panCameraTo(480);", "waitForCamera();",
                    "setCameraAt(240);", "cameraFollowActor(VAR_EGO);")
        positions = [src.index(text, src.index("local script entry()")) for text in expected]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(src.count("cameraFollowActor(VAR_EGO);"), 1)

    def test_camera_json_roundtrip(self):
        room = replace(native_room(), hotspots=(), use_rules=(), combine_rules=(), goal_text="Camera reached", camera_cues=(CameraCue("set", 160),
                          CameraCue("pan", 480), CameraCue("wait")))
        original = GameDocument("CameraDemo", (room,))
        raw = canonical_json(original)
        self.assertEqual(canonical_json(parse_document(raw)), raw)

    def test_invalid_ops_or_coordinates_rejected(self):
        for cue in (CameraCue("zoom", 100), CameraCue("pan", -1),
                    CameraCue("set", 640), CameraCue("wait", 100),
                    CameraCue("pan", True)):
            with self.subTest(cue=cue), self.assertRaises(ValueError):
                _validate(replace(native_room(), camera_cues=(cue,)))

    def test_existing_room_keeps_follow_behavior(self):
        self.assertIn("cameraFollowActor(VAR_EGO);", scummc_room_source(native_room()))

    def test_native_pan_acceptance(self):
        verify_camera_pan(10001)
        with self.assertRaises(RuntimeError):
            verify_camera_pan(9999)

