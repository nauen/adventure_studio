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
        CostumeAnimation("stand", directions),
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
