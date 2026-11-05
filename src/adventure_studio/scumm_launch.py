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


def colored_item_pixels(output_directory: Path, frame: str,
                        rgb: tuple[int, int, int], inventory: bool = False) -> int:
    screenshot = output_directory / f"scummvm-{frame}.png"
    crop = "640x112+192+472" if inventory else "640x288+192+184"
    result = subprocess.run(
        ["convert", str(screenshot), "-crop", crop, "+repage", "-format", "%c", "histogram:info:"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Could not inspect colored inventory item: {result.stderr}")
    return count_color_pixels(result.stdout, rgb)


def colored_item_center(output_directory: Path, frame: str,
                        rgb: tuple[int, int, int], inventory: bool = False) -> tuple[int, int]:
    screenshot = output_directory / f"scummvm-{frame}.png"
    color_hex = "#" + "".join(f"{channel:02X}" for channel in rgb)
    crop = "640x112+192+472" if inventory else "640x288+192+184"
    result = subprocess.run(
        ["convert", str(screenshot), "-crop", crop, "+repage",
         "-fuzz", "8%", "-fill", "white", "-opaque", color_hex,
         "-fill", "black", "+opaque", "white", "-trim", "-format", "%wx%h%O", "info:"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Could not locate colored inventory item: {result.stderr}")
    x, y = parse_key_bounds(result.stdout)
    return (x, y + 288) if inventory else (x, y)


def door_pixels(output_directory: Path, frame: str, open_state: bool = False) -> int:
    if frame not in ("pickup", "door", "exit", "return", "locked-before", "locked-after",
                     "gated-use", "chain-second", "chain-second-open", "chain-arrival",
                     "chain-middle-state", "chain-first-return"):
        raise ValueError("Invalid door frame")
    screenshot = output_directory / f"scummvm-{frame}.png"
    result = subprocess.run(
        ["convert", str(screenshot), "-crop", "640x288+192+184", "+repage",
         "-format", "%c", "histogram:info:"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Could not inspect door: {result.stderr}")
    return (count_cyan_pixels if open_state else count_green_pixels)(result.stdout)


def door_center(output_directory: Path, frame: str = "pickup") -> tuple[int, int]:
    if frame not in ("pickup", "locked-before", "exit", "chain-second", "chain-arrival"):
        raise ValueError("Invalid closed-door screenshot frame")
    screenshot = output_directory / f"scummvm-{frame}.png"
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
    if frame not in ("door", "chain-second-open"):
        raise ValueError("Invalid opened-door screenshot frame")
    screenshot = output_directory / f"scummvm-{frame}.png"
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
    if frame not in ("end", "pickup", "return"):
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


def launch_smoke(game_directory: Path, output_directory: Path, seconds: float = 6.0,
                 scene_only: bool = False, verify_return: bool = True,
                 verify_chain: bool = False, verify_recipe: bool = False) -> None:
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
    if not isinstance(combinations, list) or len(combinations) > 1:
        raise ValueError("Invalid fixture combination manifest")
    if verify_recipe:
        if len(combinations) != 1 or gates or len(route) != 1:
            raise ValueError("Recipe smoke requires exactly one combination and one exit")
        recipe = combinations[0]
        if (not isinstance(recipe, dict) or set(recipe) != {"room_id", "ingredients", "result"}
                or not isinstance(recipe["ingredients"], list) or len(recipe["ingredients"]) != 2
                or not all(isinstance(item, dict) and set(item) == {"item_id", "rgb"}
                           and isinstance(item["rgb"], list) and len(item["rgb"]) == 3
                           and all(type(c) is int and 0 <= c <= 255 for c in item["rgb"])
                           for item in [*recipe["ingredients"], recipe["result"]])):
            raise ValueError("Invalid recipe color probes")
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
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"ScummVM quit early (exit={process.returncode}); see {log_path}")
                time.sleep(0.1)
            if process.poll() is not None:
                raise RuntimeError(f"ScummVM quit early (exit={process.returncode}); see {log_path}")
            final_snapshot = capture_frame("end")
            changed = compare_frames(output_directory)
            if scene_only:
                print(f"Story-compiled SCUMM room rendered and scrolled: {changed} changed pixels")
                print(f"Scene-only screenshots: {output_directory}")
                return
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
            if verify_recipe:
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
                for x, y in ((408, 506), first_center, second_center):
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
                                "combined": combined}, indent=2) + "\n", encoding="utf-8")
                if not combined:
                    raise RuntimeError("Recipe combination did not consume ingredients and produce result")
                recipe_item_center = colored_item_center(output_directory, "recipe-combined", result_rgb,
                                                         inventory=True)
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
                (output_directory / "scummvm-chain-report.json").write_text(
                    json.dumps({"room_route": [step["room_id"] for step in route] + [goal["room_id"]],
                                "first_door_opened": door_opened, "intermediate_room_visible": arrived,
                                "second_item_acquired": acquired, "second_door_opened": opened,
                                "goal_reached": reached, "return_checks": return_checks,
                                "returns_preserved": reached and len(return_checks) == 6 and all(return_checks.values())},
                               indent=2) + "\n", encoding="utf-8",
                )
                if not reached:
                    raise RuntimeError("Chain did not reach its final story room")
                print("Full chained story gameplay succeeded: both inventory doors opened and final room reached")
                return
            goal_reached = False
            exit_deadline = time.monotonic() + 15.0
            while time.monotonic() < exit_deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"ScummVM quit during exit (exit={process.returncode})")
                capture_frame("exit")
                goal_reached = close_rgb(scene_pixel(output_directory, "exit"), tuple(expected_color))
                if goal_reached:
                    break
                time.sleep(0.4)
            (output_directory / "scummvm-use-report.json").write_text(
                json.dumps({"inventory_item": "Key", "target": "Door",
                            "click": [door_x, door_y], "green_before": initial_door_pixels,
                            "green_after": remaining_door_pixels, "door_opened": door_opened,
                            "open_door_pixels": open_door_pixels,
                            "exit_click": [exit_x, exit_y],
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
    if len(sys.argv) not in (3, 4) or (len(sys.argv) == 4 and sys.argv[3] not in ("--scene-only", "--puzzle-only", "--chain-only", "--recipe-only")):
        print("Usage: python -m adventure_studio.scumm_launch GAME_DIRECTORY OUTPUT_DIRECTORY [--scene-only|--puzzle-only|--chain-only|--recipe-only]")
        return 2
    mode = sys.argv[3] if len(sys.argv) == 4 else ""
    launch_smoke(Path(sys.argv[1]), Path(sys.argv[2]),
                 scene_only=mode == "--scene-only", verify_return=mode not in ("--puzzle-only", "--chain-only", "--recipe-only"),
                 verify_chain=mode == "--chain-only", verify_recipe=mode == "--recipe-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
