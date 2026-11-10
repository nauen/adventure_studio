"""Author ordered native SCUMM interactions without editing project JSON by hand."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha1
from pathlib import Path
import re
import unicodedata

from .scumm_project import (AnimateActorStep, DelayStep, MoveActorStep, WalkActorStep, WaitActorStep,
                            FaceActorStep, GameDocument,
                            InteractionSequence, ObjectStateStep, PickupObjectStep,
                            CombineInventoryStep, ChangeRoomStep, MusicCueStep, MusicAsset,
                            SoundAsset, SoundEffectStep, VoiceLineStep, VoiceVariant,
                            DialogueVoiceCue, DialogueAnimationCue,
                            canonical_json, parse_document)
from .story_document import parse_story_document
from .story_to_scumm import compile_story_to_scumm
from .studio_actors import (add_costume_frame, set_costume_speaking_pose, render_costume_frame,
                            costume_timeline_images, render_costume_preview)
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


def dialogue_costume_isolation_preview(raw: str | None, line_id: str | None) -> str:
    """Describe the exact Actor/Costume effects before creating a private copy."""
    if not raw or not line_id:
        return "Bitte eine native Sprecher-Dialogzeile wählen"
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        return "Diese Zeile hat keinen nativen Sprecher-Actor"
    actor = next(item for item in document.actors if item.id == target[1])
    sharing = sorted(item.id for item in document.actors
                     if item.id != actor.id and item.costume == actor.costume)
    if not sharing:
        return f"{actor.id}: Costume {actor.costume} gehört bereits nur dieser Figur"
    name = _isolated_costume_name(document, actor.costume, actor.id)
    return (f"{actor.id}: {actor.costume} → {name}. Die vollständige Costume samt "
            "Frames und Animationen wird kopiert. Nur diese Figur erhält die neue "
            "Costume; unverändert bleiben: " + ", ".join(sharing))


def _isolated_costume_name(document: GameDocument, costume: str, actor: str) -> str:
    existing = {item.name for item in document.costumes}
    base = f"{costume}_{actor}"
    name = base
    suffix = 2
    while name in existing:
        name = f"{base}_{suffix}"
        suffix += 1
    return name


def isolate_dialogue_speaker_costume(raw: str, line_id: str) -> str:
    """Copy-on-write a shared native Costume for all lines of one speaker Actor."""
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    actor = next(item for item in document.actors if item.id == target[1])
    if not any(item.id != actor.id and item.costume == actor.costume
               for item in document.actors):
        raise ValueError("Die Costume dieser Figur ist bereits exklusiv")
    costume = next(item for item in document.costumes if item.name == actor.costume)
    name = _isolated_costume_name(document, costume.name, actor.id)
    actors = tuple(replace(item, costume=name) if item.id == actor.id else item
                   for item in document.actors)
    return _checked(replace(document, actors=actors,
                            costumes=(*document.costumes, replace(costume, name=name))))


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


def dialogue_animation_phase_selection(raw: str, line_id: str | None) -> tuple[int, int]:
    """Native script ticks before and after the selected line's gesture start."""
    if not raw:
        return 1, 60
    cue = next((item for item in parse_document(raw).dialogue_animation_cues
                if item.line_id == line_id), None)
    return ((cue.start_delay_ticks, cue.minimum_animation_ticks)
            if cue is not None else (1, 60))


def dialogue_ending_animation_selection(raw: str, line_id: str | None):
    """Costume animations available as the selected line's native ending cue."""
    if not raw:
        return (), None, 12
    options, _selected, _reset = dialogue_animation_choices(raw, line_id)
    cue = next((item for item in parse_document(raw).dialogue_animation_cues
                if item.line_id == line_id), None)
    return (options, cue.ending_animation if cue else None,
            cue.ending_animation_ticks if cue and cue.ending_animation else 12)


def edit_dialogue_ending_animation(raw: str, line_id: str,
                                   animation: str | None, ticks: int | float) -> str:
    """Author an optional ending gesture after native waitForMessage."""
    document = parse_document(raw)
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    if cue is None:
        raise ValueError("Bitte zuerst eine Sprechanimation für diese Dialogzeile zuweisen")
    if animation is None:
        updated = replace(cue, ending_animation=None, ending_animation_ticks=0)
    else:
        if (type(ticks) not in (int, float) or int(ticks) != ticks or ticks <= 0):
            raise ValueError("Die Abschlussgeste benötigt mindestens einen ganzen nativen Tick")
        updated = replace(cue, ending_animation=animation,
                          ending_animation_ticks=int(ticks))
    return _checked(replace(document, dialogue_animation_cues=tuple(
        updated if item.line_id == line_id else item
        for item in document.dialogue_animation_cues)))


