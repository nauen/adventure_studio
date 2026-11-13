"""Deterministic 8-bit SCUMM source-asset preparation (not a linked game)."""

from __future__ import annotations

import json
import re
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

from .palette_animation import PaletteCycle, validate_cycles
from .scumm_direction import actor_facing_angle
from .targets import RoomGeometry, validate_geometry

_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class RoomHotspot:
    id: str
    label: str
    description: str
    x: int
    y: int
    width: int
    height: int
    pickup: bool = False
    sprite_pixels: bytes | None = None
    open_sprite_pixels: bytes | None = None
    exit_destination: str | None = None
    talk_lines: tuple[str, ...] = ()
    talk_actor_lines: tuple[str, ...] = ()
    talk_face_directions: tuple[str | None, ...] = ()
    object_zplane_pixels: bytes | None = None
    open_object_zplane_pixels: bytes | None = None


@dataclass(frozen=True)
class UseRule:
    """Use an inventory item on a room hotspot; no arbitrary script payload."""
    item_id: str
    target_id: str
    response: str
    hide_target: bool = False
    destination_room: str | None = None
    open_target: bool = False
    requires_inventory: tuple[str, ...] = ()
    unlock_walkbox: int | None = None  # native index 1..N, changed by successful Use
    reversible_walkbox: bool = False  # repeated Use toggles door and its native box


@dataclass(frozen=True)
class CombineRule:
    """Consume two owned pickups to create one initially hidden inventory item."""
    first_id: str
    second_id: str
    result_id: str
    response: str


@dataclass(frozen=True)
class TalkChoice:
    """A clickable in-room answer marker, controlled by a dialogue rule."""
    object_id: str
    caption: str
    reply_lines: tuple[str, ...]
    next_stage_id: str | None = None


@dataclass(frozen=True)
class TalkStage:
    id: str
    opening_lines: tuple[str, ...]
    choices: tuple[TalkChoice, ...]


@dataclass(frozen=True)
class TalkRule:
    speaker_id: str
    opening_lines: tuple[str, ...]
    choices: tuple[TalkChoice, ...]
    stages: tuple[TalkStage, ...] = ()
    actor_lines: tuple[tuple[str, str], ...] = ()
    actor_directions: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ZPlane:
    """One full-room binary occlusion mask (0=clear, 1=occluding)."""
    index: int
    pixels: bytes


@dataclass(frozen=True)
class Walkbox:
    """Four native SCUMM walkbox corners in UL, UR, LR, LL order."""
    corners: tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]
    mask: int = 0
    flags: int = 0
    scale: int = 255
    scale_slot: int | None = None


@dataclass(frozen=True)
class ScaleCurve:
    """Native SCUMM-v6 vertical perspective curve in one SCAL slot (1..4)."""
    slot: int
    scale1: int
    y1: int
    scale2: int
    y2: int


@dataclass(frozen=True)
class CameraCue:
    """One native v6 camera operation, ordered within room entry."""
    operation: str  # set, pan, wait, follow_ego
    x: int | None = None


@dataclass(frozen=True)
class RoomAsset:
    name: str
    geometry: RoomGeometry
    pixels: bytes
    palette: tuple[tuple[int, int, int], ...]
    hotspots: tuple[RoomHotspot, ...] = ()
    demo_walk_to_x: int | None = None
    use_rules: tuple[UseRule, ...] = ()
    goal_text: str | None = None
    combine_rules: tuple[CombineRule, ...] = ()
    palette_cycles: tuple[PaletteCycle, ...] = ()
    music_id: str | None = None
    talk_rules: tuple[TalkRule, ...] = ()
    zplanes: tuple[ZPlane, ...] = ()
    walkboxes: tuple[Walkbox, ...] = ()
    box_routes: tuple[tuple[int | None, ...], ...] = ()
    scale_slots: bytes | None = None
    scale_curves: tuple[ScaleCurve, ...] = ()
    demo_walk_to_y: int | None = None
    camera_cues: tuple[CameraCue, ...] = ()


def _scumm_string(value: str) -> str:
    """Return a deliberately restricted ScummC string literal."""
    if not value or len(value) > 160 or any(ord(c) < 32 or ord(c) > 126 or c in '\\"' for c in value):
        raise ValueError("Unsupported SCUMM text character")
    return f'"{value}"'


