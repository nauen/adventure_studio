"""Headless ScummVM launch smoke test for the isolated research fixture.

Must run under a virtual X display (for example xvfb-run). Process survival
and a captured framebuffer are *not* evidence of gameplay or scrolling.
"""

from __future__ import annotations

import os
import json
import re
import subprocess
import sys
import time
from pathlib import Path


def parse_changed_pixels(metric: str) -> int:
    """Parse ImageMagick's absolute-error metric, rejecting ambiguous output."""
    if not re.fullmatch(r"\s*\d+\s*", metric):
        raise ValueError(f"Unexpected ImageMagick AE metric: {metric[:120]!r}")
    return int(metric.strip())


def parse_srgb_pixel(value: str) -> tuple[int, int, int]:
    """Read one 8-bit ImageMagick pixel without accepting arbitrary output."""
    gray = re.fullmatch(r"gray\((\d{1,3})\)", value.strip())
    if gray:
        channel = int(gray.group(1))
        if channel > 255:
            raise ValueError("ImageMagick gray channel out of range")
        return (channel, channel, channel)
    match = re.fullmatch(r"srgb\((\d{1,3}),(\d{1,3}),(\d{1,3})\)", value.strip())
    if not match:
        raise ValueError(f"Unexpected ImageMagick pixel format: {value[:100]!r}")
    color = tuple(map(int, match.groups()))
    if any(channel > 255 for channel in color):
        raise ValueError("ImageMagick RGB channel out of range")
    return color


