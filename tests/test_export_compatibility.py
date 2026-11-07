import unittest
from dataclasses import replace
from pathlib import Path

from adventure_studio.export_compatibility import assess_export
from adventure_studio.story import Item, Placement
from adventure_studio.story_document import canonical_story_json, parse_story_document
from adventure_studio.story_to_scumm import compile_story_to_scumm
from adventure_studio.studio_service import add_decoration, change_position, scene_preview


SAMPLE = (Path(__file__).resolve().parents[1] / "examples/mini_story_chain.json").read_text(encoding="utf-8")


class ExportCompatibilityTests(unittest.TestCase):
    def test_known_blockers_are_typed_targeted_and_all_reported(self):
        original = parse_story_document(SAMPLE)
        extended = replace(original,
            items=original.items + tuple(Item(f"Decor{i}", f"Decor {i}", "Room prop", "Harbor", "decoration")
                                          for i in range(5)),
            placements=(Placement("Key", 700, 250),))
        report = assess_export(extended)
        self.assertFalse(report.exportable)
        self.assertEqual([(b.code, b.entity_kind, b.entity_id) for b in report.blockers], [
            ("AUTOMATIC_DECORATION_LAYOUT_LIMIT", "scene", "Harbor"),
            ("FIXTURE_ROOM_GEOMETRY", "item", "Key")])
        self.assertTrue(all(b.target_id == "scummvm-scumm6" for b in report.blockers))
        self.assertEqual(report, assess_export(extended))
        with self.assertRaises(ValueError):
            compile_story_to_scumm(extended)

    def test_unknown_adapter_limit_is_explicit_not_guessed_from_exception_text(self):
        story = parse_story_document(SAMPLE)
        # Invalid authoring documents are never accepted at the JSON boundary;
        # use a valid second chapter for the adapter capability test.
        from adventure_studio.story import Chapter
        modified = replace(story, chapters=(*story.chapters, Chapter("Second", "Act 2", "Later")))
        report = assess_export(modified)
        self.assertEqual(report.blockers[0].code, "CHAPTER_ROUTE_UNSUPPORTED")
        unreferenced = replace(story, items=(*story.items,
                                            Item("Loose", "Loose", "Unused pickup", "Harbor")))
        fallback = assess_export(unreferenced)
        self.assertEqual(len(fallback.blockers), 1)
        self.assertEqual(fallback.blockers[0].code, "ADAPTER_REJECTED")
        self.assertEqual(fallback.blockers[0].entity_id, "Harbor")

    def test_preview_survives_unexportable_story_and_shows_all_objects(self):
        current = SAMPLE
        for index in range(5):
            current = add_decoration(current, "Harbor", f"Decor{index}", f"Dekor {index}", "Room prop").story_json
        current = change_position(current, "Decor4", 900, 270).story_json
        width, height, pixels, palette, hotspots = scene_preview(current, "Harbor")
        self.assertEqual((width, height), (640, 200))
        self.assertEqual(len(pixels), width * height)
        self.assertTrue(palette)
        self.assertEqual(sum(label.startswith("Dekor") for label, *_ in hotspots), 5)
        self.assertTrue(any("outside export room" in label for label, *_ in hotspots))
        self.assertEqual(parse_story_document(canonical_story_json(parse_story_document(current))).placements[-1],
                         Placement("Decor4", 900, 270))

    def test_zero_one_two_and_many_decorations_remain_authorable(self):
        base = parse_story_document(SAMPLE)
        for count in (0, 1, 2, 5, 12):
            with self.subTest(count=count):
                extra = tuple(Item(f"Dec{i}", f"Decoration {i}", "Room prop", "Archive", "decoration")
                              for i in range(count))
                raw = canonical_story_json(replace(base, items=base.items + extra))
                parsed = parse_story_document(raw)
                self.assertEqual(len(parsed.items), len(base.items) + count)
                self.assertEqual(len([h for h in scene_preview(raw, "Archive")[4]
                                      if h[0].startswith("Decoration")]), count)
                report = assess_export(parsed)
                self.assertEqual(any(b.code == "AUTOMATIC_DECORATION_LAYOUT_LIMIT"
                                     for b in report.blockers), count > 4)

    def test_json_boundary_does_not_limit_story_to_128_entities_or_32_requirements(self):
        base = parse_story_document(SAMPLE)
        extra_decor = tuple(Item(f"Dec{i}", f"Decoration {i}", "Room prop", "Harbor", "decoration")
                            for i in range(129))
        expanded = replace(base, items=base.items + extra_decor)
        raw = canonical_story_json(expanded)
        self.assertEqual(parse_story_document(raw), expanded)

        extra_pickups = tuple(Item(f"Pickup{i}", f"Pickup {i}", "Puzzle item", "Harbor")
                              for i in range(33))
        first_puzzle = base.puzzles[0]
        many_requirements = replace(base,
            items=base.items + extra_pickups,
            puzzles=(replace(first_puzzle, requires=first_puzzle.requires + tuple(
                item.id for item in extra_pickups)), *base.puzzles[1:]))
        self.assertEqual(parse_story_document(canonical_story_json(many_requirements)), many_requirements)


if __name__ == "__main__":
    unittest.main()
