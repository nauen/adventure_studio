"""Author ordered native SCUMM interactions without editing project JSON by hand."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .scumm_project import (AnimateActorStep, DelayStep, MoveActorStep, WalkActorStep, WaitActorStep,
                            FaceActorStep, GameDocument,
                            InteractionSequence, ObjectStateStep, PickupObjectStep,
                            CombineInventoryStep, ChangeRoomStep, MusicCueStep, MusicAsset,
                            SoundAsset, SoundEffectStep, VoiceLineStep, VoiceVariant,
                            DialogueVoiceCue, DialogueAnimationCue,
                            canonical_json, parse_document)
from .story_document import parse_story_document
from .story_to_scumm import compile_story_to_scumm
from .studio_actors import set_costume_speaking_pose
from .scumm_costume import CostumeAnimation, CostumeDirection


VERBS = ("Push", "Pull", "Open", "Close")


def import_room_music(raw: str, room_name: str, music_id: str, midi_path: str) -> str:
    """Attach a real MIDI asset to one room; the native exporter wraps it as GMD."""
    document = parse_document(raw)
    if room_name not in {room.name for room in document.rooms}:
        raise ValueError("Bitte einen vorhandenen Musikraum wählen")
    if music_id in {asset.id for asset in document.music_assets}:
        raise ValueError("Musik-ID existiert bereits")
    path = Path(midi_path)
    if path.suffix.lower() not in (".mid", ".midi"):
        raise ValueError("Bitte eine MIDI-Datei (.mid) wählen")
    midi = path.read_bytes()
    rooms = tuple(replace(room, music_id=music_id) if room.name == room_name else room
                  for room in document.rooms)
    return _checked(replace(document, rooms=rooms,
                            music_assets=(*document.music_assets, MusicAsset(music_id, midi))))


def import_room_sound(raw: str, room_name: str, sound_id: str, voc_path: str) -> str:
    """Attach a native Creative Voice File effect to one authored room."""
    document = parse_document(raw)
    if room_name not in {room.name for room in document.rooms}:
        raise ValueError("Bitte einen vorhandenen Soundraum wählen")
    if sound_id in {asset.id for asset in document.sound_assets}:
        raise ValueError("Sound-ID existiert bereits")
    path = Path(voc_path)
    if path.suffix.lower() != ".voc":
        raise ValueError("Bitte eine Creative-Voice-Datei (.voc) wählen")
    voc = path.read_bytes()
    return _checked(replace(document, sound_assets=(
        *document.sound_assets, SoundAsset(sound_id, room_name, voc))))


def room_sound_ids(raw: str, room_name: str) -> tuple[str, ...]:
    return tuple(asset.id for asset in parse_document(raw).sound_assets
                 if asset.room == room_name)


def dialogue_voice_lines(raw: str) -> tuple[tuple[str, str], ...]:
    """Stable choices for authored NPC opening and answer dialogue lines."""
    document = parse_document(raw)
    result = []
    for room in document.rooms:
        for rule_index, rule in enumerate(room.talk_rules):
            for stage_index, stage in enumerate((rule, *rule.stages)):
                base = f"room.{room.name.lower()}.dialogue.{rule_index}"
                if stage_index:
                    base += f".stage.{stage_index - 1}"
                for line_index, line in enumerate(stage.opening_lines):
                    result.append((f"{room.name} / {rule.speaker_id} / {line}",
                                   f"{base}.opening.{line_index}"))
                for choice_index, choice in enumerate(stage.choices):
                    for line_index, line in enumerate(choice.reply_lines):
                        result.append((f"{room.name} / {choice.caption} / {line}",
                                       f"{base}.choice.{choice_index}.reply.{line_index}"))
    return tuple(result)


def _dialogue_animation_targets(document):
    targets = {}
    for room in document.rooms:
        for hotspot in room.hotspots:
            for index, actor in enumerate(hotspot.talk_actor_lines):
                key = f"room.{room.name.lower()}.object.{hotspot.id.lower()}.talk.{index}"
                targets[key] = (hotspot.talk_lines[index], actor)
        for rule_index, rule in enumerate(room.talk_rules):
            actors = dict(rule.actor_lines)
            for stage_index, stage in enumerate((rule, *rule.stages)):
                prefix = f"room.{room.name.lower()}.dialogue.{rule_index}"
                if stage_index:
                    prefix += f".stage.{stage_index - 1}"
                for index, line in enumerate(stage.opening_lines):
                    key = f"{prefix}.opening.{index}"
                    if key in actors:
                        targets[key] = (line, actors[key])
                for choice_index, choice in enumerate(stage.choices):
                    for index, line in enumerate(choice.reply_lines):
                        key = f"{prefix}.choice.{choice_index}.reply.{index}"
                        if key in actors:
                            targets[key] = (line, actors[key])
    return targets


def dialogue_animation_lines(raw: str) -> tuple[tuple[str, str], ...]:
    targets = _dialogue_animation_targets(parse_document(raw))
    return tuple((f"{actor} / {line}", key) for key, (line, actor) in targets.items())


def dialogue_animation_choices(raw: str, line_id: str | None):
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        return (), None, True
    actor = next(item for item in document.actors if item.id == target[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    options = tuple(animation.name for animation in costume.animations
                    if animation.index is not None and animation.index >= 24)
    selected = next((cue.animation for cue in document.dialogue_animation_cues
                     if cue.line_id == line_id), None)
    reset = next((cue.reset_to_stand for cue in document.dialogue_animation_cues
                  if cue.line_id == line_id), True)
    return options, selected, reset


def dialogue_speaking_frames(raw: str, line_id: str | None) -> tuple[str, ...]:
    """Offer only imported frames belonging to the selected native speaker."""
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        return ()
    actor = next(item for item in document.actors if item.id == target[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    return tuple(frame.id for frame in costume.frames)


def assign_dialogue_speaking_frame(raw: str, line_id: str, frame_id: str,
                                   reset_to_stand: bool = True) -> str:
    """Author a speaker's imported PNG pose and bind it to a dialogue line in one edit."""
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    actor = next(item for item in document.actors if item.id == target[1])
    sharing = [item.id for item in document.actors
               if item.id != actor.id and item.costume == actor.costume]
    if sharing:
        raise ValueError("Die Costume wird auch von anderen Figuren verwendet: "
                         + ", ".join(sharing) + ". Bitte zuerst eine eigene Costume zuweisen")
    costume = next(item for item in document.costumes if item.name == actor.costume)
    if frame_id not in {frame.id for frame in costume.frames}:
        raise ValueError("Bitte ein vorhandenes Costume-Frame als Sprechpose wählen")

    gesture = next((item for item in costume.animations if item.name == "gesture"), None)
    if gesture is None:
        # Preserve the original stock-ScummVM talk slots for the first pose.
        updated = set_costume_speaking_pose(raw, actor.costume, frame_id)
        return edit_dialogue_animation(updated, line_id, "gesture", reset_to_stand)

    if all(direction.commands == (frame_id,) for direction in gesture.directions):
        return edit_dialogue_animation(raw, line_id, "gesture", reset_to_stand)

    # A second line must not replace the first line's global talk_start/gesture.
    # Keep a stable animation per imported frame, reusing it on later lines.
    name = "pose_" + frame_id
    previous = next((item for item in costume.animations if item.name == name), None)
    if previous is not None:
        if any(direction.commands != (frame_id,) for direction in previous.directions):
            raise ValueError("Die vorhandene Sprechpose hat einen anderen Frame-Inhalt")
        return edit_dialogue_animation(raw, line_id, name, reset_to_stand)

    occupied = {animation.index for animation in costume.animations if animation.index is not None}
    index = next((slot for slot in range(28, 253, 4) if slot not in occupied), None)
    if index is None:
        raise ValueError("Keine freien nativen Costume-Animationsslots für weitere Sprechposen")
    animation = CostumeAnimation(name, tuple(
        CostumeDirection(direction, (frame_id,), True)
        for direction in ("N", "E", "S", "W")), index)
    updated_costume = replace(costume, animations=(*costume.animations, animation))
    updated = canonical_json(replace(document, costumes=tuple(
        updated_costume if item.name == costume.name else item for item in document.costumes)))
    return edit_dialogue_animation(updated, line_id, name, reset_to_stand)


