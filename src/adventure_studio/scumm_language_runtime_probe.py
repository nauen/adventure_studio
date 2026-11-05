"""Launch a font-ready SCUMM fixture and capture language-key screenshots.

This is an observable runtime smoke test, not OCR or a pixel-perfect glyph proof.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path


def language_runtime_probe(game: Path, output: Path) -> dict:
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("Language probe requires Xvfb DISPLAY")
    if any(not (game / f"tentacle.{suffix}").is_file() for suffix in ("000", "001")):
        raise ValueError("Missing SCUMM game data")
    output.mkdir(parents=True, exist_ok=True)
    log_path = output / "scummvm.log"
    results = {}
    environment = {**os.environ, "SDL_AUDIODRIVER": "dummy"}
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(["scummvm", f"--path={game.resolve()}", "tentacle"],
                                   stdout=log, stderr=subprocess.STDOUT, env=environment)
        try:
            time.sleep(5)
            if process.poll() is not None:
                raise RuntimeError("ScummVM exited before language input")
            # Keep Polish selected while changing rooms, then repeat the
            # translated line without changing GameLanguage.
            for key, code in (("1", "de"), ("4", "ja"), ("5", "pl"),
                              ("0", "room_after_pl"), ("6", "pl_after_room")):
                subprocess.run(["xdotool", "key", key], check=True, timeout=10)
                time.sleep(2)
                if process.poll() is not None:
                    raise RuntimeError(f"ScummVM exited after selecting {code}")
                raw = output / f"{code}.xwd"
                png = output / f"{code}.png"
                subprocess.run(["xwd", "-root", "-silent", "-out", str(raw)],
                               check=True, timeout=10)
                subprocess.run(["convert", str(raw), str(png)], check=True, timeout=10)
                if png.stat().st_size < 1000:
                    raise RuntimeError(f"Invalid {code} screenshot")
                results[code] = png.name
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    report = {"engine_survived_key_selection": True,
              "room_transition_probe_attempted": True,
              "language_persistence_visually_verified": False,
              "screenshots": results,
              "glyph_rendering_verified": False}
    (output / "language-runtime-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.scumm_language_runtime_probe GAME OUTPUT")
        return 2
    print(json.dumps(language_runtime_probe(Path(sys.argv[1]), Path(sys.argv[2])),
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
