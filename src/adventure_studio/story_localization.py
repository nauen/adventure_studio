"""Stable translation IDs for strings emitted by the SCUMM story compiler.

This inventory is a preparation gate. It does not inject translated strings
into SCUMM source until the interpreter charset tests have been approved.
"""

from __future__ import annotations

import json
import re

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
            if hotspot.exit_destination is not None and hotspot.open_sprite_pixels is not None:
                add(f"{base}.locked", "The door is locked.")
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
            for stage_index, stage in enumerate(dialogue.stages):
                stage_base = f"{base}.stage.{stage_index}"
                for line_index, line in enumerate(stage.opening_lines):
                    add(f"{stage_base}.opening.{line_index}", line)
                for choice_index, choice in enumerate(stage.choices):
                    choice_base = f"{stage_base}.choice.{choice_index}"
                    add(f"{choice_base}.caption", choice.caption)
                    for line_index, line in enumerate(choice.reply_lines):
                        add(f"{choice_base}.reply.{line_index}", line)
    return dict(sorted(result.items()))



def story_translation_template(
    document: GameDocument,
    source_language: str = "en",
    languages: tuple[str, ...] = ("de", "en", "fr", "ja", "pl"),
) -> dict:
    """Create an incomplete, editable v1 catalogue draft, never a valid package.

    None marks untranslated text explicitly. parse_catalog intentionally
    rejects this draft until every target language has been supplied.
    """
    if (not re.fullmatch(r"[a-z]{2}", source_language)
            or not languages or tuple(sorted(set(languages))) != languages
            or source_language not in languages
            or any(not re.fullmatch(r"[a-z]{2}", language) for language in languages)):
        raise ValueError("Invalid translation template languages")
    return {
        "format_version": 1,
        "source_language": source_language,
        "languages": list(languages),
        "lines": [
            {"id": key,
             "translations": {language: text if language == source_language else None
                              for language in languages}}
            for key, text in story_text_inventory(document).items()
        ],
    }


def story_translation_template_json(document: GameDocument,
                                    source_language: str = "en") -> str:
    """Return a byte-stable UTF-8 translation draft for an editor/export."""
    return json.dumps(story_translation_template(document, source_language), ensure_ascii=False,
                      sort_keys=True, separators=(",", ":")) + "\n"



def source_matches_compiled(source: str, compiled: str) -> bool:
    """Allow authored Unicode when it normalizes to this old ASCII fixture."""
    if source == compiled:
        return True
    from .story_to_scumm import _text
    try:
        return _text(source) == compiled
    except ValueError:
        return False


def story_authoring_template(story, source_language: str = "en") -> dict:
    """Retain the author's Unicode where text has a stable SCUMM counterpart."""
    from .story_to_scumm import _text, compile_story_to_scumm

    document = compile_story_to_scumm(story)
    template = story_translation_template(document, source_language)
    candidates = {}
    for value in (
        *(item.name for item in story.items),
        *(item.description for item in story.items),
        *(actor.name for actor in story.characters),
        *(actor.description for actor in story.characters),
        *(puzzle.title for puzzle in story.puzzles),
        *(recipe.title for recipe in story.recipes),
        *(node.text for node in story.dialogue_nodes),
        *(choice.text for choice in story.dialogue_choices),
    ):
        try:
            normalized = _text(value)
        except ValueError:
            continue
        candidates.setdefault(normalized, set()).add(value)
    exact = {}
    for item in story.items:
        base = f"room.{item.scene_id.lower()}.object.{item.id.lower()}"
        exact[f"{base}.label"] = item.name
        exact[f"{base}.description"] = item.description
    for actor in story.characters:
        base = f"room.{actor.scene_id.lower()}.object.{actor.id.lower()}"
        exact[f"{base}.label"] = actor.name
        exact[f"{base}.description"] = actor.description

    for line in template["lines"]:
        key = line["id"]
        compiled = line["translations"][source_language]
        if key in exact:
            original = exact[key]
        else:
            possibilities = candidates.get(compiled, set())
            original = next(iter(possibilities)) if len(possibilities) == 1 else compiled
        if not source_matches_compiled(original, compiled):
            raise ValueError(f"Authoring text no longer matches SCUMM source: {key}")
        line["translations"][source_language] = original
    return template


def story_authoring_template_json(story, source_language: str = "en") -> str:
    return json.dumps(story_authoring_template(story, source_language),
                      ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


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
        if not source_matches_compiled(actual[key][catalog.source_language], source_text):
            raise ValueError(f"Source translation differs from story: {key}")
