import unittest

from adventure_studio.scumm_audio_probe import compare_audio_activity, summarize_audio_bytes


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

    def test_music_must_exceed_silent_control(self):
        music = summarize_audio_bytes(bytes((0, 20, 255, 10)) * 4096)
        control = summarize_audio_bytes(bytes(16384))
        self.assertTrue(compare_audio_activity(music, control))
        self.assertFalse(compare_audio_activity(control, music))
        self.assertFalse(compare_audio_activity(music, music))


if __name__ == "__main__":
    unittest.main()
