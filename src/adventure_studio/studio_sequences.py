"""Author ordered native SCUMM interactions without editing project JSON by hand."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha1
from math import isfinite
from pathlib import Path
import re
import tempfile
import unicodedata

from .scumm_project import (AnimateActorStep, DelayStep, MoveActorStep, WalkActorStep, WaitActorStep,
                            FaceActorStep, GameDocument,
                            InteractionSequence, ObjectStateStep, PickupObjectStep,
                            CombineInventoryStep, ChangeRoomStep, MusicCueStep, MusicAsset,
                            SoundAsset, SoundEffectStep, VoiceLineStep, VoiceVariant,
                            DialogueVoiceCue, DialogueAnimationCue,
                            SpeakingSequenceTemplate,
                            canonical_json, parse_document)
from .story_document import parse_story_document
from .story_to_scumm import compile_story_to_scumm
from .studio_actors import (add_costume_frame, set_costume_speaking_pose, render_costume_frame,
                            costume_timeline_images, render_costume_preview,
                            render_costume_frame_sequence_preview)
from .scumm_costume import CostumeAnimation, CostumeDirection
from .scumm_assets import ScaleCurve, Walkbox, ZPlane


VERBS = ("Push", "Pull", "Open", "Close")


def author_room_walkbox(raw: str, room_name: str, index: int, corners_text: str) -> str:
    """Create or replace one convex native walkbox without inventing box routes."""
    document = parse_document(raw)
    room = next((room for room in document.rooms if room.name == room_name), None)
    if room is None:
        raise ValueError("Bitte einen vorhandenen Raum wählen")
    if type(index) is not int or not 1 <= index <= 254:
        raise ValueError("Walkbox-Nummer muss zwischen 1 und 254 liegen")
    if index > len(room.walkboxes) + 1:
        raise ValueError("Walkboxen müssen lückenlos ab 1 angelegt werden")
    parts = [part.strip() for part in corners_text.split(";")]
    if len(parts) != 4:
        raise ValueError("Vier Eckpunkte in der Reihenfolge UL;UR;LR;LL erforderlich")
    points = []
    for part in parts:
        if not re.fullmatch(r"\d+\s*,\s*\d+", part):
            raise ValueError("Eckpunkte als x,y; x,y; x,y; x,y eingeben")
        points.append(tuple(int(value.strip()) for value in part.split(",")))
    width, height = room.geometry.room_width, room.geometry.room_height
    if any(not 0 <= x < width or not 0 <= y < height for x, y in points):
        raise ValueError(f"Walkbox-Eckpunkte müssen innerhalb {width} × {height} liegen")
    turns = []
    for i in range(4):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % 4]
        x3, y3 = points[(i + 2) % 4]
        turns.append((x2 - x1) * (y3 - y2) - (y2 - y1) * (x3 - x2))
    if any(turn <= 0 for turn in turns):
        raise ValueError("Walkbox muss ein nicht entartetes, konvexes Polygon in UL/UR/LR/LL-Reihenfolge sein")
    boxes = list(room.walkboxes)
    if index <= len(boxes):
        boxes[index - 1] = replace(boxes[index - 1], corners=tuple(points))
    else:
        boxes.append(Walkbox(tuple(points)))
    routes = room.box_routes
    if len(boxes) > len(room.walkboxes) and routes:
        # Newly appended box starts isolated; existing paths remain unchanged.
        # BOXM edges are only recomputed after explicit connection authoring.
        new_index = len(boxes)
        routes = tuple(tuple(row) + (None,) for row in routes) + (
            tuple([None] * new_index + [new_index]),)
    rooms = tuple(replace(item, walkboxes=tuple(boxes), box_routes=routes)
                  if item.name == room_name else item for item in document.rooms)
    return _checked(replace(document, rooms=rooms))




def author_room_walkbox_zplane(raw: str, room_name: str, box_index: int, zplane_index: int) -> str:
    """Assign a native room ZPxx layer to an existing walkbox, without changing routes."""
    if type(reversible) is not bool:
        raise ValueError("Reversibles Tür-Gate muss ein Wahrheitswert sein")
    document = parse_document(raw)
    room = next((item for item in document.rooms if item.name == room_name), None)
    if room is None:
        raise ValueError("Bitte einen vorhandenen Raum wählen")
    if type(box_index) is not int or not 1 <= box_index <= len(room.walkboxes):
        raise ValueError("Eine vorhandene Walkbox-Nummer wählen")
    if type(zplane_index) is not int or not 0 <= zplane_index <= len(room.zplanes):
        raise ValueError("Z-Ebene muss 0 oder eine vorhandene PNG-Z-Maske sein")
    boxes = list(room.walkboxes)
    boxes[box_index - 1] = replace(boxes[box_index - 1], mask=zplane_index)
    rooms = tuple(replace(item, walkboxes=tuple(boxes)) if item.name == room_name else item
                  for item in document.rooms)
    return _checked(replace(document, rooms=rooms))



def author_room_walkbox_gate(raw: str, room_name: str, door_id: str,
                             box_index: int, reversible: bool = False) -> str:
    """Attach a real SCUMM-v6 box unlock to an existing authored door Use rule.

    This is a persistent rule parameter, never user-supplied script source.
    The door's existing successful inventory Use action changes the box state.
    """
    document = parse_document(raw)
    room = next((item for item in document.rooms if item.name == room_name), None)
    if room is None:
        raise ValueError("Bitte einen vorhandenen Raum wählen")
    if type(box_index) is not int or not 1 <= box_index <= len(room.walkboxes):
        raise ValueError("Eine vorhandene Walkbox-Nummer wählen")
    matching = [rule for rule in room.use_rules if rule.target_id == door_id]
    if len(matching) != 1 or not matching[0].open_target:
        raise ValueError("Tür benötigt eine bestehende Use-Regel mit Open-State")
    if any(rule.unlock_walkbox == box_index and rule.target_id != door_id
           for rule in room.use_rules):
        raise ValueError("Walkbox ist bereits einer anderen Tür zugeordnet")
    rules = tuple(replace(rule, unlock_walkbox=box_index,
                          reversible_walkbox=reversible)
                  if rule.target_id == door_id else rule for rule in room.use_rules)
    rooms = tuple(replace(item, use_rules=rules) if item.name == room_name else item
                  for item in document.rooms)
    return _checked(replace(document, rooms=rooms))


def author_room_box_connections(raw: str, room_name: str, connections: str) -> str:
    """Author touching box links and deterministic shortest-hop native BOXM routes.

    A link '1-2' is bidirectional. Empty input explicitly disconnects all
    boxes. The reserved native box zero remains inaccessible. Each route
    destination stores the immediate next box, not the final destination.
    """
    document = parse_document(raw)
    room = next((item for item in document.rooms if item.name == room_name), None)
    if room is None:
        raise ValueError("Bitte einen vorhandenen Raum wählen")
    count = len(room.walkboxes)
    if count < 2:
        raise ValueError("BOXM-Verbindungen benötigen mindestens zwei Walkboxen")

    def shared_border(first: Walkbox, second: Walkbox) -> bool:
        """Require a positive-length shared edge, not merely one common corner."""
        for polygon_a, polygon_b in ((first.corners, second.corners),):
            for i in range(4):
                ax, ay = polygon_a[i]
                bx, by = polygon_a[(i + 1) % 4]
                vx, vy = bx - ax, by - ay
                for j in range(4):
                    cx, cy = polygon_b[j]
                    dx, dy = polygon_b[(j + 1) % 4]
                    if vx * (cy - ay) - vy * (cx - ax):
                        continue
                    if vx * (dy - ay) - vy * (dx - ax):
                        continue
                    if (vx and min(max(ax, bx), max(cx, dx)) >
                            max(min(ax, bx), min(cx, dx))) or (
                            not vx and min(max(ay, by), max(cy, dy)) >
                            max(min(ay, by), min(cy, dy))):
                        return True
        return False

    graph = {index: set() for index in range(1, count + 1)}
    tokens = [part.strip() for part in connections.split(";") if part.strip()]
    for token in tokens:
        match = re.fullmatch(r"(\d+)\s*-\s*(\d+)", token)
        if match is None:
            raise ValueError("BOXM-Verbindungen als 1-2; 2-3 eingeben")
        first, second = map(int, match.groups())
        if not 1 <= first <= count or not 1 <= second <= count or first == second:
            raise ValueError(f"Ungültige BOXM-Verbindung {token}: Boxen 1 bis {count}, ohne Selbstverbindung")
        if not shared_border(room.walkboxes[first - 1], room.walkboxes[second - 1]):
            raise ValueError(f"Walkboxen {first} und {second} haben keine gemeinsame Kante")
        graph[first].add(second)
        graph[second].add(first)

    matrix = [[None] * (count + 1) for _ in range(count + 1)]
    matrix[0][0] = 0
    for start in range(1, count + 1):
        matrix[start][start] = start
        queue = [start]
        first_hop = {start: start}
        for current in queue:
            for neighbor in sorted(graph[current]):
                if neighbor not in first_hop:
                    first_hop[neighbor] = neighbor if current == start else first_hop[current]
                    queue.append(neighbor)
        for destination, next_box in first_hop.items():
            matrix[start][destination] = next_box

    routes = tuple(tuple(row) for row in matrix)
    rooms = tuple(replace(item, box_routes=routes) if item.name == room_name else item
                  for item in document.rooms)
    return _checked(replace(document, rooms=rooms))


def author_room_scale_curve(raw: str, room_name: str, slot: int, scale1: int,
                            y1: int, scale2: int, y2: int, box_indices: str) -> str:
    """Author native SCAL curve and bind selected boxes without losing BOXM paths."""
    document = parse_document(raw)
    room = next((item for item in document.rooms if item.name == room_name), None)
    if room is None:
        raise ValueError("Bitte einen vorhandenen Raum wählen")
    if not room.walkboxes:
        raise ValueError("SCAL benötigt mindestens eine vorhandene Walkbox")
    height = room.geometry.room_height
    if (type(slot) is not int or not 1 <= slot <= 4
        or any(type(v) is not int for v in (scale1, y1, scale2, y2))
        or not 1 <= scale1 <= 255 or not 1 <= scale2 <= 255
        or not 0 <= y1 < y2 < height):
        raise ValueError(f"SCAL: Slot 1–4, Skalierung 1–255 und 0 ≤ y1 < y2 < {height} eingeben")
    if room.scale_slots is not None and any(room.scale_slots):
        raise ValueError("Vorhandene rohe SCAL-Daten dürfen nicht still überschrieben werden")
    tokens = [part.strip() for part in box_indices.split(",")]
    if not tokens or any(not re.fullmatch(r"[1-9]\d*", part) for part in tokens):
        raise ValueError("Walkbox-Nummern als 1,2,3 eingeben")
    indices = tuple(int(part) for part in tokens)
    if len(set(indices)) != len(indices) or any(i > len(room.walkboxes) for i in indices):
        raise ValueError(f"Walkbox-Nummern müssen eindeutig zwischen 1 und {len(room.walkboxes)} liegen")
    curve = ScaleCurve(slot, scale1, y1, scale2, y2)
    curves = tuple(sorted(tuple(item for item in room.scale_curves if item.slot != slot)
                          + (curve,), key=lambda item: item.slot))
    boxes = tuple(replace(box, scale=255, scale_slot=slot) if index in indices else box
                  for index, box in enumerate(room.walkboxes, start=1))
    updated = replace(room, walkboxes=boxes, scale_curves=curves, scale_slots=None)
    rooms = tuple(updated if item.name == room_name else item for item in document.rooms)
    return _checked(replace(document, rooms=rooms))


def import_room_zplane(raw: str, room_name: str, index: int, png_path: str) -> str:
    """Author one full-room native occlusion plane from a white-on-black PNG.

    White pixels occlude actors; black pixels remain transparent. The alpha
    channel is respected, so fully transparent pixels never occlude.
    """
    from PIL import Image

    document = parse_document(raw)
    room = next((item for item in document.rooms if item.name == room_name), None)
    if room is None:
        raise ValueError("Bitte einen vorhandenen Raum wählen")
    if type(index) is not int or not 1 <= index <= 9:
        raise ValueError("Z-Ebenenindex muss zwischen 1 und 9 liegen")
    if index > len(room.zplanes) + 1:
        raise ValueError("Z-Ebenen müssen lückenlos ab 1 angelegt werden")
    path = Path(png_path)
    if path.suffix.lower() != ".png":
        raise ValueError("Bitte eine PNG-Z-Maske wählen")
    try:
        with Image.open(path) as source:
            if source.format != "PNG":
                raise ValueError("Z-Maske muss eine echte PNG-Datei sein")
            size = (room.geometry.room_width, room.geometry.room_height)
            if source.size != size:
                raise ValueError(f"Z-Maske muss exakt {size[0]} × {size[1]} Pixel groß sein")
            rgba = source.convert("RGBA")
            pixels = bytes(1 if alpha >= 128 and
                           (red * 299 + green * 587 + blue * 114) >= 128000
                           else 0 for red, green, blue, alpha in rgba.getdata())
    except (OSError, Image.DecompressionBombError) as error:
        raise ValueError(f"PNG-Z-Maske nicht lesbar: {error}") from error
    planes = list(room.zplanes)
    if index <= len(planes):
        planes[index - 1] = ZPlane(index, pixels)
    else:
        planes.append(ZPlane(index, pixels))
    rooms = tuple(replace(item, zplanes=tuple(planes)) if item.name == room_name else item
                  for item in document.rooms)
    return _checked(replace(document, rooms=rooms))



def import_object_zplane(raw: str, room_name: str, hotspot_id: str, png_path: str,
                         image_state: int = 1) -> str:
    """Assign a PNG Z-mask independently to native object image state 1 or 2."""
    from PIL import Image

    document = parse_document(raw)
    room = next((item for item in document.rooms if item.name == room_name), None)
    if room is None:
        raise ValueError("Bitte einen vorhandenen Raum wählen")
    hotspot = next((item for item in room.hotspots if item.id == hotspot_id), None)
    if hotspot is None or hotspot.sprite_pixels is None:
        raise ValueError("Objekt-Z-Maske benötigt ein vorhandenes Objektbild")
    if type(image_state) is not int or image_state not in (1, 2):
        raise ValueError("Objekt-Z-Maske unterstützt Bildzustand 1 oder 2")
    if image_state == 2 and hotspot.open_sprite_pixels is None:
        raise ValueError("Bildzustand 2 benötigt ein vorhandenes offenes Objektbild")
    path = Path(png_path)
    if path.suffix.lower() != ".png":
        raise ValueError("Bitte eine PNG-Objekt-Z-Maske wählen")
    try:
        with Image.open(path) as image:
            if image.format != "PNG":
                raise ValueError("Objekt-Z-Maske muss eine echte PNG-Datei sein")
            expected = (hotspot.width, hotspot.height)
            if image.size != expected:
                raise ValueError(f"Objekt-Z-Maske muss exakt {expected[0]} × {expected[1]} Pixel groß sein")
            pixels = bytes(
                1 if alpha >= 128 and (red * 299 + green * 587 + blue * 114) >= 128000 else 0
                for red, green, blue, alpha in image.convert("RGBA").getdata()
            )
    except (OSError, Image.DecompressionBombError) as error:
        raise ValueError(f"PNG-Objekt-Z-Maske nicht lesbar: {error}") from error
    updated = (replace(hotspot, object_zplane_pixels=pixels) if image_state == 1
               else replace(hotspot, open_object_zplane_pixels=pixels))
    rooms = tuple(
        replace(item, hotspots=tuple(updated if obj.id == hotspot_id else obj for obj in item.hotspots))
        if item.name == room_name else item for item in document.rooms
    )
    return _checked(replace(document, rooms=rooms))


def import_room_music(raw: str, room_name: str, music_id: str, midi_path: str) -> str:
    """Attach a real MIDI asset to one room; the native exporter wraps it as GMD."""
    document = parse_document(raw)
    if room_name not in {room.name for room in document.rooms}:
        raise ValueError("Bitte einen vorhandenen Musikraum wählen")
    if music_id in {asset.id for asset in document.music_assets}:
        raise ValueError("Musik-ID existiert bereits")
    path = Path(midi_path)
    if path.suffix.lower() not in (".mid", ".midi"):
        raise ValueError("Bitte eine MIDI-Datei (.mid) wählen")
    midi = path.read_bytes()
    rooms = tuple(replace(room, music_id=music_id) if room.name == room_name else room
                  for room in document.rooms)
    return _checked(replace(document, rooms=rooms,
                            music_assets=(*document.music_assets, MusicAsset(music_id, midi))))


def import_room_sound(raw: str, room_name: str, sound_id: str, voc_path: str) -> str:
    """Attach a native Creative Voice File effect to one authored room."""
    document = parse_document(raw)
    if room_name not in {room.name for room in document.rooms}:
        raise ValueError("Bitte einen vorhandenen Soundraum wählen")
    if sound_id in {asset.id for asset in document.sound_assets}:
        raise ValueError("Sound-ID existiert bereits")
    path = Path(voc_path)
    if path.suffix.lower() != ".voc":
        raise ValueError("Bitte eine Creative-Voice-Datei (.voc) wählen")
    voc = path.read_bytes()
    return _checked(replace(document, sound_assets=(
        *document.sound_assets, SoundAsset(sound_id, room_name, voc))))


def room_sound_ids(raw: str, room_name: str) -> tuple[str, ...]:
    return tuple(asset.id for asset in parse_document(raw).sound_assets
                 if asset.room == room_name)


def dialogue_voice_lines(raw: str) -> tuple[tuple[str, str], ...]:
    """Stable choices for authored NPC opening and answer dialogue lines."""
    document = parse_document(raw)
    result = []
    for room in document.rooms:
        for rule_index, rule in enumerate(room.talk_rules):
            for stage_index, stage in enumerate((rule, *rule.stages)):
                base = f"room.{room.name.lower()}.dialogue.{rule_index}"
                if stage_index:
                    base += f".stage.{stage_index - 1}"
                for line_index, line in enumerate(stage.opening_lines):
                    result.append((f"{room.name} / {rule.speaker_id} / {line}",
                                   f"{base}.opening.{line_index}"))
                for choice_index, choice in enumerate(stage.choices):
                    for line_index, line in enumerate(choice.reply_lines):
                        result.append((f"{room.name} / {choice.caption} / {line}",
                                       f"{base}.choice.{choice_index}.reply.{line_index}"))
    return tuple(result)


def _dialogue_animation_targets(document):
    targets = {}
    for room in document.rooms:
        for hotspot in room.hotspots:
            for index, actor in enumerate(hotspot.talk_actor_lines):
                key = f"room.{room.name.lower()}.object.{hotspot.id.lower()}.talk.{index}"
                targets[key] = (hotspot.talk_lines[index], actor)
        for rule_index, rule in enumerate(room.talk_rules):
            actors = dict(rule.actor_lines)
            for stage_index, stage in enumerate((rule, *rule.stages)):
                prefix = f"room.{room.name.lower()}.dialogue.{rule_index}"
                if stage_index:
                    prefix += f".stage.{stage_index - 1}"
                for index, line in enumerate(stage.opening_lines):
                    key = f"{prefix}.opening.{index}"
                    if key in actors:
                        targets[key] = (line, actors[key])
                for choice_index, choice in enumerate(stage.choices):
                    for index, line in enumerate(choice.reply_lines):
                        key = f"{prefix}.choice.{choice_index}.reply.{index}"
                        if key in actors:
                            targets[key] = (line, actors[key])
    return targets


def dialogue_animation_lines(raw: str) -> tuple[tuple[str, str], ...]:
    targets = _dialogue_animation_targets(parse_document(raw))
    return tuple((f"{actor} / {line}", key) for key, (line, actor) in targets.items())


def dialogue_costume_isolation_preview(raw: str | None, line_id: str | None) -> str:
    """Describe the exact Actor/Costume effects before creating a private copy."""
    if not raw or not line_id:
        return "Bitte eine native Sprecher-Dialogzeile wählen"
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        return "Diese Zeile hat keinen nativen Sprecher-Actor"
    actor = next(item for item in document.actors if item.id == target[1])
    sharing = sorted(item.id for item in document.actors
                     if item.id != actor.id and item.costume == actor.costume)
    if not sharing:
        return f"{actor.id}: Costume {actor.costume} gehört bereits nur dieser Figur"
    name = _isolated_costume_name(document, actor.costume, actor.id)
    return (f"{actor.id}: {actor.costume} → {name}. Die vollständige Costume samt "
            "Frames und Animationen wird kopiert. Nur diese Figur erhält die neue "
            "Costume; unverändert bleiben: " + ", ".join(sharing))


def _isolated_costume_name(document: GameDocument, costume: str, actor: str) -> str:
    existing = {item.name for item in document.costumes}
    base = f"{costume}_{actor}"
    name = base
    suffix = 2
    while name in existing:
        name = f"{base}_{suffix}"
        suffix += 1
    return name


def isolate_dialogue_speaker_costume(raw: str, line_id: str) -> str:
    """Copy-on-write a shared native Costume for all lines of one speaker Actor."""
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    actor = next(item for item in document.actors if item.id == target[1])
    if not any(item.id != actor.id and item.costume == actor.costume
               for item in document.actors):
        raise ValueError("Die Costume dieser Figur ist bereits exklusiv")
    costume = next(item for item in document.costumes if item.name == actor.costume)
    name = _isolated_costume_name(document, costume.name, actor.id)
    actors = tuple(replace(item, costume=name) if item.id == actor.id else item
                   for item in document.actors)
    return _checked(replace(document, actors=actors,
                            costumes=(*document.costumes, replace(costume, name=name))))


def dialogue_animation_choices(raw: str, line_id: str | None):
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        return (), None, True
    actor = next(item for item in document.actors if item.id == target[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    options = tuple(animation.name for animation in costume.animations
                    if animation.index is not None and animation.index >= 24)
    selected = next((cue.animation for cue in document.dialogue_animation_cues
                     if cue.line_id == line_id), None)
    reset = next((cue.reset_to_stand for cue in document.dialogue_animation_cues
                  if cue.line_id == line_id), True)
    return options, selected, reset


def dialogue_animation_phase_selection(raw: str, line_id: str | None) -> tuple[int, int]:
    """Native script ticks before and after the selected line's gesture start."""
    if not raw:
        return 1, 60
    cue = next((item for item in parse_document(raw).dialogue_animation_cues
                if item.line_id == line_id), None)
    return ((cue.start_delay_ticks, cue.minimum_animation_ticks)
            if cue is not None else (1, 60))