def edit_dialogue_animation(raw: str, line_id: str, animation: str | None,
                            reset_to_stand: bool = True) -> str:
    document = parse_document(raw)
    if type(reset_to_stand) is not bool:
        raise ValueError("Die Standpose-Einstellung muss aktiviert oder deaktiviert sein")
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    cues = {cue.line_id: cue for cue in document.dialogue_animation_cues}
    if animation is None:
        cues.pop(line_id, None)
    else:
        cues[line_id] = DialogueAnimationCue(line_id, target[0], animation, reset_to_stand)
    return _checked(replace(document, dialogue_animation_cues=tuple(
        cues[key] for key in sorted(cues))))


def edit_dialogue_voice(raw: str, line_id: str, language: str,
                        sound_id: str | None, remove: bool = False) -> str:
    """Assign a room VOC to an NPC line or to one selected language."""
    document = parse_document(raw)
    lines = dict((identity, label) for label, identity in dialogue_voice_lines(raw))
    if line_id not in lines:
        raise ValueError("Bitte eine vorhandene Dialogzeile auswählen")
    room = next(room for room in document.rooms
                if line_id.startswith(f"room.{room.name.lower()}."))
    rest = line_id.split(".dialogue.", 1)[1].split(".")
    rule = room.talk_rules[int(rest.pop(0))]
    stage = rule.stages[int(rest[1])] if rest[0] == "stage" else rule
    if rest[0] == "stage":
        rest = rest[2:]
    source = (stage.opening_lines[int(rest[1])] if rest[0] == "opening"
              else stage.choices[int(rest[1])].reply_lines[int(rest[3])])
    cues = {cue.line_id: cue for cue in document.dialogue_voice_cues}
    existing = cues.get(line_id)
    if language == document.default_voice_language:
        if remove:
            cues.pop(line_id, None)
        else:
            cues[line_id] = DialogueVoiceCue(line_id, source, sound_id,
                                            existing.variants if existing else ())
    else:
        if existing is None:
            raise ValueError("Zuerst die Aufnahme der Standardsprache zuordnen")
        variants = dict(existing.variants)
        if remove:
            if language not in variants:
                raise ValueError("Sprachaufnahme existiert nicht")
            del variants[language]
        else:
            variants[language] = sound_id
        cues[line_id] = replace(existing, variants=tuple(sorted(variants.items())))
    return _checked(replace(document, dialogue_voice_cues=tuple(cues[key] for key in sorted(cues))))


