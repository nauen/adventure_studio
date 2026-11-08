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
