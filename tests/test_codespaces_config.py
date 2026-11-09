import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CodespacesConfigTests(unittest.TestCase):
    def test_port_is_forwarded_and_studio_starts_automatically(self):
        data = json.loads((ROOT / ".devcontainer/devcontainer.json").read_text(encoding="utf-8"))
        self.assertIn(7860, data["forwardPorts"])
        self.assertEqual(data["portsAttributes"]["7860"]["onAutoForward"], "openBrowser")
        self.assertNotEqual(data["portsAttributes"]["7860"].get("visibility"), "public")
        self.assertEqual(data["postCreateCommand"], "bash .devcontainer/setup.sh")
        self.assertEqual(data["postStartCommand"], "bash .devcontainer/start-studio.sh")

    def test_launcher_is_valid_bash(self):
        if shutil.which("bash") is None:
            self.skipTest("Bash is not available on this host")
        for filename in ("start-studio.sh", "setup.sh", "install-scummc.sh"):
            subprocess.run(["bash", "-n", str(ROOT / ".devcontainer" / filename)], check=True)
        pinned = (ROOT / ".devcontainer/install-scummc.sh").read_text(encoding="utf-8")
        self.assertIn("2f61ce0f7b5051e920876dc4b71935dc99f38fff", pinned)


if __name__ == "__main__":
    unittest.main()
