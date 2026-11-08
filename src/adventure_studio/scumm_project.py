"""Versioned, declarative SCUMM project document and deterministic exporter.

No script strings or executable code are accepted from a project document.
The existing room compiler validates names, geometry, palette and references.
"""

from __future__ import annotations

import base64
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from .palette_animation import PaletteCycle
from .scumm_costume import (CostumeAnimation, CostumeAsset, CostumeDirection,
                           CostumeFrame, validate_costume, write_costume_sources)
from .scumm_assets import (CameraCue, CombineRule, RoomAsset, RoomHotspot, ScaleCurve, TalkChoice,
                           TalkRule, UseRule, Walkbox, ZPlane, _validate, write_game_sources)
from .targets import RoomGeometry


@dataclass(frozen=True)
class ActorAsset:
    """An authored native Actor symbol with an initial room placement."""

    id: str
    costume: str
    room: str
    x: int
    y: int
    direction: str = "S"
    display_name: str | None = None
    initial_animation: str | None = None


@dataclass(frozen=True)
class ActorCountCondition:
    actor_id: str
    minimum_count: int


@dataclass(frozen=True)
class ObjectStateEffect:
    room: str
    hotspot_id: str
    state: int


@dataclass(frozen=True)
class AnimationRule:
    condition: ActorCountCondition
    effect: ObjectStateEffect


@dataclass(frozen=True)
class AnimationInputRule:
    """Branch on an object verb before/after a native costume COUNT marker."""

    actor_id: str
    room: str
    hotspot_id: str
    verb: str
    before_count: int
    on_time: ObjectStateEffect
    too_late: ObjectStateEffect


@dataclass(frozen=True)
class AnimationTrigger:
    """Replay a named native Costume animation through a room object's verb."""

    actor_id: str
    room: str
    hotspot_id: str
    verb: str
    animation: str


@dataclass(frozen=True)
class AnimateActorStep:
    actor_id: str
    animation: str


@dataclass(frozen=True)
class ObjectStateStep:
    hotspot_id: str
    state: int


@dataclass(frozen=True)
class DelayStep:
    seconds: int


@dataclass(frozen=True)
class MoveActorStep:
    actor_id: str
    x: int
    y: int


@dataclass(frozen=True)
class WalkActorStep:
    actor_id: str
    x: int
    y: int


@dataclass(frozen=True)
class InteractionSequence:
    """Ordered native actions initiated by a room object verb."""

    room: str
    hotspot_id: str
    verb: str
    steps: tuple[AnimateActorStep | ObjectStateStep | DelayStep | MoveActorStep | WalkActorStep, ...]


@dataclass(frozen=True)
class GameDocument:
    id: str
    rooms: tuple[RoomAsset, ...]
    costumes: tuple[CostumeAsset, ...] = ()
    actors: tuple[ActorAsset, ...] = ()
    animation_rules: tuple[AnimationRule, ...] = ()
    animation_input_rules: tuple[AnimationInputRule, ...] = ()
    animation_triggers: tuple[AnimationTrigger, ...] = ()
    interaction_sequences: tuple[InteractionSequence, ...] = ()


def _only(data: object, allowed: set[str], required: set[str]) -> dict:
    if not isinstance(data, dict) or set(data) - allowed or required - set(data):
        raise ValueError(f"Invalid document fields: expected {sorted(allowed)}")
    return data


def _decode_pixels(encoded: object) -> bytes:
    if not isinstance(encoded, str):
        raise ValueError("Pixel data must be base64")
    try:
        return base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as error:
        raise ValueError("Invalid base64 pixel data") from error


def _encode_pixels(pixels: bytes | None) -> str | None:
    return base64.b64encode(pixels).decode("ascii") if pixels is not None else None


