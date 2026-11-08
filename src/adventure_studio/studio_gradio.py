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
                             change_dialogue_line, change_position, change_puzzle, change_scene,
                             describe_story, item_position, prepare_proposal,
                             report_text, scene_preview, translation_draft, validate_translation_draft)
from .story_document import canonical_story_json, parse_story_document
from .studio_export import export_playable, export_native_project
from .studio_sequences import (actor_animations, append_sequence_step, modify_sequence_step,
                               project_choices, sequence_choices, sequence_steps,
                               compose_story_project)
from .scumm_project import canonical_json as canonical_project_json, parse_document
from .studio_project import canonical_studio_project, parse_studio_project
from .studio_actors import (add_actor, actor_summary, costume_names, costume_summary,
                            create_costume, add_costume_frame, set_costume_animation,
                            move_actor, costume_animation_names, costume_animation_steps,
                            costume_timeline_images, edit_costume_timeline,
                            render_costume_preview, set_actor_initial_animation)


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
                dialogue_line_fields(raw, node_id or ""), *catalog_view(raw))

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
        except ValueError as error:
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
                gr.update(choices=actors, value=chosen_actor),
                gr.update(choices=animations, value=animations[0] if animations else None),
                gr.update(choices=objects, value=objects[0] if objects else None),
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
        except ValueError as error:
            raise gr.Error(str(error)) from error

    def native_asset_edit(action, raw, *args):
        if raw is None:
            raise gr.Error("Bitte zuerst die Story als natives Projekt übernehmen")
        try:
            updated = action(raw, *args)
            chosen = (args[1] if action is create_costume else args[0]
                      if action in (add_costume_frame, set_costume_animation,
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

    def native_game(raw, scummc_path, linked, story_raw):
        if raw is None or not scummc_path.strip():
            raise gr.Error("Native Projektdatei und ScummC-Pfad sind erforderlich")
        path = Path(tempfile.mkdtemp(prefix="adventure-studio-native-game-")) / "adventure.zip"
        try:
            return str(export_native_project(raw, Path(scummc_path.strip()), path,
                                             story_raw=story_raw if linked else None))
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
            gr.Markdown("Vorhandene Gesprächszeilen bearbeiten. Neue Dialoge und Verzweigungen können über die KI-Story-Regie als geprüfte Datenoperationen entstehen.")
            dialogue_node_select = gr.Dropdown(label="Dialogzeile")
            dialogue_text = gr.Textbox(label="Sprechtext", lines=4)
            save_dialogue = gr.Button("Dialogänderung prüfen")
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
            native_file = gr.File(label="Native Projekt-JSON öffnen", file_types=[".json"], type="filepath")
            native_sync_button = gr.Button("Aktuelle Story als natives Projekt übernehmen / aktualisieren")
            with gr.Accordion("Actors und Costumes erstellen", open=True):
                gr.Markdown("Ein PNG wird in eine native 32-Farben-Costume mit Transparenzfarbe umgewandelt. Bilder mit mehr als 31 sichtbaren Farben werden auf 31 Farben reduziert. Weitere Frames behalten die vorhandenen Farben; ist die Palette voll, wird der Import mit einer klaren Meldung abgelehnt.")
                with gr.Row():
                    native_costume_file = gr.File(label="Costume-PNG", file_types=[".png"], type="filepath")
                    native_costume_name = gr.Textbox(label="Neue Costume-ID")
                    native_costume_button = gr.Button("Costume aus PNG erstellen")
                native_costume_select = gr.Dropdown(label="Vorhandene Costume")
                native_costume_summary = gr.Textbox(label="Frames und Animationen", lines=5, interactive=False)
                with gr.Row():
                    native_frame_file = gr.File(label="Weiteres Frame-PNG", file_types=[".png"], type="filepath")
                    native_frame_id = gr.Textbox(label="Neue Frame-ID")
                    native_frame_button = gr.Button("Frame zur Costume hinzufügen")
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
                native_kind = gr.Dropdown(label="Aktion hinzufügen", choices=["Actor animieren", "Actor versetzen", "Actor laufen lassen", "Auf Actor warten", "Actor drehen", "Warten", "Objektzustand setzen"], value="Actor animieren")
                native_actor = gr.Dropdown(label="Actor")
                native_animation = gr.Dropdown(label="Costume-Animation")
                native_target = gr.Dropdown(label="Zielobjekt")
                native_amount = gr.Number(label="Sekunden / Objektzustand (0–2)", value=1, precision=0)
            with gr.Row():
                native_move_x = gr.Number(label="Actor-Ziel X (Versetzen/Laufen)", value=320, precision=0)
                native_move_y = gr.Number(label="Actor-Ziel Y (Versetzen/Laufen)", value=100, precision=0)
                native_face_direction = gr.Dropdown(label="Blickrichtung (Actor drehen)",
                                                    choices=["N", "E", "S", "W"], value="S")
            gr.Markdown("**Actor laufen lassen** startet den nativen Weg zum Ziel. Mit **Auf Actor warten** kannst du die nachfolgenden Schritte bis zum Ende seiner Laufbewegung anhalten.")
            native_add = gr.Button("Schritt an Interaktion anhängen", variant="primary")
            native_sequence = gr.Dropdown(label="Vorhandene Interaktion")
            native_step = gr.Dropdown(label="Schritt auswählen")
            native_steps = gr.Textbox(label="Geordnete Schritte", lines=6, interactive=False)
            with gr.Row():
                native_up = gr.Button("Schritt nach oben")
                native_down = gr.Button("Schritt nach unten")
                native_remove = gr.Button("Schritt entfernen")
            native_report = gr.Textbox(label="Projektstatus", interactive=False)
            with gr.Row():
                native_json_button = gr.Button("Validiertes Projekt herunterladen")
                native_json_download = gr.File(label="Native Projekt-JSON")
            native_game_button = gr.Button("Natives SCUMM-ZIP bauen")
            native_game_download = gr.File(label="SCUMM-Spiel")
        report = gr.Textbox(label="Deterministischer Änderungs- und Prüfbericht", lines=7, interactive=False)
        confirm_button = gr.Button("Geprüfte Änderung jetzt übernehmen", variant="primary")

        refreshed = [scene_select, item_select, puzzle_select, position_item, overview, scene_title,
                     scene_description, item_name, item_description, puzzle_title, puzzle_items,
                     position_x, position_y, preview, dialogue_node_select, dialogue_text,
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
        save_scene.click(lambda *args: propose(change_scene, *args),
                         [state, scene_select, scene_title, scene_description], [pending, report])
        save_item.click(lambda *args: propose(change_item, *args),
                        [state, item_select, item_name, item_description], [pending, report])
        add_item.click(lambda *args: propose(add_decoration, *args),
                       [state, scene_select, new_id, new_name, new_description], [pending, report])
        save_puzzle.click(propose_puzzle, [state, puzzle_select, puzzle_title, puzzle_items],
                          [pending, report])
        save_dialogue.click(lambda *args: propose(change_dialogue_line, *args),
                            [state, dialogue_node_select, dialogue_text], [pending, report])
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
        native_costume_button.click(lambda *args: native_asset_edit(create_costume, *args),
                                    [native_state, native_costume_file, native_costume_name],
                                    [native_state, *native_outputs, native_report])
        native_frame_button.click(lambda *args: native_asset_edit(add_costume_frame, *args),
                                  [native_state, native_costume_select, native_frame_file, native_frame_id],
                                  [native_state, *native_outputs, native_report])
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
        native_actor_initial_save.click(
            lambda raw, actor_id, animation: native_asset_edit(
                set_actor_initial_animation, raw, actor_id, animation),
            [native_state, native_actor, native_actor_initial],
            [native_state, *native_outputs, native_report])
        def native_room_update(raw, room):
            if raw is None:
                return gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
            _, objects, actors = project_choices(raw, room)
            animations = actor_animations(raw, actors[0] if actors else None)
            initial = next((actor.initial_animation for actor in parse_document(raw).actors
                            if actors and actor.id == actors[0]), None)
            return (gr.update(choices=objects, value=objects[0] if objects else None),
                    gr.update(choices=objects, value=objects[0] if objects else None),
                    gr.update(choices=actors, value=actors[0] if actors else None),
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
        native_add.click(lambda *args: native_edit(append_sequence_step, *args),
                         [native_state, native_room, native_hotspot, native_verb,
                          native_kind, native_actor, native_animation, native_target, native_amount,
                          native_move_x, native_move_y, native_face_direction],
                         [native_state, *native_outputs, native_report])
        for button, operation in ((native_up, "Nach oben"), (native_down, "Nach unten"),
                                  (native_remove, "Entfernen")):
            button.click(lambda raw, identity, step, op=operation: native_edit(
                modify_sequence_step, raw, identity, step, op),
                [native_state, native_sequence, native_step],
                [native_state, *native_outputs, native_report])
        native_json_button.click(native_download, [native_state, native_linked, state], [native_json_download])
        native_game_button.click(native_game, [native_state, scummc_path, native_linked, state],
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
