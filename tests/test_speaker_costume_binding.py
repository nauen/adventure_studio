"""A Story NPC can use a real PNG-authored native COST asset."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from adventure_studio.dialogue_demo import dialogue_fixture
from adventure_studio.scumm_project import parse_document, export_document
from adventure_studio.studio_actors import create_costume, set_actor_costume
from adventure_studio.studio_project import canonical_studio_project, parse_studio_project
from adventure_studio.studio_sequences import compose_story_project


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "mini_story.json"


class SpeakerCostumeBindingTests(unittest.TestCase):
    def test_png_costume_replaces_story_speaker_pose_in_export(self):
        from PIL import Image

        story = dialogue_fixture(EXAMPLE.read_text(encoding="utf-8"), multispeaker=True)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            png = root / "witness.png"
            picture = Image.new("RGBA", (12, 16), (0, 0, 0, 0))
            for x in range(3, 9):
                for y in range(2, 14):
                    picture.putpixel((x, y), (70, 210, 90, 255))
            picture.save(png)

            native = compose_story_project(story)
            native = create_costume(native, str(png), "WitnessArt")
            native = set_actor_costume(native, "SpeakerWitness", "WitnessArt")
            combined = compose_story_project(story, native)
            document = parse_document(combined)
            speaker = next(actor for actor in document.actors if actor.id == "SpeakerWitness")
            self.assertEqual(speaker.costume, "WitnessArt")
            self.assertEqual(next(actor.costume for actor in document.actors
                                  if actor.id == "SpeakerHarborKeeper"), "DialogueFigure")
            self.assertEqual(next(frame.width for costume in document.costumes
                                  if costume.name == "WitnessArt" for frame in costume.frames), 12)

            packaged = canonical_studio_project(story, native)
            restored_story, restored_native = parse_studio_project(packaged)
            self.assertEqual(parse_document(compose_story_project(restored_story, restored_native)), document)
            resources = root / "resources"
            resources.mkdir()
            export_document(document, resources)
            self.assertTrue((resources / "WitnessArt.scost").is_file())

    def test_rejects_missing_actor_or_costume(self):
        story = dialogue_fixture(EXAMPLE.read_text(encoding="utf-8"), multispeaker=True)
        native = compose_story_project(story)
        with self.assertRaisesRegex(ValueError, "Actor"):
            set_actor_costume(native, "Missing", "DialogueFigure")
        with self.assertRaisesRegex(ValueError, "Costume"):
            set_actor_costume(native, "SpeakerWitness", "Missing")


if __name__ == "__main__":
    unittest.main()
