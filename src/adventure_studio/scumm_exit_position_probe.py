"""Author room exits and verify real native forward and return transitions."""
import json
from pathlib import Path
import sys

from .scumm_launch import launch_smoke, door_center, colored_item_center
from .scumm_project import export_document, parse_document
from .scumm_toolchain import compile_story_game
from .studio_project import canonical_studio_project, parse_studio_project
from .studio_sequences import author_exit_position, compose_story_project


def run(upstream: Path, destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    story = (Path(__file__).resolve().parents[2] / "examples" /
             "mini_story_chain.json").read_text(encoding="utf-8")
    raw = compose_story_project(story)
    placements = (("Harbor", "Door", 480, 80), ("Cellar", "Door2", 496, 80),
                  ("Cellar", "Back2", 144, 80), ("Archive", "Back3", 152, 80))
    for room, hotspot, x, y in placements:
        raw = author_exit_position(raw, room, hotspot, x, y)
    saved = destination / "adventure.studio.json"
    saved.write_text(canonical_studio_project(story, raw), encoding="utf-8")
    restored_story, restored = parse_studio_project(saved.read_text(encoding="utf-8"))
    raw = compose_story_project(restored_story, restored)
    document = parse_document(raw)
    for room, hotspot, x, y in placements:
        selected = next(h for r in document.rooms if r.name == room for h in r.hotspots if h.id == hotspot)
        if (selected.x, selected.y, selected.authored_exit_position) != (x, y, True):
            raise RuntimeError(f"Authored exit position lost on reload: {room}/{hotspot}")
    build = destination / "build"
    build.mkdir(exist_ok=True)
    (build / "project.json").write_text(raw, encoding="utf-8")
    export_document(document, build / "resources")
    game = compile_story_game(build, upstream, destination / "game")
    screenshots = destination / "screenshots"
    launch_smoke(game, screenshots, seconds=8, verify_chain=True)
    report = json.loads((screenshots / "scummvm-chain-report.json").read_text(encoding="utf-8"))
    if (report["room_route"] != ["Harbor", "Cellar", "Archive"]
            or not all(report[key] for key in ("first_door_opened", "intermediate_room_visible",
                                              "second_item_acquired", "second_door_opened",
                                              "goal_reached", "returns_preserved"))):
        raise RuntimeError(f"Authored exits did not preserve native story progression: {report}")
    back_rgb = (160, 230, 55)
    samples = {"Door": door_center(screenshots, "locked-before"),
               "Door2": door_center(screenshots, "chain-arrival"),
               "Back2": colored_item_center(screenshots, "chain-middle-back", back_rgb),
               "Back3": colored_item_center(screenshots, "chain-goal", back_rgb)}
    # The viewport never scrolls vertically; the goal room is exactly one viewport wide.
    if any(abs(y - (184 + 2 * (80 + 8))) > 8 for x, y in samples.values()):
        raise RuntimeError(f"Rendered exit Y does not match the authored position: {samples}")
    if abs(samples["Back3"][0] - (192 + 2 * (152 + 8))) > 8:
        raise RuntimeError(f"Rendered goal exit X does not match the authored position: {samples}")
    report.update(native_authored_exit_positions_verified=True, screen_centers=samples)
    (destination / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