def dialogue_ending_timeline(raw: str, line_id: str | None, direction: str):
    """Read the authored ending COST frames for one line and facing."""
    if direction not in ("N", "E", "S", "W"):
        raise ValueError("Bitte eine gültige Blickrichtung N/E/S/W auswählen")
    if not raw:
        return [], (), ()
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        return [], (), ()
    actor = next(item for item in document.actors if item.id == target[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    animation = next((item for item in costume.animations
                      if cue and item.name == cue.ending_animation), None)
    selected = next((item for item in animation.directions
                     if item.direction == direction), None) if animation else None
    steps = selected.commands if selected else ()
    images = (costume_timeline_images(raw, costume.name, animation.name, direction)
              if selected and all(step in {f.id for f in costume.frames} for step in steps)
              else [])
    return (images, tuple((f"{i + 1}. {step}", i) for i, step in enumerate(steps)),
            tuple(frame.id for frame in costume.frames))


def assign_dialogue_ending_sequence(raw: str, line_id: str, direction: str,
                                    frame_ids: str, ticks: int | float = 12) -> str:
    """Create/re-edit a private native ending COST channel without the Costume editor."""
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    if direction not in ("N", "E", "S", "W"):
        raise ValueError("Bitte eine gültige Blickrichtung N/E/S/W auswählen")
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    if cue is None:
        raise ValueError("Bitte zuerst eine Sprechanimation für diese Dialogzeile zuweisen")
    actor = next(item for item in document.actors if item.id == target[1])
    sharing = [item.id for item in document.actors
               if item.id != actor.id and item.costume == actor.costume]
    if sharing:
        raise ValueError("Die Costume wird auch von anderen Figuren verwendet: "
                         + ", ".join(sharing) + ". Bitte zuerst eine eigene Costume zuweisen")
    costume = next(item for item in document.costumes if item.name == actor.costume)
    if not isinstance(frame_ids, str) or not frame_ids.strip():
        raise ValueError("Bitte mindestens ein importiertes PNG-Frame auswählen")
    sequence = tuple(part.strip() for part in frame_ids.split(","))
    available = {frame.id for frame in costume.frames}
    if any(not part or part not in available for part in sequence):
        raise ValueError("Die Abschlussfolge darf nur vorhandene PNG-Frames enthalten")
    name = "ending_line_" + sha1(line_id.encode("utf-8")).hexdigest()[:12]
    previous = next((item for item in costume.animations if item.name == name), None)
    if any(other.line_id != line_id and
           (other.animation == name or other.ending_animation == name)
           for other in document.dialogue_animation_cues):
        raise ValueError("Der native Abschluss-Slot gehört einer anderen Dialogzeile")
    if previous is None:
        occupied = {item.index for item in costume.animations if item.index is not None}
        index = next((slot for slot in range(28, 253, 4) if slot not in occupied), None)
        if index is None:
            raise ValueError("Keine freien nativen Costume-Animationsslots für Abschlussfolgen")
        base = next((item for item in costume.animations
                     if item.name == (cue.ending_animation or cue.animation)), None)
    else:
        if previous.index is None or previous.index < 28:
            raise ValueError("Vorhandene Abschlussanimation verwendet einen reservierten Slot")
        index, base = previous.index, previous
    if base is None or {item.direction for item in base.directions} != {"N", "E", "S", "W"}:
        raise ValueError("Die Abschlussfolge benötigt eine bestehende Animation mit vier Blickrichtungen")
    directions = tuple(CostumeDirection(item.direction, sequence, True)
                       if item.direction == direction else item
                       for item in base.directions)
    animation = CostumeAnimation(name, directions, index)
    updated_costume = replace(costume, animations=tuple(
        item for item in costume.animations if item.name != name) + (animation,))
    updated = canonical_json(replace(document, costumes=tuple(
        updated_costume if item.name == costume.name else item for item in document.costumes)))
    return edit_dialogue_ending_animation(updated, line_id, name, ticks)


def edit_dialogue_ending_timeline(raw: str, line_id: str, direction: str,
                                  step_number: int | float | None, operation: str,
                                  frame_id: str | None = None,
                                  ticks: int | float = 12) -> str:
    """Append, reorder or remove a PNG in the line-specific ending timeline."""
    _, steps, available = dialogue_ending_timeline(raw, line_id, direction)
    if not available:
        raise ValueError("Bitte eine Sprecher-Dialogzeile mit PNG-Costume auswählen")
    if steps and any(part.split(". ", 1)[1] not in available for part, _ in steps):
        raise ValueError("Diese Abschlussanimation enthält native Kommandos")
    sequence = [part.split(". ", 1)[1] for part, _ in steps]
    if operation == "Anhängen":
        if frame_id not in available:
            raise ValueError("Bitte ein vorhandenes PNG-Frame auswählen")
        sequence.append(frame_id)
    else:
        if (type(step_number) not in (int, float) or int(step_number) != step_number
                or not 0 <= int(step_number) < len(sequence)):
            raise ValueError("Bitte einen gültigen Abschlussframe-Schritt auswählen")
        index = int(step_number)
        if operation == "Entfernen":
            if len(sequence) == 1:
                raise ValueError("Zum Entfernen der gesamten Abschlussgeste den Entfernen-Button nutzen")
            sequence.pop(index)
        elif operation in ("Nach links", "Nach rechts"):
            other = index + (-1 if operation == "Nach links" else 1)
            if not 0 <= other < len(sequence):
                raise ValueError("Abschlussframe ist bereits am Rand")
            sequence[index], sequence[other] = sequence[other], sequence[index]
        else:
            raise ValueError("Unbekannte Abschluss-Timeline-Aktion")
    return assign_dialogue_ending_sequence(raw, line_id, direction, ", ".join(sequence), ticks)


def import_dialogue_png_frame(raw: str, line_id: str, direction: str,
                              png_path: str, frame_id: str, target: str,
                              ending_ticks: int | float = 12,
                              reset_to_stand: bool = True) -> str:
    """Import actual PNG pixels and append them to one authored dialogue channel.

    Both operations are atomic with respect to the returned project JSON: a
    missing actor, invalid image, full native palette or invalid cue cannot
    leave an orphan imported frame in the editor state.
    """
    document = parse_document(raw)
    selected = _dialogue_animation_targets(document).get(line_id)
    if selected is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    if direction not in ("N", "E", "S", "W"):
        raise ValueError("Bitte eine gültige Blickrichtung N/E/S/W auswählen")
    if target not in ("Sprechfolge", "Abschlussfolge"):
        raise ValueError("Bitte Sprechfolge oder Abschlussfolge auswählen")
    if not isinstance(frame_id, str) or not frame_id.strip():
        raise ValueError("Bitte eine eindeutige native PNG-Frame-ID eingeben")
    actor = next(item for item in document.actors if item.id == selected[1])
    sharing = [item.id for item in document.actors
               if item.id != actor.id and item.costume == actor.costume]
    if sharing:
        raise ValueError("Die Costume wird auch von anderen Figuren verwendet: "
                         + ", ".join(sharing) + ". Bitte zuerst eine eigene Costume zuweisen")
    # In particular, reject a duplicate before PNG decoding or any animation
    # reassignment. Existing native Costume frame IDs are immutable.
    costume = next(item for item in document.costumes if item.name == actor.costume)
    if frame_id in {frame.id for frame in costume.frames}:
        raise ValueError("Die PNG-Frame-ID existiert bereits in dieser Costume")
    imported = add_costume_frame(raw, costume.name, png_path, frame_id)
    if target == "Sprechfolge":
        return edit_dialogue_speaking_timeline(
            imported, line_id, direction, None, "Anhängen", frame_id, reset_to_stand)
    return edit_dialogue_ending_timeline(
        imported, line_id, direction, None, "Anhängen", frame_id, ending_ticks)


def _dialogue_png_batch_entries(paths: list[str] | tuple[str, ...] | None
                                ) -> tuple[tuple[str, str], ...]:
    if not isinstance(paths, (list, tuple)) or not paths:
        raise ValueError("Bitte mindestens eine PNG-Datei auswählen")
    entries = []
    for path in paths:
        if not isinstance(path, str) or not path or Path(path).suffix.lower() != ".png":
            raise ValueError("Die Folge darf nur PNG-Dateien enthalten")
        stem = unicodedata.normalize("NFKD", Path(path).stem).encode("ascii", "ignore").decode("ascii")
        frame_id = re.sub(r"[^A-Za-z0-9_]", "_", stem).strip("_")
        if not frame_id or not frame_id[0].isalpha():
            frame_id = "Frame_" + (frame_id or "PNG")
        entries.append((path, frame_id))
    names = [frame_id for _path, frame_id in entries]
    if len(set(names)) != len(names):
        raise ValueError("Mehrere PNG-Dateinamen ergeben dieselbe Frame-ID; bitte Dateien umbenennen")
    return tuple(entries)


def dialogue_png_batch_order(paths: list[str] | tuple[str, ...] | None,
                             order: list[int] | tuple[int, ...] | None = None
                             ) -> tuple[str, ...]:
    """Resolve included uploads, in order, without deleting staged files."""
    if not isinstance(paths, (list, tuple)) or not paths:
        raise ValueError("Bitte mindestens eine PNG-Datei auswählen")
    indexes = tuple(range(len(paths))) if order is None else tuple(order)
    if (len(indexes) > len(paths) or
            any(type(index) is not int for index in indexes) or
            len(set(indexes)) != len(indexes) or
            any(index not in range(len(paths)) for index in indexes)):
        raise ValueError("Die PNG-Reihenfolge passt nicht mehr zur Dateiauswahl; bitte neu auswählen")
    return tuple(paths[index] for index in indexes)


def move_dialogue_png_batch_frame(paths: list[str] | tuple[str, ...] | None,
                                  order: list[int] | tuple[int, ...] | None,
                                  selected: int | None, step: int
                                  ) -> tuple[tuple[int, ...], int]:
    """Move one selected upload while preserving valid inclusion indexes."""
    ordered = dialogue_png_batch_order(paths, order)
    indexes = list(range(len(ordered))) if order is None else list(order)
    if type(selected) is not int or selected not in range(len(indexes)):
        raise ValueError("Bitte zuerst ein PNG-Frame auswählen")
    if step not in (-1, 1):
        raise ValueError("Ungültige Verschieberichtung")
    destination = selected + step
    if destination in range(len(indexes)):
        indexes[selected], indexes[destination] = indexes[destination], indexes[selected]
        return tuple(indexes), destination
    return tuple(indexes), selected


def remove_dialogue_png_batch_frame(paths: list[str] | tuple[str, ...] | None,
                                    order: list[int] | tuple[int, ...] | None,
                                    selected: int | None
                                    ) -> tuple[tuple[int, ...], int | None]:
    """Exclude one staged PNG without re-uploading or touching project JSON."""
    ordered = dialogue_png_batch_order(paths, order)
    if type(selected) is not int or selected not in range(len(ordered)):
        raise ValueError("Bitte zuerst ein PNG-Frame auswählen")
    indexes = list(range(len(paths))) if order is None else list(order)
    indexes.pop(selected)
    return tuple(indexes), min(selected, len(indexes) - 1) if indexes else None


def dialogue_png_batch_excluded(paths: list[str] | tuple[str, ...] | None,
                                order: list[int] | tuple[int, ...] | None
                                ) -> tuple[tuple[str, int], ...]:
    """Offer only staged files not already present in the import sequence."""
    if not paths:
        return ()
    dialogue_png_batch_order(paths, order)
    included = set(range(len(paths))) if order is None else set(order)
    return tuple((f"{index + 1}. {Path(path).name}", index)
                 for index, path in enumerate(paths) if index not in included)


def restore_dialogue_png_batch_frame(paths: list[str] | tuple[str, ...] | None,
                                     order: list[int] | tuple[int, ...] | None,
                                     excluded_index: int | None
                                     ) -> tuple[tuple[int, ...], int]:
    """Reinclude a staged PNG at the end without changing other uploads."""
    included = dialogue_png_batch_order(paths, order)
    excluded = {index for _name, index in dialogue_png_batch_excluded(paths, order)}
    if type(excluded_index) is not int or excluded_index not in excluded:
        raise ValueError("Bitte zuerst ein ausgeschlossenes PNG-Frame auswählen")
    indexes = list(range(len(paths))) if order is None else list(order)
    indexes.append(excluded_index)
    return tuple(indexes), len(included)


def dialogue_png_batch_preview(raw: str | None, line_id: str | None,
                               paths: list[str] | tuple[str, ...] | None,
                               order: list[int] | tuple[int, ...] | None = None) -> str:
    """Show the exact ordered native frame IDs before one batch import click."""
    if not paths:
        return "Noch keine PNG-Dateien ausgewählt"
    try:
        included = dialogue_png_batch_order(paths, order)
        if not included:
            return "Alle PNG-Dateien aus der Importauswahl entfernt; bitte neue Dateien auswählen"
        entries = _dialogue_png_batch_entries(included)
    except ValueError as error:
        return str(error)
    existing = set(dialogue_speaking_frames(raw, line_id)) if raw and line_id else set()
    return "\n".join(f"{i}. {Path(path).name} → {frame_id}"
                     + (" (existiert bereits!)" if frame_id in existing else "")
                     for i, (path, frame_id) in enumerate(entries, 1))


def dialogue_png_batch_thumbnails(paths: list[str] | tuple[str, ...] | None,
                                  order: list[int] | tuple[int, ...] | None = None
                                  ) -> list[tuple[str, str]]:
    """Display actual uploaded pixels in exactly the prospective COST order."""
    if not paths:
        return []
    included = dialogue_png_batch_order(paths, order)
    return [(path, f"{position}. {frame_id}")
            for position, path in enumerate(included, 1)
            for _source, frame_id in _dialogue_png_batch_entries((path,))]


def import_dialogue_png_batch(raw: str, line_id: str, direction: str,
                              paths: list[str] | tuple[str, ...] | None, target: str,
                              ending_ticks: int | float = 12,
                              reset_to_stand: bool = True,
                              order: list[int] | tuple[int, ...] | None = None) -> str:
    """Import all PNGs in selection order, committing only the final valid JSON."""
    entries = _dialogue_png_batch_entries(dialogue_png_batch_order(paths, order))
    document = parse_document(raw)
    selected = _dialogue_animation_targets(document).get(line_id)
    if selected is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    actor = next(item for item in document.actors if item.id == selected[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    known = {frame.id for frame in costume.frames}
    if any(frame_id in known for _path, frame_id in entries):
        raise ValueError("Mindestens eine PNG-Frame-ID existiert bereits in dieser Costume")
    updated = raw
    for path, frame_id in entries:
        updated = import_dialogue_png_frame(updated, line_id, direction, path,
                                            frame_id, target, ending_ticks, reset_to_stand)
    return updated


def dialogue_ending_timeline_preview(raw: str, line_id: str, direction: str,
                                     duration_ms: int | float, destination: Path) -> Path:
    """Editor-only GIF of an authored native ending sequence."""
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    if target is None or cue is None or cue.ending_animation is None:
        raise ValueError("Bitte zuerst eine Abschlussgeste für diese Dialogzeile speichern")
    actor = next(item for item in document.actors if item.id == target[1])
    return render_costume_preview(raw, actor.costume, cue.ending_animation,
                                  direction, duration_ms, destination)


def edit_dialogue_animation_phases(raw: str, line_id: str,
                                  start_delay_ticks: int | float,
                                  minimum_animation_ticks: int | float) -> str:
    """Keep the authored gesture active for native script ticks, not UI ms."""
    document = parse_document(raw)
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    if cue is None:
        raise ValueError("Bitte zuerst eine Sprechfolge für diese Dialogzeile zuweisen")
    for label, ticks in (("Vorlauf", start_delay_ticks),
                         ("Mindestlaufzeit", minimum_animation_ticks)):
        if (type(ticks) not in (int, float) or int(ticks) != ticks or ticks < 0):
            raise ValueError(f"{label} benötigt eine nichtnegative ganze Zahl nativer Ticks")
    updated = replace(cue, start_delay_ticks=int(start_delay_ticks),
                      minimum_animation_ticks=int(minimum_animation_ticks))
    return _checked(replace(document, dialogue_animation_cues=tuple(
        updated if item.line_id == line_id else item
        for item in document.dialogue_animation_cues)))


def dialogue_speaking_frame_selection(raw: str, line_id: str | None
                                      ) -> tuple[tuple[str, ...], str | None]:
    """Resolve the saved line-specific pose to its PNG frame for the editor.

    Native COST animations may contain several frames, direction-dependent
    frames or commands. In those cases no single PNG can be truthfully
    preselected; the explicit Costume-animation selector remains available.
    """
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        return (), None
    actor = next(item for item in document.actors if item.id == target[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    frames = tuple(frame.id for frame in costume.frames)
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    animation = next((item for item in costume.animations
                      if cue is not None and item.name == cue.animation), None)
    if animation is None or not animation.directions:
        return frames, None
    commands = {direction.commands for direction in animation.directions}
    if len(commands) != 1:
        return frames, None
    commands_for_pose = next(iter(commands))
    selected = (commands_for_pose[0] if len(commands_for_pose) == 1
                and commands_for_pose[0] in frames else None)
    return frames, selected


def dialogue_speaking_frame_preview(raw: str | None, line_id: str | None,
                                    frame_id: str | None):
    """Preview the selected NPC's actual indexed frame, not a running animation."""
    if not raw or not line_id or not frame_id:
        return None
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        return None
    actor = next(item for item in document.actors if item.id == target[1])
    return render_costume_frame(raw, actor.costume, frame_id)


def dialogue_direction_animation_preview(raw: str | None, line_id: str | None,
                                         animation_name: str | None, direction: str):
    """Show one authored COST animation frame for the selected actor direction.

    This does not approximate a multi-frame native timeline or override the
    line's saved cue. A direction can have its own distinct frame.
    """
    names = {"N": "Nord", "E": "Ost", "S": "Süd", "W": "West"}
    if direction not in names:
        raise ValueError("Bitte eine gültige Blickrichtung (N, E, S, W) wählen")
    if not raw or not line_id:
        return None, "Bitte zuerst eine Sprecher-Dialogzeile wählen"
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        return None, "Die gewählte Dialogzeile hat keinen nativen Sprecher"
    if not animation_name:
        return None, "Keine Costume-Sprechanimation dieser Dialogzeile ausgewählt"
    actor = next(item for item in document.actors if item.id == target[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    animation = next((item for item in costume.animations
                      if item.name == animation_name and item.index is not None
                      and item.index >= 24), None)
    if animation is None:
        return None, "Keine indizierte Sprecheranimation dieser Figur ausgewählt"
    selected = next((item for item in animation.directions
                     if item.direction == direction), None)
    if selected is None:
        return None, f"{animation_name}: keine Animation für {names[direction]}"
    if len(selected.commands) != 1:
        return None, (f"{animation_name} · {names[direction]}: "
                      "mehrere Frames/Kommandos – keine statische Einzelbildvorschau")
    frame_id = selected.commands[0]
    if frame_id not in {frame.id for frame in costume.frames}:
        return None, (f"{animation_name} · {names[direction]}: "
                      "COST-Kommando statt PNG-Frame – keine Einzelbildvorschau")
    # Give the directional view a separate native-pixel card with a direction
    # label. Its image bytes deliberately differ from the uniform PNG picker
    # preview: Gradio may otherwise concurrently rewrite the same cached
    # image file while both independent output components are streaming.
    from PIL import Image, ImageDraw

    frame_preview = render_costume_frame(raw, costume.name, frame_id)
    card = Image.new("RGB", (304, 320), (36, 40, 48))
    card.paste(frame_preview, (24, 40))
    ImageDraw.Draw(card).text((24, 14), f"{names[direction]} · {animation.name}",
                              fill=(240, 240, 240))
    return (card,
            f"{animation_name} · {names[direction]} · Frame {frame_id} "
            "(native Costume-Palette, statische Editor-Vorschau)")


def dialogue_speaking_frames(raw: str, line_id: str | None) -> tuple[str, ...]:
    """Offer only imported frames belonging to the selected native speaker."""
    return dialogue_speaking_frame_selection(raw, line_id)[0]


def dialogue_speaking_sequence_selection(raw: str, line_id: str | None,
                                         direction: str | None = None) -> str:
    """Show saved native frames, either uniformly or for one direction."""
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        return ""
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    if cue is None:
        return ""
    actor = next(item for item in document.actors if item.id == target[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    animation = next((item for item in costume.animations if item.name == cue.animation), None)
    if animation is None or {entry.direction for entry in animation.directions} != {"N", "E", "S", "W"}:
        return ""
    if direction is not None and direction not in ("N", "E", "S", "W"):
        raise ValueError("Bitte eine gültige Blickrichtung N/E/S/W auswählen")
    commands = {entry.commands for entry in animation.directions
                if direction is None or entry.direction == direction}
    frames = {frame.id for frame in costume.frames}
    if len(commands) != 1:
        return ""
    sequence = next(iter(commands))
    return ", ".join(sequence) if all(command in frames for command in sequence) else ""


def dialogue_speaking_timeline(raw: str, line_id: str | None, direction: str):
    """Show the selected line's actual native COST direction, in frame order."""
    if direction not in ("N", "E", "S", "W"):
        raise ValueError("Bitte eine gültige Blickrichtung N/E/S/W auswählen")
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        return [], (), ()
    actor = next(item for item in document.actors if item.id == target[1])
    costume = next(item for item in document.costumes if item.name == actor.costume)
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    steps = ()
    images = []
    if cue is not None:
        animation = next((item for item in costume.animations
                          if item.name == cue.animation), None)
        selected = next((item for item in animation.directions
                         if item.direction == direction), None) if animation else None
        if selected is not None:
            steps = selected.commands
            images = costume_timeline_images(raw, costume.name, cue.animation, direction)
    return images, tuple((f"{index + 1}. {step}", index)
                         for index, step in enumerate(steps)), tuple(frame.id for frame in costume.frames)


def edit_dialogue_speaking_timeline(raw: str, line_id: str, direction: str,
                                   step_number: int | float | None, operation: str,
                                   frame_id: str | None = None,
                                   reset_to_stand: bool = True) -> str:
    """Edit one line/facing's PNG frame order using its existing COST slot."""
    _, steps, available = dialogue_speaking_timeline(raw, line_id, direction)
    if not available:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile mit PNG-Costume auswählen")
    saved = dialogue_speaking_sequence_selection(raw, line_id, direction)
    if steps and not saved:
        raise ValueError("Diese Animation enthält native Kommandos; bitte die Costume-Timeline verwenden")
    sequence = [part.strip() for part in saved.split(",")] if saved else []
    if operation == "Anhängen":
        if frame_id not in available:
            raise ValueError("Bitte ein vorhandenes PNG-Frame zum Anhängen auswählen")
        sequence.append(frame_id)
    else:
        if (type(step_number) not in (int, float) or int(step_number) != step_number
                or not 0 <= int(step_number) < len(sequence)):
            raise ValueError("Bitte einen gültigen Sprechframe-Schritt auswählen")
        index = int(step_number)
        if operation == "Entfernen":
            if len(sequence) == 1:
                raise ValueError("Eine native Sprechfolge benötigt mindestens ein PNG-Frame")
            sequence.pop(index)
        elif operation in ("Nach links", "Nach rechts"):
            other = index + (-1 if operation == "Nach links" else 1)
            if not 0 <= other < len(sequence):
                raise ValueError("Sprechframe ist bereits am Rand der Folge")
            sequence[index], sequence[other] = sequence[other], sequence[index]
        else:
            raise ValueError("Unbekannte Sprech-Timeline-Aktion")
    return assign_dialogue_direction_speaking_sequence(
        raw, line_id, direction, ", ".join(sequence), reset_to_stand)


def dialogue_speaking_timeline_preview(raw: str, line_id: str,
                                       direction: str, duration_ms: int | float,
                                       destination: Path) -> Path:
    """Render the saved NPC line as an editor GIF; ScummVM owns native timing."""
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    cue = next((item for item in document.dialogue_animation_cues
                if item.line_id == line_id), None)
    if cue is None:
        raise ValueError("Bitte zuerst eine Sprechfolge für diese Dialogzeile speichern")
    actor = next(item for item in document.actors if item.id == target[1])
    return render_costume_preview(raw, actor.costume, cue.animation,
                                  direction, duration_ms, destination)


def assign_dialogue_speaking_sequence(raw: str, line_id: str, frame_ids: str,
                                      reset_to_stand: bool = True,
                                      direction: str | None = None) -> str:
    """Save one NPC line's own native looping COST frames, without global edits."""
    document = parse_document(raw)
    target = _dialogue_animation_targets(document).get(line_id)
    if target is None:
        raise ValueError("Bitte eine native Sprecher-Dialogzeile auswählen")
    if direction is not None and direction not in ("N", "E", "S", "W"):
        raise ValueError("Bitte eine gültige Blickrichtung N/E/S/W auswählen")
    actor = next(item for item in document.actors if item.id == target[1])
    sharing = [item.id for item in document.actors
               if item.id != actor.id and item.costume == actor.costume]
    if sharing:
        raise ValueError("Die Costume wird auch von anderen Figuren verwendet: "
                         + ", ".join(sharing) + ". Bitte zuerst eine eigene Costume zuweisen")
    costume = next(item for item in document.costumes if item.name == actor.costume)
    if not isinstance(frame_ids, str) or not frame_ids.strip():
        raise ValueError("Bitte eine Folge importierter PNG-Frames eingeben")
    sequence = tuple(item.strip() for item in frame_ids.split(","))
    available = {frame.id for frame in costume.frames}
    if any(not item or item not in available for item in sequence):
        raise ValueError("Die Sprechfolge darf nur vorhandene PNG-Frames enthalten")
    # Stable per-line identity allows re-editing, independent of the selected frames.
    name = "line_" + sha1(line_id.encode("utf-8")).hexdigest()[:12]
    previous = next((item for item in costume.animations if item.name == name), None)
    if any(cue.line_id != line_id and cue.animation == name
           for cue in document.dialogue_animation_cues):
        raise ValueError("Der native Animationsslot gehört bereits zu einer anderen Dialogzeile")
    if previous is None:
        occupied = {item.index for item in costume.animations if item.index is not None}
        index = next((slot for slot in range(28, 253, 4) if slot not in occupied), None)
        if index is None:
            raise ValueError("Keine freien nativen Costume-Animationsslots für Sprechfolgen")
    else:
        if previous.index is None or previous.index < 28:
            raise ValueError("Vorhandene Dialoganimation verwendet einen reservierten Animationsslot")
        index = previous.index
    if direction is None:
        directions = tuple(CostumeDirection(facing, sequence, True)
                           for facing in ("N", "E", "S", "W"))
    else:
        if previous is not None:
            base = previous
        else:
            cue = next((item for item in document.dialogue_animation_cues
                        if item.line_id == line_id), None)
            base_name = cue.animation if cue else "gesture"
            base = next((item for item in costume.animations
                         if item.name == base_name), None)
        if base is None or {item.direction for item in base.directions} != {"N", "E", "S", "W"}:
            raise ValueError("Die Sprechfolge benötigt eine bestehende Animation mit vier Blickrichtungen")
        directions = tuple(CostumeDirection(item.direction, sequence, True)
                           if item.direction == direction else item
                           for item in base.directions)
    animation = CostumeAnimation(name, directions, index)
    updated_costume = replace(costume, animations=tuple(
        item for item in costume.animations if item.name != name) + (animation,))
    updated = canonical_json(replace(document, costumes=tuple(
        updated_costume if item.name == costume.name else item for item in document.costumes)))
    return edit_dialogue_animation(updated, line_id, name, reset_to_stand)


def assign_dialogue_direction_speaking_sequence(raw: str, line_id: str,
                                                direction: str, frame_ids: str,
                                                reset_to_stand: bool = True) -> str:
    """Author one facing of one NPC line without changing the other channels."""
    return assign_dialogue_speaking_sequence(raw, line_id, frame_ids,
                                             reset_to_stand, direction)


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
    gesture_users = {
        cue.line_id for cue in document.dialogue_animation_cues
        if cue.animation == "gesture"
        and (speaker := _dialogue_animation_targets(document).get(cue.line_id)) is not None
        and next(item for item in document.actors if item.id == speaker[1]).costume == costume.name
    }
    if gesture is None or not gesture_users or gesture_users == {line_id}:
        # The first assignment may replace an unused legacy gesture, while
        # another line's active gesture must never be overwritten.
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
        previous = cues.get(line_id)
        cues[line_id] = (replace(previous, animation=animation,
                                reset_to_stand=reset_to_stand)
                         if previous is not None else
                         DialogueAnimationCue(line_id, target[0], animation, reset_to_stand))
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
