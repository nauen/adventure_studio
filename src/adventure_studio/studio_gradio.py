"""Optional Gradio authoring UI over the validated story-service boundary.

Run: python -m adventure_studio.studio_gradio
Offline editing works without API credentials; AI is explicit opt-in.
"""

from __future__ import annotations

import tempfile
import subprocess
import os
from pathlib import Path

from .studio_catalog import relationship_svg, story_catalog
from .story_ai import preview_ai_response, propose_story_change
from .studio_service import (accept_proposal, add_decoration, change_item,
                             change_dialogue_line, change_dialogue_facing, extend_dialogue_line,
                             add_dialogue_choice, change_dialogue_choice, extend_dialogue_choice,
                             change_position, change_puzzle, change_scene,
                             describe_story, item_position, prepare_proposal,
                             report_text, scene_preview, translation_draft, validate_translation_draft)
from .story_document import canonical_story_json, parse_story_document
from .studio_export import export_playable, export_native_project
from .studio_sequences import (actor_animations, append_sequence_step, append_selected_sequence_step,
                               modify_sequence_step,
                               replace_sequence_step, sequence_step_fields,
                               sequence_condition_fields, set_sequence_condition,
                               duplicate_sequence_variant, sequence_skip_enabled,
                               set_sequence_skippable,
                               project_choices, sequence_choices, sequence_steps,
                               compose_story_project, import_room_music,
                               import_room_sound, room_sound_ids,
                               edit_voice_variant, set_default_voice_language,
                               dialogue_voice_lines, edit_dialogue_voice,
                               dialogue_animation_lines, dialogue_animation_choices,
                               dialogue_speaking_frame_selection, dialogue_speaking_frame_preview,
                                dialogue_direction_animation_preview,
                               assign_dialogue_speaking_frame,
                               assign_dialogue_speaking_sequence,
                               assign_dialogue_direction_speaking_sequence,
                               dialogue_speaking_sequence_selection,
                               dialogue_speaking_timeline, edit_dialogue_speaking_timeline,
                               dialogue_speaking_timeline_preview,
                               dialogue_animation_phase_selection,
                               edit_dialogue_animation_phases, edit_dialogue_animation)
from .studio_sequences import (dialogue_ending_animation_selection,
                               edit_dialogue_ending_animation,
                               dialogue_ending_timeline,
                               edit_dialogue_ending_timeline, dialogue_ending_timeline_preview,
                               import_dialogue_png_frame,
                               dialogue_png_batch_preview, import_dialogue_png_batch,
                               dialogue_png_batch_order, move_dialogue_png_batch_frame,
                               remove_dialogue_png_batch_frame,
                               dialogue_png_batch_excluded, restore_dialogue_png_batch_frame,
                               dialogue_png_batch_animation_preview,
                               dialogue_png_batch_preflight, dialogue_png_batch_image_diagnostics,
                               dialogue_png_batch_frame_preview, step_dialogue_png_batch_frame,
                               replace_dialogue_png_batch_frame,
                               dialogue_png_batch_selected_frame_id,
                               set_dialogue_png_batch_frame_id,
                               suggest_dialogue_png_batch_frame_id,
                               resolve_dialogue_png_batch_frame_ids,
                               stage_dialogue_png_sprite_sheet,
                               dialogue_costume_isolation_preview,
                               isolate_dialogue_speaker_costume)
from .scumm_project import canonical_json as canonical_project_json, parse_document
from .studio_project import canonical_studio_project, parse_studio_project
from .studio_actors import (add_actor, actor_summary, costume_names, costume_summary,
                            create_costume, add_costume_frame, set_costume_animation,
                            costume_frame_names, set_costume_speaking_pose,
                            set_costume_direction_speaking_pose, set_costume_direction_speaking_sequence,
                            costume_direction_speaking_frame,
                            move_actor, costume_animation_names, costume_animation_steps,
                            costume_timeline_images, edit_costume_timeline,
                            render_costume_preview, set_actor_initial_animation,
                            set_actor_costume)


EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "mini_story_chain.json"


def scene_fields(raw: str, scene_id: str) -> tuple[str, str]:
    story = parse_story_document(raw)
    scene = next((s for s in story.scenes if s.id == scene_id), None)
    return (scene.title, scene.description) if scene else ("", "")


def item_fields(raw: str, item_id: str) -> tuple[str, str]:
    story = parse_story_document(raw)
    item = next((i for i in story.items if i.id == item_id), None)
    return (item.name, item.description) if item else ("", "")


def puzzle_fields(raw: str, puzzle_id: str) -> tuple[str, str]:
    story = parse_story_document(raw)
    puzzle = next((p for p in story.puzzles if p.id == puzzle_id), None)
    return (puzzle.title, ", ".join(puzzle.requires)) if puzzle else ("", "")


def dialogue_line_fields(raw: str, node_id: str) -> str:
    node = next((n for n in parse_story_document(raw).dialogue_nodes if n.id == node_id), None)
    return node.text if node else ""


def dialogue_facing_fields(raw: str, node_id: str) -> str | None:
    node = next((n for n in parse_story_document(raw).dialogue_nodes if n.id == node_id), None)
    return node.face_direction if node else None


def dialogue_choice_fields(raw: str, choice_id: str):
    story = parse_story_document(raw)
    choice = next((c for c in story.dialogue_choices if c.id == choice_id), None)
    if choice is None:
        return "", {"choices": [("Gespräch beenden", None)], "value": None}
    parent = next(n for n in story.dialogue_nodes if n.id == choice.node_id)
    return choice.text, {"choices": [("Gespräch beenden", None)] + [
        (n.id, n.id) for n in story.dialogue_nodes if n.dialogue_id == parent.dialogue_id],
        "value": choice.next_node_id}


def dialogue_speaker_fields(raw: str, node_id: str):
    story = parse_story_document(raw)
    node = next((n for n in story.dialogue_nodes if n.id == node_id), None)
    if node is None:
        return {"choices": [], "value": None}
    dialogue = next(d for d in story.dialogues if d.id == node.dialogue_id)
    return {"choices": [(character.name, character.id) for character in story.characters
                        if character.scene_id == dialogue.scene_id],
            "value": node.speaker_id}


def room_items(raw: str, scene_id: str) -> tuple[tuple[str, str], ...]:
    story = parse_story_document(raw)
    return tuple((item.name, item.id) for item in story.items
                 if item.scene_id == scene_id and item.role != "crafted")


def position_fields(raw: str, item_id: str) -> tuple[int, int]:
    if not item_id:
        return 0, 0
    try:
        return item_position(raw, item_id)
    except ValueError:
        position = next((p for p in parse_story_document(raw).placements if p.item_id == item_id), None)
        return (position.x, position.y) if position else (0, 0)


def render_scene(raw: str, scene_id: str):
    from PIL import Image, ImageDraw

    width, height, pixels, palette, hotspots = scene_preview(raw, scene_id)
    image = Image.frombytes("P", (width, height), pixels)
    image.putpalette([component for rgb in palette for component in rgb]
                     + [0] * (3 * (256 - len(palette))))
    image = image.convert("RGB")
    draw = ImageDraw.Draw(image)
    for label, x, y, w, h in hotspots:
        draw.rectangle((x, y, x + w - 1, y + h - 1), outline=(255, 255, 255), width=1)
        draw.text((x, max(0, y - 12)), label, fill=(255, 255, 255))
    return image


def safe_render_scene(raw: str, scene_id: str):
    try:
        return render_scene(raw, scene_id)
    except (ValueError, ImportError):
        return None  # Authoring data is valid, but SCUMM preview is unavailable.


def catalog_view(raw: str):
    """Shared overview after load and after each confirmed edit."""
    catalog = story_catalog(raw)
    gallery = []
    for scene_id, title, _chapter, _description in catalog.scenes:
        try:
            gallery.append((render_scene(raw, scene_id), f"{title} ({scene_id})"))
        except (ValueError, ImportError):
            # The story bible may contain scenes not yet supported by the
            # deliberately bounded SCUMM adapter. Core installs also omit PIL.
            pass
    summary = (f"**{len(catalog.chapters)} Kapitel · {len(catalog.scenes)} Szenen · "
               f"{len(catalog.characters)} Figuren · {len(catalog.items)} Objekte · "
               f"{len(catalog.puzzles)} Rätsel · {len(catalog.recipes)} Rezepte · "
               f"{len(catalog.dialogues)} Dialoge · {len(catalog.assets)} Asset-Referenzen**\n\n"
               "Raumbilder sind derzeit technische Vorschauen. Referenzierte "
               "Charakterbilder und Sprachdateien werden noch nicht gerendert.")
    return (summary, list(catalog.chapters), list(catalog.scenes),
            list(catalog.characters), list(catalog.items), list(catalog.puzzles),
            list(catalog.recipes), list(catalog.dialogues), list(catalog.dialogue_nodes),
            list(catalog.dialogue_choices), list(catalog.assets), gallery, relationship_svg(raw))