def _validate(room: RoomAsset) -> None:
    validate_geometry(room.geometry)
    if not _IDENTIFIER.fullmatch(room.name):
        raise ValueError("Invalid SCUMM room identifier")
    width = room.geometry.room_width
    height = room.geometry.room_height
    if width % 8:
        raise ValueError("Experimental strip exporter requires width divisible by eight")
    if len(room.pixels) != width * height:
        raise ValueError("Pixel buffer length mismatch")
    if not (1 <= len(room.palette) <= 256):
        raise ValueError("Indexed palette must have between 1 and 256 colors")
    if any(len(rgb) != 3 or any(type(c) is not int or not 0 <= c <= 255 for c in rgb)
           for rgb in room.palette):
        raise ValueError("Palette contains invalid RGB values")
    if room.pixels and max(room.pixels) >= len(room.palette):
        raise ValueError("Pixels reference missing palette entries")
    # ScummC scc.h: SCC_MAX_IM_PLANES == 10; index zero is reserved.
    if len(room.zplanes) > 9 or tuple(p.index for p in room.zplanes) != tuple(range(1, len(room.zplanes) + 1)):
        raise ValueError("Z-plane indices must be unique and consecutive from 1 (maximum 9)")
    for plane in room.zplanes:
        if len(plane.pixels) != width * height or any(value not in (0, 1) for value in plane.pixels):
            raise ValueError("Z-plane must contain one binary pixel per room pixel")
    if len(room.walkboxes) > 254:
        raise ValueError("SCUMM supports at most 254 authored walkboxes plus reserved box zero")
    for box in room.walkboxes:
        if len(box.corners) != 4 or any(len(point) != 2 or any(type(v) is not int for v in point) for point in box.corners):
            raise ValueError("Walkbox requires four integer coordinate pairs")
        if any(not 0 <= x < width or not 0 <= y < height for x, y in box.corners):
            raise ValueError("Walkbox corners outside room bounds")
        if any(type(value) is not int or not 0 <= value <= limit
               for value, limit in ((box.mask, 255), (box.flags, 255), (box.scale, 65535))):
            raise ValueError("Invalid native walkbox mask, flags or scale")
        if box.scale_slot is not None and (
            type(box.scale_slot) is not int or not 1 <= box.scale_slot <= 4
            or box.scale != 255
        ):
            raise ValueError("Walkbox scale slot requires slot 1..4 and default constant scale 255")
    if len(room.scale_curves) > 4 or len({curve.slot for curve in room.scale_curves}) != len(room.scale_curves):
        raise ValueError("SCAL supports at most four distinct scale curves")
    for curve in room.scale_curves:
        if (type(curve.slot) is not int or not 1 <= curve.slot <= 4
            or any(type(v) is not int for v in (curve.scale1, curve.y1, curve.scale2, curve.y2))
            or not 1 <= curve.scale1 <= 255 or not 1 <= curve.scale2 <= 255
            or not 0 <= curve.y1 < curve.y2 < height):
            raise ValueError("Invalid SCAL curve endpoint or slot")
    if room.scale_slots is not None and room.scale_curves:
        raise ValueError("Raw SCAL bytes and typed curves cannot be combined")
    curve_slots = {curve.slot for curve in room.scale_curves}
    if any(box.scale_slot is not None and box.scale_slot not in curve_slots
           for box in room.walkboxes):
        raise ValueError("Walkbox references an undefined SCAL curve")
    count = len(room.walkboxes) + 1
    if room.box_routes:
        if not room.walkboxes or len(room.box_routes) != count or any(len(row) != count for row in room.box_routes):
            raise ValueError("BOXM route matrix must include the reserved box zero")
        for row in room.box_routes:
            if any(value is not None and (type(value) is not int or not 0 <= value < count) for value in row):
                raise ValueError("Invalid BOXM route target")
    if room.scale_slots is not None and (not room.walkboxes or len(room.scale_slots) != 32):
        raise ValueError("SCAL requires exactly 32 bytes and walkboxes")
    if room.demo_walk_to_x is not None and (
        type(room.demo_walk_to_x) is not int
        or not 0 <= room.demo_walk_to_x < width
    ):
        raise ValueError("Demo walk target outside room bounds")
    if room.demo_walk_to_y is not None and (
        room.demo_walk_to_x is None or type(room.demo_walk_to_y) is not int
        or not 0 <= room.demo_walk_to_y < height
    ):
        raise ValueError("Demo walk Y target requires a valid X target and room Y coordinate")
    for cue in room.camera_cues:
        if cue.operation not in ("set", "pan", "wait", "follow_ego"):
            raise ValueError("Unsupported native v6 camera operation")
        if cue.operation in ("set", "pan"):
            if type(cue.x) is not int or not 0 <= cue.x < width:
                raise ValueError("Camera target X must be inside the room")
        elif cue.x is not None:
            raise ValueError("Camera wait/follow must not have an X parameter")
    if room.goal_text is not None:
        _scumm_string(room.goal_text)
    ids: set[str] = set()
    pickups: set[str] = set()
    for hotspot in room.hotspots:
        if not _IDENTIFIER.fullmatch(hotspot.id) or hotspot.id in ids:
            raise ValueError("Invalid or duplicated hotspot identifier")
        ids.add(hotspot.id)
        if hotspot.pickup:
            pickups.add(hotspot.id)
        _scumm_string(hotspot.label)
        _scumm_string(hotspot.description)
        if len(hotspot.talk_lines) > 16:
            raise ValueError("Dialogue exceeds sixteen lines per actor hotspot")
        if hotspot.talk_actor_lines and (len(hotspot.talk_actor_lines) != len(hotspot.talk_lines)
                or any(not isinstance(actor, str) or not _IDENTIFIER.fullmatch(actor)
                       for actor in hotspot.talk_actor_lines)):
            raise ValueError("Linear dialogue Actor bindings must match every spoken line")
        if hotspot.talk_face_directions and (
                len(hotspot.talk_face_directions) != len(hotspot.talk_lines)
                or len(hotspot.talk_actor_lines) != len(hotspot.talk_lines)
                or any(direction not in (None, "N", "E", "S", "W")
                       for direction in hotspot.talk_face_directions)):
            raise ValueError("Linear dialogue facing cues require native Actors and aligned lines")
        for line in hotspot.talk_lines:
            _scumm_string(line)
        if any(type(v) is not int for v in (hotspot.x, hotspot.y, hotspot.width, hotspot.height)):
            raise ValueError("Hotspot coordinates must be integers")
        if (hotspot.x < 0 or hotspot.y < 0 or hotspot.width <= 0 or hotspot.height <= 0
                or hotspot.x + hotspot.width > width or hotspot.y + hotspot.height > height):
            raise ValueError("Hotspot outside room bounds")
        if hotspot.sprite_pixels is not None:
            if hotspot.width % 8 or hotspot.height % 8:
                raise ValueError("SCUMM sprite dimensions must be multiples of eight")
            if hotspot.pickup and (hotspot.width > 40 or hotspot.height > 16):
                raise ValueError("Inventory icon sprite exceeds fixed 40x16 GUI slot")
            if len(hotspot.sprite_pixels) != hotspot.width * hotspot.height:
                raise ValueError("Hotspot sprite pixel buffer length mismatch")
            if hotspot.sprite_pixels and max(hotspot.sprite_pixels) >= len(room.palette):
                raise ValueError("Hotspot sprite references missing palette entries")
        if hotspot.object_zplane_pixels is not None:
            if hotspot.sprite_pixels is None or len(hotspot.object_zplane_pixels) != hotspot.width * hotspot.height:
                raise ValueError("Object Z-mask requires a sprite and exact sprite dimensions")
            if any(pixel not in (0, 1) for pixel in hotspot.object_zplane_pixels):
                raise ValueError("Object Z-mask pixels must be binary")
        if hotspot.open_object_zplane_pixels is not None:
            if hotspot.open_sprite_pixels is None or len(hotspot.open_object_zplane_pixels) != hotspot.width * hotspot.height:
                raise ValueError("Open-state object Z-mask requires an open sprite with exact dimensions")
            if any(pixel not in (0, 1) for pixel in hotspot.open_object_zplane_pixels):
                raise ValueError("Open-state object Z-mask pixels must be binary")
        if hotspot.open_sprite_pixels is not None:
            if hotspot.sprite_pixels is None or len(hotspot.open_sprite_pixels) != hotspot.width * hotspot.height:
                raise ValueError("Open sprite dimensions do not match closed sprite")
            if max(hotspot.open_sprite_pixels) >= len(room.palette):
                raise ValueError("Open sprite references missing palette entries")
        if hotspot.exit_destination is not None:
            if not _IDENTIFIER.fullmatch(hotspot.exit_destination) or hotspot.exit_destination == room.name:
                raise ValueError("Invalid exit destination room")
    used_choices: set[str] = set()
    used_speakers: set[str] = set()
    for dialogue in room.talk_rules:
        if dialogue.speaker_id not in ids or dialogue.speaker_id in used_speakers:
            raise ValueError("Invalid or duplicate dialogue speaker hotspot")
        used_speakers.add(dialogue.speaker_id)
        if (len(dict(dialogue.actor_lines)) != len(dialogue.actor_lines)
                or any(not isinstance(key, str) or not isinstance(actor, str)
                       for key, actor in dialogue.actor_lines)):
            raise ValueError("Duplicate or invalid dialogue actor line binding")
        if (len(dict(dialogue.actor_directions)) != len(dialogue.actor_directions)
                or any(key not in dict(dialogue.actor_lines)
                       or direction not in ("N", "E", "S", "W")
                       for key, direction in dialogue.actor_directions)):
            raise ValueError("Dialogue facing cues require Actor bindings and cardinal directions")
        if not 1 <= len(dialogue.choices) <= 3 or len(dialogue.opening_lines) > 16:
            raise ValueError("Dialogue must offer one to three choices")
        stages = {stage.id: stage for stage in dialogue.stages}
        if (len(stages) != len(dialogue.stages)
                or any(not isinstance(stage.id, str) or not _IDENTIFIER.fullmatch(stage.id)
                       or not 1 <= len(stage.choices) <= 3 or len(stage.opening_lines) > 16
                       for stage in dialogue.stages)):
            raise ValueError("Invalid or duplicate dialogue stage")
        for stage in (dialogue, *dialogue.stages):
            for line in stage.opening_lines:
                _scumm_string(line)
            for choice in stage.choices:
                if (choice.object_id not in ids or choice.object_id in used_choices
                        or choice.object_id == dialogue.speaker_id):
                    raise ValueError("Invalid or reused answer hotspot")
                used_choices.add(choice.object_id)
                _scumm_string(choice.caption)
                if len(choice.reply_lines) > 16:
                    raise ValueError("Dialogue answer exceeds sixteen lines")
                if choice.next_stage_id is not None and choice.next_stage_id != "Entry" and choice.next_stage_id not in stages:
                    raise ValueError("Unknown next dialogue stage")
                for line in choice.reply_lines:
                    _scumm_string(line)
                answer = next(h for h in room.hotspots if h.id == choice.object_id)
                if answer.pickup or answer.exit_destination is not None:
                    raise ValueError("Answer hotspot cannot be a pickup or an exit")
        reachable = {None}
        queue = [None]
        while queue:
            current = queue.pop()
            choices = dialogue.choices if current in (None, "Entry") else stages[current].choices
            for choice in choices:
                target = choice.next_stage_id
                if target == "Entry":
                    continue
                if target is not None and target not in reachable:
                    reachable.add(target)
                    queue.append(target)
        if len(reachable) != len(stages) + 1:
            raise ValueError("Unreachable dialogue stage")
    if any(h.id in used_speakers and h.talk_lines for h in room.hotspots):
        raise ValueError("A character cannot have both linear and branching dialogue")
    # Check cycles after hotspot validation so malformed sprite indices receive
    # their canonical asset error instead of a misleading cycle error.
    protected = {0}
    for hotspot in room.hotspots:
        for sprite in (hotspot.sprite_pixels, hotspot.open_sprite_pixels):
            if sprite is not None:
                protected.update(sprite)
    validate_cycles(room.palette, room.palette_cycles, frozenset(protected))
    if any(c.period_ticks > 16384 or not _IDENTIFIER.fullmatch(c.name)
           for c in room.palette_cycles):
        raise ValueError("SCUMM v6 palette cycle delay or name is invalid")
    if room.music_id is not None and (not isinstance(room.music_id, str)
                                      or not _IDENTIFIER.fullmatch(room.music_id)):
        raise ValueError("Invalid SCUMM music resource ID")
    targets: set[str] = set()
    for rule in room.use_rules:
        if rule.item_id not in pickups or rule.target_id not in ids or rule.item_id == rule.target_id:
            raise ValueError("Use rule must connect an inventory pickup to another room hotspot")
        if rule.target_id in targets:
            raise ValueError("Multiple use rules for the same target are not yet supported")
        targets.add(rule.target_id)
        _scumm_string(rule.response)
        if rule.destination_room is not None and (
            not _IDENTIFIER.fullmatch(rule.destination_room) or rule.destination_room == room.name
        ):
            raise ValueError("Invalid destination room in use rule")
        if rule.open_target and rule.hide_target:
            raise ValueError("Use rule cannot hide and open the same target")
        if type(rule.reversible_walkbox) is not bool:
            raise ValueError("Reversible walkbox flag must be boolean")
        if rule.reversible_walkbox and rule.unlock_walkbox is None:
            raise ValueError("Reversible door requires an authored walkbox gate")
        if rule.unlock_walkbox is not None:
            if (type(rule.unlock_walkbox) is not int or not 1 <= rule.unlock_walkbox <= len(room.walkboxes)):
                raise ValueError("Walkbox unlock must reference an authored native walkbox")
            if not rule.open_target or rule.destination_room is not None or rule.hide_target:
                raise ValueError("Walkbox unlock needs a local open-state door Use action")
            if room.walkboxes[rule.unlock_walkbox - 1].flags & 0xC0:
                raise ValueError("Walkbox unlock requires an initially passable authored box")
        if rule.open_target and next(h for h in room.hotspots if h.id == rule.target_id).open_sprite_pixels is None:
            raise ValueError("Use rule open target needs an open-state sprite")
        if len(set(rule.requires_inventory)) != len(rule.requires_inventory):
            raise ValueError("Duplicate inventory requirements")
        if rule.item_id in rule.requires_inventory or any(item not in pickups for item in rule.requires_inventory):
            raise ValueError("Use rule inventory requirements must reference distinct pickup items")
    results: set[str] = set()
    combination_inputs: set[str] = set()
    for rule in room.combine_rules:
        if (len({rule.first_id, rule.second_id, rule.result_id}) != 3
                or any(item not in pickups for item in (rule.first_id, rule.second_id, rule.result_id))):
            raise ValueError("Combination must reference three distinct room inventory objects")
        if (rule.result_id in results
                or rule.first_id in targets or rule.second_id in targets
                or rule.first_id in combination_inputs or rule.second_id in combination_inputs):
            raise ValueError("Ambiguous combination result or target")
        results.add(rule.result_id)
        combination_inputs.update((rule.first_id, rule.second_id))
        _scumm_string(rule.response)
    # Produced objects may be consumed by later recipes. Reject cycles even
    # when the input order is not the order in which recipes were declared.
    producers = {rule.result_id: rule for rule in room.combine_rules}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(item_id: str) -> None:
        if item_id in visiting:
            raise ValueError("Cyclic inventory combinations are not supported")
        if item_id in visited or item_id not in producers:
            return
        visiting.add(item_id)
        recipe = producers[item_id]
        visit(recipe.first_id)
        visit(recipe.second_id)
        visiting.remove(item_id)
        visited.add(item_id)

    for output_id in producers:
        visit(output_id)


