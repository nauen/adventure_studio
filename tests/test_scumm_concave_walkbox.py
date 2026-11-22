"""R08 concave aggregate: native authoring and BOXM preservation contract.

The aggregate is concave, but every individual SCUMM v6 BOXD box is convex.
Real Actor route evidence in stock ScummVM remains a separate required gate.
"""

import struct
import tempfile
import unittest
from pathlib import Path

from adventure_studio.scumm_assets import _native_box_file, destination_fixture, scrolling_fixture
from adventure_studio.scumm_project import GameDocument, canonical_json, parse_document
from adventure_studio.studio_sequences import (
    author_room_box_connections, author_room_walkbox, compose_story_project,
)


class ConcaveWalkboxCompositionTests(unittest.TestCase):
    def test_l_shaped_connected_aggregate_survives_studio_json_story_and_boxm(self):
        raw = canonical_json(GameDocument(
            "r08_concave", (scrolling_fixture(), destination_fixture())))
        polygons = (
            "0,110; 220,110; 220,150; 0,150",
            "180,70; 260,70; 260,150; 180,150",
            "260,70; 639,70; 639,110; 260,110",
        )
        for index, polygon in enumerate(polygons, 1):
            raw = author_room_walkbox(raw, "Harbor", index, polygon)
        connected = author_room_box_connections(raw, "Harbor", "1-2; 2-3")
        disconnected = author_room_box_connections(raw, "Harbor", "1-2")

        authored = parse_document(connected)
        room = authored.rooms[0]
        self.assertEqual(len(room.walkboxes), 3)
        self.assertEqual(room.box_routes[1][3], 2)
        self.assertEqual(room.box_routes[3][1], 2)
        self.assertIsNone(parse_document(disconnected).rooms[0].box_routes[1][3])

        saved = parse_document(canonical_json(authored)).rooms[0]
        self.assertEqual(saved.walkboxes, room.walkboxes)
        self.assertEqual(saved.box_routes, room.box_routes)

        story = (Path(__file__).resolve().parents[1] /
                 "examples" / "mini_story_chain.json").read_text(encoding="utf-8")
        composed = parse_document(compose_story_project(story, connected))
        story_room = next(item for item in composed.rooms if item.name == "Harbor")
        self.assertEqual(story_room.walkboxes, room.walkboxes)
        self.assertEqual(story_room.box_routes, room.box_routes)

        native = _native_box_file(story_room)
        self.assertEqual(struct.unpack_from("<8h", native, 9),
                         (0, 110, 220, 110, 220, 150, 0, 150))
        self.assertIn(b"BOXM", native)
        self.assertNotEqual(native, _native_box_file(parse_document(disconnected).rooms[0]))
        with tempfile.TemporaryDirectory() as directory:
            from adventure_studio.scumm_assets import write_room_sources
            write_room_sources(story_room, Path(directory))
            self.assertTrue((Path(directory) / "Harbor.box").is_file())


if __name__ == "__main__":
    unittest.main()
