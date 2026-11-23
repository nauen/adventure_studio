"""R06 #280: native staggered Actor turn tests; no synthetic V claims."""
from __future__ import annotations

from dataclasses import replace
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from adventure_studio.scumm_project import parse_document
from adventure_studio.scumm_opposing_actor_probe import ACTOR_IDS
from adventure_studio.scumm_staggered_return_probe import (
    author_staggered_native_return, assert_staggered_native_return,
    verify_staggered_native_return,
)


def trace(xs):
    return [{"frame": str(i), "seconds": float(i) * 0.3, "world_x": x}
            for i, x in enumerate(xs)]


class NativeStaggeredReturnTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Studio PNG fixture requires Pillow")
    def test_three_native_control_games_and_distinct_costume_names(self):
        unique = set()
        with TemporaryDirectory() as directory:
            for variant in ("masked", "transparent", "wrong-box"):
                doc = parse_document(author_staggered_native_return(
                    Path(directory) / variant, variant=variant))
                verdict = assert_staggered_native_return(doc, variant=variant)
                self.assertTrue(verdict["staggered_native_return_authored"])
                self.assertFalse(verdict["staggered_native_return_pixels_verified"])
                costume = doc.costumes[-1].name
                self.assertNotIn(costume, unique)
                unique.add(costume)
                self.assertTrue(all(a.costume == costume for a in doc.actors
                                    if a.id in ACTOR_IDS))

    @unittest.skipUnless(find_spec("PIL"), "Studio PNG fixture requires Pillow")
    def test_no_early_return_of_b_allowed(self):
        with TemporaryDirectory() as directory:
            doc = parse_document(author_staggered_native_return(Path(directory)))
            sequence = next(s for s in doc.interaction_sequences if (
                s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close"))
            malformed = replace(sequence, steps=sequence.steps[:11] + sequence.steps[12:])
            bad = replace(doc, interaction_sequences=tuple(
                malformed if s is sequence else s for s in doc.interaction_sequences
            ))
            with self.assertRaisesRegex(RuntimeError, "precede B"):
                assert_staggered_native_return(bad)

    def test_visual_stagger_required_before_b_reverses(self):
        outbound_a = [260 + i * 25 for i in range(11)]
        outbound_b = [540 - i * 25 for i in range(11)]
        inbound_a = [510 - i * 25 for i in range(1, 11)]
        inbound_b = [290, 290, 290, 315, 340, 365, 390, 415, 440, 465]
        a = trace(outbound_a + inbound_a)
        b = trace(outbound_b + inbound_b)
        self.assertTrue(verify_staggered_native_return({
            ACTOR_IDS[0]: a, ACTOR_IDS[1]: b,
        })["staggered_native_return_verified"])
        with self.assertRaisesRegex(RuntimeError, "while B remains stopped"):
            verify_staggered_native_return({
                ACTOR_IDS[0]: a,
                ACTOR_IDS[1]: trace(outbound_b + [290 + i * 25 for i in range(1, 11)]),
            })
        with self.assertRaisesRegex(RuntimeError, "did not visibly reverse"):
            verify_staggered_native_return({
                ACTOR_IDS[0]: a,
                ACTOR_IDS[1]: trace(outbound_b + [290] * 10),
            })


if __name__ == "__main__":
    unittest.main()
