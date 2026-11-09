"""Image-provider boundary; no external generator is contacted during builds.

Providers deliver *already indexed* pixels.  The existing SCUMM exporter owns
the game-specific asset format and is deliberately independent of providers.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Mapping, Protocol


_KEY = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


@dataclass(frozen=True)
class ImageRequest:
    asset_id: str
    description: str
    width: int
    height: int

    def __post_init__(self) -> None:
        if not _KEY.fullmatch(self.asset_id):
            raise ValueError("Invalid asset ID")
        if not self.description.strip() or len(self.description) > 4000:
            raise ValueError("Missing or oversized image description")
        if any(type(n) is not int or n < 1 or n > 4096 for n in (self.width, self.height)):
            raise ValueError("Invalid image dimensions")


@dataclass(frozen=True)
class IndexedImage:
    pixels: bytes
    palette: tuple[tuple[int, int, int], ...]
    width: int
    height: int
    source_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.pixels, bytes) or len(self.pixels) != self.width * self.height:
            raise ValueError("Indexed pixel buffer length mismatch")
        if not (1 <= len(self.palette) <= 256):
            raise ValueError("Indexed image requires 1..256 palette entries")
        if any(len(rgb) != 3 or any(type(v) is not int or not 0 <= v <= 255 for v in rgb)
               for rgb in self.palette):
            raise ValueError("Invalid RGB palette entry")
        if self.pixels and max(self.pixels) >= len(self.palette):
            raise ValueError("Pixel references an undefined palette index")
        if not self.source_id:
            raise ValueError("Image provenance is required")

    @property
    def digest(self) -> str:
        """Stable content identity, independent of provider and file metadata."""
        palette_bytes = bytes(v for rgb in self.palette for v in rgb)
        payload = self.width.to_bytes(4, "big") + self.height.to_bytes(4, "big")
        payload += len(self.palette).to_bytes(2, "big") + palette_bytes + self.pixels
        return hashlib.sha256(payload).hexdigest()


class ImageProvider(Protocol):
    def generate(self, request: ImageRequest) -> IndexedImage: ...


class FixtureImageProvider:
    """Reproducible, offline provider for development and CI.

    Later providers may call ComfyUI, but must return the same IndexedImage
    contract. Their results must be persisted before building SCUMM resources.
    """

    def __init__(self, assets: Mapping[str, IndexedImage]) -> None:
        self._assets = dict(assets)

    def generate(self, request: ImageRequest) -> IndexedImage:
        try:
            image = self._assets[request.asset_id]
        except KeyError as exc:
            raise ValueError(f"Missing generated asset: {request.asset_id}") from exc
        if (image.width, image.height) != (request.width, request.height):
            raise ValueError(f"Asset dimensions disagree with request: {request.asset_id}")
        return image
