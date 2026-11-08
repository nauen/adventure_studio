"""Author ordered native SCUMM interactions without editing project JSON by hand."""

from __future__ import annotations

from dataclasses import replace

from .scumm_project import (AnimateActorStep, DelayStep, MoveActorStep, GameDocument,
                            InteractionSequence, ObjectStateStep,
                            canonical_json, parse_document)
from .story_document import parse_story_document
from .story_to_scumm import compile_story_to_scumm


VERBS = ("Push", "Pull", "Open", "Close")


def compose_story_project(story_raw: str, native_raw: str | None = None) -> str:
    """Combine current authored Story rooms with typed native Actor and verb actions.

    The Story owns the room resources. Only the explicitly supported native
    Actor/Costume/action fields are carried across; all references are validated
    against the freshly compiled Story rooms before a project is returned.
    """
    project = compile_story_to_scumm(parse_story_document(story_raw))
    if native_raw is None:
        return canonical_json(project)
    native = parse_document(native_raw)
    composed = replace(project, costumes=native.costumes, actors=native.actors,
                       animation_rules=native.animation_rules,
                       animation_input_rules=native.animation_input_rules,
                       animation_triggers=native.animation_triggers,
                       interaction_sequences=native.interaction_sequences)
    return canonical_json(composed)


def sequence_choices(raw: str) -> tuple[tuple[str, str], ...]:
    document = parse_document(raw)
    return tuple((f"{item.room} / {item.hotspot_id} / {item.verb}",
                  f"{item.room}|{item.hotspot_id}|{item.verb}")
                 for item in document.interaction_sequences)


def sequence_steps(raw: str, identity: str) -> tuple[str, ...]:
    document = parse_document(raw)
    sequence = next((item for item in document.interaction_sequences
                     if _identity(item) == identity), None)
    return tuple(_describe(step) for step in sequence.steps) if sequence else ()


def _identity(sequence: InteractionSequence) -> str:
    return f"{sequence.room}|{sequence.hotspot_id}|{sequence.verb}"


def _describe(step: AnimateActorStep | DelayStep | ObjectStateStep | MoveActorStep) -> str:
    if isinstance(step, AnimateActorStep):
        return f"Actor {step.actor_id}: {step.animation}"
    if isinstance(step, DelayStep):
        return f"Warten: {step.seconds} s"
    if isinstance(step, MoveActorStep):
        return f"Actor {step.actor_id}: zu ({step.x}, {step.y}) setzen"
    return f"Objekt {step.hotspot_id}: Zustand {step.state}"


def project_choices(raw: str, room_name: str | None = None) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    document = parse_document(raw)
    rooms = tuple(room.name for room in document.rooms)
    room = next((room for room in document.rooms if room.name == room_name), document.rooms[0])
    objects = tuple(hotspot.id for hotspot in room.hotspots)
    actors = tuple(actor.id for actor in document.actors if actor.room == room.name)
    return rooms, objects, actors


def actor_animations(raw: str, actor_id: str | None) -> tuple[str, ...]:
    document = parse_document(raw)
    actor = next((actor for actor in document.actors if actor.id == actor_id), None)
    if actor is None:
        return ()
    costume = next(costume for costume in document.costumes if costume.name == actor.costume)
    return tuple(animation.name for animation in costume.animations
                 if animation.index is not None
                 and actor.direction in {direction.direction for direction in animation.directions})


def append_sequence_step(raw: str, room: str, hotspot_id: str, verb: str,
                         kind: str, actor_id: str | None, animation: str | None,
                         target_id: str | None, amount: int | float | None,
                         x: int | float | None = None, y: int | float | None = None) -> str:
    """Append to an existing verb sequence or create it; never silently replace another binding."""
    document = parse_document(raw)
    if verb not in VERBS:
        raise ValueError("Unbekanntes Verb")
    if kind == "Actor animieren":
        step = AnimateActorStep(actor_id, animation)
    elif kind == "Objektzustand setzen":
        if amount is None or type(amount) not in (int, float) or int(amount) != amount:
            raise ValueError("Objektzustand muss eine ganze Zahl sein")
        step = ObjectStateStep(target_id, int(amount))
    elif kind == "Warten":
        if amount is None or type(amount) not in (int, float) or int(amount) != amount:
            raise ValueError("Wartezeit muss eine ganze Zahl sein")
        step = DelayStep(int(amount))
    elif kind == "Actor versetzen":
        if (type(x) not in (int, float) or type(y) not in (int, float)
                or int(x) != x or int(y) != y):
            raise ValueError("Actor-Ziel benötigt ganze Pixelkoordinaten")
        step = MoveActorStep(actor_id, int(x), int(y))
    else:
        raise ValueError("Unbekannter Aktionstyp")
    key = (room, hotspot_id, verb)
    sequences = list(document.interaction_sequences)
    index = next((index for index, item in enumerate(sequences)
                  if (item.room, item.hotspot_id, item.verb) == key), None)
    if index is None:
        sequences.append(InteractionSequence(room, hotspot_id, verb, (step,)))
    else:
        sequences[index] = replace(sequences[index], steps=(*sequences[index].steps, step))
    return _checked(replace(document, interaction_sequences=tuple(sequences)))


def modify_sequence_step(raw: str, identity: str, step_number: int | float | None,
                         direction: str) -> str:
    """Move one authored step or remove it; deleting the last step removes its binding."""
    document = parse_document(raw)
    if step_number is None or type(step_number) not in (int, float) or int(step_number) != step_number:
        raise ValueError("Bitte einen Schritt wählen")
    sequences = list(document.interaction_sequences)
    index = next((i for i, item in enumerate(sequences) if _identity(item) == identity), None)
    if index is None:
        raise ValueError("Bitte eine vorhandene Interaktion wählen")
    steps = list(sequences[index].steps)
    selected = int(step_number)
    if not 0 <= selected < len(steps):
        raise ValueError("Schritt existiert nicht")
    if direction == "Entfernen":
        steps.pop(selected)
    elif direction in ("Nach oben", "Nach unten"):
        other = selected + (-1 if direction == "Nach oben" else 1)
        if not 0 <= other < len(steps):
            raise ValueError("Schritt ist bereits am Rand")
        steps[selected], steps[other] = steps[other], steps[selected]
    else:
        raise ValueError("Unbekannte Bearbeitung")
    if steps:
        sequences[index] = replace(sequences[index], steps=tuple(steps))
    else:
        sequences.pop(index)
    return _checked(replace(document, interaction_sequences=tuple(sequences)))


def _checked(document: GameDocument) -> str:
    encoded = canonical_json(document)
    parse_document(encoded)
    return encoded
