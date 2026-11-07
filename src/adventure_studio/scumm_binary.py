"""Read-only structural verifier for ScummC/SCUMM-v6 room resources.

Chunk lengths are big endian and include their eight-byte header.  SMAP
offsets are little-endian 32-bit values relative to the SMAP chunk start;
ZP offsets are little-endian 16-bit values with zero denoting an empty strip.
This module deliberately does not claim to decode compressed pixel payloads.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    tag: str
    offset: int
    size: int
    children: tuple["Chunk", ...] = ()

    @property
    def end(self) -> int:
        return self.offset + self.size

    def find(self, tag: str) -> tuple["Chunk", ...]:
        return tuple(child for child in self.children if child.tag == tag)


_CONTAINERS = {"LECF", "LFLF", "ROOM", "RMIM", "OBIM", "OBCD", "PALS", "WRAP"}


def _image_container(tag: str) -> bool:
    return len(tag) == 4 and tag[:2] == "IM" and tag[2:].isdigit()


def _children(data: bytes, begin: int, end: int, depth: int) -> tuple[Chunk, ...]:
    if depth > 12:
        raise ValueError("SCUMM chunk nesting exceeds safety limit")
    result = []
    cursor = begin
    while cursor < end:
        if end - cursor < 8:
            raise ValueError(f"Truncated SCUMM chunk header at {cursor}")
        raw_tag = data[cursor:cursor + 4]
        if any(c < 32 or c > 126 for c in raw_tag):
            raise ValueError(f"Invalid SCUMM chunk tag at {cursor}")
        tag = raw_tag.decode("ascii")
        size = int.from_bytes(data[cursor + 4:cursor + 8], "big")
        if size < 8 or size > end - cursor:
            raise ValueError(f"SCUMM chunk {tag} has invalid length at {cursor}")
        nested = ()
        if tag in _CONTAINERS or _image_container(tag):
            nested = _children(data, cursor + 8, cursor + size, depth + 1)
        result.append(Chunk(tag, cursor, size, nested))
        cursor += size
    return tuple(result)


def parse_chunks(data: bytes, *, xor_key: int | None = None) -> tuple[Chunk, ...]:
    """Parse a complete chunk-aligned resource or XOR-obfuscated linked .001.

    ScummC's intermediate .roobj has its own non-chunk preamble and must be
    linked first; this reader targets the final SCUMM chunk representation.
    """
    if not isinstance(data, bytes):
        raise TypeError("SCUMM binary input must be bytes")
    if xor_key is not None:
        if type(xor_key) is not int or not 0 <= xor_key <= 255:
            raise ValueError("Invalid SCUMM XOR key")
        data = bytes(byte ^ xor_key for byte in data)
    return _children(data, 0, len(data), 0)


def _descendants(chunks: tuple[Chunk, ...]):
    for chunk in chunks:
        yield chunk
        yield from _descendants(chunk.children)


def _offsets(data: bytes, chunk: Chunk, count: int, entry_bytes: int, *, zero_ok: bool) -> None:
    if count <= 0 or chunk.size < 8 + entry_bytes * count:
        raise ValueError(f"{chunk.tag} has missing strip offset table")
    floor = 8 + entry_bytes * count
    previous = floor - 1
    for index in range(count):
        p = chunk.offset + 8 + entry_bytes * index
        offset = int.from_bytes(data[p:p + entry_bytes], "little")
        if offset == 0 and zero_ok:
            continue
        if offset < floor or offset >= chunk.size:
            raise ValueError(f"{chunk.tag} strip {index} offset outside compressed payload")
        if offset <= previous:
            raise ValueError(f"{chunk.tag} strip offsets are not strictly increasing")
        previous = offset


def verify_room_binary(data: bytes, *, xor_key: int | None = None) -> tuple[Chunk, ...]:
    """Check room structure, strip offsets, ZP numbering and object ID pairs.

    Returns the parsed tree for inspection.  This checks structure, *not* the
    pixel decoding or visual behavior of the ScummVM interpreter.
    """
    decoded = bytes(byte ^ xor_key for byte in data) if xor_key is not None else data
    chunks = parse_chunks(data, xor_key=xor_key)
    rooms = [c for c in _descendants(chunks) if c.tag in {"ROOM", "room"}]
    if not rooms:
        raise ValueError("No SCUMM ROOM resource found")
    for room in rooms:
        headers = room.find("RMHD")
        if len(headers) != 1 or headers[0].size < 12:
            raise ValueError("ROOM requires one valid RMHD")
        position = headers[0].offset + 8
        width = int.from_bytes(decoded[position:position + 2], "little")
        height = int.from_bytes(decoded[position + 2:position + 4], "little")
        if width == 0 or width % 8 or height == 0:
            raise ValueError("Invalid room image geometry")
        for image in room.find("RMIM"):
            for frame in image.find("IM00"):
                smaps = frame.find("SMAP")
                if len(smaps) != 1:
                    raise ValueError("Background image requires one SMAP")
                _offsets(decoded, smaps[0], width // 8, 4, zero_ok=False)
                zplanes = [c for c in frame.children if c.tag.startswith("ZP")]
                indices = []
                for plane in zplanes:
                    if not plane.tag[2:].isdigit():
                        raise ValueError("Invalid Z-plane tag")
                    indices.append(int(plane.tag[2:]))
                    _offsets(decoded, plane, width // 8, 2, zero_ok=True)
                if indices != list(range(1, len(indices) + 1)):
                    raise ValueError("Z-plane indices must be consecutive from 1")
        image_ids, control_ids = [], []
        for child in room.children:
            if child.tag in {"OBIM", "obim"}:
                headers = child.find("IMHD") or child.find("imhd")
                if len(headers) != 1 or headers[0].size < 24:
                    raise ValueError("Object image requires IMHD")
                p = headers[0].offset + 8
                image_ids.append(int.from_bytes(decoded[p:p + 2], "little"))
                object_width = int.from_bytes(decoded[p + 12:p + 14], "little")
                for frame in child.children:
                    if _image_container(frame.tag):
                        smaps = frame.find("SMAP")
                        if len(smaps) != 1 or object_width == 0 or object_width % 8:
                            raise ValueError("Object image requires valid width and SMAP")
                        _offsets(decoded, smaps[0], object_width // 8, 4, zero_ok=False)
            if child.tag in {"OBCD", "obcd"}:
                headers = child.find("CDHD") or child.find("cdhd")
                if len(headers) != 1 or headers[0].size < 10:
                    raise ValueError("Object control requires CDHD")
                p = headers[0].offset + 8
                control_ids.append(int.from_bytes(decoded[p:p + 2], "little"))
        if len(set(image_ids)) != len(image_ids) or len(set(control_ids)) != len(control_ids):
            raise ValueError("Duplicate object resource IDs")
        if sorted(image_ids) != sorted(control_ids):
            raise ValueError("OBIM/OBCD object IDs differ")
    return chunks