def set_default_voice_language(raw: str, language: str) -> str:
    """Choose the project's initial native spoken language."""
    return _checked(replace(parse_document(raw), default_voice_language=language))


def edit_voice_variant(raw: str, identity: str, step_number: int,
                       language: str, sound_id: str | None, subtitle: str | None,
                       remove: bool = False) -> str:
    """Add/replace or remove one translation on a selected spoken sequence step."""
    document = parse_document(raw)
    sequences = list(document.interaction_sequences)
    index = next((i for i, item in enumerate(sequences) if _identity(item) == identity), None)
    if index is None or type(step_number) is not int or not 0 <= step_number < len(sequences[index].steps):
        raise ValueError("Bitte eine bestehende Sprachzeile auswählen")
    steps = list(sequences[index].steps)
    voice = steps[step_number]
    if not isinstance(voice, VoiceLineStep):
        raise ValueError("Der gewählte Schritt ist keine gesprochene Zeile")
    variants = {item.language: item for item in voice.variants}
    if remove:
        if language not in variants:
            raise ValueError("Sprachvariante existiert nicht")
        del variants[language]
    else:
        variants[language] = VoiceVariant(language, sound_id, subtitle)
    steps[step_number] = replace(voice, variants=tuple(variants[key] for key in sorted(variants)))
    sequences[index] = replace(sequences[index], steps=tuple(steps))
    return _checked(replace(document, interaction_sequences=tuple(sequences)))


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
    music_by_room = {room.name: room.music_id for room in native.rooms}
    composed = replace(project, rooms=tuple(replace(room, music_id=music_by_room.get(room.name))
                                            for room in project.rooms),
                       costumes=native.costumes, actors=native.actors,
                       animation_rules=native.animation_rules,
                       animation_input_rules=native.animation_input_rules,
                       animation_triggers=native.animation_triggers,
                       interaction_sequences=native.interaction_sequences,
                       music_assets=native.music_assets,
                       sound_assets=native.sound_assets,
                       default_voice_language=native.default_voice_language,
                       dialogue_voice_cues=native.dialogue_voice_cues)
    composed = replace(composed, dialogue_animation_cues=native.dialogue_animation_cues)
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
    if isinstance(step, MusicCueStep):
        return "Musik starten" if step.operation == "start" else "Musik stoppen"
    if isinstance(step, SoundEffectStep):
        return f"Sound {step.sound_id}: {'starten' if step.operation == 'start' else 'stoppen'}"
    if isinstance(step, VoiceLineStep):
        return (f"Sprachzeile {step.sound_id} ({step.actor_id or 'Ego'}): {step.text}"
                + (" [" + ", ".join(item.language for item in step.variants) + "]"
                   if step.variants else ""))
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
                direction: str | None, subtitle: str | None = None):
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
    elif kind == "Musik starten":
        step = MusicCueStep("start")
    elif kind == "Musik stoppen":
        step = MusicCueStep("stop")
    elif kind == "Sound starten":
        step = SoundEffectStep(target_id, "start")
    elif kind == "Sound stoppen":
        step = SoundEffectStep(target_id, "stop")
    elif kind == "Gesprochene Zeile":
        step = VoiceLineStep(target_id, subtitle, actor_id)
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
                         direction: str | None = None, subtitle: str | None = None) -> str:
    """Append to an existing verb sequence or create it; never silently replace another binding."""
    document = parse_document(raw)
    if verb not in VERBS:
        raise ValueError("Unbekanntes Verb")
    step = _build_step(kind, actor_id, animation, target_id, amount, x, y, direction, subtitle)
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
                                  direction: str | None = None, subtitle: str | None = None) -> str:
    """Append to an existing guarded or unguarded variant, preserving its trigger."""
    document = parse_document(raw)
    index = next((i for i, sequence in enumerate(document.interaction_sequences)
                  if _identity(sequence) == identity), None)
    if index is None:
        raise ValueError("Bitte eine vorhandene Interaktion wählen")
    step = _build_step(kind, actor_id, animation, target_id, amount, x, y, direction, subtitle)
    sequences = list(document.interaction_sequences)
    sequences[index] = replace(sequences[index], steps=(*sequences[index].steps, step))
    return _checked(replace(document, interaction_sequences=tuple(sequences)))


