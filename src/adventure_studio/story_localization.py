"""Stable translation IDs for strings emitted by the SCUMM story compiler.

This inventory is a preparation gate. It does not inject translated strings
into SCUMM source until the interpreter charset tests have been approved.
"""

from __future__ import annotations

from .localization import LanguageCatalog, validate_catalog
from .scumm_project import GameDocument, _validate_document


def story_text_inventory(document: GameDocument) -> dict[str, str]:
    """Enumerate visible text without relying on mutable display labels."""
    _validate_document(document)
    result: dict[str, str] = {}

    def add(key: str, value: str) -> None:
        if key in result:
            raise ValueError(f"Translation ID collision: {key}")
        if not value:
            return
        if len(key) > 96:
            raise ValueError(f"Translation ID too long: {key}")
        result[key] = value

    for room in document.rooms:
        prefix = f"room.{room.name.lower()}"
        if room.goal_text is not None:
            add(f"{prefix}.goal", room.goal_text)
        for hotspot in room.hotspots:
            base = f"{prefix}.object.{hotspot.id.lower()}"
            add(f"{base}.label", hotspot.label)
            add(f"{base}.description", hotspot.description)
            for index, line in enumerate(hotspot.talk_lines):
                add(f"{base}.talk.{index}", line)
        for index, rule in enumerate(room.use_rules):
            add(f"{prefix}.use.{index}.response", rule.response)
        for index, rule in enumerate(room.combine_rules):
            add(f"{prefix}.combine.{index}.response", rule.response)
        for index, dialogue in enumerate(room.talk_rules):
            base = f"{prefix}.dialogue.{index}"
            for line_index, line in enumerate(dialogue.opening_lines):
                add(f"{base}.opening.{line_index}", line)
            for choice_index, choice in enumerate(dialogue.choices):
                choice_base = f"{base}.choice.{choice_index}"
                add(f"{choice_base}.caption", choice.caption)
                for line_index, line in enumerate(choice.reply_lines):
                    add(f"{choice_base}.reply.{line_index}", line)
    return dict(sorted(result.items()))


def validate_story_catalog(document: GameDocument, catalog: LanguageCatalog) -> None:
    """Require exact coverage and unchanged source-language text."""
    validate_catalog(catalog)
    expected = story_text_inventory(document)
    actual = {line.id: dict(line.translations) for line in catalog.lines}
    missing = sorted(expected.keys() - actual.keys())
    extra = sorted(actual.keys() - expected.keys())
    if missing or extra:
        raise ValueError(f"Story translation IDs mismatch: missing={missing}, extra={extra}")
    for key, source_text in expected.items():
        if actual[key][catalog.source_language] != source_text:
            raise ValueError(f"Source translation differs from story: {key}")