def document_dict(document: GameDocument) -> dict:
    _validate_document(document)
    return {
        "format_version": 1,
        "id": document.id,
        **({"costumes": [{
            "name": costume.name,
            "palette": [list(rgb) for rgb in costume.palette],
            "palette_first": costume.palette_first,
            "palette_last": costume.palette_last,
            "frames": [{"id": frame.id, "width": frame.width, "height": frame.height,
                        "pixels": _encode_pixels(frame.pixels),
                        "offset_x": frame.offset_x, "offset_y": frame.offset_y}
                       for frame in costume.frames],
            "animations": [{"name": animation.name,
                            **({"index": animation.index} if animation.index is not None else {}),
                            "directions": [{"direction": direction.direction,
                                            "commands": list(direction.commands),
                                            "loop": direction.loop}
                                           for direction in animation.directions]}
                           for animation in costume.animations],
        } for costume in document.costumes]} if document.costumes else {}),
        **({"actors": [{"id": actor.id, "costume": actor.costume, "room": actor.room,
                       "x": actor.x, "y": actor.y, "direction": actor.direction,
                       **({"display_name": actor.display_name} if actor.display_name is not None else {}),
                       **({"initial_animation": actor.initial_animation} if actor.initial_animation is not None else {})}
                      for actor in document.actors]} if document.actors else {}),
        **({"animation_rules": [{"condition": {"actor_id": rule.condition.actor_id,
                                               "minimum_count": rule.condition.minimum_count},
                                 "effect": {"room": rule.effect.room,
                                            "hotspot_id": rule.effect.hotspot_id,
                                            "state": rule.effect.state}}
                                for rule in document.animation_rules]} if document.animation_rules else {}),
        **({"animation_input_rules": [{"actor_id": rule.actor_id, "room": rule.room,
                                         "hotspot_id": rule.hotspot_id, "verb": rule.verb,
                                         "before_count": rule.before_count,
                                         "on_time": vars(rule.on_time),
                                         "too_late": vars(rule.too_late)}
                                        for rule in document.animation_input_rules]}
           if document.animation_input_rules else {}),
        **({"animation_triggers": [vars(trigger) for trigger in document.animation_triggers]}
           if document.animation_triggers else {}),
        **({"interaction_sequences": [{"room": sequence.room,
                                        "hotspot_id": sequence.hotspot_id,
                                        "verb": sequence.verb,
                                        "steps": [({"type": "animate_actor", **vars(step)}
                                                   if isinstance(step, AnimateActorStep)
                                                   else {"type": "set_object_state", **vars(step)}
                                                   if isinstance(step, ObjectStateStep)
                                                   else {"type": "move_actor", **vars(step)}
                                                   if isinstance(step, MoveActorStep)
                                                   else {"type": "walk_actor", **vars(step)}
                                                   if isinstance(step, WalkActorStep)
                                                   else {"type": "delay_seconds", **vars(step)})
                                                  for step in sequence.steps]}
                                       for sequence in document.interaction_sequences]}
           if document.interaction_sequences else {}),
        "rooms": [{
            "name": room.name,
            "geometry": {"width": room.geometry.room_width, "height": room.geometry.room_height,
                         "viewport_width": room.geometry.viewport_width,
                         "viewport_height": room.geometry.viewport_height},
            "pixels": _encode_pixels(room.pixels),
            "palette": [list(rgb) for rgb in room.palette],
            **({"zplanes": [{"index": plane.index, "pixels": _encode_pixels(plane.pixels)}
                            for plane in room.zplanes]} if room.zplanes else {}),
            **({"walkboxes": [{"corners": [list(point) for point in box.corners],
                                "mask": box.mask, "flags": box.flags, "scale": box.scale,
                                **({"scale_slot": box.scale_slot} if box.scale_slot is not None else {})}
                               for box in room.walkboxes]} if room.walkboxes else {}),
            **({"box_routes": [[target for target in row] for row in room.box_routes]}
               if room.box_routes else {}),
            **({"scale_slots": _encode_pixels(room.scale_slots)}
               if room.scale_slots is not None else {}),
            **({"scale_curves": [{"slot": c.slot, "scale1": c.scale1,
                                  "y1": c.y1, "scale2": c.scale2, "y2": c.y2}
                                 for c in room.scale_curves]} if room.scale_curves else {}),
            **({"demo_walk_to_y": room.demo_walk_to_y}
               if room.demo_walk_to_y is not None else {}),
            **({"camera_cues": [{"operation": cue.operation,
                                  **({"x": cue.x} if cue.x is not None else {})}
                                 for cue in room.camera_cues]} if room.camera_cues else {}),
            "hotspots": [{"id": h.id, "label": h.label, "description": h.description,
                          "x": h.x, "y": h.y, "width": h.width, "height": h.height,
                          "pickup": h.pickup, "sprite_pixels": _encode_pixels(h.sprite_pixels),
                          "open_sprite_pixels": _encode_pixels(h.open_sprite_pixels),
                          "exit_destination": h.exit_destination,
                          **({"talk_lines": list(h.talk_lines)} if h.talk_lines else {})} for h in room.hotspots],
            "use_rules": [{"item_id": r.item_id, "target_id": r.target_id,
                           "response": r.response, "hide_target": r.hide_target,
                           "destination_room": r.destination_room, "open_target": r.open_target,
                           "requires_inventory": list(r.requires_inventory)}
                          for r in room.use_rules],
            "demo_walk_to_x": room.demo_walk_to_x,
            "goal_text": room.goal_text,
            **({"combine_rules": [{"first_id": rule.first_id, "second_id": rule.second_id,
                                    "result_id": rule.result_id, "response": rule.response}
                                   for rule in room.combine_rules]} if room.combine_rules else {}),
            **({"palette_cycles": [{"name": cycle.name, "first": cycle.first,
                                     "last": cycle.last, "period_ticks": cycle.period_ticks,
                                     "reverse": cycle.reverse}
                                    for cycle in room.palette_cycles]} if room.palette_cycles else {}),
            **({"music_id": room.music_id} if room.music_id is not None else {}),
            **({"talk_rules": [{"speaker_id": rule.speaker_id,
                                 "opening_lines": list(rule.opening_lines),
                                 "choices": [{"object_id": c.object_id,
                                              "caption": c.caption,
                                              "reply_lines": list(c.reply_lines)}
                                             for c in rule.choices]}
                                for rule in room.talk_rules]} if room.talk_rules else {}),
        } for room in document.rooms],
    }


