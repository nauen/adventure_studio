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

from .scumm_recipe_plan import plan_recipes


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


def should_retry_open_door_exit(open_pixels: int, *, already_retried: bool) -> bool:
    """Retry an exit click only once and only while the door is visibly open."""
    return not already_retried and type(open_pixels) is int and open_pixels >= 40


def count_gold_pixels(histogram: str) -> int:
    """Count the fixture's key pixels in ImageMagick RGB histogram output."""
    return count_color_pixels(histogram, (255, 220, 75))


def count_color_pixels(histogram: str, expected: tuple[int, int, int]) -> int:
    """Count a unique inventory color in ImageMagick histogram output."""
    total = 0
    for line in histogram.splitlines():
        match = re.match(r"^\s*(\d+):\s*\((\d+),(\d+),(\d+)\)", line)
        if match:
            count, red, green, blue = map(int, match.groups())
            if close_rgb((red, green, blue), expected, tolerance=15):
                total += count
    return total


def count_green_pixels(histogram: str) -> int:
    """Detect the uniquely green door frame (not the room or inventory)."""
    return count_color_pixels(histogram, (60, 220, 90))


def count_cyan_pixels(histogram: str) -> int:
    return count_color_pixels(histogram, (50, 220, 220))


def screenshot_frame(output_directory: Path, frame: str) -> Path:
    """Resolve any safe fixture frame name without a scenario-specific allowlist."""
    if not isinstance(frame, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", frame):
        raise ValueError("Invalid screenshot frame name")
    return output_directory / f"scummvm-{frame}.png"


def colored_item_pixels(output_directory: Path, frame: str,
                        rgb: tuple[int, int, int], inventory: bool = False) -> int:
    screenshot = screenshot_frame(output_directory, frame)
    # Inventory icons occupy a fixed strip on the right; the verb and
    # sentence labels have similar colors and must not affect item detection.
    crop = "304x40+528+500" if inventory else "640x288+192+184"
    result = subprocess.run(
        ["convert", str(screenshot), "-crop", crop, "+repage", "-format", "%c", "histogram:info:"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Could not inspect colored inventory item: {result.stderr}")
    return count_color_pixels(result.stdout, rgb)


def colored_item_center(output_directory: Path, frame: str,
                        rgb: tuple[int, int, int], inventory: bool = False,
                        fuzz_percent: int = 8) -> tuple[int, int]:
    if type(fuzz_percent) is not int or not 0 <= fuzz_percent <= 8:
        raise ValueError("Invalid item color matching tolerance")
    screenshot = screenshot_frame(output_directory, frame)
    color_hex = "#" + "".join(f"{channel:02X}" for channel in rgb)
    crop = "304x40+528+500" if inventory else "640x288+192+184"
    result = subprocess.run(
        ["convert", str(screenshot), "-crop", crop, "+repage",
         "-fuzz", f"{fuzz_percent}%", "-fill", "white", "-opaque", color_hex,
         "-fill", "black", "+opaque", "white", "-trim", "-format", "%wx%h%O", "info:"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Could not locate colored inventory item: {result.stderr}")
    if inventory:
        match = re.fullmatch(r"(\d+)x(\d+)\+(\d+)\+(\d+)", result.stdout.strip())
        if not match:
            raise ValueError(f"Invalid inventory icon bounds: {result.stdout[:100]!r}")
        width, height, x, y = map(int, match.groups())
        if not (1 <= width <= 304 and 1 <= height <= 40 and x + width <= 304 and y + height <= 40):
            raise ValueError("Inventory icon outside fixed strip")
        return 528 + x + width // 2, 500 + y + height // 2
    return parse_key_bounds(result.stdout)


def authored_item_center(output_directory: Path, frame: str,
                         rgb: tuple[int, int, int], inventory: bool = False) -> tuple[int, int]:
    """Locate a story-authored object without assuming a specific palette entry.

    Rendered colors can be slightly shifted by ScummVM. Prefer a tight match
    that excludes similarly colored backgrounds, widening only if it finds no
    sprite pixels at all.
    """
    try:
        return colored_item_center(output_directory, frame, rgb, inventory=inventory,
                                   fuzz_percent=4)
    except ValueError as error:
        if "Unexpected sprite bounds" not in str(error):
            raise
        return colored_item_center(output_directory, frame, rgb, inventory=inventory,
                                   fuzz_percent=8)


def door_pixels(output_directory: Path, frame: str, open_state: bool = False) -> int:
    screenshot = screenshot_frame(output_directory, frame)
    result = subprocess.run(
        ["convert", str(screenshot), "-crop", "640x288+192+184", "+repage",
         "-format", "%c", "histogram:info:"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Could not inspect door: {result.stderr}")
    return (count_cyan_pixels if open_state else count_green_pixels)(result.stdout)


def door_center(output_directory: Path, frame: str = "pickup") -> tuple[int, int]:
    screenshot = screenshot_frame(output_directory, frame)
    result = subprocess.run(
        ["convert", str(screenshot), "-crop", "640x288+192+184", "+repage",
         "-fuzz", "8%", "-fill", "white", "-opaque", "#3CDC5A",
         "-fill", "black", "+opaque", "white", "-trim", "-format", "%wx%h%O", "info:"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Could not locate door: {result.stderr}")
    return parse_key_bounds(result.stdout)


def open_door_center(output_directory: Path, frame: str = "door") -> tuple[int, int]:
    screenshot = screenshot_frame(output_directory, frame)
    result = subprocess.run(
        ["convert", str(screenshot), "-crop", "640x288+192+184", "+repage",
         "-fuzz", "8%", "-fill", "white", "-opaque", "#32DCDC",
         "-fill", "black", "+opaque", "white", "-trim", "-format", "%wx%h%O", "info:"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Could not locate open door: {result.stderr}")
    return parse_key_bounds(result.stdout)


def visible_key_pixels(output_directory: Path, frame: str = "end") -> int:
    """Inspect the cropped game viewport, excluding the SCUMM verb GUI."""
    screenshot = screenshot_frame(output_directory, frame)
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
    if frame not in ("end", "pre-pickup", "pre-pickup-retry"):
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


def compare_frames(output_directory: Path, minimum_changed_pixels: int = 500,
                   expect_scroll: bool = True,
                   initial_pickup_rgb: tuple[int, int, int] | None = None,
                   require_key_sprite: bool = True) -> int:
    """Require visible frame variation; this alone does not prove scrolling."""
    if (type(minimum_changed_pixels) is not int or minimum_changed_pixels < 0
            or (expect_scroll and minimum_changed_pixels == 0)):
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
    key_pixels = (colored_item_pixels(output_directory, "end", initial_pickup_rgb)
                  if initial_pickup_rgb is not None else visible_key_pixels(output_directory))
    (output_directory / "scummvm-frame-report.json").write_text(
        json.dumps({
            "changed_pixels": count,
            "minimum_changed_pixels": minimum_changed_pixels,
            "frame_variation_passed": count >= minimum_changed_pixels,
            "frame_variation_required": minimum_changed_pixels > 0,
            "scene_probe_pixel": [700, 280],
            "start_rgb": start_rgb,
            "end_rgb": end_rgb,
            "scroll_color_signature_passed": scroll_signature,
            "scroll_expected": expect_scroll,
            "visible_key_pixels": key_pixels,
            "key_sprite_visible": key_pixels >= 40,
            "key_sprite_required": require_key_sprite,
            "smooth_scrolling_proven": False,
        }, indent=2) + "\n", encoding="utf-8",
    )
    if count < minimum_changed_pixels:
        raise RuntimeError(f"Insufficient visual variation: {count} changed pixels")
    if expect_scroll and not scroll_signature:
        raise RuntimeError(f"Expected blue-to-orange scroll marker missing: {start_rgb} -> {end_rgb}")
    if require_key_sprite and key_pixels < 40:
        raise RuntimeError(f"Expected key sprite missing from room: {key_pixels} gold pixels")
    return count


def launch_smoke(game_directory: Path, output_directory: Path, seconds: float = 6.0,
                 scene_only: bool = False, verify_return: bool = True,
                 verify_chain: bool = False, verify_recipe: bool = False,
                 allow_static_scene: bool = False, reverse_recipe: bool = False,
                 auto_recipe: bool = False, sample_scene_frames: bool = False,
                 scene_walk_clicks: tuple[tuple[str, int, int], ...] = (),
                 native_walkbox_gate_probe: bool = False,
                 native_reversible_walkbox_probe: bool = False,
                 native_reversible_gate_save_probe: bool = False,
                 native_gate_room_return_probe: bool = False,
                 native_independent_gate_chain_probe: bool = False,
                 native_independent_gate_control: bool = False) -> None:
    if native_independent_gate_control and not native_independent_gate_chain_probe:
        raise ValueError("Native independent-gate control requires the same route capture")
    if native_independent_gate_chain_probe and not verify_chain:
        raise ValueError("Independent native gates require the real two-room chain")
    if scene_walk_clicks and not scene_only:
        raise ValueError("Scene walking probes require scene-only mode")
    if native_reversible_gate_save_probe and not native_reversible_walkbox_probe:
        raise ValueError("Native gate Save/Load requires the reversible gameplay route")
    if native_gate_room_return_probe and (
            not native_reversible_walkbox_probe or native_reversible_gate_save_probe):
        raise ValueError("Native gate room return requires its own reversible gameplay route")
    if native_reversible_walkbox_probe and not native_walkbox_gate_probe:
        raise ValueError("Reversible walkbox probe requires the native gate route")
    if native_walkbox_gate_probe and (scene_only or verify_recipe or verify_chain or scene_walk_clicks):
        raise ValueError("Walkbox-gate smoke needs its own single-room inventory action")
    if any(not re.fullmatch(r"[a-z][a-z0-9-]*", label)
           or type(x) is not int or type(y) is not int
           or not 192 <= x < 832 or not 184 <= y < 472
           for label, x, y in scene_walk_clicks):
        raise ValueError("Scene click coordinates must lie within game viewport")
    if allow_static_scene and not (verify_chain or scene_only):
        raise ValueError("Static scene exception requires a chain or isolated scene fixture")
    if reverse_recipe and not verify_recipe:
        raise ValueError("Reversed inventory combination requires recipe mode")
    if auto_recipe and not verify_recipe:
        raise ValueError("Automatic recipe replay requires recipe mode")
    if not (game_directory / "tentacle.000").is_file() or not (game_directory / "tentacle.001").is_file():
        raise ValueError("Missing isolated tentacle compatibility fixture")
    if seconds <= 0 or seconds > 20:
        raise ValueError("Smoke duration must be between 0 and 20 seconds")
    goal_path = game_directory / "game-goal.json"
    if not goal_path.is_file():
        raise ValueError("Missing deterministic goal manifest")
    goal = json.loads(goal_path.read_text(encoding="utf-8"))
    if goal.get("condition") != "enter_room" or not isinstance(goal.get("room_id"), str):
        raise ValueError("Unsupported goal manifest")
    expected_color = goal.get("fixture_probe_rgb")
    if not isinstance(expected_color, list) or len(expected_color) != 3 or any(
        type(channel) is not int or channel < 0 or channel > 255 for channel in expected_color
    ):
        raise ValueError("Invalid goal room color probe")
    gates = goal.get("fixture_inventory_gates", [])
    if not isinstance(gates, list) or len(gates) > 2 or any(
        not isinstance(gate, dict) or not isinstance(gate.get("item_id"), str)
        or not gate["item_id"] or not isinstance(gate.get("rgb"), list)
        or len(gate["rgb"]) != 3 or any(type(c) is not int or not 0 <= c <= 255 for c in gate["rgb"])
        for gate in gates
    ):
        raise ValueError("Invalid fixture inventory gates")
    route = goal.get("fixture_route", [])
    if not isinstance(route, list) or len(route) > 2 or any(
        not isinstance(step, dict) or set(step) != {"room_id", "item_id", "rgb", "next_room_id"}
        or not all(isinstance(step[field], str) and step[field] for field in ("room_id", "item_id", "next_room_id"))
        or not isinstance(step["rgb"], list) or len(step["rgb"]) != 3
        or any(type(c) is not int or not 0 <= c <= 255 for c in step["rgb"])
        for step in route
    ):
        raise ValueError("Invalid fixture route")
    if verify_chain and (len(route) != 2 or route[0]["next_room_id"] != route[1]["room_id"]
                         or route[1]["next_room_id"] != goal["room_id"] or gates):
        raise ValueError("Chain smoke requires exactly two sequential single-item doors")
    combinations = goal.get("fixture_combinations", [])
    if not isinstance(combinations, list) or len(combinations) > 16:
        raise ValueError("Invalid fixture combination manifest")
    if verify_recipe:
        if not 1 <= len(combinations) <= (16 if auto_recipe else 4) or gates or len(route) != 1:
            raise ValueError("Recipe smoke requires supported combinations and one exit")
        for recipe in combinations:
            if (not isinstance(recipe, dict) or set(recipe) != {"room_id", "ingredients", "result"}
                or not isinstance(recipe["ingredients"], list) or len(recipe["ingredients"]) != 2
                or not all(isinstance(item, dict)
                           and set(item) in ({"item_id", "rgb"},
                                             {"item_id", "rgb", "world_x", "world_y"})
                           and isinstance(item["rgb"], list) and len(item["rgb"]) == 3
                           and all(type(c) is int and 0 <= c <= 255 for c in item["rgb"])
                           and ("world_x" not in item or
                                (type(item["world_x"]) is int and item["world_x"] >= 0
                                 and type(item["world_y"]) is int and item["world_y"] >= 0))
                           for item in [*recipe["ingredients"], recipe["result"]])):
                raise ValueError("Invalid recipe color probes")
        if not auto_recipe and len(combinations) == 2 and (
                combinations[0]["result"]["item_id"] not in
                [item["item_id"] for item in combinations[1]["ingredients"]]):
            raise ValueError("Recipe chain smoke requires dependent combinations in order")
        if not auto_recipe and len(combinations) in (3, 4) and (
                {item["item_id"] for item in combinations[2]["ingredients"]}
                != {combinations[0]["result"]["item_id"], combinations[1]["result"]["item_id"]}):
            raise ValueError("Recipe graph smoke requires two branches feeding a final recipe")
        if not auto_recipe and len(combinations) == 4 and (
                combinations[2]["result"]["item_id"] not in
                {item["item_id"] for item in combinations[3]["ingredients"]}):
            raise ValueError("Fourth recipe must consume the combined branch result")
    recipe_plan = plan_recipes(combinations, route[0]["item_id"]) if auto_recipe else ()
    initial_ingredient = recipe_plan[0]["ingredients"][0] if auto_recipe else None
    initial_rgb = tuple(initial_ingredient["rgb"]) if initial_ingredient is not None else None
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("A virtual X display is required")

    output_directory.mkdir(parents=True, exist_ok=True)
    log_path = output_directory / "scummvm-launch.log"
    save_path = output_directory / "native-gate-saves"
    if native_reversible_gate_save_probe:
        save_path.mkdir(exist_ok=True)
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

    independent_gate_routes = {}

    def capture_independent_route(label: str) -> list[str]:
        """Record aligned native Actor screenshots after a real walk command."""
        for _ in range(3):
            subprocess.run(["xdotool", "mousemove", "220", "390", "click", "1"],
                           check=True, timeout=5)
            time.sleep(5)
        capture_frame(f"independent-{label}-left")
        subprocess.run(["xdotool", "mousemove", "790", "390", "click", "1"],
                       check=True, timeout=5)
        labels = []
        for ordinal in range(9):
            time.sleep(0.4)
            name = f"independent-{label}-{ordinal:02d}"
            capture_frame(name)
            labels.append(name)
        for _ in range(3):
            subprocess.run(["xdotool", "mousemove", "790", "390", "click", "1"],
                           check=True, timeout=5)
            time.sleep(5)
        capture_frame(f"independent-{label}-right")
        return labels

    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            ["scummvm", *(["--debuglevel=3"] if (native_walkbox_gate_probe or native_independent_gate_chain_probe) else []),
             *([f"--savepath={save_path.resolve()}"] if native_reversible_gate_save_probe else []),
             f"--path={game_directory.resolve()}", "tentacle"],
            stdout=log,
            stderr=subprocess.STDOUT,
            env=environment,
        )
        try:
            readiness_deadline = time.monotonic() + 20.0
            while time.monotonic() < readiness_deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"ScummVM quit early (exit={process.returncode}); see {log_path}")
                capture_frame("start")
                if close_rgb(scene_pixel(output_directory, "start"), (70, 130, 190)):
                    break
                time.sleep(0.3)
            else:
                raise RuntimeError("Blue initial room was not visible within 20 seconds")
            deadline = time.monotonic() + seconds
            next_sample = time.monotonic()
            sample_number = 0
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"ScummVM quit early (exit={process.returncode}); see {log_path}")
                if sample_scene_frames and time.monotonic() >= next_sample:
                    capture_frame(f"sample-{sample_number:02d}")
                    sample_number += 1
                    next_sample = time.monotonic() + 0.15
                time.sleep(0.1)
            if process.poll() is not None:
                raise RuntimeError(f"ScummVM quit early (exit={process.returncode}); see {log_path}")
            final_snapshot = capture_frame("end")
            changed = compare_frames(output_directory,
                                     minimum_changed_pixels=0 if allow_static_scene else 500,
                                     expect_scroll=not allow_static_scene,
                                     initial_pickup_rgb=initial_rgb,
                                     require_key_sprite=not (allow_static_scene and scene_only))
            if scene_only:
                for label, screen_x, screen_y in scene_walk_clicks:
                    click = subprocess.run(
                        ["xdotool", "mousemove", str(screen_x), str(screen_y), "click", "1"],
                        capture_output=True, text=True, timeout=5, check=False)
                    if click.returncode:
                        raise RuntimeError(f"Native walk click failed: {click.stderr}")
                    time.sleep(5)
                    if process.poll() is not None:
                        raise RuntimeError("ScummVM quit during authored walking route")
                    capture_frame(label)
                print(f"Story-compiled SCUMM room rendered and scrolled: {changed} changed pixels")
                print(f"Scene-only screenshots: {output_directory}")
                return
            if native_independent_gate_chain_probe:
                independent_gate_routes["first_closed"] = capture_independent_route(
                    "first-closed")
            # Negative path: walking into the locked door must leave it closed
            # and must not satisfy the goal. Check before collecting the key.
            capture_frame("locked-before")
            locked_before = door_pixels(output_directory, "locked-before")
            if locked_before < 40:
                raise RuntimeError(f"Closed door not visible for negative test: {locked_before}")
            locked_x, locked_y = door_center(output_directory, "locked-before")
            locked_click = subprocess.run(
                ["xdotool", "mousemove", str(locked_x), str(locked_y), "click", "1"],
                capture_output=True, text=True, timeout=5, check=False,
            )
            if locked_click.returncode:
                raise RuntimeError(f"Locked door input failed: {locked_click.stderr}")
            time.sleep(3)
            capture_frame("locked-after")
            locked_after = door_pixels(output_directory, "locked-after")
            still_locked = (locked_after >= 40
                            and door_pixels(output_directory, "locked-after", open_state=True) < 10
                            and not close_rgb(scene_pixel(output_directory, "locked-after"), tuple(expected_color)))
            (output_directory / "scummvm-negative-report.json").write_text(
                json.dumps({"action": "WalkTo closed Door", "click": [locked_x, locked_y],
                            "closed_before": locked_before, "closed_after": locked_after,
                            "blocked": still_locked}, indent=2) + "\n", encoding="utf-8",
            )
            if not still_locked:
                raise RuntimeError("Locked door allowed an invalid transition or changed state")
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
            key_x, key_y = (authored_item_center(output_directory, "pre-pickup", initial_rgb)
                            if initial_rgb is not None
                            else key_center(output_directory, "pre-pickup"))
            click = subprocess.run(
                ["xdotool", "mousemove", str(key_x), str(key_y), "click", "1"],
                capture_output=True, text=True, timeout=5, check=False,
            )
            if click.returncode:
                raise RuntimeError(f"Key mouse input failed: {click.stderr}")
            picked_up = False
            remaining = (colored_item_pixels(output_directory, "pre-pickup", initial_rgb)
                         if initial_rgb is not None else visible_key_pixels(output_directory))
            inventory_pixels = 0
            pickup_start = time.monotonic()
            pickup_deadline = pickup_start + 20.0
            pickup_retried = False
            while time.monotonic() < pickup_deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"ScummVM quit during pickup (exit={process.returncode})")
                capture_frame("pickup")
                remaining = (colored_item_pixels(output_directory, "pickup", initial_rgb)
                             if initial_rgb is not None else visible_key_pixels(output_directory, "pickup"))
                inventory_pixels = (colored_item_pixels(output_directory, "pickup", initial_rgb,
                                                       inventory=True)
                                    if initial_rgb is not None else inventory_key_pixels(output_directory))
                if remaining < 10 and inventory_pixels >= 40:
                    picked_up = True
                    break
                # On slower CI runners the first object click can land while
                # the actor/camera is still moving. Reacquire the visible key
                # once after settling, rather than treating input timing as
                # an inventory-regression failure.
                if (not pickup_retried and remaining >= 10
                        and time.monotonic() - pickup_start >= 7.0):
                    pickup_retried = True
                    subprocess.run(
                        ["xdotool", "mousemove", "328", "506", "click", "1"],
                        check=True, timeout=5,
                    )
                    time.sleep(0.3)
                    capture_frame("pre-pickup-retry")
                    retry_x, retry_y = (authored_item_center(output_directory, "pre-pickup-retry", initial_rgb)
                                        if initial_rgb is not None
                                        else key_center(output_directory, "pre-pickup-retry"))
                    subprocess.run(
                        ["xdotool", "mousemove", str(retry_x), str(retry_y), "click", "1"],
                        check=True, timeout=5,
                    )
                time.sleep(0.4)
            (output_directory / "scummvm-interaction-report.json").write_text(
                json.dumps({"verb": "PickUp", "key_click": [key_x, key_y],
                            "remaining_gold_pixels": remaining,
                            "inventory_gold_pixels": inventory_pixels,
                            "pickup_retried": pickup_retried,
                            "key_removed_from_room": picked_up}, indent=2) + "\n",
                encoding="utf-8",
            )
            if not picked_up:
                raise RuntimeError(f"Pickup/inventory mismatch: room={remaining}, inventory={inventory_pixels} gold pixels")
            # Prove in the real engine that the key alone cannot bypass an
            # inventory prerequisite at *every* incomplete inventory state.
            # The fixture metadata supplies colors and required item order.
            if gates:
                acquired = []
                blocked_attempts = []
                for index, gate in enumerate(gates):
                    capture_frame("pickup")
                    blocked_door = door_center(output_directory, "pickup")
                    for click_x, click_y in ((408, 506), (552, 520), blocked_door):
                        click = subprocess.run(
                            ["xdotool", "mousemove", str(click_x), str(click_y), "click", "1"],
                            capture_output=True, text=True, timeout=5, check=False,
                        )
                        if click.returncode:
                            raise RuntimeError(f"Premature Use input failed: {click.stderr}")
                        time.sleep(0.3)
                    time.sleep(3)
                    capture_frame("gated-use")
                    blocked = (door_pixels(output_directory, "gated-use") >= 40
                               and door_pixels(output_directory, "gated-use", open_state=True) < 10
                               and not close_rgb(scene_pixel(output_directory, "gated-use"), tuple(expected_color)))
                    blocked_attempts.append({"owned": ["Key"] + [item["item_id"] for item in acquired],
                                             "missing": [g["item_id"] for g in gates[index:]],
                                             "blocked": blocked})
                    (output_directory / "scummvm-gate-negative-report.json").write_text(
                        json.dumps({"attempts": blocked_attempts,
                                    "blocked": all(a["blocked"] for a in blocked_attempts)},
                                   indent=2) + "\n", encoding="utf-8",
                    )
                    if not blocked:
                        raise RuntimeError("Door opened without all required inventory prerequisites")
                    rgb = tuple(gate["rgb"])
                    verb_click = subprocess.run(
                        ["xdotool", "mousemove", "328", "506", "click", "1"],
                        capture_output=True, text=True, timeout=5, check=False,
                    )
                    if verb_click.returncode:
                        raise RuntimeError(f"PickUp verb input failed: {verb_click.stderr}")
                    time.sleep(0.3)
                    frame = f"gate-before-{index}"
                    capture_frame(frame)
                    if colored_item_pixels(output_directory, frame, rgb) < 40:
                        raise RuntimeError(f"Required pickup not visible: {gate['item_id']}")
                    x, y = colored_item_center(output_directory, frame, rgb)
                    click = subprocess.run(
                        ["xdotool", "mousemove", str(x), str(y), "click", "1"],
                        capture_output=True, text=True, timeout=5, check=False,
                    )
                    if click.returncode:
                        raise RuntimeError(f"Required item pickup failed: {click.stderr}")
                    acquired_item = False
                    observed_room = observed_inventory = 0
                    item_deadline = time.monotonic() + 15
                    while time.monotonic() < item_deadline:
                        if process.poll() is not None:
                            raise RuntimeError("ScummVM quit while collecting inventory prerequisite")
                        frame = f"gate-picked-{index}"
                        capture_frame(frame)
                        observed_room = colored_item_pixels(output_directory, frame, rgb)
                        observed_inventory = colored_item_pixels(output_directory, frame, rgb, inventory=True)
                        if observed_room < 10 and observed_inventory >= 40:
                            acquired_item = True
                            break
                        time.sleep(0.4)
                    acquired.append({"item_id": gate["item_id"], "click": [x, y],
                                     "room_pixels": observed_room, "inventory_pixels": observed_inventory,
                                     "acquired": acquired_item})
                    if not acquired_item:
                        raise RuntimeError(f"Required item {gate['item_id']} not transferred to inventory")
                (output_directory / "scummvm-gate-pickup-report.json").write_text(
                    json.dumps({"items": acquired, "all_acquired": all(x["acquired"] for x in acquired)},
                               indent=2) + "\n", encoding="utf-8",
                )
                capture_frame("pickup")
            recipe_item_center = None
            if verify_recipe and not auto_recipe:
                ingredients = combinations[0]["ingredients"]
                result_rgb = tuple(combinations[0]["result"]["rgb"])
                second_rgb = tuple(ingredients[1]["rgb"])
                command = subprocess.run(["xdotool", "mousemove", "328", "506", "click", "1"],
                                         capture_output=True, text=True, timeout=5, check=False)
                if command.returncode:
                    raise RuntimeError(f"Recipe pickup verb failed: {command.stderr}")
                time.sleep(0.3)
                capture_frame("recipe-before")
                second_x, second_y = colored_item_center(output_directory, "recipe-before", second_rgb)
                command = subprocess.run(["xdotool", "mousemove", str(second_x), str(second_y), "click", "1"],
                                         capture_output=True, text=True, timeout=5, check=False)
                if command.returncode:
                    raise RuntimeError(f"Recipe second ingredient click failed: {command.stderr}")
                ingredient_owned = False
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    capture_frame("recipe-second")
                    if (colored_item_pixels(output_directory, "recipe-second", second_rgb) < 10
                            and colored_item_pixels(output_directory, "recipe-second", second_rgb, inventory=True) >= 40):
                        ingredient_owned = True
                        break
                    time.sleep(0.4)
                if not ingredient_owned:
                    raise RuntimeError("Second ingredient not in inventory")
                first_center = colored_item_center(output_directory, "recipe-second",
                                                   tuple(ingredients[0]["rgb"]), inventory=True)
                second_center = colored_item_center(output_directory, "recipe-second", second_rgb, inventory=True)
                ordered_ingredients = ((second_center, first_center) if reverse_recipe
                                       else (first_center, second_center))
                for x, y in ((408, 506), *ordered_ingredients):
                    command = subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                                             capture_output=True, text=True, timeout=5, check=False)
                    if command.returncode:
                        raise RuntimeError(f"Recipe combination input failed: {command.stderr}")
                    time.sleep(0.3)
                combined = False
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    capture_frame("recipe-combined")
                    result_pixels = colored_item_pixels(output_directory, "recipe-combined", result_rgb, inventory=True)
                    first_pixels = colored_item_pixels(output_directory, "recipe-combined", tuple(ingredients[0]["rgb"]), inventory=True)
                    second_pixels = colored_item_pixels(output_directory, "recipe-combined", second_rgb, inventory=True)
                    if result_pixels >= 40 and first_pixels < 10 and second_pixels < 10:
                        combined = True
                        break
                    time.sleep(0.4)
                (output_directory / "scummvm-recipe-report.json").write_text(
                    json.dumps({"recipe": combinations[0], "ingredient_pickup": ingredient_owned,
                                "ingredients_consumed": first_pixels < 10 and second_pixels < 10,
                                "result_inventory_pixels": result_pixels,
                                "reversed_ingredient_order": reverse_recipe,
                                "combined": combined}, indent=2) + "\n", encoding="utf-8")
                if not combined:
                    raise RuntimeError("Recipe combination did not consume ingredients and produce result")
                recipe_item_center = colored_item_center(output_directory, "recipe-combined", result_rgb,
                                                         inventory=True)
                if len(combinations) == 2:
                    next_recipe = combinations[1]
                    next_ingredients = next_recipe["ingredients"]
                    extra = next(item for item in next_ingredients
                                 if item["item_id"] != combinations[0]["result"]["item_id"])
                    extra_rgb = tuple(extra["rgb"])
                    subprocess.run(["xdotool", "mousemove", "328", "506", "click", "1"],
                                   check=True, timeout=5)
                    time.sleep(0.3)
                    capture_frame("recipe-chain-before")
                    extra_x, extra_y = colored_item_center(output_directory, "recipe-chain-before", extra_rgb)
                    subprocess.run(["xdotool", "mousemove", str(extra_x), str(extra_y), "click", "1"],
                                   check=True, timeout=5)
                    extra_owned = False
                    deadline = time.monotonic() + 15
                    while time.monotonic() < deadline:
                        capture_frame("recipe-chain-picked")
                        if (colored_item_pixels(output_directory, "recipe-chain-picked", extra_rgb) < 10
                                and colored_item_pixels(output_directory, "recipe-chain-picked", extra_rgb,
                                                        inventory=True) >= 40):
                            extra_owned = True
                            break
                        time.sleep(0.4)
                    if not extra_owned:
                        raise RuntimeError("Second recipe ingredient not in inventory")
                    prior_center = colored_item_center(output_directory, "recipe-chain-picked", result_rgb,
                                                       inventory=True)
                    extra_center = colored_item_center(output_directory, "recipe-chain-picked", extra_rgb,
                                                       inventory=True)
                    for x, y in ((408, 506), prior_center, extra_center):
                        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                                       check=True, timeout=5)
                        time.sleep(0.3)
                    final_rgb = tuple(next_recipe["result"]["rgb"])
                    chained = False
                    deadline = time.monotonic() + 15
                    while time.monotonic() < deadline:
                        capture_frame("recipe-chain-combined")
                        final_pixels = colored_item_pixels(output_directory, "recipe-chain-combined", final_rgb,
                                                           inventory=True)
                        prior_pixels = colored_item_pixels(output_directory, "recipe-chain-combined", result_rgb,
                                                           inventory=True)
                        extra_pixels = colored_item_pixels(output_directory, "recipe-chain-combined", extra_rgb,
                                                           inventory=True)
                        if final_pixels >= 40 and prior_pixels < 10 and extra_pixels < 10:
                            chained = True
                            break
                        time.sleep(0.4)
                    (output_directory / "scummvm-recipe-chain-report.json").write_text(
                        json.dumps({"first_combined": combined, "second_combined": chained,
                                    "prior_ingredient_consumed": prior_pixels < 10,
                                    "extra_ingredient_consumed": extra_pixels < 10,
                                    "final_inventory_pixels": final_pixels}, indent=2) + "\n",
                        encoding="utf-8")
                    if not chained:
                        raise RuntimeError("Second recipe did not consume ingredients and produce result")
                    recipe_item_center = colored_item_center(output_directory, "recipe-chain-combined", final_rgb,
                                                             inventory=True)
                if len(combinations) in (3, 4):
                    # Two disjoint ingredient branches are combined first;
                    # their outputs then form the final recipe. Only the
                    # initial branch was collected by the common path above.
                    second_recipe, final_recipe = combinations[1:3]
                    branch_items = second_recipe["ingredients"]
                    for item_index, item in enumerate(branch_items):
                        rgb = tuple(item["rgb"])
                        subprocess.run(["xdotool", "mousemove", "328", "506", "click", "1"],
                                       check=True, timeout=5)
                        time.sleep(0.3)
                        frame = f"recipe-graph-before-{item_index}"
                        capture_frame(frame)
                        x, y = colored_item_center(output_directory, frame, rgb)
                        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                                       check=True, timeout=5)
                        deadline = time.monotonic() + 15
                        acquired = False
                        while time.monotonic() < deadline:
                            frame = f"recipe-graph-picked-{item_index}"
                            capture_frame(frame)
                            if (colored_item_pixels(output_directory, frame, rgb) < 10
                                    and colored_item_pixels(output_directory, frame, rgb,
                                                            inventory=True) >= 40):
                                acquired = True
                                break
                            time.sleep(0.4)
                        if not acquired:
                            raise RuntimeError(f"Branch ingredient {item['item_id']} was not picked up")
                    branch_rgbs = [tuple(item["rgb"]) for item in branch_items]
                    branch_result_rgb = tuple(second_recipe["result"]["rgb"])
                    for stage, (left_rgb, right_rgb, output_rgb) in enumerate((
                            (*branch_rgbs, branch_result_rgb),
                            (result_rgb, branch_result_rgb, tuple(final_recipe["result"]["rgb"])) )):
                        frame = f"recipe-graph-stage-{stage}"
                        capture_frame(frame)
                        first_x, first_y = colored_item_center(output_directory, frame, left_rgb,
                                                               inventory=True)
                        second_x, second_y = colored_item_center(output_directory, frame, right_rgb,
                                                                 inventory=True)
                        for x, y in ((408, 506), (first_x, first_y), (second_x, second_y)):
                            subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                                           check=True, timeout=5)
                            time.sleep(0.3)
                        done = False
                        deadline = time.monotonic() + 15
                        while time.monotonic() < deadline:
                            frame = f"recipe-graph-combined-{stage}"
                            capture_frame(frame)
                            output_pixels = colored_item_pixels(output_directory, frame, output_rgb,
                                                                inventory=True)
                            left_pixels = colored_item_pixels(output_directory, frame, left_rgb, inventory=True)
                            right_pixels = colored_item_pixels(output_directory, frame, right_rgb, inventory=True)
                            if output_pixels >= 40 and left_pixels < 10 and right_pixels < 10:
                                done = True
                                break
                            time.sleep(0.4)
                        (output_directory / f"scummvm-recipe-graph-stage-{stage}.json").write_text(
                            json.dumps({"combined": done, "result_inventory_pixels": output_pixels,
                                        "first_consumed": left_pixels < 10,
                                        "second_consumed": right_pixels < 10}, indent=2) + "\n",
                            encoding="utf-8")
                        if not done:
                            raise RuntimeError(f"Recipe graph combination {stage + 2} failed")
                    recipe_item_center = colored_item_center(output_directory,
                                                             "recipe-graph-combined-1", output_rgb,
                                                             inventory=True)
                    if len(combinations) == 4:
                        fourth_recipe = combinations[3]
                        prior_rgb = output_rgb
                        extra = next(item for item in fourth_recipe["ingredients"]
                                     if item["item_id"] != final_recipe["result"]["item_id"])
                        extra_rgb = tuple(extra["rgb"])
                        subprocess.run(["xdotool", "mousemove", "328", "506", "click", "1"],
                                       check=True, timeout=5)
                        time.sleep(0.3)
                        capture_frame("recipe-four-before")
                        extra_x, extra_y = colored_item_center(output_directory, "recipe-four-before",
                                                               extra_rgb, fuzz_percent=4)
                        subprocess.run(["xdotool", "mousemove", str(extra_x), str(extra_y), "click", "1"],
                                       check=True, timeout=5)
                        acquired = False
                        deadline = time.monotonic() + 15
                        while time.monotonic() < deadline:
                            capture_frame("recipe-four-picked")
                            if (colored_item_pixels(output_directory, "recipe-four-picked", extra_rgb) < 10
                                    and colored_item_pixels(output_directory, "recipe-four-picked",
                                                            extra_rgb, inventory=True) >= 40):
                                acquired = True
                                break
                            time.sleep(0.4)
                        if not acquired:
                            raise RuntimeError("Fourth recipe's physical ingredient not picked up")
                        prior_x, prior_y = colored_item_center(output_directory, "recipe-four-picked",
                                                               prior_rgb, inventory=True)
                        extra_x, extra_y = colored_item_center(output_directory, "recipe-four-picked",
                                                               extra_rgb, inventory=True)
                        for x, y in ((408, 506), (prior_x, prior_y), (extra_x, extra_y)):
                            subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                                           check=True, timeout=5)
                            time.sleep(0.3)
                        final_rgb = tuple(fourth_recipe["result"]["rgb"])
                        crafted = False
                        deadline = time.monotonic() + 15
                        while time.monotonic() < deadline:
                            capture_frame("recipe-four-combined")
                            final_pixels = colored_item_pixels(output_directory, "recipe-four-combined",
                                                               final_rgb, inventory=True)
                            prior_pixels = colored_item_pixels(output_directory, "recipe-four-combined",
                                                               prior_rgb, inventory=True)
                            extra_pixels = colored_item_pixels(output_directory, "recipe-four-combined",
                                                               extra_rgb, inventory=True)
                            if final_pixels >= 40 and prior_pixels < 10 and extra_pixels < 10:
                                crafted = True
                                break
                            time.sleep(0.4)
                        (output_directory / "scummvm-recipe-four-report.json").write_text(
                            json.dumps({"crafted": crafted, "final_inventory_pixels": final_pixels,
                                        "third_recipe_result_consumed": prior_pixels < 10,
                                        "extra_ingredient_consumed": extra_pixels < 10}, indent=2) + "\n",
                            encoding="utf-8")
                        if not crafted:
                            raise RuntimeError("Fourth recipe did not consume both ingredients")
                        recipe_item_center = colored_item_center(output_directory, "recipe-four-combined",
                                                                 final_rgb, inventory=True)
                capture_frame("pickup")
            if verify_recipe and auto_recipe:
                # The common pickup prelude collected the first physical
                # ingredient selected by the planner, regardless of palette.
                owned = {initial_ingredient["item_id"]}
                produced_ids = {recipe["result"]["item_id"] for recipe in recipe_plan}
                completed_recipes = []
                for recipe_index, recipe in enumerate(recipe_plan):
                    for ingredient_index, item in enumerate(recipe["ingredients"]):
                        if item["item_id"] in owned:
                            continue
                        if item["item_id"] in produced_ids:
                            raise RuntimeError(f"Required intermediate {item['item_id']} not in inventory")
                        rgb = tuple(item["rgb"])
                        subprocess.run(["xdotool", "mousemove", "328", "506", "click", "1"],
                                       check=True, timeout=5)
                        time.sleep(0.3)
                        frame = f"auto-before-{recipe_index}-{ingredient_index}"
                        capture_frame(frame)
                        try:
                            item_x, item_y = authored_item_center(output_directory, frame, rgb)
                        except ValueError as missing:
                            if "Unexpected sprite bounds" not in str(missing):
                                raise
                            # The actor can occlude a nearby ground sprite after
                            # the preceding pickup. Walk away, then re-scan the
                            # rendered scene rather than guessing a world offset.
                            # Start at the far right: later recipe ingredients
                            # may be beyond the current camera viewport.
                            for walk_x in (800, 730, 610, 245):
                                subprocess.run(["xdotool", "mousemove", str(walk_x), "355", "click", "1"],
                                               check=True, timeout=5)
                                time.sleep(3)
                                subprocess.run(["xdotool", "mousemove", "328", "506", "click", "1"],
                                               check=True, timeout=5)
                                time.sleep(0.3)
                                capture_frame(frame)
                                try:
                                    item_x, item_y = authored_item_center(output_directory, frame, rgb)
                                    break
                                except ValueError as retry_missing:
                                    if "Unexpected sprite bounds" not in str(retry_missing):
                                        raise
                            else:
                                raise RuntimeError(
                                    f"Could not locate ground ingredient {item['item_id']} "
                                    f"at world position ({item.get('world_x', '?')}, "
                                    f"{item.get('world_y', '?')}) after camera sweep") from missing
                        subprocess.run(["xdotool", "mousemove", str(item_x), str(item_y), "click", "1"],
                                       check=True, timeout=5)
                        acquired = False
                        pickup_start = time.monotonic()
                        retried = False
                        while time.monotonic() - pickup_start < 18:
                            frame = f"auto-picked-{recipe_index}-{ingredient_index}"
                            capture_frame(frame)
                            if (colored_item_pixels(output_directory, frame, rgb) < 10
                                    and colored_item_pixels(output_directory, frame, rgb,
                                                            inventory=True) >= 40):
                                acquired = True
                                break
                            if not retried and time.monotonic() - pickup_start >= 7:
                                retried = True
                                subprocess.run(["xdotool", "mousemove", "328", "506", "click", "1"],
                                               check=True, timeout=5)
                                time.sleep(0.3)
                                capture_frame(frame)
                                item_x, item_y = authored_item_center(output_directory, frame, rgb)
                                subprocess.run(["xdotool", "mousemove", str(item_x), str(item_y), "click", "1"],
                                               check=True, timeout=5)
                            time.sleep(0.4)
                        if not acquired:
                            raise RuntimeError(f"Automatic recipe pickup failed: {item['item_id']}")
                        owned.add(item["item_id"])
                        time.sleep(0.5)
                    frame = f"auto-ready-{recipe_index}"
                    capture_frame(frame)
                    inputs = recipe["ingredients"]
                    clicks = [colored_item_center(output_directory, frame, tuple(item["rgb"]),
                                                  inventory=True, fuzz_percent=4)
                              for item in inputs]
                    for x, y in ((408, 506), *clicks):
                        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                                       check=True, timeout=5)
                        time.sleep(0.3)
                    output_rgb = tuple(recipe["result"]["rgb"])
                    input_rgbs = [tuple(item["rgb"]) for item in inputs]
                    combined = False
                    deadline = time.monotonic() + 15
                    while time.monotonic() < deadline:
                        frame = f"auto-combined-{recipe_index}"
                        capture_frame(frame)
                        if (colored_item_pixels(output_directory, frame, output_rgb, inventory=True) >= 40
                                and all(colored_item_pixels(output_directory, frame, rgb,
                                                            inventory=True) < 10 for rgb in input_rgbs)):
                            combined = True
                            break
                        time.sleep(0.4)
                    completed_recipes.append({"result": recipe["result"]["item_id"], "combined": combined})
                    if not combined:
                        raise RuntimeError(f"Automatic recipe combination failed: {recipe['result']['item_id']}")
                    owned.difference_update(item["item_id"] for item in inputs)
                    owned.add(recipe["result"]["item_id"])
                recipe_item_center = colored_item_center(output_directory, frame, output_rgb,
                                                         inventory=True, fuzz_percent=4)
                (output_directory / "scummvm-recipe-auto-report.json").write_text(
                    json.dumps({"completed_recipes": completed_recipes,
                                "goal_item": route[0]["item_id"], "owned": sorted(owned)},
                               indent=2) + "\n", encoding="utf-8")
                capture_frame("pickup")
            initial_door_pixels = door_pixels(output_directory, "pickup")
            if initial_door_pixels < 40:
                raise RuntimeError(f"Door not visible before using key: {initial_door_pixels} green pixels")
            door_x, door_y = door_center(output_directory)
            # Use -> inventory slot -> target. The example UI has its first
            # inventory slot at x536..568,y504..536 on our 1024x768 Xvfb.
            for click_x, click_y in ((408, 506), recipe_item_center or (552, 520), (door_x, door_y)):
                click = subprocess.run(
                    ["xdotool", "mousemove", str(click_x), str(click_y), "click", "1"],
                    capture_output=True, text=True, timeout=5, check=False,
                )
                if click.returncode:
                    raise RuntimeError(f"Use interaction mouse input failed: {click.stderr}")
                time.sleep(0.3)
            door_opened = False
            room_changed = False
            remaining_door_pixels = initial_door_pixels
            open_door_pixels = 0
            door_deadline = time.monotonic() + 15.0
            while time.monotonic() < door_deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"ScummVM quit during door use (exit={process.returncode})")
                capture_frame("door")
                remaining_door_pixels = door_pixels(output_directory, "door")
                room_changed = close_rgb(scene_pixel(output_directory, "door"), tuple(expected_color))
                open_door_pixels = door_pixels(output_directory, "door", open_state=True)
                if remaining_door_pixels < 10 and open_door_pixels >= 40 and not room_changed:
                    door_opened = True
                    break
                time.sleep(0.4)
            if not door_opened:
                raise RuntimeError(f"Use Key with Door did not leave an open door in Harbor: closed={remaining_door_pixels}, open={open_door_pixels}, transitioned={room_changed}")
            if native_walkbox_gate_probe:
                # R09: this is the same live stock-ScummVM process in which
                # the real inventory Use just opened the author-controlled box.
                # The room-entry demo walk supplied initial closed-route
                # screenshots (sample-XX). After opening, walk back to the
                # left, cross again and return: no runtime or source patch.
                actions = (
                    ("gate-leftward-1", 220, 390, 5.0),
                    ("gate-leftward-2", 220, 390, 5.0),
                    ("gate-return-start", 220, 390, 5.0),
                    ("gate-open-transit", 790, 390, 1.5),
                    ("gate-open-goal", None, None, 5.0),
                    ("gate-return-transit", 220, 390, 3.0),
                    ("gate-return-complete", 220, 390, 5.0),
                )
                for label, x, y, seconds_to_wait in actions:
                    if x is not None:
                        subprocess.run(["xdotool", "mousemove", str(x), str(y),
                                        "click", "1"], check=True, timeout=5)
                    time.sleep(seconds_to_wait)
                    if process.poll() is not None:
                        raise RuntimeError("Native gate game exited during walkbox route")
                    capture_frame(label)
                if native_reversible_walkbox_probe:
                    # Stage the next two *real* Use Key with Door operations in
                    # the same live interpreter, not a source or resource edit.
                    # Re-use the exact inventory/verb workflow already used
                    # for the initial open state above.
                    transitions = []
                    for ordinal, wanted_open in ((1, False), (2, True)):
                        # Travel to the far door; it can be off camera after
                        # the previous return toward the left walkboxes.
                        for step in range(3):
                            subprocess.run(["xdotool", "mousemove", "790", "390",
                                            "click", "1"], check=True, timeout=5)
                            time.sleep(5.0)
                        approach = f"gate-switch-{ordinal}-approach"
                        capture_frame(approach)
                        if wanted_open:
                            target_x, target_y = door_center(output_directory, approach)
                        else:
                            target_x, target_y = open_door_center(output_directory, approach)
                        for click_x, click_y in ((408, 506), recipe_item_center or (552, 520),
                                                 (target_x, target_y)):
                            subprocess.run(["xdotool", "mousemove", str(click_x), str(click_y),
                                            "click", "1"], check=True, timeout=5)
                            time.sleep(0.3)
                        expected = "open" if wanted_open else "closed"
                        switched = False
                        for attempt in range(40):
                            label = f"gate-{expected}-{ordinal}-state"
                            capture_frame(label)
                            closed_pixels = door_pixels(output_directory, label)
                            open_pixels = door_pixels(output_directory, label, open_state=True)
                            if (open_pixels >= 40 and closed_pixels < 10) if wanted_open else (
                                    closed_pixels >= 40 and open_pixels < 10):
                                switched = True
                                break
                            time.sleep(0.35)
                        if not switched:
                            raise RuntimeError(
                                f"Native reversible gate did not become {expected}: "
                                f"closed={closed_pixels}, opened={open_pixels}")
                        for step in range(3):
                            subprocess.run(["xdotool", "mousemove", "220", "390",
                                            "click", "1"], check=True, timeout=5)
                            time.sleep(5.0)
                        capture_frame(f"gate-{expected}-{ordinal}-left")
                        subprocess.run(["xdotool", "mousemove", "790", "390",
                                        "click", "1"], check=True, timeout=5)
                        samples = []
                        for sample in range(9):
                            time.sleep(0.4)
                            label = f"gate-{expected}-{ordinal}-sample-{sample:02d}"
                            capture_frame(label)
                            samples.append(label)
                        time.sleep(4)
                        capture_frame(f"gate-{expected}-{ordinal}-far")
                        transitions.append({"state": expected, "door_state_verified": True,
                                            "actor_sample_frames": samples})
                    if native_reversible_gate_save_probe:
                        # Save the REOPENED gate after a real third inventory Use,
                        # with the Actor back at the left endpoint. The subsequent
                        # probe starts a fresh stock ScummVM process from slot 1.
                        for step in range(3):
                            subprocess.run(["xdotool", "mousemove", "220", "390",
                                            "click", "1"], check=True, timeout=5)
                            time.sleep(5.0)
                        capture_frame("gate-before-save")
                        from .scumm_save_load_probe import (open_native_global_menu,
                                                           verify_global_menu_ready)
                        open_native_global_menu()
                        time.sleep(2)
                        capture_frame("gate-save-menu")
                        verify_global_menu_ready(output_directory / "scummvm-gate-save-menu.png")
                        subprocess.run(["xdotool", "mousemove", "512", "367",
                                        "click", "1"], check=True, timeout=5)
                        time.sleep(2)
                        subprocess.run(["xdotool", "mousemove", "298", "285",
                                        "click", "1"], check=True, timeout=5)
                        time.sleep(2)
                        subprocess.run(["xdotool", "type", "--clearmodifiers",
                                        "--delay", "60", "R09 reversible gate"],
                                       check=True, timeout=15)
                        subprocess.run(["xdotool", "mousemove", "618", "414",
                                        "click", "1"], check=True, timeout=5)
                        time.sleep(3)
                        slot = save_path / "tentacle.s01"
                        if not slot.is_file() or slot.stat().st_size == 0:
                            raise RuntimeError("Native R09 gate save slot was not created")
                        (output_directory / "scummvm-native-gate-save-report.json").write_text(
                            json.dumps({"native_save_created": True,
                                        "slot": "tentacle.s01",
                                        "saved_gate_state": "open-after-reopen",
                                        "saved_actor_endpoint": "left"}, indent=2) + "\n",
                            encoding="utf-8")
                    if native_gate_room_return_probe:
                        from .scumm_gate_room_return_probe import play_native_gate_room_return
                        play_native_gate_room_return(
                            output_directory, capture_frame, process,
                            recipe_item_center or (552, 520))
                    (output_directory / "scummvm-native-reversible-walkbox-report.json").write_text(
                        json.dumps({"initial_open": door_opened,
                                    "transitions": transitions,
                                    "native_actor_returned": True}, indent=2) + "\n",
                        encoding="utf-8")
                (output_directory / "scummvm-native-walkbox-gate-report.json").write_text(
                    json.dumps({"native_door_use_opened": door_opened,
                                "closed_walk_sampled": sample_scene_frames,
                                "open_walk_captured": True,
                                "return_captured": True,
                                "door_click": [door_x, door_y]}, indent=2) + "\n",
                    encoding="utf-8")
                return
            exit_x, exit_y = open_door_center(output_directory)
            exit_click = subprocess.run(
                ["xdotool", "mousemove", str(exit_x), str(exit_y), "click", "1"],
                capture_output=True, text=True, timeout=5, check=False,
            )
            if exit_click.returncode:
                raise RuntimeError(f"Exit mouse input failed: {exit_click.stderr}")
            if verify_chain:
                second = route[1]
                rgb = tuple(second["rgb"])
                # Entering the intermediate room restores its own local
                # pickup and closed exit; the first door is already open.
                arrived = False
                arrival_deadline = time.monotonic() + 20
                while time.monotonic() < arrival_deadline:
                    if process.poll() is not None:
                        raise RuntimeError("ScummVM quit during chain room transition")
                    capture_frame("chain-arrival")
                    if (colored_item_pixels(output_directory, "chain-arrival", rgb) >= 40
                            and door_pixels(output_directory, "chain-arrival") >= 40):
                        arrived = True
                        break
                    time.sleep(0.4)
                if not arrived:
                    raise RuntimeError("Second story room did not render its pickup and locked exit")
                if native_independent_gate_chain_probe:
                    independent_gate_routes["second_closed"] = capture_independent_route(
                        "second-closed")
                # The second room cannot be left before collecting its item.
                second_door = door_center(output_directory, "chain-arrival")
                for x, y in ((328, 506),):
                    command = subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                                             capture_output=True, text=True, timeout=5, check=False)
                    if command.returncode:
                        raise RuntimeError(f"Second room PickUp verb failed: {command.stderr}")
                time.sleep(0.3)
                capture_frame("chain-second")
                item_x, item_y = colored_item_center(output_directory, "chain-second", rgb)
                command = subprocess.run(
                    ["xdotool", "mousemove", str(item_x), str(item_y), "click", "1"],
                    capture_output=True, text=True, timeout=5, check=False,
                )
                if command.returncode:
                    raise RuntimeError(f"Second room item click failed: {command.stderr}")
                acquired = False
                acquire_deadline = time.monotonic() + 15
                while time.monotonic() < acquire_deadline:
                    capture_frame("chain-second")
                    if (colored_item_pixels(output_directory, "chain-second", rgb) < 10
                            and colored_item_pixels(output_directory, "chain-second", rgb, inventory=True) >= 40):
                        acquired = True
                        break
                    time.sleep(0.4)
                if not acquired:
                    raise RuntimeError("Second room pickup was not transferred to inventory")
                inventory_x, inventory_y = colored_item_center(output_directory, "chain-second", rgb, inventory=True)
                second_door = door_center(output_directory, "chain-second")
                for x, y in ((408, 506), (inventory_x, inventory_y), second_door):
                    command = subprocess.run(
                        ["xdotool", "mousemove", str(x), str(y), "click", "1"],
                        capture_output=True, text=True, timeout=5, check=False,
                    )
                    if command.returncode:
                        raise RuntimeError(f"Second room use failed: {command.stderr}")
                    time.sleep(0.3)
                opened = False
                open_deadline = time.monotonic() + 15
                while time.monotonic() < open_deadline:
                    capture_frame("chain-second-open")
                    if (door_pixels(output_directory, "chain-second-open") < 10
                            and door_pixels(output_directory, "chain-second-open", open_state=True) >= 40):
                        opened = True
                        break
                    time.sleep(0.4)
                if not opened:
                    raise RuntimeError("Second room door did not open with its story item")
                second_exit = open_door_center(output_directory, "chain-second-open")
                command = subprocess.run(
                    ["xdotool", "mousemove", str(second_exit[0]), str(second_exit[1]), "click", "1"],
                    capture_output=True, text=True, timeout=5, check=False,
                )
                if command.returncode:
                    raise RuntimeError(f"Second room exit failed: {command.stderr}")
                reached = False
                reach_deadline = time.monotonic() + 15
                while time.monotonic() < reach_deadline:
                    capture_frame("chain-goal")
                    if close_rgb(scene_pixel(output_directory, "chain-goal"), tuple(expected_color)):
                        reached = True
                        break
                    time.sleep(0.4)
                return_checks = {}
                if reached:
                    back_rgb = (160, 230, 55)

                    def back_to_previous(source_frame: str, target_frame: str) -> None:
                        capture_frame(source_frame)
                        if colored_item_pixels(output_directory, source_frame, back_rgb) < 40:
                            raise RuntimeError(f"Back passage not visible: {source_frame}")
                        back_x, back_y = colored_item_center(output_directory, source_frame, back_rgb)
                        click_back = subprocess.run(
                            ["xdotool", "mousemove", str(back_x), str(back_y), "click", "1"],
                            capture_output=True, text=True, timeout=5, check=False,
                        )
                        if click_back.returncode:
                            raise RuntimeError(f"Back passage input failed: {click_back.stderr}")
                        # Wait for the new room's back passage to render.
                        limit = time.monotonic() + 12
                        while time.monotonic() < limit:
                            capture_frame(target_frame)
                            if (not close_rgb(scene_pixel(output_directory, target_frame), tuple(expected_color))
                                    and colored_item_pixels(output_directory, target_frame, back_rgb) >= 40):
                                return
                            time.sleep(0.25)
                        raise RuntimeError(f"Back passage did not reach {target_frame}")

                    back_to_previous("chain-goal", "chain-middle-return")
                    # After return, the opened second door must still be cyan
                    # and the second pickup must not respawn in the room.
                    time.sleep(7)
                    capture_frame("chain-middle-state")
                    return_checks["middle_door_open"] = door_pixels(output_directory, "chain-middle-state", open_state=True) >= 40
                    return_checks["middle_pickup_gone"] = colored_item_pixels(output_directory, "chain-middle-state", rgb) < 10
                    return_checks["middle_item_owned"] = colored_item_pixels(output_directory, "chain-middle-state", rgb, inventory=True) >= 40
                    if not all(return_checks.values()):
                        raise RuntimeError(f"Middle room state was not preserved: {return_checks}")
                    if native_independent_gate_chain_probe:
                        independent_gate_routes["second_open"] = capture_independent_route(
                            "second-open")
                    # The camera may be scrolled to the right. Move ego left
                    # until the uniquely colored back passage is visible.
                    for _ in range(4):
                        capture_frame("chain-middle-back")
                        if colored_item_pixels(output_directory, "chain-middle-back", back_rgb) >= 40:
                            break
                        turn = subprocess.run(["xdotool", "mousemove", "220", "355", "click", "1"],
                                              capture_output=True, text=True, timeout=5, check=False)
                        if turn.returncode:
                            raise RuntimeError(f"Could not walk back to previous room: {turn.stderr}")
                        time.sleep(2.5)
                    capture_frame("chain-middle-back")
                    if colored_item_pixels(output_directory, "chain-middle-back", back_rgb) < 40:
                        raise RuntimeError("Could not find middle-room back passage")
                    back_x, back_y = colored_item_center(output_directory, "chain-middle-back", back_rgb)
                    back = subprocess.run(["xdotool", "mousemove", str(back_x), str(back_y), "click", "1"],
                                          capture_output=True, text=True, timeout=5, check=False)
                    if back.returncode:
                        raise RuntimeError(f"Return to first room failed: {back.stderr}")
                    time.sleep(7)
                    capture_frame("chain-first-return")
                    return_checks["first_door_open"] = door_pixels(output_directory, "chain-first-return", open_state=True) >= 40
                    return_checks["first_pickup_gone"] = colored_item_pixels(output_directory, "chain-first-return", tuple(route[0]["rgb"])) < 10
                    return_checks["first_item_owned"] = colored_item_pixels(output_directory, "chain-first-return", tuple(route[0]["rgb"]), inventory=True) >= 40
                    if not all(return_checks.values()):
                        raise RuntimeError(f"Return-to-start state was not preserved: {return_checks}")
                    if native_independent_gate_chain_probe:
                        independent_gate_routes["first_open"] = capture_independent_route(
                            "first-open")
                (output_directory / "scummvm-chain-report.json").write_text(
                    json.dumps({"room_route": [step["room_id"] for step in route] + [goal["room_id"]],
                                "first_door_opened": door_opened, "intermediate_room_visible": arrived,
                                "second_item_acquired": acquired, "second_door_opened": opened,
                                "goal_reached": reached, "return_checks": return_checks,
                                "returns_preserved": reached and len(return_checks) == 6 and all(return_checks.values())},
                               indent=2) + "\n", encoding="utf-8",
                )
                if native_independent_gate_chain_probe:
                    if not (door_opened and arrived and opened and reached and
                            len(return_checks) == 6 and all(return_checks.values())):
                        raise RuntimeError("Native independent gates failed chain gameplay/return")
                    # Each room entry restores its own box flags based on
                    # persistent door state, using the unmodified interpreter.
                    log.flush()
                    native_log = log_path.read_text(encoding="utf-8")
                    closed = native_log.count("setBoxFlags(2, 0x80)")
                    open_ = native_log.count("setBoxFlags(2, 0x00)")
                    if not native_independent_gate_control and (closed < 2 or open_ < 2):
                        raise RuntimeError(
                            f"Two native gate flag cycles not observed: closed={closed}, open={open_}")
                    (output_directory / "scummvm-native-independent-gates-report.json").write_text(
                        json.dumps({"native_two_room_gates_executed": True,
                                    "first_door_use_opened": door_opened,
                                    "second_door_use_opened": opened,
                                    "return_preserved_both_states": all(return_checks.values()),
                                    "native_box_flags_closed_calls": closed,
                                    "native_box_flags_open_calls": open_,
                                    "control_game": native_independent_gate_control,
                                    "actor_routes": independent_gate_routes},
                                   indent=2) + "\n", encoding="utf-8")
                if not reached:
                    raise RuntimeError("Chain did not reach its final story room")
                print("Full chained story gameplay succeeded: both inventory doors opened and final room reached")
                return
            goal_reached = False
            exit_deadline = time.monotonic() + 15.0
            exit_retry_at = time.monotonic() + 6.0
            exit_retried = False
            while time.monotonic() < exit_deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"ScummVM quit during exit (exit={process.returncode})")
                capture_frame("exit")
                goal_reached = close_rgb(scene_pixel(output_directory, "exit"), tuple(expected_color))
                if goal_reached:
                    break
                # The actor may still be finishing the door-opening animation
                # when the first exit click arrives. Once the open hotspot is
                # stable, repeat the click once with freshly measured bounds.
                # This is required for the ordinary --puzzle-only story too,
                # not only for recipes: CI observed a fully opened door but
                # no transition to Cellar after the first exit click.
                if (time.monotonic() >= exit_retry_at
                        and should_retry_open_door_exit(
                            door_pixels(output_directory, "exit", open_state=True),
                            already_retried=exit_retried)):
                    exit_retried = True
                    exit_x, exit_y = open_door_center(output_directory, "exit")
                    subprocess.run(
                        ["xdotool", "mousemove", str(exit_x), str(exit_y), "click", "1"],
                        check=True, timeout=5,
                    )
                time.sleep(0.4)
            (output_directory / "scummvm-use-report.json").write_text(
                json.dumps({"inventory_item": "Key", "target": "Door",
                            "click": [door_x, door_y], "green_before": initial_door_pixels,
                            "green_after": remaining_door_pixels, "door_opened": door_opened,
                            "open_door_pixels": open_door_pixels,
                            "exit_click": [exit_x, exit_y],
                            "exit_retried": exit_retried,
                            "destination_room_visible": goal_reached,
                            "goal_room": goal["room_id"], "goal_reached": goal_reached}, indent=2) + "\n",
                encoding="utf-8",
            )
            if not goal_reached:
                raise RuntimeError(f"Opened door did not lead to {goal['room_id']}")
            if not verify_return:
                print(f"Story-built puzzle succeeded: {'combined recipe, ' if verify_recipe else ''}unlocked Door, entered {goal['room_id']}")
                return
            # Return from the goal room and verify that the engine preserved
            # both object states (opened door and already collected key).
            time.sleep(1)
            capture_frame("exit")
            stairs_x, stairs_y = door_center(output_directory, "exit")
            go_back = subprocess.run(
                ["xdotool", "mousemove", str(stairs_x), str(stairs_y), "click", "1"],
                capture_output=True, text=True, timeout=5, check=False,
            )
            if go_back.returncode:
                raise RuntimeError(f"Return exit input failed: {go_back.stderr}")
            time.sleep(7)
            capture_frame("return")
            open_on_return = door_pixels(output_directory, "return", open_state=True)
            closed_on_return = door_pixels(output_directory, "return")
            key_on_return = visible_key_pixels(output_directory, "return")
            preserved = open_on_return >= 40 and closed_on_return < 10 and key_on_return < 10
            (output_directory / "scummvm-state-report.json").write_text(
                json.dumps({"returned_from": goal["room_id"], "stairs_click": [stairs_x, stairs_y],
                            "open_door_pixels": open_on_return,
                            "closed_door_pixels": closed_on_return,
                            "key_room_pixels": key_on_return,
                            "state_preserved": preserved}, indent=2) + "\n", encoding="utf-8",
            )
            if not preserved:
                raise RuntimeError(f"Object state lost on room return: open={open_on_return}, closed={closed_on_return}, key={key_on_return}")
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
    print(f"Using the inventory key opened the door at ({door_x}, {door_y}); walking through reached {goal['room_id']} at ({exit_x}, {exit_y}).")
    print("Return to Harbor preserved the unlocked door and collected key state.")
    print("Camera, inventory and scripted use passed; save/load remains unverified.")


