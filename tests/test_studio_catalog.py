import unittest
import importlib.util
from pathlib import Path

from adventure_studio.studio_catalog import relationship_svg, story_catalog
from adventure_studio.studio_gradio import catalog_view
from adventure_studio.studio_service import change_position


SAMPLE = (Path(__file__).resolve().parents[1] / "examples/mini_story_chain.json").read_text(encoding="utf-8")


class StudioCatalogTests(unittest.TestCase):
    def test_lists_locations_dependencies_and_transitions(self):
        catalog = story_catalog(SAMPLE)
        self.assertEqual(len(catalog.chapters), 1)
        self.assertEqual(len(catalog.scenes), 3)
        self.assertIn(("chapter", "intro", "scene", "Harbor", "enthält"), catalog.edges)
        self.assertIn(("item", "Key", "puzzle", "OpenCellar", "benötigt"), catalog.edges)
        self.assertIn(("puzzle", "OpenCellar", "scene", "Cellar", "öffnet"), catalog.edges)
        self.assertIn(("Key", "Schluessel", "Harbor", "pickup", "automatisch"), catalog.items)

    def test_position_is_reflected_without_changing_any_story(self):
        raw = change_position(SAMPLE, "Key", 270, 120).story_json
        catalog = story_catalog(raw)
        self.assertIn(("Key", "Schluessel", "Harbor", "pickup", "270, 120"), catalog.items)
        self.assertEqual(story_catalog(raw), catalog)

    def test_graph_has_nodes_and_escapes_text(self):
        svg = relationship_svg(SAMPLE)
        self.assertIn("<svg ", svg)
        self.assertIn("OpenCellar", svg)
        self.assertIn("marker-end", svg)
        self.assertNotIn("<script", svg)
        from adventure_studio.story_document import parse_story_document, canonical_story_json
        from dataclasses import replace
        story = parse_story_document(SAMPLE)
        modified = replace(story, chapters=(replace(story.chapters[0], title="<script>alert(1)</script>"),))
        rendered = relationship_svg(canonical_story_json(modified))
        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn("<script>", rendered)

    def test_room_gallery_contains_images(self):
        view = catalog_view(SAMPLE)
        self.assertEqual(len(view), 13)
        self.assertEqual(len(view[11]), 3 if importlib.util.find_spec("PIL") else 0)
        self.assertIn("Figuren", view[0])

    def test_dialogue_choice_nodes_are_visible_even_when_terminal(self):
        from adventure_studio.dialogue_demo import dialogue_fixture
        raw = dialogue_fixture(SAMPLE, choices=True)
        catalog = story_catalog(raw)
        self.assertEqual(len(catalog.dialogue_choices), 2)
        for choice_id, node_id, label, next_node in catalog.dialogue_choices:
            self.assertIn(("dialogue_node", node_id, "dialogue_choice", choice_id, "Antwort"), catalog.edges)
            self.assertTrue(label)
            self.assertTrue(next_node)
            if next_node != "Ende":
                self.assertIn(("dialogue_choice", choice_id, "dialogue_node", next_node, "führt zu"), catalog.edges)
            self.assertIn(choice_id, relationship_svg(raw))


if __name__ == "__main__":
    unittest.main()