def make_app():
    try:
        import gradio as gr
    except ImportError as exc:
        raise RuntimeError("Gradio ist nicht installiert: pip install -e '.[studio]'") from exc

    initial = canonical_story_json(parse_story_document(EXAMPLE.read_text(encoding="utf-8")))
    def selectors(raw: str):
        view = describe_story(raw)
        scene = view.scenes[0][0]
        item = view.items[0][0] if view.items else None
        puzzle = view.puzzles[0][0] if view.puzzles else None
        dialogue_nodes = parse_story_document(raw).dialogue_nodes
        node_id = dialogue_nodes[0].id if dialogue_nodes else None
        objects = room_items(raw, scene)
        selected_object = objects[0][1] if objects else None
        chapters = "\n".join(f"- {title} (`{id_}`)" for id_, title in view.chapters)
        path = " → ".join(view.playable_path)
        return (gr.update(choices=[(title, id_) for id_, title in view.scenes], value=scene),
                gr.update(choices=[(f"{name} ({scene_id})", id_) for id_, name, scene_id in view.items], value=item),
                gr.update(choices=[(title, id_) for id_, title in view.puzzles], value=puzzle),
                gr.update(choices=objects, value=selected_object),
                f"**Kapitel**\n{chapters}\n\n**Spielbarer Pfad:** {path}",
                *scene_fields(raw, scene), *item_fields(raw, item or ""),
                *puzzle_fields(raw, puzzle or ""), *position_fields(raw, selected_object or ""),
                safe_render_scene(raw, scene),
                gr.update(choices=[(f"{n.speaker_id}: {n.text[:48]}", n.id) for n in dialogue_nodes],
                          value=node_id),
                dialogue_line_fields(raw, node_id or ""),
                gr.update(**dialogue_speaker_fields(raw, node_id or "")), *catalog_view(raw))

    def load_file(file_path):
        if not file_path:
            raise gr.Error("Bitte eine Story-JSON-Datei wählen")
        try:
            raw = canonical_story_json(parse_story_document(Path(file_path).read_text(encoding="utf-8")))
            return (raw, *selectors(raw), "Story erfolgreich geladen und validiert")
        except (ValueError, OSError) as error:
            raise gr.Error(str(error)) from error

    def propose(action, raw, *args):
        try:
            edit = action(raw, *args)
            proposal = prepare_proposal(raw, edit)
            return proposal, "VORSCHAU – noch nicht übernommen:\n" + report_text(edit.report)
        except (ValueError, OSError) as error:
            raise gr.Error(str(error)) from error

    def propose_puzzle(raw, puzzle_id, title, required):
        ids = tuple(text.strip() for text in required.split(","))
        return propose(change_puzzle, raw, puzzle_id, title, ids)

    def propose_position(raw, item_id, x, y):
        if x is None or y is None or int(x) != x or int(y) != y:
            raise gr.Error("Koordinaten müssen ganze Zahlen sein")
        return propose(change_position, raw, item_id, int(x), int(y))

    def propose_ai(raw, request):
        from .ai_provider import generate_openai_operations
        try:
            proposal = propose_story_change(raw, request, generate_openai_operations)
            return proposal, "KI-VORSCHAU – noch nicht übernommen:\n" + report_text(proposal.edit.report)
        except ValueError as error:
            raise gr.Error(str(error)) from error

    def propose_imported(raw, response_json):
        try:
            proposal = preview_ai_response(raw, response_json)
            return proposal, "IMPORTIERTE VORSCHAU – noch nicht übernommen:\n" + report_text(proposal.edit.report)
        except (ValueError, TypeError) as error:
            raise gr.Error(str(error)) from error

    def choose_pixel(raw, scene_id, item_id, evt: gr.SelectData):
        if not item_id or item_id not in {id_ for _, id_ in room_items(raw, scene_id)}:
            raise gr.Error("Bitte zuerst ein sichtbares Objekt aus dieser Szene auswählen")
        if not isinstance(evt.index, (tuple, list)) or len(evt.index) != 2:
            raise gr.Error("Keine Pixelkoordinate ermittelt")
        x, y = evt.index
        width, height, *_ = scene_preview(raw, scene_id)
        return max(0, min(int(x), width - 16)), max(0, min(int(y), height - 16))

    def confirm(raw, proposal):
        if proposal is None:
            raise gr.Error("Bitte zuerst eine Änderung prüfen")
        try:
            updated = accept_proposal(raw, proposal)
            return (updated, None, *selectors(updated),
                    "ÜBERNOMMEN:\n" + report_text(proposal.edit.report))
        except ValueError as error:
            raise gr.Error(str(error)) from error

    def export_story(raw):
        canonical = canonical_story_json(parse_story_document(raw))
        path = Path(tempfile.mkdtemp(prefix="adventure-studio-export-")) / "story.json"
        path.write_text(canonical, encoding="utf-8")
        return str(path)

    def export_translations(raw, source_language):
        try:
            draft = translation_draft(raw, source_language)
        except ValueError as error:
            raise gr.Error(f"Übersetzungsentwurf nicht möglich: {error}") from error
        path = Path(tempfile.mkdtemp(prefix="adventure-studio-i18n-")) / "translations-draft.json"
        path.write_text(draft, encoding="utf-8")
        return str(path)

    def validate_translations(raw, file_path):
        if not file_path:
            raise gr.Error("Bitte einen ausgefüllten Übersetzungskatalog wählen")
        try:
            canonical = validate_translation_draft(raw, Path(file_path).read_text(encoding="utf-8"))
        except (ValueError, OSError) as error:
            raise gr.Error(f"Übersetzungskatalog ungültig: {error}") from error
        path = Path(tempfile.mkdtemp(prefix="adventure-studio-i18n-")) / "translations-validated.json"
        path.write_text(canonical, encoding="utf-8")
        return str(path)

    def export_scumm(raw, scummc_path):
        if not scummc_path.strip():
            raise gr.Error("Bitte den lokalen Pfad zur gebauten ScummC-Toolchain eingeben")
        folder = Path(tempfile.mkdtemp(prefix="adventure-studio-game-"))
        try:
            return str(export_playable(raw, Path(scummc_path.strip()), folder / "adventure.zip"))
        except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
            raise gr.Error(f"SCUMM-Export fehlgeschlagen: {error}") from error

    def native_selectors(raw, selected_room=None, selected_sequence=None,
                         selected_costume=None, selected_actor=None):
        rooms, objects, actors = project_choices(raw, selected_room)
        costumes = costume_names(raw)
        chosen_costume = selected_costume if selected_costume in costumes else (
            costumes[0] if costumes else None)
        room = selected_room if selected_room in rooms else rooms[0]
        sequences = sequence_choices(raw)
        identity = selected_sequence if selected_sequence in {value for _, value in sequences} else (
            sequences[0][1] if sequences else None)
        steps = sequence_steps(raw, identity) if identity else ()
        chosen_actor = selected_actor if selected_actor in actors else (actors[0] if actors else None)
        animations = actor_animations(raw, chosen_actor)
        initial = next((actor.initial_animation for actor in parse_document(raw).actors
                        if actor.id == chosen_actor), None)
        return (gr.update(choices=rooms, value=room),
                gr.update(choices=objects, value=objects[0] if objects else None),
                gr.update(choices=[("Ego (für gesprochene Zeile)", None),
                                   *[(item, item) for item in actors]], value=chosen_actor),
                gr.update(choices=animations, value=animations[0] if animations else None),
                gr.update(choices=[*[(f"Objekt: {name}", name) for name in objects],
                                   *[(f"Raum: {name}", name) for name in rooms],
                                   *[(f"Sound: {name}", name) for name in room_sound_ids(raw, room)]],
                          value=objects[0] if objects else room),
                gr.update(choices=sequences, value=identity),
                gr.update(choices=[(f"{i+1}. {text}", i) for i, text in enumerate(steps)],
                          value=0 if steps else None),
                "\n".join(f"{i+1}. {text}" for i, text in enumerate(steps)) or "Noch keine Schritte",
                gr.update(choices=costumes, value=chosen_costume),
                actor_summary(raw), costume_summary(raw, chosen_costume),
                gr.update(choices=[("Keine Startanimation", None), *[(name, name) for name in animations]],
                          value=initial))

    def native_load(file_path):
        if not file_path:
            raise gr.Error("Bitte native Projekt-JSON-Datei auswählen")
        try:
            raw = canonical_project_json(parse_document(Path(file_path).read_text(encoding="utf-8")))
            return raw, False, *native_selectors(raw), "Natives Projekt geladen und validiert"
        except (OSError, ValueError) as error:
            raise gr.Error(str(error)) from error

    def native_sync(story_raw, native_raw):
        try:
            raw = compose_story_project(story_raw, native_raw)
            return (raw, True, *native_selectors(raw),
                    "Story-Räume übernommen; native Actors und Aktionen geprüft. "
                    "Beim Export wird stets die aktuelle Story neu übersetzt.")
        except ValueError as error:
            raise gr.Error(f"Story und native Aktionen sind nicht kompatibel: {error}") from error

    def native_edit(action, raw, *args):
        if raw is None:
            raise gr.Error("Bitte zuerst eine native Projektdatei laden")
        try:
            updated = action(raw, *args)
            if action is append_sequence_step:
                room, hotspot, verb = args[:3]
                identity = f"{room}|{hotspot}|{verb}"
            else:
                identity = args[0]
                room = identity.split("|", 1)[0]
            return (updated, *native_selectors(updated, room, identity),
                    "Interaktionsablauf geändert und validiert")
        except (ValueError, OSError) as error:
            raise gr.Error(str(error)) from error

    def native_asset_edit(action, raw, *args):
        if raw is None:
            raise gr.Error("Bitte zuerst die Story als natives Projekt übernehmen")
        try:
            updated = action(raw, *args)
            chosen = (args[1] if action is create_costume else args[0]
                      if action in (add_costume_frame, set_costume_animation,
                                    set_costume_speaking_pose,
                                    set_costume_direction_speaking_pose,
                                    edit_costume_timeline) else
                      args[1] if action is add_actor else None)
            selected_actor = args[0] if action is set_actor_initial_animation else (
                args[0] if action is add_actor else None)
            actor_room = next((actor.room for actor in parse_document(updated).actors
                               if actor.id == selected_actor), None)
            return (updated, *native_selectors(updated, selected_room=actor_room,
                                              selected_costume=chosen,
                                              selected_actor=selected_actor),
                    "Actor-/Costume-Daten geändert und validiert")
        except (ValueError, OSError) as error:
            raise gr.Error(str(error)) from error

    def native_music_import(raw, room, music_id, file_path):
        if raw is None or not file_path:
            raise gr.Error("Bitte zuerst ein Projekt und eine MIDI-Datei wählen")
        try:
            updated = import_room_music(raw, room, music_id, file_path)
            return (updated, *native_selectors(updated, selected_room=room),
                    f"MIDI {music_id} für {room} gespeichert; ScummC erstellt die native SOUN-Ressource beim Export")
        except (ValueError, OSError) as error:
            raise gr.Error(str(error)) from error

    def native_sound_import(raw, room, sound_id, file_path):
        if raw is None or not file_path:
            raise gr.Error("Bitte zuerst ein Projekt und eine VOC-Datei wählen")
        try:
            updated = import_room_sound(raw, room, sound_id, file_path)
            return (updated, *native_selectors(updated, selected_room=room),
                    f"VOC {sound_id} für {room} gespeichert; ScummC erstellt die native SOUN-Ressource beim Export")
        except (ValueError, OSError) as error:
            raise gr.Error(str(error)) from error

    def native_download(raw, linked, story_raw):
        if raw is None:
            raise gr.Error("Bitte zuerst eine native Projektdatei laden")
        try:
            project = compose_story_project(story_raw, raw) if linked else canonical_project_json(parse_document(raw))
        except ValueError as error:
            raise gr.Error(f"Aktuelle Story ist nicht mit nativen Aktionen kompatibel: {error}") from error
        path = Path(tempfile.mkdtemp(prefix="adventure-studio-project-")) / "project.json"
        path.write_text(project, encoding="utf-8")
        return str(path)

    def native_game(raw, scummc_path, linked, story_raw, translation_file):
        if raw is None or not scummc_path.strip():
            raise gr.Error("Native Projektdatei und ScummC-Pfad sind erforderlich")
        path = Path(tempfile.mkdtemp(prefix="adventure-studio-native-game-")) / "adventure.zip"
        try:
            catalog_raw = (Path(translation_file).read_text(encoding="utf-8")
                           if translation_file else None)
            return str(export_native_project(raw, Path(scummc_path.strip()), path,
                                             story_raw=story_raw if linked else None,
                                             language_catalog_raw=catalog_raw))
        except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
            raise gr.Error(f"Nativer SCUMM-Export fehlgeschlagen: {error}") from error

    def native_animation_preview(raw, costume, animation, direction, frame_duration):
        if raw is None:
            raise gr.Error("Bitte zuerst eine native Costume erstellen oder laden")
        path = Path(tempfile.mkdtemp(prefix="adventure-studio-costume-preview-")) / "animation.gif"
        try:
            rendered = render_costume_preview(raw, costume, animation, direction,
                                              frame_duration, path)
            steps = costume_animation_steps(raw, costume, animation, direction)
            pictures = sum(step not in ("COUNT", "SHOW", "HIDE", "NOP") for step in steps)
            return (str(rendered),
                    f"{pictures} Bildframes · {int(frame_duration)} ms pro Bild (nur Editor-Vorschau). "
                    "COUNT/SHOW/HIDE/NOP werden nicht als Engine-Timing simuliert.")
        except (ValueError, OSError) as error:
            raise gr.Error(f"Costume-Vorschau nicht möglich: {error}") from error

    def studio_load(file_path):
        if not file_path:
            raise gr.Error("Bitte eine Studio-Projektdatei auswählen")
        try:
            story_raw, native_raw = parse_studio_project(Path(file_path).read_text(encoding="utf-8"))
            return (story_raw, None, *selectors(story_raw), "Gemeinsames Studio-Projekt geladen",
                    native_raw, True, *native_selectors(native_raw),
                    "Story, Actors, Costumes und Interaktionen gemeinsam geladen")
        except (ValueError, OSError) as error:
            raise gr.Error(f"Studio-Projekt kann nicht geladen werden: {error}") from error

    def studio_download(story_raw, native_raw):
        try:
            combined = canonical_studio_project(story_raw, native_raw)
        except ValueError as error:
            raise gr.Error(f"Studio-Projekt kann nicht gespeichert werden: {error}") from error
        path = Path(tempfile.mkdtemp(prefix="adventure-studio-authoring-")) / "adventure.studio.json"
        path.write_text(combined, encoding="utf-8")
        return str(path)

    with gr.Blocks(title="Adventure Studio") as app:
        gr.Markdown("# Adventure Studio\nStory schreiben, KI-Änderungen prüfen und als SCUMM-fähige Daten speichern.")
        state = gr.State(initial)
        pending = gr.State(None)
        with gr.Row():
            story_file = gr.File(label="Story-JSON öffnen", file_types=[".json"], type="filepath")
            export_button = gr.Button("Geprüfte Story exportieren", variant="primary")
            download = gr.File(label="Story herunterladen")
        with gr.Row():
            studio_file = gr.File(label="Gemeinsames Studio-Projekt öffnen", file_types=[".json"], type="filepath")
            studio_save_button = gr.Button("Gesamtes Studio-Projekt speichern", variant="primary")
            studio_download_file = gr.File(label="Studio-Projekt herunterladen")
        gr.Markdown("Das gemeinsame Projekt speichert Story und native Actors/Costumes/Interaktionsregeln ohne doppelte Raum-Bitmaps. Bisherige Story- und native Projekt-JSON-Dateien bleiben separat ladbar.")
        with gr.Row():
            source_language = gr.Dropdown(label="Quellsprache der Story",
                                          choices=[("Deutsch", "de"), ("Englisch", "en"),
                                                   ("Französisch", "fr"), ("Japanisch", "ja"),
                                                   ("Polnisch", "pl")], value="de")
            translations_button = gr.Button("Übersetzungsentwurf für 5 Sprachen erzeugen")
            translations_download = gr.File(label="Übersetzungsentwurf herunterladen")
        gr.Markdown("Der Entwurf enthält fehlende Übersetzungen als `null` und ist noch kein spielbares Sprachpaket. Autorisierte Story-Texte bleiben soweit eindeutig zuordenbar in Unicode erhalten; synthetische Compilertexte und mehrdeutig normalisierte Texte können weiterhin ASCII sein.")
        with gr.Accordion("Vollständige Übersetzungen prüfen", open=False):
            translation_file = gr.File(label="Ausgefüllten Übersetzungskatalog öffnen", file_types=[".json"], type="filepath")
            translation_validate_button = gr.Button("Übersetzungen gegen aktuelle Story prüfen")
            translation_validated_download = gr.File(label="Geprüften Katalog herunterladen")
        with gr.Accordion("Spielbares SCUMM-ZIP erzeugen (experimentell)", open=False):
            gr.Markdown("In Codespaces wird ScummC einmalig beim Einrichten installiert. Lokal kann alternativ ein vorhandener ScummC-Pfad angegeben werden. Der eigentliche Build benötigt keine Downloads und arbeitet auf einer temporären Kopie.")
            scummc_path = gr.Textbox(label="ScummC-Installationsordner (in Codespaces automatisch)",
                                     value=os.environ.get("ADVENTURE_STUDIO_SCUMMC", ""), placeholder="/opt/scummc")
            game_export_button = gr.Button("SCUMM-ZIP bauen")
            game_download = gr.File(label="Spielbares Adventure herunterladen")
        overview = gr.Markdown()
        with gr.Tab("Projektübersicht"):
            catalog_summary = gr.Markdown()
            with gr.Accordion("Kapitel", open=False):
                chapter_grid = gr.Dataframe(headers=["ID", "Titel", "Inhalt"], interactive=False)
            with gr.Accordion("Szenen", open=True):
                scene_grid = gr.Dataframe(headers=["ID", "Titel", "Kapitel", "Beschreibung"], interactive=False)
                room_gallery = gr.Gallery(label="Hintergrundbilder / Raumvorschauen", columns=2,
                                          object_fit="contain", height=270)
            with gr.Accordion("Charaktere", open=False):
                character_grid = gr.Dataframe(headers=["ID", "Name", "Szene", "Bildstatus"], interactive=False)
                gr.Markdown("Porträt- und Laufanimations-Referenzen sind im Storyformat v4 vorgesehen. Bilder werden erst dargestellt, sobald eine überprüfte Asset-Datei geladen werden kann.")
            with gr.Accordion("Gegenstände und Positionen", open=False):
                item_grid = gr.Dataframe(headers=["ID", "Name", "Szene", "Rolle", "Position X,Y"], interactive=False)
            with gr.Accordion("Aktionen, Rätsel und Rezepte", open=False):
                puzzle_grid = gr.Dataframe(headers=["ID", "Titel", "Szene", "Benötigt", "Öffnet"], interactive=False)
                recipe_grid = gr.Dataframe(headers=["ID", "Titel", "Zutaten", "Ergebnis"], interactive=False)
                gr.Markdown("Die Aktionsübersicht zeigt zurzeit deklarative Tür-Rätsel und Kombinationsrezepte. Dialoge und frei definierte Aktionen folgen in einer späteren Modellversion.")
            with gr.Accordion("Dialoge und Antworten", open=False):
                dialogue_grid = gr.Dataframe(headers=["ID", "Szene", "Startknoten"], interactive=False)
                dialogue_node_grid = gr.Dataframe(headers=["ID", "Dialog", "Sprecher", "Text", "Weiter"], interactive=False)
                dialogue_choice_grid = gr.Dataframe(headers=["ID", "Knoten", "Antworttext", "Weiter/Ende"], interactive=False)
                gr.Markdown("Einfache Gespräche und bis zu drei terminale Antwortzweige werden als SCUMM v6 exportiert. Mehrstufige Dialogbäume und spielverändernde Antworten sind noch nicht implementiert.")
            with gr.Accordion("Asset-Referenzen", open=False):
                asset_grid = gr.Dataframe(headers=["ID", "Zieltyp", "Ziel-ID", "Art", "Quelle"], interactive=False)
                gr.Markdown("Asset-IDs und SHA-256-Hashes sind versionierte Metadaten. Die Bilddateien selbst werden noch nicht aus externen Providern geladen.")
            with gr.Accordion("Beziehungsgraph", open=True):
                graph_view = gr.HTML(label="Story-Beziehungen")
        with gr.Tab("Szenen"):
            scene_select = gr.Dropdown(label="Szene")
            scene_title = gr.Textbox(label="Titel")
            scene_description = gr.Textbox(label="Beschreibung", lines=4)
            save_scene = gr.Button("Szenenänderung prüfen")
            preview = gr.Image(label="Raumvorschau (Hotspots markiert)", interactive=False)
            gr.Markdown("**Objekt platzieren:** Gegenstand auswählen und auf die Raumvorschau klicken. Die Position wird erst nach der Prüfung übernommen.")
            position_item = gr.Dropdown(label="Sichtbares Objekt in dieser Szene")
            with gr.Row():
                position_x = gr.Number(label="X (Pixel)", precision=0)
                position_y = gr.Number(label="Y (Pixel)", precision=0)
            save_position = gr.Button("Position prüfen")
        with gr.Tab("Gegenstände"):
            item_select = gr.Dropdown(label="Gegenstand")
            item_name = gr.Textbox(label="Name")
            item_description = gr.Textbox(label="Beschreibung", lines=3)
            save_item = gr.Button("Gegenstandsänderung prüfen")
            gr.Markdown("### Dekorationsobjekt hinzufügen\nEin neues Objekt bleibt in der Story; die einfache SCUMM-Vorschau positioniert es vorläufig automatisch.")
            new_id = gr.Textbox(label="Stabile Objekt-ID (z. B. Fridge)")
            new_name = gr.Textbox(label="Name")
            new_description = gr.Textbox(label="Beschreibung")
            add_item = gr.Button("Objekt hinzufügen: Vorschau")
        with gr.Tab("Rätsel"):
            puzzle_select = gr.Dropdown(label="Rätsel")
            puzzle_title = gr.Textbox(label="Rätseltitel")
            puzzle_items = gr.Textbox(label="Benötigte Gegenstands-IDs, mit Komma getrennt")
            save_puzzle = gr.Button("Rätseländerung prüfen")
        with gr.Tab("Dialogzeilen"):
            gr.Markdown("Gesprächszeilen bearbeiten und zusätzliche Antwortstufen anlegen. Antworten können zu einem vorhandenen Knoten (auch zum Gesprächseinstieg) zurückführen oder das Gespräch beenden. Änderungen werden vor der Übernahme auf Erreichbarkeit und einen möglichen Abschluss geprüft.")
            dialogue_node_select = gr.Dropdown(label="Dialogzeile")
            dialogue_text = gr.Textbox(label="Sprechtext", lines=4)
            dialogue_speaker = gr.Dropdown(label="Sprecher dieser Zeile")
            save_dialogue = gr.Button("Dialogänderung prüfen")
            dialogue_facing = gr.Dropdown(label="Blickrichtung beim Sprechen",
                                          choices=[("Keine Änderung", None), ("Norden", "N"),
                                                   ("Osten", "E"), ("Süden", "S"),
                                                   ("Westen", "W")], value=None)
            save_dialogue_facing = gr.Button("Blickrichtung prüfen")
            gr.Markdown("**Nächste Sprechzeile:** Eine abschließende Zeile ohne Antworten um eine weitere gesprochene Zeile ergänzen. So lassen sich lineare Gespräche mit Sprecherwechsel direkt im Studio aufbauen.")
            with gr.Row():
                dialogue_linear_id = gr.Textbox(label="Neue Sprechzeilen-ID")
                dialogue_linear_text = gr.Textbox(label="Text der nächsten Zeile")
                dialogue_linear_speaker = gr.Dropdown(label="Nächster Sprecher (leer: bisheriger Sprecher)")
            dialogue_linear_add = gr.Button("Sprechzeile anhängen: Änderung prüfen")
            gr.Markdown("**Neue Antwort am ausgewählten Dialogknoten:** Die Zielzeile kann auch eine bestehende Frage sein. Ohne Ziel beendet die Antwort das Gespräch.")
            with gr.Row():
                dialogue_answer_id = gr.Textbox(label="Neue Antwort-ID (z. B. AskAgain)")
                dialogue_answer_text = gr.Textbox(label="Antworttext")
                dialogue_answer_target = gr.Dropdown(label="Zielknoten", choices=[("Gespräch beenden", None)])
            dialogue_answer_add = gr.Button("Antwort hinzufügen: Änderung prüfen")
            gr.Markdown("**Bestehende Antwort bearbeiten:** Antworttext und Folgeknoten ändern, ohne die stabile Antwort-ID zu verlieren.")
            dialogue_edit_choice = gr.Dropdown(label="Antwort auswählen")
            with gr.Row():
                dialogue_edit_text = gr.Textbox(label="Antworttext bearbeiten")
                dialogue_edit_target = gr.Dropdown(label="Weiter zu", choices=[("Gespräch beenden", None)])
            dialogue_edit_save = gr.Button("Antwortänderung prüfen")
            gr.Markdown("**Antwort fortsetzen:** Eine bisher abschließende Antwort erhält eine neue gesprochene Zeile. Anschließend können an diese Zeile weitere Antworten angehängt werden.")
            with gr.Row():
                dialogue_terminal_choice = gr.Dropdown(label="Abschließende Antwort")
                dialogue_new_node_id = gr.Textbox(label="Neue Dialogknoten-ID")
                dialogue_new_node_text = gr.Textbox(label="Text der neuen Zeile")
                dialogue_new_speaker = gr.Dropdown(label="Sprecher der neuen Zeile (leer: bisheriger Sprecher)")
            dialogue_extend = gr.Button("Antwort mit neuem Knoten fortsetzen: Änderung prüfen")
        with gr.Tab("KI-Story-Regie"):
            gr.Markdown("Beschreibe die gewünschte Änderung. Die KI erzeugt nur Datenoperationen; Story-Solver und SCUMM-Compiler prüfen sie. **Erst der Button unten übernimmt Änderungen.** Für den kostenpflichtigen API-Aufruf müssen `OPENAI_API_KEY` und `pip install -e '.[studio,ai]'` konfiguriert sein.")
            ai_request = gr.Textbox(label="Was soll sich in der Story ändern?", lines=5,
                                    placeholder="Im Hafen steht ein kaputter Kühlschrank mit einer verschimmelten Ananas. Stelle ihn links neben die Tür.")
            ai_button = gr.Button("Mit KI Vorschlag erstellen")
            with gr.Accordion("Für andere KI-Anbieter: JSON-Operationen importieren", open=False):
                imported_json = gr.Textbox(label="Deklarative Operations-JSON", lines=5)
                import_button = gr.Button("JSON-Vorschlag deterministisch prüfen")
        with gr.Tab("Native Interaktionsabläufe"):
            gr.Markdown("Objekt-Verben mit Actor-Animationen, Pausen und Objektzuständen verknüpfen. **Story synchronisieren** erzeugt Räume aus deiner aktuellen Story und überträgt ausdrücklich nur Actors, Costumes und native Aktionsregeln aus dem geladenen Projekt. Andere native Raumänderungen werden dabei nicht übernommen. Bei inkompatiblen Referenzen wird abgebrochen.")
            native_state = gr.State(None)
            native_linked = gr.State(False)
            native_file = gr.File(label="Native Projekt-JSON öffnen", file_types=[".json"], type="filepath", elem_id="native-project-file")
            native_sync_button = gr.Button("Aktuelle Story als natives Projekt übernehmen / aktualisieren")
            with gr.Accordion("Actors und Costumes erstellen", open=True):
                gr.Markdown("Ein PNG wird in eine native 32-Farben-Costume mit Transparenzfarbe umgewandelt. Bilder mit mehr als 31 sichtbaren Farben werden auf 31 Farben reduziert. Weitere Frames behalten die vorhandenen Farben; ist die Palette voll, wird der Import mit einer klaren Meldung abgelehnt.")
                with gr.Row():
                    native_costume_file = gr.File(label="Costume-PNG", file_types=[".png"], type="filepath")
                    native_costume_name = gr.Textbox(label="Neue Costume-ID")
                    native_costume_button = gr.Button("Costume aus PNG erstellen")
                native_costume_select = gr.Dropdown(label="Vorhandene Costume", elem_id="native-costume-select")
                native_costume_summary = gr.Textbox(label="Frames und Animationen", lines=5, interactive=False)
                with gr.Row():
                    native_frame_file = gr.File(label="Weiteres Frame-PNG", file_types=[".png"], type="filepath")
                    native_frame_id = gr.Textbox(label="Neue Frame-ID")
                    native_frame_button = gr.Button("Frame zur Costume hinzufügen")
                gr.Markdown("**Sprechpose aus PNG:** Importiere oben ein zweites Frame und wähle es hier. Ein Klick setzt `gesture` (Index 24) und den nativen Sprechbeginn `talk_start` (Index 16) für alle vier Blickrichtungen. `talk_stop` (Index 20) verwendet die erhaltene Standpose.")
                with gr.Row():
                    native_speaking_frame = gr.Dropdown(label="Frame für die Sprechpose")
                    native_speaking_save = gr.Button("Frame als Sprechpose verwenden")
                gr.Markdown("**Richtungsspezifische Sprechpose:** Eine eigene PNG-Pose für Nord/Ost/Süd/West setzen. Die anderen Richtungen und die Standpose bleiben unverändert. Zuerst muss die Sprechpose oben angelegt sein.")
                with gr.Row():
                    native_speaking_direction = gr.Dropdown(label="Blickrichtung der Sprechpose", elem_id="native-speaking-direction",
                                                            choices=[("Nord", "N"), ("Ost", "E"),
                                                                     ("Süd", "S"), ("West", "W")], value="S")
                    native_direction_frame = gr.Dropdown(label="PNG-Frame dieser Richtung", elem_id="native-direction-frame")
                    native_direction_save = gr.Button("Sprechpose dieser Richtung speichern", elem_id="native-direction-save")
                gr.Markdown("**Animierte Sprechfolge:** Mehrere importierte PNG-Frame-IDs durch Komma trennen. Die native COST-Animation wiederholt die Bilder während der Dialogzeile; ihre Abspielgeschwindigkeit steuert ScummVM. Nur die gewählte Blickrichtung wird geändert, die Standpose bleibt erhalten.")
                with gr.Row():
                    native_speaking_sequence = gr.Textbox(label="Sprechframes in Reihenfolge", elem_id="native-speaking-sequence")
                    native_sequence_save = gr.Button("Animierte Sprechfolge speichern", elem_id="native-speaking-sequence-save")
                gr.Markdown("**Animation gestalten:** Frame-IDs in der gewünschten Reihenfolge durch Komma trennen. `COUNT`, `SHOW`, `HIDE` und `NOP` sind native Costume-Kommandos. Der Index muss durch vier teilbar sein; `gesture` verwendet zunächst 24.")
                with gr.Row():
                    native_anim_name = gr.Textbox(label="Animationsname", value="gesture")
                    native_anim_index = gr.Number(label="Nativer Index", value=24, precision=0)
                    native_anim_direction = gr.Dropdown(label="Animationsrichtung", choices=["N", "E", "S", "W"], value="S")
                    native_anim_commands = gr.Textbox(label="Frame- und COUNT-Folge", value="Pose0")
                    native_anim_loop = gr.Checkbox(label="Wiederholen", value=False)
                native_anim_button = gr.Button("Animation für diese Richtung speichern")
                with gr.Accordion("Visuelle Animationsfolge", open=True):
                    gr.Markdown("Wähle eine vorhandene Animation und Blickrichtung. Jeder Frame und jedes native COST-Kommando wird in Reihenfolge gezeigt. Du kannst einen Schritt anklicken, verschieben oder entfernen sowie einen Frame bzw. ein Kommando anhängen.")
                    native_timeline_animation = gr.Dropdown(label="Animation auswählen")
                    native_timeline_gallery = gr.Gallery(label="Frame- und Kommando-Timeline", columns=6,
                                                         object_fit="contain", height=180)
                    native_timeline_step = gr.Dropdown(label="Schritt der Animation")
                    native_timeline_command = gr.Dropdown(label="Frame/Kommando anhängen")
                    with gr.Row():
                        native_timeline_append = gr.Button("Anhängen")
                        native_timeline_up = gr.Button("Nach links")
                        native_timeline_down = gr.Button("Nach rechts")
                        native_timeline_remove = gr.Button("Entfernen")
                    with gr.Row():
                        native_preview_duration = gr.Number(label="Vorschau-Millisekunden pro Bild",
                                                            value=180, precision=0)
                        native_preview_button = gr.Button("Animation abspielen")
                    native_preview_image = gr.Image(label="Animierte Costume-Vorschau (GIF)",
                                                    interactive=False, format="gif")
                    native_preview_report = gr.Markdown()
                with gr.Row():
                    native_actor_id = gr.Textbox(label="Actor-ID")
                    native_actor_name = gr.Textbox(label="Anzeigename")
                    native_actor_x = gr.Number(label="Position X", value=320, precision=0)
                    native_actor_y = gr.Number(label="Position Y", value=120, precision=0)
                    native_actor_direction = gr.Dropdown(label="Blickrichtung", choices=["N", "E", "S", "W"], value="S")
                native_actor_button = gr.Button("Actor im gewählten Raum anlegen")
                native_actor_move = gr.Button("Ausgewählten Actor an diese Position bewegen")
                native_actor_costume_save = gr.Button("Ausgewähltem Actor diese Costume zuweisen")
                native_actor_list = gr.Textbox(label="Actors im Projekt", lines=4, interactive=False)
                with gr.Row():
                    native_actor_initial = gr.Dropdown(label="Startanimation des ausgewählten Actors",
                                                       choices=[("Keine Startanimation", None)])
                    native_actor_initial_save = gr.Button("Startanimation speichern")
            with gr.Row():
                native_room = gr.Dropdown(label="Raum")
                native_hotspot = gr.Dropdown(label="Auslösendes Objekt")
                native_verb = gr.Dropdown(label="Verb", choices=["Push", "Pull", "Open", "Close"], value="Open")
            with gr.Row():
                native_music_file = gr.File(label="Raummusik als MIDI importieren", file_types=[".mid", ".midi"], type="filepath")
                native_music_id = gr.Textbox(label="Musik-ID", value="RoomTheme")
                native_music_add = gr.Button("MIDI dem Raum zuweisen")
            with gr.Row():
                native_sound_file = gr.File(label="Soundeffekt als VOC importieren", file_types=[".voc"], type="filepath")
                native_sound_id = gr.Textbox(label="Sound-ID", value="EffectSound")
                native_sound_add = gr.Button("VOC dem Raum zuweisen")
            with gr.Row():
                native_kind = gr.Dropdown(label="Aktion hinzufügen / bearbeiten", choices=["Actor animieren", "Actor versetzen", "Actor laufen lassen", "Auf Actor warten", "Actor drehen", "Warten", "Objektzustand setzen", "Gegenstand aufnehmen", "Inventar kombinieren", "Raum wechseln", "Musik starten", "Musik stoppen", "Sound starten", "Sound stoppen", "Gesprochene Zeile"], value="Actor animieren")
                native_actor = gr.Dropdown(label="Actor")
                native_animation = gr.Dropdown(label="Costume-Animation")
                native_target = gr.Dropdown(label="Zielobjekt / Zielraum")
                native_amount = gr.Number(label="Sekunden / Objektzustand (0–2)", value=1, precision=0)
            with gr.Row():
                native_move_x = gr.Number(label="Actor-Ziel X (Versetzen/Laufen)", value=320, precision=0)
                native_move_y = gr.Number(label="Actor-Ziel Y (Versetzen/Laufen)", value=100, precision=0)
                native_face_direction = gr.Dropdown(label="Blickrichtung (Actor drehen)",
                                                    choices=["N", "E", "S", "W"], value="S")
            native_subtitle = gr.Textbox(label="Untertitel für gesprochene Zeile (Unicode, maximal 160 Zeichen)",
                                         placeholder="Text, den die Spielfigur spricht")
            gr.Markdown("**Actor laufen lassen** startet den nativen Weg zum Ziel. Mit **Auf Actor warten** kannst du die nachfolgenden Schritte bis zum Ende seiner Laufbewegung anhalten.")
            native_add = gr.Button("Schritt an Interaktion anhängen", variant="primary")
            native_sequence = gr.Dropdown(label="Vorhandene Interaktion")
            native_add_selected = gr.Button("Schritt an ausgewählte Variante anhängen")
            with gr.Row():
                native_condition_object = gr.Dropdown(
                    label="Interaktion nur bei Objektzustand", choices=[("Immer ausführen", None)])
                native_condition_state = gr.Number(label="Erforderlicher Zustand (0–2)",
                                                   value=0, precision=0)
                native_condition_save = gr.Button("Bedingung speichern")
                native_variant_add = gr.Button("Alternative Zustandsvariante duplizieren")
            gr.Markdown("Mehrere Varianten desselben Verbs dürfen unterschiedliche Zustände **desselben Raumobjekts** abdecken. Eine Variante ohne Bedingung dient als Fallback. Nach dem Duplizieren die Schritte der neuen Variante bearbeiten.")
            with gr.Row():
                native_skippable = gr.Checkbox(label="Mit Escape überspringbar", value=False)
                native_skip_save = gr.Button("Skip-Einstellung speichern")
            gr.Markdown("Beim Überspringen übernimmt SCUMM die **letzten Objektzustände, Actor-Zielpositionen und Blickrichtungen sowie Inventaraufnahmen und -kombinationen** der Sequenz. Für *Inventar kombinieren* ein Ergebnisobjekt mit vorhandener Raum-Kombinationsregel wählen. *Raum wechseln* muss der letzte Schritt sein; der Wechsel erfolgt nach dem normalen Ablauf oder nach Escape und dem Setzen aller Endzustände.")
            gr.Markdown("*Musik starten/stoppen* nutzt die MIDI-Ressource des Sequenzraums. Beim Escape wird der letzte Musikzustand der Folge ausgeführt. Die Raumzuweisung startet Musik auch beim normalen Betreten des Raums.")
            gr.Markdown("*Sound starten/stoppen* verwendet einen zuvor für den Raum importierten VOC-Effekt. Mehrere Effekte bleiben unabhängig; beim Escape wird der jeweils letzte Zustand pro Sound gesetzt.")
            native_step = gr.Dropdown(label="Schritt auswählen")
            native_steps = gr.Textbox(label="Geordnete Schritte", lines=6, interactive=False)
            gr.Markdown("**Mehrsprachige VOC-Zeile:** Wähle eine *Gesprochene Zeile*, dann ergänze pro Sprache einen Untertitel und eine importierte VOC-Aufnahme. Die sichtbaren Sprachkürzel im Spiel schalten die Variante um; nicht übersetzte Zeilen verwenden die Standardsprache.")
            with gr.Row():
                native_default_voice = gr.Textbox(label="Standardsprache (ISO-Code, z. B. en)", value="en")
                native_default_voice_save = gr.Button("Standardsprache speichern")
            with gr.Row():
                native_voice_language = gr.Textbox(label="Weitere Sprache (z. B. de)", value="de")
                native_voice_sound = gr.Dropdown(label="VOC der Sprachvariante")
            native_voice_text = gr.Textbox(label="Übersetzter Untertitel")
            with gr.Row():
                native_voice_add = gr.Button("Sprachvariante hinzufügen / aktualisieren")
                native_voice_remove = gr.Button("Sprachvariante entfernen")
            gr.Markdown("**Dialog-Stimmen:** Ordne einer NPC-Gesprächszeile eine zuvor importierte VOC-Aufnahme zu. Zuerst die Standardsprache, danach weitere Sprachen auswählen. Der gesprochene Text stammt aus der Story-Übersetzung.")
            native_dialogue_line = gr.Dropdown(label="NPC-Dialogzeile (Öffnung oder Antwort)")
            with gr.Row():
                native_dialogue_language = gr.Textbox(label="Sprache der Aufnahme (z. B. en)", value="en")
                native_dialogue_sound = gr.Dropdown(label="VOC-Aufnahme für Dialogzeile")
            with gr.Row():
                native_dialogue_voice_save = gr.Button("Dialogaufnahme zuweisen / ersetzen")
                native_dialogue_voice_remove = gr.Button("Dialogaufnahme entfernen")
            gr.Markdown("**Sprecher-Animation:** Wähle eine Dialogzeile mit nativem Actor und eine seiner indizierten Costume-Animationen. Der Actor startet die Geste während der Sprechzeile. Für die Rückkehr zur Standpose muss zusätzlich die Costume-Animation `stand` den nativen Stand-Index 12 besitzen (bei neuen PNG-Costumes automatisch). Beide Animationen müssen die gewünschte Blickrichtung unterstützen.")
            with gr.Row():
                native_dialogue_animation_line = gr.Dropdown(label="Sprecher-Dialogzeile", elem_id="native-dialogue-line")
                native_dialogue_animation = gr.Dropdown(label="Costume-Animation", elem_id="native-dialogue-animation")
            with gr.Row():
                native_dialogue_speaking_frame = gr.Dropdown(label="PNG-Sprechpose dieser Zeile (gespeicherte Pose vorausgewählt)", elem_id="native-dialogue-pose")
                native_dialogue_speaking_apply = gr.Button("PNG-Sprechpose dieser Zeile zuweisen", elem_id="native-dialogue-pose-apply")
            gr.Markdown("**Eigene animierte Sprechfolge für diese Zeile:** Importierte PNG-Frame-IDs in Abspielreihenfolge durch Komma trennen. Die Folge kann für alle Richtungen oder gezielt für die unten gewählte Richtung gespeichert werden. Andere Richtungen, Dialogzeilen und globale Sprechframes bleiben erhalten. Die Geschwindigkeit bestimmt ScummVM.")
            with gr.Row():
                native_dialogue_speaking_sequence = gr.Textbox(label="Sprechframes dieser Dialogzeile", elem_id="native-dialogue-speaking-sequence")
                native_dialogue_sequence_apply = gr.Button("Für alle Richtungen speichern", elem_id="native-dialogue-sequence-apply")
            native_dialogue_speaking_preview = gr.Image(
                label="PNG-Sprechpose · echte Costume-Pixel (Editor-Vorschau)",
                interactive=False, type="pil", height=270,
                elem_id="native-dialogue-pose-preview")
            native_dialogue_direction = gr.Dropdown(
                label="Blickrichtung der gespeicherten Sprechanimation",
                choices=[("Nord", "N"), ("Ost", "E"), ("Süd", "S"), ("West", "W")],
                value="S", elem_id="native-dialogue-direction")
            with gr.Accordion("PNG-Datei direkt für diese Dialogzeile importieren", open=False):
                gr.Markdown("Importiere eine **neue PNG-Datei** in die eigene Costume der gewählten Sprecherfigur. Der Frame wird sofort an die Sprech- oder Abschlussfolge **dieser Zeile und Blickrichtung** angehängt. Bestehende Frames und die anderen Richtungen bleiben erhalten. Falls mehrere Figuren dieselbe Costume nutzen, **erst unten eine private Kopie für den gewählten Sprecher erstellen**. Andere Figuren behalten die bisherige Costume. Bei ungültigen Pixeln oder voller nativer Palette wird nichts gespeichert.")
                native_dialogue_costume_isolation = gr.Textbox(
                    label="Vorschau: Costume dieser Sprecherfigur trennen",
                    interactive=False, elem_id="native-dialogue-costume-isolation")
                native_dialogue_costume_isolate = gr.Button(
                    "Eigene Costume für diese Sprecherfigur erstellen",
                    elem_id="native-dialogue-costume-isolate")
                with gr.Row():
                    native_dialogue_png_file = gr.File(
                        label="Neues PNG-Bild", file_types=[".png"], type="filepath",
                        elem_id="native-dialogue-png-file")
                    native_dialogue_png_id = gr.Textbox(
                        label="Neue native Frame-ID", elem_id="native-dialogue-png-id")
                    native_dialogue_png_target = gr.Dropdown(
                        label="An welche Folge anhängen?",
                        choices=["Sprechfolge", "Abschlussfolge"], value="Sprechfolge",
                        elem_id="native-dialogue-png-target")
                native_dialogue_png_import = gr.Button(
                    "PNG importieren und Frame anhängen", elem_id="native-dialogue-png-import")
                gr.Markdown("**Mehrere PNGs in einem Schritt:** Dateien auswählen, sortieren, ausschließen, wieder aufnehmen, ein Bild ersetzen oder dessen native Frame-ID ändern. **Sprite-Sheet-Frames hinzufügen** zerlegt ein PNG-Raster zeilenweise in zusätzliche Bilder. **Freie Frame-ID vergeben** löst den Konflikt des gewählten Bilds; **Alle Frame-ID-Konflikte beheben** repariert den gesamten vorbereiteten Stapel, ohne bereits freie IDs zu verändern. Die ursprünglichen Upload-Dateikarten bleiben unverändert; verbindlich sind die **Importauswahl und Bildvorschau** unten. Nur eine neue Mehrfach-Dateiauswahl setzt die Bearbeitung zurück. Ungültige PNGs, doppelte IDs oder eine volle Palette verhindern den gesamten Import ohne Teiländerungen.")
                native_dialogue_png_batch_files = gr.File(
                    label="Mehrere PNG-Dateien in Abspielreihenfolge", file_types=[".png"],
                    file_count="multiple", type="filepath", elem_id="native-dialogue-png-batch-files")
                with gr.Row():
                    native_dialogue_sprite_sheet = gr.File(
                        label="PNG-Sprite-Sheet (gleichmäßiges Raster)",
                        file_types=[".png"], type="filepath", file_count="single",
                        elem_id="native-dialogue-sprite-sheet")
                    native_dialogue_sprite_columns = gr.Number(
                        label="Spalten", value=2, precision=0,
                        elem_id="native-dialogue-sprite-columns")
                    native_dialogue_sprite_rows = gr.Number(
                        label="Zeilen", value=1, precision=0,
                        elem_id="native-dialogue-sprite-rows")
                    native_dialogue_sprite_add = gr.Button(
                        "Sprite-Sheet-Frames hinzufügen",
                        elem_id="native-dialogue-sprite-add")
                native_dialogue_png_batch_order = gr.State(None)
                native_dialogue_png_batch_paths = gr.State(None)
                native_dialogue_png_batch_frame_ids = gr.State({})
                native_dialogue_png_batch_selected = gr.Dropdown(
                    label="PNG in der Importauswahl bearbeiten", choices=[],
                    elem_id="native-dialogue-png-batch-selected")
                with gr.Row():
                    native_dialogue_png_batch_id = gr.Textbox(
                        label="Native Frame-ID des gewählten PNGs",
                        elem_id="native-dialogue-png-batch-id")
                    native_dialogue_png_batch_set_id = gr.Button(
                        "Frame-ID übernehmen", elem_id="native-dialogue-png-batch-set-id")
                    native_dialogue_png_batch_suggest_id = gr.Button(
                        "Freie Frame-ID vergeben", elem_id="native-dialogue-png-batch-suggest-id")
                native_dialogue_png_batch_resolve_ids = gr.Button(
                    "Alle Frame-ID-Konflikte beheben",
                    elem_id="native-dialogue-png-batch-resolve-ids")
                with gr.Row():
                    native_dialogue_png_batch_up = gr.Button(
                        "↑ Nach oben", elem_id="native-dialogue-png-batch-up")
                    native_dialogue_png_batch_down = gr.Button(
                        "↓ Nach unten", elem_id="native-dialogue-png-batch-down")
                    native_dialogue_png_batch_remove = gr.Button(
                        "Aus Import entfernen", elem_id="native-dialogue-png-batch-remove")
                with gr.Row():
                    native_dialogue_png_batch_replacement = gr.File(
                        label="Ersatz-PNG für das gewählte Bild", file_types=[".png"],
                        file_count="single", type="filepath",
                        elem_id="native-dialogue-png-batch-replacement")
                    native_dialogue_png_batch_replace = gr.Button(
                        "Gewähltes PNG ersetzen", elem_id="native-dialogue-png-batch-replace")
                native_dialogue_png_batch_excluded = gr.Dropdown(
                    label="Ausgeschlossene PNGs wieder aufnehmen", choices=[],
                    elem_id="native-dialogue-png-batch-excluded")
                native_dialogue_png_batch_restore = gr.Button(
                    "Ausgewähltes PNG wieder aufnehmen",
                    elem_id="native-dialogue-png-batch-restore")
                native_dialogue_png_batch_plan = gr.Textbox(
                    label="Verbindliche Importauswahl: Reihenfolge und native Frame-IDs",
                    interactive=False,
                    lines=4, elem_id="native-dialogue-png-batch-plan")
                native_dialogue_png_batch_gallery = gr.Gallery(
                    label="PNG-Miniaturen in nativer Abspielreihenfolge (vor dem Import)",
                    columns=6, object_fit="contain", height=180,
                    elem_id="native-dialogue-png-batch-gallery")
                native_dialogue_png_batch_image_issues = gr.Textbox(
                    label="Bildbezogene Importkonflikte (⚠️ markiert betroffene Miniaturen)",
                    lines=2, interactive=False,
                    elem_id="native-dialogue-png-batch-image-issues")
                with gr.Row():
                    native_dialogue_png_batch_previous = gr.Button(
                        "← Vorheriges Bild", elem_id="native-dialogue-png-batch-previous")
                    native_dialogue_png_batch_next = gr.Button(
                        "Nächstes Bild →", elem_id="native-dialogue-png-batch-next")
                native_dialogue_png_batch_frame_image = gr.Image(
                    label="Gewähltes PNG vor dem Import", interactive=False, height=180,
                    elem_id="native-dialogue-png-batch-frame-image")
                native_dialogue_png_batch_frame_status = gr.Markdown()
                with gr.Row():
                    native_dialogue_png_batch_duration = gr.Number(
                        label="Editor-Vorschau: Millisekunden pro Bild", value=180,
                        precision=0, elem_id="native-dialogue-png-batch-duration")
                    native_dialogue_png_batch_play = gr.Button(
                        "Importfolge vorab abspielen", elem_id="native-dialogue-png-batch-play")
                native_dialogue_png_batch_animation = gr.Image(
                    label="Noch nicht importierte PNG-Folge · nur Editor-GIF",
                    interactive=False, format="gif", elem_id="native-dialogue-png-batch-animation")
                native_dialogue_png_batch_animation_status = gr.Markdown()
                native_dialogue_png_batch_readiness = gr.Markdown(
                    "Bitte PNGs und eine native Dialogzeile auswählen",
                    elem_id="native-dialogue-png-batch-readiness")
                native_dialogue_png_batch_import = gr.Button(
                    "Alle PNGs als geordnete Folge importieren",
                    interactive=False, elem_id="native-dialogue-png-batch-import")
            native_dialogue_direction_sequence_apply = gr.Button(
                "Nur Sprechfolge dieser Blickrichtung speichern",
                elem_id="native-dialogue-direction-sequence-apply")
            with gr.Accordion("Grafische Sprechfolge dieser Zeile und Blickrichtung", open=True):
                gr.Markdown("Wähle ein Frame in der Timeline. Füge importierte PNG-Frames an, ändere ihre Reihenfolge oder entferne sie. Jede Änderung wird sofort für **diese Zeile und Richtung** gespeichert. Die GIF-Geschwindigkeit dient ausschließlich der Editor-Vorschau; das native Timing bestimmt ScummVM.")
                native_dialogue_timeline_gallery = gr.Gallery(
                    label="PNG-Framefolge · native COST-Reihenfolge", columns=6,
                    object_fit="contain", height=180, elem_id="native-dialogue-timeline-gallery")
                with gr.Row():
                    native_dialogue_timeline_step = gr.Dropdown(
                        label="Gewähltes Frame", elem_id="native-dialogue-timeline-step")
                    native_dialogue_timeline_add_frame = gr.Dropdown(
                        label="PNG-Frame anhängen", elem_id="native-dialogue-timeline-add-frame")
                with gr.Row():
                    native_dialogue_timeline_append = gr.Button("Frame anhängen", elem_id="native-dialogue-timeline-append")
                    native_dialogue_timeline_left = gr.Button("Nach links", elem_id="native-dialogue-timeline-left")
                    native_dialogue_timeline_right = gr.Button("Nach rechts", elem_id="native-dialogue-timeline-right")
                    native_dialogue_timeline_remove = gr.Button("Entfernen", elem_id="native-dialogue-timeline-remove")
                with gr.Row():
                    native_dialogue_timeline_duration = gr.Number(
                        label="Editor-Vorschau: Millisekunden pro Bild", value=180, precision=0,
                        elem_id="native-dialogue-timeline-duration")
                    native_dialogue_timeline_play = gr.Button("Sprechfolge abspielen", elem_id="native-dialogue-timeline-play")
                native_dialogue_timeline_preview_image = gr.Image(
                    label="Animierte Sprechfolge · nur Editor-GIF", interactive=False,
                    format="gif", elem_id="native-dialogue-timeline-preview")
                native_dialogue_timeline_preview_status = gr.Markdown()
            native_dialogue_direction_preview = gr.Image(
                label="Native Sprechanimation · gewählte Blickrichtung (Einzelbild-Vorschau)",
                interactive=False, type="pil", height=270,
                elem_id="native-dialogue-direction-preview")
            native_dialogue_direction_status = gr.Textbox(
                label="Richtungsvorschau-Status", interactive=False,
                elem_id="native-dialogue-direction-status")
            native_dialogue_reset = gr.Checkbox(label="Nach der Sprechzeile zur Standpose zurückkehren",
                                                value=True, elem_id="native-dialogue-reset")
            with gr.Accordion("Native Sprechphasen dieser Dialogzeile", open=True):
                gr.Markdown("**Textbeginn → Vorlauf → native Sprechgeste → Mindestlaufzeit → Ende des Dialogtexts abwarten → Standpose.** Beide Werte sind ganze native `delay`-Ticks des SCUMM-v6-Skripts, keine Millisekunden oder automatische Wort-Synchronisation. Bei 0 entfällt die jeweilige Verzögerung. Erst eine Sprechanimation zuweisen, dann die Phasen speichern.")
                with gr.Row():
                    native_dialogue_phase_start = gr.Number(
                        label="Vorlauf bis Sprechgeste (native Ticks)", precision=0,
                        value=1, elem_id="native-dialogue-phase-start")
                    native_dialogue_phase_minimum = gr.Number(
                        label="Mindestlaufzeit vor Dialogende-Wait (native Ticks)",
                        precision=0, value=60, elem_id="native-dialogue-phase-minimum")
                    native_dialogue_phase_save = gr.Button(
                        "Sprechphasen dieser Zeile speichern",
                        elem_id="native-dialogue-phase-save")
            with gr.Accordion("Optionale Abschlussgeste dieser Dialogzeile", open=True):
                gr.Markdown("Nach dem tatsächlichen Ende des Dialogtexts (`waitForMessage`) startet die optionale native Abschlussgeste. Du kannst eine bestehende Costume-Animation wählen **oder hier direkt eine eigene PNG-Framefolge für die gewählte Blickrichtung erstellen**. Andere Richtungen und Dialogzeilen bleiben erhalten. Die Laufzeit wird in nativen Skript-Ticks angegeben.")
                with gr.Row():
                    native_dialogue_ending_animation = gr.Dropdown(
                        label="Costume-Abschlussanimation", elem_id="native-dialogue-ending-animation")
                    native_dialogue_ending_ticks = gr.Number(
                        label="Abschlussgeste zeigen (native Ticks)", value=12, precision=0,
                        elem_id="native-dialogue-ending-ticks")
                native_dialogue_ending_gallery = gr.Gallery(
                    label="Abschluss-PNG-Folge · gewählte Blickrichtung", columns=6,
                    object_fit="contain", height=180, elem_id="native-dialogue-ending-gallery")
                with gr.Row():
                    native_dialogue_ending_step = gr.Dropdown(
                        label="Abschlussframe", elem_id="native-dialogue-ending-step")
                    native_dialogue_ending_frame = gr.Dropdown(
                        label="Importiertes PNG-Frame anhängen", elem_id="native-dialogue-ending-frame")
                with gr.Row():
                    native_dialogue_ending_append = gr.Button(
                        "Abschlussframe anhängen", elem_id="native-dialogue-ending-append")
                    native_dialogue_ending_left = gr.Button(
                        "Nach links", elem_id="native-dialogue-ending-left")
                    native_dialogue_ending_right = gr.Button(
                        "Nach rechts", elem_id="native-dialogue-ending-right")
                    native_dialogue_ending_delete_frame = gr.Button(
                        "Frame entfernen", elem_id="native-dialogue-ending-delete-frame")
                with gr.Row():
                    native_dialogue_ending_preview_duration = gr.Number(
                        label="Editor-Vorschau: ms pro Bild", value=180, precision=0,
                        elem_id="native-dialogue-ending-preview-duration")
                    native_dialogue_ending_play = gr.Button(
                        "Abschlussfolge abspielen", elem_id="native-dialogue-ending-play")
                native_dialogue_ending_preview = gr.Image(
                    label="Abschlussfolge · nur Editor-GIF", interactive=False,
                    format="gif", elem_id="native-dialogue-ending-preview")
                with gr.Row():
                    native_dialogue_ending_save = gr.Button(
                        "Abschlussgeste dieser Zeile speichern", elem_id="native-dialogue-ending-save")
                    native_dialogue_ending_remove = gr.Button(
                        "Abschlussgeste entfernen", elem_id="native-dialogue-ending-remove")
            with gr.Row():
                native_dialogue_animation_save = gr.Button("Sprechanimation zuweisen")
                native_dialogue_animation_remove = gr.Button("Sprechanimation entfernen")
            with gr.Row():
                native_replace = gr.Button("Ausgewählten Schritt mit Formularwerten ersetzen")
                native_up = gr.Button("Schritt nach oben")
                native_down = gr.Button("Schritt nach unten")
                native_remove = gr.Button("Schritt entfernen")
            native_report = gr.Textbox(label="Projektstatus", interactive=False, elem_id="native-project-report")
            with gr.Row():
                native_json_button = gr.Button("Validiertes Projekt herunterladen", elem_id="native-project-export-button")
                native_json_download = gr.File(label="Native Projekt-JSON", elem_id="native-project-export-file")
            native_translation_file = gr.File(
                label="Optional: vollständiger Story-Sprachkatalog (language-catalog.json)",
                file_types=[".json"], type="filepath")
            gr.Markdown("Wird ein Sprachkatalog geladen, übersetzt der native Export Story-Texte und VOC-Untertitel gemeinsam. Die Quellsprache muss der VOC-Standardsprache entsprechen; jede VOC-Sprache muss im Katalog stehen.")
            native_game_button = gr.Button("Natives SCUMM-ZIP bauen")
            native_game_download = gr.File(label="SCUMM-Spiel")
        report = gr.Textbox(label="Deterministischer Änderungs- und Prüfbericht", lines=7, interactive=False)
        confirm_button = gr.Button("Geprüfte Änderung jetzt übernehmen", variant="primary")

        refreshed = [scene_select, item_select, puzzle_select, position_item, overview, scene_title,
                     scene_description, item_name, item_description, puzzle_title, puzzle_items,
                     position_x, position_y, preview, dialogue_node_select, dialogue_text,
                     dialogue_speaker,
                     catalog_summary, chapter_grid, scene_grid,
                     character_grid, item_grid, puzzle_grid, recipe_grid, dialogue_grid,
                     dialogue_node_grid, dialogue_choice_grid, asset_grid, room_gallery, graph_view]
        app.load(selectors, inputs=[state], outputs=refreshed)
        def load_and_clear(file_path):
            raw, *rest = load_file(file_path)
            return (raw, None, *rest)

        story_file.change(load_and_clear, inputs=[story_file], outputs=[state, pending, *refreshed, report])
        scene_select.change(scene_fields, inputs=[state, scene_select], outputs=[scene_title, scene_description])
        scene_select.change(safe_render_scene, inputs=[state, scene_select], outputs=[preview])
        def update_room_objects(raw, scene_id):
            choices = room_items(raw, scene_id)
            item_id = choices[0][1] if choices else None
            return gr.update(choices=choices, value=item_id), *position_fields(raw, item_id or "")

        scene_select.change(update_room_objects, inputs=[state, scene_select],
                            outputs=[position_item, position_x, position_y])
        position_item.change(position_fields, inputs=[state, position_item],
                             outputs=[position_x, position_y])
        preview.select(choose_pixel, inputs=[state, scene_select, position_item],
                       outputs=[position_x, position_y])
        item_select.change(item_fields, inputs=[state, item_select], outputs=[item_name, item_description])
        puzzle_select.change(puzzle_fields, inputs=[state, puzzle_select], outputs=[puzzle_title, puzzle_items])
        dialogue_node_select.change(dialogue_line_fields, inputs=[state, dialogue_node_select], outputs=[dialogue_text])
        dialogue_node_select.change(dialogue_facing_fields,
                                    inputs=[state, dialogue_node_select], outputs=[dialogue_facing])
        dialogue_node_select.change(lambda raw, node: gr.update(**dialogue_speaker_fields(raw, node)),
                                    inputs=[state, dialogue_node_select], outputs=[dialogue_speaker])
        def next_linear_speakers(raw, node_id):
            options = dialogue_speaker_fields(raw, node_id)
            return gr.update(choices=[("Bisherigen Sprecher übernehmen", None)] + options["choices"],
                             value=None)
        dialogue_node_select.change(next_linear_speakers,
                                    inputs=[state, dialogue_node_select], outputs=[dialogue_linear_speaker])
        save_scene.click(lambda *args: propose(change_scene, *args),
                         [state, scene_select, scene_title, scene_description], [pending, report])
        save_item.click(lambda *args: propose(change_item, *args),
                        [state, item_select, item_name, item_description], [pending, report])
        add_item.click(lambda *args: propose(add_decoration, *args),
                       [state, scene_select, new_id, new_name, new_description], [pending, report])
        save_puzzle.click(propose_puzzle, [state, puzzle_select, puzzle_title, puzzle_items],
                          [pending, report])
        save_dialogue.click(lambda *args: propose(change_dialogue_line, *args),
                            [state, dialogue_node_select, dialogue_text, dialogue_speaker], [pending, report])
        save_dialogue_facing.click(lambda *args: propose(change_dialogue_facing, *args),
                                   [state, dialogue_node_select, dialogue_facing], [pending, report])
        dialogue_linear_add.click(lambda *args: propose(extend_dialogue_line, *args),
                                  [state, dialogue_node_select, dialogue_linear_id,
                                   dialogue_linear_text, dialogue_linear_speaker], [pending, report])
        state.change(lambda raw: gr.update(
            choices=[("Gespräch beenden", None)] + [(node.id, node.id)
                for node in parse_story_document(raw).dialogue_nodes] if raw else [("Gespräch beenden", None)],
            value=None), [state], [dialogue_answer_target])
        state.change(lambda raw: gr.update(
            choices=[(f"{choice.id}: {choice.text[:48]}", choice.id)
                     for choice in parse_story_document(raw).dialogue_choices
                     if choice.next_node_id is None] if raw else (), value=None),
            [state], [dialogue_terminal_choice])
        def next_speaker_choices(raw, choice_id):
            story = parse_story_document(raw)
            choice = next((c for c in story.dialogue_choices if c.id == choice_id), None)
            if choice is None:
                return gr.update(choices=[], value=None)
            parent = next(n for n in story.dialogue_nodes if n.id == choice.node_id)
            dialogue = next(d for d in story.dialogues if d.id == parent.dialogue_id)
            return gr.update(choices=[("Vorherigen Sprecher übernehmen", None)] +
                             [(c.name, c.id) for c in story.characters
                              if c.scene_id == dialogue.scene_id], value=None)
        dialogue_terminal_choice.change(next_speaker_choices,
                                        inputs=[state, dialogue_terminal_choice],
                                        outputs=[dialogue_new_speaker])
        dialogue_answer_add.click(lambda *args: propose(add_dialogue_choice, *args),
                                  [state, dialogue_node_select, dialogue_answer_id,
                                   dialogue_answer_text, dialogue_answer_target], [pending, report])
        state.change(lambda raw: gr.update(
            choices=[(f"{choice.id}: {choice.text[:48]}", choice.id)
                     for choice in parse_story_document(raw).dialogue_choices] if raw else [], value=None),
            [state], [dialogue_edit_choice])
        def selected_answer(raw, choice_id):
            answer_text, target = dialogue_choice_fields(raw, choice_id)
            return answer_text, gr.update(**target)
        dialogue_edit_choice.change(selected_answer, [state, dialogue_edit_choice],
                                    [dialogue_edit_text, dialogue_edit_target])
        dialogue_edit_save.click(lambda *args: propose(change_dialogue_choice, *args),
                                 [state, dialogue_edit_choice, dialogue_edit_text,
                                  dialogue_edit_target], [pending, report])
        dialogue_extend.click(lambda *args: propose(extend_dialogue_choice, *args),
                              [state, dialogue_terminal_choice, dialogue_new_node_id,
                               dialogue_new_node_text, dialogue_new_speaker], [pending, report])
        save_position.click(propose_position, [state, position_item, position_x, position_y],
                            [pending, report])
        ai_button.click(propose_ai, [state, ai_request], [pending, report])
        import_button.click(propose_imported, [state, imported_json], [pending, report])
        confirm_button.click(confirm, [state, pending], [state, pending, *refreshed, report])
        export_button.click(export_story, inputs=[state], outputs=[download])
        translations_button.click(export_translations, inputs=[state, source_language], outputs=[translations_download])
        translation_validate_button.click(validate_translations, inputs=[state, translation_file],
                                          outputs=[translation_validated_download])
        game_export_button.click(export_scumm, inputs=[state, scummc_path], outputs=[game_download])
        native_outputs = [native_room, native_hotspot, native_actor, native_animation,
                          native_target, native_sequence, native_step, native_steps,
                          native_costume_select, native_actor_list, native_costume_summary,
                          native_actor_initial]
        native_file.change(native_load, [native_file], [native_state, native_linked,
                                                       *native_outputs, native_report])
        native_sync_button.click(native_sync, [state, native_state],
                                 [native_state, native_linked, *native_outputs, native_report])
        native_music_add.click(native_music_import,
                               [native_state, native_room, native_music_id, native_music_file],
                               [native_state, *native_outputs, native_report])
        native_sound_add.click(native_sound_import,
                               [native_state, native_room, native_sound_id, native_sound_file],
                               [native_state, *native_outputs, native_report])
        native_costume_button.click(lambda *args: native_asset_edit(create_costume, *args),
                                    [native_state, native_costume_file, native_costume_name],
                                    [native_state, *native_outputs, native_report])
        native_frame_button.click(lambda *args: native_asset_edit(add_costume_frame, *args),
                                  [native_state, native_costume_select, native_frame_file, native_frame_id],
                                  [native_state, *native_outputs, native_report])
        native_speaking_save.click(lambda *args: native_asset_edit(set_costume_speaking_pose, *args),
                                   [native_state, native_costume_select, native_speaking_frame],
                                   [native_state, *native_outputs, native_report])
        native_direction_save.click(lambda *args: native_asset_edit(set_costume_direction_speaking_pose, *args),
                                    [native_state, native_costume_select, native_speaking_direction,
                                     native_direction_frame],
                                    [native_state, *native_outputs, native_report])
        native_sequence_save.click(lambda *args: native_asset_edit(set_costume_direction_speaking_sequence, *args),
                                   [native_state, native_costume_select, native_speaking_direction,
                                    native_speaking_sequence],
                                   [native_state, *native_outputs, native_report])
        def direction_frame_choices(raw, name, direction):
            if not raw:
                return gr.update(choices=[], value=None)
            frames = costume_frame_names(raw, name)
            selected = costume_direction_speaking_frame(raw, name, direction)
            return gr.update(choices=frames, value=selected)
        for source in (native_state, native_costume_select, native_speaking_direction):
            source.change(direction_frame_choices,
                          [native_state, native_costume_select, native_speaking_direction],
                          [native_direction_frame])
        def direction_sequence(raw, name, direction):
            if not raw or not name:
                return ""
            return ", ".join(costume_animation_steps(raw, name, "gesture", direction))
        for source in (native_state, native_costume_select, native_speaking_direction):
            source.change(direction_sequence,
                          [native_state, native_costume_select, native_speaking_direction],
                          [native_speaking_sequence])
        def speaking_frame_choices(raw, name):
            frames = costume_frame_names(raw, name) if raw and name else ()
            return gr.update(choices=frames, value=frames[-1] if frames else None)
        native_state.change(speaking_frame_choices, [native_state, native_costume_select],
                            [native_speaking_frame])
        native_costume_select.change(speaking_frame_choices, [native_state, native_costume_select],
                                     [native_speaking_frame])
        native_anim_button.click(lambda *args: native_asset_edit(set_costume_animation, *args),
                                 [native_state, native_costume_select, native_anim_name,
                                  native_anim_index, native_anim_direction, native_anim_commands,
                                  native_anim_loop], [native_state, *native_outputs, native_report])
        native_costume_select.change(lambda raw, name: costume_summary(raw, name)
                                     if raw is not None else "Bitte ein Projekt laden",
                                     [native_state, native_costume_select], [native_costume_summary])
        def timeline_choices(raw, name, current):
            if raw is None:
                return gr.update(choices=[], value=None), gr.update(choices=[], value=None)
            animations = costume_animation_names(raw, name)
            selected = (current if current in animations else "gesture" if "gesture" in animations
                        else animations[0] if animations else None)
            costume = next((item for item in parse_document(raw).costumes if item.name == name), None)
            commands = [frame.id for frame in costume.frames] if costume else []
            commands.extend(("COUNT", "SHOW", "HIDE", "NOP"))
            return (gr.update(choices=animations, value=selected),
                    gr.update(choices=commands, value=commands[0] if commands else None))

        native_state.change(timeline_choices, [native_state, native_costume_select,
                                               native_timeline_animation],
                            [native_timeline_animation, native_timeline_command])
        native_costume_select.change(timeline_choices, [native_state, native_costume_select,
                                                        native_timeline_animation],
                                     [native_timeline_animation, native_timeline_command])

        def timeline_editor(raw, name, animation_name, direction):
            if raw is None or not name or not animation_name:
                return "", 24, "", False
            costume = next((item for item in parse_document(raw).costumes if item.name == name), None)
            animation = next((item for item in costume.animations if item.name == animation_name), None) if costume else None
            selected = next((item for item in animation.directions if item.direction == direction), None) if animation else None
            return (animation_name, animation.index if animation and animation.index is not None else 24,
                    ", ".join(selected.commands) if selected else "",
                    selected.loop if selected else False)

        for component in (native_timeline_animation, native_anim_direction):
            component.change(timeline_editor,
                             [native_state, native_costume_select, native_timeline_animation,
                              native_anim_direction],
                             [native_anim_name, native_anim_index, native_anim_commands, native_anim_loop])

        def timeline_view(raw, name, animation, direction):
            if raw is None or not name or not animation:
                return [], gr.update(choices=[], value=None)
            steps = costume_animation_steps(raw, name, animation, direction)
            return (costume_timeline_images(raw, name, animation, direction),
                    gr.update(choices=[(f"{i+1}. {step}", i) for i, step in enumerate(steps)],
                              value=0 if steps else None))

        for component in (native_state, native_costume_select, native_timeline_animation,
                          native_anim_direction):
            component.change(timeline_view,
                             [native_state, native_costume_select, native_timeline_animation,
                              native_anim_direction], [native_timeline_gallery, native_timeline_step])
        def select_timeline_step(evt: gr.SelectData):
            return evt.index if type(evt.index) is int else None

        native_timeline_gallery.select(select_timeline_step, outputs=[native_timeline_step])

        def timeline_edit(raw, name, animation, direction, step, operation, command):
            result = native_asset_edit(edit_costume_timeline, raw, name, animation, direction,
                                       step, operation, command)
            updated = result[0]
            return (*result, gr.update(value=animation),
                    *timeline_editor(updated, name, animation, direction))

        timeline_inputs = [native_state, native_costume_select, native_timeline_animation,
                           native_anim_direction, native_timeline_step]
        timeline_outputs = [native_state, *native_outputs, native_report,
                            native_timeline_animation, native_anim_name, native_anim_index,
                            native_anim_commands, native_anim_loop]
        for button, operation in ((native_timeline_append, "Anhängen"),
                                  (native_timeline_up, "Nach oben"),
                                  (native_timeline_down, "Nach unten"),
                                  (native_timeline_remove, "Entfernen")):
            button.click(lambda raw, name, animation, direction, step, command,
                         op=operation: timeline_edit(raw, name, animation, direction,
                                                     step, op, command),
                         [*timeline_inputs, native_timeline_command], timeline_outputs)
        native_preview_button.click(native_animation_preview,
                                    [native_state, native_costume_select, native_timeline_animation,
                                     native_anim_direction, native_preview_duration],
                                    [native_preview_image, native_preview_report])
        native_actor_button.click(lambda raw, actor_id, costume, room, x, y, direction, name:
                                  native_asset_edit(add_actor, raw, actor_id, costume, room,
                                                    x, y, direction, name),
                                  [native_state, native_actor_id, native_costume_select,
                                   native_room, native_actor_x, native_actor_y,
                                   native_actor_direction, native_actor_name],
                                  [native_state, *native_outputs, native_report])
        native_actor_move.click(lambda raw, actor_id, room, x, y, direction:
                                native_asset_edit(move_actor, raw, actor_id, room, x, y, direction),
                                [native_state, native_actor, native_room, native_actor_x,
                                 native_actor_y, native_actor_direction],
                                [native_state, *native_outputs, native_report])
        native_actor_costume_save.click(
            lambda raw, actor_id, costume: native_asset_edit(
                set_actor_costume, raw, actor_id, costume),
            [native_state, native_actor, native_costume_select],
            [native_state, *native_outputs, native_report])
        native_actor_initial_save.click(
            lambda raw, actor_id, animation: native_asset_edit(
                set_actor_initial_animation, raw, actor_id, animation),
            [native_state, native_actor, native_actor_initial],
            [native_state, *native_outputs, native_report])
        def native_room_update(raw, room):
            if raw is None:
                return gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
            rooms, objects, actors = project_choices(raw, room)
            animations = actor_animations(raw, actors[0] if actors else None)
            initial = next((actor.initial_animation for actor in parse_document(raw).actors
                            if actors and actor.id == actors[0]), None)
            return (gr.update(choices=objects, value=objects[0] if objects else None),
                    gr.update(choices=[*[(f"Objekt: {name}", name) for name in objects],
                                       *[(f"Raum: {name}", name) for name in rooms],
                                       *[(f"Sound: {name}", name) for name in room_sound_ids(raw, room)]],
                              value=objects[0] if objects else room),
                    gr.update(choices=[("Ego (für gesprochene Zeile)", None), *[(item, item) for item in actors]],
                              value=actors[0] if actors else None),
                    gr.update(choices=animations, value=animations[0] if animations else None),
                    gr.update(choices=[("Keine Startanimation", None), *[(name, name) for name in animations]],
                              value=initial))

        native_room.change(native_room_update, [native_state, native_room],
                           [native_hotspot, native_target, native_actor, native_animation,
                            native_actor_initial])
        def native_actor_update(raw, actor):
            animations = actor_animations(raw, actor) if raw is not None else ()
            initial = next((item.initial_animation for item in parse_document(raw).actors
                            if item.id == actor), None) if raw is not None else None
            return (gr.update(choices=animations, value=animations[0] if animations else None),
                    gr.update(choices=[("Keine Startanimation", None), *[(name, name) for name in animations]],
                              value=initial))

        native_actor.change(native_actor_update, [native_state, native_actor],
                            [native_animation, native_actor_initial])
        def native_sequence_update(raw, identity):
            steps = sequence_steps(raw, identity) if raw is not None and identity else ()
            return (gr.update(choices=[(f"{i+1}. {text}", i) for i, text in enumerate(steps)],
                              value=0 if steps else None),
                    "\n".join(f"{i+1}. {text}" for i, text in enumerate(steps)) or "Noch keine Schritte")

        native_sequence.change(native_sequence_update, [native_state, native_sequence],
                               [native_step, native_steps])
        def native_condition_update(raw, identity):
            if raw is None:
                return gr.update(choices=[("Immer ausführen", None)], value=None), 0
            room = identity.split("|", 1)[0] if identity else None
            _, objects, _ = project_choices(raw, room)
            target, state = sequence_condition_fields(raw, identity)
            return (gr.update(choices=[("Immer ausführen", None),
                                       *[(item, item) for item in objects]], value=target),
                    state)

        native_sequence.change(native_condition_update, [native_state, native_sequence],
                               [native_condition_object, native_condition_state])
        native_sequence.change(lambda raw, identity: sequence_skip_enabled(raw, identity)
                               if raw is not None else False,
                               [native_state, native_sequence], [native_skippable])
        native_skip_save.click(lambda *args: native_edit(set_sequence_skippable, *args),
                               [native_state, native_sequence, native_skippable],
                               [native_state, *native_outputs, native_report])
        native_condition_save.click(lambda *args: native_edit(set_sequence_condition, *args),
                                    [native_state, native_sequence, native_condition_object,
                                     native_condition_state],
                                    [native_state, *native_outputs, native_report])
        native_variant_add.click(lambda *args: native_edit(duplicate_sequence_variant, *args),
                                 [native_state, native_sequence, native_condition_object,
                                  native_condition_state],
                                 [native_state, *native_outputs, native_report])
        def native_step_update(raw, identity, number):
            fields = sequence_step_fields(raw, identity, number)
            sequence_room = identity.split("|", 1)[0] if identity else None
            rooms, objects, actors = project_choices(raw, sequence_room)
            animations = actor_animations(raw, fields[1]) if fields[1] else ()
            return (fields[0], gr.update(choices=[("Ego (für gesprochene Zeile)", None),
                                                 *[(item, item) for item in actors]], value=fields[1]),
                    gr.update(choices=animations, value=fields[2]),
                    gr.update(choices=[*[(f"Objekt: {name}", name) for name in objects],
                                       *[(f"Raum: {name}", name) for name in rooms],
                                       *[(f"Sound: {name}", name) for name in room_sound_ids(raw, sequence_room)]],
                              value=fields[3]),
                    fields[4], fields[5], fields[6], fields[7], fields[8] if len(fields) > 8 else "")

        native_step.change(native_step_update, [native_state, native_sequence, native_step],
                           [native_kind, native_actor, native_animation, native_target,
                            native_amount, native_move_x, native_move_y, native_face_direction,
                            native_subtitle])
        native_room.change(
            lambda raw, room: gr.update(choices=room_sound_ids(raw, room) if raw else (),
                                        value=None),
            [native_state, native_room], [native_voice_sound])
        native_sequence.change(
            lambda raw, identity: gr.update(choices=room_sound_ids(raw, identity.split("|", 1)[0])
                                           if raw and identity else (), value=None),
            [native_state, native_sequence], [native_voice_sound])
        native_state.change(
            lambda raw, room: gr.update(choices=room_sound_ids(raw, room) if raw and room else (),
                                        value=None),
            [native_state, native_room], [native_voice_sound])
        native_state.change(lambda raw: parse_document(raw).default_voice_language
                            if raw else "en", [native_state], [native_default_voice])
        native_default_voice_save.click(
            lambda *args: native_edit(set_default_voice_language, *args),
            [native_state, native_default_voice],
            [native_state, *native_outputs, native_report])
        native_voice_add.click(
            lambda raw, identity, number, language, sound, subtitle:
            native_edit(edit_voice_variant, raw, identity, number, language, sound, subtitle),
            [native_state, native_sequence, native_step, native_voice_language,
             native_voice_sound, native_voice_text],
            [native_state, *native_outputs, native_report])
        native_voice_remove.click(
            lambda raw, identity, number, language:
            native_edit(edit_voice_variant, raw, identity, number, language, None, None, True),
            [native_state, native_sequence, native_step, native_voice_language],
            [native_state, *native_outputs, native_report])
        native_state.change(
            lambda raw: gr.update(choices=dialogue_voice_lines(raw) if raw else (), value=None),
            [native_state], [native_dialogue_line])
        native_dialogue_line.change(
            lambda raw, line: gr.update(
                choices=room_sound_ids(raw, next((room.name for room in parse_document(raw).rooms
                                                 if line and line.startswith(f"room.{room.name.lower()}.")), ""))
                if raw else (), value=None),
            [native_state, native_dialogue_line], [native_dialogue_sound])
        native_dialogue_voice_save.click(
            lambda *args: native_edit(edit_dialogue_voice, *args),
            [native_state, native_dialogue_line, native_dialogue_language, native_dialogue_sound],
            [native_state, *native_outputs, native_report])
        native_dialogue_voice_remove.click(
            lambda raw, line, language: native_edit(edit_dialogue_voice, raw, line, language, None, True),
            [native_state, native_dialogue_line, native_dialogue_language],
            [native_state, *native_outputs, native_report])
        def dialogue_animation_update(raw, line, direction):
            if not raw:
                return (gr.update(choices=[], value=None), True,
                        gr.update(choices=[], value=None), None, None,
                        "",
                        "Bitte zuerst eine Sprecher-Dialogzeile wählen")
            choices, selected, reset = dialogue_animation_choices(raw, line)
            frames, selected_frame = dialogue_speaking_frame_selection(raw, line)
            direction_image, direction_status = dialogue_direction_animation_preview(
                raw, line, selected, direction)
            return (gr.update(choices=choices, value=selected), reset,
                    gr.update(choices=frames, value=selected_frame),
                    dialogue_speaking_frame_preview(raw, line, selected_frame),
                    direction_image, dialogue_speaking_sequence_selection(raw, line, direction), direction_status)

        def dialogue_animation_refresh(raw, line, direction):
            lines = dialogue_animation_lines(raw) if raw else ()
            current = line if line in {identity for _label, identity in lines} else None
            return (gr.update(choices=lines, value=current),
                    *dialogue_animation_update(raw, current, direction))

        # Retain the selected authored line across a save, and refresh both
        # its animation and PNG pose from the persisted project. Old/stale
        # lines are cleared instead of silently selecting another speaker.
        native_state.change(
            dialogue_animation_refresh,
            [native_state, native_dialogue_animation_line, native_dialogue_direction],
            [native_dialogue_animation_line, native_dialogue_animation,
             native_dialogue_reset, native_dialogue_speaking_frame,
             native_dialogue_speaking_preview, native_dialogue_direction_preview,
             native_dialogue_speaking_sequence,
             native_dialogue_direction_status])
        # Programmatic dropdown refreshes from native_state already render
        # the previews. Only real user selection should request them again;
        # overlapping identical Gradio image writes can truncate HTTP PNGs.
        native_dialogue_animation_line.input(
            dialogue_animation_update,
            [native_state, native_dialogue_animation_line, native_dialogue_direction],
            [native_dialogue_animation, native_dialogue_reset, native_dialogue_speaking_frame,
             native_dialogue_speaking_preview, native_dialogue_direction_preview,
             native_dialogue_speaking_sequence,
             native_dialogue_direction_status])
        for direction_control in (native_dialogue_animation, native_dialogue_direction):
            direction_control.input(
                dialogue_direction_animation_preview,
                [native_state, native_dialogue_animation_line,
                 native_dialogue_animation, native_dialogue_direction],
                [native_dialogue_direction_preview, native_dialogue_direction_status])
        native_dialogue_direction.input(
            dialogue_speaking_sequence_selection,
            [native_state, native_dialogue_animation_line, native_dialogue_direction],
            [native_dialogue_speaking_sequence])
        native_dialogue_speaking_frame.input(
            dialogue_speaking_frame_preview,
            [native_state, native_dialogue_animation_line, native_dialogue_speaking_frame],
            [native_dialogue_speaking_preview])
        native_dialogue_speaking_apply.click(
            lambda *args: native_edit(assign_dialogue_speaking_frame, *args),
            [native_state, native_dialogue_animation_line, native_dialogue_speaking_frame,
             native_dialogue_reset], [native_state, *native_outputs, native_report])
        native_dialogue_sequence_apply.click(
            lambda *args: native_edit(assign_dialogue_speaking_sequence, *args),
            [native_state, native_dialogue_animation_line, native_dialogue_speaking_sequence,
             native_dialogue_reset], [native_state, *native_outputs, native_report])
        native_dialogue_direction_sequence_apply.click(
            lambda *args: native_edit(assign_dialogue_direction_speaking_sequence, *args),
            [native_state, native_dialogue_animation_line, native_dialogue_direction,
             native_dialogue_speaking_sequence, native_dialogue_reset],
            [native_state, *native_outputs, native_report])
        def dialogue_timeline_view(raw, line, direction, selected_frame):
            if not raw or not line:
                return [], gr.update(choices=[], value=None), gr.update(choices=[], value=None)
            images, steps, frames = dialogue_speaking_timeline(raw, line, direction)
            return (images, gr.update(choices=steps, value=0 if steps else None),
                    gr.update(choices=frames, value=(selected_frame if selected_frame in frames
                                                    else frames[0] if frames else None)))

        for source in (native_state, native_dialogue_animation_line, native_dialogue_direction):
            source.change(dialogue_timeline_view,
                          [native_state, native_dialogue_animation_line, native_dialogue_direction,
                           native_dialogue_timeline_add_frame],
                          [native_dialogue_timeline_gallery, native_dialogue_timeline_step,
                           native_dialogue_timeline_add_frame])
        native_dialogue_timeline_gallery.select(select_timeline_step,
                                                outputs=[native_dialogue_timeline_step])

        for button, operation in ((native_dialogue_timeline_append, "Anhängen"),
                                  (native_dialogue_timeline_left, "Nach links"),
                                  (native_dialogue_timeline_right, "Nach rechts"),
                                  (native_dialogue_timeline_remove, "Entfernen")):
            button.click(lambda raw, line, direction, step, frame, reset, op=operation:
                         native_edit(edit_dialogue_speaking_timeline, raw, line, direction,
                                     step, op, frame, reset),
                         [native_state, native_dialogue_animation_line, native_dialogue_direction,
                          native_dialogue_timeline_step, native_dialogue_timeline_add_frame,
                          native_dialogue_reset], [native_state, *native_outputs, native_report])

        def dialogue_timeline_play(raw, line, direction, duration):
            if not raw:
                raise gr.Error("Bitte zuerst ein natives Projekt laden")
            path = Path(tempfile.mkdtemp(prefix="adventure-studio-dialogue-preview-")) / "speaking.gif"
            try:
                rendered = dialogue_speaking_timeline_preview(raw, line, direction, duration, path)
                return str(rendered), (f"{int(duration)} ms pro Bild nur im Editor; "
                                       "ScummVM bestimmt die tatsächliche COST-Abspielrate.")
            except (ValueError, OSError) as error:
                raise gr.Error(f"Sprechvorschau nicht möglich: {error}") from error

        native_dialogue_timeline_play.click(
            dialogue_timeline_play,
            [native_state, native_dialogue_animation_line, native_dialogue_direction,
             native_dialogue_timeline_duration],
            [native_dialogue_timeline_preview_image, native_dialogue_timeline_preview_status])
        for source in (native_state, native_dialogue_animation_line):
            source.change(dialogue_animation_phase_selection,
                          [native_state, native_dialogue_animation_line],
                          [native_dialogue_phase_start, native_dialogue_phase_minimum])
        native_dialogue_phase_save.click(
            lambda *args: native_edit(edit_dialogue_animation_phases, *args),
            [native_state, native_dialogue_animation_line,
             native_dialogue_phase_start, native_dialogue_phase_minimum],
            [native_state, *native_outputs, native_report])
        def dialogue_ending_view(raw, line):
            options, selected, ticks = dialogue_ending_animation_selection(raw, line)
            return gr.update(choices=options, value=selected), ticks

        for source in (native_state, native_dialogue_animation_line):
            source.change(dialogue_ending_view,
                          [native_state, native_dialogue_animation_line],
                          [native_dialogue_ending_animation, native_dialogue_ending_ticks])
        native_dialogue_ending_save.click(
            lambda *args: native_edit(edit_dialogue_ending_animation, *args),
            [native_state, native_dialogue_animation_line,
             native_dialogue_ending_animation, native_dialogue_ending_ticks],
            [native_state, *native_outputs, native_report])
        native_dialogue_ending_remove.click(
            lambda raw, line: native_edit(edit_dialogue_ending_animation, raw, line, None, 0),
            [native_state, native_dialogue_animation_line],
            [native_state, *native_outputs, native_report])
        native_dialogue_png_import.click(
            lambda *args: native_edit(import_dialogue_png_frame, *args),
            [native_state, native_dialogue_animation_line, native_dialogue_direction,
             native_dialogue_png_file, native_dialogue_png_id, native_dialogue_png_target,
             native_dialogue_ending_ticks, native_dialogue_reset],
            [native_state, *native_outputs, native_report])
        def png_batch_selection(paths, order, selected=None):
            if not paths:
                return gr.update(choices=[], value=None)
            ordered = dialogue_png_batch_order(paths, order)
            choices = [(f"{i}. {Path(path).name}", i - 1)
                       for i, path in enumerate(ordered, 1)]
            return gr.update(choices=choices, value=(selected if selected is not None else 0)
                             if choices else None)

        def png_batch_excluded_selection(paths, order):
            choices = dialogue_png_batch_excluded(paths, order)
            return gr.update(choices=choices, value=choices[0][1] if choices else None)

        def png_batch_new_files(raw, line, paths):
            order = None
            return (list(paths) if paths else None, {}, order, png_batch_selection(paths, order),
                    png_batch_excluded_selection(paths, order),
                    dialogue_png_batch_preview(raw, line, paths, order))

        native_dialogue_png_batch_files.change(
            png_batch_new_files,
            [native_state, native_dialogue_animation_line, native_dialogue_png_batch_files],
            [native_dialogue_png_batch_paths, native_dialogue_png_batch_frame_ids,
             native_dialogue_png_batch_order,
             native_dialogue_png_batch_selected,
             native_dialogue_png_batch_excluded,
             native_dialogue_png_batch_plan])

        def png_batch_add_sprite_sheet(raw, line, paths, order, frame_ids,
                                       sheet, columns, rows):
            try:
                selected = len(dialogue_png_batch_order(paths, order)) if paths else 0
                updated, new_order = stage_dialogue_png_sprite_sheet(
                    paths, order, sheet, columns, rows)
            except (ValueError, OSError) as error:
                raise gr.Error(f"Sprite-Sheet kann nicht hinzugefügt werden: {error}") from error
            return (updated, new_order, png_batch_selection(updated, new_order, selected),
                    png_batch_excluded_selection(updated, new_order),
                    dialogue_png_batch_preview(raw, line, updated, new_order, frame_ids))

        native_dialogue_sprite_add.click(
            png_batch_add_sprite_sheet,
            [native_state, native_dialogue_animation_line,
             native_dialogue_png_batch_paths, native_dialogue_png_batch_order,
             native_dialogue_png_batch_frame_ids, native_dialogue_sprite_sheet,
             native_dialogue_sprite_columns, native_dialogue_sprite_rows],
            [native_dialogue_png_batch_paths, native_dialogue_png_batch_order,
             native_dialogue_png_batch_selected, native_dialogue_png_batch_excluded,
             native_dialogue_png_batch_plan])

        def png_batch_replace(raw, line, paths, order, selected, replacement, frame_ids):
            try:
                updated = replace_dialogue_png_batch_frame(paths, order, selected, replacement)
            except ValueError as error:
                raise gr.Error(str(error)) from error
            source_index = selected if order is None else order[selected]
            updated_ids = dict(frame_ids or {})
            updated_ids.pop(source_index, None)
            return (updated, updated_ids, png_batch_selection(updated, order, selected),
                    png_batch_excluded_selection(updated, order),
                    dialogue_png_batch_preview(raw, line, updated, order, updated_ids))

        native_dialogue_png_batch_replace.click(
            png_batch_replace,
            [native_state, native_dialogue_animation_line, native_dialogue_png_batch_paths,
             native_dialogue_png_batch_order, native_dialogue_png_batch_selected,
             native_dialogue_png_batch_replacement, native_dialogue_png_batch_frame_ids],
            [native_dialogue_png_batch_paths, native_dialogue_png_batch_frame_ids,
             native_dialogue_png_batch_selected,
             native_dialogue_png_batch_excluded, native_dialogue_png_batch_plan])

        def png_batch_save_id(paths, order, selected, proposed, frame_ids):
            try:
                return set_dialogue_png_batch_frame_id(
                    paths, order, selected, proposed, frame_ids)
            except ValueError as error:
                raise gr.Error(str(error)) from error

        native_dialogue_png_batch_set_id.click(
            png_batch_save_id,
            [native_dialogue_png_batch_paths, native_dialogue_png_batch_order,
             native_dialogue_png_batch_selected, native_dialogue_png_batch_id,
             native_dialogue_png_batch_frame_ids],
            [native_dialogue_png_batch_frame_ids])

        def png_batch_suggest_id(raw, line, paths, order, selected, frame_ids):
            try:
                return suggest_dialogue_png_batch_frame_id(
                    raw, line, paths, order, selected, frame_ids)
            except ValueError as error:
                raise gr.Error(str(error)) from error

        native_dialogue_png_batch_suggest_id.click(
            png_batch_suggest_id,
            [native_state, native_dialogue_animation_line,
             native_dialogue_png_batch_paths, native_dialogue_png_batch_order,
             native_dialogue_png_batch_selected, native_dialogue_png_batch_frame_ids],
            [native_dialogue_png_batch_frame_ids])

        def png_batch_resolve_ids(raw, line, paths, order, frame_ids):
            try:
                return resolve_dialogue_png_batch_frame_ids(
                    raw, line, paths, order, frame_ids)
            except ValueError as error:
                raise gr.Error(str(error)) from error

        native_dialogue_png_batch_resolve_ids.click(
            png_batch_resolve_ids,
            [native_state, native_dialogue_animation_line,
             native_dialogue_png_batch_paths, native_dialogue_png_batch_order,
             native_dialogue_png_batch_frame_ids],
            [native_dialogue_png_batch_frame_ids])
        for source in (native_dialogue_png_batch_paths, native_dialogue_png_batch_order,
                       native_dialogue_png_batch_selected, native_dialogue_png_batch_frame_ids):
            source.change(
                dialogue_png_batch_selected_frame_id,
                [native_dialogue_png_batch_paths, native_dialogue_png_batch_order,
                 native_dialogue_png_batch_selected, native_dialogue_png_batch_frame_ids],
                [native_dialogue_png_batch_id])

        def png_batch_readiness(raw, line, direction, paths, target, ticks, reset, order, frame_ids):
            ready, description = dialogue_png_batch_preflight(
                raw, line, direction, paths, target, ticks, reset, order, frame_ids)
            gallery, issues = dialogue_png_batch_image_diagnostics(
                raw, line, direction, paths, target, ticks, reset, order, frame_ids)
            return (("✅ " if ready else "⚠️ ") + description,
                    gr.update(interactive=ready), gallery, issues)

        for source in (native_state, native_dialogue_animation_line,
                       native_dialogue_direction, native_dialogue_png_batch_paths,
                       native_dialogue_png_target, native_dialogue_ending_ticks,
                       native_dialogue_reset, native_dialogue_png_batch_order,
                       native_dialogue_png_batch_frame_ids):
            source.change(
                png_batch_readiness,
                [native_state, native_dialogue_animation_line,
                 native_dialogue_direction, native_dialogue_png_batch_paths,
                 native_dialogue_png_target, native_dialogue_ending_ticks,
                 native_dialogue_reset, native_dialogue_png_batch_order,
                 native_dialogue_png_batch_frame_ids],
                [native_dialogue_png_batch_readiness, native_dialogue_png_batch_import,
                 native_dialogue_png_batch_gallery, native_dialogue_png_batch_image_issues])

        for source in (native_dialogue_png_batch_paths, native_dialogue_png_batch_order,
                       native_dialogue_png_batch_selected, native_dialogue_png_batch_frame_ids):
            source.change(
                dialogue_png_batch_frame_preview,
                [native_dialogue_png_batch_paths, native_dialogue_png_batch_order,
                 native_dialogue_png_batch_selected, native_dialogue_png_batch_frame_ids],
                [native_dialogue_png_batch_frame_image,
                 native_dialogue_png_batch_frame_status])

        def png_batch_choose_tile(evt: gr.SelectData):
            if evt is None or type(evt.index) is not int:
                raise gr.Error("Bitte ein Bild in der aktuellen Importgalerie auswählen")
            return evt.index

        # With postponed annotations, Gradio's event injection needs the
        # actual SelectData class rather than the string "gr.SelectData".
        png_batch_choose_tile.__annotations__["evt"] = gr.SelectData
        native_dialogue_png_batch_gallery.select(
            png_batch_choose_tile, outputs=[native_dialogue_png_batch_selected])

        for button, step in ((native_dialogue_png_batch_previous, -1),
                             (native_dialogue_png_batch_next, 1)):
            button.click(
                lambda paths, order, selected, step=step: gr.update(
                    value=step_dialogue_png_batch_frame(paths, order, selected, step)),
                [native_dialogue_png_batch_paths, native_dialogue_png_batch_order,
                 native_dialogue_png_batch_selected],
                [native_dialogue_png_batch_selected])

        def png_batch_play(paths, order, duration, frame_ids):
            destination = (Path(tempfile.mkdtemp(prefix="adventure-studio-png-batch-preview-"))
                           / "staged.gif")
            try:
                rendered = dialogue_png_batch_animation_preview(
                    paths, order, duration, destination, frame_ids)
                return str(rendered), (f"{int(duration)} ms pro Bild nur in der Editor-Vorschau; "
                                       "die native COST-Abspielrate bestimmt ScummVM.")
            except (ValueError, OSError) as error:
                raise gr.Error(f"PNG-Importvorschau nicht möglich: {error}") from error

        native_dialogue_png_batch_play.click(
            png_batch_play,
            [native_dialogue_png_batch_paths, native_dialogue_png_batch_order,
             native_dialogue_png_batch_duration, native_dialogue_png_batch_frame_ids],
            [native_dialogue_png_batch_animation, native_dialogue_png_batch_animation_status])
        # A previously rendered GIF must never masquerade as the current staged order.
        for source in (native_dialogue_png_batch_paths, native_dialogue_png_batch_order):
            source.change(lambda: (None, ""),
                          outputs=[native_dialogue_png_batch_animation,
                                   native_dialogue_png_batch_animation_status])

        def png_batch_move(raw, line, paths, order, selected, frame_ids, step):
            moved, new_selected = move_dialogue_png_batch_frame(paths, order, selected, step)
            return (moved, png_batch_selection(paths, moved, new_selected),
                    png_batch_excluded_selection(paths, moved),
                    dialogue_png_batch_preview(raw, line, paths, moved, frame_ids))

        for button, step in ((native_dialogue_png_batch_up, -1),
                             (native_dialogue_png_batch_down, 1)):
            button.click(
                lambda raw, line, paths, order, selected, frame_ids, step=step: png_batch_move(
                    raw, line, paths, order, selected, frame_ids, step),
                [native_state, native_dialogue_animation_line, native_dialogue_png_batch_paths,
                 native_dialogue_png_batch_order, native_dialogue_png_batch_selected,
                 native_dialogue_png_batch_frame_ids],
                [native_dialogue_png_batch_order, native_dialogue_png_batch_selected,
                 native_dialogue_png_batch_excluded,
                 native_dialogue_png_batch_plan])
        def png_batch_remove(raw, line, paths, order, selected, frame_ids):
            remaining, new_selected = remove_dialogue_png_batch_frame(
                paths, order, selected)
            return (remaining, png_batch_selection(paths, remaining, new_selected),
                    png_batch_excluded_selection(paths, remaining),
                    dialogue_png_batch_preview(raw, line, paths, remaining, frame_ids))

        native_dialogue_png_batch_remove.click(
            png_batch_remove,
            [native_state, native_dialogue_animation_line, native_dialogue_png_batch_paths,
             native_dialogue_png_batch_order, native_dialogue_png_batch_selected,
             native_dialogue_png_batch_frame_ids],
            [native_dialogue_png_batch_order, native_dialogue_png_batch_selected,
             native_dialogue_png_batch_excluded,
             native_dialogue_png_batch_plan])
        def png_batch_restore(raw, line, paths, order, excluded, frame_ids):
            restored, selected = restore_dialogue_png_batch_frame(
                paths, order, excluded)
            return (restored, png_batch_selection(paths, restored, selected),
                    png_batch_excluded_selection(paths, restored),
                    dialogue_png_batch_preview(raw, line, paths, restored, frame_ids))

        native_dialogue_png_batch_restore.click(
            png_batch_restore,
            [native_state, native_dialogue_animation_line, native_dialogue_png_batch_paths,
             native_dialogue_png_batch_order, native_dialogue_png_batch_excluded,
             native_dialogue_png_batch_frame_ids],
            [native_dialogue_png_batch_order, native_dialogue_png_batch_selected,
             native_dialogue_png_batch_excluded, native_dialogue_png_batch_plan])
        for source in (native_state, native_dialogue_animation_line,
                       native_dialogue_png_batch_frame_ids):
            source.change(dialogue_png_batch_preview,
                          [native_state, native_dialogue_animation_line,
                           native_dialogue_png_batch_paths, native_dialogue_png_batch_order,
                           native_dialogue_png_batch_frame_ids],
                          [native_dialogue_png_batch_plan])
        native_dialogue_png_batch_import.click(
            lambda *args: native_edit(import_dialogue_png_batch, *args),
            [native_state, native_dialogue_animation_line, native_dialogue_direction,
             native_dialogue_png_batch_paths, native_dialogue_png_target,
             native_dialogue_ending_ticks, native_dialogue_reset,
             native_dialogue_png_batch_order, native_dialogue_png_batch_frame_ids],
            [native_state, *native_outputs, native_report])
        for source in (native_state, native_dialogue_animation_line):
            source.change(dialogue_costume_isolation_preview,
                          [native_state, native_dialogue_animation_line],
                          [native_dialogue_costume_isolation])
        native_dialogue_costume_isolate.click(
            lambda raw, line: native_edit(isolate_dialogue_speaker_costume, raw, line),
            [native_state, native_dialogue_animation_line],
            [native_state, *native_outputs, native_report])
        def dialogue_ending_timeline_view(raw, line, direction, selected_frame):
            images, steps, frames = dialogue_ending_timeline(raw, line, direction)
            return (images, gr.update(choices=steps, value=0 if steps else None),
                    gr.update(choices=frames, value=(selected_frame if selected_frame in frames
                                                     else frames[0] if frames else None)))

        for source in (native_state, native_dialogue_animation_line, native_dialogue_direction):
            source.change(dialogue_ending_timeline_view,
                          [native_state, native_dialogue_animation_line, native_dialogue_direction,
                           native_dialogue_ending_frame],
                          [native_dialogue_ending_gallery, native_dialogue_ending_step,
                           native_dialogue_ending_frame])
        native_dialogue_ending_gallery.select(select_timeline_step,
                                              outputs=[native_dialogue_ending_step])
        for button, operation in (
                (native_dialogue_ending_append, "Anhängen"),
                (native_dialogue_ending_left, "Nach links"),
                (native_dialogue_ending_right, "Nach rechts"),
                (native_dialogue_ending_delete_frame, "Entfernen")):
            button.click(lambda raw, line, direction, step, frame, ticks, op=operation:
                         native_edit(edit_dialogue_ending_timeline, raw, line, direction,
                                     step, op, frame, ticks),
                         [native_state, native_dialogue_animation_line, native_dialogue_direction,
                          native_dialogue_ending_step, native_dialogue_ending_frame,
                          native_dialogue_ending_ticks],
                         [native_state, *native_outputs, native_report])

        def dialogue_ending_play(raw, line, direction, duration):
            path = Path(tempfile.mkdtemp(prefix="adventure-studio-ending-preview-")) / "ending.gif"
            try:
                rendered = dialogue_ending_timeline_preview(raw, line, direction, duration, path)
                return str(rendered)
            except (ValueError, OSError) as error:
                raise gr.Error(f"Abschlussvorschau nicht möglich: {error}") from error

        native_dialogue_ending_play.click(
            dialogue_ending_play,
            [native_state, native_dialogue_animation_line, native_dialogue_direction,
             native_dialogue_ending_preview_duration],
            [native_dialogue_ending_preview])
        native_dialogue_animation_save.click(
            lambda *args: native_edit(edit_dialogue_animation, *args),
            [native_state, native_dialogue_animation_line, native_dialogue_animation,
             native_dialogue_reset],
            [native_state, *native_outputs, native_report])
        native_dialogue_animation_remove.click(
            lambda raw, line: native_edit(edit_dialogue_animation, raw, line, None),
            [native_state, native_dialogue_animation_line],
            [native_state, *native_outputs, native_report])
        native_add.click(lambda *args: native_edit(append_sequence_step, *args),
                         [native_state, native_room, native_hotspot, native_verb,
                          native_kind, native_actor, native_animation, native_target, native_amount,
                          native_move_x, native_move_y, native_face_direction, native_subtitle],
                         [native_state, *native_outputs, native_report])
        native_add_selected.click(lambda *args: native_edit(append_selected_sequence_step, *args),
                                  [native_state, native_sequence, native_kind, native_actor,
                                   native_animation, native_target, native_amount, native_move_x,
                                   native_move_y, native_face_direction, native_subtitle],
                                  [native_state, *native_outputs, native_report])
        native_replace.click(lambda *args: native_edit(replace_sequence_step, *args),
                             [native_state, native_sequence, native_step,
                              native_kind, native_actor, native_animation, native_target,
                              native_amount, native_move_x, native_move_y, native_face_direction,
                              native_subtitle],
                             [native_state, *native_outputs, native_report])
        for button, operation in ((native_up, "Nach oben"), (native_down, "Nach unten"),
                                  (native_remove, "Entfernen")):
            button.click(lambda raw, identity, step, op=operation: native_edit(
                modify_sequence_step, raw, identity, step, op),
                [native_state, native_sequence, native_step],
                [native_state, *native_outputs, native_report])
        native_json_button.click(native_download, [native_state, native_linked, state], [native_json_download])
        native_game_button.click(native_game, [native_state, scummc_path, native_linked, state,
                                               native_translation_file],
                                 [native_game_download])
        studio_file.change(studio_load, [studio_file],
                           [state, pending, *refreshed, report,
                            native_state, native_linked, *native_outputs, native_report])
        studio_save_button.click(studio_download, [state, native_state], [studio_download_file])
    return app


def main() -> None:
    codespaces = os.environ.get("CODESPACES", "").lower() == "true"
    make_app().launch(server_name="0.0.0.0" if codespaces else "127.0.0.1",
                      server_port=7860, share=False, inbrowser=not codespaces)


if __name__ == "__main__":
    main()
