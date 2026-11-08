"""Original short Creative Voice File used for native sound-effect gameplay checks."""

from __future__ import annotations

import math
import struct


def original_voc_effect(frequency: int = 440, duration_ms: int = 1800) -> bytes:
    """Create mono unsigned 8-bit PCM in a VOC 1.0 block for ScummC's -voc path."""
    if not 100 <= frequency <= 2500 or not 100 <= duration_ms <= 5000:
        raise ValueError("Invalid fixture sound parameters")
    rate = 11025
    samples = bytes(max(0, min(255, round(128 + 48 * math.sin(
        2 * math.pi * frequency * index / rate))))
                    for index in range(rate * duration_ms // 1000))
    version = 0x010A  # ScummC's soun.c accepts exactly this Creative Voice version.
    header = (b"Creative Voice File\x1a" + struct.pack("<HHH", 26, version,
                                                      (0x1233 - version) & 0xFFFF))
    sample_block = (bytes((1,)) + (len(samples) + 2).to_bytes(3, "little")
                    + bytes((256 - 1_000_000 // rate, 0)) + samples)
    return header + sample_block + b"\x00"
