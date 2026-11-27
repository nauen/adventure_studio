"""Observe actual moving costume pixels, with unchanged stand pose after arrival."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image, ImageChops

from .scumm_assets import CameraCue, RoomHotspot, scrolling_fixture, destination_fixture
from .scumm_costume import CostumeAnimation, CostumeDirection
from .scumm_costume_probe import gesture_fixture
from .scumm_project import ActorAsset, GameDocument, canonical_json, export_document, parse_document
from .scumm_toolchain import compile_story_game
from .studio_sequences import append_sequence_step, author_room_walkbox, set_sequence_skippable

COLORS = ((242, 38, 117), (44, 240, 149), (215, 140, 27))
MARKERS = ((191, 61, 220), (42, 195, 243), (45, 130, 210))


def color_mask(image, rgb):
    bands = [band.point([255 if abs(value-target) <= 7 else 0 for value in range(256)])
             for band, target in zip(image.split(), rgb)]
    return ImageChops.multiply(ImageChops.multiply(bands[0], bands[1]), bands[2])


def measure_pose(lane):
    """Find one dense native Costume block; ignore sparse same-palette Ego pixels.

    Only pixels in the uniquely identified Costume columns count toward the
    pose verdict. Multiple dense blocks are ambiguous and fail closed.
    """
    columns = [[0] * lane.width for _ in COLORS]
    for pose, rgb in enumerate(COLORS):
        mask = color_mask(lane, rgb)
        for i, value in enumerate(mask.getdata()):
            if value:
                columns[pose][i % lane.width] += 1
    density = [sum(values) for values in zip(*columns)]
    blocks = []
    start = None
    for x, count in enumerate((*density, 0)):
        if count >= 24:
            if start is None:
                start = x
        elif start is not None:
            if x-start >= 8 and sum(density[start:x]) >= 100:
                blocks.append((start, x))
            start = None
    if len(blocks) != 1:
        return None, [sum(values) for values in columns]
    left, right = blocks[0]
    return (left+right-1)/2, [sum(values[left:right]) for values in columns]


def run(upstream, destination):
    build = destination / "build"
    room = scrolling_fixture()
    index = len(room.palette)
    controls = tuple(RoomHotspot(name, name, name, x, 120, 16, 16,
                                sprite_pixels=bytes([index+i])*256)
                     for i, (name, x) in enumerate((("Alternative", 210), ("Restore", 250),
                                                    ("CheckWalk", 290))))
    room = replace(room, palette=(*room.palette, *MARKERS),
                   hotspots=(*room.hotspots, *controls), demo_walk_to_x=None,
                   camera_cues=(CameraCue("set", x=320),), ego_start_x=320)
    costume = gesture_fixture()
    palette = list(costume.palette)
    for i, color in enumerate(COLORS):
        palette[17+i] = color
    base = costume.frames[0]
    frames = tuple(replace(base, id=name, pixels=bytes([i+1])*(base.width*base.height))
                   for i, name in enumerate(("DefaultWalk", "AlternateWalk", "Standing")))
    def directions(frame):
        return tuple(CostumeDirection(d, (frame,)) for d in ("N","E","S","W"))
    costume = replace(costume, name="NativeWalkBindingCostume", palette=tuple(palette),
                      frames=frames, animations=(
                          CostumeAnimation("walk", directions("DefaultWalk")),
                          CostumeAnimation("stand", directions("Standing")),
                          CostumeAnimation("init", directions("Standing")),
                          CostumeAnimation("stride", directions("AlternateWalk"), 24)))
    raw = canonical_json(GameDocument("NativeWalkBinding", (room, destination_fixture()),
                                      (costume,), (ActorAsset("Guide", costume.name, "Harbor", 180, 85, "S"),)))
    raw = author_room_walkbox(raw, "Harbor", 1, "160,70; 480,70; 480,150; 160,150")
    raw = append_sequence_step(raw, "Harbor", "Alternative", "Close",
                               "Actor Laufanimation", "Guide", "stride", None, None)
    for kind, x, y in (("Actor laufen lassen", 460, 85), ("Auf Actor warten", None, None)):
        raw = append_sequence_step(raw, "Harbor", "Alternative", "Close", kind,
                                   "Guide", None, None, None, x, y)
    for kind, who, anim, target, amount in (
            ("Objektzustand setzen", None, None, "Restore", 0),
            ("Warten", None, None, None, 12),
            ("Actor Laufanimation", "Guide", "walk", None, None)):
        raw = append_sequence_step(raw, "Harbor", "Restore", "Close", kind, who, anim, target, amount)
    raw = set_sequence_skippable(raw, "Harbor|Restore|Close", True)
    for kind, x, y in (("Actor laufen lassen", 180, 85), ("Auf Actor warten", None, None)):
        raw = append_sequence_step(raw, "Harbor", "CheckWalk", "Close", kind,
                                   "Guide", None, None, None, x, y)
    build.mkdir(parents=True, exist_ok=True)
    (build / "project.json").write_text(raw, encoding="utf-8")
    export_document(parse_document(raw), build / "resources")
    game_dir = compile_story_game(build, upstream, destination / "game")
    screenshots = destination / "screenshots"
    screenshots.mkdir(exist_ok=True)

    def capture(label):
        xwd = screenshots / f"scummvm-{label}.xwd"
        png = screenshots / f"scummvm-{label}.png"
        subprocess.run(["xwd", "-root", "-silent", "-out", str(xwd)], check=True, timeout=10)
        subprocess.run(["convert", str(xwd), str(png)], check=True, timeout=10)
        xwd.unlink()
        with Image.open(png) as im:
            return im.convert("RGB").crop((192, 184, 832, 472))

    def points(image, rgb):
        mask = color_mask(image, rgb)
        return [(i % image.width, i // image.width) for i,value in enumerate(mask.getdata()) if value]

    def center(pixels):
        if len(pixels)<100:
            return None
        xs,ys=zip(*pixels)
        return (min(xs)+max(xs))/2,(min(ys)+max(ys))/2

    def click(label,color):
        point=center(points(capture(label),color))
        if point is None:
            raise RuntimeError(f"Native interaction target missing: {label}")
        for i,(x,y) in enumerate(((234,563),(round(point[0]+192),round(point[1]+184)))):
            subprocess.run(["xdotool","mousemove",str(x),str(y),"click","1"],check=True,timeout=10)
            if i == 0:
                time.sleep(.2)

    def observe(label, start_x, target_x, walk_pose=None, timeout=25):
        deadline = time.monotonic()+timeout
        moving, arrival = [], []
        attempt = 0
        while time.monotonic()<deadline:
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited during walk binding")
            name = f"{label}-{attempt:03d}"
            attempt += 1
            image = capture(name)
            anchor = center(points(image, MARKERS[0]))
            actor_x, counts = measure_pose(image.crop((0,96,image.width,181)))
            if anchor is not None and actor_x is not None:
                x = 218+(actor_x-anchor[0])/2
                pose = next((i for i,n in enumerate(counts)
                             if n>=100 and all(v<40 for j,v in enumerate(counts) if j!=i)), None)
                row = {"frame": name, "x": x, "pose": pose, "pixels": counts}
                if (walk_pose is not None and pose == walk_pose
                        and min(start_x,target_x)+10 < x < max(start_x,target_x)-10):
                    if not moving or (x-moving[-1]["x"])*(target_x-start_x)>0:
                        moving.append(row)
                if abs(x-target_x)<10 and pose == 2:
                    arrival.append(row)
                    if len(arrival)==5:
                        if walk_pose is not None and (len(moving)<3 or
                                abs(moving[-1]["x"]-moving[0]["x"])<32):
                            raise RuntimeError(f"Native walk pose not visible at three moving positions: {moving}")
                        return {"moving": moving, "arrival": arrival}
                else:
                    arrival = []
            else:
                arrival = []
            time.sleep(.02 if walk_pose is not None else .2)
        raise RuntimeError(f"Native walk/arrival missing: {label}, moving={moving}, arrival={arrival}")

    with (screenshots / "scummvm.log").open("w",encoding="utf-8") as log:
        game=subprocess.Popen(["scummvm",f"--path={game_dir.resolve()}","tentacle"],
                              stdout=log,stderr=subprocess.STDOUT)
        try:
            initial=observe("initial",180,180)
            click("alternative-click",MARKERS[0])
            alternative=observe("alternative-walk",180,460,1)
            click("restore-click",MARKERS[1])
            deadline=time.monotonic()+20
            while time.monotonic()<deadline:
                if game.poll() is not None:
                    raise RuntimeError("ScummVM exited before walk binding restore")
                if center(points(capture("restore-start"),MARKERS[1])) is None:
                    break
                time.sleep(.2)
            else:
                raise RuntimeError("Native restore cutscene did not begin")
            started=time.monotonic()
            subprocess.run(["xdotool","keydown","Escape"],check=True,timeout=5)
            try:
                time.sleep(.25)
            finally:
                subprocess.run(["xdotool","keyup","Escape"],check=True,timeout=5)
            time.sleep(.5)
            # Rebinding is not an animation command. Only the next arrival
            # should use the restored native walk frame.
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited after walk binding Escape")
            click("check-click",MARKERS[2])
            restored=observe("restored-walk",460,180,0)
            report={"initial":initial,"alternative":alternative,"restored":restored,
                    "escape_to_arrival_seconds":time.monotonic()-started,
                    "native_actor_walk_animation_verified":True}
            (destination/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
            return report
        finally:
            game.terminate()
            try:
                game.wait(timeout=5)
            except subprocess.TimeoutExpired:
                game.kill()
                game.wait(timeout=5)


if __name__=="__main__":
    print(json.dumps(run(Path(sys.argv[1]),Path(sys.argv[2])),indent=2))