def _indexed_bmp(width: int, height: int, pixels: bytes, palette: tuple[tuple[int, int, int], ...]) -> bytes:
    """Encode validated 8-bit indexed pixels in a bottom-up Windows BMP."""
    stride = (width + 3) & ~3
    pixel_data = b"".join(pixels[y * width:(y + 1) * width] + b"\x00" * (stride - width)
                          for y in range(height - 1, -1, -1))
    palette_data = b"".join(bytes((b, g, r, 0)) for r, g, b in palette)
    offset = 14 + 40 + len(palette_data)
    file_size = offset + len(pixel_data)
    header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, offset)
    info = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 8, 0, len(pixel_data),
                       2835, 2835, len(palette), 0)
    return header + info + palette_data + pixel_data


def _validate_stock_v6_zplanes(room: RoomAsset) -> None:
    """Refuse room masks that stock ScummVM's SCUMM-v6 Gdi cannot decode.

    The authoring model retains up to nine ordered Z-planes for lossless
    editing. The stock-v6 export is narrower: Gdi::getZPlanes() uses fixed
    ZP00..ZP04 tags, so a fifth room plane silently fails to occlude actors.
    Do not mistake ScummC acceptance of ZP05 for runtime compatibility.
    """
    if len(room.zplanes) > 4:
        raise ValueError(
            f"Stock ScummVM SCUMM v6 export: room {room.name} has "
            f"{len(room.zplanes)} Z-planes; only ZP01-ZP04 are supported "
            "(ZP05 and higher do not render actor occlusion). "
            "The Studio project remains editable; reduce room Z-planes "
            "before exporting.")
    for index, box in enumerate(room.walkboxes, start=1):
        if box.mask > 4:
            raise ValueError(
                f"Stock ScummVM SCUMM v6 export: room {room.name}, "
                f"walkbox {index} selects unsupported ZP{box.mask:02}; "
                "only mask indices 0-ZP04 are supported.")


