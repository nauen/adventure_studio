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


def run(upstream: Path, destination: Path, width: int = 640) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    story = (Path(__file__).resolve().parents[2] / "examples" /
             "mini_story_chain.json").read_text(encoding="utf-8")
    raw = compose_story_project(story)
    source = destination / "harbor.png"
    colors = ((18, 166, 111), (175, 37, 210))
    left = width - 320 if width > 640 else 0
    image = Image.new("RGB", (width, 200), (70, 130, 190))
    ImageDraw.Draw(image).rectangle((left, 0, left + 159, 199), fill=colors[0])
    ImageDraw.Draw(image).rectangle((left + 160, 0, width - 1, 199), fill=colors[1])
    image.save(source)
    raw = import_room_background(raw, "Harbor", str(source), expand_width=width > 640)
    raw = author_room_camera_plan(raw, "Harbor", 60, 100, f"set:{left + 160}", True)
    saved = destination / "adventure.studio.json"
    saved.write_text(canonical_studio_project(story, raw), encoding="utf-8")
    story, restored = parse_studio_project(saved.read_text(encoding="utf-8"))
    raw = compose_story_project(story, restored)
    document = parse_document(raw)
    room = document.rooms[0]
    if (not room.authored_background or room.geometry.room_width != width
            or tuple(room.palette[i] for i in room.pixels) != tuple(image.getdata())):
        raise RuntimeError("Authored PNG changed after Studio reload/synchronization")
    build = destination / "build"
    build.mkdir(exist_ok=True)
    (build / "project.json").write_text(raw, encoding="utf-8")
    export_document(document, build / "resources")
    game = compile_story_game(build, upstream, destination / "game")
    screenshots = destination / "screenshots"
    launch_smoke(game, screenshots, seconds=8, scene_only=True, allow_static_scene=True,
                 scene_ready_rgb=colors[1])
    observations = []
    with Image.open(screenshots / "scummvm-end.png") as source:
        frame = source.convert("RGB")
        for expected, xs in zip(colors, ((40, 80, 120), (200, 240, 280))):
            for x in xs:
                observed = frame.getpixel((192 + 2*x, 184 + 2*30))
                if max(abs(a-b) for a, b in zip(expected, observed)) > 8:
                    raise RuntimeError(f"Authored background pixel mismatch at {x}: {observed}, expected {expected}")
                observations.append({"room_x": left + x, "room_y": 30, "expected": expected, "observed": observed})
    report = {"native_authored_room_background_verified": True, "room_width": width, "samples": observations}
    (destination / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    upstream, destination = Path(sys.argv[1]), Path(sys.argv[2])
    print(json.dumps(run(upstream, destination), indent=2))
    print(json.dumps(run(upstream, destination / "extended", width=960), indent=2))