def _validate_document(document: GameDocument) -> None:
    if not isinstance(document.id, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", document.id):
        raise ValueError("Invalid game project identifier")
    if not document.rooms or len(document.rooms) > 64:
        raise ValueError("Project must contain between 1 and 64 rooms")
    room_names = [r.name for r in document.rooms]
    if len(set(room_names)) != len(room_names):
        raise ValueError("Duplicate room name")
    costume_names = set()
    costumes_by_name = {}
    for costume in document.costumes:
        validate_costume(costume)
        if costume.name in costume_names or costume.name in room_names:
            raise ValueError("Duplicate or conflicting costume name")
        costume_names.add(costume.name)
        costumes_by_name[costume.name] = costume
    actor_ids = set()
    for actor in document.actors:
        if (not isinstance(actor.id, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", actor.id)
                or actor.id in actor_ids or actor.id in room_names or actor.id in costume_names):
            raise ValueError(f"Duplicate or invalid actor ID: {actor.id}")
        actor_ids.add(actor.id)
        if actor.costume not in costume_names:
            raise ValueError(f"Actor {actor.id} references unknown costume: {actor.costume}")
        if actor.initial_animation is not None:
            animations = [animation for animation in costumes_by_name[actor.costume].animations
                          if animation.name == actor.initial_animation]
            if not animations:
                raise ValueError(f"Actor {actor.id} references unknown animation: {actor.initial_animation}")
            if animations[0].index is None:
                raise ValueError(f"Actor {actor.id} initial animation requires an explicit native index")
            if actor.direction not in {direction.direction for direction in animations[0].directions}:
                raise ValueError(f"Actor {actor.id} initial animation lacks direction {actor.direction}")
        if actor.room not in room_names:
            raise ValueError(f"Actor {actor.id} references unknown room: {actor.room}")
        room = next(room for room in document.rooms if room.name == actor.room)
        if (type(actor.x) is not int or type(actor.y) is not int
                or not 0 <= actor.x < room.geometry.room_width
                or not 0 <= actor.y < room.geometry.room_height):
            raise ValueError(f"Actor {actor.id} initial position outside room")
        if actor.direction not in ("N", "E", "S", "W"):
            raise ValueError(f"Actor {actor.id} has invalid initial direction")
        if (actor.display_name is not None and (not isinstance(actor.display_name, str)
                or not 1 <= len(actor.display_name) <= 80
                or any(ord(c) < 32 or ord(c) > 126 or c in '\\"' for c in actor.display_name))):
            raise ValueError(f"Actor {actor.id} has invalid display name")
    for room in document.rooms:
        _validate(room)
        for destination in (r.destination_room for r in room.use_rules):
            if destination is not None and destination not in room_names:
                raise ValueError(f"Unknown destination room: {destination}")
        for destination in (h.exit_destination for h in room.hotspots):
            if destination is not None and destination not in room_names:
                raise ValueError(f"Unknown exit destination room: {destination}")
    if sum(r.goal_text is not None for r in document.rooms) != 1:
        raise ValueError("Project needs exactly one goal room")
    actors_by_id = {actor.id: actor for actor in document.actors}
    rooms_by_name = {room.name: room for room in document.rooms}
    for rule in document.animation_rules:
        if not isinstance(rule, AnimationRule) or not isinstance(rule.condition, ActorCountCondition) or not isinstance(rule.effect, ObjectStateEffect):
            raise ValueError("Invalid typed animation rule")
        if any(not isinstance(value, str) for value in
               (rule.condition.actor_id, rule.effect.room, rule.effect.hotspot_id)):
            raise ValueError("COUNT rules require string identifiers")
        actor = actors_by_id.get(rule.condition.actor_id)
        if actor is None or actor.initial_animation is None:
            raise ValueError(f"COUNT condition requires an Actor with an initial animation: {rule.condition.actor_id}")
        if type(rule.condition.minimum_count) is not int or rule.condition.minimum_count < 1:
            raise ValueError("COUNT condition requires a positive event threshold")
        costume = costumes_by_name[actor.costume]
        animation = next(animation for animation in costume.animations
                         if animation.name == actor.initial_animation)
        direction = next(direction for direction in animation.directions
                         if direction.direction == actor.direction)
        events_per_cycle = direction.commands.count("COUNT")
        if events_per_cycle == 0 or (not direction.loop and rule.condition.minimum_count > events_per_cycle):
            raise ValueError(f"COUNT threshold is unreachable in Actor {actor.id}'s initial animation")
        room = rooms_by_name.get(rule.effect.room)
        if room is None or actor.room != rule.effect.room:
            raise ValueError(f"COUNT rule requires the Actor in its effect room: {rule.effect.room}")
        if rule.effect.hotspot_id not in {hotspot.id for hotspot in room.hotspots}:
            raise ValueError(f"COUNT effect references unknown room hotspot: {rule.effect.hotspot_id}")
        if type(rule.effect.state) is not int or not 0 <= rule.effect.state <= 2:
            raise ValueError("COUNT effect requires a supported SCUMM object state 0, 1 or 2")
    seen_inputs = set()
    for rule in document.animation_input_rules:
        if not isinstance(rule, AnimationInputRule):
            raise ValueError("Invalid typed animation input rule")
        actor = actors_by_id.get(rule.actor_id) if isinstance(rule.actor_id, str) else None
        if actor is None or actor.initial_animation is None:
            raise ValueError("Animation input requires an Actor with an initial animation")
        room = rooms_by_name.get(rule.room) if isinstance(rule.room, str) else None
        if room is None or room.name != actor.room:
            raise ValueError("Animation input Actor and hotspot must share a room")
        if not isinstance(rule.hotspot_id, str) or rule.hotspot_id not in {h.id for h in room.hotspots}:
            raise ValueError("Animation input references unknown hotspot")
        if rule.verb not in ("Push", "Pull", "Open", "Close"):
            raise ValueError("Unsupported animation input verb")
        identity = (rule.room, rule.hotspot_id, rule.verb)
        if identity in seen_inputs:
            raise ValueError("Duplicate animation input verb binding")
        seen_inputs.add(identity)
        costume = costumes_by_name[actor.costume]
        animation = next(a for a in costume.animations if a.name == actor.initial_animation)
        direction = next(d for d in animation.directions if d.direction == actor.direction)
        count = direction.commands.count("COUNT")
        if (type(rule.before_count) is not int or rule.before_count < 1
                or (not direction.loop and rule.before_count > count) or count == 0):
            raise ValueError("Animation input COUNT boundary is unreachable")
        for effect in (rule.on_time, rule.too_late):
            if not isinstance(effect, ObjectStateEffect) or effect.room != room.name:
                raise ValueError("Animation input effect must target its room")
            if not isinstance(effect.hotspot_id, str) or effect.hotspot_id not in {h.id for h in room.hotspots}:
                raise ValueError("Animation input effect references unknown hotspot")
            if type(effect.state) is not int or not 0 <= effect.state <= 2:
                raise ValueError("Animation input effect requires object state 0, 1 or 2")
    for trigger in document.animation_triggers:
        if not isinstance(trigger, AnimationTrigger):
            raise ValueError("Invalid typed animation trigger")
        actor = actors_by_id.get(trigger.actor_id) if isinstance(trigger.actor_id, str) else None
        room = rooms_by_name.get(trigger.room) if isinstance(trigger.room, str) else None
        if actor is None or room is None or actor.room != room.name:
            raise ValueError("Animation trigger requires an Actor in its room")
        if (not isinstance(trigger.hotspot_id, str)
                or trigger.hotspot_id not in {hotspot.id for hotspot in room.hotspots}):
            raise ValueError("Animation trigger references unknown hotspot")
        if trigger.verb not in ("Push", "Pull", "Open", "Close"):
            raise ValueError("Unsupported animation trigger verb")
        identity = (trigger.room, trigger.hotspot_id, trigger.verb)
        if identity in seen_inputs:
            raise ValueError("Duplicate animation verb binding")
        seen_inputs.add(identity)
        costume = costumes_by_name[actor.costume]
        animation = next((item for item in costume.animations if item.name == trigger.animation), None)
        if animation is None or animation.index is None:
            raise ValueError("Animation trigger requires a named, explicitly indexed animation")
        if actor.direction not in {direction.direction for direction in animation.directions}:
            raise ValueError("Animation trigger lacks the Actor's direction")
    for sequence in document.interaction_sequences:
        if not isinstance(sequence, InteractionSequence):
            raise ValueError("Invalid typed interaction sequence")
        room = rooms_by_name.get(sequence.room) if isinstance(sequence.room, str) else None
        if room is None or not isinstance(sequence.hotspot_id, str) or sequence.hotspot_id not in {
                hotspot.id for hotspot in room.hotspots}:
            raise ValueError("Interaction sequence requires an existing room hotspot")
        if sequence.verb not in ("Push", "Pull", "Open", "Close"):
            raise ValueError("Unsupported interaction sequence verb")
        identity = (sequence.room, sequence.hotspot_id, sequence.verb)
        if identity in seen_inputs:
            raise ValueError("Duplicate animation verb binding")
        seen_inputs.add(identity)
        if not isinstance(sequence.steps, tuple) or not sequence.steps:
            raise ValueError("Interaction sequence requires ordered steps")
        for step in sequence.steps:
            if isinstance(step, AnimateActorStep):
                actor = actors_by_id.get(step.actor_id) if isinstance(step.actor_id, str) else None
                if actor is None or actor.room != room.name:
                    raise ValueError("Interaction animation Actor must be in the sequence room")
                costume = costumes_by_name[actor.costume]
                animation = next((item for item in costume.animations if item.name == step.animation), None)
                if animation is None or animation.index is None:
                    raise ValueError("Interaction animation requires named, indexed Costume animation")
                if actor.direction not in {direction.direction for direction in animation.directions}:
                    raise ValueError("Interaction animation lacks Actor direction")
            elif isinstance(step, ObjectStateStep):
                if (not isinstance(step.hotspot_id, str)
                        or step.hotspot_id not in {hotspot.id for hotspot in room.hotspots}
                        or type(step.state) is not int or not 0 <= step.state <= 2):
                    raise ValueError("Interaction state step requires a valid room object and native state")
            elif isinstance(step, DelayStep):
                if type(step.seconds) is not int or step.seconds < 1:
                    raise ValueError("Interaction delay must be positive whole seconds")
            elif isinstance(step, (MoveActorStep, WalkActorStep)):
                actor = actors_by_id.get(step.actor_id) if isinstance(step.actor_id, str) else None
                if (actor is None or actor.room != room.name or type(step.x) is not int
                        or type(step.y) is not int
                        or not 0 <= step.x < room.geometry.room_width
                        or not 0 <= step.y < room.geometry.room_height):
                    raise ValueError("Interaction movement requires an Actor and position in the sequence room")
            else:
                raise ValueError("Unsupported interaction sequence step")


def parse_document(source: str) -> GameDocument:
    """Reject unknown fields and invalid references before exporting anything."""
    try:
        root = json.loads(source)
    except json.JSONDecodeError as error:
        raise ValueError("Invalid project JSON") from error
    data = _only(root, {"format_version", "id", "rooms", "costumes", "actors", "animation_rules", "animation_input_rules", "animation_triggers", "interaction_sequences"},
                 {"format_version", "id", "rooms"})
    if type(data["format_version"]) is not int or data["format_version"] != 1:
        raise ValueError("Unsupported project format version")
    if not isinstance(data["rooms"], list):
        raise ValueError("Rooms must be a list")
    if len(data["rooms"]) > 64:
        raise ValueError("Too many rooms")
    raw_costumes = data.get("costumes", [])
    if not isinstance(raw_costumes, list):
        raise ValueError("Costumes must be a list")
    costumes = []
    for raw_costume in raw_costumes:
        costume = _only(raw_costume, {"name", "palette", "palette_first", "palette_last",
                                     "frames", "animations"},
                        {"name", "palette", "frames", "animations"})
        if not isinstance(costume["frames"], list) or not isinstance(costume["animations"], list):
            raise ValueError("Costume frames and animations must be lists")
        frames = []
        for raw_frame in costume["frames"]:
            frame = _only(raw_frame, {"id", "width", "height", "pixels", "offset_x", "offset_y"},
                          {"id", "width", "height", "pixels"})
            frames.append(CostumeFrame(frame["id"], frame["width"], frame["height"],
                                      _decode_pixels(frame["pixels"]),
                                      frame.get("offset_x", 0), frame.get("offset_y", 0)))
        animations = []
        for raw_animation in costume["animations"]:
            animation = _only(raw_animation, {"name", "index", "directions"},
                              {"name", "directions"})
            if not isinstance(animation["directions"], list):
                raise ValueError("Costume directions must be a list")
            directions = []
            for raw_direction in animation["directions"]:
                direction = _only(raw_direction, {"direction", "commands", "loop"},
                                  {"direction", "commands"})
                if not isinstance(direction["commands"], list):
                    raise ValueError("Costume commands must be a list")
                directions.append(CostumeDirection(direction["direction"],
                                                   tuple(direction["commands"]),
                                                   direction.get("loop", True)))
            animations.append(CostumeAnimation(animation["name"], tuple(directions),
                                               animation.get("index")))
        costumes.append(CostumeAsset(costume["name"], tuple(tuple(rgb) for rgb in costume["palette"]),
                                     tuple(frames), tuple(animations),
                                     costume.get("palette_first", 16), costume.get("palette_last", 47)))
    raw_actors = data.get("actors", [])
    if not isinstance(raw_actors, list):
        raise ValueError("Actors must be a list")
    actors = []
    for raw_actor in raw_actors:
        actor = _only(raw_actor, {"id", "costume", "room", "x", "y", "direction", "display_name", "initial_animation"},
                      {"id", "costume", "room", "x", "y"})
        actors.append(ActorAsset(actor["id"], actor["costume"], actor["room"],
                                 actor["x"], actor["y"], actor.get("direction", "S"),
                                 actor.get("display_name"), actor.get("initial_animation")))
    raw_animation_rules = data.get("animation_rules", [])
    if not isinstance(raw_animation_rules, list):
        raise ValueError("Animation rules must be a list")
    animation_rules = []
    for raw_rule in raw_animation_rules:
        item = _only(raw_rule, {"condition", "effect"}, {"condition", "effect"})
        condition = _only(item["condition"], {"actor_id", "minimum_count"},
                          {"actor_id", "minimum_count"})
        effect = _only(item["effect"], {"room", "hotspot_id", "state"},
                       {"room", "hotspot_id", "state"})
        animation_rules.append(AnimationRule(ActorCountCondition(**condition),
                                             ObjectStateEffect(**effect)))
    raw_inputs = data.get("animation_input_rules", [])
    if not isinstance(raw_inputs, list):
        raise ValueError("Animation input rules must be a list")
    animation_inputs = []
    for raw_rule in raw_inputs:
        item = _only(raw_rule, {"actor_id", "room", "hotspot_id", "verb", "before_count", "on_time", "too_late"},
                     {"actor_id", "room", "hotspot_id", "verb", "before_count", "on_time", "too_late"})
        effects = []
        for key in ("on_time", "too_late"):
            effect = _only(item[key], {"room", "hotspot_id", "state"}, {"room", "hotspot_id", "state"})
            effects.append(ObjectStateEffect(**effect))
        animation_inputs.append(AnimationInputRule(item["actor_id"], item["room"],
                                                   item["hotspot_id"], item["verb"],
                                                   item["before_count"], *effects))
    raw_triggers = data.get("animation_triggers", [])
    if not isinstance(raw_triggers, list):
        raise ValueError("Animation triggers must be a list")
    animation_triggers = []
    for raw_trigger in raw_triggers:
        item = _only(raw_trigger, {"actor_id", "room", "hotspot_id", "verb", "animation"},
                     {"actor_id", "room", "hotspot_id", "verb", "animation"})
        animation_triggers.append(AnimationTrigger(**item))
    raw_sequences = data.get("interaction_sequences", [])
    if not isinstance(raw_sequences, list):
        raise ValueError("Interaction sequences must be a list")
    interaction_sequences = []
    for raw_sequence in raw_sequences:
        item = _only(raw_sequence, {"room", "hotspot_id", "verb", "steps"},
                     {"room", "hotspot_id", "verb", "steps"})
        if not isinstance(item["steps"], list):
            raise ValueError("Interaction steps must be a list")
        steps = []
        for raw_step in item["steps"]:
            if not isinstance(raw_step, dict):
                raise ValueError("Invalid interaction sequence step")
            kind = raw_step.get("type")
            if kind == "animate_actor":
                step = _only(raw_step, {"type", "actor_id", "animation"},
                             {"type", "actor_id", "animation"})
                steps.append(AnimateActorStep(step["actor_id"], step["animation"]))
            elif kind == "set_object_state":
                step = _only(raw_step, {"type", "hotspot_id", "state"},
                             {"type", "hotspot_id", "state"})
                steps.append(ObjectStateStep(step["hotspot_id"], step["state"]))
            elif kind == "delay_seconds":
                step = _only(raw_step, {"type", "seconds"}, {"type", "seconds"})
                steps.append(DelayStep(step["seconds"]))
            elif kind == "move_actor":
                step = _only(raw_step, {"type", "actor_id", "x", "y"},
                             {"type", "actor_id", "x", "y"})
                steps.append(MoveActorStep(step["actor_id"], step["x"], step["y"]))
            elif kind == "walk_actor":
                step = _only(raw_step, {"type", "actor_id", "x", "y"},
                             {"type", "actor_id", "x", "y"})
                steps.append(WalkActorStep(step["actor_id"], step["x"], step["y"]))
            else:
                raise ValueError("Unsupported interaction sequence step type")
        interaction_sequences.append(InteractionSequence(item["room"], item["hotspot_id"],
                                                         item["verb"], tuple(steps)))
    rooms = []
    for raw in data["rooms"]:
        room = _only(raw, {"name", "geometry", "pixels", "palette", "hotspots", "use_rules", "combine_rules", "palette_cycles", "music_id", "talk_rules", "zplanes", "walkboxes", "box_routes", "scale_slots", "scale_curves", "camera_cues",
                           "demo_walk_to_x", "demo_walk_to_y", "goal_text"},
                     {"name", "geometry", "pixels", "palette", "hotspots", "use_rules",
                      "demo_walk_to_x", "goal_text"})
        g = _only(room["geometry"], {"width", "height", "viewport_width", "viewport_height"},
                  {"width", "height", "viewport_width", "viewport_height"})
        if any(type(value) is not int for value in g.values()):
            raise ValueError("Room geometry must use integers")
        if not isinstance(room["hotspots"], list) or not isinstance(room["use_rules"], list):
            raise ValueError("Hotspots and rules must be lists")
        raw_planes = room.get("zplanes", [])
        if not isinstance(raw_planes, list) or len(raw_planes) > 9:
            raise ValueError("Invalid room Z-plane list")
        planes = []
        for raw_plane in raw_planes:
            plane = _only(raw_plane, {"index", "pixels"}, {"index", "pixels"})
            if type(plane["index"]) is not int:
                raise ValueError("Z-plane index must be an integer")
            planes.append(ZPlane(plane["index"], _decode_pixels(plane["pixels"])))
        raw_boxes = room.get("walkboxes", [])
        if not isinstance(raw_boxes, list) or len(raw_boxes) > 254:
            raise ValueError("Invalid room walkbox list")
        boxes = []
        for raw_box in raw_boxes:
            box = _only(raw_box, {"corners", "mask", "flags", "scale", "scale_slot"},
                        {"corners", "mask", "flags", "scale"})
            if not isinstance(box["corners"], list) or any(
                not isinstance(point, list) or len(point) != 2 for point in box["corners"]
            ):
                raise ValueError("Walkbox corners must be coordinate lists")
            boxes.append(Walkbox(tuple(tuple(point) for point in box["corners"]),
                                 box["mask"], box["flags"], box["scale"], box.get("scale_slot")))
        raw_routes = room.get("box_routes", [])
        if not isinstance(raw_routes, list) or any(not isinstance(row, list) for row in raw_routes):
            raise ValueError("Invalid walkbox route matrix")
        routes = tuple(tuple(row) for row in raw_routes)
        scale = room.get("scale_slots")
        if scale is not None:
            scale = _decode_pixels(scale)
        raw_curves = room.get("scale_curves", [])
        if not isinstance(raw_curves, list) or len(raw_curves) > 4:
            raise ValueError("Invalid SCAL curve list")
        curves = []
        for item in raw_curves:
            curve = _only(item, {"slot", "scale1", "y1", "scale2", "y2"},
                          {"slot", "scale1", "y1", "scale2", "y2"})
            curves.append(ScaleCurve(**curve))
        raw_camera = room.get("camera_cues", [])
        if not isinstance(raw_camera, list):
            raise ValueError("Camera cues must be a list")
        camera_cues = []
        for item in raw_camera:
            cue = _only(item, {"operation", "x"}, {"operation"})
            camera_cues.append(CameraCue(cue["operation"], cue.get("x")))
        raw_combinations = room.get("combine_rules", [])
        if not isinstance(raw_combinations, list) or len(raw_combinations) > 16:
            raise ValueError("Invalid combine rules")
        combinations = []
        raw_talk_rules = room.get("talk_rules", [])
        if not isinstance(raw_talk_rules, list) or len(raw_talk_rules) > 16:
            raise ValueError("Invalid dialogue rules")
        talk_rules = []
        for raw_talk in raw_talk_rules:
            talk = _only(raw_talk, {"speaker_id", "opening_lines", "choices"},
                         {"speaker_id", "opening_lines", "choices"})
            if (not isinstance(talk["speaker_id"], str)
                    or not isinstance(talk["opening_lines"], list)
                    or not all(isinstance(x, str) for x in talk["opening_lines"])
                    or not isinstance(talk["choices"], list)):
                raise ValueError("Invalid dialogue rule content")
            choices = []
            for raw_choice in talk["choices"]:
                choice = _only(raw_choice, {"object_id", "caption", "reply_lines"},
                               {"object_id", "caption", "reply_lines"})
                if (not isinstance(choice["object_id"], str) or not isinstance(choice["caption"], str)
                        or not isinstance(choice["reply_lines"], list)
                        or not all(isinstance(x, str) for x in choice["reply_lines"])):
                    raise ValueError("Invalid dialogue choice content")
                choices.append(TalkChoice(choice["object_id"], choice["caption"], tuple(choice["reply_lines"])))
            talk_rules.append(TalkRule(talk["speaker_id"], tuple(talk["opening_lines"]), tuple(choices)))
        raw_cycles = room.get("palette_cycles", [])
        if not isinstance(raw_cycles, list) or len(raw_cycles) > 16:
            raise ValueError("Invalid palette cycles")
        cycles = []
        for raw_cycle in raw_cycles:
            cycle = _only(raw_cycle, {"name", "first", "last", "period_ticks", "reverse"},
                          {"name", "first", "last", "period_ticks", "reverse"})
            if not isinstance(cycle["name"], str) or type(cycle["reverse"]) is not bool:
                raise ValueError("Invalid palette cycle fields")
            cycles.append(PaletteCycle(**cycle))
        for raw_rule in raw_combinations:
            rule = _only(raw_rule, {"first_id", "second_id", "result_id", "response"},
                         {"first_id", "second_id", "result_id", "response"})
            if any(not isinstance(v, str) for v in rule.values()):
                raise ValueError("Combination fields must be strings")
            combinations.append(CombineRule(**rule))
        hotspots = []
        for item in room["hotspots"]:
            h = _only(item, {"id", "label", "description", "x", "y", "width", "height", "pickup",
                             "sprite_pixels", "open_sprite_pixels", "exit_destination", "talk_lines"},
                      {"id", "label", "description", "x", "y", "width", "height", "pickup",
                       "sprite_pixels", "open_sprite_pixels", "exit_destination"})
            if type(h["pickup"]) is not bool:
                raise ValueError("Pickup must be a Boolean")
            talk_lines = h.get("talk_lines", [])
            if not isinstance(talk_lines, list) or not all(isinstance(x, str) for x in talk_lines):
                raise ValueError("Invalid dialogue lines")
            hotspots.append(RoomHotspot(
                h["id"], h["label"], h["description"], h["x"], h["y"], h["width"], h["height"],
                h["pickup"], _decode_pixels(h["sprite_pixels"]) if h["sprite_pixels"] is not None else None,
                _decode_pixels(h["open_sprite_pixels"]) if h["open_sprite_pixels"] is not None else None,
                h["exit_destination"], tuple(talk_lines),
            ))
        rules = []
        for item in room["use_rules"]:
            r = _only(item, {"item_id", "target_id", "response", "hide_target", "destination_room",
                             "open_target", "requires_inventory"},
                      {"item_id", "target_id", "response", "hide_target", "destination_room",
                       "open_target", "requires_inventory"})
            if type(r["hide_target"]) is not bool or type(r["open_target"]) is not bool:
                raise ValueError("Rule state actions must be Booleans")
            if not isinstance(r["requires_inventory"], list) or len(r["requires_inventory"]) > 16:
                raise ValueError("Invalid inventory requirements")
            if any(not isinstance(item_id, str) for item_id in r["requires_inventory"]):
                raise ValueError("Inventory requirement IDs must be strings")
            rules.append(UseRule(**{**r, "requires_inventory": tuple(r["requires_inventory"])}))
        if not isinstance(room["palette"], list):
            raise ValueError("Palette must be a list")
        rooms.append(RoomAsset(
            room["name"], RoomGeometry(g["width"], g["height"], g["viewport_width"], g["viewport_height"]),
            _decode_pixels(room["pixels"]), tuple(tuple(rgb) for rgb in room["palette"]),
            tuple(hotspots), room["demo_walk_to_x"], tuple(rules), room["goal_text"], tuple(combinations),
            tuple(cycles),
            room.get("music_id"),
            tuple(talk_rules),
            tuple(planes), tuple(boxes), routes, scale, tuple(curves), room.get("demo_walk_to_y"), tuple(camera_cues),
        ))
    document = GameDocument(data["id"], tuple(rooms), tuple(costumes), tuple(actors),
                            tuple(animation_rules), tuple(animation_inputs), tuple(animation_triggers),
                            tuple(interaction_sequences))
    _validate_document(document)
    return document


def canonical_json(document: GameDocument) -> str:
    return json.dumps(document_dict(document), sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def export_document(document: GameDocument, directory: Path) -> None:
    """Generate identical files for identical inputs; never interpret code."""
    _validate_document(document)
    write_game_sources(document.rooms, directory)
    for costume in document.costumes:
        write_costume_sources(costume, directory)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.scumm_project PROJECT.json OUTPUT_DIRECTORY")
        return 2
    source = Path(sys.argv[1]).read_text(encoding="utf-8")
    document = parse_document(source)
    export_document(document, Path(sys.argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