def dialogue_ending_animation_selection(raw: str, line_id: str | None):
    """Costume animations available as the selected line's native ending cue."""
    if not raw:
        return (), None, 12
    options, _selected, _reset = dialogue_animation_choices(raw, line_id)
    cue = next((item for item in parse_document(raw).dialogue_animation_cues
                if item.line_id == line_id), None)
    return (options, cue.ending_animation if cue else None,
            cue.ending_animation_ticks if cue and cue.ending_animation else 12)


def edit_dialogue_ending_animation(raw: str, line_id: str,
                                   animation: str | None, ticks: int | float) -> str:
    """Author an optional ending gesture after native waitForMessage."""
    document = parse_document(raw)
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    if cue is None:
        raise ValueError("Bitte zuerst eine Sprechanimation für diese Dialogzeile zuweisen")
    if animation is None:
        updated = replace(cue, ending_animation=None, ending_animation_ticks=0)
    else:
        if (type(ticks) not in (int, float) or int(ticks) != ticks or ticks <= 0):
            raise ValueError("Die Abschlussgeste benötigt mindestens einen ganzen nativen Tick")
        updated = replace(cue, ending_animation=animation,
                          ending_animation_ticks=int(ticks))
    return _checked(replace(document, dialogue_animation_cues=tuple(
        updated if item.line_id == line_id else item
        for item in document.dialogue_animation_cues)))


