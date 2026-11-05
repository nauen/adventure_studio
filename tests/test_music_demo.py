import unittest
from dataclasses import replace
from pathlib import Path

from adventure_studio.music_demo import add_music_entry, original_midi_theme
from adventure_studio.scumm_assets import scummc_room_source, indexed_bmp
from adventure_studio.scumm_project import canonical_json, parse_document
from adventure_studio.story_document import parse_story_document
from adventure_studio.story_to_scumm import compile_story_to_scumm


class MusicDemoTests(unittest.TestCase):
    @staticmethod
    def game():
        path = Path(__file__).resolve().parents[1] / "examples" / "mini_story.json"
        return compile_story_to_scumm(parse_story_document(path.read_text(encoding="utf-8")))

    def test_generated_midi_has_smf_header_and_duration_events(self):
        midi = original_midi_theme()
        self.assertEqual(midi[:4], b"MThd")
        self.assertEqual(midi[8:14], b"\x00\x00\x00\x01\x01\xe0")
        self.assertEqual(midi[14:18], b"MTrk")
        self.assertEqual(int.from_bytes(midi[18:22], "big"), len(midi) - 22)
        self.assertTrue(midi.endswith(b"\xff\x2f\x00"))
        self.assertEqual(midi, original_midi_theme())

    def test_opt_in_music_source_and_json_roundtrip(self):
        original = self.game()
        game = add_music_entry(original)
        source = scummc_room_source(game.rooms[0])
        self.assertIn('sound HarborTheme = "HarborTheme.soun";', source)
        self.assertIn("startMusic(HarborTheme);", source)
        self.assertNotIn("startMusic", scummc_room_source(original.rooms[0]))
        self.assertEqual(original.rooms[0].pixels, game.rooms[0].pixels)
        self.assertEqual(parse_document(canonical_json(game)), game)

    def test_sound_resource_name_cannot_escape_directory(self):
        room = self.game().rooms[0]
        with self.assertRaisesRegex(ValueError, "music resource ID"):
            indexed_bmp(replace(room, music_id="../attack"))


if __name__ == "__main__":
    unittest.main()