def scene_pixel(output_directory: Path, frame: str) -> tuple[int, int, int]:
    """Read the right-side diagnostic sky marker in our fixed Xvfb viewport."""
    screenshot = output_directory / f"scummvm-{frame}.png"
    result = subprocess.run(
        ["convert", str(screenshot), "-format", "%[pixel:p{700,280}]", "info:"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Could not sample scene pixel: {result.stderr}")
    return parse_srgb_pixel(result.stdout)


def close_rgb(actual: tuple[int, int, int], expected: tuple[int, int, int], tolerance: int = 25) -> bool:
    return all(abs(a - e) <= tolerance for a, e in zip(actual, expected))


def count_gold_pixels(histogram: str) -> int:
    """Count the fixture's key pixels in ImageMagick RGB histogram output."""
    total = 0
    for line in histogram.splitlines():
        match = re.match(r"^\s*(\d+):\s*\((\d+),(\d+),(\d+)\)", line)
        if match:
            count, red, green, blue = map(int, match.groups())
            if close_rgb((red, green, blue), (255, 220, 75), tolerance=15):
                total += count
    return total


def visible_key_pixels(output_directory: Path, frame: str = "end") -> int:
    """Inspect the cropped game viewport, excluding the SCUMM verb GUI."""
    if frame not in ("end", "pickup"):
        raise ValueError("Invalid screenshot frame")
    screenshot = output_directory / f"scummvm-{frame}.png"
    result = subprocess.run(
        ["convert", str(screenshot), "-crop", "640x288+192+184", "+repage",
         "-format", "%c", "histogram:info:"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Could not inspect room colors: {result.stderr}")
    return count_gold_pixels(result.stdout)


def inventory_key_pixels(output_directory: Path) -> int:
    """Count visible key-colored pixels in SCUMM's lower verb/inventory UI."""
    screenshot = output_directory / "scummvm-pickup.png"
    result = subprocess.run(
        ["convert", str(screenshot), "-crop", "640x112+192+472", "+repage",
         "-format", "%c", "histogram:info:"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Could not inspect inventory colors: {result.stderr}")
    return count_gold_pixels(result.stdout)


def parse_key_bounds(bounds: str) -> tuple[int, int]:
    """Convert trimmed sprite bounds into absolute Xvfb click coordinates."""
    match = re.fullmatch(r"(\d+)x(\d+)\+(\d+)\+(\d+)", bounds.strip())
    if not match:
        raise ValueError(f"Unexpected sprite bounds: {bounds[:100]!r}")
    width, height, x, y = map(int, match.groups())
    if not (1 <= width <= 640 and 1 <= height <= 288 and x + width <= 640 and y + height <= 288):
        raise ValueError("Key sprite bounds outside game viewport")
    return 192 + x + width // 2, 184 + y + height // 2


def key_center(output_directory: Path, frame: str = "end") -> tuple[int, int]:
    """Locate the visible key silhouette, rather than assuming camera offset."""
    if frame not in ("end", "pre-pickup"):
        raise ValueError("Invalid key location frame")
    screenshot = output_directory / f"scummvm-{frame}.png"
    result = subprocess.run(
        ["convert", str(screenshot), "-crop", "640x288+192+184", "+repage",
         "-fuzz", "8%", "-fill", "white", "-opaque", "#FFDC4B",
         "-fill", "black", "+opaque", "white", "-trim", "-format", "%wx%h%O", "info:"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Could not locate key sprite: {result.stderr}")
    return parse_key_bounds(result.stdout)


def compare_frames(output_directory: Path, minimum_changed_pixels: int = 500) -> int:
    """Require visible frame variation; this alone does not prove scrolling."""
    if type(minimum_changed_pixels) is not int or minimum_changed_pixels < 1:
        raise ValueError("Invalid minimum changed pixel count")
    start = output_directory / "scummvm-start.png"
    end = output_directory / "scummvm-end.png"
    diff = output_directory / "scummvm-diff.png"
    result = subprocess.run(
        ["compare", "-metric", "AE", "-fuzz", "5%", str(start), str(end), str(diff)],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f"ImageMagick compare failed: {result.stderr}")
    count = parse_changed_pixels(result.stderr)
    start_rgb = scene_pixel(output_directory, "start")
    end_rgb = scene_pixel(output_directory, "end")
    # SCUMM's 320x200 viewport is scaled 2x and centered inside our fixed
    # 1024x768 Xvfb screen. The fixture's sky is blue in the first half and
    # orange in the second. This tests the *visible* camera pan signature.
    scroll_signature = close_rgb(start_rgb, (70, 130, 190)) and close_rgb(end_rgb, (240, 175, 95))
    key_pixels = visible_key_pixels(output_directory)
    (output_directory / "scummvm-frame-report.json").write_text(
        json.dumps({
            "changed_pixels": count,
            "minimum_changed_pixels": minimum_changed_pixels,
            "frame_variation_passed": count >= minimum_changed_pixels,
            "scene_probe_pixel": [700, 280],
            "start_rgb": start_rgb,
            "end_rgb": end_rgb,
            "scroll_color_signature_passed": scroll_signature,
            "visible_key_pixels": key_pixels,
            "key_sprite_visible": key_pixels >= 40,
            "smooth_scrolling_proven": False,
        }, indent=2) + "\n", encoding="utf-8",
    )
    if count < minimum_changed_pixels:
        raise RuntimeError(f"Insufficient visual variation: {count} changed pixels")
    if not scroll_signature:
        raise RuntimeError(f"Expected blue-to-orange scroll marker missing: {start_rgb} -> {end_rgb}")
    if key_pixels < 40:
        raise RuntimeError(f"Expected key sprite missing from room: {key_pixels} gold pixels")
    return count


def launch_smoke(game_directory: Path, output_directory: Path, seconds: float = 6.0) -> None:
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
        if preview.returncode != 0 or not preview_path.is_file() or preview_path.stat().st_size < 64:
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
            readiness_deadline = time.monotonic() + 8.0
            while time.monotonic() < readiness_deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"ScummVM quit early (exit={process.returncode}); see {log_path}")
                capture_frame("start")
                if close_rgb(scene_pixel(output_directory, "start"), (70, 130, 190)):
                    break
                time.sleep(0.3)
            else:
                raise RuntimeError("Blue initial room was not visible within 8 seconds")
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"ScummVM quit early (exit={process.returncode}); see {log_path}")
                time.sleep(0.1)
            if process.poll() is not None:
                raise RuntimeError(f"ScummVM quit early (exit={process.returncode}); see {log_path}")
            final_snapshot = capture_frame("end")
            changed = compare_frames(output_directory)
            # First choose the verb, then locate the key again: the camera
            # continues to move while the actor is walking.
            verb_click = subprocess.run(
                ["xdotool", "mousemove", "328", "506", "click", "1"],
                capture_output=True, text=True, timeout=5, check=False,
            )
            if verb_click.returncode:
                raise RuntimeError(f"Mouse input failed: {verb_click.stderr}")
            time.sleep(0.3)
            capture_frame("pre-pickup")
            key_x, key_y = key_center(output_directory, "pre-pickup")
            click = subprocess.run(
                ["xdotool", "mousemove", str(key_x), str(key_y), "click", "1"],
                capture_output=True, text=True, timeout=5, check=False,
            )
            if click.returncode:
                raise RuntimeError(f"Key mouse input failed: {click.stderr}")
            picked_up = False
            remaining = visible_key_pixels(output_directory)
            inventory_pixels = 0
            pickup_deadline = time.monotonic() + 15.0
            while time.monotonic() < pickup_deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"ScummVM quit during pickup (exit={process.returncode})")
                capture_frame("pickup")
                remaining = visible_key_pixels(output_directory, "pickup")
                inventory_pixels = inventory_key_pixels(output_directory)
                if remaining < 10 and inventory_pixels >= 40:
                    picked_up = True
                    break
                time.sleep(0.4)
            (output_directory / "scummvm-interaction-report.json").write_text(
                json.dumps({"verb": "PickUp", "key_click": [key_x, key_y],
                            "remaining_gold_pixels": remaining,
                            "inventory_gold_pixels": inventory_pixels,
                            "key_removed_from_room": picked_up}, indent=2) + "\n",
                encoding="utf-8",
            )
            if not picked_up:
                raise RuntimeError(f"Pickup/inventory mismatch: room={remaining}, inventory={inventory_pixels} gold pixels")
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
    print(f"ScummVM showed the blue room, then survived {seconds:.1f}s; final screenshot: {final_snapshot}")
    print(f"Visible frame variation: {changed} changed pixels (5% color tolerance)")
    print(f"Pickup moved the key from room to inventory at ({key_x}, {key_y}).")
    print("Camera and inventory icon passed; save/load remains unverified.")


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.scumm_launch GAME_DIRECTORY OUTPUT_DIRECTORY")
        return 2
    launch_smoke(Path(sys.argv[1]), Path(sys.argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
