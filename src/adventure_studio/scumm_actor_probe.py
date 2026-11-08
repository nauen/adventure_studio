"""Native research acceptance: multiple project-authored Actors share a COST."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

from .scumm_assets import destination_fixture, scrolling_fixture
from .scumm_costume_probe import gesture_fixture
from .scumm_costume import CostumeDirection
from .scumm_launch import (launch_smoke, close_rgb, colored_item_center, colored_item_pixels,
                           door_center, door_pixels, scene_pixel, visible_key_pixels)
from .scumm_binary import verify_room_binary
from .scumm_project import (ActorAsset, ActorCountCondition, AnimationRule, AnimationInputRule,
                            AnimationTrigger,
                            GameDocument, ObjectStateEffect, canonical_json,
                            export_document, parse_document)
from .scumm_bootstrap import inject_actor_count_rules
from .scumm_toolchain import _tool, compile_story_game


def actor_count_room_source(source: str, required: int) -> str:
    """Add a native COUNT observer to the isolated generated-room fixture."""
    marker = "        animateActor(Companion,24);\n"
    if source.count(marker) != 1 or type(required) is not int or required not in (0, 1, 2, 3):
        raise ValueError("Invalid native Actor COUNT probe source or event threshold")
    injection = (
        f"        while(getActorAnimCounter1(Companion) < {required}) {{\n"
        "            breakScript();\n"
        "        }\n"
        "        setObjectState(Key, 0);\n"
    )
    camera_and_actor = (
        "        delaySeconds(2);\n"
        "        setCameraAt(480);\n"
        "        putActorAt(Companion, 430, 100, Harbor);\n"
    )
    return source.replace(marker, camera_and_actor + marker + injection, 1)


def actor_binding_room_source(source: str, check: str) -> str:
    """Isolate native Actor identity, Costume assignment and active frame."""
    expressions = {
        "room": "getActorRoom(Companion) == Harbor",
        "costume": "getActorCostume(Companion) != 0",
        "frame": "getActorFrame(Companion) == 24",
    }
    marker = "        animateActor(Companion,24);\n"
    if check not in expressions or source.count(marker) != 1:
        raise ValueError("Invalid native Actor binding probe")
    return source.replace(
        marker,
        "        delaySeconds(2);\n"
        "        setCameraAt(480);\n"
        "        putActorAt(Companion, 430, 100, Harbor);\n"
        + marker
        + f"        if({expressions[check]}) setObjectState(Key, 0);\n", 1)


def project_count_room_source(source: str, document: GameDocument, required: int) -> str:
    """Exercise the same typed JSON-to-native rule path as the exporter."""
    rule = AnimationRule(ActorCountCondition("Companion", required),
                         ObjectStateEffect("Harbor", "Key", 0))
    validated = parse_document(canonical_json(replace(document, animation_rules=(rule,))))
    marker = "        animateActor(Companion,24);\n"
    if source.count(marker) != 1:
        raise ValueError("Missing native authored Actor animation trigger")
    prepared = source.replace(marker,
                              "        delaySeconds(2);\n"
                              "        setCameraAt(480);\n"
                              "        putActorAt(Companion, 430, 100, Harbor);\n"
                              + marker, 1)
    return inject_actor_count_rules(prepared, "Harbor", validated.animation_rules,
                                    validated.actors, validated.costumes)


def run_actor_probe(upstream: Path, destination: Path) -> dict:
    build = destination / "build"
    resources = build / "resources"
    resources.mkdir(parents=True, exist_ok=True)
    base_costume = gesture_fixture()
    # The extra Actor may have a different facing than the upstream hero.
    # Exercise the same two COUNT events in every native costume direction.
    gesture = next(animation for animation in base_costume.animations
                   if animation.name == "gesture")
    commands = gesture.directions[0].commands
    directions = tuple(CostumeDirection(direction, commands, loop=False)
                       for direction in ("N", "E", "S", "W"))
    costume = replace(base_costume, name="StudioCompanionCostume",
                      animations=tuple(replace(animation, directions=directions)
                                       if animation.name == "gesture" else animation
                                       for animation in base_costume.animations))
    document = GameDocument("NativeActorProbe", (scrolling_fixture(), destination_fixture()),
                            (costume,), (
                                ActorAsset("Companion", costume.name, "Harbor", 410, 110, "S", "Companion",
                                           "gesture"),
                                ActorAsset("Guide", costume.name, "Harbor", 470, 110, "E", "Guide"),
                            ), animation_input_rules=(
                                AnimationInputRule("Companion", "Harbor", "Key", "Push", 2,
                                                   ObjectStateEffect("Harbor", "Door", 0),
                                                   ObjectStateEffect("Harbor", "Key", 0)),
                            ), animation_triggers=(
                                AnimationTrigger("Guide", "Harbor", "Key", "Pull", "gesture"),
                            ))
    encoded = canonical_json(document)
    (build / "project.json").write_text(encoded, encoding="utf-8")
    export_document(parse_document(encoded), resources)
    game = compile_story_game(build, upstream, destination / "game")
    launch_smoke(game, destination / "screenshots", scene_only=True)
    result = {"native_actor_link_passed": True, "stock_scummvm_launch_passed": True,
              "actor_count": len(document.actors), "shared_costume_count": len(document.costumes),
              "actors": [actor.id for actor in document.actors],
              "initial_animation_compiled": True,
              "repeatable_animation_action_compiled": True,
              "animation_input_verb_compiled": True,
              "animation_gameplay_verified": False}
    (destination / "native-actor-report.json").write_text(json.dumps(result, indent=2) + "\n",
                                                             encoding="utf-8")
    return result


def run_actor_count_probe(upstream: Path, actor_build: Path, destination: Path) -> dict:
    """Prove two authored-Actor COUNT events, with a three-event control."""
    # Reuse the validated link probe's compiler inputs; its COST was already
    # staged in the external Road fixture and must not be copied a second time.
    resources = actor_build / "build" / "resources"
    for name in ("bootstrap.roobj", "Harbor.scc", "Cellar.roobj", "game-goal.json"):
        if not (resources / name).is_file():
            raise ValueError(f"Missing compiled Actor fixture resource: {name}")
    source = (resources / "Harbor.scc").read_text(encoding="utf-8")
    document = parse_document((actor_build / "build" / "project.json").read_text(encoding="utf-8"))
    road = upstream / "examples" / "road"

    def run_variant(target: Path, generated_source: str) -> int:
        target.mkdir(parents=True, exist_ok=True)
        room_source = target / "Harbor.scc"
        room_source.write_text(generated_source, encoding="utf-8")
        room_object = target / "Harbor.roobj"
        subprocess.run([str(_tool(upstream, "scc")), "-V", "6",
                        "-I", str(upstream / "include"), "-I", str(resources),
                        "-I", str(road), "-R", str(resources),
                        "-o", str(room_object), str(room_source)], check=True, timeout=120)
        subprocess.run([str(_tool(upstream, "sld")), "-o", str(target / "tentacle"),
                        "-key", "0x69", str(resources / "bootstrap.roobj"),
                        str(room_object), str(resources / "Cellar.roobj")],
                       cwd=road, check=True, timeout=120)
        verify_room_binary((target / "tentacle.001").read_bytes(), xor_key=0x69)
        shutil.copyfile(resources / "game-goal.json", target / "game-goal.json")
        launch_smoke(target, target / "screenshots", scene_only=True,
                     allow_static_scene=True)
        return visible_key_pixels(target / "screenshots")

    baseline = run_variant(destination / "zero_counts", actor_count_room_source(source, 0))
    first = run_variant(destination / "one_count", actor_count_room_source(source, 1))
    positive = run_variant(destination / "two_counts", actor_count_room_source(source, 2))
    control = run_variant(destination / "three_counts", actor_count_room_source(source, 3))
    binding_pixels = {check: run_variant(destination / f"binding_{check}",
                                         actor_binding_room_source(source, check))
                      for check in ("room", "costume", "frame")}
    declarative_positive = run_variant(destination / "project_two_counts",
                                        project_count_room_source(source, document, 2))
    passed = (baseline < 40 and first < 40 and positive < 40 and control >= 40
              and declarative_positive < 40)
    report = {"authored_actor_count_verified": passed, "expected_events": 2,
              "zero_count_key_pixels": baseline, "one_count_key_pixels": first,
              "positive_key_pixels": positive, "control_key_pixels": control,
              "project_positive_key_pixels": declarative_positive,
              "actor_binding_key_pixels": binding_pixels}
    (destination / "actor-count-report.json").write_text(json.dumps(report, indent=2) + "\n",
                                                               encoding="utf-8")
    if not passed:
        raise RuntimeError(f"Authored Actor COUNT thresholds failed: {report}")
    return report


def run_actor_input_probe(upstream: Path, actor_build: Path, destination: Path) -> dict:
    """Prove native zero, early, late and repeated Push input outcomes."""
    resources = actor_build / "build" / "resources"
    source = (resources / "Harbor.scc").read_text(encoding="utf-8")
    document = parse_document((actor_build / "build" / "project.json").read_text(encoding="utf-8"))
    first_count_rule = AnimationRule(ActorCountCondition("Companion", 1),
                                     ObjectStateEffect("Harbor", "Door", 2))
    replay_detector = AnimationRule(ActorCountCondition("Companion", 1),
                                    ObjectStateEffect("Harbor", "Key", 1))
    source = inject_actor_count_rules(source, "Harbor", (first_count_rule, replay_detector),
                                      document.actors, document.costumes)
    walk_marker = "        walkActorTo(VAR_EGO, 540, 100);\n"
    if source.count(walk_marker) != 1:
        raise ValueError("Missing fixture hero walk for input probe")
    source = source.replace(walk_marker, "", 1)
    if source.count("        animateActor(Companion,24);\n") != 1:
        raise ValueError("Missing native Actor animation for input probe")
    entry_guard = "        if(!__studioActorInitial0) {\n"
    if source.count(entry_guard) != 1:
        raise ValueError("Missing first-entry animation guard in native input probe")
    # The fixture camera/hero setup is needed on *every* entry. It must not
    # accidentally be hidden inside the production once-only animation guard.
    source = source.replace(entry_guard,
                            "        putActorAt(VAR_EGO, 375, 100, Harbor);\n"
                            "        setCameraAt(480);\n" + entry_guard, 1)
    # Slow only the isolated fixture's Actor, leaving the authored project and
    # exporter timing unchanged. The first COUNT is observable as a cyan door.
    source = source.replace("        animateActor(Companion,24);\n",
                            "        setCurrentActor(Companion);\n"
                            "        setActorAnimSpeed(30);\n"
                            "        setCurrentActor(VAR_EGO);\n"
                            "        delaySeconds(2);\n"
                            "        animateActor(Companion,24);\n", 1)
    destination.mkdir(parents=True, exist_ok=True)
    room_file = destination / "Harbor.scc"
    room_file.write_text(source, encoding="utf-8")
    road = upstream / "examples" / "road"
    room_obj = destination / "Harbor.roobj"
    subprocess.run([str(_tool(upstream, "scc")), "-V", "6",
                    "-I", str(upstream / "include"), "-I", str(resources),
                    "-I", str(road), "-R", str(resources),
                    "-o", str(room_obj), str(room_file)], check=True, timeout=120)
    subprocess.run([str(_tool(upstream, "sld")), "-o", str(destination / "tentacle"),
                    "-key", "0x69", str(resources / "bootstrap.roobj"),
                    str(room_obj), str(resources / "Cellar.roobj")],
                   cwd=road, check=True, timeout=120)
    verify_room_binary((destination / "tentacle.001").read_bytes(), xor_key=0x69)

    def run_click(kind: str) -> dict:
        output = destination / kind
        output.mkdir(parents=True, exist_ok=True)
        if not os.environ.get("DISPLAY"):
            raise RuntimeError("Input probe needs a virtual X display")
        environment = {**os.environ, "SDL_AUDIODRIVER": "dummy"}

        def frame(name: str) -> None:
            xwd = output / f"scummvm-{name}.xwd"
            png = output / f"scummvm-{name}.png"
            subprocess.run(["xwd", "-root", "-silent", "-out", str(xwd)],
                           check=True, stdout=subprocess.DEVNULL, timeout=10)
            subprocess.run(["convert", str(xwd), str(png)], check=True,
                           stdout=subprocess.DEVNULL, timeout=10)

        def click(x: int, y: int) -> None:
            subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                           check=True, timeout=10)

        with (output / "scummvm.log").open("w", encoding="utf-8") as log:
            game = subprocess.Popen(["scummvm", f"--path={destination.resolve()}", "tentacle"],
                                    stdout=log, stderr=subprocess.STDOUT, env=environment)
            try:
                started = time.monotonic()
                first_count = None
                while time.monotonic() - started < 16:
                    if game.poll() is not None:
                        raise RuntimeError(f"ScummVM ended before COUNT: {kind}")
                    frame("door")
                    if door_pixels(output, "door", open_state=True) >= 40:
                        first_count = time.monotonic()
                        break
                    time.sleep(0.08)
                if first_count is None:
                    raise RuntimeError(f"Native first COUNT marker never opened door: {kind}")
                key_x, key_y = colored_item_center(output, "door", (255, 220, 75))
                if kind != "none":
                    if kind in ("late", "return"):
                        time.sleep(6)
                    click(392, 524)  # Upstream Road Push verb at logical (100, 170).
                    click(key_x, key_y)
                time.sleep(2.5)
                first_result = None
                if kind == "repeat":
                    frame("after-first")
                    first_result = {
                        "key_pixels": colored_item_pixels(output, "after-first", (255, 220, 75)),
                        "open_door_pixels": colored_item_pixels(output, "after-first", (50, 220, 220)),
                    }
                    # The first action hides the door but leaves the Key hotspot
                    # reachable. A later click must re-evaluate COUNT, not
                    # silently reuse the first branch or lose the input.
                    time.sleep(6)
                    click(392, 524)
                    click(key_x, key_y)
                    time.sleep(2.5)
                elif kind == "none":
                    time.sleep(6)
                return_result = None
                if kind == "return":
                    frame("post-action")
                    before_return = {
                        "key_pixels": colored_item_pixels(output, "post-action", (255, 220, 75)),
                        "open_door_pixels": colored_item_pixels(output, "post-action", (50, 220, 220)),
                    }
                    if before_return["key_pixels"] >= 10 or before_return["open_door_pixels"] < 40:
                        raise RuntimeError(f"Late input was not effective before room exit: {before_return}")

                    # WalkTo is selected again after a completed sentence.
                    # Hit the open door frame away from the overlapping Guide Actor.
                    door_x, door_y = colored_item_center(output, "post-action", (50, 220, 220))
                    click(door_x - 12, door_y - 12)
                    deadline = time.monotonic() + 14
                    while time.monotonic() < deadline:
                        if game.poll() is not None:
                            raise RuntimeError("ScummVM stopped before the Cellar transition")
                        frame("cellar")
                        if close_rgb(scene_pixel(output, "cellar"), (120, 70, 180)):
                            break
                        time.sleep(0.3)
                    else:
                        raise RuntimeError("WalkTo open Door did not reach Cellar")
                    time.sleep(1)
                    frame("exit")
                    stairs_x, stairs_y = door_center(output, "exit")
                    click(stairs_x, stairs_y)
                    # On return the normal room-entry scripts run again.
                    # Wait for the camera to reach the right side before sampling.
                    deadline = time.monotonic() + 16
                    while time.monotonic() < deadline:
                        if game.poll() is not None:
                            raise RuntimeError("ScummVM stopped before Harbor re-entry")
                        frame("return")
                        if close_rgb(scene_pixel(output, "return"), (240, 175, 95)):
                            break
                        time.sleep(0.3)
                    else:
                        raise RuntimeError("Stairs did not return to visible Harbor")
                    # An unguarded re-entry restarts the COST and its COUNT
                    # watcher, which would make the already removed Key visible.
                    time.sleep(5)
                    frame("return")
                    return_result = {
                        "key_pixels": colored_item_pixels(output, "return", (255, 220, 75)),
                        "open_door_pixels": colored_item_pixels(output, "return", (50, 220, 220)),
                        "cellar_reached": True, "harbor_reentered": True,
                        "exit_click": [door_x - 12, door_y - 12],
                        "stairs_click": [stairs_x, stairs_y],
                    }
                frame("end")
                gold = visible_key_pixels(output)
                cyan = colored_item_pixels(output, "end", (50, 220, 220))
                return {"key_pixels": gold, "open_door_pixels": cyan,
                        "first_count_time": round(first_count - started, 3),
                        "key_click": [key_x, key_y],
                        **({"after_first": first_result} if first_result is not None else {}),
                        **({"after_return": return_result} if return_result is not None else {})}
            finally:
                game.terminate()
                try:
                    game.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    game.kill()
                    game.wait(timeout=5)

    none = run_click("none")
    early = run_click("early")
    late = run_click("late")
    repeat = run_click("repeat")
    returned = run_click("return")
    report = {"native_early_late_and_repeated_input_verified": (
              none["key_pixels"] >= 10 and none["open_door_pixels"] >= 40
              and
              early["key_pixels"] >= 10 and early["open_door_pixels"] < 40
              and late["key_pixels"] < 40 and late["open_door_pixels"] >= 40
              and repeat["after_first"]["key_pixels"] >= 10
              and repeat["after_first"]["open_door_pixels"] < 40
              and repeat["key_pixels"] < 40 and repeat["open_door_pixels"] < 40),
              "native_room_return_state_verified": (
              returned["after_return"]["cellar_reached"]
              and returned["after_return"]["harbor_reentered"]
              and returned["after_return"]["key_pixels"] < 10
              and returned["after_return"]["open_door_pixels"] >= 40),
              "none": none, "early": early, "late": late, "repeat": repeat,
              "return": returned}
    (destination / "actor-input-report.json").write_text(json.dumps(report, indent=2) + "\n",
                                                          encoding="utf-8")
    if not (report["native_early_late_and_repeated_input_verified"]
            and report["native_room_return_state_verified"]):
        raise RuntimeError(f"Native COUNT input state or room return differs: {report}")
    return report


if __name__ == "__main__":
    if len(sys.argv) == 3:
        print(run_actor_probe(Path(sys.argv[1]), Path(sys.argv[2])))
    elif len(sys.argv) == 5 and sys.argv[1] == "--count":
        print(run_actor_count_probe(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])))
    elif len(sys.argv) == 5 and sys.argv[1] == "--input":
        print(run_actor_input_probe(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])))
    else:
        raise SystemExit("Usage: python -m adventure_studio.scumm_actor_probe SCUMMC_DIR OUTPUT_DIR | --count SCUMMC_DIR ACTOR_BUILD OUTPUT_DIR")
