"""Optional Gradio authoring UI over the validated story-service boundary.

Run: python -m adventure_studio.studio_gradio
No network/API key is needed for this offline first iteration.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from .studio_service import (add_decoration, change_item, change_scene,
                             describe_story, report_text, scene_preview)
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
    initial_view = describe_story(initial)

    def selectors(raw: str):
        view = describe_story(raw)
        scene = view.scenes[0][0]
        item = view.items[0][0] if view.items else None
        chapters = "\n".join(f"- {title} (`{id_}`)" for id_, title in view.chapters)
        path = " → ".join(view.playable_path)
        return (gr.update(choices=[(title, id_) for id_, title in view.scenes], value=scene),
                gr.update(choices=[(f"{name} ({scene_id})", id_) for id_, name, scene_id in view.items], value=item),
                f"**Kapitel**\n{chapters}\n\n**Spielbarer Pfad:** {path}",
                *scene_fields(raw, scene), *item_fields(raw, item or ""), render_scene(raw, scene))

    def load_file(file_path):
        if not file_path:
            raise gr.Error("Bitte eine Story-JSON-Datei wählen")
        try:
            raw = canonical_story_json(parse_story_document(Path(file_path).read_text(encoding="utf-8")))
            return (raw, *selectors(raw), "Story erfolgreich geladen und validiert")
        except (ValueError, OSError) as error:
            raise gr.Error(str(error)) from error

    def apply_scene(raw, scene_id, title, description):
        try:
            result = change_scene(raw, scene_id, title, description)
            return (result.story_json, *selectors(result.story_json), report_text(result.report))
        except ValueError as error:
            raise gr.Error(str(error)) from error

    def apply_item(raw, item_id, name, description):
        try:
            result = change_item(raw, item_id, name, description)
            return (result.story_json, *selectors(result.story_json), report_text(result.report))
        except ValueError as error:
            raise gr.Error(str(error)) from error

    def apply_decoration(raw, scene_id, item_id, name, description):
        try:
            result = add_decoration(raw, scene_id, item_id, name, description)
            return (result.story_json, *selectors(result.story_json), report_text(result.report))
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
        with gr.Row():
            story_file = gr.File(label="Story-JSON öffnen", file_types=[".json"], type="filepath")
            export_button = gr.Button("Geprüfte Story exportieren", variant="primary")
            download = gr.File(label="Story herunterladen")
        overview = gr.Markdown()
        with gr.Tab("Szenen"):
            scene_select = gr.Dropdown(label="Szene")
            scene_title = gr.Textbox(label="Titel")
            scene_description = gr.Textbox(label="Beschreibung", lines=4)
            save_scene = gr.Button("Szenenänderung prüfen und übernehmen")
            preview = gr.Image(label="Raumvorschau (Hotspots markiert)", interactive=False)
        with gr.Tab("Gegenstände"):
            item_select = gr.Dropdown(label="Gegenstand")
            item_name = gr.Textbox(label="Name")
            item_description = gr.Textbox(label="Beschreibung", lines=3)
            save_item = gr.Button("Gegenstandsänderung prüfen und übernehmen")
            gr.Markdown("### Dekorationsobjekt hinzufügen\nEin neues Objekt bleibt in der Story; die einfache SCUMM-Vorschau positioniert es vorläufig automatisch.")
            new_id = gr.Textbox(label="Stabile Objekt-ID (z. B. Fridge)")
            new_name = gr.Textbox(label="Name")
            new_description = gr.Textbox(label="Beschreibung")
            add_item = gr.Button("Objekt prüfen und hinzufügen")
        report = gr.Textbox(label="Deterministischer Änderungs- und Prüfbericht", lines=7, interactive=False)

        refreshed = [scene_select, item_select, overview, scene_title,
                     scene_description, item_name, item_description, preview]
        app.load(selectors, inputs=[state], outputs=refreshed)
        story_file.change(load_file, inputs=[story_file], outputs=[state, *refreshed, report])
        scene_select.change(scene_fields, inputs=[state, scene_select], outputs=[scene_title, scene_description])
        scene_select.change(render_scene, inputs=[state, scene_select], outputs=[preview])
        item_select.change(item_fields, inputs=[state, item_select], outputs=[item_name, item_description])
        save_scene.click(apply_scene, [state, scene_select, scene_title, scene_description],
                         [state, *refreshed, report])
        save_item.click(apply_item, [state, item_select, item_name, item_description],
                        [state, *refreshed, report])
        add_item.click(apply_decoration, [state, scene_select, new_id, new_name, new_description],
                       [state, *refreshed, report])
        export_button.click(export_story, inputs=[state], outputs=[download])
    return app


def main() -> None:
    make_app().launch(inbrowser=True)


if __name__ == "__main__":
    main()
