"""Author ordered native SCUMM interactions without editing project JSON by hand."""

from __future__ import annotations

from dataclasses import replace

from .scumm_project import (AnimateActorStep, DelayStep, MoveActorStep, WalkActorStep, WaitActorStep,
                            FaceActorStep, GameDocument,
                            InteractionSequence, ObjectStateStep, PickupObjectStep,
                            CombineInventoryStep, ChangeRoomStep,
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
    return tuple((f"{item.room} / {item.hotspot_id} / {item.verb}"
                  + (f" [wenn {item.condition_hotspot_id}={item.condition_state}]"
                     if item.condition_hotspot_id is not None else " [sonst/immer]"),
                  _identity(item))
                 for item in document.interaction_sequences)


def sequence_steps(raw: str, identity: str) -> tuple[str, ...]:
    document = parse_document(raw)
    sequence = next((item for item in document.interaction_sequences
                     if _identity(item) == identity), None)
    return tuple(_describe(step) for step in sequence.steps) if sequence else ()


def sequence_condition_fields(raw: str, identity: str | None) -> tuple[str | None, int]:
    sequence = next((item for item in parse_document(raw).interaction_sequences
                     if _identity(item) == identity), None)
    return ((sequence.condition_hotspot_id, sequence.condition_state)
            if sequence and sequence.condition_hotspot_id is not None else (None, 0))


def sequence_skip_enabled(raw: str, identity: str | None) -> bool:
    sequence = next((item for item in parse_document(raw).interaction_sequences
                     if _identity(item) == identity), None)
    return sequence.skippable if sequence else False


def set_sequence_skippable(raw: str, identity: str, enabled: bool) -> str:
    """Enable native Escape override with deterministic final object/Actor states."""
    document = parse_document(raw)
    index = next((i for i, item in enumerate(document.interaction_sequences)
                  if _identity(item) == identity), None)
    if index is None or type(enabled) is not bool:
        raise ValueError("Bitte eine Interaktion und gültige Skip-Einstellung wählen")
    sequences = list(document.interaction_sequences)
    sequences[index] = replace(sequences[index], skippable=enabled)
    return _checked(replace(document, interaction_sequences=tuple(sequences)))


def set_sequence_condition(raw: str, identity: str, hotspot_id: str | None,
                           state: int | float | None) -> str:
    """Set or clear a native object-state guard on an existing verb sequence."""
    document = parse_document(raw)
    index = next((i for i, item in enumerate(document.interaction_sequences)
                  if _identity(item) == identity), None)
    if index is None:
        raise ValueError("Bitte eine vorhandene Interaktion wählen")
    if hotspot_id is None:
        condition_state = None
    elif state is None or type(state) not in (int, float) or int(state) != state:
        raise ValueError("Bedingung benötigt einen ganzen Objektzustand")
    else:
        condition_state = int(state)
    sequences = list(document.interaction_sequences)
    sequences[index] = replace(sequences[index], condition_hotspot_id=hotspot_id,
                               condition_state=condition_state)
    return _checked(replace(document, interaction_sequences=tuple(sequences)))


def duplicate_sequence_variant(raw: str, identity: str, hotspot_id: str | None,
                               state: int | float | None) -> str:
    """Copy the selected action sequence as an independently editable state branch."""
    document = parse_document(raw)
    original = next((item for item in document.interaction_sequences
                     if _identity(item) == identity), None)
    if original is None:
        raise ValueError("Bitte eine vorhandene Interaktion wählen")
    if hotspot_id is None or state is None or type(state) not in (int, float) or int(state) != state:
        raise ValueError("Alternative benötigt ein Objekt und einen ganzen Zustand")
    variant = replace(original, condition_hotspot_id=hotspot_id, condition_state=int(state))
    return _checked(replace(document, interaction_sequences=(*document.interaction_sequences, variant)))


def _identity(sequence: InteractionSequence) -> str:
    base = f"{sequence.room}|{sequence.hotspot_id}|{sequence.verb}"
    return (base if sequence.condition_hotspot_id is None else
            f"{base}|{sequence.condition_hotspot_id}|{sequence.condition_state}")


def _describe(step: AnimateActorStep | DelayStep | ObjectStateStep | MoveActorStep | WalkActorStep | WaitActorStep | FaceActorStep) -> str:
    if isinstance(step, AnimateActorStep):
        return f"Actor {step.actor_id}: {step.animation}"
    if isinstance(step, DelayStep):
        return f"Warten: {step.seconds} s"
    if isinstance(step, MoveActorStep):
        return f"Actor {step.actor_id}: zu ({step.x}, {step.y}) setzen"
    if isinstance(step, WalkActorStep):
        return f"Actor {step.actor_id}: zu ({step.x}, {step.y}) laufen lassen"
    if isinstance(step, WaitActorStep):
        return f"Auf Actor {step.actor_id} warten"
    if isinstance(step, FaceActorStep):
        return f"Actor {step.actor_id}: Richtung {step.direction}"
    if isinstance(step, PickupObjectStep):
        return f"Inventar: {step.hotspot_id} aufnehmen"
    if isinstance(step, CombineInventoryStep):
        return f"Inventar: zu {step.result_id} kombinieren"
    if isinstance(step, ChangeRoomStep):
        return f"Raumwechsel: {step.room}"
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


def _build_step(kind: str, actor_id: str | None, animation: str | None,
                target_id: str | None, amount: int | float | None,
                x: int | float | None, y: int | float | None,
                direction: str | None):
    if kind == "Actor animieren":
        step = AnimateActorStep(actor_id, animation)
    elif kind == "Objektzustand setzen":
        if amount is None or type(amount) not in (int, float) or int(amount) != amount:
            raise ValueError("Objektzustand muss eine ganze Zahl sein")
        step = ObjectStateStep(target_id, int(amount))
    elif kind == "Gegenstand aufnehmen":
        step = PickupObjectStep(target_id)
    elif kind == "Inventar kombinieren":
        step = CombineInventoryStep(target_id)
    elif kind == "Raum wechseln":
        step = ChangeRoomStep(target_id)
    elif kind == "Warten":
        if amount is None or type(amount) not in (int, float) or int(amount) != amount:
            raise ValueError("Wartezeit muss eine ganze Zahl sein")
        step = DelayStep(int(amount))
    elif kind in ("Actor versetzen", "Actor laufen lassen"):
        if (type(x) not in (int, float) or type(y) not in (int, float)
                or int(x) != x or int(y) != y):
            raise ValueError("Actor-Ziel benötigt ganze Pixelkoordinaten")
        step = (MoveActorStep(actor_id, int(x), int(y)) if kind == "Actor versetzen"
                else WalkActorStep(actor_id, int(x), int(y)))
    elif kind == "Auf Actor warten":
        step = WaitActorStep(actor_id)
    elif kind == "Actor drehen":
        step = FaceActorStep(actor_id, direction)
    else:
        raise ValueError("Unbekannter Aktionstyp")
    return step


def append_sequence_step(raw: str, room: str, hotspot_id: str, verb: str,
                         kind: str, actor_id: str | None, animation: str | None,
                         target_id: str | None, amount: int | float | None,
                         x: int | float | None = None, y: int | float | None = None,
                         direction: str | None = None) -> str:
    """Append to an existing verb sequence or create it; never silently replace another binding."""
    document = parse_document(raw)
    if verb not in VERBS:
        raise ValueError("Unbekanntes Verb")
    step = _build_step(kind, actor_id, animation, target_id, amount, x, y, direction)
    key = (room, hotspot_id, verb)
    sequences = list(document.interaction_sequences)
    index = next((index for index, item in enumerate(sequences)
                  if (item.room, item.hotspot_id, item.verb) == key
                  and item.condition_hotspot_id is None), None)
    if index is None:
        sequences.append(InteractionSequence(room, hotspot_id, verb, (step,)))
    else:
        sequences[index] = replace(sequences[index], steps=(*sequences[index].steps, step))
    return _checked(replace(document, interaction_sequences=tuple(sequences)))


def append_selected_sequence_step(raw: str, identity: str, kind: str,
                                  actor_id: str | None, animation: str | None,
                                  target_id: str | None, amount: int | float | None,
                                  x: int | float | None = None, y: int | float | None = None,
                                  direction: str | None = None) -> str:
    """Append to an existing guarded or unguarded variant, preserving its trigger."""
    document = parse_document(raw)
    index = next((i for i, sequence in enumerate(document.interaction_sequences)
                  if _identity(sequence) == identity), None)
    if index is None:
        raise ValueError("Bitte eine vorhandene Interaktion wählen")
    step = _build_step(kind, actor_id, animation, target_id, amount, x, y, direction)
    sequences = list(document.interaction_sequences)
    sequences[index] = replace(sequences[index], steps=(*sequences[index].steps, step))
    return _checked(replace(document, interaction_sequences=tuple(sequences)))


def replace_sequence_step(raw: str, identity: str, step_number: int | float | None,
                          kind: str, actor_id: str | None, animation: str | None,
                          target_id: str | None, amount: int | float | None,
                          x: int | float | None = None, y: int | float | None = None,
                          direction: str | None = None) -> str:
    """Edit an existing action in place without changing its order or trigger."""
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
    steps[selected] = _build_step(kind, actor_id, animation, target_id, amount, x, y, direction)
    sequences[index] = replace(sequences[index], steps=tuple(steps))
    return _checked(replace(document, interaction_sequences=tuple(sequences)))


def sequence_step_fields(raw: str, identity: str | None, step_number: int | float | None) -> tuple:
    """Load an authored step back into the existing action form."""
    empty = ("Actor animieren", None, None, None, 1, 320, 100, "S")
    if not identity or step_number is None:
        return empty
    sequence = next((item for item in parse_document(raw).interaction_sequences
                     if _identity(item) == identity), None)
    if sequence is None or int(step_number) not in range(len(sequence.steps)):
        return empty
    step = sequence.steps[int(step_number)]
    if isinstance(step, AnimateActorStep):
        return ("Actor animieren", step.actor_id, step.animation, None, 1, 320, 100, "S")
    if isinstance(step, MoveActorStep):
        return ("Actor versetzen", step.actor_id, None, None, 1, step.x, step.y, "S")
    if isinstance(step, WalkActorStep):
        return ("Actor laufen lassen", step.actor_id, None, None, 1, step.x, step.y, "S")
    if isinstance(step, WaitActorStep):
        return ("Auf Actor warten", step.actor_id, None, None, 1, 320, 100, "S")
    if isinstance(step, FaceActorStep):
        return ("Actor drehen", step.actor_id, None, None, 1, 320, 100, step.direction)
    if isinstance(step, DelayStep):
        return ("Warten", None, None, None, step.seconds, 320, 100, "S")
    if isinstance(step, PickupObjectStep):
        return ("Gegenstand aufnehmen", None, None, step.hotspot_id, 1, 320, 100, "S")
    if isinstance(step, CombineInventoryStep):
        return ("Inventar kombinieren", None, None, step.result_id, 1, 320, 100, "S")
    if isinstance(step, ChangeRoomStep):
        return ("Raum wechseln", None, None, step.room, 1, 320, 100, "S")
    return ("Objektzustand setzen", None, None, step.hotspot_id, step.state, 320, 100, "S")


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
