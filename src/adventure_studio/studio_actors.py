"""Author playable native Actors and Costumes from Studio-uploaded PNG art."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .scumm_costume import CostumeAnimation, CostumeAsset, CostumeDirection, CostumeFrame
from .scumm_project import ActorAsset, canonical_json, parse_document


def costume_names(raw: str) -> tuple[str, ...]:
    return tuple(costume.name for costume in parse_document(raw).costumes)


def actor_summary(raw: str) -> str:
    actors = parse_document(raw).actors
    return "\n".join(f"{actor.id}: {actor.costume} in {actor.room} bei ({actor.x}, {actor.y}), {actor.direction}"
                     for actor in actors) or "Noch keine nativen Actors"


def _costume_image(path: str) -> tuple[int, int, bytes, tuple[tuple[int, int, int], ...]]:
    if not path:
        raise ValueError("Bitte ein PNG-Bild für die Costume auswählen")
    try:
        from PIL import Image
    except ImportError as error:
        raise ValueError("PNG-Import benötigt Pillow (Studio-Abhängigkeit)") from error
    with Image.open(Path(path)) as source:
        if source.format != "PNG":
            raise ValueError("Costume-Bild muss eine PNG-Datei sein")
        image = source.convert("RGBA")
    width, height = image.size
    if not 1 <= width <= 255 or not 1 <= height <= 255:
        raise ValueError("Costume-Frame benötigt 1–255 Pixel Breite und Höhe")
    pixel_bytes = image.tobytes()
    pixels = [tuple(pixel_bytes[index:index + 4])
              for index in range(0, len(pixel_bytes), 4)]
    if any(alpha not in (0, 255) for *_, alpha in pixels):
        raise ValueError("Native Costume unterstützt keine Teiltransparenz; PNG-Alpha muss 0 oder 255 sein")
    colors = [(r, g, b) for r, g, b, alpha in pixels if alpha == 255]
    if not colors:
        raise ValueError("Costume-Frame benötigt sichtbare Pixel")
    distinct = sorted(set(colors))
    if len(distinct) <= 31:
        palette_colors = distinct
        indices = {rgb: index + 1 for index, rgb in enumerate(palette_colors)}
        values = bytes(0 if pixel[3] == 0 else indices[pixel[:3]] for pixel in pixels)
    else:
        # ScummC's selected COST range contains 32 colors, including local
        # index zero for transparency. Quantization is explicit in the UI.
        image_colors = Image.new("RGB", (len(colors), 1))
        image_colors.putdata(colors)
        quantized = image_colors.quantize(colors=31, method=Image.Quantize.MEDIANCUT)
        palette_values = quantized.getpalette()
        used = sorted(set(quantized.tobytes()))
        palette_colors = [tuple(palette_values[i*3:i*3+3]) for i in used]
        mapping = {value: index + 1 for index, value in enumerate(used)}
        opaque_indices = iter(mapping[value] for value in quantized.tobytes())
        values = bytes(0 if pixel[3] == 0 else next(opaque_indices) for pixel in pixels)
    palette = [(0, 0, 0)] * 48
    for index, rgb in enumerate(palette_colors, start=17):
        palette[index] = rgb
    return width, height, values, tuple(palette)


def create_costume(raw: str, png_path: str, name: str) -> str:
    """Create a Costume from actual uploaded art, with a native idle and action pose."""
    document = parse_document(raw)
    width, height, pixels, palette = _costume_image(png_path)
    frame = CostumeFrame("Pose0", width, height, pixels, -width // 2, 1 - height)
    directions = tuple(CostumeDirection(direction, (frame.id,))
                       for direction in ("N", "E", "S", "W"))
    actions = tuple(CostumeDirection(direction, (frame.id,), loop=False)
                    for direction in ("N", "E", "S", "W"))
    costume = CostumeAsset(name, palette, (frame,), (
        CostumeAnimation("stand", directions, 12),
        CostumeAnimation("talk_start", directions, 16),
        CostumeAnimation("talk_stop", directions, 20),
        CostumeAnimation("gesture", actions, 24)))
    return canonical_json(replace(document, costumes=(*document.costumes, costume)))


def costume_summary(raw: str, name: str | None) -> str:
    document = parse_document(raw)
    costume = next((costume for costume in document.costumes if costume.name == name), None)
    if costume is None:
        return "Bitte eine Costume wählen"
    frames = ", ".join(frame.id for frame in costume.frames)
    animations = "\n".join(
        f"{animation.name} ({animation.index if animation.index is not None else 'Standard'}): "
        + "; ".join(f"{direction.direction} = {', '.join(direction.commands)}"
                     for direction in animation.directions)
        for animation in costume.animations)
    return f"Frames: {frames}\nAnimationen:\n{animations}"


def add_costume_frame(raw: str, name: str, png_path: str, frame_id: str) -> str:
    """Add visible artwork without silently recoloring previously authored frames."""
    document = parse_document(raw)
    existing = next((item for item in document.costumes if item.name == name), None)
    if existing is None:
        raise ValueError("Bitte eine vorhandene Costume auswählen")
    width, height, values, imported_palette = _costume_image(png_path)
    used = {pixel for frame in existing.frames for pixel in frame.pixels if pixel}
    palette = list(existing.palette)
    color_indices = {palette[existing.palette_first + index]: index for index in sorted(used)}
    free_indices = iter(index for index in range(1, existing.palette_last - existing.palette_first + 1)
                        if index not in used)
    mapping = {0: 0}
    for source_index in sorted(set(values) - {0}):
        color = imported_palette[16 + source_index]
        if color in color_indices:
            mapping[source_index] = color_indices[color]
        else:
            next_index = next(free_indices, None)
            if next_index is None:
                raise ValueError("Costume-Palette enthält bereits 31 Farben; bitte PNG-Farben angleichen")
            palette[existing.palette_first + next_index] = color
            color_indices[color] = next_index
            mapping[source_index] = next_index
    frame = CostumeFrame(frame_id, width, height,
                         bytes(mapping[value] for value in values), -width // 2, 1 - height)
    updated = replace(existing, palette=tuple(palette), frames=(*existing.frames, frame))
    costumes = tuple(updated if item.name == name else item for item in document.costumes)
    return canonical_json(replace(document, costumes=costumes))


def set_costume_animation(raw: str, costume_name: str, animation_name: str, index: int | float,
                          direction: str, commands: str, loop: bool) -> str:
    """Author a native COST command sequence in one direction of a named animation."""
    document = parse_document(raw)
    costume = next((item for item in document.costumes if item.name == costume_name), None)
    if costume is None:
        raise ValueError("Bitte eine vorhandene Costume auswählen")
    if type(index) not in (int, float) or int(index) != index:
        raise ValueError("Animationsindex muss eine ganze Zahl sein")
    if not isinstance(commands, str) or not commands.strip():
        raise ValueError("Animation benötigt Frame-IDs oder native COST-Kommandos")
    sequence = tuple(token.strip() for token in commands.split(","))
    if any(not token for token in sequence):
        raise ValueError("Animation enthält einen leeren Schritt")
    new_direction = CostumeDirection(direction, sequence, loop)
    animations = list(costume.animations)
    position = next((i for i, item in enumerate(animations) if item.name == animation_name), None)
    if position is None:
        animations.append(CostumeAnimation(animation_name, (new_direction,), int(index)))
    else:
        current = animations[position]
        directions = tuple(item for item in current.directions if item.direction != direction)
        animations[position] = replace(current, index=int(index),
                                       directions=(*directions, new_direction))
    updated = replace(costume, animations=tuple(animations))
    costumes = tuple(updated if item.name == costume_name else item for item in document.costumes)
    return canonical_json(replace(document, costumes=costumes))


def costume_frame_names(raw: str, costume_name: str | None) -> tuple[str, ...]:
    costume = next((item for item in parse_document(raw).costumes if item.name == costume_name), None)
    return tuple(frame.id for frame in costume.frames) if costume else ()


def set_costume_speaking_pose(raw: str, costume_name: str, frame_id: str) -> str:
    """Assign one imported pose to the native dialogue gesture in every direction."""
    document = parse_document(raw)
    costume = next((item for item in document.costumes if item.name == costume_name), None)
    if costume is None:
        raise ValueError("Bitte eine vorhandene Costume auswählen")
    if frame_id not in {frame.id for frame in costume.frames}:
        raise ValueError("Bitte ein vorhandenes Costume-Frame als Sprechpose wählen")
    existing = next((animation for animation in costume.animations if animation.name == "gesture"), None)
    if existing is not None and existing.index not in (None, 24):
        raise ValueError("Die vorhandene gesture-Animation verwendet einen anderen nativen Index")
    stand = next((animation for animation in costume.animations if animation.name == "stand"), None)
    if stand is None or stand.index != 12:
        raise ValueError("Die Sprechpose benötigt eine native stand-Animation mit Index 12")
    for name, index in (("talk_start", 16), ("talk_stop", 20)):
        previous = next((animation for animation in costume.animations if animation.name == name), None)
        if previous is not None and previous.index != index:
            raise ValueError(f"Die native {name}-Animation benötigt Index {index}")
    gesture = CostumeAnimation("gesture", tuple(
        CostumeDirection(direction, (frame_id,), True)
        for direction in ("N", "E", "S", "W")), 24)
    talk_start = CostumeAnimation("talk_start", gesture.directions, 16)
    talk_stop = CostumeAnimation("talk_stop", tuple(
        CostumeDirection(direction.direction, direction.commands, True)
        for direction in stand.directions), 20)
    animations = tuple(animation for animation in costume.animations
                       if animation.name not in ("gesture", "talk_start", "talk_stop"))
    updated = replace(costume, animations=(*animations, talk_start, talk_stop, gesture))
    costumes = tuple(updated if item.name == costume_name else item for item in document.costumes)
    return canonical_json(replace(document, costumes=costumes))


def set_costume_direction_speaking_pose(raw: str, costume_name: str,
                                        direction: str, frame_id: str) -> str:
    """Replace one native speaking direction without changing the other three."""
    return set_costume_direction_speaking_sequence(raw, costume_name, direction, frame_id)


def set_costume_direction_speaking_sequence(raw: str, costume_name: str,
                                            direction: str, frame_ids: str) -> str:
    """Author an ordered, looping native speaking sequence for one direction."""
    document = parse_document(raw)
    costume = next((item for item in document.costumes if item.name == costume_name), None)
    if costume is None:
        raise ValueError("Bitte eine vorhandene Costume auswählen")
    if direction not in ("N", "E", "S", "W"):
        raise ValueError("Bitte eine gültige Blickrichtung N/E/S/W auswählen")
    if not isinstance(frame_ids, str) or not frame_ids.strip():
        raise ValueError("Bitte mindestens ein PNG-Frame für die Sprechfolge wählen")
    sequence = tuple(item.strip() for item in frame_ids.split(","))
    available = {frame.id for frame in costume.frames}
    if any(not item or item not in available for item in sequence):
        raise ValueError("Bitte ein vorhandenes Costume-Frame für jeden Schritt der Sprechfolge wählen")
    by_name = {animation.name: animation for animation in costume.animations}
    for name, index in (("stand", 12), ("talk_start", 16),
                        ("talk_stop", 20), ("gesture", 24)):
        animation = by_name.get(name)
        if animation is None or animation.index != index:
            raise ValueError(f"Die Sprechpose benötigt {name} mit nativem Index {index}")
        if {item.direction for item in animation.directions} != {"N", "E", "S", "W"}:
            raise ValueError(f"Die Animation {name} benötigt alle vier Blickrichtungen")
    replacement = CostumeDirection(direction, sequence, True)
    animations = tuple(replace(animation, directions=tuple(
        replacement if item.direction == direction else item
        for item in animation.directions))
        if animation.name in ("gesture", "talk_start") else animation
        for animation in costume.animations)
    costumes = tuple(replace(costume, animations=animations) if item.name == costume_name
                     else item for item in document.costumes)
    return canonical_json(replace(document, costumes=costumes))


def costume_direction_speaking_frame(raw: str, costume_name: str | None,
                                     direction: str) -> str | None:
    costume = next((item for item in parse_document(raw).costumes
                    if item.name == costume_name), None)
    gesture = next((item for item in costume.animations if item.name == "gesture"), None) if costume else None
    selected = next((item for item in gesture.directions if item.direction == direction), None) if gesture else None
    if selected and len(selected.commands) == 1 and selected.commands[0] in {f.id for f in costume.frames}:
        return selected.commands[0]
    return None


def costume_animation_names(raw: str, costume_name: str | None) -> tuple[str, ...]:
    costume = next((item for item in parse_document(raw).costumes if item.name == costume_name), None)
    return tuple(item.name for item in costume.animations) if costume else ()


def costume_animation_steps(raw: str, costume_name: str | None,
                            animation_name: str | None, direction: str) -> tuple[str, ...]:
    costume = next((item for item in parse_document(raw).costumes if item.name == costume_name), None)
    animation = next((item for item in costume.animations if item.name == animation_name), None) if costume else None
    selected = next((item for item in animation.directions if item.direction == direction), None) if animation else None
    return selected.commands if selected else ()


def costume_timeline_images(raw: str, costume_name: str | None,
                            animation_name: str | None, direction: str):
    """Render real authored frame pixels and native command cards in order."""
    from PIL import Image, ImageDraw

    costume = next((item for item in parse_document(raw).costumes if item.name == costume_name), None)
    if costume is None:
        return []
    frames = {frame.id: frame for frame in costume.frames}
    results = []
    for index, command in enumerate(costume_animation_steps(raw, costume_name, animation_name, direction)):
        if command in frames:
            frame = frames[command]
            pixels = bytes(component for value in frame.pixels for component in
                           ((*costume.palette[costume.palette_first + value], 255)
                            if value else (0, 0, 0, 0)))
            original = Image.frombytes("RGBA", (frame.width, frame.height), pixels)
            scale = min(8, 96 / max(frame.width, frame.height))
            enlarged = original.resize((max(1, round(frame.width * scale)),
                                        max(1, round(frame.height * scale))),
                                       Image.Resampling.NEAREST)
            card = Image.new("RGB", (112, 112), (42, 45, 52))
            card.paste(enlarged, ((112 - enlarged.width) // 2, (112 - enlarged.height) // 2), enlarged)
        else:
            card = Image.new("RGB", (112, 112), (42, 45, 52))
            ImageDraw.Draw(card).text((15, 48), command, fill=(244, 232, 155))
        results.append((card, f"{index + 1}. {command}"))
    return results


def render_costume_frame(raw: str, costume_name: str, frame_id: str):
    """Display an authored native COST bitmap, with its indexed palette.

    This is a still Editor preview. Native animation timing, actor movement,
    and ScummVM's renderer are intentionally not simulated here.
    """
    from PIL import Image

    costume = next((item for item in parse_document(raw).costumes
                    if item.name == costume_name), None)
    if costume is None:
        raise ValueError("Die Costume der Sprecherfigur ist nicht vorhanden")
    frame = next((item for item in costume.frames if item.id == frame_id), None)
    if frame is None:
        raise ValueError("Das gewählte PNG-Frame gehört nicht zur Sprecher-Costume")
    rgba = bytes(channel for value in frame.pixels for channel in
                 ((*costume.palette[costume.palette_first + value], 255)
                  if value else (0, 0, 0, 0)))
    original = Image.frombytes("RGBA", (frame.width, frame.height), rgba)
    scale = min(8, 224 / max(frame.width, frame.height))
    image = original.resize((max(1, round(frame.width * scale)),
                             max(1, round(frame.height * scale))),
                            Image.Resampling.NEAREST)
    canvas = Image.new("RGB", (256, 256), (36, 40, 48))
    canvas.paste(image, ((256 - image.width) // 2,
                         (256 - image.height) // 2), image)
    return canvas


def render_costume_preview(raw: str, costume_name: str, animation_name: str,
                           direction: str, frame_duration_ms: int | float,
                           destination: Path) -> Path:
    """Render authored frame order as a preview GIF, not a SCUMM runtime simulation."""
    document = parse_document(raw)
    costume = next((item for item in document.costumes if item.name == costume_name), None)
    if costume is None:
        raise ValueError("Bitte eine Costume auswählen")
    animation = next((item for item in costume.animations if item.name == animation_name), None)
    if animation is None:
        raise ValueError("Bitte eine Animation auswählen")
    selected = next((item for item in animation.directions if item.direction == direction), None)
    if selected is None:
        raise ValueError("Diese Animation hat keine Frames für die gewählte Richtung")
    return render_costume_frame_sequence_preview(
        raw, costume_name, selected.commands, frame_duration_ms,
        destination, loop=selected.loop)



def render_costume_frame_sequence_preview(
        raw: str, costume_name: str, frame_ids: tuple[str, ...],
        frame_duration_ms: int | float, destination: Path, *, loop: bool = True) -> Path:
    """Render existing native COST pixel frames in order, without project edits."""
    from PIL import Image

    if (type(frame_duration_ms) not in (int, float) or int(frame_duration_ms) != frame_duration_ms
            or not 40 <= frame_duration_ms <= 2000):
        raise ValueError("Vorschau-Framezeit muss zwischen 40 und 2000 Millisekunden liegen")
    document = parse_document(raw)
    costume = next((item for item in document.costumes if item.name == costume_name), None)
    if costume is None:
        raise ValueError("Bitte eine vorhandene Costume auswählen")
    by_id = {frame.id: frame for frame in costume.frames}
    frames = [by_id[command] for command in frame_ids if command in by_id]
    if not frames:
        raise ValueError("Die Animationsfolge enthält keine darstellbaren Frames")
    # All poses share the same native actor origin. A fixed canvas and nearest-
    # neighbor scaling retain the relative frame offsets and pixel-art edges.
    left = min(frame.offset_x for frame in frames)
    top = min(frame.offset_y for frame in frames)
    right = max(frame.offset_x + frame.width for frame in frames)
    bottom = max(frame.offset_y + frame.height for frame in frames)
    scale = min(8, 224 / max(right - left, bottom - top))
    rendered = []
    for frame in frames:
        rgba = bytes(channel for value in frame.pixels for channel in
                     ((*costume.palette[costume.palette_first + value], 255)
                      if value else (0, 0, 0, 0)))
        original = Image.frombytes("RGBA", (frame.width, frame.height), rgba)
        image = original.resize((max(1, round(frame.width * scale)),
                                 max(1, round(frame.height * scale))), Image.Resampling.NEAREST)
        canvas = Image.new("RGB", (256, 256), (36, 40, 48))
        x = round((256 - (right - left) * scale) / 2 + (frame.offset_x - left) * scale)
        y = round((256 - (bottom - top) * scale) / 2 + (frame.offset_y - top) * scale)
        canvas.paste(image, (x, y), image)
        rendered.append(canvas)
    destination.parent.mkdir(parents=True, exist_ok=True)
    options = {"save_all": True, "append_images": rendered[1:],
               "duration": int(frame_duration_ms), "optimize": False, "disposal": 2}
    if loop:
        options["loop"] = 0
    rendered[0].save(destination, format="GIF", **options)
    return destination


def edit_costume_timeline(raw: str, costume_name: str, animation_name: str,
                          direction: str, step_number: int | float | None,
                          operation: str, command: str | None = None) -> str:
    """Edit the selected native command sequence, preserving other directions."""
    document = parse_document(raw)
    costume = next((item for item in document.costumes if item.name == costume_name), None)
    if costume is None:
        raise ValueError("Bitte eine Costume auswählen")
    animation = next((item for item in costume.animations if item.name == animation_name), None)
    if animation is None:
        raise ValueError("Bitte eine vorhandene Animation auswählen")
    selected = next((item for item in animation.directions if item.direction == direction), None)
    if selected is None:
        raise ValueError("Die gewählte Animation hat noch keine Folge für diese Richtung")
    commands = list(selected.commands)
    if operation == "Anhängen":
        if command is None:
            raise ValueError("Bitte ein Frame oder COST-Kommando wählen")
        commands.append(command)
    else:
        if (step_number is None or type(step_number) not in (int, float)
                or int(step_number) != step_number or not 0 <= int(step_number) < len(commands)):
            raise ValueError("Bitte einen gültigen Animationsschritt auswählen")
        index = int(step_number)
        if operation == "Entfernen":
            if len(commands) == 1:
                raise ValueError("Eine native Richtung benötigt mindestens einen Animationsschritt")
            commands.pop(index)
        elif operation in ("Nach oben", "Nach unten"):
            other = index + (-1 if operation == "Nach oben" else 1)
            if not 0 <= other < len(commands):
                raise ValueError("Animationsschritt ist bereits am Rand")
            commands[index], commands[other] = commands[other], commands[index]
        else:
            raise ValueError("Unbekannte Timeline-Aktion")
    updated_direction = replace(selected, commands=tuple(commands))
    updated_animation = replace(animation, directions=tuple(
        updated_direction if item.direction == direction else item for item in animation.directions))
    updated_costume = replace(costume, animations=tuple(
        updated_animation if item.name == animation_name else item for item in costume.animations))
    costumes = tuple(updated_costume if item.name == costume_name else item for item in document.costumes)
    return canonical_json(replace(document, costumes=costumes))


def add_actor(raw: str, actor_id: str, costume_name: str, room: str, x: int | float,
              y: int | float, direction: str, display_name: str) -> str:
    document = parse_document(raw)
    if (type(x) not in (int, float) or type(y) not in (int, float)
            or int(x) != x or int(y) != y):
        raise ValueError("Actor-Position benötigt ganze Pixelkoordinaten")
    actor = ActorAsset(actor_id, costume_name, room, int(x), int(y), direction,
                       display_name or None)
    return canonical_json(replace(document, actors=(*document.actors, actor)))


def move_actor(raw: str, actor_id: str, room: str, x: int | float, y: int | float,
               direction: str) -> str:
    document = parse_document(raw)
    if (type(x) not in (int, float) or type(y) not in (int, float)
            or int(x) != x or int(y) != y):
        raise ValueError("Actor-Position benötigt ganze Pixelkoordinaten")
    actors = tuple(replace(actor, room=room, x=int(x), y=int(y), direction=direction)
                   if actor.id == actor_id else actor for actor in document.actors)
    if not any(actor.id == actor_id for actor in document.actors):
        raise ValueError("Unbekannter Actor")
    return canonical_json(replace(document, actors=actors))


def set_actor_costume(raw: str, actor_id: str, costume_name: str) -> str:
    """Bind an existing Story or native Actor to an authored COST resource."""
    document = parse_document(raw)
    actor = next((actor for actor in document.actors if actor.id == actor_id), None)
    if actor is None:
        raise ValueError("Unbekannter Actor")
    costume = next((item for item in document.costumes if item.name == costume_name), None)
    if costume is None:
        raise ValueError("Bitte eine vorhandene Costume auswählen")
    if (actor.initial_animation is not None
            and actor.initial_animation not in {animation.name for animation in costume.animations}):
        raise ValueError("Die Startanimation des Actors fehlt in der gewählten Costume")
    actors = tuple(replace(item, costume=costume_name) if item.id == actor_id else item
                   for item in document.actors)
    return canonical_json(replace(document, actors=actors))


def set_actor_initial_animation(raw: str, actor_id: str, animation: str | None) -> str:
    """Select a native COST animation to play when the Actor first enters the game."""
    document = parse_document(raw)
    if not any(actor.id == actor_id for actor in document.actors):
        raise ValueError("Unbekannter Actor")
    actors = tuple(replace(actor, initial_animation=animation or None)
                   if actor.id == actor_id else actor for actor in document.actors)
    return canonical_json(replace(document, actors=actors))
