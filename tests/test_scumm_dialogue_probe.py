import unittest

from adventure_studio.scumm_dialogue_probe import detect_answer_transition


class DialogueProbeTests(unittest.TestCase):
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