def dialogue_ending_timeline(raw: str, line_id: str | None, direction: str):
    """Read the authored ending COST frames for one line and facing."""
    if direction not in ("N", "E", "S", "W"):
        raise ValueError("Bitte eine gültige Blickrichtung N/E/S/W auswählen")
    if not raw:
        return [], (), ()
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        return [], (), ()
    actor = next(item for item in document.actors if item.id == target[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    animation = next((item for item in costume.animations
                      if cue and item.name == cue.ending_animation), None)
    selected = next((item for item in animation.directions
                     if item.direction == direction), None) if animation else None
    steps = selected.commands if selected else ()
    images = (costume_timeline_images(raw, costume.name, animation.name, direction)
              if selected and all(step in {f.id for f in costume.frames} for step in steps)
              else [])
    return (images, tuple((f"{i + 1}. {step}", i) for i, step in enumerate(steps)),
            tuple(frame.id for frame in costume.frames))


def assign_dialogue_ending_sequence(raw: str, line_id: str, direction: str,
                                    frame_ids: str, ticks: int | float = 12) -> str:
    """Create/re-edit a private native ending COST channel without the Costume editor."""
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    if direction not in ("N", "E", "S", "W"):
        raise ValueError("Bitte eine gültige Blickrichtung N/E/S/W auswählen")
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    if cue is None:
        raise ValueError("Bitte zuerst eine Sprechanimation für diese Dialogzeile zuweisen")
    actor = next(item for item in document.actors if item.id == target[1])
    sharing = [item.id for item in document.actors
               if item.id != actor.id and item.costume == actor.costume]
    if sharing:
        raise ValueError("Die Costume wird auch von anderen Figuren verwendet: "
                         + ", ".join(sharing) + ". Bitte zuerst eine eigene Costume zuweisen")
    costume = next(item for item in document.costumes if item.name == actor.costume)
    if not isinstance(frame_ids, str) or not frame_ids.strip():
        raise ValueError("Bitte mindestens ein importiertes PNG-Frame auswählen")
    sequence = tuple(part.strip() for part in frame_ids.split(","))
    available = {frame.id for frame in costume.frames}
    if any(not part or part not in available for part in sequence):
        raise ValueError("Die Abschlussfolge darf nur vorhandene PNG-Frames enthalten")
    name = "ending_line_" + sha1(line_id.encode("utf-8")).hexdigest()[:12]
    previous = next((item for item in costume.animations if item.name == name), None)
    if any(other.line_id != line_id and
           (other.animation == name or other.ending_animation == name)
           for other in document.dialogue_animation_cues):
        raise ValueError("Der native Abschluss-Slot gehört einer anderen Dialogzeile")
    if previous is None:
        occupied = {item.index for item in costume.animations if item.index is not None}
        index = next((slot for slot in range(28, 253, 4) if slot not in occupied), None)
        if index is None:
            raise ValueError("Keine freien nativen Costume-Animationsslots für Abschlussfolgen")
        base = next((item for item in costume.animations
                     if item.name == (cue.ending_animation or cue.animation)), None)
    else:
        if previous.index is None or previous.index < 28:
            raise ValueError("Vorhandene Abschlussanimation verwendet einen reservierten Slot")
        index, base = previous.index, previous
    if base is None or {item.direction for item in base.directions} != {"N", "E", "S", "W"}:
        raise ValueError("Die Abschlussfolge benötigt eine bestehende Animation mit vier Blickrichtungen")
    directions = tuple(CostumeDirection(item.direction, sequence, True)
                       if item.direction == direction else item
                       for item in base.directions)
    animation = CostumeAnimation(name, directions, index)
    updated_costume = replace(costume, animations=tuple(
        item for item in costume.animations if item.name != name) + (animation,))
    updated = canonical_json(replace(document, costumes=tuple(
        updated_costume if item.name == costume.name else item for item in document.costumes)))
    return edit_dialogue_ending_animation(updated, line_id, name, ticks)


def edit_dialogue_ending_timeline(raw: str, line_id: str, direction: str,
                                  step_number: int | float | None, operation: str,
                                  frame_id: str | None = None,
                                  ticks: int | float = 12) -> str:
    """Append, reorder or remove a PNG in the line-specific ending timeline."""
    _, steps, available = dialogue_ending_timeline(raw, line_id, direction)
    if not available:
        raise ValueError("Bitte eine Sprecher-Dialogzeile mit PNG-Costume auswählen")
    if steps and any(part.split(". ", 1)[1] not in available for part, _ in steps):
        raise ValueError("Diese Abschlussanimation enthält native Kommandos")
    sequence = [part.split(". ", 1)[1] for part, _ in steps]
    if operation == "Anhängen":
        if frame_id not in available:
            raise ValueError("Bitte ein vorhandenes PNG-Frame auswählen")
        sequence.append(frame_id)
    else:
        if (type(step_number) not in (int, float) or int(step_number) != step_number
                or not 0 <= int(step_number) < len(sequence)):
            raise ValueError("Bitte einen gültigen Abschlussframe-Schritt auswählen")
        index = int(step_number)
        if operation == "Entfernen":
            if len(sequence) == 1:
                raise ValueError("Zum Entfernen der gesamten Abschlussgeste den Entfernen-Button nutzen")
            sequence.pop(index)
        elif operation in ("Nach links", "Nach rechts"):
            other = index + (-1 if operation == "Nach links" else 1)
            if not 0 <= other < len(sequence):
                raise ValueError("Abschlussframe ist bereits am Rand")
            sequence[index], sequence[other] = sequence[other], sequence[index]
        else:
            raise ValueError("Unbekannte Abschluss-Timeline-Aktion")
    return assign_dialogue_ending_sequence(raw, line_id, direction, ", ".join(sequence), ticks)


def import_dialogue_png_frame(raw: str, line_id: str, direction: str,
                              png_path: str, frame_id: str, target: str,
                              ending_ticks: int | float = 12,
                              reset_to_stand: bool = True) -> str:
    """Import actual PNG pixels and append them to one authored dialogue channel.

    Both operations are atomic with respect to the returned project JSON: a
    missing actor, invalid image, full native palette or invalid cue cannot
    leave an orphan imported frame in the editor state.
    """
    document = parse_document(raw)
    selected = _dialogue_animation_targets(document).get(line_id)
    if selected is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    if direction not in ("N", "E", "S", "W"):
        raise ValueError("Bitte eine gültige Blickrichtung N/E/S/W auswählen")
    if target not in ("Sprechfolge", "Abschlussfolge"):
        raise ValueError("Bitte Sprechfolge oder Abschlussfolge auswählen")
    if not isinstance(frame_id, str) or not frame_id.strip():
        raise ValueError("Bitte eine eindeutige native PNG-Frame-ID eingeben")
    actor = next(item for item in document.actors if item.id == selected[1])
    sharing = [item.id for item in document.actors
               if item.id != actor.id and item.costume == actor.costume]
    if sharing:
        raise ValueError("Die Costume wird auch von anderen Figuren verwendet: "
                         + ", ".join(sharing) + ". Bitte zuerst eine eigene Costume zuweisen")
    # In particular, reject a duplicate before PNG decoding or any animation
    # reassignment. Existing native Costume frame IDs are immutable.
    costume = next(item for item in document.costumes if item.name == actor.costume)
    if frame_id in {frame.id for frame in costume.frames}:
        raise ValueError("Die PNG-Frame-ID existiert bereits in dieser Costume")
    imported = add_costume_frame(raw, costume.name, png_path, frame_id)
    if target == "Sprechfolge":
        return edit_dialogue_speaking_timeline(
            imported, line_id, direction, None, "Anhängen", frame_id, reset_to_stand)
    return edit_dialogue_ending_timeline(
        imported, line_id, direction, None, "Anhängen", frame_id, ending_ticks)


def _dialogue_png_batch_entries(paths: list[str] | tuple[str, ...] | None,
                                frame_ids: list[str] | tuple[str, ...] | None = None
                                ) -> tuple[tuple[str, str], ...]:
    if not isinstance(paths, (list, tuple)) or not paths:
        raise ValueError("Bitte mindestens eine PNG-Datei auswählen")
    entries = []
    if frame_ids is not None and len(frame_ids) != len(paths):
        raise ValueError("Die PNG-Frame-IDs passen nicht mehr zur Dateiauswahl")
    for index, path in enumerate(paths):
        if not isinstance(path, str) or not path or Path(path).suffix.lower() != ".png":
            raise ValueError("Die Folge darf nur PNG-Dateien enthalten")
        stem = unicodedata.normalize("NFKD", Path(path).stem).encode("ascii", "ignore").decode("ascii")
        frame_id = re.sub(r"[^A-Za-z0-9_]", "_", stem).strip("_")
        if not frame_id or not frame_id[0].isalpha():
            frame_id = "Frame_" + (frame_id or "PNG")
        if frame_ids is not None:
            frame_id = frame_ids[index]
            if not isinstance(frame_id, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", frame_id):
                raise ValueError(f"Ungültige native Frame-ID für {Path(path).name}: "
                                 "nur Buchstaben, Zahlen und _; Beginn mit Buchstabe")
        entries.append((path, frame_id))
    names = [frame_id for _path, frame_id in entries]
    if len(set(names)) != len(names):
        raise ValueError("Mehrere PNG-Dateinamen ergeben dieselbe Frame-ID; bitte Dateien umbenennen")
    return tuple(entries)


def dialogue_png_batch_entries(paths: list[str] | tuple[str, ...] | None,
                               order: list[int] | tuple[int, ...] | None = None,
                               frame_ids: dict[int, str] | None = None
                               ) -> tuple[tuple[str, str], ...]:
    """Resolve explicit IDs by original upload index, across sorting and exclusion."""
    included = dialogue_png_batch_order(paths, order)
    indexes = tuple(range(len(paths))) if order is None else tuple(order)
    if frame_ids is not None and (not isinstance(frame_ids, dict) or
                                  any(type(index) is not int or index not in range(len(paths))
                                      for index in frame_ids)):
        raise ValueError("Die PNG-Frame-IDs passen nicht mehr zur Dateiauswahl")
    default_ids = tuple(_dialogue_png_batch_entries((path,))[0][1] for path in included)
    ids = tuple(frame_ids.get(index, default_id) if frame_ids else default_id
                for index, default_id in zip(indexes, default_ids))
    return _dialogue_png_batch_entries(included, ids)


def set_dialogue_png_batch_frame_id(paths: list[str] | tuple[str, ...] | None,
                                    order: list[int] | tuple[int, ...] | None,
                                    selected: int | None, frame_id: str,
                                    overrides: dict[int, str] | None = None
                                    ) -> dict[int, str]:
    """Set the selected native ID without mutating another staged upload."""
    included = dialogue_png_batch_order(paths, order)
    if type(selected) is not int or selected not in range(len(included)):
        raise ValueError("Bitte zuerst ein PNG-Frame in der Importauswahl auswählen")
    index = selected if order is None else order[selected]
    updated = dict(overrides or {})
    updated[index] = frame_id
    _dialogue_png_batch_entries((included[selected],), (frame_id,))
    return updated


def dialogue_png_batch_selected_frame_id(paths: list[str] | tuple[str, ...] | None,
                                          order: list[int] | tuple[int, ...] | None,
                                          selected: int | None,
                                          frame_ids: dict[int, str] | None = None) -> str:
    """Show an editable ID even while other staged frames conflict."""
    if not paths:
        return ""
    included = dialogue_png_batch_order(paths, order)
    if type(selected) is not int or selected not in range(len(included)):
        return ""
    source_index = selected if order is None else order[selected]
    default_id = _dialogue_png_batch_entries((included[selected],))[0][1]
    return frame_ids.get(source_index, default_id) if frame_ids else default_id


def suggest_dialogue_png_batch_frame_id(raw: str | None, line_id: str | None,
                                         paths: list[str] | tuple[str, ...] | None,
                                         order: list[int] | tuple[int, ...] | None,
                                         selected: int | None,
                                         frame_ids: dict[int, str] | None = None
                                         ) -> dict[int, str]:
    """Reserve the first free native ID across this Costume and included uploads."""
    included = dialogue_png_batch_order(paths, order)
    if type(selected) is not int or selected not in range(len(included)):
        raise ValueError("Bitte zuerst ein PNG-Frame in der Importauswahl auswählen")
    if not raw or not line_id:
        raise ValueError("Bitte zuerst eine native Sprecher-Dialogzeile auswählen")
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    actor = next(item for item in document.actors if item.id == target[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    used = {frame.id for frame in costume.frames}
    used.update(dialogue_png_batch_selected_frame_id(paths, order, index, frame_ids)
                for index in range(len(included)) if index != selected)
    original = dialogue_png_batch_selected_frame_id(paths, order, selected, frame_ids)
    candidate = original
    suffix = 2
    while candidate in used:
        candidate = f"{original}_{suffix}"
        suffix += 1
    return set_dialogue_png_batch_frame_id(paths, order, selected, candidate, frame_ids)


def resolve_dialogue_png_batch_frame_ids(raw: str | None, line_id: str | None,
                                          paths: list[str] | tuple[str, ...] | None,
                                          order: list[int] | tuple[int, ...] | None,
                                          frame_ids: dict[int, str] | None = None
                                          ) -> dict[int, str]:
    """Fix all ID collisions atomically, preserving every already-free staged ID."""
    included = dialogue_png_batch_order(paths, order)
    if not included:
        raise ValueError("Die Importauswahl enthält keine Bilder")
    if not raw or not line_id:
        raise ValueError("Bitte zuerst eine native Sprecher-Dialogzeile auswählen")
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    actor = next(item for item in document.actors if item.id == target[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    known = {frame.id for frame in costume.frames}
    names = [dialogue_png_batch_selected_frame_id(paths, order, index, frame_ids)
             for index in range(len(included))]
    for path, name in zip(included, names):
        _dialogue_png_batch_entries((path,), (name,))
    # Reserve every first usable occurrence before assigning new suffixes.
    reserved = set(known)
    conflict_positions = []
    for position, name in enumerate(names):
        if name in reserved:
            conflict_positions.append(position)
        else:
            reserved.add(name)
    updated = dict(frame_ids or {})
    indexes = tuple(range(len(paths))) if order is None else tuple(order)
    for position in conflict_positions:
        base = names[position]
        suffix = 2
        candidate = f"{base}_{suffix}"
        while candidate in reserved:
            suffix += 1
            candidate = f"{base}_{suffix}"
        updated[indexes[position]] = candidate
        reserved.add(candidate)
    dialogue_png_batch_entries(paths, order, updated)
    return updated


def dialogue_png_batch_order(paths: list[str] | tuple[str, ...] | None,
                             order: list[int] | tuple[int, ...] | None = None
                             ) -> tuple[str, ...]:
    """Resolve included uploads, in order, without deleting staged files."""
    if not isinstance(paths, (list, tuple)) or not paths:
        raise ValueError("Bitte mindestens eine PNG-Datei auswählen")
    indexes = tuple(range(len(paths))) if order is None else tuple(order)
    if (len(indexes) > len(paths) or
            any(type(index) is not int for index in indexes) or
            len(set(indexes)) != len(indexes) or
            any(index not in range(len(paths)) for index in indexes)):
        raise ValueError("Die PNG-Reihenfolge passt nicht mehr zur Dateiauswahl; bitte neu auswählen")
    return tuple(paths[index] for index in indexes)


def _dialogue_png_sprite_sheet_cells(
        sheet_path: str | None, columns: int | float, rows: int | float,
        margin_x: int | float = 0, margin_y: int | float = 0,
        gap_x: int | float = 0, gap_y: int | float = 0
        ) -> tuple[object, tuple[tuple[int, int, int, int], ...]]:
    """The single pixel-exact grid contract for both preview and native staging."""
    from PIL import Image

    if (not isinstance(sheet_path, str) or not sheet_path or
            Path(sheet_path).suffix.lower() != ".png"):
        raise ValueError("Bitte ein PNG-Sprite-Sheet auswählen")
    for label, count in (("Spalten", columns), ("Zeilen", rows)):
        if (type(count) not in (int, float) or not isfinite(count) or count < 1 or
                int(count) != count):
            raise ValueError(f"Sprite-Sheet-{label} müssen positive ganze Zahlen sein")
    for label, count in (("Außenrand X", margin_x), ("Außenrand Y", margin_y),
                         ("Zellabstand X", gap_x), ("Zellabstand Y", gap_y)):
        if (type(count) not in (int, float) or not isfinite(count) or count < 0 or
                int(count) != count):
            raise ValueError(f"Sprite-Sheet-{label} muss eine nichtnegative ganze Pixelzahl sein")
    columns, rows = int(columns), int(rows)
    margin_x, margin_y, gap_x, gap_y = (int(value) for value in
                                      (margin_x, margin_y, gap_x, gap_y))
    with Image.open(sheet_path) as source:
        if source.format != "PNG" or getattr(source, "n_frames", 1) != 1:
            raise ValueError("Das Sprite-Sheet muss ein einzelnes PNG-Bild sein")
        width, height = source.size
        usable_width = width - 2 * margin_x - (columns - 1) * gap_x
        usable_height = height - 2 * margin_y - (rows - 1) * gap_y
        if usable_width < columns or usable_height < rows:
            raise ValueError("Außenränder/Zellabstände lassen keinen Platz für gültige Sprite-Zellen")
        if usable_width % columns or usable_height % rows:
            raise ValueError("Sprite-Sheet-Abmessungen nach Außenrändern und Zellabständen "
                             "müssen durch Spalten und Zeilen teilbar sein")
        cell_width, cell_height = usable_width // columns, usable_height // rows
        pixels = source.convert("RGBA")
    boxes = []
    for row in range(rows):
        for column in range(columns):
            left = margin_x + column * (cell_width + gap_x)
            top = margin_y + row * (cell_height + gap_y)
            boxes.append((left, top, left + cell_width, top + cell_height))
    return pixels, tuple(boxes)


def dialogue_png_sprite_sheet_preview(
        sheet_path: str | None, columns: int | float, rows: int | float,
        margin_x: int | float = 0, margin_y: int | float = 0,
        gap_x: int | float = 0, gap_y: int | float = 0,
        skipped: list[int] | tuple[int, ...] | None = None,
        cell_order: list[int] | tuple[int, ...] | None = None,
        repeats: dict[int, int] | None = None,
        timeline: str | None = None
        ) -> tuple[object, list[tuple[object, str]], str]:
    """Show the exact prospective source rectangles without staging any frames."""
    from PIL import ImageDraw

    pixels, boxes = _dialogue_png_sprite_sheet_cells(
        sheet_path, columns, rows, margin_x, margin_y, gap_x, gap_y)
    excluded = _dialogue_png_sprite_skipped(boxes, skipped)
    sequence = dialogue_png_sprite_sheet_order(len(boxes), cell_order)
    expanded = dialogue_png_sprite_sheet_sequence(
        len(boxes), skipped, cell_order, repeats, timeline)
    positions: dict[int, list[int]] = {}
    for number, index in enumerate(expanded, 1):
        positions.setdefault(index, []).append(number)
    overlay = pixels.copy()
    draw = ImageDraw.Draw(overlay)
    for index, (left, top, right, bottom) in enumerate(boxes):
        draw.rectangle((left, top, right - 1, bottom - 1),
                       outline=((130, 130, 130, 255) if index in excluded else
                                (255, 75, 35, 255)), width=1)
    thumbnails = [(pixels.crop(box), f"{index}. Zeile {(index - 1) // int(columns) + 1}, "
                    f"Spalte {(index - 1) % int(columns) + 1} · "
                    + ("⛔ Überspringen" if index - 1 in excluded else
                       ("✓ Abspielpositionen " if len(positions[index - 1]) > 1 and timeline else
                        "✓ Abspielposition ") +
                       (", ".join(str(i) for i in positions[index - 1]) if timeline else
                        str(positions[index - 1][0])) +
                       (f" · {len(positions[index - 1])}×" if len(positions[index - 1]) > 1 else "")))
                  for index, box in enumerate(boxes, 1)]
    width = boxes[0][2] - boxes[0][0]
    height = boxes[0][3] - boxes[0][1]
    return overlay, thumbnails, (f"{len(boxes) - len(excluded)} von {len(boxes)} "
                                  "PNG-Frames ausgewählt · "
                                  f"{len(expanded)} Abspielbilder · "
                                  + ("Freie Abspielsequenz " if timeline and timeline.strip() else
                                     "Abspielreihenfolge ") +
                                  f"· je {width} × {height} Pixel · noch nicht hinzugefügt")


def dialogue_png_sprite_sheet_playback_frames(
        sheet_path: str | None, columns: int | float, rows: int | float,
        margin_x: int | float = 0, margin_y: int | float = 0,
        gap_x: int | float = 0, gap_y: int | float = 0,
        skipped: list[int] | tuple[int, ...] | None = None,
        cell_order: list[int] | tuple[int, ...] | None = None,
        repeats: dict[int, int] | None = None,
        timeline: str | None = None) -> list[tuple[object, str]]:
    """Return one inspectable thumbnail for every actual native playback position."""
    pixels, boxes = _dialogue_png_sprite_sheet_cells(
        sheet_path, columns, rows, margin_x, margin_y, gap_x, gap_y)
    sequence = dialogue_png_sprite_sheet_sequence(
        len(boxes), skipped, cell_order, repeats, timeline)
    return [(pixels.crop(boxes[source]), f"{position}. Bild · Zelle {source + 1}")
            for position, source in enumerate(sequence, 1)]


def _dialogue_png_sprite_repeat_counts(count: int,
                                       repeats: dict[int, int] | None) -> dict[int, int]:
    if repeats is None:
        return {}
    if (not isinstance(repeats, dict) or
            any(type(index) is not int or index not in range(count) or
                type(amount) is not int or amount < 2
                for index, amount in repeats.items())):
        raise ValueError("Die Sprite-Sheet-Wiederholungen passen nicht mehr zum Raster")
    return repeats


def dialogue_png_sprite_sheet_sequence(count: int,
                                       skipped: list[int] | tuple[int, ...] | None,
                                       cell_order: list[int] | tuple[int, ...] | None,
                                       repeats: dict[int, int] | None = None,
                                       timeline: str | None = None
                                       ) -> tuple[int, ...]:
    """One sequence for native staging, visual thumbnails and GIF playback."""
    order = dialogue_png_sprite_sheet_order(count, cell_order)
    excluded = _dialogue_png_sprite_skipped(tuple((0, 0, 1, 1) for _ in range(count)), skipped)
    counts = _dialogue_png_sprite_repeat_counts(count, repeats)
    if timeline is not None and not isinstance(timeline, str):
        raise ValueError("Die freie Sprite-Sheet-Abspielsequenz muss eine Zellnummernliste sein")
    if timeline is not None and timeline.strip():
        parts = [part.strip() for part in timeline.split(",")]
        if any(not part.isascii() or not part.isdecimal() for part in parts):
            raise ValueError("Freie Abspielsequenz: Zellnummern mit Kommas trennen, z. B. 1,2,1")
        selected = tuple(int(part) - 1 for part in parts)
        if any(index not in range(count) for index in selected):
            raise ValueError("Freie Abspielsequenz: Zellnummer liegt außerhalb des Rasters")
        if any(index in excluded for index in selected):
            raise ValueError("Freie Abspielsequenz enthält eine ausgeschlossene Zelle")
        missing = [index + 1 for index in order if index not in excluded and index not in selected]
        if missing:
            raise ValueError("Freie Abspielsequenz: ausgewählte Zellen fehlen: " +
                             ", ".join(str(index) for index in missing))
        return selected
    return tuple(index for index in order if index not in excluded
                 for _ in range(counts.get(index, 1)))


# Bounded, in-memory editor history; this is not a SCUMM-v6 sequence limit.
SPRITE_SHEET_UNDO_STEPS = 20


def track_dialogue_png_sprite_sheet_undo(
        history: tuple[tuple[object, ...], tuple[str, ...], int] | None,
        timeline: str, context: tuple[object, ...]
        ) -> tuple[tuple[object, ...], tuple[str, ...], int]:
    """Record each actual edit, discarding redo states on a new branch."""
    if not isinstance(timeline, str):
        raise ValueError("Die Abspielsequenz muss eine Zellnummernliste sein")
    if history is None:
        states = ("",) if timeline == "" else ("", timeline)
        return context, states, len(states) - 1
    if history[0] != context:
        return context, (timeline,), 0
    _, states, index = history
    if states[index] == timeline:
        return history
    updated = (*states[:index + 1], timeline)[-(SPRITE_SHEET_UNDO_STEPS + 1):]
    return context, updated, len(updated) - 1


def undo_dialogue_png_sprite_sheet_edit(
        history: tuple[tuple[object, ...], tuple[str, ...], int] | None,
        timeline: str, context: tuple[object, ...]
        ) -> tuple[str, tuple[tuple[object, ...], tuple[str, ...], int]]:
    """Move backward one state without changing the stored future."""
    if (history is None or history[0] != context or
            history[1][history[2]] != timeline or history[2] == 0):
        raise ValueError("Keine rückgängig machbare Änderung der aktuellen Bildfolge")
    next_index = history[2] - 1
    return history[1][next_index], (context, history[1], next_index)


def redo_dialogue_png_sprite_sheet_edit(
        history: tuple[tuple[object, ...], tuple[str, ...], int] | None,
        timeline: str, context: tuple[object, ...]
        ) -> tuple[str, tuple[tuple[object, ...], tuple[str, ...], int]]:
    """Move forward one state while no intervening edit changed the branch."""
    if (history is None or history[0] != context or
            history[1][history[2]] != timeline or
            history[2] == len(history[1]) - 1):
        raise ValueError("Keine wiederherstellbare Änderung der aktuellen Bildfolge")
    next_index = history[2] + 1
    return history[1][next_index], (context, history[1], next_index)



def dialogue_png_sprite_sheet_history_choices(
        history: tuple[tuple[object, ...], tuple[str, ...], int] | None
        ) -> list[tuple[str, int]]:
    """Give every reachable history state a readable, factual description."""
    if history is None:
        return []
    states = history[1]
    choices = []
    for index, timeline in enumerate(states):
        count = len([cell for cell in timeline.split(",") if cell.strip()])
        if index == 0:
            label = "Ausgangsstand" if len(states) <= 1 or timeline == "" else "Ältester Stand"
        else:
            previous_count = len([cell for cell in states[index - 1].split(",")
                                  if cell.strip()])
            if count > previous_count:
                label = f"Auf {count} Bilder erweitert"
            elif count < previous_count:
                label = f"Auf {count} Bilder gekürzt"
            else:
                label = f"Folge mit {count} Bildern geändert"
        preview = timeline if len(timeline) <= 32 else timeline[:29] + "…"
        choices.append((f"Schritt {index}: {label} · {preview or '(Knopf-Reihenfolge)'}",
                        index))
    return choices


def jump_dialogue_png_sprite_sheet_history(
        history: tuple[tuple[object, ...], tuple[str, ...], int] | None,
        timeline: str, context: tuple[object, ...], position: int
        ) -> tuple[str, tuple[tuple[object, ...], tuple[str, ...], int]]:
    """Navigate to an existing state without inventing a new history entry."""
    if (history is None or history[0] != context or
            history[1][history[2]] != timeline):
        raise ValueError("Der Bildfolgenverlauf passt nicht zum aktuellen Editorzustand")
    if type(position) is not int or not 0 <= position < len(history[1]):
        raise ValueError("Diese Bildfolgen-Historienposition ist nicht verfügbar")
    return history[1][position], (context, history[1], position)


def edit_dialogue_png_sprite_sheet_sequence(
        count: int, skipped: list[int] | tuple[int, ...] | None,
        cell_order: list[int] | tuple[int, ...] | None,
        repeats: dict[int, int] | None, timeline: str | None,
        action: str, position: int | None = None,
        source_index: int | None = None, step: int | None = None,
        end_position: int | None = None,
        destination_position: int | None = None,
        repetitions: int | None = None) -> str:
    """Compose a free play sequence using source-cell and position selectors."""
    if action == "reset":
        return ""
    sequence = list(dialogue_png_sprite_sheet_sequence(
        count, skipped, cell_order, repeats, timeline))
    if type(position) is not int:
        raise ValueError("Bitte eine Abspielposition auswählen")
    if action == "insert":
        if position not in range(len(sequence) + 1):
            raise ValueError("Die Einfügeposition gehört nicht zur aktuellen Abspielsequenz")
        excluded = _dialogue_png_sprite_skipped(
            tuple((0, 0, 1, 1) for _ in range(count)), skipped)
        if (type(source_index) is not int or source_index not in range(count) or
                source_index in excluded):
            raise ValueError("Bitte eine übernommene Sprite-Sheet-Zelle auswählen")
        sequence.insert(position, source_index)
    elif action == "remove":
        if position not in range(1, len(sequence) + 1):
            raise ValueError("Bitte ein vorhandenes Abspielbild zum Entfernen auswählen")
        index = sequence[position - 1]
        if sequence.count(index) <= 1:
            raise ValueError("Die letzte Kopie einer ausgewählten Zelle muss erhalten bleiben")
        sequence.pop(position - 1)
    elif action == "move":
        if position not in range(1, len(sequence) + 1):
            raise ValueError("Bitte ein vorhandenes Abspielbild zum Verschieben auswählen")
        if type(step) is not int or step not in (-1, 1):
            raise ValueError("Ungültige Richtung für das Verschieben eines Abspielbildes")
        target = position - 1 + step
        if target not in range(len(sequence)) or sequence[target] == sequence[position - 1]:
            return timeline or ""
        sequence[position - 1], sequence[target] = sequence[target], sequence[position - 1]
    elif action == "move_block":
        if (position not in range(1, len(sequence) + 1) or
                type(end_position) is not int or
                end_position not in range(position, len(sequence) + 1)):
            raise ValueError("Bitte einen gültigen Abspielblock von Start bis Ende auswählen")
        if type(step) is not int or step not in (-1, 1):
            raise ValueError("Ungültige Richtung für das Verschieben des Abspielblocks")
        if (step == -1 and position == 1) or (step == 1 and end_position == len(sequence)):
            return timeline or ""
        previous = tuple(sequence)
        if step == -1:
            sequence[position - 2:end_position] = (
                sequence[position - 1:end_position] + [sequence[position - 2]])
        else:
            sequence[position - 1:end_position + 1] = (
                [sequence[end_position]] + sequence[position - 1:end_position])
        if tuple(sequence) == previous:
            return timeline or ""
    elif action == "relocate_block":
        if (position not in range(1, len(sequence) + 1) or
                type(end_position) is not int or
                end_position not in range(position, len(sequence) + 1)):
            raise ValueError("Bitte einen gültigen Bildblock von Start bis Ende auswählen")
        if (type(destination_position) is not int or
                destination_position not in range(len(sequence) + 1)):
            raise ValueError("Bitte eine gültige Zielposition für den Bildblock auswählen")
        # Destination is a boundary in the original sequence: 0 before the
        # first image, N after image N. Boundaries within the block are no-ops.
        if position - 1 <= destination_position <= end_position:
            return timeline or ""
        block = sequence[position - 1:end_position]
        del sequence[position - 1:end_position]
        insertion = (destination_position if destination_position < position - 1
                     else destination_position - len(block))
        sequence[insertion:insertion] = block
    elif action == "remove_block":
        if (position not in range(1, len(sequence) + 1) or
                type(end_position) is not int or
                end_position not in range(position, len(sequence) + 1)):
            raise ValueError("Bitte einen gültigen Bildblock von Start bis Ende auswählen")
        block = sequence[position - 1:end_position]
        if any(sequence.count(index) == block.count(index) for index in set(block)):
            raise ValueError(
                "Die letzte Kopie jeder ausgewählten Zelle muss erhalten bleiben")
        del sequence[position - 1:end_position]
    elif action == "repeat_block":
        if (position not in range(1, len(sequence) + 1) or
                type(end_position) is not int or
                end_position not in range(position, len(sequence) + 1)):
            raise ValueError("Bitte einen gültigen Bildblock von Start bis Ende auswählen")
        if (type(destination_position) is not int or
                destination_position not in range(len(sequence) + 1)):
            raise ValueError("Bitte eine gültige Einfügeposition für den Bildblock auswählen")
        if type(repetitions) is not int or repetitions < 1:
            raise ValueError("Bitte mindestens eine zusätzliche Blockkopie angeben")
        block = sequence[position - 1:end_position]
        # Temporary PNG staging and the pixel gallery are deliberately bounded;
        # this is an editor-resource guard, not a native SCUMM-v6 frame limit.
        if len(block) * repetitions > 2048 - len(sequence):
            raise ValueError(
                "Maximal 2048 Abspielbilder je Sprite-Sheet-Import im Editor "
                "(temporäres Staging-Limit, keine SCUMM-v6-Grenze)")
        sequence[destination_position:destination_position] = block * repetitions
    elif action == "copy_block":
        if (position not in range(1, len(sequence) + 1) or
                type(end_position) is not int or
                end_position not in range(position, len(sequence) + 1)):
            raise ValueError("Bitte einen gültigen Bildblock von Start bis Ende auswählen")
        if (type(destination_position) is not int or
                destination_position not in range(len(sequence) + 1)):
            raise ValueError("Bitte eine gültige Einfügeposition für den Bildblock auswählen")
        block = sequence[position - 1:end_position]
        sequence[destination_position:destination_position] = block
    else:
        raise ValueError("Unbekannte Bearbeitung der Sprite-Sheet-Abspielsequenz")
    return ",".join(str(index + 1) for index in sequence)


def change_dialogue_png_sprite_sheet_repetition(
        count: int, skipped: list[int] | tuple[int, ...] | None,
        repeats: dict[int, int] | None, selected: int | None, step: int
        ) -> dict[int, int]:
    """Change a selected source cell's consecutive play count, minimum one."""
    excluded = _dialogue_png_sprite_skipped(tuple((0, 0, 1, 1) for _ in range(count)), skipped)
    counts = dict(_dialogue_png_sprite_repeat_counts(count, repeats))
    if type(selected) is not int or selected not in range(count) or selected in excluded:
        raise ValueError("Bitte zuerst eine übernommene Sprite-Sheet-Zelle auswählen")
    if type(step) is not int or step not in (-1, 1):
        raise ValueError("Ungültige Sprite-Sheet-Wiederholung")
    amount = max(1, counts.get(selected, 1) + step)
    if amount == 1:
        counts.pop(selected, None)
    else:
        counts[selected] = amount
    return counts


def dialogue_png_sprite_sheet_order(count: int,
                                     cell_order: list[int] | tuple[int, ...] | None
                                     ) -> tuple[int, ...]:
    """Validate a full permutation so skipped cells retain their position on restore."""
    if type(count) is not int or count < 1:
        raise ValueError("Das Sprite-Sheet benötigt mindestens eine Zelle")
    if cell_order is not None and not isinstance(cell_order, (list, tuple)):
        raise ValueError("Die Sprite-Sheet-Abspielreihenfolge passt nicht mehr zum Raster")
    indexes = tuple(range(count)) if cell_order is None or len(cell_order) == 0 else tuple(cell_order)
    if (len(indexes) != count or any(type(i) is not int for i in indexes) or
            set(indexes) != set(range(count))):
        raise ValueError("Die Sprite-Sheet-Abspielreihenfolge passt nicht mehr zum Raster")
    return indexes


def move_dialogue_png_sprite_sheet_cell(count: int,
                                        cell_order: list[int] | tuple[int, ...] | None,
                                        skipped: list[int] | tuple[int, ...] | None,
                                        selected: int | None, step: int
                                        ) -> tuple[int, ...]:
    """Move an included source cell among included positions; keep exclusions stable."""
    sequence = list(dialogue_png_sprite_sheet_order(count, cell_order))
    excluded = _dialogue_png_sprite_skipped(tuple((0, 0, 1, 1) for _ in range(count)), skipped)
    included = [index for index in sequence if index not in excluded]
    if type(selected) is not int or selected not in included:
        raise ValueError("Bitte zuerst eine übernommene Sprite-Sheet-Zelle auswählen")
    if step not in (-1, 1):
        raise ValueError("Die Sprite-Sheet-Zelle kann nur eine Position bewegt werden")
    position = included.index(selected)
    destination = position + step
    if destination not in range(len(included)):
        return tuple(sequence)
    other = included[destination]
    first, second = sequence.index(selected), sequence.index(other)
    sequence[first], sequence[second] = sequence[second], sequence[first]
    return tuple(sequence)


def _dialogue_png_sprite_skipped(boxes: tuple[tuple[int, int, int, int], ...],
                                 skipped: list[int] | tuple[int, ...] | None) -> set[int]:
    if skipped is None:
        return set()
    if (not isinstance(skipped, (list, tuple)) or
            any(type(index) is not int or index not in range(len(boxes)) for index in skipped) or
            len(set(skipped)) != len(skipped)):
        raise ValueError("Die ausgewählten Sprite-Sheet-Zellen passen nicht mehr zum Raster")
    return set(skipped)


def stage_dialogue_png_sprite_sheet(
        paths: list[str] | tuple[str, ...] | None,
        order: list[int] | tuple[int, ...] | None,
        sheet_path: str | None, columns: int | float, rows: int | float,
        margin_x: int | float = 0, margin_y: int | float = 0,
        gap_x: int | float = 0, gap_y: int | float = 0,
        skipped: list[int] | tuple[int, ...] | None = None,
        cell_order: list[int] | tuple[int, ...] | None = None,
        repeats: dict[int, int] | None = None,
        timeline: str | None = None
        ) -> tuple[tuple[str, ...], tuple[int, ...]]:
    """Append selected tiles in preview order, preserving existing staged exclusions."""
    originals = tuple(paths or ())
    included_indexes = (tuple(range(len(originals))) if order is None else tuple(order))
    if originals:
        dialogue_png_batch_order(originals, order)
    elif included_indexes:
        raise ValueError("Die PNG-Reihenfolge passt nicht mehr zur Dateiauswahl")
    pixels, boxes = _dialogue_png_sprite_sheet_cells(
        sheet_path, columns, rows, margin_x, margin_y, gap_x, gap_y)
    excluded = _dialogue_png_sprite_skipped(boxes, skipped)
    expanded = dialogue_png_sprite_sheet_sequence(
        len(boxes), skipped, cell_order, repeats, timeline)
    if len(excluded) == len(boxes):
        raise ValueError("Bitte mindestens eine Sprite-Sheet-Zelle für den Import auswählen")
    destination = Path(tempfile.mkdtemp(prefix="adventure-studio-sprite-sheet-"))
    tiles = []
    seen: dict[int, int] = {}
    for index in expanded:
        box = boxes[index]
        row, column = divmod(index, int(columns))
        seen[index] = seen.get(index, 0) + 1
        suffix = "" if seen[index] == 1 else f"_repeat{seen[index]}"
        tile = destination / f"{Path(sheet_path).stem}_r{row + 1}_c{column + 1}{suffix}.png"
        pixels.crop(box).save(tile)
        tiles.append(str(tile))
    indexes = (*included_indexes, *range(len(originals), len(originals) + len(tiles)))
    return (*originals, *tiles), indexes


def dialogue_png_sprite_sheet_animation_preview(
        sheet_path: str | None, columns: int | float, rows: int | float,
        duration_ms: int | float, destination: Path,
        margin_x: int | float = 0, margin_y: int | float = 0,
        gap_x: int | float = 0, gap_y: int | float = 0,
        skipped: list[int] | tuple[int, ...] | None = None,
        cell_order: list[int] | tuple[int, ...] | None = None,
        repeats: dict[int, int] | None = None,
        timeline: str | None = None) -> Path:
    """Play only selected sheet rectangles in native import order; no staging writes."""
    from PIL import Image

    if (type(duration_ms) not in (int, float) or not isfinite(duration_ms) or
            int(duration_ms) != duration_ms or not 40 <= duration_ms <= 2000):
        raise ValueError("Vorschau-Framezeit muss zwischen 40 und 2000 Millisekunden liegen")
    pixels, boxes = _dialogue_png_sprite_sheet_cells(
        sheet_path, columns, rows, margin_x, margin_y, gap_x, gap_y)
    included = dialogue_png_sprite_sheet_sequence(
        len(boxes), skipped, cell_order, repeats, timeline)
    if not included:
        raise ValueError("Bitte mindestens eine Sprite-Sheet-Zelle für die Vorschau auswählen")
    width, height = boxes[0][2] - boxes[0][0], boxes[0][3] - boxes[0][1]
    rendered = []
    for index in included:
        frame = pixels.crop(boxes[index])
        canvas = Image.new("RGB", (width, height), (36, 40, 48))
        canvas.paste(frame, (0, 0), frame)
        rendered.append(canvas)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rendered[0].save(destination, format="GIF", save_all=True,
                     append_images=rendered[1:], duration=int(duration_ms),
                     loop=0, optimize=False, disposal=2)
    return destination


def replace_dialogue_png_batch_frame(paths: list[str] | tuple[str, ...] | None,
                                     order: list[int] | tuple[int, ...] | None,
                                     selected: int | None,
                                     replacement: str | None) -> tuple[str, ...]:
    """Replace one included upload, keeping all source indexes and exclusions stable."""
    included = dialogue_png_batch_order(paths, order)
    if type(selected) is not int or selected not in range(len(included)):
        raise ValueError("Bitte zuerst ein PNG-Frame in der Importauswahl auswählen")
    if not isinstance(replacement, str) or not replacement or Path(replacement).suffix.lower() != ".png":
        raise ValueError("Bitte eine neue PNG-Datei als Ersatz auswählen")
    source_index = selected if order is None else order[selected]
    updated = list(paths)
    updated[source_index] = replacement
    return tuple(updated)


def move_dialogue_png_batch_frame(paths: list[str] | tuple[str, ...] | None,
                                  order: list[int] | tuple[int, ...] | None,
                                  selected: int | None, step: int
                                  ) -> tuple[tuple[int, ...], int]:
    """Move one selected upload while preserving valid inclusion indexes."""
    ordered = dialogue_png_batch_order(paths, order)
    indexes = list(range(len(ordered))) if order is None else list(order)
    if type(selected) is not int or selected not in range(len(indexes)):
        raise ValueError("Bitte zuerst ein PNG-Frame auswählen")
    if step not in (-1, 1):
        raise ValueError("Ungültige Verschieberichtung")
    destination = selected + step
    if destination in range(len(indexes)):
        indexes[selected], indexes[destination] = indexes[destination], indexes[selected]
        return tuple(indexes), destination
    return tuple(indexes), selected


def remove_dialogue_png_batch_frame(paths: list[str] | tuple[str, ...] | None,
                                    order: list[int] | tuple[int, ...] | None,
                                    selected: int | None
                                    ) -> tuple[tuple[int, ...], int | None]:
    """Exclude one staged PNG without re-uploading or touching project JSON."""
    ordered = dialogue_png_batch_order(paths, order)
    if type(selected) is not int or selected not in range(len(ordered)):
        raise ValueError("Bitte zuerst ein PNG-Frame auswählen")
    indexes = list(range(len(paths))) if order is None else list(order)
    indexes.pop(selected)
    return tuple(indexes), min(selected, len(indexes) - 1) if indexes else None


def dialogue_png_batch_excluded(paths: list[str] | tuple[str, ...] | None,
                                order: list[int] | tuple[int, ...] | None
                                ) -> tuple[tuple[str, int], ...]:
    """Offer only staged files not already present in the import sequence."""
    if not paths:
        return ()
    dialogue_png_batch_order(paths, order)
    included = set(range(len(paths))) if order is None else set(order)
    return tuple((f"{index + 1}. {Path(path).name}", index)
                 for index, path in enumerate(paths) if index not in included)


def restore_dialogue_png_batch_frame(paths: list[str] | tuple[str, ...] | None,
                                     order: list[int] | tuple[int, ...] | None,
                                     excluded_index: int | None
                                     ) -> tuple[tuple[int, ...], int]:
    """Reinclude a staged PNG at the end without changing other uploads."""
    included = dialogue_png_batch_order(paths, order)
    excluded = {index for _name, index in dialogue_png_batch_excluded(paths, order)}
    if type(excluded_index) is not int or excluded_index not in excluded:
        raise ValueError("Bitte zuerst ein ausgeschlossenes PNG-Frame auswählen")
    indexes = list(range(len(paths))) if order is None else list(order)
    indexes.append(excluded_index)
    return tuple(indexes), len(included)


def dialogue_png_batch_preview(raw: str | None, line_id: str | None,
                               paths: list[str] | tuple[str, ...] | None,
                               order: list[int] | tuple[int, ...] | None = None,
                               frame_ids: dict[int, str] | None = None) -> str:
    """Show the exact ordered native frame IDs before one batch import click."""
    if not paths:
        return "Noch keine PNG-Dateien ausgewählt"
    try:
        included = dialogue_png_batch_order(paths, order)
        if not included:
            return "Alle PNG-Dateien aus der Importauswahl entfernt; bitte neue Dateien auswählen"
        entries = dialogue_png_batch_entries(paths, order, frame_ids)
    except ValueError as error:
        return str(error)
    existing = set(dialogue_speaking_frames(raw, line_id)) if raw and line_id else set()
    return "\n".join(f"{i}. {Path(path).name} → {frame_id}"
                     + (" (existiert bereits!)" if frame_id in existing else "")
                     for i, (path, frame_id) in enumerate(entries, 1))


def dialogue_png_batch_thumbnails(paths: list[str] | tuple[str, ...] | None,
                                  order: list[int] | tuple[int, ...] | None = None,
                                  frame_ids: dict[int, str] | None = None
                                  ) -> list[tuple[str, str]]:
    """Display actual uploaded pixels in exactly the prospective COST order."""
    if not paths:
        return []
    included = dialogue_png_batch_order(paths, order)
    return [(path, f"{position}. {dialogue_png_batch_selected_frame_id(paths, order, position - 1, frame_ids)}")
            for position, path in enumerate(included, 1)]


def dialogue_png_batch_image_diagnostics(
        raw: str | None, line_id: str | None, direction: str | None,
        paths: list[str] | tuple[str, ...] | None, target: str | None,
        ending_ticks: int | float = 12, reset_to_stand: bool = True,
        order: list[int] | tuple[int, ...] | None = None,
        frame_ids: dict[int, str] | None = None
        ) -> tuple[list[tuple[str, str]], str]:
    """Locate per-PNG import errors using the real native frame import path."""
    if not paths:
        return [], "Noch keine PNG-Dateien ausgewählt"
    included = dialogue_png_batch_order(paths, order)
    if not included:
        return [], "Die Importauswahl enthält keine Bilder"
    if not raw or not line_id:
        return dialogue_png_batch_thumbnails(paths, order, frame_ids), "Bitte eine Dialogzeile wählen"
    updated = raw
    gallery = []
    failures = []
    indexes = tuple(range(len(paths))) if order is None else tuple(order)
    for position, (path, source_index) in enumerate(zip(included, indexes), 1):
        try:
            default_id = _dialogue_png_batch_entries((path,))[0][1]
            frame_id = frame_ids.get(source_index, default_id) if frame_ids else default_id
            _dialogue_png_batch_entries((path,), (frame_id,))
            updated = import_dialogue_png_frame(updated, line_id, direction,
                                                path, frame_id, target,
                                                ending_ticks, reset_to_stand)
            caption = f"{position}. {frame_id}"
        except (ValueError, OSError) as error:
            caption = f"{position}. {Path(path).name} ⚠️"
            failures.append(f"{position}. {Path(path).name}: {error}")
        gallery.append((path, caption))
    return gallery, ("\n".join(failures) if failures else
                     "Keine bildbezogenen Konflikte erkannt")


def dialogue_png_batch_frame_preview(
        paths: list[str] | tuple[str, ...] | None,
        order: list[int] | tuple[int, ...] | None,
        selected: int | None,
        frame_ids: dict[int, str] | None = None) -> tuple[str | None, str]:
    """Show the chosen staged frame and its position without importing it."""
    if not paths:
        return None, "Noch keine PNG-Dateien ausgewählt"
    included = dialogue_png_batch_order(paths, order)
    if not included:
        return None, "Die Importauswahl enthält keine Bilder"
    if type(selected) is not int or selected not in range(len(included)):
        return None, "Bitte ein PNG in der Importauswahl auswählen"
    frame_id = dialogue_png_batch_selected_frame_id(paths, order, selected, frame_ids)
    return included[selected], (f"Bild {selected + 1} von {len(included)} · "
                                f"{frame_id} · noch nicht importiert")


def step_dialogue_png_batch_frame(
        paths: list[str] | tuple[str, ...] | None,
        order: list[int] | tuple[int, ...] | None,
        selected: int | None, step: int) -> int:
    """Navigate one position in the staged sequence, never wrap silently."""
    included = dialogue_png_batch_order(paths, order)
    if type(step) is not int or step not in (-1, 1):
        raise ValueError("Ungültige Bildnavigation")
    if type(selected) is not int or selected not in range(len(included)):
        raise ValueError("Bitte zuerst ein PNG-Frame auswählen")
    return max(0, min(len(included) - 1, selected + step))


def dialogue_png_batch_animation_preview(
        paths: list[str] | tuple[str, ...] | None,
        order: list[int] | tuple[int, ...] | None,
        duration_ms: int | float, destination: Path,
        frame_ids: dict[int, str] | None = None) -> Path:
    """Animate the staged, unsaved PNG order; never mutate the native project."""
    from PIL import Image

    if (type(duration_ms) not in (int, float) or int(duration_ms) != duration_ms
            or not 40 <= duration_ms <= 2000):
        raise ValueError("Vorschau-Framezeit muss zwischen 40 und 2000 Millisekunden liegen")
    included = dialogue_png_batch_order(paths, order)
    # Use the same filenames/IDs validation as the actual atomic import.
    dialogue_png_batch_entries(paths, order, frame_ids)
    frames = []
    for path in included:
        with Image.open(path) as source:
            if source.format != "PNG":
                raise ValueError(f"Keine PNG-Datei: {Path(path).name}")
            frames.append(source.convert("RGBA"))
    width = max(frame.width for frame in frames)
    height = max(frame.height for frame in frames)
    rendered = []
    for frame in frames:
        canvas = Image.new("RGB", (width, height), (36, 40, 48))
        canvas.paste(frame, ((width - frame.width) // 2,
                             (height - frame.height) // 2), frame)
        rendered.append(canvas)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rendered[0].save(destination, format="GIF", save_all=True,
                     append_images=rendered[1:], duration=int(duration_ms),
                     loop=0, optimize=False, disposal=2)
    return destination


def import_dialogue_png_batch(raw: str, line_id: str, direction: str,
                              paths: list[str] | tuple[str, ...] | None, target: str,
                              ending_ticks: int | float = 12,
                              reset_to_stand: bool = True,
                              order: list[int] | tuple[int, ...] | None = None,
                              frame_ids: dict[int, str] | None = None) -> str:
    """Import all PNGs in selection order, committing only the final valid JSON."""
    entries = dialogue_png_batch_entries(paths, order, frame_ids)
    document = parse_document(raw)
    selected = _dialogue_animation_targets(document).get(line_id)
    if selected is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    actor = next(item for item in document.actors if item.id == selected[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    known = {frame.id for frame in costume.frames}
    if any(frame_id in known for _path, frame_id in entries):
        raise ValueError("Mindestens eine PNG-Frame-ID existiert bereits in dieser Costume")
    updated = raw
    for path, frame_id in entries:
        try:
            updated = import_dialogue_png_frame(updated, line_id, direction, path,
                                                frame_id, target, ending_ticks, reset_to_stand)
        except (ValueError, OSError) as error:
            raise ValueError(f"{Path(path).name}: {error}") from error
    return updated


def dialogue_png_batch_preflight(raw: str | None, line_id: str | None,
                                 direction: str | None,
                                 paths: list[str] | tuple[str, ...] | None,
                                 target: str | None, ending_ticks: int | float = 12,
                                 reset_to_stand: bool = True,
                                 order: list[int] | tuple[int, ...] | None = None,
                                 frame_ids: dict[int, str] | None = None
                                 ) -> tuple[bool, str]:
    """Check the real atomic import in memory before exposing its commit action."""
    if not raw or not line_id:
        return False, "Bitte zuerst eine native Sprecher-Dialogzeile auswählen"
    try:
        included = dialogue_png_batch_order(paths, order)
        if not included:
            return False, "Die Importauswahl ist leer; bitte PNGs aufnehmen"
        import_dialogue_png_batch(raw, line_id, direction, paths, target,
                                  ending_ticks, reset_to_stand, order, frame_ids)
    except (ValueError, OSError) as error:
        return False, f"Import blockiert: {error}"
    return True, f"Importbereit: {len(included)} PNG-Frame(s) für {target} · {direction}"


def dialogue_ending_timeline_preview(raw: str, line_id: str, direction: str,
                                     duration_ms: int | float, destination: Path) -> Path:
    """Editor-only GIF of an authored native ending sequence."""
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    if target is None or cue is None or cue.ending_animation is None:
        raise ValueError("Bitte zuerst eine Abschlussgeste für diese Dialogzeile speichern")
    actor = next(item for item in document.actors if item.id == target[1])
    return render_costume_preview(raw, actor.costume, cue.ending_animation,
                                  direction, duration_ms, destination)


def edit_dialogue_animation_phases(raw: str, line_id: str,
                                  start_delay_ticks: int | float,
                                  minimum_animation_ticks: int | float) -> str:
    """Keep the authored gesture active for native script ticks, not UI ms."""
    document = parse_document(raw)
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    if cue is None:
        raise ValueError("Bitte zuerst eine Sprechfolge für diese Dialogzeile zuweisen")
    for label, ticks in (("Vorlauf", start_delay_ticks),
                         ("Mindestlaufzeit", minimum_animation_ticks)):
        if (type(ticks) not in (int, float) or int(ticks) != ticks or ticks < 0):
            raise ValueError(f"{label} benötigt eine nichtnegative ganze Zahl nativer Ticks")
    updated = replace(cue, start_delay_ticks=int(start_delay_ticks),
                      minimum_animation_ticks=int(minimum_animation_ticks))
    return _checked(replace(document, dialogue_animation_cues=tuple(
        updated if item.line_id == line_id else item
        for item in document.dialogue_animation_cues)))


def dialogue_speaking_frame_selection(raw: str, line_id: str | None
                                      ) -> tuple[tuple[str, ...], str | None]:
    """Resolve the saved line-specific pose to its PNG frame for the editor.

    Native COST animations may contain several frames, direction-dependent
    frames or commands. In those cases no single PNG can be truthfully
    preselected; the explicit Costume-animation selector remains available.
    """
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        return (), None
    actor = next(item for item in document.actors if item.id == target[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    frames = tuple(frame.id for frame in costume.frames)
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    animation = next((item for item in costume.animations
                      if cue is not None and item.name == cue.animation), None)
    if animation is None or not animation.directions:
        return frames, None
    commands = {direction.commands for direction in animation.directions}
    if len(commands) != 1:
        return frames, None
    commands_for_pose = next(iter(commands))
    selected = (commands_for_pose[0] if len(commands_for_pose) == 1
                and commands_for_pose[0] in frames else None)
    return frames, selected


def dialogue_speaking_frame_preview(raw: str | None, line_id: str | None,
                                    frame_id: str | None):
    """Preview the selected NPC's actual indexed frame, not a running animation."""
    if not raw or not line_id or not frame_id:
        return None
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        return None
    actor = next(item for item in document.actors if item.id == target[1])
    return render_costume_frame(raw, actor.costume, frame_id)


def dialogue_direction_animation_preview(raw: str | None, line_id: str | None,
                                         animation_name: str | None, direction: str):
    """Show one authored COST animation frame for the selected actor direction.

    This does not approximate a multi-frame native timeline or override the
    line's saved cue. A direction can have its own distinct frame.
    """
    names = {"N": "Nord", "E": "Ost", "S": "Süd", "W": "West"}
    if direction not in names:
        raise ValueError("Bitte eine gültige Blickrichtung (N, E, S, W) wählen")
    if not raw or not line_id:
        return None, "Bitte zuerst eine Sprecher-Dialogzeile wählen"
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        return None, "Die gewählte Dialogzeile hat keinen nativen Sprecher"
    if not animation_name:
        return None, "Keine Costume-Sprechanimation dieser Dialogzeile ausgewählt"
    actor = next(item for item in document.actors if item.id == target[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    animation = next((item for item in costume.animations
                      if item.name == animation_name and item.index is not None
                      and item.index >= 24), None)
    if animation is None:
        return None, "Keine indizierte Sprecheranimation dieser Figur ausgewählt"
    selected = next((item for item in animation.directions
                     if item.direction == direction), None)
    if selected is None:
        return None, f"{animation_name}: keine Animation für {names[direction]}"
    if len(selected.commands) != 1:
        return None, (f"{animation_name} · {names[direction]}: "
                      "mehrere Frames/Kommandos – keine statische Einzelbildvorschau")
    frame_id = selected.commands[0]
    if frame_id not in {frame.id for frame in costume.frames}:
        return None, (f"{animation_name} · {names[direction]}: "
                      "COST-Kommando statt PNG-Frame – keine Einzelbildvorschau")
    # Give the directional view a separate native-pixel card with a direction
    # label. Its image bytes deliberately differ from the uniform PNG picker
    # preview: Gradio may otherwise concurrently rewrite the same cached
    # image file while both independent output components are streaming.
    from PIL import Image, ImageDraw

    frame_preview = render_costume_frame(raw, costume.name, frame_id)
    card = Image.new("RGB", (304, 320), (36, 40, 48))
    card.paste(frame_preview, (24, 40))
    ImageDraw.Draw(card).text((24, 14), f"{names[direction]} · {animation.name}",
                              fill=(240, 240, 240))
    return (card,
            f"{animation_name} · {names[direction]} · Frame {frame_id} "
            "(native Costume-Palette, statische Editor-Vorschau)")


def dialogue_speaking_frames(raw: str, line_id: str | None) -> tuple[str, ...]:
    """Offer only imported frames belonging to the selected native speaker."""
    return dialogue_speaking_frame_selection(raw, line_id)[0]


def dialogue_speaking_sequence_selection(raw: str, line_id: str | None,
                                         direction: str | None = None) -> str:
    """Show saved native frames, either uniformly or for one direction."""
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        return ""
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    if cue is None:
        return ""
    actor = next(item for item in document.actors if item.id == target[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    animation = next((item for item in costume.animations if item.name == cue.animation), None)
    if animation is None or {entry.direction for entry in animation.directions} != {"N", "E", "S", "W"}:
        return ""
    if direction is not None and direction not in ("N", "E", "S", "W"):
        raise ValueError("Bitte eine gültige Blickrichtung N/E/S/W auswählen")
    commands = {entry.commands for entry in animation.directions
                if direction is None or entry.direction == direction}
    frames = {frame.id for frame in costume.frames}
    if len(commands) != 1:
        return ""
    sequence = next(iter(commands))
    return ", ".join(sequence) if all(command in frames for command in sequence) else ""


def dialogue_speaking_draft_save_status(
        raw: str | None, line_id: str | None, direction: str,
        frame_ids: str | None) -> str:
    """Compare unsaved editor frames to this line's persisted native direction."""
    if not raw or not line_id:
        return "Bitte eine Sprecher-Dialogzeile auswählen"
    document = parse_document(raw)
    if _dialogue_animation_targets(document).get(line_id) is None:
        return "Bitte eine Sprecher-Dialogzeile auswählen"
    persisted = dialogue_speaking_sequence_selection(raw, line_id, direction)
    saved_frames = tuple(item.strip() for item in persisted.split(",")) if persisted else ()
    draft_frames = (tuple(item.strip() for item in frame_ids.split(","))
                    if isinstance(frame_ids, str) and frame_ids.strip() else ())
    if draft_frames == saved_frames:
        return "Sprechfolge entspricht dem gespeicherten Stand"
    return "Ungespeicherte Änderungen an der Sprechfolge"


def switch_dialogue_speaking_draft(
        raw: str | None, line_id: str | None, direction: str,
        current_sequence: str | None, session: dict | None) -> tuple[str, dict]:
    """Select the target's session draft without assigning another line's text."""
    previous = dict(session or {})
    drafts = dict(previous.get("drafts", {}))
    target = (parse_document(raw).id, line_id, direction) if raw and line_id else None
    old_target = previous.get("target")
    if old_target and old_target != target and raw and old_target[0] == parse_document(raw).id:
        saved_old = dialogue_speaking_sequence_selection(raw, old_target[1], old_target[2])
        old_value = current_sequence or ""
        if tuple(part.strip() for part in old_value.split(",")) == tuple(
                part.strip() for part in saved_old.split(",")):
            drafts.pop(old_target, None)
        else:
            drafts[old_target] = old_value
    saved_next = (dialogue_speaking_sequence_selection(raw, line_id, direction)
                  if target else "")
    # A saved edit invalidates its session copy; other directions stay intact.
    if target in drafts and tuple(part.strip() for part in drafts[target].split(",")) == tuple(
            part.strip() for part in saved_next.split(",")):
        drafts.pop(target)
    return drafts.get(target, saved_next), {**previous, "target": target, "drafts": drafts}


def record_dialogue_speaking_draft(
        raw: str | None, line_id: str | None, direction: str,
        sequence: str | None, session: dict | None) -> dict:
    """Store an explicit editor edit under its current target, never a prior one."""
    updated = dict(session or {})
    drafts = dict(updated.get("drafts", {}))
    if raw and line_id:
        target = (parse_document(raw).id, line_id, direction)
        saved = dialogue_speaking_sequence_selection(raw, line_id, direction)
        value = sequence or ""
        if tuple(part.strip() for part in value.split(",")) == tuple(
                part.strip() for part in saved.split(",")):
            drafts.pop(target, None)
        else:
            drafts[target] = value
        updated["target"] = target
    updated["drafts"] = drafts
    return updated


def has_unsaved_dialogue_speaking_drafts(
        raw: str | None, line_id: str | None, direction: str,
        sequence: str | None, session: dict | None) -> bool:
    """Include the currently edited field when checking a project switch."""
    return bool(unsaved_dialogue_speaking_draft_targets(
        raw, line_id, direction, sequence, session))


def unsaved_dialogue_speaking_draft_targets(
        raw: str | None, line_id: str | None, direction: str,
        sequence: str | None, session: dict | None) -> tuple[str, ...]:
    """Name the actual unsaved line/direction pairs in a stable author order."""
    return tuple(label for label, _line, _direction in
                 unsaved_dialogue_speaking_draft_entries(
                     raw, line_id, direction, sequence, session))


def unsaved_dialogue_speaking_draft_entries(
        raw: str | None, line_id: str | None, direction: str,
        sequence: str | None, session: dict | None) -> tuple[tuple[str, str, str], ...]:
    """Return labelled unsaved destinations without parsing UI display text."""
    if not raw:
        return ()
    document_id = parse_document(raw).id
    current = record_dialogue_speaking_draft(raw, line_id, direction, sequence, session)
    drafts = current["drafts"]
    names = dict((key, label) for label, key in dialogue_animation_lines(raw))
    directions = {"N": "Nord", "E": "Ost", "S": "Süd", "W": "West"}
    result = []
    for target_id, label in names.items():
        for facing, facing_name in directions.items():
            target = (document_id, target_id, facing)
            if target not in drafts:
                continue
            saved = dialogue_speaking_sequence_selection(raw, target_id, facing)
            changed = tuple(part.strip() for part in drafts[target].split(","))
            persisted = tuple(part.strip() for part in saved.split(","))
            if changed != persisted:
                result.append((f"{label} · {facing_name} ({target_id})",
                               target_id, facing))
    return tuple(result)


def discard_dialogue_speaking_draft(raw: str, line_id: str, direction: str) -> str:
    """Return the persisted line/direction frames, discarding only UI edits."""
    document = parse_document(raw)
    if _dialogue_animation_targets(document).get(line_id) is None:
        raise ValueError("Bitte zuerst eine Sprecher-Dialogzeile auswählen")
    return dialogue_speaking_sequence_selection(raw, line_id, direction)


def discard_selected_dialogue_speaking_draft(
        raw: str | None, line_id: str | None, direction: str,
        sequence: str | None, session: dict | None,
        selected_line: str, selected_direction: str) -> tuple[str, dict]:
    """Discard exactly one listed session draft, preserving the current editor target."""
    allowed = {(target_id, facing) for _, target_id, facing in
               unsaved_dialogue_speaking_draft_entries(
                   raw, line_id, direction, sequence, session)}
    if (selected_line, selected_direction) not in allowed:
        raise ValueError("Der gewählte Entwurf ist nicht mehr ungespeichert")
    updated = record_dialogue_speaking_draft(raw, line_id, direction, sequence, session)
    drafts = dict(updated["drafts"])
    target = (parse_document(raw).id, selected_line, selected_direction)
    drafts.pop(target)
    updated["drafts"] = drafts
    if line_id == selected_line and direction == selected_direction:
        return dialogue_speaking_sequence_selection(raw, selected_line, selected_direction), updated
    return sequence or "", updated


def dialogue_speaking_timeline(raw: str, line_id: str | None, direction: str):
    """Show the selected line's actual native COST direction, in frame order."""
    if direction not in ("N", "E", "S", "W"):
        raise ValueError("Bitte eine gültige Blickrichtung N/E/S/W auswählen")
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        return [], (), ()
    actor = next(item for item in document.actors if item.id == target[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    steps = ()
    images = []
    if cue is not None:
        animation = next((item for item in costume.animations
                          if item.name == cue.animation), None)
        selected = next((item for item in animation.directions
                         if item.direction == direction), None) if animation else None
        if selected is not None:
            steps = selected.commands
            images = costume_timeline_images(raw, costume.name, cue.animation, direction)
    return images, tuple((f"{index + 1}. {step}", index)
                         for index, step in enumerate(steps)), tuple(frame.id for frame in costume.frames)


def edit_dialogue_speaking_timeline(raw: str, line_id: str, direction: str,
                                   step_number: int | float | None, operation: str,
                                   frame_id: str | None = None,
                                   reset_to_stand: bool = True) -> str:
    """Edit one line/facing's PNG frame order using its existing COST slot."""
    _, steps, available = dialogue_speaking_timeline(raw, line_id, direction)
    if not available:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile mit PNG-Costume auswählen")
    saved = dialogue_speaking_sequence_selection(raw, line_id, direction)
    if steps and not saved:
        raise ValueError("Diese Animation enthält native Kommandos; bitte die Costume-Timeline verwenden")
    sequence = [part.strip() for part in saved.split(",")] if saved else []
    if operation == "Anhängen":
        if frame_id not in available:
            raise ValueError("Bitte ein vorhandenes PNG-Frame zum Anhängen auswählen")
        sequence.append(frame_id)
    else:
        if (type(step_number) not in (int, float) or int(step_number) != step_number
                or not 0 <= int(step_number) < len(sequence)):
            raise ValueError("Bitte einen gültigen Sprechframe-Schritt auswählen")
        index = int(step_number)
        if operation == "Entfernen":
            if len(sequence) == 1:
                raise ValueError("Eine native Sprechfolge benötigt mindestens ein PNG-Frame")
            sequence.pop(index)
        elif operation in ("Nach links", "Nach rechts"):
            other = index + (-1 if operation == "Nach links" else 1)
            if not 0 <= other < len(sequence):
                raise ValueError("Sprechframe ist bereits am Rand der Folge")
            sequence[index], sequence[other] = sequence[other], sequence[index]
        else:
            raise ValueError("Unbekannte Sprech-Timeline-Aktion")
    return assign_dialogue_direction_speaking_sequence(
        raw, line_id, direction, ", ".join(sequence), reset_to_stand)


def dialogue_speaking_timeline_preview(raw: str, line_id: str,
                                       direction: str, duration_ms: int | float,
                                       destination: Path) -> Path:
    """Render the saved NPC line as an editor GIF; ScummVM owns native timing."""
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    if cue is None:
        raise ValueError("Bitte zuerst eine Sprechfolge für diese Dialogzeile speichern")
    actor = next(item for item in document.actors if item.id == target[1])
    return render_costume_preview(raw, actor.costume, cue.animation,
                                  direction, duration_ms, destination)


def dialogue_speaking_template_choices(raw: str | None) -> list[str]:
    """Read persisted template names, including after a project reimport."""
    if not raw:
        return []
    return [template.name for template in
            parse_document(raw).speaking_sequence_templates]


def save_dialogue_speaking_template(
        raw: str, line_id: str, name: str, frame_ids: str) -> str:
    """Persist a validated named sequence as optional native-project authoring data."""
    label = name.strip() if isinstance(name, str) else ""
    if not label or len(label) > 80:
        raise ValueError("Vorlagenname muss zwischen 1 und 80 Zeichen enthalten")
    document = parse_document(raw)
    if any(template.name.casefold() == label.casefold()
           for template in document.speaking_sequence_templates):
        raise ValueError("Eine Sprechfolgenvorlage mit diesem Namen existiert bereits")
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte zuerst eine Sprecher-Dialogzeile auswählen")
    if not isinstance(frame_ids, str) or not frame_ids.strip():
        raise ValueError("Bitte zuerst eine Sprechfolge eingeben")
    sequence = tuple(item.strip() for item in frame_ids.split(","))
    actor = next(item for item in document.actors if item.id == target[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    available = {frame.id for frame in costume.frames}
    if any(not item or item not in available for item in sequence):
        raise ValueError("Die Vorlage darf nur vorhandene PNG-Frames enthalten")
    return _checked(replace(document, speaking_sequence_templates=(
        *document.speaking_sequence_templates,
        SpeakingSequenceTemplate(label, costume.name, sequence))))


def dialogue_speaking_template_preview(
        raw: str | None, line_id: str | None, name: str | None
        ) -> tuple[str, bool]:
    """Describe one saved template and its target compatibility before applying."""
    if not raw or not name:
        return "Bitte eine gespeicherte Vorlage auswählen", False
    document = parse_document(raw)
    template = next((item for item in document.speaking_sequence_templates
                     if item.name == name), None)
    if template is None:
        return "Die ausgewählte Vorlage ist im Projekt nicht mehr vorhanden", False
    target = _dialogue_animation_targets(document).get(line_id)
    actor = next((item for item in document.actors
                  if target is not None and item.id == target[1]), None)
    compatible = actor is not None and actor.costume == template.costume
    if actor is None:
        assessment = "Ziel: Bitte eine Sprecher-Dialogzeile auswählen"
    elif not compatible:
        assessment = (f"Ziel: nicht kompatibel (ausgewählte Costume: "
                      f"{actor.costume})")
    else:
        assessment = "Ziel: kompatibel – kann auf diese Dialogzeile angewendet werden"
    frames = "\n".join(f"{index}. {frame}" for index, frame
                        in enumerate(template.frames, start=1))
    return (f"Vorlage: {template.name}\nCostume: {template.costume}\n"
            f"Abspielbilder: {len(template.frames)}\n"
            f"Frame-Reihenfolge:\n{frames}\n{assessment}"), compatible


def dialogue_speaking_draft_step_preview(
        raw: str | None, line_id: str | None, frame_ids: str | None,
        step_index: int | float | None):
    """Preview the actual Costume pixels of one unsaved numbered step."""
    if not raw or not line_id or step_index is None:
        return None
    if not isinstance(frame_ids, str) or not frame_ids.strip():
        return None
    sequence = tuple(item.strip() for item in frame_ids.split(","))
    if (type(step_index) not in (int, float) or not isfinite(step_index)
            or int(step_index) != step_index or not 0 <= int(step_index) < len(sequence)):
        raise ValueError("Bitte einen gültigen Sprechschritt auswählen")
    if not sequence[int(step_index)]:
        raise ValueError("Der gewählte Sprechschritt hat keine Frame-ID")
    return dialogue_speaking_frame_preview(raw, line_id, sequence[int(step_index)])


def edit_dialogue_speaking_draft(
        raw: str, line_id: str, frame_ids: str, operation: str,
        frame_id: str | None = None, step_index: int | float | None = None
        ) -> tuple[str, int | None]:
    """Edit only the visible speaking draft; never persist a costume or cue."""
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte zuerst eine Sprecher-Dialogzeile auswählen")
    actor = next(item for item in document.actors if item.id == target[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    available = {frame.id for frame in costume.frames}
    if not isinstance(frame_ids, str):
        raise ValueError("Bitte eine gültige Sprechfolge eingeben")
    sequence = [part.strip() for part in frame_ids.split(",")] if frame_ids.strip() else []
    if any(not part or part not in available for part in sequence):
        raise ValueError("Die Sprechfolge darf nur vorhandene PNG-Frames enthalten")
    if operation == "Hinzufügen":
        if frame_id not in available:
            raise ValueError("Bitte einen vorhandenen PNG-Frame auswählen")
        sequence.append(frame_id)
        selected = len(sequence) - 1
    else:
        if (type(step_index) not in (int, float) or not isfinite(step_index)
                or int(step_index) != step_index
                or not 0 <= int(step_index) < len(sequence)):
            raise ValueError("Bitte einen vorhandenen Sprechschritt auswählen")
        selected = int(step_index)
        if operation == "Duplizieren":
            sequence.insert(selected + 1, sequence[selected])
            selected += 1
        elif operation in ("Davor einfügen", "Danach einfügen"):
            if frame_id not in available:
                raise ValueError("Bitte einen vorhandenen PNG-Frame auswählen")
            selected += int(operation == "Danach einfügen")
            sequence.insert(selected, frame_id)
        elif operation == "Ersetzen":
            if frame_id not in available:
                raise ValueError("Bitte einen vorhandenen PNG-Frame auswählen")
            sequence[selected] = frame_id
        elif operation == "Entfernen":
            sequence.pop(selected)
            selected = min(selected, len(sequence) - 1) if sequence else None
        elif operation in ("Nach oben", "Nach unten"):
            other = selected + (-1 if operation == "Nach oben" else 1)
            if not 0 <= other < len(sequence):
                raise ValueError("Sprechschritt ist bereits am Rand")
            sequence[selected], sequence[other] = sequence[other], sequence[selected]
            selected = other
        else:
            raise ValueError("Unbekannte Sprechentwurf-Aktion")
    return ", ".join(sequence), selected


def dialogue_speaking_draft_animation_preview(
        raw: str, line_id: str, frame_ids: str,
        frame_duration_ms: int | float, destination: Path) -> Path:
    """Preview the unsaved speaking input with native Costume pixels, read-only."""
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte zuerst eine Sprecher-Dialogzeile auswählen")
    if not isinstance(frame_ids, str) or not frame_ids.strip():
        raise ValueError("Bitte zuerst eine Sprechfolge eingeben")
    actor = next(item for item in document.actors if item.id == target[1])
    sharing = [item.id for item in document.actors
               if item.id != actor.id and item.costume == actor.costume]
    if sharing:
        raise ValueError("Die Costume wird auch von anderen Figuren verwendet: "
                         + ", ".join(sharing) + ". Bitte zuerst eine eigene Costume zuweisen")
    costume = next(item for item in document.costumes if item.name == actor.costume)
    frames = tuple(part.strip() for part in frame_ids.split(","))
    known = {frame.id for frame in costume.frames}
    if any(not frame or frame not in known for frame in frames):
        raise ValueError("Die Sprechfolge darf nur vorhandene PNG-Frames enthalten")
    return render_costume_frame_sequence_preview(
        raw, costume.name, frames, frame_duration_ms, destination)


def dialogue_speaking_template_animation_preview(
        raw: str, line_id: str, name: str, frame_duration_ms: int | float,
        destination: Path) -> Path:
    """Play the saved template's real costume pixels, without assigning it."""
    # Use the same target/Costume guard as the editable-template and apply flows.
    load_dialogue_speaking_template_for_editing(raw, line_id, name)
    document = parse_document(raw)
    template = next(item for item in document.speaking_sequence_templates
                    if item.name == name)
    return render_costume_frame_sequence_preview(
        raw, template.costume, template.frames, frame_duration_ms,
        destination)


def load_dialogue_speaking_template_for_editing(
        raw: str, line_id: str, name: str) -> str:
    """Read one validated project template into an editable sequence, without saving."""
    document = parse_document(raw)
    template = next((item for item in document.speaking_sequence_templates
                     if item.name == name), None)
    if template is None:
        raise ValueError("Bitte eine gespeicherte Sprechfolgenvorlage auswählen")
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte zuerst eine Sprecher-Dialogzeile auswählen")
    actor = next(item for item in document.actors if item.id == target[1])
    if actor.costume != template.costume:
        raise ValueError("Die Vorlage gehört zu einer anderen Costume; "
                         "bitte eine Dialogzeile derselben Costume auswählen")
    return ", ".join(template.frames)


def update_dialogue_speaking_template(
        raw: str, line_id: str, name: str, frame_ids: str) -> str:
    """Replace a persisted template's frames without editing assigned animations."""
    document = parse_document(raw)
    current = next((item for item in document.speaking_sequence_templates
                    if item.name == name), None)
    if current is None:
        raise ValueError("Bitte eine vorhandene Sprechfolgenvorlage auswählen")
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte zuerst eine Sprecher-Dialogzeile auswählen")
    actor = next(item for item in document.actors if item.id == target[1])
    if actor.costume != current.costume:
        raise ValueError("Die Vorlage gehört zu einer anderen Costume; "
                         "bitte eine Dialogzeile derselben Costume auswählen")
    if not isinstance(frame_ids, str) or not frame_ids.strip():
        raise ValueError("Bitte zuerst eine Sprechfolge eingeben")
    sequence = tuple(item.strip() for item in frame_ids.split(","))
    costume = next(item for item in document.costumes if item.name == actor.costume)
    available = {frame.id for frame in costume.frames}
    if any(not frame or frame not in available for frame in sequence):
        raise ValueError("Die Vorlage darf nur vorhandene PNG-Frames enthalten")
    updated = tuple(replace(item, frames=sequence) if item.name == name else item
                    for item in document.speaking_sequence_templates)
    return _checked(replace(document, speaking_sequence_templates=updated))


def rename_dialogue_speaking_template(
        raw: str, line_id: str, name: str, new_name: str) -> str:
    """Rename one persisted template without altering any native speaking cues."""
    document = parse_document(raw)
    current = next((item for item in document.speaking_sequence_templates
                    if item.name == name), None)
    if current is None:
        raise ValueError("Bitte eine vorhandene Sprechfolgenvorlage auswählen")
    label = new_name.strip() if isinstance(new_name, str) else ""
    if not 1 <= len(label) <= 80:
        raise ValueError("Vorlagenname muss zwischen 1 und 80 Zeichen enthalten")
    if any(item.name.casefold() == label.casefold() and item.name != name
           for item in document.speaking_sequence_templates):
        raise ValueError("Eine Sprechfolgenvorlage mit diesem Namen existiert bereits")
    updated = tuple(replace(item, name=label) if item.name == name else item
                    for item in document.speaking_sequence_templates)
    return _checked(replace(document, speaking_sequence_templates=updated))


def delete_dialogue_speaking_template(
        raw: str, line_id: str, name: str) -> str:
    """Remove only the named authoring preset; keep assigned COST animations."""
    document = parse_document(raw)
    if name not in {item.name for item in document.speaking_sequence_templates}:
        raise ValueError("Bitte eine vorhandene Sprechfolgenvorlage auswählen")
    updated = tuple(item for item in document.speaking_sequence_templates
                    if item.name != name)
    return _checked(replace(document, speaking_sequence_templates=updated))


def apply_dialogue_speaking_template(
        raw: str, line_id: str, name: str,
        reset_to_stand: bool = True) -> str:
    """Apply a project template through the ordinary native per-line authoring path."""
    document = parse_document(raw)
    template = next((entry for entry in document.speaking_sequence_templates
                     if entry.name == name), None)
    if template is None:
        raise ValueError("Bitte eine gespeicherte Sprechfolgenvorlage auswählen")
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    actor = next(item for item in document.actors if item.id == target[1])
    if actor.costume != template.costume:
        raise ValueError("Die Vorlage gehört zu einer anderen Costume; "
                         "bitte eine Dialogzeile derselben Costume auswählen")
    return assign_dialogue_speaking_sequence(
        raw, line_id, ", ".join(template.frames), reset_to_stand)


def assign_dialogue_speaking_sequence(raw: str, line_id: str, frame_ids: str,
                                      reset_to_stand: bool = True,
                                      direction: str | None = None) -> str:
    """Save one NPC line's own native looping COST frames, without global edits."""
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    if direction is not None and direction not in ("N", "E", "S", "W"):
        raise ValueError("Bitte eine gültige Blickrichtung N/E/S/W auswählen")
    actor = next(item for item in document.actors if item.id == target[1])
    sharing = [item.id for item in document.actors
               if item.id != actor.id and item.costume == actor.costume]
    if sharing:
        raise ValueError("Die Costume wird auch von anderen Figuren verwendet: "
                         + ", ".join(sharing) + ". Bitte zuerst eine eigene Costume zuweisen")
    costume = next(item for item in document.costumes if item.name == actor.costume)
    if not isinstance(frame_ids, str) or not frame_ids.strip():
        raise ValueError("Bitte eine Folge importierter PNG-Frames eingeben")
    sequence = tuple(item.strip() for item in frame_ids.split(","))
    available = {frame.id for frame in costume.frames}
    if any(not item or item not in available for item in sequence):
        raise ValueError("Die Sprechfolge darf nur vorhandene PNG-Frames enthalten")
    # Stable per-line identity allows re-editing, independent of the selected frames.
    name = "line_" + sha1(line_id.encode("utf-8")).hexdigest()[:12]
    previous = next((item for item in costume.animations if item.name == name), None)
    if any(cue.line_id != line_id and cue.animation == name
           for cue in document.dialogue_animation_cues):
        raise ValueError("Der native Animationsslot gehört bereits zu einer anderen Dialogzeile")
    if previous is None:
        occupied = {item.index for item in costume.animations if item.index is not None}
        index = next((slot for slot in range(28, 253, 4) if slot not in occupied), None)
        if index is None:
            raise ValueError("Keine freien nativen Costume-Animationsslots für Sprechfolgen")
    else:
        if previous.index is None or previous.index < 28:
            raise ValueError("Vorhandene Dialoganimation verwendet einen reservierten Animationsslot")
        index = previous.index
    if direction is None:
        directions = tuple(CostumeDirection(facing, sequence, True)
                           for facing in ("N", "E", "S", "W"))
    else:
        if previous is not None:
            base = previous
        else:
            cue = next((item for item in document.dialogue_animation_cues
                        if item.line_id == line_id), None)
            base_name = cue.animation if cue else "gesture"
            base = next((item for item in costume.animations
                         if item.name == base_name), None)
        if base is None or {item.direction for item in base.directions} != {"N", "E", "S", "W"}:
            raise ValueError("Die Sprechfolge benötigt eine bestehende Animation mit vier Blickrichtungen")
        directions = tuple(CostumeDirection(item.direction, sequence, True)
                           if item.direction == direction else item
                           for item in base.directions)
    animation = CostumeAnimation(name, directions, index)
    updated_costume = replace(costume, animations=tuple(
        item for item in costume.animations if item.name != name) + (animation,))
    updated = canonical_json(replace(document, costumes=tuple(
        updated_costume if item.name == costume.name else item for item in document.costumes)))
    return edit_dialogue_animation(updated, line_id, name, reset_to_stand)


def assign_dialogue_direction_speaking_sequence(raw: str, line_id: str,
                                                direction: str, frame_ids: str,
                                                reset_to_stand: bool = True) -> str:
    """Author one facing of one NPC line without changing the other channels."""
    return assign_dialogue_speaking_sequence(raw, line_id, frame_ids,
                                             reset_to_stand, direction)


def save_all_dialogue_speaking_drafts(
        raw: str | None, line_id: str | None, direction: str,
        sequence: str | None, session: dict | None) -> tuple[str, str, dict, int]:
    """Atomically save all changed line/facing drafts using the native writer."""
    if not raw:
        raise ValueError("Bitte zuerst ein natives Projekt laden")
    entries = unsaved_dialogue_speaking_draft_entries(
        raw, line_id, direction, sequence, session)
    if not entries:
        raise ValueError("Keine ungespeicherten Sprechfolgenentwürfe vorhanden")
    updated_session = record_dialogue_speaking_draft(
        raw, line_id, direction, sequence, session)
    draft_values = updated_session["drafts"]
    document_id = parse_document(raw).id
    updated_raw = raw
    for label, target_line, facing in entries:
        cue = next((item for item in parse_document(updated_raw).dialogue_animation_cues
                    if item.line_id == target_line), None)
        reset = cue.reset_to_stand if cue else True
        try:
            updated_raw = assign_dialogue_direction_speaking_sequence(
                updated_raw, target_line, facing,
                draft_values[(document_id, target_line, facing)], reset)
        except ValueError as error:
            raise ValueError(f"Sprechfolge {label} nicht gespeichert: {error}") from error
    drafts = dict(draft_values)
    for _, target_line, facing in entries:
        drafts.pop((document_id, target_line, facing))
    updated_session = {**updated_session, "drafts": drafts}
    active_sequence = (dialogue_speaking_sequence_selection(
        updated_raw, line_id, direction) if line_id else "")
    return updated_raw, active_sequence, updated_session, len(entries)


def assign_dialogue_speaking_frame(raw: str, line_id: str, frame_id: str,
                                   reset_to_stand: bool = True) -> str:
    """Author a speaker's imported PNG pose and bind it to a dialogue line in one edit."""
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    actor = next(item for item in document.actors if item.id == target[1])
    sharing = [item.id for item in document.actors
               if item.id != actor.id and item.costume == actor.costume]
    if sharing:
        raise ValueError("Die Costume wird auch von anderen Figuren verwendet: "
                         + ", ".join(sharing) + ". Bitte zuerst eine eigene Costume zuweisen")
    costume = next(item for item in document.costumes if item.name == actor.costume)
    if frame_id not in {frame.id for frame in costume.frames}:
        raise ValueError("Bitte ein vorhandenes Costume-Frame als Sprechpose wählen")

    gesture = next((item for item in costume.animations if item.name == "gesture"), None)
    gesture_users = {
        cue.line_id for cue in document.dialogue_animation_cues
        if cue.animation == "gesture"
        and (speaker := _dialogue_animation_targets(document).get(cue.line_id)) is not None
        and next(item for item in document.actors if item.id == speaker[1]).costume == costume.name
    }
    if gesture is None or not gesture_users or gesture_users == {line_id}:
        # The first assignment may replace an unused legacy gesture, while
        # another line's active gesture must never be overwritten.
        updated = set_costume_speaking_pose(raw, actor.costume, frame_id)
        return edit_dialogue_animation(updated, line_id, "gesture", reset_to_stand)

    if all(direction.commands == (frame_id,) for direction in gesture.directions):
        return edit_dialogue_animation(raw, line_id, "gesture", reset_to_stand)

    # A second line must not replace the first line's global talk_start/gesture.
    # Keep a stable animation per imported frame, reusing it on later lines.
    name = "pose_" + frame_id
    previous = next((item for item in costume.animations if item.name == name), None)
    if previous is not None:
        if any(direction.commands != (frame_id,) for direction in previous.directions):
            raise ValueError("Die vorhandene Sprechpose hat einen anderen Frame-Inhalt")
        return edit_dialogue_animation(raw, line_id, name, reset_to_stand)

    occupied = {animation.index for animation in costume.animations if animation.index is not None}
    index = next((slot for slot in range(28, 253, 4) if slot not in occupied), None)
    if index is None:
        raise ValueError("Keine freien nativen Costume-Animationsslots für weitere Sprechposen")
    animation = CostumeAnimation(name, tuple(
        CostumeDirection(direction, (frame_id,), True)
        for direction in ("N", "E", "S", "W")), index)
    updated_costume = replace(costume, animations=(*costume.animations, animation))
    updated = canonical_json(replace(document, costumes=tuple(
        updated_costume if item.name == costume.name else item for item in document.costumes)))
    return edit_dialogue_animation(updated, line_id, name, reset_to_stand)


def edit_dialogue_animation(raw: str, line_id: str, animation: str | None,
                            reset_to_stand: bool = True) -> str:
    document = parse_document(raw)
    if type(reset_to_stand) is not bool:
        raise ValueError("Die Standpose-Einstellung muss aktiviert oder deaktiviert sein")
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    cues = {cue.line_id: cue for cue in document.dialogue_animation_cues}
    if animation is None:
        cues.pop(line_id, None)
    else:
        previous = cues.get(line_id)
        cues[line_id] = (replace(previous, animation=animation,
                                reset_to_stand=reset_to_stand)
                         if previous is not None else
                         DialogueAnimationCue(line_id, target[0], animation, reset_to_stand))
    return _checked(replace(document, dialogue_animation_cues=tuple(
        cues[key] for key in sorted(cues))))


def edit_dialogue_voice(raw: str, line_id: str, language: str,
                        sound_id: str | None, remove: bool = False) -> str:
    """Assign a room VOC to an NPC line or to one selected language."""
    document = parse_document(raw)
    lines = dict((identity, label) for label, identity in dialogue_voice_lines(raw))
    if line_id not in lines:
        raise ValueError("Bitte eine vorhandene Dialogzeile auswählen")
    room = next(room for room in document.rooms
                if line_id.startswith(f"room.{room.name.lower()}."))
    rest = line_id.split(".dialogue.", 1)[1].split(".")
    rule = room.talk_rules[int(rest.pop(0))]
    stage = rule.stages[int(rest[1])] if rest[0] == "stage" else rule
    if rest[0] == "stage":
        rest = rest[2:]
    source = (stage.opening_lines[int(rest[1])] if rest[0] == "opening"
              else stage.choices[int(rest[1])].reply_lines[int(rest[3])])
    cues = {cue.line_id: cue for cue in document.dialogue_voice_cues}
    existing = cues.get(line_id)
    if language == document.default_voice_language:
        if remove:
            cues.pop(line_id, None)
        else:
            cues[line_id] = DialogueVoiceCue(line_id, source, sound_id,
                                            existing.variants if existing else ())
    else:
        if existing is None:
            raise ValueError("Zuerst die Aufnahme der Standardsprache zuordnen")
        variants = dict(existing.variants)
        if remove:
            if language not in variants:
                raise ValueError("Sprachaufnahme existiert nicht")
            del variants[language]
        else:
            variants[language] = sound_id
        cues[line_id] = replace(existing, variants=tuple(sorted(variants.items())))
    return _checked(replace(document, dialogue_voice_cues=tuple(cues[key] for key in sorted(cues))))


def set_default_voice_language(raw: str, language: str) -> str:
    """Choose the project's initial native spoken language."""
    return _checked(replace(parse_document(raw), default_voice_language=language))


def edit_voice_variant(raw: str, identity: str, step_number: int,
                       language: str, sound_id: str | None, subtitle: str | None,
                       remove: bool = False) -> str:
    """Add/replace or remove one translation on a selected spoken sequence step."""
    document = parse_document(raw)
    sequences = list(document.interaction_sequences)
    index = next((i for i, item in enumerate(sequences) if _identity(item) == identity), None)
    if index is None or type(step_number) is not int or not 0 <= step_number < len(sequences[index].steps):
        raise ValueError("Bitte eine bestehende Sprachzeile auswählen")
    steps = list(sequences[index].steps)
    voice = steps[step_number]
    if not isinstance(voice, VoiceLineStep):
        raise ValueError("Der gewählte Schritt ist keine gesprochene Zeile")
    variants = {item.language: item for item in voice.variants}
    if remove:
        if language not in variants:
            raise ValueError("Sprachvariante existiert nicht")
        del variants[language]
    else:
        variants[language] = VoiceVariant(language, sound_id, subtitle)
    steps[step_number] = replace(voice, variants=tuple(variants[key] for key in sorted(variants)))
    sequences[index] = replace(sequences[index], steps=tuple(steps))
    return _checked(replace(document, interaction_sequences=tuple(sequences)))


def compose_story_project(story_raw: str, native_raw: str | None = None) -> str:
    """Combine current authored Story rooms with typed native Actor and verb actions.

    The Story owns the room resources. Only the explicitly supported native
    Actor/Costume/action fields are carried across; all references are validated
    against the freshly compiled Story rooms before a project is returned.
    """
    project = compile_story_to_scumm(parse_story_document(story_raw))
    if native_raw is None:
        return canonical_json(project)
    native = parse_document(native_raw)
    music_by_room = {room.name: room.music_id for room in native.rooms}
    native_by_room = {room.name: room for room in native.rooms}
    rooms = []
    for room in project.rooms:
        previous = native_by_room.get(room.name)
        zplanes = previous.zplanes if previous is not None else ()
        if previous is not None and (zplanes or previous.walkboxes) and (
                room.geometry.room_width != previous.geometry.room_width or
                room.geometry.room_height != previous.geometry.room_height):
            raise ValueError(f"Raum-Z-Maske/Walkbox für {room.name} passt nicht mehr zur Story-Raumgröße")
        # Story regenerates its inventory rules. Preserve the Studio-native gate
        # only when the same item still opens the same local door. Otherwise
        # reject a stale binding instead of silently losing gameplay.
        native_gates = {rule.target_id: rule for rule in previous.use_rules
                        if rule.unlock_walkbox is not None} if previous is not None else {}
        story_rules = []
        for rule in room.use_rules:
            old = native_gates.pop(rule.target_id, None)
            if old is not None:
                if (old.item_id != rule.item_id or not rule.open_target
                        or rule.hide_target or rule.destination_room is not None):
                    raise ValueError(f"Story changed native walkbox gate action: {room.name}/{rule.target_id}")
                rule = replace(rule, unlock_walkbox=old.unlock_walkbox,
                               reversible_walkbox=old.reversible_walkbox)
            story_rules.append(rule)
        if native_gates:
            raise ValueError(f"Story removed native walkbox gate target: {room.name}/{sorted(native_gates)}")
        rooms.append(replace(room, music_id=music_by_room.get(room.name), zplanes=zplanes,
                             walkboxes=previous.walkboxes if previous is not None else (),
                             box_routes=previous.box_routes if previous is not None else (),
                             scale_slots=previous.scale_slots if previous is not None else None,
                             scale_curves=previous.scale_curves if previous is not None else (),
                             use_rules=tuple(story_rules)))
    composed = replace(project, rooms=tuple(rooms),
                       costumes=native.costumes, actors=native.actors,
                       animation_rules=native.animation_rules,
                       animation_input_rules=native.animation_input_rules,
                       animation_triggers=native.animation_triggers,
                       interaction_sequences=native.interaction_sequences,
                       music_assets=native.music_assets,
                       sound_assets=native.sound_assets,
                       default_voice_language=native.default_voice_language,
                       dialogue_voice_cues=native.dialogue_voice_cues)
    composed = replace(composed, dialogue_animation_cues=native.dialogue_animation_cues)
    return canonical_json(composed)


def sequence_choices(raw: str) -> tuple[tuple[str, str], ...]:
    document = parse_document(raw)
    return tuple((f"{item.room} / {item.hotspot_id} / {item.verb}"
                  + (f" [wenn {item.condition_hotspot_id}={item.condition_state}]"
                     if item.condition_hotspot_id is not None else " [sonst/immer]"),
                  _identity(item))
                 for item in document.interaction_sequences)


def sequence_steps(raw: str, identity: str) -> tuple[str, ...]:
    document = parse_document(raw)
    sequence = next((item for item in document.interaction_sequences
                     if _identity(item) == identity), None)
    return tuple(_describe(step) for step in sequence.steps) if sequence else ()


def sequence_condition_fields(raw: str, identity: str | None) -> tuple[str | None, int]:
    sequence = next((item for item in parse_document(raw).interaction_sequences
                     if _identity(item) == identity), None)
    return ((sequence.condition_hotspot_id, sequence.condition_state)
            if sequence and sequence.condition_hotspot_id is not None else (None, 0))


def sequence_skip_enabled(raw: str, identity: str | None) -> bool:
    sequence = next((item for item in parse_document(raw).interaction_sequences
                     if _identity(item) == identity), None)
    return sequence.skippable if sequence else False


def set_sequence_skippable(raw: str, identity: str, enabled: bool) -> str:
    """Enable native Escape override with deterministic final object/Actor states."""
    document = parse_document(raw)
    index = next((i for i, item in enumerate(document.interaction_sequences)
                  if _identity(item) == identity), None)
    if index is None or type(enabled) is not bool:
        raise ValueError("Bitte eine Interaktion und gültige Skip-Einstellung wählen")
    sequences = list(document.interaction_sequences)
    sequences[index] = replace(sequences[index], skippable=enabled)
    return _checked(replace(document, interaction_sequences=tuple(sequences)))


def set_sequence_condition(raw: str, identity: str, hotspot_id: str | None,
                           state: int | float | None) -> str:
    """Set or clear a native object-state guard on an existing verb sequence."""
    document = parse_document(raw)
    index = next((i for i, item in enumerate(document.interaction_sequences)
                  if _identity(item) == identity), None)
    if index is None:
        raise ValueError("Bitte eine vorhandene Interaktion wählen")
    if hotspot_id is None:
        condition_state = None
    elif state is None or type(state) not in (int, float) or int(state) != state:
        raise ValueError("Bedingung benötigt einen ganzen Objektzustand")
    else:
        condition_state = int(state)
    sequences = list(document.interaction_sequences)
    sequences[index] = replace(sequences[index], condition_hotspot_id=hotspot_id,
                               condition_state=condition_state)
    return _checked(replace(document, interaction_sequences=tuple(sequences)))


def duplicate_sequence_variant(raw: str, identity: str, hotspot_id: str | None,
                               state: int | float | None) -> str:
    """Copy the selected action sequence as an independently editable state branch."""
    document = parse_document(raw)
    original = next((item for item in document.interaction_sequences
                     if _identity(item) == identity), None)
    if original is None:
        raise ValueError("Bitte eine vorhandene Interaktion wählen")
    if hotspot_id is None or state is None or type(state) not in (int, float) or int(state) != state:
        raise ValueError("Alternative benötigt ein Objekt und einen ganzen Zustand")
    variant = replace(original, condition_hotspot_id=hotspot_id, condition_state=int(state))
    return _checked(replace(document, interaction_sequences=(*document.interaction_sequences, variant)))


def _identity(sequence: InteractionSequence) -> str:
    base = f"{sequence.room}|{sequence.hotspot_id}|{sequence.verb}"
    return (base if sequence.condition_hotspot_id is None else
            f"{base}|{sequence.condition_hotspot_id}|{sequence.condition_state}")


def _describe(step: AnimateActorStep | DelayStep | ObjectStateStep | MoveActorStep | WalkActorStep | WaitActorStep | FaceActorStep) -> str:
    if isinstance(step, AnimateActorStep):
        return f"Actor {step.actor_id}: {step.animation}"
    if isinstance(step, DelayStep):
        return f"Warten: {step.seconds} s"
    if isinstance(step, MoveActorStep):
        return f"Actor {step.actor_id}: zu ({step.x}, {step.y}) setzen"
    if isinstance(step, WalkActorStep):
        return f"Actor {step.actor_id}: zu ({step.x}, {step.y}) laufen lassen"
    if isinstance(step, WaitActorStep):
        return f"Auf Actor {step.actor_id} warten"
    if isinstance(step, FaceActorStep):
        return f"Actor {step.actor_id}: Richtung {step.direction}"
    if isinstance(step, PickupObjectStep):
        return f"Inventar: {step.hotspot_id} aufnehmen"
    if isinstance(step, CombineInventoryStep):
        return f"Inventar: zu {step.result_id} kombinieren"
    if isinstance(step, ChangeRoomStep):
        return f"Raumwechsel: {step.room}"
    if isinstance(step, MusicCueStep):
        return "Musik starten" if step.operation == "start" else "Musik stoppen"
    if isinstance(step, SoundEffectStep):
        return f"Sound {step.sound_id}: {'starten' if step.operation == 'start' else 'stoppen'}"
    if isinstance(step, VoiceLineStep):
        return (f"Sprachzeile {step.sound_id} ({step.actor_id or 'Ego'}): {step.text}"
                + (" [" + ", ".join(item.language for item in step.variants) + "]"
                   if step.variants else ""))
    return f"Objekt {step.hotspot_id}: Zustand {step.state}"


def project_choices(raw: str, room_name: str | None = None) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    document = parse_document(raw)
    rooms = tuple(room.name for room in document.rooms)
    room = next((room for room in document.rooms if room.name == room_name), document.rooms[0])
    objects = tuple(hotspot.id for hotspot in room.hotspots)
    actors = tuple(actor.id for actor in document.actors if actor.room == room.name)
    return rooms, objects, actors


def actor_animations(raw: str, actor_id: str | None) -> tuple[str, ...]:
    document = parse_document(raw)
    actor = next((actor for actor in document.actors if actor.id == actor_id), None)
    if actor is None:
        return ()
    costume = next(costume for costume in document.costumes if costume.name == actor.costume)
    return tuple(animation.name for animation in costume.animations
                 if animation.index is not None
                 and actor.direction in {direction.direction for direction in animation.directions})


def _build_step(kind: str, actor_id: str | None, animation: str | None,
                target_id: str | None, amount: int | float | None,
                x: int | float | None, y: int | float | None,
                direction: str | None, subtitle: str | None = None):
    if kind == "Actor animieren":
        step = AnimateActorStep(actor_id, animation)
    elif kind == "Objektzustand setzen":
        if amount is None or type(amount) not in (int, float) or int(amount) != amount:
            raise ValueError("Objektzustand muss eine ganze Zahl sein")
        step = ObjectStateStep(target_id, int(amount))
    elif kind == "Gegenstand aufnehmen":
        step = PickupObjectStep(target_id)
    elif kind == "Inventar kombinieren":
        step = CombineInventoryStep(target_id)
    elif kind == "Raum wechseln":
        step = ChangeRoomStep(target_id)
    elif kind == "Musik starten":
        step = MusicCueStep("start")
    elif kind == "Musik stoppen":
        step = MusicCueStep("stop")
    elif kind == "Sound starten":
        step = SoundEffectStep(target_id, "start")
    elif kind == "Sound stoppen":
        step = SoundEffectStep(target_id, "stop")
    elif kind == "Gesprochene Zeile":
        step = VoiceLineStep(target_id, subtitle, actor_id)
    elif kind == "Warten":
        if amount is None or type(amount) not in (int, float) or int(amount) != amount:
            raise ValueError("Wartezeit muss eine ganze Zahl sein")
        step = DelayStep(int(amount))
    elif kind in ("Actor versetzen", "Actor laufen lassen"):
        if (type(x) not in (int, float) or type(y) not in (int, float)
                or int(x) != x or int(y) != y):
            raise ValueError("Actor-Ziel benötigt ganze Pixelkoordinaten")
        step = (MoveActorStep(actor_id, int(x), int(y)) if kind == "Actor versetzen"
                else WalkActorStep(actor_id, int(x), int(y)))
    elif kind == "Auf Actor warten":
        step = WaitActorStep(actor_id)
    elif kind == "Actor drehen":
        step = FaceActorStep(actor_id, direction)
    else:
        raise ValueError("Unbekannter Aktionstyp")
    return step


def append_sequence_step(raw: str, room: str, hotspot_id: str, verb: str,
                         kind: str, actor_id: str | None, animation: str | None,
                         target_id: str | None, amount: int | float | None,
                         x: int | float | None = None, y: int | float | None = None,
                         direction: str | None = None, subtitle: str | None = None) -> str:
    """Append to an existing verb sequence or create it; never silently replace another binding."""
    document = parse_document(raw)
    if verb not in VERBS:
        raise ValueError("Unbekanntes Verb")
    step = _build_step(kind, actor_id, animation, target_id, amount, x, y, direction, subtitle)
    key = (room, hotspot_id, verb)
    sequences = list(document.interaction_sequences)
    index = next((index for index, item in enumerate(sequences)
                  if (item.room, item.hotspot_id, item.verb) == key
                  and item.condition_hotspot_id is None), None)
    if index is None:
        sequences.append(InteractionSequence(room, hotspot_id, verb, (step,)))
    else:
        sequences[index] = replace(sequences[index], steps=(*sequences[index].steps, step))
    return _checked(replace(document, interaction_sequences=tuple(sequences)))


def append_selected_sequence_step(raw: str, identity: str, kind: str,
                                  actor_id: str | None, animation: str | None,
                                  target_id: str | None, amount: int | float | None,
                                  x: int | float | None = None, y: int | float | None = None,
                                  direction: str | None = None, subtitle: str | None = None) -> str:
    """Append to an existing guarded or unguarded variant, preserving its trigger."""
    document = parse_document(raw)
    index = next((i for i, sequence in enumerate(document.interaction_sequences)
                  if _identity(sequence) == identity), None)
    if index is None:
        raise ValueError("Bitte eine vorhandene Interaktion wählen")
    step = _build_step(kind, actor_id, animation, target_id, amount, x, y, direction, subtitle)
    sequences = list(document.interaction_sequences)
    sequences[index] = replace(sequences[index], steps=(*sequences[index].steps, step))
    return _checked(replace(document, interaction_sequences=tuple(sequences)))


def replace_sequence_step(raw: str, identity: str, step_number: int | float | None,
                          kind: str, actor_id: str | None, animation: str | None,
                          target_id: str | None, amount: int | float | None,
                          x: int | float | None = None, y: int | float | None = None,
                          direction: str | None = None, subtitle: str | None = None) -> str:
    """Edit an existing action in place without changing its order or trigger."""
    document = parse_document(raw)
    if step_number is None or type(step_number) not in (int, float) or int(step_number) != step_number:
        raise ValueError("Bitte einen Schritt wählen")
    sequences = list(document.interaction_sequences)
    index = next((i for i, item in enumerate(sequences) if _identity(item) == identity), None)
    if index is None:
        raise ValueError("Bitte eine vorhandene Interaktion wählen")
    steps = list(sequences[index].steps)
    selected = int(step_number)
    if not 0 <= selected < len(steps):
        raise ValueError("Schritt existiert nicht")
    replacement = _build_step(kind, actor_id, animation, target_id, amount, x, y, direction, subtitle)
    if isinstance(steps[selected], VoiceLineStep) and isinstance(replacement, VoiceLineStep):
        replacement = replace(replacement, variants=steps[selected].variants)
    steps[selected] = replacement
    sequences[index] = replace(sequences[index], steps=tuple(steps))
    return _checked(replace(document, interaction_sequences=tuple(sequences)))


def sequence_step_fields(raw: str, identity: str | None, step_number: int | float | None) -> tuple:
    """Load an authored step back into the existing action form."""
    empty = ("Actor animieren", None, None, None, 1, 320, 100, "S", "")
    if not identity or step_number is None:
        return empty
    sequence = next((item for item in parse_document(raw).interaction_sequences
                     if _identity(item) == identity), None)
    if sequence is None or int(step_number) not in range(len(sequence.steps)):
        return empty
    step = sequence.steps[int(step_number)]
    if isinstance(step, AnimateActorStep):
        return ("Actor animieren", step.actor_id, step.animation, None, 1, 320, 100, "S")
    if isinstance(step, MoveActorStep):
        return ("Actor versetzen", step.actor_id, None, None, 1, step.x, step.y, "S")
    if isinstance(step, WalkActorStep):
        return ("Actor laufen lassen", step.actor_id, None, None, 1, step.x, step.y, "S")
    if isinstance(step, WaitActorStep):
        return ("Auf Actor warten", step.actor_id, None, None, 1, 320, 100, "S")
    if isinstance(step, FaceActorStep):
        return ("Actor drehen", step.actor_id, None, None, 1, 320, 100, step.direction)
    if isinstance(step, DelayStep):
        return ("Warten", None, None, None, step.seconds, 320, 100, "S")
    if isinstance(step, PickupObjectStep):
        return ("Gegenstand aufnehmen", None, None, step.hotspot_id, 1, 320, 100, "S")
    if isinstance(step, CombineInventoryStep):
        return ("Inventar kombinieren", None, None, step.result_id, 1, 320, 100, "S")
    if isinstance(step, ChangeRoomStep):
        return ("Raum wechseln", None, None, step.room, 1, 320, 100, "S")
    if isinstance(step, MusicCueStep):
        return ("Musik starten" if step.operation == "start" else "Musik stoppen",
                None, None, None, 1, 320, 100, "S")
    if isinstance(step, SoundEffectStep):
        return ("Sound starten" if step.operation == "start" else "Sound stoppen",
                None, None, step.sound_id, 1, 320, 100, "S")
    if isinstance(step, VoiceLineStep):
        return ("Gesprochene Zeile", step.actor_id, None, step.sound_id,
                1, 320, 100, "S", step.text)
    return ("Objektzustand setzen", None, None, step.hotspot_id, step.state, 320, 100, "S")


def modify_sequence_step(raw: str, identity: str, step_number: int | float | None,
                         direction: str) -> str:
    """Move one authored step or remove it; deleting the last step removes its binding."""
    document = parse_document(raw)
    if step_number is None or type(step_number) not in (int, float) or int(step_number) != step_number:
        raise ValueError("Bitte einen Schritt wählen")
    sequences = list(document.interaction_sequences)
    index = next((i for i, item in enumerate(sequences) if _identity(item) == identity), None)
    if index is None:
        raise ValueError("Bitte eine vorhandene Interaktion wählen")
    steps = list(sequences[index].steps)
    selected = int(step_number)
    if not 0 <= selected < len(steps):
        raise ValueError("Schritt existiert nicht")
    if direction == "Entfernen":
        steps.pop(selected)
    elif direction in ("Nach oben", "Nach unten"):
        other = selected + (-1 if direction == "Nach oben" else 1)
        if not 0 <= other < len(steps):
            raise ValueError("Schritt ist bereits am Rand")
        steps[selected], steps[other] = steps[other], steps[selected]
    else:
        raise ValueError("Unbekannte Bearbeitung")
    if steps:
        sequences[index] = replace(sequences[index], steps=tuple(steps))
    else:
        sequences.pop(index)
    return _checked(replace(document, interaction_sequences=tuple(sequences)))


def _checked(document: GameDocument) -> str:
    encoded = canonical_json(document)
    parse_document(encoded)
    return encoded
