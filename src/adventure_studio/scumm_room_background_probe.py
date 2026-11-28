"""Import, save, reopen, synchronize and render a real authored room PNG."""
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw

from .scumm_launch import launch_smoke
from .scumm_project import export_document, parse_document
from .scumm_toolchain import compile_story_game
from .studio_project import canonical_studio_project, parse_studio_project
from .studio_sequences import author_room_camera_plan, compose_story_project, import_room_background


def run(upstream: Path, destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    story = (Path(__file__).resolve().parents[2] / "examples" /
             "mini_story_chain.json").read_text(encoding="utf-8")
    raw = compose_story_project(story)
    source = destination / "harbor.png"
    colors = ((18, 166, 111), (175, 37, 210))
    image = Image.new("RGB", (640, 200), colors[0])
    ImageDraw.Draw(image).rectangle((160, 0, 639, 199), fill=colors[1])
    image.save(source)
    raw = import_room_background(raw, "Harbor", str(source))
    raw = author_room_camera_plan(raw, "Harbor", 60, 100, "set:160", True)
    saved = destination / "adventure.studio.json"
    saved.write_text(canonical_studio_project(story, raw), encoding="utf-8")
    story, restored = parse_studio_project(saved.read_text(encoding="utf-8"))
    raw = compose_story_project(story, restored)
    document = parse_document(raw)
    room = document.rooms[0]
    if not room.authored_background or tuple(room.palette[i] for i in room.pixels) != tuple(image.getdata()):
        raise RuntimeError("Authored PNG changed after Studio reload/synchronization")
    build = destination / "build"
    build.mkdir(exist_ok=True)
    (build / "project.json").write_text(raw, encoding="utf-8")
    export_document(document, build / "resources")
    game = compile_story_game(build, upstream, destination / "game")
    screenshots = destination / "screenshots"
    launch_smoke(game, screenshots, seconds=8, scene_only=True, allow_static_scene=True)
    observations = []
    with Image.open(screenshots / "scummvm-end.png") as source:
        frame = source.convert("RGB")
        for expected, xs in zip(colors, ((40, 80, 120), (200, 240, 280))):
            for x in xs:
                observed = frame.getpixel((192 + 2*x, 184 + 2*30))
                if max(abs(a-b) for a, b in zip(expected, observed)) > 8:
                    raise RuntimeError(f"Authored background pixel mismatch at {x}: {observed}, expected {expected}")
                observations.append({"room_x": x, "room_y": 30, "expected": expected, "observed": observed})
    report = {"native_authored_room_background_verified": True, "samples": observations}
    (destination / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
