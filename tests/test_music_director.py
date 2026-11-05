import unittest

from adventure_studio.music_director import (
    MusicCommand, MusicPlan, MusicTrack, MusicTransition,
    compile_immediate_music_event, consolidate_music_plan, orphan_music_tracks,
    resolve_music_event, validate_music_plan,
)


class MusicDirectorTests(unittest.TestCase):
    def setUp(self):
        self.plan = MusicPlan(
            (MusicTrack("HarborTheme", "HarborMidi"),
             MusicTrack("DangerTheme", "DangerMidi"),
             MusicTrack("UnusedTheme", "UnusedMidi")),
            (MusicTransition("EnterHarbor", "HarborTheme", "bar"),
             MusicTransition("MonsterSeen", "DangerTheme", "beat"),
             MusicTransition("MonsterGone", "HarborTheme"),
             MusicTransition("Ending", None)),
            "HarborTheme",
        )

    def test_event_selection_and_modes(self):
        self.assertEqual(resolve_music_event(self.plan, "HarborTheme", "MonsterSeen"),
                         ("DangerTheme", "beat"))
        self.assertEqual(resolve_music_event(self.plan, "DangerTheme", "MonsterGone"),
                         ("HarborTheme", "immediate"))
        self.assertEqual(resolve_music_event(self.plan, "HarborTheme", "Ending"),
                         (None, "immediate"))
        self.assertEqual(resolve_music_event(self.plan, "HarborTheme", "NoMusicChange"),
                         ("HarborTheme", "unchanged"))

    def test_consolidation_reports_orphans_without_deleting(self):
        self.assertEqual(orphan_music_tracks(self.plan), ("UnusedTheme",))
        self.assertEqual(len(self.plan.tracks), 3)

    def test_rejects_unknown_and_duplicate_references(self):
        cases = [
            MusicPlan((MusicTrack("A", "MidiA"),), (MusicTransition("Go", "Unknown"),)),
            MusicPlan((MusicTrack("A", "MidiA"), MusicTrack("A", "MidiB")), ()),
            MusicPlan((MusicTrack("A", "MidiA"),),
                      (MusicTransition("Go", "A"), MusicTransition("Go", None))),
            MusicPlan((MusicTrack("A", "MidiA"),), (MusicTransition("Go", "A", "fadesomehow"),)),
            MusicPlan((MusicTrack("../escape", "MidiA"),), ()),
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                validate_music_plan(case)

    def test_resolving_unknown_current_track_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Unknown current"):
            resolve_music_event(self.plan, "Missing", "EnterHarbor")

    def test_immediate_commands_are_idempotent_and_resolve_asset_identity(self):
        self.assertEqual(compile_immediate_music_event(self.plan, "DangerTheme", "MonsterGone"),
                         ("HarborTheme", MusicCommand("play", "HarborMidi")))
        self.assertEqual(compile_immediate_music_event(self.plan, "HarborTheme", "MonsterGone"),
                         ("HarborTheme", None))
        self.assertEqual(compile_immediate_music_event(self.plan, "HarborTheme", "Ending"),
                         (None, MusicCommand("stop")))
        self.assertEqual(compile_immediate_music_event(self.plan, "HarborTheme", "Other"),
                         ("HarborTheme", None))

    def test_unproven_quantized_transitions_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "unverified beat"):
            compile_immediate_music_event(self.plan, "HarborTheme", "MonsterSeen")
        with self.assertRaisesRegex(ValueError, "unverified bar"):
            compile_immediate_music_event(self.plan, "DangerTheme", "EnterHarbor")
        self.assertEqual(compile_immediate_music_event(self.plan, "HarborTheme", "EnterHarbor"),
                         ("HarborTheme", None))

    def test_consolidation_returns_explicit_removal_report(self):
        result = consolidate_music_plan(self.plan)
        self.assertEqual(result.removed_track_ids, ("UnusedTheme",))
        self.assertEqual(result.removed_asset_ids, ("UnusedMidi",))
        self.assertEqual(len(result.plan.tracks), 2)
        self.assertEqual(len(self.plan.tracks), 3)
        self.assertEqual(consolidate_music_plan(result.plan).removed_track_ids, ())
        self.assertEqual(compile_immediate_music_event(result.plan, "DangerTheme", "MonsterGone"),
                         ("HarborTheme", MusicCommand("play", "HarborMidi")))


if __name__ == "__main__":
    unittest.main()
