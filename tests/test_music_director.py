import unittest

from adventure_studio.music_director import (
    MusicPlan, MusicTrack, MusicTransition, orphan_music_tracks,
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


if __name__ == "__main__":
    unittest.main()