def indexed_bmp(room: RoomAsset) -> bytes:
    """Emit an uncompressed bottom-up Windows BMP with 8-bit indexed pixels."""
    _validate(room)
    return _indexed_bmp(room.geometry.room_width, room.geometry.room_height, room.pixels, room.palette)


def scummc_room_source(room: RoomAsset, catalog=None,
                       graphical_language_buttons: bool = False,
                       dialogue_voice_cues=(), dialogue_animation_cues=()) -> str:
    _validate(room)
    _validate_stock_v6_zplanes(room)
    if graphical_language_buttons and catalog is None:
        raise ValueError("Graphical language buttons require a language catalog")
    if graphical_language_buttons:
        from .scumm_language_buttons import button_room_source, button_state_source
        from .scumm_language_buttons import button_names
        occupied = {hotspot.id for hotspot in room.hotspots}
        if occupied.intersection(name for name, _lang, _code in button_names(catalog)):
            raise ValueError("Language button object ID collides with a room hotspot")
    if catalog is not None:
        from .localization import scumm_language_dispatch, validate_catalog
        validate_catalog(catalog)
        translations = {line.id: dict(line.translations) for line in catalog.lines}
    cues = {cue.line_id: cue for cue in dialogue_voice_cues}
    # Legacy source callers pass four fields; persisted cues additionally
    # provide the authored native pre-gesture and minimum gesture delays.
    animation_cues = {}
    for binding in dialogue_animation_cues:
        if len(binding) == 4:
            line_id, actor_id, index, stand_index = binding
            start_ticks, minimum_ticks = 1, 60
            ending_index, ending_ticks = None, 0
        elif len(binding) == 6:
            line_id, actor_id, index, stand_index, start_ticks, minimum_ticks = binding
            ending_index, ending_ticks = None, 0
        elif len(binding) == 8:
            (line_id, actor_id, index, stand_index, start_ticks, minimum_ticks,
             ending_index, ending_ticks) = binding
        else:
            raise ValueError("Invalid native dialogue animation binding")
        animation_cues[line_id] = (actor_id, index, stand_index, start_ticks, minimum_ticks,
                                   ending_index, ending_ticks)
    line_actors = {key: actor for rule in room.talk_rules for key, actor in rule.actor_lines}
    line_directions = {key: direction for rule in room.talk_rules
                       for key, direction in rule.actor_directions}
    for hotspot in room.hotspots:
        for index, actor in enumerate(hotspot.talk_actor_lines):
            key = f"room.{room.name.lower()}.object.{hotspot.id.lower()}.talk.{index}"
            line_actors[key] = actor
            if hotspot.talk_face_directions and hotspot.talk_face_directions[index] is not None:
                line_directions[key] = hotspot.talk_face_directions[index]

    def say(key: str, original: str, indent: int) -> str:
        actor = line_actors.get(key)
        if catalog is None:
            call = (f"actorSay({actor},{_scumm_string(original)})" if actor else
                    f"egoSay({_scumm_string(original)})")
            return " " * indent + call + ";\n"
        entry = translations.get(key)
        from .story_localization import source_matches_compiled
        if entry is None or not source_matches_compiled(entry.get(catalog.source_language, ""), original):
            raise ValueError(f"Missing or stale SCUMM translation: {key}")
        dispatch = scumm_language_dispatch(catalog, key)
        if actor:
            dispatch = dispatch.replace("egoSay(", f"actorSay({actor},")
        return "".join(" " * indent + line + "\n" for line in dispatch.splitlines())

    def spoken(key: str, original: str, indent: int) -> str:
        animation = animation_cues.get(key)
        # The native talk-start (16) and talk-stop (20) COST slots are
        # selected by the engine during actorSay. Overriding the actor's
        # talk frames here prevents that automatic speaking pose.
        animate = ((" " * indent + f"delay({animation[3]});\n" if animation[3] else "")
                   + " " * indent + f"animateActor({animation[0]},{animation[1]});\n"
                   + (" " * indent + f"delay({animation[4]});\n" if animation[4] else "")
                   if animation is not None else "")
        standing = (" " * indent + f"setCurrentActor({animation[0]});\n"
                    + " " * indent + "setActorStanding();\n"
                    + " " * indent + "setActorTalkFrame(4,5);\n"
                    + " " * indent + "setCurrentActor(VAR_EGO);\n"
                    + " " * indent + f"animateActor({animation[0]},{animation[2]});\n"
                    if animation is not None and animation[2] is not None else "")
        closing = (" " * indent + f"animateActor({animation[0]},{animation[5]});\n"
                   + " " * indent + f"delay({animation[6]});\n"
                   if animation is not None and animation[5] is not None else "")
        direction = line_directions.get(key)
        face = ""
        if direction is not None:
            actor = line_actors[key]
            native = actor_facing_angle(direction)
            pad = " " * indent
            face = (f"{pad}setCurrentActor({actor});\n"
                    f"{pad}setActorDirection({native});\n"
                    f"{pad}setCurrentActor(VAR_EGO);\n")
        cue = cues.get(key)
        if cue is None:
            return (face + say(key, original, indent) + animate
                    + " " * indent + "waitForMessage();\n" + closing + standing)
        if cue.source_text != original:
            raise ValueError(f"Stale dialogue audio line: {key}")
        pad = " " * indent

        def sound(operation: str) -> str:
            if not cue.variants:
                return f"{pad}{operation}({cue.sound_id});\n"
            branches = []
            for index, (language, sound_id) in enumerate(cue.variants):
                code = int.from_bytes(language.encode("ascii"), "big")
                keyword = "if" if index == 0 else "else if"
                branches.append(f"{pad}{keyword}(GameLanguage == {code}) "
                                f"{operation}({sound_id});\n")
            branches.append(f"{pad}else {operation}({cue.sound_id});\n")
            return "".join(branches)

        stops = "".join(f"{pad}stopSound({sound_id});\n" for sound_id in sorted(
            {cue.sound_id, *(variant[1] for variant in cue.variants)}))
        return face + sound("startSound") + say(key, original, indent) + animate + \
            f"{pad}waitForMessage();\n" + stops + closing + standing
    def localized_name(hotspot: RoomHotspot) -> str:
        if catalog is None:
            return ""
        from .localization import charset_plan, encode_scumm_literal
        key = f"room.{room.name.lower()}.object.{hotspot.id.lower()}.label"
        entry = translations.get(key)
        from .story_localization import source_matches_compiled
        if entry is None or not source_matches_compiled(entry.get(catalog.source_language, ""), hotspot.label):
            raise ValueError(f"Missing or stale SCUMM translation: {key}")
        plan = charset_plan(catalog)
        branches = []
        for index, language in enumerate(catalog.languages):
            code = int.from_bytes(language.encode("ascii"), "big")
            keyword = "if" if index == 0 else "else if"
            literal = encode_scumm_literal(entry[language], plan)
            branches.append(f"        {keyword} (GameLanguage == {code}) "
                            f"setObjectName({hotspot.id},{literal});\n")
        fallback = encode_scumm_literal(entry[catalog.source_language], plan)
        branches.append(f"        else setObjectName({hotspot.id},{fallback});\n")
        return "".join(branches)

    # The external test bootstrap provides verbs, actor and UI. A generated
    # room always owns its own entry script, even when it has no hotspots.
    parts = ["#include <scummVars6.s>\n", '#include "common.sch"\n']
    destinations = ({r.destination_room for r in room.use_rules if r.destination_room}
                    | {h.exit_destination for h in room.hotspots if h.exit_destination})
    for destination in sorted(destinations):
        parts.append(f"room {destination};\n")
    parts.append(f'\nroom {room.name} {{\n    image = "{room.name}.bmp";\n')
    if room.zplanes:
        planes = ", ".join(f'"{room.name}Z{plane.index:02}.bmp"' for plane in room.zplanes)
        parts.append(f"    zplane = {{ {planes} }};\n")
    if room.walkboxes:
        parts.append(f'    boxd = "{room.name}.box";\n')
    if room.music_id is not None:
        parts.append(f'    sound {room.music_id} = "{room.music_id}.soun";\n')
    for sound_id in sorted({sid for cue in cues.values()
                            for sid in (cue.sound_id, *(variant[1] for variant in cue.variants))}):
        parts.append(f'    sound {sound_id} = "{sound_id}.soun";\n')
    for cycle in room.palette_cycles:
        # ScummC scc_parse.y: cycle name = {delay, flags, start, end};
        # flags bit 1 reverses the direction of palette cycling.
        parts.append(f"    cycle {cycle.name} = {{{cycle.period_ticks},"
                     f"{2 if cycle.reverse else 0},{cycle.first},{cycle.last}}};\n")
    hidden = {rule.result_id for rule in room.combine_rules}
    hidden.update(choice.object_id for rule in room.talk_rules
                  for stage in (rule, *rule.stages) for choice in stage.choices)
    # ScummC resolves object symbols as it parses each script body. Explicit
    # forward declarations keep the generated helper independent of object
    # layout order (the complete object definitions follow below).
    for item_id in sorted({item for rule in room.combine_rules
                           for item in (rule.first_id, rule.second_id, rule.result_id)}):
        parts.append(f"    object {item_id};\n")
    for item_id in sorted({choice.object_id for rule in room.talk_rules
                           for stage in (rule, *rule.stages) for choice in stage.choices}):
        parts.append(f"    object {item_id};\n")
    for index, rule in enumerate(room.combine_rules):
        parts.extend([
            f"    script combine_{index}() {{\n",
            say(f"room.{room.name.lower()}.combine.{index}.response", rule.response, 8),
            f"        setObjectOwner({rule.first_id}, 0);\n",
            f"        setObjectOwner({rule.second_id}, 0);\n",
            f"        pickupObject({rule.result_id}, VAR_ROOM);\n",
            f"        setObjectState({rule.result_id}, 1);\n",
            "    }\n",
        ])
    for hotspot in room.hotspots:
        speaker_rule = next((r for r in room.talk_rules if r.speaker_id == hotspot.id), None)
        answer_pair = next(((r, stage, c) for r in room.talk_rules
                            for stage in (r, *r.stages) for c in stage.choices
                            if c.object_id == hotspot.id), None)
        parts.extend([
            f"    object {hotspot.id} {{\n",
            f"        x = {hotspot.x};\n        y = {hotspot.y};\n",
            f"        w = {hotspot.width};\n        h = {hotspot.height};\n",
            f"        name = {_scumm_string(hotspot.label)};\n",
        ])
        if hotspot.sprite_pixels is not None:
            if hotspot.open_sprite_pixels is None:
                if hotspot.object_zplane_pixels is None:
                    parts.append(f'        states = {{ {{ 0, 0, "{hotspot.id}.bmp" }} }};\n')
                else:
                    parts.append(f'        states = {{ {{ 0, 0, "{hotspot.id}.bmp", {{ "{hotspot.id}Z01.bmp" }} }} }};\n')
            else:
                first = (f'{{ 0, 0, "{hotspot.id}.bmp", {{ "{hotspot.id}Z01.bmp" }} }}'
                         if hotspot.object_zplane_pixels is not None
                         else f'{{ 0, 0, "{hotspot.id}.bmp" }}')
                second = (f'{{ 0, 0, "{hotspot.id}Open.bmp", {{ "{hotspot.id}OpenZ01.bmp" }} }}'
                          if hotspot.open_object_zplane_pixels is not None
                          else f'{{ 0, 0, "{hotspot.id}Open.bmp" }}')
                parts.append(f'        states = {{ {first}, {second} }};\n')
            parts.append("        state = 0;\n" if hotspot.id in hidden else "        state = 1;\n")
        if hotspot.pickup:
            parts.append("        class = { Pickable };\n")
        parts.extend([
            "        verb(int vrb, int objA, int objB) {\n",
            "        case LookAt:\n" + say(f"room.{room.name.lower()}.object.{hotspot.id.lower()}.description", hotspot.description, 12) + "            return;\n",
        ])
        if hotspot.talk_lines:
            parts.append("        case TalkTo:\n")
            for line_index, line in enumerate(hotspot.talk_lines):
                parts.append(spoken(f"room.{room.name.lower()}.object.{hotspot.id.lower()}.talk.{line_index}", line, 12))
            parts.append("            return;\n")
        if speaker_rule:
            parts.append("        case TalkTo:\n")
            for stage in (speaker_rule, *speaker_rule.stages):
                for choice in stage.choices:
                    parts.append(f"            setObjectState({choice.object_id},0);\n")
            for line_index, line in enumerate(speaker_rule.opening_lines):
                parts.append(spoken(f"room.{room.name.lower()}.dialogue.{room.talk_rules.index(speaker_rule)}.opening.{line_index}", line, 12))
            for choice in speaker_rule.choices:
                parts.append(f"            setObjectState({choice.object_id},1);\n")
            parts.append("            return;\n")
        if answer_pair:
            rule, stage, selected = answer_pair
            parts.append("        case TalkTo:\n")
            for group in (rule, *rule.stages):
                for choice in group.choices:
                    parts.append(f"            setObjectState({choice.object_id},0);\n")
            base = f"room.{room.name.lower()}.dialogue.{room.talk_rules.index(rule)}"
            prefix = (base if stage is rule else
                      f"{base}.stage.{rule.stages.index(stage)}")
            selected_index = stage.choices.index(selected)
            parts.extend([say(f"{prefix}.choice.{selected_index}.caption", selected.caption, 12),
                          "            waitForMessage();\n"])
            for line_index, line in enumerate(selected.reply_lines):
                parts.append(spoken(f"{prefix}.choice.{selected_index}.reply.{line_index}", line, 12))
            if selected.next_stage_id is not None:
                # Redraws during spoken replies can leave an old choice
                # sprite visible in the SCUMM object layer. Invalidate the
                # previous menu again at the exact stage transition.
                for group in (rule, *rule.stages):
                    for choice in group.choices:
                        parts.append(f"            setObjectState({choice.object_id},0);\n")
                next_stage = (rule if selected.next_stage_id == "Entry" else
                              next(item for item in rule.stages if item.id == selected.next_stage_id))
                next_prefix = (base if next_stage is rule else
                               f"{base}.stage.{rule.stages.index(next_stage)}")
                for line_index, line in enumerate(next_stage.opening_lines):
                    parts.append(spoken(f"{next_prefix}.opening.{line_index}", line, 12))
                for choice in next_stage.choices:
                    parts.append(f"            setObjectState({choice.object_id},1);\n")
            parts.append("            return;\n")
        if hotspot.exit_destination is not None:
            parts.append("        case WalkTo:\n")
            if hotspot.open_sprite_pixels is not None:
                parts.extend(["            if(getObjectState(objA) == 2) {\n",
                              f"                startRoom({hotspot.exit_destination});\n",
                              "            } else {\n",
                              say(f"room.{room.name.lower()}.object.{hotspot.id.lower()}.locked", "The door is locked.", 16),
                              "            }\n"])
            else:
                parts.append(f"            startRoom({hotspot.exit_destination});\n")
            parts.append("            return;\n")
        if hotspot.pickup:
            if (any(rule.item_id == hotspot.id for rule in room.use_rules)
                    or any(hotspot.id in (rule.first_id, rule.second_id)
                           for rule in room.combine_rules)):
                parts.extend(["        case Preposition:\n",
                              '            sntcPrepo[0] = "with";\n',
                              "            return;\n"])
            parts.extend(["        case PickUp:\n", "            pickupObject(objA,VAR_ROOM);\n",
                          "            setObjectState(objA,0);\n",
                          "            return;\n"])
            if hotspot.sprite_pixels is not None:
                parts.extend(["        case Icon:\n",
                              f"            startScript2(vrb,[ResRoom::{hotspot.id}Icon,objA,objB]);\n",
                              "            return;\n"])
        for rule in room.use_rules:
            if rule.target_id == hotspot.id:
                requirements = "".join(
                    f" && getObjectOwner({item}) == VAR_EGO" for item in rule.requires_inventory
                )
                parts.extend([
                    "        case Use:\n",
                    f"            if(objB == {rule.item_id}{requirements}) {{\n",
                    say(f"room.{room.name.lower()}.use.{room.use_rules.index(rule)}.response", rule.response, 16),
                ])
                if rule.hide_target:
                    parts.append("                setObjectState(objA,0);\n")
                if rule.reversible_walkbox:
                    parts.extend([
                        "                if(getObjectState(objA) == 2) {\n",
                        "                    setObjectState(objA,1);\n",
                        f"                    setBoxFlags([{rule.unlock_walkbox}],128);\n",
                        "                } else {\n",
                        "                    setObjectState(objA,2);\n",
                        f"                    setBoxFlags([{rule.unlock_walkbox}],0);\n",
                        "                }\n",
                        "                createBoxMatrix();\n",
                    ])
                else:
                    if rule.open_target:
                        parts.append("                setObjectState(objA,2);\n")
                    if rule.unlock_walkbox is not None:
                        parts.append(f"                setBoxFlags([{rule.unlock_walkbox}],0);\n")
                        parts.append("                createBoxMatrix();\n")
                if rule.destination_room:
                    parts.append(f"                startRoom({rule.destination_room});\n")
                parts.extend(["                return;\n", "            }\n", "            return;\n"])
        for index, rule in enumerate(room.combine_rules):
            if hotspot.id in (rule.first_id, rule.second_id):
                other_id = (rule.first_id if hotspot.id == rule.second_id
                            else rule.second_id)
                parts.extend([
                    "        case Use:\n",
                    f"            if(objB == {other_id} && getObjectOwner({rule.first_id}) == VAR_EGO",
                    f" && getObjectOwner({rule.second_id}) == VAR_EGO) {{\n",
                    f"                combine_{index}();\n",
                    "                return;\n",
                    "            }\n            return;\n",
                ])
        parts.append("        }\n    }\n")
    if graphical_language_buttons:
        parts.append(button_room_source(room.name, catalog))
    # ScummC resolves object symbols before script bodies: place the watcher
    # after all object declarations, not before them. It refreshes cached
    # labels when the language changes within a loaded room.
    if catalog is not None and (room.hotspots or graphical_language_buttons):
        parts.extend([
            "    local script watchLanguage() {\n",
            "        int observedLanguage;\n",
            "        observedLanguage = GameLanguage;\n",
            "        while(1) {\n",
            "            if(observedLanguage != GameLanguage) {\n",
            "                observedLanguage = GameLanguage;\n",
            *[localized_name(hotspot) for hotspot in room.hotspots],
            *([button_state_source(catalog, 16)] if graphical_language_buttons else []),
            "            }\n",
            "            breakScript();\n",
            "        }\n",
            "    }\n",
        ])
    parts.extend([
        "    local script entry() {\n",
        "        setCurrentActor(VAR_EGO);\n",
        f"        putActorAt(VAR_EGO, 60, 100, {room.name});\n",
        "        setActorFollowBoxes();\n" if room.walkboxes else "        setActorIgnoreBoxes();\n",
        "        setActorStanding();\n",
        *[f"        if(getObjectState({rule.target_id}) == 2) setBoxFlags([{rule.unlock_walkbox}],0);\n"
          f"        else setBoxFlags([{rule.unlock_walkbox}],128);\n" for rule in room.use_rules
          if rule.unlock_walkbox is not None],
        *(["        createBoxMatrix();\n"] if any(rule.unlock_walkbox is not None
                                                  for rule in room.use_rules) else []),
        *(["        cameraFollowActor(VAR_EGO);\n"] if not room.camera_cues else []),
        *[{
            "set": lambda cue: f"        setCameraAt({cue.x});\n",
            "pan": lambda cue: f"        panCameraTo({cue.x});\n",
            "wait": lambda cue: "        waitForCamera();\n",
            "follow_ego": lambda cue: "        cameraFollowActor(VAR_EGO);\n",
        }[cue.operation](cue) for cue in room.camera_cues],
        *[localized_name(hotspot) for hotspot in room.hotspots],
        *([button_state_source(catalog)] if graphical_language_buttons else []),
        *(["        watchLanguage();\n"] if catalog is not None and
          (room.hotspots or graphical_language_buttons) else []),
        "        ResRoom::showVerbs(1);\n",
        "        ResRoom::showCursor();\n",
    ])
    if room.music_id is not None:
        parts.append(f"        startMusic({room.music_id});\n")
    if room.demo_walk_to_x is not None:
        target_y = room.demo_walk_to_y if room.demo_walk_to_y is not None else 100
        parts.append(f"        walkActorTo(VAR_EGO, {room.demo_walk_to_x}, {target_y});\n")
    if room.goal_text is not None:
        parts.append(say(f"room.{room.name.lower()}.goal", room.goal_text, 8))
    parts.append("    }\n")
    parts.append("}\n")
    return "".join(parts)


