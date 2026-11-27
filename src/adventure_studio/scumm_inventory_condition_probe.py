"""Play a cross-room inventory ownership puzzle before and after genuine pickup."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image

from .scumm_assets import CameraCue, RoomHotspot, scrolling_fixture, destination_fixture
from .scumm_project import GameDocument, canonical_json, export_document, parse_document
from .scumm_puzzle_workflow_probe import mask
from .scumm_toolchain import compile_story_game
from .studio_sequences import append_sequence_step, duplicate_sequence_variant, replace_sequence_step

KEY, OUT, BACK, GATE, READY, ACCEPTED = (
    (191, 61, 220), (42, 195, 243), (215, 140, 27),
    (242, 38, 117), (44, 240, 149), (45, 130, 210))
COLORS = (KEY, OUT, BACK, GATE, READY, ACCEPTED)


def authored_project():
    harbor, cellar = scrolling_fixture(), destination_fixture()
    first = len(harbor.palette)
    def marker(name, x, color, pickup=False, alternative=None):
        return RoomHotspot(name, name, name, x, 100, 16, 16, pickup=pickup,
                           sprite_pixels=bytes([first+color])*256,
                           open_sprite_pixels=None if alternative is None else bytes([first+alternative])*256)
    harbor = replace(harbor, palette=(*harbor.palette, *COLORS),
                     hotspots=(marker("Key", 210, 0, pickup=True), marker("Crossing", 290, 1)),
                     use_rules=(), demo_walk_to_x=None, camera_cues=(CameraCue("set", x=320),),
                     ego_start_x=320)
    vault = replace(destination_fixture(), name="Vault", hotspots=(),
                    pixels=bytes([0]) * (320 * 200))
    cellar = replace(cellar, palette=(*cellar.palette, *COLORS), goal_text=None,
                     hotspots=(marker("Return", 80, 2), marker("Gate", 150, 3),
                               marker("Progress", 230, 4, alternative=5)))
    raw = canonical_json(GameDocument("InventoryOwnershipPuzzle", (harbor, cellar, vault)))
    raw = append_sequence_step(raw, "Harbor", "Crossing", "Close",
                               "Raum wechseln", None, None, "Cellar", None)
    raw = append_sequence_step(raw, "Cellar", "Return", "Close",
                               "Raum wechseln", None, None, "Harbor", None)
    raw = append_sequence_step(raw, "Cellar", "Gate", "Close",
                               "Objektzustand setzen", None, None, "Progress", 0)
    raw = duplicate_sequence_variant(raw, "Cellar|Gate|Close", "inv:Key", 1)
    raw = replace_sequence_step(raw, "Cellar|Gate|Close|inv:Key|1", 0,
                                "Objektzustand setzen", None, None, "Progress", 2)
    raw = append_sequence_step(raw, "Cellar", "Progress", "Close",
                               "Raum wechseln", None, None, "Vault", None)
    from .studio_sequences import set_sequence_condition
    raw = set_sequence_condition(raw, "Cellar|Progress|Close", "Progress", 2)
    return raw


def run(upstream, destination):
    build = destination/"build"
    build.mkdir(parents=True, exist_ok=True)
    raw = authored_project()
    (build/"project.json").write_text(raw, encoding="utf-8")
    doc = parse_document((build/"project.json").read_text(encoding="utf-8"))
    if canonical_json(doc) != raw:
        raise RuntimeError("Inventory ownership project did not round-trip")
    export_document(doc, build/"resources")
    game_dir = compile_story_game(build, upstream, destination/"game")
    frames = destination/"screenshots"
    frames.mkdir(exist_ok=True)
    evidence = {}
    def capture(label):
        xwd, png = frames/f"{label}.xwd", frames/f"{label}.png"
        subprocess.run(["xwd","-root","-silent","-out",str(xwd)],check=True,timeout=10)
        subprocess.run(["convert",str(xwd),str(png)],check=True,timeout=10)
        xwd.unlink()
        with Image.open(png) as im:
            return im.convert("RGB")
    def count(image, rgb):
        return mask(image,rgb).histogram()[255]
    def wait(label, visible=(), absent=(), owned=None):
        deadline = time.monotonic()+30
        stable=[]
        i=0
        while time.monotonic()<deadline:
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited during "+label)
            i+=1
            name=f"{label}-{i:03d}"
            screenshot=capture(name)
            scene=screenshot.crop((192,184,832,472))
            inventory=screenshot.crop((528,500,832,540))
            yes=[count(scene,rgb) for rgb in visible]
            no=[count(scene,rgb) for rgb in absent]
            item=count(inventory,KEY)
            if (all(n>=100 for n in yes) and all(n<40 for n in no)
                    and (owned is None or (item>=40 if owned else item<10))):
                stable.append({"frame":name,"visible_pixels":yes,"absent_pixels":no,"inventory_key_pixels":item})
                if len(stable)==3:
                    evidence[label]=stable
                    return scene
            else:
                stable=[]
            time.sleep(.15)
        raise RuntimeError("Native inventory puzzle state missing: "+label)
    def click(label,rgb,pickup=False):
        scene=wait(label,visible=(rgb,))
        bounds=mask(scene,rgb).getbbox()
        x,y=(bounds[0]+bounds[2])/2+192,(bounds[1]+bounds[3])/2+184
        verb=(328,506) if pickup else (234,563)
        for px,py in (verb,(round(x),round(y))):
            subprocess.run(["xdotool","mousemove",str(px),str(py),"click","1"],check=True,timeout=10)
            time.sleep(.25)
    with (frames/"scummvm.log").open("w",encoding="utf-8") as log:
        game=subprocess.Popen(["scummvm",f"--path={game_dir.resolve()}","tentacle"],stdout=log,stderr=subprocess.STDOUT)
        try:
            wait("harbor-before-pickup",visible=(KEY,OUT),owned=False)
            click("cross-without-key",OUT)
            wait("cellar-before-pickup",visible=(GATE,READY),absent=(ACCEPTED,),owned=False)
            click("gate-without-key",GATE)
            wait("blocked-without-key",visible=(GATE,),absent=(READY,ACCEPTED),owned=False)
            click("return-for-key",BACK)
            wait("harbor-return",visible=(KEY,OUT),owned=False)
            click("pick-up-key",KEY,pickup=True)
            wait("key-in-inventory",visible=(OUT,),absent=(KEY,),owned=True)
            time.sleep(2)
            click("cross-with-key",OUT)
            wait("cellar-with-key",visible=(GATE,),absent=(ACCEPTED,),owned=True)
            click("gate-with-key",GATE)
            wait("accepted-with-key",visible=(GATE,ACCEPTED),absent=(READY,),owned=True)
            click("enter-goal",ACCEPTED)
            wait("goal-room",visible=((70,130,190),),absent=(GATE,ACCEPTED),owned=True)
            report={"native_inventory_condition_verified":True,"evidence":evidence}
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
