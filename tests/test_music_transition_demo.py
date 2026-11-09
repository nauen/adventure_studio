import tempfile
import unittest
from pathlib import Path

from adventure_studio.music_transition_demo import TRACKS, add_room_music_switch, build
from adventure_studio.scumm_assets import scummc_room_source
from adventure_studio.scumm_project import parse_document
from adventure_studio.story_document import parse_story_document
from adventure_studio.story_to_scumm import compile_story_to_scumm


STORY = Path(__file__).resolve().parents[1] / "examples" / "mini_story_chain.json"


class MusicTransitionDemoTests(unittest.TestCase):
    def test_story_room_entry_starts_distinct_midi_resources(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            game = build(STORY, directory)
            self.assertEqual(tuple(room.music_id for room in game.rooms[:2]),
                             ("HarborTheme", "CellarTheme"))
            self.assertEqual(len(game.rooms[0].palette_cycles), 1)
            self.assertIn("cycle Water", scummc_room_source(game.rooms[0]))
            self.assertEqual(parse_document((directory / "project.json").read_text()), game)
            for index, (track_id, _) in enumerate(TRACKS):
                self.assertIn(f"startMusic({track_id});", scummc_room_source(game.rooms[index]))
                self.assertTrue((directory / "resources" / f"{track_id}.mid").is_file())
            self.assertNotEqual((directory / "resources/HarborTheme.mid").read_bytes(),
                                (directory / "resources/CellarTheme.mid").read_bytes())
            self.assertIsNone(game.rooms[2].music_id)

    def test_fixture_rejects_ambiguous_existing_music(self):
        story = parse_story_document(STORY.read_text(encoding="utf-8"))
        game = compile_story_to_scumm(story)
        modified = add_room_music_switch(game)
        with self.assertRaisesRegex(ValueError, "overwrite"):
            add_room_music_switch(modified)


if __name__ == "__main__":
    unittest.main()
