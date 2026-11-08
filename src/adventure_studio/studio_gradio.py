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
                               project_choices, sequence_choices, sequence_steps)
from .scumm_project import canonical_json as canonical_project_json, parse_document


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

    def native_selectors(raw, selected_room=None, selected_sequence=None):
        rooms, objects, actors = project_choices(raw, selected_room)
        room = selected_room if selected_room in rooms else rooms[0]
        sequences = sequence_choices(raw)
        identity = selected_sequence if selected_sequence in {value for _, value in sequences} else (
            sequences[0][1] if sequences else None)
        steps = sequence_steps(raw, identity) if identity else ()
        animations = actor_animations(raw, actors[0] if actors else None)
        return (gr.update(choices=rooms, value=room),
                gr.update(choices=objects, value=objects[0] if objects else None),
                gr.update(choices=actors, value=actors[0] if actors else None),
                gr.update(choices=animations, value=animations[0] if animations else None),
                gr.update(choices=objects, value=objects[0] if objects else None),
                gr.update(choices=sequences, value=identity),
                gr.update(choices=[(f"{i+1}. {text}", i) for i, text in enumerate(steps)],
                          value=0 if steps else None),
                "\n".join(f"{i+1}. {text}" for i, text in enumerate(steps)) or "Noch keine Schritte")

    def native_load(file_path):
        if not file_path:
            raise gr.Error("Bitte native Projekt-JSON-Datei auswählen")
        try:
            raw = canonical_project_json(parse_document(Path(file_path).read_text(encoding="utf-8")))
            return raw, *native_selectors(raw), "Natives Projekt geladen und validiert"
        except (OSError, ValueError) as error:
            raise gr.Error(str(error)) from error

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

    def native_download(raw):
        if raw is None:
            raise gr.Error("Bitte zuerst eine native Projektdatei laden")
        path = Path(tempfile.mkdtemp(prefix="adventure-studio-project-")) / "project.json"
        path.write_text(canonical_project_json(parse_document(raw)), encoding="utf-8")
        return str(path)

    def native_game(raw, scummc_path):
        if raw is None or not scummc_path.strip():
            raise gr.Error("Native Projektdatei und ScummC-Pfad sind erforderlich")
        path = Path(tempfile.mkdtemp(prefix="adventure-studio-native-game-")) / "adventure.zip"
        try:
            return str(export_native_project(raw, Path(scummc_path.strip()), path))
        except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
            raise gr.Error(f"Nativer SCUMM-Export fehlgeschlagen: {error}") from error

    with gr.Blocks(title="Adventure Studio") as app:
        gr.Markdown("# Adventure Studio\nStory schreiben, KI-Änderungen prüfen und als SCUMM-fähige Daten speichern.")
        state = gr.State(initial)
        pending = gr.State(None)
        with gr.Row():
            story_file = gr.File(label="Story-JSON öffnen", file_types=[".json"], type="filepath")
            export_button = gr.Button("Geprüfte Story exportieren", variant="primary")
            download = gr.File(label="Story herunterladen")
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
            gr.Markdown("Native `GameDocument`-Projekte bearbeiten: Objekt-Verben mit Actor-Animationen, Pausen und Objektzuständen verknüpfen. Dieses Projektformat ist vom Storyformat getrennt; es wird nichts stillschweigend konvertiert.")
            native_state = gr.State(None)
            native_file = gr.File(label="Native Projekt-JSON öffnen", file_types=[".json"], type="filepath")
            with gr.Row():
                native_room = gr.Dropdown(label="Raum")
                native_hotspot = gr.Dropdown(label="Auslösendes Objekt")
                native_verb = gr.Dropdown(label="Verb", choices=["Push", "Pull", "Open", "Close"], value="Open")
            with gr.Row():
                native_kind = gr.Dropdown(label="Aktion hinzufügen", choices=["Actor animieren", "Warten", "Objektzustand setzen"], value="Actor animieren")
                native_actor = gr.Dropdown(label="Actor")
                native_animation = gr.Dropdown(label="Costume-Animation")
                native_target = gr.Dropdown(label="Zielobjekt")
                native_amount = gr.Number(label="Sekunden / Objektzustand (0–2)", value=1, precision=0)
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
                          native_target, native_sequence, native_step, native_steps]
        native_file.change(native_load, [native_file], [native_state, *native_outputs, native_report])
        def native_room_update(raw, room):
            if raw is None:
                return gr.update(), gr.update(), gr.update(), gr.update()
            _, objects, actors = project_choices(raw, room)
            animations = actor_animations(raw, actors[0] if actors else None)
            return (gr.update(choices=objects, value=objects[0] if objects else None),
                    gr.update(choices=objects, value=objects[0] if objects else None),
                    gr.update(choices=actors, value=actors[0] if actors else None),
                    gr.update(choices=animations, value=animations[0] if animations else None))

        native_room.change(native_room_update, [native_state, native_room],
                           [native_hotspot, native_target, native_actor, native_animation])
        def native_actor_update(raw, actor):
            animations = actor_animations(raw, actor) if raw is not None else ()
            return gr.update(choices=animations, value=animations[0] if animations else None)

        native_actor.change(native_actor_update, [native_state, native_actor], [native_animation])
        def native_sequence_update(raw, identity):
            steps = sequence_steps(raw, identity) if raw is not None and identity else ()
            return (gr.update(choices=[(f"{i+1}. {text}", i) for i, text in enumerate(steps)],
                              value=0 if steps else None),
                    "\n".join(f"{i+1}. {text}" for i, text in enumerate(steps)) or "Noch keine Schritte")

        native_sequence.change(native_sequence_update, [native_state, native_sequence],
                               [native_step, native_steps])
        native_add.click(lambda *args: native_edit(append_sequence_step, *args),
                         [native_state, native_room, native_hotspot, native_verb,
                          native_kind, native_actor, native_animation, native_target, native_amount],
                         [native_state, *native_outputs, native_report])
        for button, operation in ((native_up, "Nach oben"), (native_down, "Nach unten"),
                                  (native_remove, "Entfernen")):
            button.click(lambda raw, identity, step, op=operation: native_edit(
                modify_sequence_step, raw, identity, step, op),
                [native_state, native_sequence, native_step],
                [native_state, *native_outputs, native_report])
        native_json_button.click(native_download, [native_state], [native_json_download])
        native_game_button.click(native_game, [native_state, scummc_path], [native_game_download])
    return app


def main() -> None:
    codespaces = os.environ.get("CODESPACES", "").lower() == "true"
    make_app().launch(server_name="0.0.0.0" if codespaces else "127.0.0.1",
                      server_port=7860, share=False, inbrowser=not codespaces)


if __name__ == "__main__":
    main()
