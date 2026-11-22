"""R06 #268: fail-closed JSON-v1/Story bindings for two native Actors."""
from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from adventure_studio.scumm_project import parse_document, canonical_json
from adventure_studio.scumm_two_actor_four_mask_probe import (
    ACTOR_IDS, author_two_actor_four_mask_project, assert_native_two_actor_authoring,
    verify_two_actor_native_walks,
)


class TwoActorFourMaskAuthoringTests(unittest.TestCase):
    def test_two_independent_actors_survive_product_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            document = parse_document(
                author_two_actor_four_mask_project(Path(tmp)))
            result = assert_native_two_actor_authoring(
                parse_document(canonical_json(document)))
        self.assertEqual(result["actor_ids"], list(ACTOR_IDS))
        self.assertTrue(result["distinct_actor_positions"])
        self.assertTrue(result["camera_roundtrip_authored"])
        self.assertFalse(result["independent_actor_motion_verified"])
        self.assertFalse(result["per_actor_native_occlusion_verified"])

    def test_missing_actor_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            document = parse_document(
                author_two_actor_four_mask_project(Path(tmp)))
        changed = replace(document, actors=document.actors[:-1])
        with self.assertRaisesRegex(RuntimeError, "independent Actors missing"):
            assert_native_two_actor_authoring(changed)

    def test_overlapping_actor_positions_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            document = parse_document(
                author_two_actor_four_mask_project(Path(tmp)))
        first = document.actors[-2]
        second = replace(document.actors[-1], x=first.x, y=first.y)
        changed = replace(document, actors=(*document.actors[:-1], second))
        with self.assertRaisesRegex(RuntimeError, "world positions changed"):
            assert_native_two_actor_authoring(changed)

    def test_missing_independent_walk_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            document = parse_document(
                author_two_actor_four_mask_project(Path(tmp)))
        sequence = document.interaction_sequences[-1]
        changed = replace(document, interaction_sequences=(
            *document.interaction_sequences[:-1],
            replace(sequence, steps=sequence.steps[1:])))
        with self.assertRaisesRegex(RuntimeError, "walk commands missing"):
            assert_native_two_actor_authoring(changed)

    def test_short_actor_route_rejected(self):
        from adventure_studio.scumm_project import WalkActorStep
        with tempfile.TemporaryDirectory() as tmp:
            document = parse_document(
                author_two_actor_four_mask_project(Path(tmp)))
        sequence = document.interaction_sequences[-1]
        short_route = replace(sequence, steps=(
            sequence.steps[0], WalkActorStep(ACTOR_IDS[1], 390, 115),
            *sequence.steps[2:]))
        changed = replace(document, interaction_sequences=(
            *document.interaction_sequences[:-1], short_route))
        with self.assertRaisesRegex(RuntimeError, "walk commands missing"):
            assert_native_two_actor_authoring(changed)

    def test_native_tracks_require_both_independent_costume_routes(self):
        def trace(start):
            return [{"frame": str(i), "seconds": i * 0.2,
                     "world_x": x, "camera_x": 320, "screen_x": x + start}
                    for i, x in enumerate((190, 220, 270, 330, 380,
                                           410, 460, 520, 540))]
        valid = {ACTOR_IDS[0]: trace(0), ACTOR_IDS[1]: trace(15)}
        result = verify_two_actor_native_walks(valid)
        self.assertTrue(result["two_independent_native_actor_walks_verified"])
        with self.assertRaisesRegex(RuntimeError, "independently measured"):
            verify_two_actor_native_walks({
                ACTOR_IDS[0]: trace(0), ACTOR_IDS[1]: trace(0)})
        with self.assertRaisesRegex(RuntimeError, "did not independently walk"):
            verify_two_actor_native_walks({
                ACTOR_IDS[0]: trace(0),
                ACTOR_IDS[1]: [{**row, "world_x": 220} for row in trace(15)]})
        with self.assertRaisesRegex(RuntimeError, "every native mask zone"):
            verify_two_actor_native_walks({
                ACTOR_IDS[0]: trace(0),
                ACTOR_IDS[1]: [{**row, "world_x": 550 if row["world_x"] >= 320
                                else row["world_x"]} for row in trace(15)]})

    def test_wrong_box_mask_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            document = parse_document(
                author_two_actor_four_mask_project(Path(tmp)))
        room = document.rooms[0]
        wrong = replace(room, walkboxes=(
            *room.walkboxes[:-1], replace(room.walkboxes[-1], mask=0)))
        changed = replace(document, rooms=(wrong, *document.rooms[1:]))
        with self.assertRaisesRegex(RuntimeError, "BOXD mask assignments"):
            assert_native_two_actor_authoring(changed)


if __name__ == "__main__":
    unittest.main()