def replace_sequence_step(raw: str, identity: str, step_number: int | float | None,
                          kind: str, actor_id: str | None, animation: str | None,
                          target_id: str | None, amount: int | float | None,
                          x: int | float | None = None, y: int | float | None = None,
                          direction: str | None = None, subtitle: str | None = None) -> str:
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
    replacement = _build_step(kind, actor_id, animation, target_id, amount, x, y, direction, subtitle)
    if isinstance(steps[selected], VoiceLineStep) and isinstance(replacement, VoiceLineStep):
        replacement = replace(replacement, variants=steps[selected].variants)
    steps[selected] = replacement
    sequences[index] = replace(sequences[index], steps=tuple(steps))
    return _checked(replace(document, interaction_sequences=tuple(sequences)))


def sequence_step_fields(raw: str, identity: str | None, step_number: int | float | None) -> tuple:
    """Load an authored step back into the existing action form."""
    empty = ("Actor animieren", None, None, None, 1, 320, 100, "S", "")
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
    if isinstance(step, MusicCueStep):
        return ("Musik starten" if step.operation == "start" else "Musik stoppen",
                None, None, None, 1, 320, 100, "S")
    if isinstance(step, SoundEffectStep):
        return ("Sound starten" if step.operation == "start" else "Sound stoppen",
                None, None, step.sound_id, 1, 320, 100, "S")
    if isinstance(step, VoiceLineStep):
        return ("Gesprochene Zeile", step.actor_id, None, step.sound_id,
                1, 320, 100, "S", step.text)
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
