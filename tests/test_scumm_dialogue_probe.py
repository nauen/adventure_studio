import unittest

from adventure_studio.scumm_dialogue_probe import detect_answer_transition, initial_dialogue_ready


class DialogueProbeTests(unittest.TestCase):
    def test_waits_for_actor_after_background_renders(self):
        self.assertFalse(initial_dialogue_ready(False, 0, 0))
        self.assertFalse(initial_dialogue_ready(True, 0, 0))
        self.assertFalse(initial_dialogue_ready(True, 39, 0))
        self.assertFalse(initial_dialogue_ready(True, 50, 10))
        self.assertTrue(initial_dialogue_ready(True, 40, 0))

    def test_requires_absent_then_visible_then_absent(self):
        self.assertTrue(detect_answer_transition(0, 250, 0))
        for counts in ((30, 250, 0), (0, 20, 0), (0, 250, 100)):
            with self.subTest(counts=counts):
                self.assertFalse(detect_answer_transition(*counts))

    def test_rejects_invalid_counts(self):
        for counts in ((True, 200, 0), (-1, 200, 0), (0, 200, 0.1)):
            with self.subTest(counts=counts), self.assertRaises(ValueError):
                detect_answer_transition(*counts)


if __name__ == "__main__":
    unittest.main()

