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
        self.assertIn(".[studio]", data["postCreateCommand"])
        self.assertEqual(data["postStartCommand"], "bash .devcontainer/start-studio.sh")

    def test_launcher_is_valid_bash(self):
        if shutil.which("bash") is None:
            self.skipTest("Bash is not available on this host")
        subprocess.run(["bash", "-n", str(ROOT / ".devcontainer/start-studio.sh")], check=True)


if __name__ == "__main__":
    unittest.main()