def write_room_sources(room: RoomAsset, directory: Path) -> tuple[Path, Path]:
    """Write independent ScummC room inputs, never claim a linked game."""
    binary = indexed_bmp(room)
    source = scummc_room_source(room)
    directory.mkdir(parents=True, exist_ok=True)
    bmp = directory / f"{room.name}.bmp"
    scc = directory / f"{room.name}.scc"
    bmp.write_bytes(binary)
    scc.write_text(source, encoding="utf-8")
    for plane in room.zplanes:
        (directory / f"{room.name}Z{plane.index:02}.bmp").write_bytes(
            _indexed_bmp(room.geometry.room_width, room.geometry.room_height,
                         plane.pixels, ((0, 0, 0), (255, 255, 255)))
        )
    if room.walkboxes:
        (directory / f"{room.name}.box").write_bytes(_native_box_file(room))
    for hotspot in room.hotspots:
        if hotspot.sprite_pixels is not None:
            if hotspot.object_zplane_pixels is not None:
                (directory / f"{hotspot.id}Z01.bmp").write_bytes(
                    _indexed_bmp(hotspot.width, hotspot.height, hotspot.object_zplane_pixels,
                                 ((0, 0, 0), (255, 255, 255))))
            (directory / f"{hotspot.id}.bmp").write_bytes(
                _indexed_bmp(hotspot.width, hotspot.height, hotspot.sprite_pixels, room.palette)
            )
            if hotspot.open_object_zplane_pixels is not None:
                (directory / f"{hotspot.id}OpenZ01.bmp").write_bytes(
                    _indexed_bmp(hotspot.width, hotspot.height, hotspot.open_object_zplane_pixels,
                                 ((0, 0, 0), (255, 255, 255))))
            if hotspot.open_sprite_pixels is not None:
                (directory / f"{hotspot.id}Open.bmp").write_bytes(
                    _indexed_bmp(hotspot.width, hotspot.height, hotspot.open_sprite_pixels, room.palette)
                )
            if hotspot.pickup:
                # The inherited SCUMM verb UI allocates 40x16 pixels per item.
                # Use the same source sprite, centered on a GUI-blue backdrop.
                icon_width, icon_height = 40, 16
                x_offset = (icon_width - hotspot.width) // 2
                icon_pixels = bytearray(icon_width * icon_height)
                for y in range(hotspot.height):
                    start = y * icon_width + x_offset
                    icon_pixels[start:start + hotspot.width] = hotspot.sprite_pixels[y * hotspot.width:(y + 1) * hotspot.width]
                (directory / f"Inv_{hotspot.id}.bmp").write_bytes(
                    _indexed_bmp(icon_width, icon_height, bytes(icon_pixels), room.palette)
                )
    return bmp, scc


