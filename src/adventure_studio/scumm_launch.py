"""Headless ScummVM launch smoke test for the isolated research fixture.

Must run under a virtual X display (for example xvfb-run). Process survival
and a captured framebuffer are *not* evidence of gameplay or scrolling.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


def launch_smoke(game_directory: Path, output_directory: Path, seconds: float = 4.0) -> None:
    if not (game_directory / "tentacle.000").is_file() or not (game_directory / "tentacle.001").is_file():
        raise ValueError("Missing isolated tentacle compatibility fixture")
    if seconds <= 0 or seconds > 20:
        raise ValueError("Smoke duration must be between 0 and 20 seconds")
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("A virtual X display is required")

    output_directory.mkdir(parents=True, exist_ok=True)
    log_path = output_directory / "scummvm-launch.log"
    environment = {**os.environ, "SDL_AUDIODRIVER": "dummy"}

    def capture_frame(label: str) -> Path:
        image_path = output_directory / f"scummvm-{label}.xwd"
        preview_path = output_directory / f"scummvm-{label}.png"
        capture = subprocess.run(
            ["xwd", "-root", "-silent", "-out", str(image_path)],
            capture_output=True, text=True, timeout=10, check=False,
        )
        if capture.returncode != 0 or not image_path.is_file() or image_path.stat().st_size < 1024:
            raise RuntimeError(f"X framebuffer capture failed: {capture.stderr}")
        preview = subprocess.run(
            ["convert", str(image_path), str(preview_path)],
            capture_output=True, text=True, timeout=10, check=False,
        )
        if preview.returncode != 0 or not preview_path.is_file() or preview_path.stat().st_size < 1024:
            raise RuntimeError(f"Screenshot PNG conversion failed: {preview.stderr}")
        return preview_path

    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            ["scummvm", f"--path={game_directory.resolve()}", "tentacle"],
            stdout=log,
            stderr=subprocess.STDOUT,
            env=environment,
        )
        try:
            deadline = time.monotonic() + seconds
            start_snapshot_taken = False
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"ScummVM quit early (exit={process.returncode}); see {log_path}")
                if not start_snapshot_taken and time.monotonic() >= deadline - seconds + 0.5:
                    capture_frame("start")
                    start_snapshot_taken = True
                time.sleep(0.1)
            if process.poll() is not None:
                raise RuntimeError(f"ScummVM quit early (exit={process.returncode}); see {log_path}")
            final_snapshot = capture_frame("end")
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
    print(f"ScummVM process survived {seconds:.1f}s; final screenshot: {final_snapshot}")
    print("This does NOT prove game rendering, interactions, camera movement, or save/load.")


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.scumm_launch GAME_DIRECTORY OUTPUT_DIRECTORY")
        return 2
    launch_smoke(Path(sys.argv[1]), Path(sys.argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
