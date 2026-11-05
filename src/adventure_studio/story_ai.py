"""Untrusted natural-language proposal boundary; never generates game code."""

from __future__ import annotations

import json
from dataclasses import fields, replace
from collections.abc import Callable

from .story import (AssetRef, Chapter, Character, Dialogue, DialogueChoice,
                    DialogueNode, Item, Placement, Puzzle, Recipe, Scene)
from .story_changes import edit_story
from .story_document import canonical_story_json, parse_story_document
from .story_protocol import parse_operations
from .studio_service import StudioEdit, StudioProposal, export_warning, prepare_proposal


SYSTEM_INSTRUCTIONS = """Du bist die Story-Regie für ein SCUMM-v6-Adventure.
Antworte ausschließlich als JSON-Objekt mit dem Schlüssel 'operations' (Liste).
Jede Operation ist entweder:
{'op':'put','kind':'chapter|scene|character|item|puzzle|recipe|placement|dialogue|dialogue_node|dialogue_choice|asset','entity':{...}}
oder {'op':'delete','kind':'chapter|scene|character|item|puzzle|recipe|placement|dialogue|dialogue_node|dialogue_choice|asset','id':'...'}.
Benutze ausschließlich die vorhandenen Datenfelder aus der aktuellen Story.
Für neue Gegenstände: id, name, description, scene_id, role ('decoration' oder 'pickup').
Für Positionen: {'item_id':'ID','x':ganze_Zahl,'y':ganze_Zahl}.
Für Dialoge: Lege erst Sprecher als character an, dann dialogue, dialogue_node
und bei Verzweigungen dialogue_choice. Null beendet eine Gesprächsroute.
Jeder Dialogknoten muss vom Start erreichbar sein und einen möglichen Abschluss haben.
AssetRef speichert nur referenzierte Herkunft und SHA-256-Hash; er erfindet keine Binärdatei.
Bestehende Entities bei Änderungen vollständig mit allen Feldern zurückgeben.
Verwende stabile ASCII-IDs und gültige Referenzen. Maximal 100 Operationen.
Schreibe niemals Python, SCUMM-Skripte, Markdown oder Kommentare.
Lösche keine erzählerisch wichtigen Elemente, es sei denn, der Autor verlangt es.
Wenn die Story nicht eindeutig geändert werden kann, liefere eine leere Liste.
Die Änderungen werden vor einer Übernahme technisch geprüft und angezeigt."""

_ENTITY_SCHEMAS = {"chapter": Chapter, "scene": Scene, "character": Character,
                   "item": Item, "puzzle": Puzzle, "recipe": Recipe, "placement": Placement,
                   "dialogue": Dialogue, "dialogue_node": DialogueNode,
                   "dialogue_choice": DialogueChoice, "asset": AssetRef}


def proposal_messages(raw_story: str, request: str) -> tuple[str, str]:
    """Bound and canonicalize inputs passed to any text-generation provider."""
    if not isinstance(request, str) or not request.strip() or len(request) > 8_000:
        raise ValueError("Bitte einen Änderungswunsch mit maximal 8000 Zeichen eingeben")
    canonical = canonical_story_json(parse_story_document(raw_story))
    if len(canonical) > 150_000:
        raise ValueError("Story ist für diese KI-Vorschau zu groß")
    user = json.dumps({"story": json.loads(canonical), "request": request.strip()}, ensure_ascii=False)
    field_guide = "\nZulässige Entity-Felder (vollständig für put):\n" + "\n".join(
        f"- {kind}: {', '.join(field.name for field in fields(cls))}"
        for kind, cls in _ENTITY_SCHEMAS.items())
    return SYSTEM_INSTRUCTIONS + field_guide, user


def preview_ai_response(raw_story: str, response_json: str) -> StudioProposal:
    """Apply an untrusted response only in memory, with full deterministic gates."""
    operations = parse_operations(response_json)
    if not operations:
        raise ValueError("Der Vorschlag enthält keine Änderungen")
    changed, report = edit_story(parse_story_document(raw_story), operations)
    warning = export_warning(changed)
    canonical = canonical_story_json(changed)
    parse_story_document(canonical)
    return prepare_proposal(raw_story, StudioEdit(canonical, replace(report, export_warning=warning)))


def propose_story_change(raw_story: str, request: str,
                         generate: Callable[[str, str], str]) -> StudioProposal:
    """Provider-injected LLM request, returning a preview rather than a mutation."""
    system, user = proposal_messages(raw_story, request)
    response = generate(system, user)
    if not isinstance(response, str):
        raise ValueError("KI-Antwort ist kein JSON-Text")
    return preview_ai_response(raw_story, response)
