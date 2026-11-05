"""Optional Gradio authoring UI over the validated story-service boundary.

Run: python -m adventure_studio.studio_gradio
No network/API key is needed for this offline first iteration.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from .studio_service import (accept_proposal, add_decoration, change_item,
                             change_puzzle, change_scene, describe_story,
                             prepare_proposal, report_text, scene_preview)
from .story_document import canonical_story_json, parse_story_document


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
        chapters = "\n".join(f"- {title} (`{id_}`)" for id_, title in view.chapters)
        path = " → ".join(view.playable_path)
        return (gr.update(choices=[(title, id_) for id_, title in view.scenes], value=scene),
                gr.update(choices=[(f"{name} ({scene_id})", id_) for id_, name, scene_id in view.items], value=item),
                gr.update(choices=[(title, id_) for id_, title in view.puzzles], value=puzzle),
                f"**Kapitel**\n{chapters}\n\n**Spielbarer Pfad:** {path}",
                *scene_fields(raw, scene), *item_fields(raw, item or ""),
                *puzzle_fields(raw, puzzle or ""), render_scene(raw, scene))

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

    with gr.Blocks(title="Adventure Studio") as app:
        gr.Markdown("# Adventure Studio\nStory schreiben, prüfen und als SCUMM-fähige Daten speichern. Noch ohne KI-Anbindung.")
        state = gr.State(initial)
        pending = gr.State(None)
        with gr.Row():
            story_file = gr.File(label="Story-JSON öffnen", file_types=[".json"], type="filepath")
            export_button = gr.Button("Geprüfte Story exportieren", variant="primary")
            download = gr.File(label="Story herunterladen")
        overview = gr.Markdown()
        with gr.Tab("Szenen"):
            scene_select = gr.Dropdown(label="Szene")
            scene_title = gr.Textbox(label="Titel")
            scene_description = gr.Textbox(label="Beschreibung", lines=4)
            save_scene = gr.Button("Szenenänderung prüfen")
            preview = gr.Image(label="Raumvorschau (Hotspots markiert)", interactive=False)
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
        report = gr.Textbox(label="Deterministischer Änderungs- und Prüfbericht", lines=7, interactive=False)
        confirm_button = gr.Button("Geprüfte Änderung jetzt übernehmen", variant="primary")

        refreshed = [scene_select, item_select, puzzle_select, overview, scene_title,
                     scene_description, item_name, item_description, puzzle_title, puzzle_items, preview]
        app.load(selectors, inputs=[state], outputs=refreshed)
        def load_and_clear(file_path):
            raw, *rest = load_file(file_path)
            return (raw, None, *rest)

        story_file.change(load_and_clear, inputs=[story_file], outputs=[state, pending, *refreshed, report])
        scene_select.change(scene_fields, inputs=[state, scene_select], outputs=[scene_title, scene_description])
        scene_select.change(render_scene, inputs=[state, scene_select], outputs=[preview])
        item_select.change(item_fields, inputs=[state, item_select], outputs=[item_name, item_description])
        puzzle_select.change(puzzle_fields, inputs=[state, puzzle_select], outputs=[puzzle_title, puzzle_items])
        save_scene.click(lambda *args: propose(change_scene, *args),
                         [state, scene_select, scene_title, scene_description], [pending, report])
        save_item.click(lambda *args: propose(change_item, *args),
                        [state, item_select, item_name, item_description], [pending, report])
        add_item.click(lambda *args: propose(add_decoration, *args),
                       [state, scene_select, new_id, new_name, new_description], [pending, report])
        save_puzzle.click(propose_puzzle, [state, puzzle_select, puzzle_title, puzzle_items],
                          [pending, report])
        confirm_button.click(confirm, [state, pending], [state, pending, *refreshed, report])
        export_button.click(export_story, inputs=[state], outputs=[download])
    return app


def main() -> None:
    make_app().launch(inbrowser=True)


if __name__ == "__main__":
    main()
