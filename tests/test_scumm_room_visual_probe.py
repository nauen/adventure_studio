import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from adventure_studio.scumm_room_visual_probe import black_costume_pixels


class NativeRoomVisualProbeTests(unittest.TestCase):
    def test_dark_costume_histogram_excludes_bright_background(self):
        histogram = ("  125: (0,0,0) #000000 black\n"
                     "  75: (8,8,8) #080808 dark\n"
                     "  500: (246,173,90) #F6AD5A orange\n"
                     "  12: (30,30,30) #1E1E1E charcoal\n")
        with patch("adventure_studio.scumm_room_visual_probe.subprocess.run",
                   return_value=subprocess.CompletedProcess([], 0, histogram, "")) as runner:
            self.assertEqual(black_costume_pixels(Path("frame.png")), 200)
            self.assertIn("140x105+535+305", runner.call_args.args[0])
