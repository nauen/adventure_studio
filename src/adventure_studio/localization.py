"""Versioned, strict multilingual text catalogue and SCUMM byte planning.

This module deliberately does not promise that a SCUMM charset resource exists.
The returned glyph map is a *requirement* for a future font compiler: text
must not be emitted into a playable game until the matching font is verified.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass


_KEY = re.compile(r"^[a-z][a-z0-9_.-]{0,95}$")
_LANG = re.compile(r"^[a-z]{2}(?:-[A-Z]{2})?$")
_EXTRA_CODES = tuple(range(0x80, 0xFE))  # Reserve ASCII DEL and SCUMM 0xfe/0xff controls.


@dataclass(frozen=True)
class LocalizedLine:
    id: str
    translations: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class LanguageCatalog:
    source_language: str
    languages: tuple[str, ...]
    lines: tuple[LocalizedLine, ...]


@dataclass(frozen=True)
class CharsetPlan:
    """A deterministic glyph inventory; not yet a compiled SCUMM CHAR resource."""

    extra_glyphs: tuple[tuple[str, int], ...]

    def byte_for(self, char: str) -> int:
        if len(char) != 1:
            raise ValueError("A single character is required")
        code = ord(char)
        if 32 <= code <= 126:
            return code
        for glyph, byte in self.extra_glyphs:
            if glyph == char:
                return byte
        raise ValueError(f"Glyph missing from charset plan: U+{code:04X}")


def validate_catalog(catalog: LanguageCatalog) -> None:
    if not _LANG.fullmatch(catalog.source_language):
        raise ValueError("Invalid source language")
    if not 1 <= len(catalog.languages) <= 16 or tuple(sorted(set(catalog.languages))) != catalog.languages:
        raise ValueError("Languages must be sorted, unique and bounded")
    if any(not _LANG.fullmatch(language) for language in catalog.languages):
        raise ValueError("Invalid language code")
    if catalog.source_language not in catalog.languages:
        raise ValueError("Source language is missing")
    if len(catalog.lines) > 2048 or len({line.id for line in catalog.lines}) != len(catalog.lines):
        raise ValueError("Duplicate or excessive text identifiers")
    for line in catalog.lines:
        if not _KEY.fullmatch(line.id):
            raise ValueError(f"Invalid text identifier: {line.id}")
        keys = tuple(language for language, _ in line.translations)
        if keys != catalog.languages:
            raise ValueError(f"Missing or unordered translation for: {line.id}")
        for language, value in line.translations:
            if not value or len(value) > 160:
                raise ValueError(f"Invalid translation length: {line.id}/{language}")
            if any(ord(c) < 32 or 0x7F <= ord(c) <= 0x9F or c in "\\\"" for c in value):
                raise ValueError(f"Unsupported control/escape character: {line.id}/{language}")


def charset_plan(catalog: LanguageCatalog) -> CharsetPlan:
    validate_catalog(catalog)
    extras = sorted({char for line in catalog.lines for _, text in line.translations
                     for char in text if ord(char) > 126})
    if len(extras) > len(_EXTRA_CODES):
        raise ValueError(f"Single-byte SCUMM font capacity exceeded: {len(extras)} extra glyphs")
    return CharsetPlan(tuple(zip(extras, _EXTRA_CODES)))


def encode_scumm_literal(text: str, plan: CharsetPlan) -> str:
    """Compile safe source syntax only; verify matching font before gameplay.

    Extended glyphs are emitted as ScummC's explicit `\\xNN` byte escape.
    ASCII needs no escaping because validate_catalog rejects source escapes.
    """
    if not text or len(text) > 160 or any(ord(c) < 32 or c in "\\\"" for c in text):
        raise ValueError("Invalid SCUMM text")
    parts = []
    for char in text:
        number = plan.byte_for(char)
        parts.append(char if 32 <= number <= 126 else f"\\x{number:02X}")
    return '"' + "".join(parts) + '"'


def scumm_language_dispatch(catalog: LanguageCatalog, line_id: str) -> str:
    """Generate a bounded SCUMM-v6 conditional fragment for a *font-ready* game.

    GameLanguage is a separately declared global integer. Two-letter language
    codes have stable 16-bit identifiers, independent of language list order.
    This is source text, not a runtime-verified game or font declaration.
    """
    plan = charset_plan(catalog)
    line = next((item for item in catalog.lines if item.id == line_id), None)
    if line is None:
        raise ValueError(f"Unknown translation ID: {line_id}")
    if any(len(language) != 2 for language in catalog.languages):
        raise ValueError("SCUMM language dispatch currently supports only two-letter languages")
    branches = []
    for index, (language, value) in enumerate(line.translations):
        literal = encode_scumm_literal(value, plan)
        keyword = "if" if index == 0 else "else if"
        language_code = int.from_bytes(language.encode("ascii"), "big")
        branches.append(f"{keyword} (GameLanguage == {language_code}) egoSay({literal}); /* {language} */")
    branches.append("else egoSay(" + encode_scumm_literal(dict(line.translations)[catalog.source_language], plan)
                    + "); /* default */")
    return "\n".join(branches) + "\n"


def canonical_catalog_json(catalog: LanguageCatalog) -> str:
    validate_catalog(catalog)
    data = {"format_version": 1, "source_language": catalog.source_language,
            "languages": list(catalog.languages),
            "lines": [{"id": line.id, "translations": dict(line.translations)}
                      for line in sorted(catalog.lines, key=lambda item: item.id)]}
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def parse_catalog(raw: str) -> LanguageCatalog:
    if len(raw) > 1_000_000:
        raise ValueError("Translation document exceeds size limit")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("Invalid translation JSON") from error
    if not isinstance(data, dict) or set(data) != {"format_version", "source_language", "languages", "lines"}:
        raise ValueError("Invalid translation document fields")
    if type(data["format_version"]) is not int or data["format_version"] != 1:
        raise ValueError("Unknown translation document version")
    languages = data["languages"]
    lines = data["lines"]
    if not isinstance(languages, list) or not isinstance(lines, list):
        raise ValueError("Invalid translation collections")
    parsed = []
    for entry in lines:
        if not isinstance(entry, dict) or set(entry) != {"id", "translations"}:
            raise ValueError("Invalid translation entry")
        values = entry["translations"]
        if not isinstance(values, dict) or not all(isinstance(k, str) and isinstance(v, str)
                                                   for k, v in values.items()):
            raise ValueError("Invalid translation values")
        parsed.append(LocalizedLine(entry["id"], tuple(sorted(values.items()))))
    catalog = LanguageCatalog(data["source_language"], tuple(languages), tuple(parsed))
    validate_catalog(catalog)
    return catalog
