"""Real NPC dialogue line bindings survive Studio authoring and story rebuilds."""

import unittest
from dataclasses import replace
from pathlib import Path

from adventure_studio.dialogue_demo import dialogue_fixture
from adventure_studio.localization import LanguageCatalog, LocalizedLine
from adventure_studio.scumm_assets import scummc_room_source
from adventure_studio.scumm_project import (SoundAsset, canonical_json, parse_document)
from adventure_studio.scumm_voc_fixture import original_voc_effect
from adventure_studio.story_document import parse_story_document
from adventure_studio.story_localization import story_text_inventory
from adventure_studio.story_to_scumm import compile_story_to_scumm
from adventure_studio.studio_sequences import (compose_story_project, dialogue_voice_lines,
                                               edit_dialogue_voice)


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "mini_story.json"


class DialogueVoiceTests(unittest.TestCase):
    def fixture(self):
        story = dialogue_fixture(EXAMPLE.read_text(encoding="utf-8"), choices=True)
        document = compile_story_to_scumm(parse_story_document(story))
        document = replace(document, sound_assets=(
            SoundAsset("KeeperEnglish", "Harbor", original_voc_effect()),
            SoundAsset("KeeperGerman", "Harbor", original_voc_effect(frequency=330)),))
        return story, canonical_json(document)

    def test_dialogue_opening_and_answer_replies_use_authored_voc_languages(self):
        story, raw = self.fixture()
        choices = dialogue_voice_lines(raw)
        self.assertTrue(any(".opening." in identity for _label, identity in choices))
        self.assertTrue(any(".reply." in identity for _label, identity in choices))
        opening = next(identity for _label, identity in choices if ".opening." in identity)
        answer = next(identity for _label, identity in choices if ".reply." in identity)
        raw = edit_dialogue_voice(raw, opening, "en", "KeeperEnglish")
        raw = edit_dialogue_voice(raw, opening, "de", "KeeperGerman")
        raw = edit_dialogue_voice(raw, answer, "en", "KeeperEnglish")
        doc = parse_document(raw)
        self.assertEqual(canonical_json(doc), raw)
        self.assertEqual(len(doc.dialogue_voice_cues), 2)
        self.assertEqual(next(cue for cue in doc.dialogue_voice_cues
                              if cue.line_id == opening).variants, (("de", "KeeperGerman"),))
        recomposed = parse_document(compose_story_project(story, raw))
        self.assertEqual(recomposed.dialogue_voice_cues, doc.dialogue_voice_cues)
        catalog = LanguageCatalog("en", ("de", "en"), tuple(
            LocalizedLine(key, (("de", value), ("en", value)))
            for key, value in story_text_inventory(doc).items()))
        source = scummc_room_source(doc.rooms[0], catalog, dialogue_voice_cues=doc.dialogue_voice_cues)
        self.assertIn("startSound(KeeperGerman)", source)
        self.assertIn("stopSound(KeeperGerman)", source)
        self.assertIn("startSound(KeeperEnglish)", source)
        self.assertEqual(source.count("startSound(KeeperGerman)"), 1)
        self.assertIn("GameLanguage == 25701", source)

    def test_missing_recording_and_stale_story_text_fail_closed(self):
        story, raw = self.fixture()
        opening = next(identity for _label, identity in dialogue_voice_lines(raw)
                       if ".opening." in identity)
        with self.assertRaisesRegex(ValueError, "Standardsprache"):
            edit_dialogue_voice(raw, opening, "de", "KeeperGerman")
        with self.assertRaisesRegex(ValueError, "room VOC"):
            edit_dialogue_voice(raw, opening, "en", "Missing")
        raw = edit_dialogue_voice(raw, opening, "en", "KeeperEnglish")
        with self.assertRaisesRegex(ValueError, "stale"):
            changed = parse_document(raw)
            changed_room = changed.rooms[0]
            first = changed_room.talk_rules[0]
            modified = replace(changed_room, talk_rules=(replace(
                first, opening_lines=("A different greeting.", *first.opening_lines[1:])),))
            canonical_json(replace(changed, rooms=(modified, *changed.rooms[1:])))
        removed = edit_dialogue_voice(raw, opening, "en", None, True)
        self.assertEqual(parse_document(removed).dialogue_voice_cues, ())


if __name__ == "__main__":
    unittest.main()