def _chunk(tag: bytes, payload: bytes) -> bytes:
    return tag + struct.pack(">I", len(payload) + 8) + payload


def _native_box_file(room: RoomAsset) -> bytes:
    """ScummC scc_roobj_set_boxd input: named `boxd` plus BOXM and SCAL.

    The lowercase `boxd` format contains name-prefixed entries; ScummC adds
    reserved box zero itself and then reads BOXM and SCAL from the same file.
    The uppercase `BOXD` input form does *not* load these trailing chunks.
    Each BOXM row is run-length encoded as
    (first destination, last destination, next-hop) triples, 0xff terminated.
    """
    _validate(room)
    _validate_stock_v6_zplanes(room)
    boxes = bytearray()
    for box in room.walkboxes:
        coordinates = [number for point in box.corners for number in point]
        boxes.append(0)  # empty name; named box format still uses a length byte
        native_scale = (0x8000 | (box.scale_slot - 1)) if box.scale_slot is not None else box.scale
        boxes.extend(struct.pack("<8hBBH", *coordinates, box.mask, box.flags, native_scale))
    boxd = _chunk(b"boxd", bytes(boxes))
    if room.box_routes:
        routes = room.box_routes
    else:
        # Default is conservative: each box may stay within itself, with no
        # inferred connection to any other geometry.
        count = len(room.walkboxes) + 1
        routes = tuple(tuple(i if i == j else None for j in range(count)) for i in range(count))
    matrix = bytearray()
    for row in routes:
        index = 0
        while index < len(row):
            destination = row[index]
            if destination is None:
                index += 1
                continue
            last = index
            while last + 1 < len(row) and row[last + 1] == destination:
                last += 1
            matrix.extend((index, last, destination))
            index = last + 1
        matrix.append(255)
    if room.scale_curves:
        fields = bytearray(32)
        for curve in room.scale_curves:
            struct.pack_into("<HHHH", fields, (curve.slot - 1) * 8,
                             curve.scale1, curve.y1, curve.scale2, curve.y2)
        scal = bytes(fields)
    else:
        scal = room.scale_slots if room.scale_slots is not None else bytes(32)
    return boxd + _chunk(b"BOXM", bytes(matrix)) + _chunk(b"SCAL", scal)


