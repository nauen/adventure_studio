"""Linear conversations use native Actors for each authored speaker."""

from pathlib import Path
import unittest

from adventure_studio.dialogue_demo import dialogue_fixture
from adventure_studio.scumm_assets import scummc_room_source
from adventure_studio.scumm_project import canonical_json, parse_document
from adventure_studio.story_document import parse_story_document
from adventure_studio.story_to_scumm import compile_story_to_scumm


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "mini_story.json"


class LinearMultispeakerTests(unittest.TestCase):
    def test_two_speakers_without_answers_have_native_actor_speech(self):
        raw = dialogue_fixture(EXAMPLE.read_text(encoding="utf-8"), multispeaker=True)
        game = compile_story_to_scumm(parse_story_document(raw))
        room = game.rooms[0]
        self.assertFalse(room.talk_rules)
        hotspot = next(h for h in room.hotspots if h.id == "HarborKeeper")
        self.assertEqual(hotspot.talk_actor_lines,
                         ("SpeakerHarborKeeper", "SpeakerWitness"))
        self.assertEqual(tuple(actor.id for actor in game.actors),
                         ("SpeakerHarborKeeper", "SpeakerWitness"))
        source = scummc_room_source(room)
        self.assertIn('actorSay(SpeakerHarborKeeper,"Was suchst du hier?");', source)
        self.assertIn('actorSay(SpeakerWitness,"Der Schluessel liegt am Boden.");', source)
        self.assertEqual(canonical_json(parse_document(canonical_json(game))), canonical_json(game))

    def test_existing_single_speaker_linear_dialogue_remains_unchanged(self):
        raw = dialogue_fixture(EXAMPLE.read_text(encoding="utf-8"))
        game = compile_story_to_scumm(parse_story_document(raw))
        self.assertFalse(game.actors)
        self.assertFalse(next(h for h in game.rooms[0].hotspots
                              if h.id == "HarborKeeper").talk_actor_lines)
        self.assertIn('egoSay("Was suchst du hier?");', scummc_room_source(game.rooms[0]))


if __name__ == "__main__":
    unittest.main()
