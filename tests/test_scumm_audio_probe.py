import unittest

from adventure_studio.scumm_audio_probe import summarize_audio_bytes


class AudioProbeTests(unittest.TestCase):
    def test_rejects_absent_or_silent_audio(self):
        self.assertFalse(summarize_audio_bytes(b"")["pcm_activity_detected"])
        self.assertFalse(summarize_audio_bytes(bytes(8192))["pcm_activity_detected"])
        self.assertFalse(summarize_audio_bytes(bytes([128]) * 8192)["pcm_activity_detected"])

    def test_recognizes_non_silent_pcm_payload(self):
        sample = bytes((0, 20, 255, 10)) * 4096
        report = summarize_audio_bytes(sample)
        self.assertTrue(report["pcm_activity_detected"])
        self.assertEqual(report["bytes"], 16384)


if __name__ == "__main__":
    unittest.main()
