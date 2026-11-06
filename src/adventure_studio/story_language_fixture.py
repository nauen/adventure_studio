"""Bounded five-language SCUMM integration fixture, not production translations.

Most fixture strings deliberately reuse their English source. A bounded set
of object names, a description, a response and a goal exercise the runtime
language branches across both rooms.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .localization import LanguageCatalog, LocalizedLine, canonical_catalog_json
from .scumm_project import GameDocument, parse_document
from .story_localization import story_text_inventory, validate_story_catalog


LANGUAGES = ("de", "en", "fr", "ja", "pl")
TRANSLATED_GOAL = {
    "de": "Du hast den Keller erreicht!",
    "fr": "Tu es arrivé à la cave !",
    "ja": "地下室に着きました。",
    "pl": "Dotarłeś do piwnicy!",
}
TRANSLATED_DOOR = {
    "de": "Die Tür ist offen.",
    "fr": "La porte est ouverte.",
    "ja": "扉が開きました。",
    "pl": "Drzwi są otwarte.",
}
TRANSLATED_KEY_NAME = {
    "de": "Schlüssel", "fr": "clé", "ja": "鍵", "pl": "klucz",
}
TRANSLATED_DOOR_NAME = {
    "de": "Tür", "fr": "porte", "ja": "扉", "pl": "drzwi",
}
TRANSLATED_DOOR_DESCRIPTION = {
    "de": "Eine verschlossene Tür.",
    "fr": "Une porte fermée.",
    "ja": "閉じた扉。",
    "pl": "Zamknięte drzwi.",
}
TRANSLATED = {
    "room.cellar.goal": TRANSLATED_GOAL,
    "room.harbor.use.0.response": TRANSLATED_DOOR,
    "room.harbor.object.key.label": TRANSLATED_KEY_NAME,
    "room.harbor.object.door.label": TRANSLATED_DOOR_NAME,
    "room.harbor.object.door.description": TRANSLATED_DOOR_DESCRIPTION,
}


def fixture_catalog(document: GameDocument) -> LanguageCatalog:
    inventory = story_text_inventory(document)
    required = set(TRANSLATED)
    if not required <= inventory.keys():
        raise ValueError("Language fixture requires the two-room key-and-door story")
    lines = []
    for key, source in inventory.items():
        translated = TRANSLATED.get(key, {})
        lines.append(LocalizedLine(key, tuple(
            (language, source if language == "en" else translated.get(language, source))
            for language in LANGUAGES
        )))
    catalog = LanguageCatalog("en", LANGUAGES, tuple(lines))
    validate_story_catalog(document, catalog)
    return catalog


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.story_language_fixture PROJECT_JSON OUTPUT_JSON")
        return 2
    document = parse_document(Path(sys.argv[1]).read_text(encoding="utf-8"))
    data = canonical_catalog_json(fixture_catalog(document))
    output = Path(sys.argv[2])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(data, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

