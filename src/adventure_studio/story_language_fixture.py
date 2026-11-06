"""Complete five-language translation of the tiny two-room runtime fixture.

This is a deliberately small, hand-authored integration story; the strings
must never be presented as translations for a user's own adventure.
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
    "de": "der Schlüssel", "fr": "la clé", "ja": "鍵", "pl": "klucz",
}
TRANSLATED_DOOR_NAME = {
    "de": "die Tür", "fr": "la porte", "ja": "扉", "pl": "drzwi",
}
TRANSLATED_DOOR_DESCRIPTION = {
    "de": "Eine verschlossene Tür.",
    "fr": "Une porte fermée.",
    "ja": "閉じた扉。",
    "pl": "Zamknięte drzwi.",
}
TRANSLATED_STAIRS_NAME = {
    "de": "Treppe zum Hafen", "fr": "escalier vers le port",
    "ja": "港への階段", "pl": "schody do portu",
}
TRANSLATED_STAIRS_DESCRIPTION = {
    "de": "Der Weg zurück.", "fr": "Le chemin du retour.",
    "ja": "戻る道。", "pl": "Droga powrotna.",
}
TRANSLATED_KEY_DESCRIPTION = {
    "de": "Ein rostiger Schlüssel.", "fr": "Une clé rouillée.",
    "ja": "さびた鍵。", "pl": "Zardzewiały klucz.",
}
TRANSLATED_DOOR_LOCKED = {
    "de": "Die Tür ist verschlossen.",
    "fr": "La porte est verrouillée.",
    "ja": "扉には鍵がかかっています。",
    "pl": "Drzwi są zamknięte.",
}
TRANSLATED = {
    "room.cellar.goal": TRANSLATED_GOAL,
    "room.harbor.use.0.response": TRANSLATED_DOOR,
    "room.harbor.object.key.label": TRANSLATED_KEY_NAME,
    "room.harbor.object.door.label": TRANSLATED_DOOR_NAME,
    "room.harbor.object.door.description": TRANSLATED_DOOR_DESCRIPTION,
    "room.harbor.object.door.locked": TRANSLATED_DOOR_LOCKED,
    "room.harbor.object.key.description": TRANSLATED_KEY_DESCRIPTION,
    "room.cellar.object.stairs.label": TRANSLATED_STAIRS_NAME,
    "room.cellar.object.stairs.description": TRANSLATED_STAIRS_DESCRIPTION,
}

# mini_story_language_en.json is an English source variant of the tiny story.
# Keep it separate from the original German mini_story.json example, whose
# legacy ASCII literals must remain unchanged for other compatibility tests.
STORY_TRANSLATED = {
    "room.cellar.goal": {
        "de": "Die Kellertür ist jetzt offen.", "en": "The cellar door is open now.",
        "fr": "La porte de la cave est ouverte.", "ja": "地下室の扉が開きました。",
        "pl": "Drzwi do piwnicy są otwarte.",
    },
    "room.harbor.object.door.description": {
        "de": "Die Kellertür ist jetzt offen.", "en": "The cellar door is open now.",
        "fr": "La porte de la cave est ouverte.", "ja": "地下室の扉が開きました。",
        "pl": "Drzwi do piwnicy są otwarte.",
    },
    "room.harbor.object.door.label": {
        "de": "der Ausgang", "en": "the exit", "fr": "la sortie",
        "ja": "出口", "pl": "wyjście",
    },
    "room.harbor.object.door.locked": {
        **TRANSLATED_DOOR_LOCKED, "en": "The door is locked.",
    },
    "room.harbor.object.key.description": {
        "de": "Ein verrosteter Schlüssel.", "en": "A rusty key.",
        "fr": "Une clé rouillée.", "ja": "さびた鍵。",
        "pl": "Zardzewiały klucz.",
    },
    "room.harbor.object.key.label": {
        "de": "Schlüssel", "en": "key", "fr": "clé",
        "ja": "鍵", "pl": "klucz",
    },
    "room.harbor.use.0.response": {
        "de": "Die Kellertür ist jetzt offen.", "en": "The cellar door is open now.",
        "fr": "La porte de la cave est ouverte.", "ja": "地下室の扉が開きました。",
        "pl": "Drzwi do piwnicy są otwarte.",
    },
}


def fixture_catalog(document: GameDocument) -> LanguageCatalog:
    inventory = story_text_inventory(document)
    if set(inventory) == set(TRANSLATED):
        translations, source_language = TRANSLATED, "en"
    elif set(inventory) == set(STORY_TRANSLATED):
        translations, source_language = STORY_TRANSLATED, "en"
    else:
        raise ValueError("Language fixture requires a supported two-room key-and-door story")
    lines = []
    for key, source in inventory.items():
        translated = translations[key]
        lines.append(LocalizedLine(key, tuple(
            (language, source if language == source_language else translated[language])
            for language in LANGUAGES
        )))
    catalog = LanguageCatalog(source_language, LANGUAGES, tuple(lines))
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