def write_game_sources(rooms: tuple[RoomAsset, ...], directory: Path) -> tuple[tuple[Path, Path], ...]:
    """Validate all destinations before writing any linked-room source files."""
    if not rooms:
        raise ValueError("A game must contain at least one room")
    names = [room.name for room in rooms]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate room name")
    for room in rooms:
        _validate(room)
        _validate_stock_v6_zplanes(room)
        for rule in room.use_rules:
            if rule.destination_room is not None and rule.destination_room not in names:
                raise ValueError(f"Unknown destination room: {rule.destination_room}")
        for hotspot in room.hotspots:
            if hotspot.exit_destination is not None and hotspot.exit_destination not in names:
                raise ValueError(f"Unknown exit destination room: {hotspot.exit_destination}")
    if sum(room.goal_text is not None for room in rooms) != 1:
        raise ValueError("A game needs exactly one goal room")
    pickup_ids = [h.id for room in rooms for h in room.hotspots if h.pickup]
    if len(pickup_ids) != len(set(pickup_ids)):
        raise ValueError("Duplicate global inventory identifier")
    generated = tuple(write_room_sources(room, directory) for room in rooms)
    goal_room = next(room for room in rooms if room.goal_text is not None)
    # Synthetic CI fixture only: the goal room fills its background uniformly,
    # so the known screen probe color demonstrates the actual destination.
    probe_rgb = goal_room.palette[goal_room.pixels[0]]
    # Fixture-only runtime assertions: every additional inventory prerequisite
    # must be acquired before the use rule can open its target. The palette
    # colors identify sprites in screenshots without knowing story item names.
    gates = []
    fixture_combinations = []
    fixture_route = []
    fixture_rooms = {}
    for room in rooms:
        fixture_rooms[room.name] = {
            "width": room.geometry.room_width,
            "viewport_width": room.geometry.viewport_width,
        }
        pickups = {hotspot.id: hotspot for hotspot in room.hotspots if hotspot.pickup}
        for rule in room.combine_rules:
            fixture_combinations.append({"room_id": room.name,
                "ingredients": [{"item_id": item_id,
                                 "rgb": list(room.palette[pickups[item_id].sprite_pixels[0]]),
                                 "world_x": pickups[item_id].x, "world_y": pickups[item_id].y}
                                for item_id in (rule.first_id, rule.second_id)],
                "result": {"item_id": rule.result_id,
                           "rgb": list(room.palette[pickups[rule.result_id].sprite_pixels[0]]),
                           "world_x": pickups[rule.result_id].x,
                           "world_y": pickups[rule.result_id].y}})
        for rule in room.use_rules:
            source = pickups[rule.item_id]
            assert source.sprite_pixels is not None
            destination = next(h.exit_destination for h in room.hotspots if h.id == rule.target_id)
            fixture_route.append({"room_id": room.name, "item_id": rule.item_id,
                                  "rgb": list(room.palette[source.sprite_pixels[0]]),
                                  "next_room_id": destination})
            for item_id in rule.requires_inventory:
                hotspot = pickups[item_id]
                assert hotspot.sprite_pixels is not None
                color_index = hotspot.sprite_pixels[0]
                gates.append({"item_id": item_id, "rgb": list(room.palette[color_index])})
    (directory / "game-goal.json").write_text(
        json.dumps({"condition": "enter_room", "room_id": goal_room.name,
                    "description": goal_room.goal_text,
                    "fixture_probe_rgb": probe_rgb,
                    "fixture_room_geometry": fixture_rooms,
                    "fixture_inventory_gates": gates,
                    "fixture_combinations": fixture_combinations,
                    "fixture_route": fixture_route}, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (directory / "inventory-ids.txt").write_text(",".join(sorted(pickup_ids)) + "\n", encoding="ascii")
    return generated


def scrolling_fixture() -> RoomAsset:
    """A synthetic two-screen-wide room with distinct left/right regions."""
    width, height = 640, 200
    pixels = bytes(1 if y >= 150 else (2 if x >= 320 else 0)
                   for y in range(height) for x in range(width))
    # An 8-bit golden key silhouette, with orange sky matching its room area.
    key = bytes(3 if (2 <= y <= 4 and 1 <= x <= 5) or (y == 3 and 5 <= x <= 14)
                or (x in (11, 14) and y in (4, 5)) else 2
                for y in range(16) for x in range(16))
    door = bytes(4 if x in (0, 15) or y in (0, 15) else 1
                 for y in range(16) for x in range(16))
    open_door = bytes(5 if x in (0, 15) or y in (0, 15) else 2
                      for y in range(16) for x in range(16))
    return RoomAsset("Harbor", RoomGeometry(width, height, 320, 200), pixels,
                     ((70, 130, 190), (95, 60, 35), (240, 175, 95), (255, 220, 75),
                      (60, 220, 90), (50, 220, 220)),
                     (RoomHotspot("Key", "the key", "A rusty key.", 355, 100, 16, 16, True, key),
                      RoomHotspot("Door", "the door", "A locked door.", 450, 100, 16, 16, False, door,
                                  open_sprite_pixels=open_door, exit_destination="Cellar")),
                     demo_walk_to_x=540,
                     use_rules=(UseRule("Key", "Door", "The door is unlocked.",
                                        open_target=True),))


def destination_fixture() -> RoomAsset:
    """The second room verifies a real engine transition after the puzzle."""
    width, height = 320, 200
    palette = ((70, 130, 190), (95, 60, 35), (240, 175, 95), (255, 220, 75),
               (60, 220, 90), (120, 70, 180))
    stairs = bytes(4 if x in (0, 15) or y in (0, 15) else 1
                   for y in range(16) for x in range(16))
    return RoomAsset("Cellar", RoomGeometry(width, height, 320, 200), bytes([5]) * (width * height), palette,
                     hotspots=(RoomHotspot("Stairs", "stairs to the harbor", "The way back.",
                                           125, 100, 16, 16, sprite_pixels=stairs,
                                           exit_destination="Harbor"),),
                     goal_text="You reached the cellar. Puzzle solved!")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m adventure_studio.scumm_assets OUTPUT_DIRECTORY")
        return 2
    for generated in write_game_sources((scrolling_fixture(), destination_fixture()), Path(sys.argv[1])):
        for path in generated:
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