def main() -> int:
    if len(sys.argv) not in (3, 4) or (len(sys.argv) == 4 and sys.argv[3] not in ("--scene-only", "--puzzle-only", "--chain-only", "--static-chain-only", "--recipe-only", "--recipe-reverse-only", "--recipe-chain-only", "--recipe-graph-only", "--recipe-four-only", "--recipe-auto-only")):
        print("Usage: python -m adventure_studio.scumm_launch GAME_DIRECTORY OUTPUT_DIRECTORY [--scene-only|--puzzle-only|--chain-only|--static-chain-only|--recipe-only|--recipe-reverse-only|--recipe-chain-only|--recipe-graph-only|--recipe-four-only|--recipe-auto-only]")
        return 2
    mode = sys.argv[3] if len(sys.argv) == 4 else ""
    launch_smoke(Path(sys.argv[1]), Path(sys.argv[2]),
                 scene_only=mode == "--scene-only", verify_return=mode not in ("--puzzle-only", "--chain-only", "--static-chain-only", "--recipe-only", "--recipe-reverse-only", "--recipe-chain-only", "--recipe-graph-only", "--recipe-four-only", "--recipe-auto-only"),
                 verify_chain=mode in ("--chain-only", "--static-chain-only"),
                 verify_recipe=mode in ("--recipe-only", "--recipe-reverse-only", "--recipe-chain-only", "--recipe-graph-only", "--recipe-four-only", "--recipe-auto-only"),
                 auto_recipe=mode == "--recipe-auto-only",
                 reverse_recipe=mode == "--recipe-reverse-only",
                 allow_static_scene=mode == "--static-chain-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

