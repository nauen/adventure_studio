"""Integration checks for actual SCUMM v6 data and unmodified ScummVM.

Detection is only the first gate. Launch/play/save/load must be tested before
the target is marked production compatible.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DetectionResult:
    files_valid: bool
    detected: bool
    game_id: str | None
    diagnostic: str


def check_game_files(directory: Path) -> tuple[bool, str]:
    """Require an SCUMM index and data pair. Avoid treating assets as a game."""
    if not directory.is_dir():
        return False, "Game directory is missing"
    indices = {p.stem for p in directory.glob("*.000") if p.is_file() and p.stat().st_size > 0}
    data = {p.stem for p in directory.glob("*.001") if p.is_file() and p.stat().st_size > 0}
    if not indices & data:
        return False, "Missing non-empty matching .000/.001 SCUMM pair"
    return True, "SCUMM file pair present (format not yet verified)"


def detect(directory: Path, executable: str = "scummvm", timeout: float = 15.0) -> DetectionResult:
    files_valid, diagnostic = check_game_files(directory)
    if not files_valid:
        return DetectionResult(False, False, None, diagnostic)
    try:
        result = subprocess.run([executable, f"--path={directory.resolve()}", "--detect"],
                                capture_output=True, text=True, timeout=timeout, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        return DetectionResult(True, False, None, f"ScummVM unavailable: {error}")
    output = (result.stdout + "\n" + result.stderr).strip()
    # Detection output is version-sensitive. A parsable ID is required, not
    # merely process exit code 0 or an arbitrary game's name in the output.
    found = re.search(r"(?im)^\s*(scumm:[a-z0-9_-]+)\s+", output)
    if result.returncode != 0 or not found:
        return DetectionResult(True, False, None, f"Game not recognized (exit={result.returncode}): {output[:600]}")
    return DetectionResult(True, True, found.group(1), "ScummVM detected the game; playability still unverified")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m adventure_studio.scumm_probe GAME_DIRECTORY")
        return 2
    result = detect(Path(sys.argv[1]))
    print(result)
    return 0 if result.detected else 1


if __name__ == "__main__":
    raise SystemExit(main())
