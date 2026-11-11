"""Real Chromium acceptance of native dialogue pose authoring in Gradio.

Uses a generated SCUMM-v6 project, the actual browser controls, and a
download/reimport cycle. Run only from the Gradio UI CI with a live server.
"""

from __future__ import annotations

import json
import os
import re
from io import BytesIO
from dataclasses import replace
from pathlib import Path
from urllib.parse import urljoin

from PIL import Image
from playwright.sync_api import expect, sync_playwright

from adventure_studio.scumm_project import canonical_json, parse_document
from adventure_studio.studio_sequences import (
    dialogue_animation_lines, dialogue_speaking_frame_selection,
    dialogue_speaking_sequence_selection, dialogue_speaking_template_choices,
    dialogue_ending_timeline,
    dialogue_ending_animation_selection,
)
from adventure_studio.studio_actors import costume_direction_speaking_frame


def select_option(page, elem_id: str, label: str) -> None:
    """Select a Gradio Dropdown option by the text visible to authors."""
    dropdown = page.locator("#" + elem_id)
    entry = dropdown.locator('input[role="combobox"]')
    entry.click()
    entry.fill(label)
    options_id = entry.get_attribute("aria-controls")
    if options_id:
        options = page.locator('[id="' + options_id + '"]')
        print("Dropdown", elem_id, "expanded", entry.get_attribute("aria-expanded"),
              "options", options.inner_text()[:1200] if options.count() else "none")
    page.get_by_role("option", name=label, exact=True).click(timeout=12000)


def displayed_value(page, elem_id: str) -> str:
    dropdown = page.locator("#" + elem_id)
    entry = dropdown.locator("input")
    if entry.count() and entry.first.input_value():
        return entry.first.input_value()
    return dropdown.inner_text()


def await_selection(page, elem_id: str, label: str) -> None:
    page.wait_for_function(
        """({id, label}) => {
            const element = document.getElementById(id);
            if (!element) return false;
            const input = element.querySelector('input');
            return (input && input.value === label) ||
                   element.textContent.trim() === label;
        }""",
        arg={"id": elem_id, "label": label}, timeout=15000,
    )


def await_preview_color(page, rgb: tuple[int, int, int]) -> None:
    """Require real pixel colors from the Gradio image in Chromium."""
    image = page.locator("#native-dialogue-pose-preview img")
    expect(image.first).to_have_attribute("src", re.compile(r"/gradio_api/file="), timeout=20000)
    image.first.evaluate("(img) => { img.loading = 'eager'; }")
    page.wait_for_function(
        """({color}) => {
            const img = document.querySelector('#native-dialogue-pose-preview img');
            if (!img || !img.complete || img.naturalWidth === 0) return false;
            const canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
            const context = canvas.getContext('2d');
            context.drawImage(img, 0, 0);
            const rgba = context.getImageData(0, 0, canvas.width, canvas.height).data;
            let count = 0;
            for (let i = 0; i < rgba.length; i += 4) {
                if (Math.abs(rgba[i] - color[0]) <= 25 &&
                    Math.abs(rgba[i+1] - color[1]) <= 25 &&
                    Math.abs(rgba[i+2] - color[2]) <= 25) count++;
            }
            return count >= 24;
        }""", arg={"color": list(rgb)}, timeout=20000,
    )


def await_direction_preview_color(page, rgb: tuple[int, int, int]) -> None:
    """Inspect native direction-specific frame pixels, not only the dropdown."""
    image = page.locator("#native-dialogue-direction-preview img")
    expect(image.first).to_have_attribute("src", re.compile(r"/gradio_api/file="), timeout=20000)
    image.first.evaluate("(img) => { img.loading = 'eager'; }")
    page.wait_for_function(
        """({color}) => {
            const img = document.querySelector('#native-dialogue-direction-preview img');
            if (!img || !img.complete || img.naturalWidth === 0) return false;
            const canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
            const context = canvas.getContext('2d');
            context.drawImage(img, 0, 0);
            const rgba = context.getImageData(0, 0, canvas.width, canvas.height).data;
            let count = 0;
            for (let i = 0; i < rgba.length; i += 4) {
                if (Math.abs(rgba[i] - color[0]) <= 25 &&
                    Math.abs(rgba[i+1] - color[1]) <= 25 &&
                    Math.abs(rgba[i+2] - color[2]) <= 25) count++;
            }
            return count >= 24;
        }""", arg={"color": list(rgb)}, timeout=20000,
    )


def await_batch_gallery_colors(page, colors: list[tuple[int, int, int]],
                               gallery_id="native-dialogue-png-batch-gallery") -> None:
    """Read rendered thumbnail pixels in the exact import order in Chromium."""
    gallery = page.locator("#" + gallery_id)
    gallery.scroll_into_view_if_needed()
    page.wait_for_function(
        """({colors, galleryId}) => {
            const images = [...document.querySelectorAll('#' + galleryId + ' img')];
            if (images.length !== colors.length) return false;
            return images.every((img, i) => {
                if (!img.complete || !img.naturalWidth || !img.naturalHeight) return false;
                const canvas = document.createElement('canvas');
                canvas.width = canvas.height = 1;
                const context = canvas.getContext('2d');
                context.drawImage(img, Math.floor(img.naturalWidth / 2),
                    Math.floor(img.naturalHeight / 2), 1, 1, 0, 0, 1, 1);
                const pixel = context.getImageData(0, 0, 1, 1).data;
                return colors[i].every((expected, channel) =>
                    Math.abs(pixel[channel] - expected) <= 18);
            });
        }""", arg={"colors": [list(color) for color in colors],
                   "galleryId": gallery_id}, timeout=20000)


def await_batch_frame_color(page, color: tuple[int, int, int]) -> None:
    """Verify the navigated single-image preview contains the staged PNG pixels."""
    page.wait_for_function(
        """({color}) => {
            const img = document.querySelector('#native-dialogue-png-batch-frame-image img');
            if (!img || !img.complete || !img.naturalWidth) return false;
            const canvas = document.createElement('canvas');
            canvas.width = canvas.height = 1;
            const context = canvas.getContext('2d');
            context.drawImage(img, Math.floor(img.naturalWidth / 2),
                Math.floor(img.naturalHeight / 2), 1, 1, 0, 0, 1, 1);
            const pixel = context.getImageData(0, 0, 1, 1).data;
            return color.every((expected, channel) =>
                Math.abs(pixel[channel] - expected) <= 18);
        }""", arg={"color": list(color)}, timeout=20000)


def main() -> None:
    fixture = Path(os.environ["ADVENTURE_STUDIO_BROWSER_PROJECT"]).resolve()
    evidence = Path(os.environ.get("ADVENTURE_STUDIO_BROWSER_EVIDENCE", "/tmp/studio-browser-evidence"))
    evidence.mkdir(parents=True, exist_ok=True)
    raw = fixture.read_text(encoding="utf-8")
    names = [(label, identity) for label, identity in dialogue_animation_lines(raw)
             if label.startswith("SpeakerWitness")]
    if len(names) < 2:
        raise AssertionError(f"Expected at least two real authored NPC lines: {names}")
    first, second = names[:2]
    if dialogue_speaking_frame_selection(raw, first[1])[1] != "Speak":
        raise AssertionError("First fixture pose must be Speak")
    if dialogue_speaking_frame_selection(raw, second[1])[1] != "SpeakAlt":
        raise AssertionError("Second fixture pose must be SpeakAlt")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True,
                                             args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1440, "height": 900},
                                accept_downloads=True)
        try:
            page.goto("http://127.0.0.1:7860/", wait_until="domcontentloaded",
                      timeout=30000)
            page.get_by_role("tab", name="Native Interaktionsabläufe").click()
            page.locator("#native-project-file input[type=file]").set_input_files(
                str(fixture))
            expect(page.locator("#native-project-report textarea, #native-project-report input")).to_have_value(
                "Natives Projekt geladen und validiert", timeout=30000)

            select_option(page, "native-dialogue-line", first[0])
            await_selection(page, "native-dialogue-pose", "Speak")
            await_selection(page, "native-dialogue-animation", "gesture")
            await_preview_color(page, (220, 80, 80))
            select_option(page, "native-dialogue-direction", "Nord")
            expect(page.locator("#native-dialogue-direction-status input, #native-dialogue-direction-status textarea")).to_have_value(
                "gesture · Nord · Frame Speak (native Costume-Palette, statische Editor-Vorschau)")
            await_direction_preview_color(page, (220, 80, 80))
            select_option(page, "native-dialogue-direction", "West")
            expect(page.locator("#native-dialogue-direction-status input, #native-dialogue-direction-status textarea")).to_have_value(
                "gesture · West · Frame Speak (native Costume-Palette, statische Editor-Vorschau)")
            page.screenshot(path=str(evidence / "first-line.png"), full_page=True)

            select_option(page, "native-dialogue-line", second[0])
            await_selection(page, "native-dialogue-pose", "SpeakAlt")
            await_selection(page, "native-dialogue-animation", "pose_SpeakAlt")
            await_preview_color(page, (35, 225, 35))
            select_option(page, "native-dialogue-direction", "Ost")
            expect(page.locator("#native-dialogue-direction-status input, #native-dialogue-direction-status textarea")).to_have_value(
                "pose_SpeakAlt · Ost · Frame SpeakAlt (native Costume-Palette, statische Editor-Vorschau)")
            await_direction_preview_color(page, (35, 225, 35))
            page.screenshot(path=str(evidence / "second-line.png"), full_page=True)

            # Edit the second line using the actual PNG selector and button,
            # while retaining the first line's native talk-start pose.
            select_option(page, "native-dialogue-pose", "Speak")
            await_preview_color(page, (220, 80, 80))
            page.locator("#native-dialogue-pose-apply").click()
            await_selection(page, "native-dialogue-pose", "Speak")
            await_selection(page, "native-dialogue-animation", "gesture")
            await_preview_color(page, (220, 80, 80))

            # Author a different native frame for one facing direction using
            # the actual Costume editor, not a direct model-only edit.
            select_option(page, "native-costume-select", "WitnessCostume")
            select_option(page, "native-speaking-direction", "Nord")
            await_selection(page, "native-direction-frame", "Speak")
            select_option(page, "native-direction-frame", "SpeakAlt")
            page.locator("#native-direction-save").click()
            await_selection(page, "native-direction-frame", "SpeakAlt")
            select_option(page, "native-speaking-direction", "Ost")
            await_selection(page, "native-direction-frame", "Speak")
            select_option(page, "native-speaking-direction", "Nord")
            await_selection(page, "native-direction-frame", "SpeakAlt")
            page.screenshot(path=str(evidence / "direction-authored.png"), full_page=True)

            page.locator("#native-project-export-button").click()
            download_link = page.locator("#native-project-export-file a[download]")
            expect(download_link.first).to_be_visible(timeout=20000)
            with page.expect_download() as info:
                download_link.first.click()
            download = info.value
            saved = evidence / "saved-native-project.json"
            download.save_as(str(saved))
            updated = parse_document(saved.read_text(encoding="utf-8"))
            data = saved.read_text(encoding="utf-8")
            assert updated.dialogue_animation_cues
            # A direction-dependent gesture is deliberately not presented
            # as one unambiguous PNG in the line-level shortcut selector.
            assert dialogue_speaking_frame_selection(data, first[1])[1] is None
            assert dialogue_speaking_frame_selection(data, second[1])[1] is None
            assert costume_direction_speaking_frame(data, "WitnessCostume", "N") == "SpeakAlt"
            assert costume_direction_speaking_frame(data, "WitnessCostume", "E") == "Speak"
            assert costume_direction_speaking_frame(data, "WitnessCostume", "S") == "Speak"
            assert costume_direction_speaking_frame(data, "WitnessCostume", "W") == "Speak"

            # A Gradio File changes to a preview after loading. Authors
            # clear the selected file before choosing a replacement.
            page.locator('#native-project-file button[aria-label="Clear"]').click()
            page.locator("#native-project-file input[type=file]").set_input_files(
                str(saved))
            expect(page.locator("#native-project-report textarea, #native-project-report input")).to_have_value(
                "Natives Projekt geladen und validiert", timeout=30000)
            select_option(page, "native-dialogue-line", second[0])
            await_selection(page, "native-dialogue-animation", "gesture")
            select_option(page, "native-dialogue-line", first[0])
            await_selection(page, "native-dialogue-animation", "gesture")
            page.screenshot(path=str(evidence / "reimported.png"), full_page=True)
            select_option(page, "native-costume-select", "WitnessCostume")
            select_option(page, "native-speaking-direction", "Nord")
            await_selection(page, "native-direction-frame", "SpeakAlt")
            # Two different multi-frame animations through the real dialogue
            # editor, preserving the actor's shared Costume and old cues.
            sequence_input = page.locator("#native-dialogue-speaking-sequence textarea, #native-dialogue-speaking-sequence input")
            # The first line is already selected and its animation refreshed
            # above. Re-selecting it starts a redundant asynchronous Gradio
            # callback that can race with the immediately following save.
            await_selection(page, "native-dialogue-line", first[0])
            expect(sequence_input).to_have_value("Speak", timeout=20000)
            draft_save_status = page.locator("#native-dialogue-draft-save-status")
            expect(draft_save_status).to_contain_text(
                "Sprechfolge entspricht dem gespeicherten Stand", timeout=20000)
            sequence_input.fill("SpeakAlt, SpeakAlt")
            expect(draft_save_status).to_contain_text(
                "Ungespeicherte Änderungen an der Sprechfolge", timeout=20000)
            select_option(page, "native-dialogue-line", second[0])
            expect(sequence_input).to_have_value("Speak", timeout=20000)
            select_option(page, "native-dialogue-line", first[0])
            expect(sequence_input).to_have_value("SpeakAlt, SpeakAlt", timeout=20000)
            expect(draft_save_status).to_contain_text(
                "Ungespeicherte Änderungen an der Sprechfolge", timeout=20000)
            page.locator("#native-dialogue-draft-discard").click()
            expect(sequence_input).to_have_value("Speak", timeout=20000)
            expect(draft_save_status).to_contain_text(
                "Sprechfolge entspricht dem gespeicherten Stand", timeout=20000)
            # The persistent saved-state indicator confirms discard; preview
            # feedback is cleared because no GIF belongs to the restored draft.
            picker_image = page.locator("#native-dialogue-draft-frame-preview img")
            expect(picker_image.first).to_be_visible(timeout=20000)
            initial_src = picker_image.first.get_attribute("src")
            select_option(page, "native-dialogue-draft-frame", "Speak")
            expect(picker_image.first).not_to_have_attribute(
                "src", initial_src, timeout=20000)
            red_src = picker_image.first.get_attribute("src")
            red_response = page.request.get(urljoin(page.url, red_src))
            assert red_response.ok
            with Image.open(BytesIO(red_response.body())) as red_picture:
                assert red_picture.convert("RGB").getpixel((128, 128))[0] > 180
            select_option(page, "native-dialogue-draft-frame", "SpeakAlt")
            expect(picker_image.first).not_to_have_attribute(
                "src", red_src, timeout=20000)
            green_response = page.request.get(
                urljoin(page.url, picker_image.first.get_attribute("src")))
            assert green_response.ok
            with Image.open(BytesIO(green_response.body())) as green_picture:
                assert green_picture.convert("RGB").getpixel((128, 128))[1] > 180
            page.locator("#native-dialogue-draft-add").click()
            expect(sequence_input).to_have_value("Speak, SpeakAlt", timeout=20000)
            select_option(page, "native-dialogue-draft-step", "2. SpeakAlt")
            step_picture = page.locator("#native-dialogue-draft-step-preview img")
            expect(step_picture.first).to_be_visible(timeout=20000)
            green_step_response = page.request.get(
                urljoin(page.url, step_picture.first.get_attribute("src")))
            assert green_step_response.ok
            with Image.open(BytesIO(green_step_response.body())) as green_step:
                assert green_step.convert("RGB").getpixel((128, 128))[1] > 180
            select_option(page, "native-dialogue-draft-frame", "Speak")
            page.locator("#native-dialogue-draft-insert-before").click()
            expect(sequence_input).to_have_value("Speak, Speak, SpeakAlt", timeout=20000)
            select_option(page, "native-dialogue-draft-step", "2. Speak")
            page.locator("#native-dialogue-draft-remove").click()
            expect(sequence_input).to_have_value("Speak, SpeakAlt", timeout=20000)
            select_option(page, "native-dialogue-draft-step", "2. SpeakAlt")
            page.locator("#native-dialogue-draft-insert-after").click()
            expect(sequence_input).to_have_value("Speak, SpeakAlt, Speak", timeout=20000)
            select_option(page, "native-dialogue-draft-step", "3. Speak")
            page.locator("#native-dialogue-draft-remove").click()
            expect(sequence_input).to_have_value("Speak, SpeakAlt", timeout=20000)
            select_option(page, "native-dialogue-draft-step", "2. SpeakAlt")
            page.locator("#native-dialogue-draft-duplicate").click()
            expect(sequence_input).to_have_value("Speak, SpeakAlt, SpeakAlt", timeout=20000)
            select_option(page, "native-dialogue-draft-step", "3. SpeakAlt")
            page.locator("#native-dialogue-draft-remove").click()
            expect(sequence_input).to_have_value("Speak, SpeakAlt", timeout=20000)
            select_option(page, "native-dialogue-draft-step", "2. SpeakAlt")
            page.locator("#native-dialogue-draft-up").click()
            expect(sequence_input).to_have_value("SpeakAlt, Speak", timeout=20000)
            green_step_src = step_picture.first.get_attribute("src")
            select_option(page, "native-dialogue-draft-step", "2. Speak")
            expect(step_picture.first).not_to_have_attribute(
                "src", green_step_src, timeout=20000)
            red_step_response = page.request.get(
                urljoin(page.url, step_picture.first.get_attribute("src")))
            assert red_step_response.ok
            with Image.open(BytesIO(red_step_response.body())) as red_step:
                assert red_step.convert("RGB").getpixel((128, 128))[0] > 180
            select_option(page, "native-dialogue-draft-frame", "SpeakAlt")
            page.locator("#native-dialogue-draft-replace").click()
            expect(sequence_input).to_have_value("SpeakAlt, SpeakAlt", timeout=20000)
            select_option(page, "native-dialogue-draft-frame", "Speak")
            page.locator("#native-dialogue-draft-replace").click()
            expect(sequence_input).to_have_value("SpeakAlt, Speak", timeout=20000)
            select_option(page, "native-dialogue-draft-step", "1. SpeakAlt")
            page.locator("#native-dialogue-draft-down").click()
            expect(sequence_input).to_have_value("Speak, SpeakAlt", timeout=20000)
            select_option(page, "native-dialogue-draft-step", "2. SpeakAlt")
            page.locator("#native-dialogue-draft-remove").click()
            expect(sequence_input).to_have_value("Speak", timeout=20000)
            select_option(page, "native-dialogue-draft-frame", "SpeakAlt")
            page.locator("#native-dialogue-draft-add").click()
            expect(sequence_input).to_have_value("Speak, SpeakAlt", timeout=20000)
            page.locator("#native-dialogue-draft-duration input").fill("260")
            page.locator("#native-dialogue-draft-play").click()
            draft_gif = page.locator("#native-dialogue-draft-animation img")
            expect(draft_gif.first).to_be_visible(timeout=20000)
            expect(page.locator("#native-dialogue-draft-animation-status")).to_contain_text(
                "260 ms pro Bild · nur Entwurf", timeout=20000)
            draft_response = page.request.get(
                urljoin(page.url, draft_gif.first.get_attribute("src")))
            assert draft_response.ok
            with Image.open(BytesIO(draft_response.body())) as draft_animation:
                assert draft_animation.format == "GIF"
                assert draft_animation.n_frames == 2
                assert draft_animation.info["duration"] == 260
            sequence_input.fill("SpeakAlt, Speak")
            expect(draft_gif).to_have_count(0, timeout=20000)
            sequence_input.fill("Speak, SpeakAlt")
            expect(draft_save_status).to_contain_text(
                "Ungespeicherte Änderungen an der Sprechfolge", timeout=20000)
            page.locator("#native-dialogue-sequence-apply").click()
            expect(page.locator("#native-project-report textarea, #native-project-report input")).to_have_value(
                "Interaktionsablauf geändert und validiert", timeout=20000)
            expect(sequence_input).to_have_value("Speak, SpeakAlt", timeout=20000)
            expect(draft_save_status).to_contain_text(
                "Sprechfolge entspricht dem gespeicherten Stand", timeout=20000)
            page.get_by_text("Sprechfolge als Vorlage für weitere Dialogzeilen",
                             exact=True).click()
            page.locator("#native-dialogue-template-name input, #native-dialogue-template-name textarea").fill("Begrüßung")
            page.locator("#native-dialogue-template-save").click()
            expect(page.locator("#native-dialogue-template-status")).to_contain_text(
                "Begrüßung", timeout=20000)
            select_option(page, "native-dialogue-line", second[0])
            expect(sequence_input).to_have_value("Speak", timeout=20000)
            page.locator("#native-dialogue-template-apply").click()
            expect(sequence_input).to_have_value("Speak, SpeakAlt", timeout=20000)
            sequence_input.fill("SpeakAlt, Speak, SpeakAlt")
            page.locator("#native-dialogue-sequence-apply").click()
            expect(sequence_input).to_have_value("SpeakAlt, Speak, SpeakAlt", timeout=20000)
            select_option(page, "native-dialogue-line", first[0])
            expect(sequence_input).to_have_value("Speak, SpeakAlt", timeout=20000)
            page.screenshot(path=str(evidence / "line-sequences-authored.png"), full_page=True)
            page.locator("#native-project-export-button").click()
            sequence_link = page.locator("#native-project-export-file a[download]")
            expect(sequence_link.first).to_be_visible(timeout=20000)
            with page.expect_download() as sequence_info:
                sequence_link.first.click()
            sequence_file = evidence / "line-sequences-project.json"
            sequence_info.value.save_as(str(sequence_file))
            sequence_data = sequence_file.read_text(encoding="utf-8")
            assert dialogue_speaking_sequence_selection(sequence_data, first[1]) == "Speak, SpeakAlt"
            assert dialogue_speaking_sequence_selection(sequence_data, second[1]) == "SpeakAlt, Speak, SpeakAlt"
            assert dialogue_speaking_template_choices(sequence_data) == ["Begrüßung"]
            page.locator('#native-project-file button[aria-label="Clear"]').click()
            page.locator("#native-project-file input[type=file]").set_input_files(str(sequence_file))
            expect(page.locator("#native-project-report textarea, #native-project-report input")).to_have_value(
                "Natives Projekt geladen und validiert", timeout=30000)
            select_option(page, "native-dialogue-template-select", "Begrüßung")
            template_preview = page.locator(
                "#native-dialogue-template-preview textarea, "
                "#native-dialogue-template-preview input")
            expect(template_preview).to_have_value(
                re.compile(r"Vorlage: Begrüßung.*Costume: WitnessCostume.*"
                           r"Abspielbilder: 2.*1\. Speak.*2\. SpeakAlt.*"
                           r"Ziel: kompatibel", re.S), timeout=20000)
            expect(page.locator("#native-dialogue-template-apply")).to_be_enabled(
                timeout=20000)
            page.locator("#native-dialogue-template-duration input").fill("240")
            page.locator("#native-dialogue-template-play").click()
            template_gif = page.locator("#native-dialogue-template-animation img")
            expect(template_gif.first).to_be_visible(timeout=20000)
            expect(page.locator("#native-dialogue-template-animation-status")).to_contain_text(
                "240 ms pro Bild nur im Editor", timeout=20000)
            template_response = page.request.get(
                urljoin(page.url, template_gif.first.get_attribute("src")))
            assert template_response.ok
            with Image.open(BytesIO(template_response.body())) as template_animation:
                assert template_animation.format == "GIF"
                assert template_animation.n_frames == 2
                assert template_animation.info["duration"] == 240
            await_selection(page, "native-dialogue-line", first[0])
            sequence_input.fill("unfertiger Entwurf")
            page.locator("#native-dialogue-template-load").click()
            expect(sequence_input).to_have_value(
                "Speak, SpeakAlt", timeout=20000)
            expect(page.locator("#native-dialogue-template-status")).to_contain_text(
                "noch nicht gespeichert", timeout=20000)
            sequence_input.fill("SpeakAlt, Speak")
            page.locator("#native-dialogue-template-update").click()
            expect(page.locator("#native-dialogue-template-status")).to_contain_text(
                "aktualisiert", timeout=20000)
            expect(page.locator("#native-dialogue-template-select input")).to_have_value(
                "Begrüßung", timeout=20000)
            page.locator(
                "#native-dialogue-template-name input, #native-dialogue-template-name textarea"
            ).fill("Antwort")
            page.locator("#native-dialogue-template-rename").click()
            expect(page.locator("#native-dialogue-template-status")).to_contain_text(
                "umbenannt", timeout=20000)
            expect(page.locator("#native-dialogue-template-select input")).to_have_value(
                "Antwort", timeout=20000)
            page.locator("#native-dialogue-template-delete").click()
            expect(page.locator("#native-dialogue-template-status")).to_contain_text(
                "gelöscht", timeout=20000)
            expect(page.locator("#native-dialogue-template-select input")).to_have_value(
                "", timeout=20000)

            page.locator("#native-dialogue-draft-discard").click()
            expect(sequence_input).to_have_value("Speak, SpeakAlt", timeout=20000)
            select_option(page, "native-dialogue-line", second[0])
            expect(sequence_input).to_have_value("SpeakAlt, Speak, SpeakAlt", timeout=20000)
            select_option(page, "native-dialogue-line", first[0])
            expect(sequence_input).to_have_value("Speak, SpeakAlt", timeout=20000)
            select_option(page, "native-dialogue-direction", "Süd")
            expect(sequence_input).to_have_value("Speak, SpeakAlt", timeout=20000)
            sequence_input.fill("SpeakAlt")
            select_option(page, "native-dialogue-direction", "Nord")
            expect(sequence_input).to_have_value("Speak, SpeakAlt", timeout=20000)
            expect(draft_save_status).to_contain_text(
                "Sprechfolge entspricht dem gespeicherten Stand", timeout=20000)
            sequence_input.fill("SpeakAlt, Speak")
            expect(draft_save_status).to_contain_text(
                "Ungespeicherte Änderungen an der Sprechfolge", timeout=20000)
            page.locator("#native-dialogue-direction-sequence-apply").click()
            expect(page.locator("#native-project-report textarea, #native-project-report input")).to_have_value(
                "Interaktionsablauf geändert und validiert", timeout=20000)
            expect(sequence_input).to_have_value("SpeakAlt, Speak", timeout=20000)
            select_option(page, "native-dialogue-direction", "Süd")
            expect(sequence_input).to_have_value("SpeakAlt", timeout=20000)
            page.locator("#native-dialogue-draft-discard").click()
            expect(sequence_input).to_have_value("Speak, SpeakAlt", timeout=20000)
            select_option(page, "native-dialogue-direction", "Nord")
            expect(sequence_input).to_have_value("SpeakAlt, Speak", timeout=20000)
            # Edit the saved line/facing by clicking the graphical timeline,
            # then play its actual indexed PNG frames as an editor GIF.
            timeline_gallery = page.locator("#native-dialogue-timeline-gallery")
            expect(timeline_gallery.locator("img")).to_have_count(2, timeout=20000)
            select_option(page, "native-dialogue-timeline-add-frame", "SpeakAlt")
            page.locator("#native-dialogue-timeline-append").click()
            expect(sequence_input).to_have_value("SpeakAlt, Speak, SpeakAlt", timeout=20000)
            expect(timeline_gallery.locator("img")).to_have_count(3, timeout=20000)
            select_option(page, "native-dialogue-timeline-step", "3. SpeakAlt")
            page.locator("#native-dialogue-timeline-left").click()
            expect(sequence_input).to_have_value("SpeakAlt, SpeakAlt, Speak", timeout=20000)
            select_option(page, "native-dialogue-timeline-step", "2. SpeakAlt")
            page.locator("#native-dialogue-timeline-remove").click()
            expect(sequence_input).to_have_value("SpeakAlt, Speak", timeout=20000)
            page.locator("#native-dialogue-timeline-play").click()
            gif_preview = page.locator("#native-dialogue-timeline-preview img")
            expect(gif_preview.first).to_be_visible(timeout=20000)
            page.locator("#native-dialogue-timeline-append").click()
            expect(sequence_input).to_have_value("SpeakAlt, Speak, SpeakAlt", timeout=20000)
            phase_start = page.locator("#native-dialogue-phase-start input")
            phase_minimum = page.locator("#native-dialogue-phase-minimum input")
            phase_start.fill("12")
            phase_minimum.fill("90")
            page.locator("#native-dialogue-phase-save").click()
            select_option(page, "native-dialogue-line", second[0])
            expect(phase_start).to_have_value("1", timeout=20000)
            expect(phase_minimum).to_have_value("60", timeout=20000)
            select_option(page, "native-dialogue-line", first[0])
            expect(phase_start).to_have_value("12", timeout=20000)
            expect(phase_minimum).to_have_value("90", timeout=20000)
            select_option(page, "native-dialogue-ending-animation", "gesture")
            ending_ticks = page.locator("#native-dialogue-ending-ticks input")
            ending_ticks.fill("18")
            page.locator("#native-dialogue-ending-save").click()
            select_option(page, "native-dialogue-line", second[0])
            expect(ending_ticks).to_have_value("12", timeout=20000)
            select_option(page, "native-dialogue-line", first[0])
            expect(ending_ticks).to_have_value("18", timeout=20000)
            await_selection(page, "native-dialogue-ending-animation", "gesture")
            page.screenshot(path=str(evidence / "line-direction-sequence.png"), full_page=True)
            page.locator("#native-project-export-button").click()
            expect(sequence_link.first).to_be_visible(timeout=20000)
            with page.expect_download() as directional_info:
                sequence_link.first.click()
            directional_file = evidence / "line-direction-project.json"
            directional_info.value.save_as(str(directional_file))
            directional_data = directional_file.read_text(encoding="utf-8")
            assert dialogue_speaking_sequence_selection(directional_data, first[1], "N") == "SpeakAlt, Speak, SpeakAlt"
            assert dialogue_speaking_sequence_selection(directional_data, first[1], "S") == "Speak, SpeakAlt"
            assert dialogue_speaking_sequence_selection(directional_data, second[1], "N") == "SpeakAlt, Speak, SpeakAlt"
            phases = {cue.line_id: cue for cue in parse_document(directional_data).dialogue_animation_cues}
            assert (phases[first[1]].start_delay_ticks, phases[first[1]].minimum_animation_ticks) == (12, 90)
            assert (phases[second[1]].start_delay_ticks, phases[second[1]].minimum_animation_ticks) == (1, 60)
            assert (phases[first[1]].ending_animation, phases[first[1]].ending_animation_ticks) == ("gesture", 18)
            assert phases[second[1]].ending_animation is None
            # Direct PNG authoring for the ending cue: no Costume-editor roundtrip.
            # The native ending slot remains private to this line and direction.
            select_option(page, "native-dialogue-ending-frame", "Speak")
            page.locator("#native-dialogue-ending-append").click()
            ending_gallery = page.locator("#native-dialogue-ending-gallery")
            expect(ending_gallery.locator("img")).to_have_count(2, timeout=20000)
            select_option(page, "native-dialogue-ending-frame", "SpeakAlt")
            page.locator("#native-dialogue-ending-append").click()
            expect(ending_gallery.locator("img")).to_have_count(3, timeout=20000)
            select_option(page, "native-dialogue-ending-step", "3. SpeakAlt")
            page.locator("#native-dialogue-ending-left").click()
            select_option(page, "native-dialogue-ending-step", "2. SpeakAlt")
            page.locator("#native-dialogue-ending-delete-frame").click()
            expect(ending_gallery.locator("img")).to_have_count(2, timeout=20000)
            page.locator("#native-dialogue-ending-play").click()
            expect(page.locator("#native-dialogue-ending-preview img").first).to_be_visible(timeout=20000)
            page.locator("#native-project-export-button").click()
            expect(sequence_link.first).to_be_visible(timeout=20000)
            with page.expect_download() as ending_info:
                sequence_link.first.click()
            ending_file = evidence / "ending-png-project.json"
            ending_info.value.save_as(str(ending_file))
            ending_raw = ending_file.read_text(encoding="utf-8")
            ending_cues = {cue.line_id: cue for cue in parse_document(ending_raw).dialogue_animation_cues}
            assert ending_cues[first[1]].ending_animation.startswith("ending_line_")
            assert ending_cues[first[1]].ending_animation_ticks == 18
            assert ending_cues[second[1]].ending_animation is None
            assert len(dialogue_ending_timeline(ending_raw, first[1], "N")[1]) == 2
            assert dialogue_speaking_sequence_selection(ending_raw, first[1], "N") == "SpeakAlt, Speak, SpeakAlt"
            # Import actual *new image files* from the NPC dialogue panel
            # without visiting Costume editor controls.
            speaking_png = evidence / "fresh-speaking.png"
            ending_png = evidence / "fresh-ending.png"
            Image.new("RGBA", (8, 8), (180, 50, 130, 255)).save(speaking_png)
            Image.new("RGBA", (8, 8), (40, 180, 180, 255)).save(ending_png)
            page.get_by_text("PNG-Datei direkt für diese Dialogzeile importieren", exact=True).click()
            png_id = page.locator("#native-dialogue-png-id textarea, #native-dialogue-png-id input")
            page.locator("#native-dialogue-png-file input[type=file]").set_input_files(str(speaking_png))
            png_id.fill("FreshSpeaking")
            page.locator("#native-dialogue-png-import").click()
            expect(sequence_input).to_have_value(
                "SpeakAlt, Speak, SpeakAlt, FreshSpeaking", timeout=20000)
            page.locator('#native-dialogue-png-file button[aria-label="Clear"]').click()
            page.locator("#native-dialogue-png-file input[type=file]").set_input_files(str(ending_png))
            png_id.fill("FreshEnding")
            select_option(page, "native-dialogue-png-target", "Abschlussfolge")
            page.locator("#native-dialogue-png-import").click()
            expect(ending_gallery.locator("img")).to_have_count(3, timeout=20000)
            page.locator("#native-project-export-button").click()
            expect(sequence_link.first).to_be_visible(timeout=20000)
            with page.expect_download() as imported_info:
                sequence_link.first.click()
            imported_file = evidence / "direct-png-import-project.json"
            imported_info.value.save_as(str(imported_file))
            imported_raw = imported_file.read_text(encoding="utf-8")
            assert dialogue_speaking_sequence_selection(imported_raw, first[1], "N").endswith(
                "FreshSpeaking")
            assert dialogue_ending_timeline(imported_raw, first[1], "N")[1][-1][0] == "3. FreshEnding"
            assert dialogue_ending_animation_selection(imported_raw, second[1])[1] is None
            # A second actor intentionally shares the exact native Costume;
            # split it in the real dialogue editor, then import one new PNG.
            shared_project = parse_document(imported_raw)
            original_witness = next(actor for actor in shared_project.actors
                                    if actor.id == "SpeakerWitness")
            shared_project = replace(shared_project, actors=tuple(
                replace(actor, costume=original_witness.costume)
                if actor.id == "SpeakerHarborKeeper" else actor
                for actor in shared_project.actors))
            shared_path = evidence / "shared-costume-project.json"
            shared_path.write_text(canonical_json(shared_project), encoding="utf-8")
            page.locator('#native-project-file button[aria-label="Clear"]').click()
            page.locator("#native-project-file input[type=file]").set_input_files(str(shared_path))
            expect(page.locator("#native-project-report textarea, #native-project-report input")).to_have_value(
                "Natives Projekt geladen und validiert", timeout=30000)
            select_option(page, "native-dialogue-line", first[0])
            isolation_preview = page.locator(
                "#native-dialogue-costume-isolation textarea, #native-dialogue-costume-isolation input")
            expect(isolation_preview).to_have_value(
                re.compile(r"WitnessCostume → WitnessCostume_SpeakerWitness"), timeout=20000)
            page.locator("#native-dialogue-costume-isolate").click()
            expect(isolation_preview).to_have_value(
                re.compile("gehört bereits nur dieser Figur"), timeout=20000)
            isolated_png = evidence / "isolated-ending.png"
            Image.new("RGBA", (8, 8), (185, 100, 210, 255)).save(isolated_png)
            page.locator('#native-dialogue-png-file button[aria-label="Clear"]').click()
            page.locator("#native-dialogue-png-file input[type=file]").set_input_files(str(isolated_png))
            png_id.fill("PrivateEnding")
            page.locator("#native-dialogue-png-import").click()
            expect(ending_gallery.locator("img")).to_have_count(4, timeout=20000)
            page.locator("#native-project-export-button").click()
            expect(sequence_link.first).to_be_visible(timeout=20000)
            with page.expect_download() as split_info:
                sequence_link.first.click()
            isolated_file = evidence / "isolated-costume-project.json"
            split_info.value.save_as(str(isolated_file))
            isolated_document = parse_document(isolated_file.read_text(encoding="utf-8"))
            actors = {actor.id: actor for actor in isolated_document.actors}
            assert actors["SpeakerWitness"].costume == "WitnessCostume_SpeakerWitness"
            assert actors["SpeakerHarborKeeper"].costume == "WitnessCostume"
            costumes = {item.name: item for item in isolated_document.costumes}
            assert "PrivateEnding" in {frame.id for frame in costumes[actors["SpeakerWitness"].costume].frames}
            assert "PrivateEnding" not in {frame.id for frame in costumes[actors["SpeakerHarborKeeper"].costume].frames}
            # Multi-file import: preview names/order, append the whole native
            # sequence in one browser action and verify persisted frame order.
            batch_a = evidence / "Batch-A.png"
            batch_b = evidence / "Batch-B.png"
            batch_c = evidence / "Batch-Excluded.png"
            Image.new("RGBA", (8, 8), (125, 185, 55, 255)).save(batch_a)
            Image.new("RGBA", (8, 8), (225, 110, 40, 255)).save(batch_b)
            Image.new("RGBA", (8, 8), (65, 120, 215, 255)).save(batch_c)
            page.locator("#native-dialogue-png-batch-files input[type=file]").set_input_files(
                [str(batch_a), str(batch_b), str(batch_c)])
            batch_preview = page.locator(
                "#native-dialogue-png-batch-plan textarea, #native-dialogue-png-batch-plan input")
            expect(batch_preview).to_have_value(
                re.compile(r"1\. Batch-A\.png → Batch_A.*2\. Batch-B\.png → Batch_B.*3\. Batch-Excluded\.png → Batch_Excluded", re.S),
                timeout=20000)
            readiness = page.locator("#native-dialogue-png-batch-readiness")
            image_issues = page.locator(
                "#native-dialogue-png-batch-image-issues textarea, "
                "#native-dialogue-png-batch-image-issues input")
            batch_import = page.locator("#native-dialogue-png-batch-import")
            expect(readiness).to_contain_text("Importbereit: 3 PNG-Frame(s)", timeout=20000)
            expect(batch_import).to_be_enabled()
            expect(image_issues).to_have_value("Keine bildbezogenen Konflikte erkannt", timeout=20000)
            await_batch_gallery_colors(page, [(125, 185, 55), (225, 110, 40), (65, 120, 215)])
            select_option(page, "native-dialogue-png-batch-selected", "2. Batch-B.png")
            page.locator("#native-dialogue-png-batch-up").click()
            expect(batch_preview).to_have_value(
                re.compile(r"1\. Batch-B\.png → Batch_B.*2\. Batch-A\.png → Batch_A.*3\. Batch-Excluded\.png → Batch_Excluded", re.S),
                timeout=20000)
            await_batch_gallery_colors(page, [(225, 110, 40), (125, 185, 55), (65, 120, 215)])
            select_option(page, "native-dialogue-png-batch-selected", "3. Batch-Excluded.png")
            page.locator("#native-dialogue-png-batch-remove").click()
            expect(batch_preview).to_have_value(
                re.compile(r"1\. Batch-B\.png → Batch_B\s*2\. Batch-A\.png → Batch_A\s*$"),
                timeout=20000)
            await_batch_gallery_colors(page, [(225, 110, 40), (125, 185, 55)])
            select_option(page, "native-dialogue-png-batch-excluded", "3. Batch-Excluded.png")
            page.locator("#native-dialogue-png-batch-restore").click()
            expect(batch_preview).to_have_value(
                re.compile(r"1\. Batch-B\.png → Batch_B\s*2\. Batch-A\.png → Batch_A\s*3\. Batch-Excluded\.png → Batch_Excluded\s*$"),
                timeout=20000)
            await_batch_gallery_colors(page, [(225, 110, 40), (125, 185, 55), (65, 120, 215)])
            select_option(page, "native-dialogue-png-batch-selected", "2. Batch-A.png")
            page.locator("#native-dialogue-png-batch-remove").click()
            expect(batch_preview).to_have_value(
                re.compile(r"1\. Batch-B\.png → Batch_B\s*2\. Batch-Excluded\.png → Batch_Excluded\s*$"),
                timeout=20000)
            await_batch_gallery_colors(page, [(225, 110, 40), (65, 120, 215)])
            page.locator("#native-dialogue-png-batch-previous").click()
            expect(page.get_by_text("Bild 1 von 2 · Batch_B · noch nicht importiert")).to_be_visible(timeout=20000)
            await_batch_frame_color(page, (225, 110, 40))
            page.locator("#native-dialogue-png-batch-next").click()
            expect(page.get_by_text("Bild 2 von 2 · Batch_Excluded · noch nicht importiert")).to_be_visible(timeout=20000)
            await_batch_frame_color(page, (65, 120, 215))
            # Preview the actual staged sequence, without committing it.
            page.locator("#native-dialogue-png-batch-duration input").fill("240")
            page.locator("#native-dialogue-png-batch-play").click()
            animated = page.locator("#native-dialogue-png-batch-animation img")
            expect(animated.first).to_be_visible(timeout=20000)
            expect(page.get_by_text("240 ms pro Bild nur in der Editor-Vorschau", exact=False)).to_be_visible()
            page.locator("#native-dialogue-png-batch-gallery img").nth(1).click()
            expect(page.get_by_text("Bild 2 von 2 · Batch_Excluded · noch nicht importiert")).to_be_visible(timeout=20000)
            await_batch_frame_color(page, (65, 120, 215))
            page.keyboard.press("Escape")
            # Exchange just the selected staged source, preserving the first
            # imported frame, the excluded upload, and the manual order.
            batch_repair = evidence / "Batch-Repaired.png"
            Image.new("RGBA", (8, 8), (35, 205, 165, 255)).save(batch_repair)
            page.locator("#native-dialogue-png-batch-replacement input[type=file]").set_input_files(
                str(batch_repair))
            page.locator("#native-dialogue-png-batch-replace").click()
            expect(batch_preview).to_have_value(
                re.compile(r"1\. Batch-B\.png → Batch_B\s*2\. Batch-Repaired\.png → Batch_Repaired\s*$"),
                timeout=20000)
            await_batch_gallery_colors(page, [(225, 110, 40), (35, 205, 165)])
            expect(page.get_by_text("Bild 2 von 2 · Batch_Repaired · noch nicht importiert")).to_be_visible(timeout=20000)
            await_batch_frame_color(page, (35, 205, 165))
            expect(image_issues).to_have_value("Keine bildbezogenen Konflikte erkannt", timeout=20000)
            custom_id = page.locator(
                "#native-dialogue-png-batch-id textarea, #native-dialogue-png-batch-id input")
            expect(custom_id).to_have_value("Batch_Repaired", timeout=20000)
            custom_id.fill("CustomEnding")
            page.locator("#native-dialogue-png-batch-set-id").click()
            expect(batch_preview).to_have_value(
                re.compile(r"1\. Batch-B\.png → Batch_B\s*2\. Batch-Repaired\.png → CustomEnding\s*$"),
                timeout=20000)
            expect(page.get_by_text("Bild 2 von 2 · CustomEnding · noch nicht importiert")).to_be_visible(timeout=20000)
            await_batch_gallery_colors(page, [(225, 110, 40), (35, 205, 165)])
            expect(readiness).to_contain_text("Importbereit: 2 PNG-Frame(s)", timeout=20000)
            batch_import.click()
            expect(ending_gallery.locator("img")).to_have_count(6, timeout=20000)
            expect(readiness).to_contain_text("Import blockiert:", timeout=20000)
            expect(readiness).to_contain_text("Frame-ID existiert bereits")
            expect(batch_import).to_be_disabled()
            expect(image_issues).to_have_value(
                re.compile(r"1\. Batch-B\.png:.*2\. Batch-Repaired\.png:", re.S),
                timeout=20000)
            expect(page.locator("#native-dialogue-png-batch-gallery")).to_contain_text("⚠️")
            page.locator("#native-project-export-button").click()
            expect(sequence_link.first).to_be_visible(timeout=20000)
            with page.expect_download() as batch_info:
                sequence_link.first.click()
            batch_file = evidence / "batch-import-project.json"
            batch_info.value.save_as(str(batch_file))
            batch_document = parse_document(batch_file.read_text(encoding="utf-8"))
            batch_raw = batch_file.read_text(encoding="utf-8")
            last_two = dialogue_ending_timeline(batch_raw, first[1], "N")[1][-2:]
            assert last_two == (("5. Batch_B", 4), ("6. CustomEnding", 5))
            assert "Batch_A" not in batch_raw
            assert "Batch_Excluded" not in batch_raw
            assert next(actor for actor in batch_document.actors
                        if actor.id == "SpeakerHarborKeeper").costume == "WitnessCostume"
            # Both staged native IDs now collide with the imported Costume.
            # Resolve the complete import sequence at once, preserving order.
            page.locator("#native-dialogue-png-batch-resolve-ids").click()
            expect(custom_id).to_have_value("CustomEnding_2", timeout=20000)
            expect(batch_preview).to_have_value(
                re.compile(r"1\. Batch-B\.png → Batch_B_2\s*2\. Batch-Repaired\.png → CustomEnding_2\s*$"),
                timeout=20000)
            await_batch_gallery_colors(page, [(225, 110, 40), (35, 205, 165)])
            expect(image_issues).to_have_value("Keine bildbezogenen Konflikte erkannt", timeout=20000)
            expect(readiness).to_contain_text("Importbereit: 2 PNG-Frame(s)", timeout=20000)
            expect(batch_import).to_be_enabled()
            batch_import.click()
            expect(ending_gallery.locator("img")).to_have_count(8, timeout=20000)
            page.locator("#native-project-export-button").click()
            expect(sequence_link.first).to_be_visible(timeout=20000)
            with page.expect_download() as suggested_info:
                sequence_link.first.click()
            suggested_file = evidence / "suggested-id-project.json"
            suggested_info.value.save_as(str(suggested_file))
            suggested_raw = suggested_file.read_text(encoding="utf-8")
            assert dialogue_ending_timeline(suggested_raw, first[1], "N")[1][-2:] == (
                ("7. Batch_B_2", 6), ("8. CustomEnding_2", 7))
            # Append two actual Sprite-Sheet tiles to the edited staged
            # selection, then import/export all four native COST frames.
            sprite_sheet = evidence / "Mouth-Strip.png"
            strip = Image.new("RGBA", (24, 12), (240, 10, 230, 255))
            strip.paste((170, 55, 210, 255), (2, 2, 10, 10))
            strip.paste((55, 205, 115, 255), (14, 2, 22, 10))
            strip.save(sprite_sheet)
            page.locator("#native-dialogue-sprite-sheet input[type=file]").set_input_files(
                str(sprite_sheet))
            page.locator("#native-dialogue-sprite-margin-x input").fill("2")
            page.locator("#native-dialogue-sprite-margin-y input").fill("2")
            page.locator("#native-dialogue-sprite-gap-x input").fill("4")
            sprite_status = page.locator("#native-dialogue-sprite-preview-status")
            expect(sprite_status).to_contain_text("2 von 2 PNG-Frames ausgewählt", timeout=20000)
            expect(sprite_status).to_contain_text("8 × 8 Pixel")
            await_batch_gallery_colors(page, [(170, 55, 210), (55, 205, 115)],
                                       "native-dialogue-sprite-preview-tiles")
            playback_gallery = page.locator("#native-dialogue-sprite-playback-frames")
            await_batch_gallery_colors(page, [(170, 55, 210), (55, 205, 115)],
                                       "native-dialogue-sprite-playback-frames")
            expect(playback_gallery).to_contain_text("1. Bild · Zelle 1")
            expect(page.locator("#native-dialogue-sprite-preview-overlay img")).to_be_visible()
            page.locator("#native-dialogue-sprite-gap-x input").fill("5")
            expect(sprite_status).to_contain_text("teilbar", timeout=20000)
            page.locator("#native-dialogue-sprite-gap-x input").fill("4")
            expect(sprite_status).to_contain_text("8 × 8 Pixel", timeout=20000)
            preview_gallery = page.locator("#native-dialogue-sprite-preview-tiles")
            preview_gallery.locator("img").nth(1).click()
            expect(sprite_status).to_contain_text("1 von 2 PNG-Frames ausgewählt", timeout=20000)
            expect(preview_gallery).to_contain_text("⛔ Überspringen")
            page.keyboard.press("Escape")
            preview_gallery.locator("img").first.click()
            expect(sprite_status).to_contain_text("0 von 2 PNG-Frames ausgewählt", timeout=20000)
            page.keyboard.press("Escape")
            preview_gallery.locator("img").first.click()
            expect(sprite_status).to_contain_text("1 von 2 PNG-Frames ausgewählt", timeout=20000)
            page.keyboard.press("Escape")
            preview_gallery.locator("img").nth(1).click()
            expect(sprite_status).to_contain_text("2 von 2 PNG-Frames ausgewählt", timeout=20000)
            page.keyboard.press("Escape")
            select_option(page, "native-dialogue-sprite-selected", "Position 2: Zelle 2")
            page.locator("#native-dialogue-sprite-move-up").click()
            expect(preview_gallery).to_contain_text("Abspielposition 1", timeout=20000)
            expect(page.locator("#native-dialogue-sprite-selected input")).to_have_value(
                "Position 1: Zelle 2", timeout=20000)
            page.locator("#native-dialogue-sprite-duration input").fill("240")
            page.locator("#native-dialogue-sprite-play").click()
            sheet_gif = page.locator("#native-dialogue-sprite-animation img")
            expect(sheet_gif.first).to_be_visible(timeout=20000)
            expect(page.locator("#native-dialogue-sprite-animation-status")).to_contain_text(
                "2 Sheet-Abspielbilder · 240 ms pro Bild", timeout=20000)
            gif_response = page.request.get(urljoin(page.url, sheet_gif.first.get_attribute("src")))
            assert gif_response.ok
            with Image.open(BytesIO(gif_response.body())) as sheet_preview:
                assert sheet_preview.format == "GIF"
                assert sheet_preview.n_frames == 2
                assert sheet_preview.info["duration"] == 240
                for position, color in enumerate(((55, 205, 115), (170, 55, 210))):
                    sheet_preview.seek(position)
                    assert sheet_preview.convert("RGB").getpixel((4, 4)) == color
            page.locator("#native-dialogue-sprite-duration input").fill("180")
            expect(sheet_gif).to_have_count(0, timeout=20000)
            page.locator("#native-dialogue-sprite-repeat-add").click()
            expect(sprite_status).to_contain_text("3 Abspielbilder", timeout=20000)
            expect(preview_gallery).to_contain_text("2×")
            page.locator("#native-dialogue-sprite-repeat-add").click()
            expect(sprite_status).to_contain_text("4 Abspielbilder", timeout=20000)
            page.locator("#native-dialogue-sprite-repeat-remove").click()
            expect(sprite_status).to_contain_text("3 Abspielbilder", timeout=20000)
            page.locator("#native-dialogue-sprite-play").click()
            expect(sheet_gif.first).to_be_visible(timeout=20000)
            expect(page.locator("#native-dialogue-sprite-animation-status")).to_contain_text(
                "3 Sheet-Abspielbilder · 180 ms pro Bild", timeout=20000)
            repeat_response = page.request.get(urljoin(page.url, sheet_gif.first.get_attribute("src")))
            assert repeat_response.ok
            with Image.open(BytesIO(repeat_response.body())) as repeated_preview:
                assert repeated_preview.format == "GIF"
                assert repeated_preview.n_frames == 2
                durations = []
                for position, color in enumerate(((55, 205, 115), (170, 55, 210))):
                    repeated_preview.seek(position)
                    durations.append(repeated_preview.info["duration"])
                    assert repeated_preview.convert("RGB").getpixel((4, 4)) == color
                assert durations == [360, 180]
            free_order = page.locator(
                "#native-dialogue-sprite-timeline textarea, "
                "#native-dialogue-sprite-timeline input")
            free_order.fill("2,3,1")
            expect(sprite_status).to_contain_text("außerhalb des Rasters", timeout=20000)
            expect(sheet_gif).to_have_count(0, timeout=20000)
            free_order.fill("2,1,2")
            expect(sprite_status).to_contain_text("3 Abspielbilder · Freie Abspielsequenz",
                                                   timeout=20000)
            expect(preview_gallery).to_contain_text("Abspielpositionen 1, 3")
            page.locator("#native-dialogue-sprite-play").click()
            expect(sheet_gif.first).to_be_visible(timeout=20000)
            free_response = page.request.get(urljoin(page.url, sheet_gif.first.get_attribute("src")))
            assert free_response.ok
            with Image.open(BytesIO(free_response.body())) as freely_ordered:
                assert freely_ordered.n_frames == 3
                for position, color in enumerate(((55, 205, 115), (170, 55, 210),
                                                  (55, 205, 115))):
                    freely_ordered.seek(position)
                    assert freely_ordered.info["duration"] == 180
                    assert freely_ordered.convert("RGB").getpixel((4, 4)) == color
            page.locator("#native-dialogue-sprite-reset-timeline").click()
            expect(free_order).to_have_value("", timeout=20000)
            expect(sprite_status).to_contain_text("3 Abspielbilder", timeout=20000)
            page.locator("#native-dialogue-sprite-repeat-remove").click()
            expect(sprite_status).to_contain_text("2 Abspielbilder", timeout=20000)
            select_option(page, "native-dialogue-sprite-position",
                          "2 · nach Bild 2 (Zelle 1)")
            page.locator("#native-dialogue-sprite-insert").click()
            expect(free_order).to_have_value("2,1,2", timeout=20000)
            expect(sprite_status).to_contain_text("3 Abspielbilder · Freie Abspielsequenz",
                                                   timeout=20000)
            await_batch_gallery_colors(page, [(55, 205, 115), (170, 55, 210),
                                              (55, 205, 115)],
                                       "native-dialogue-sprite-playback-frames")
            expect(playback_gallery).to_contain_text("3. Bild · Zelle 2")
            playback_gallery.locator("img").nth(2).click()
            expect(page.locator("#native-dialogue-sprite-position input")).to_have_value(
                "3 · nach Bild 3 (Zelle 2)", timeout=20000)
            page.keyboard.press("Escape")
            page.locator("#native-dialogue-sprite-remove-position").click()
            expect(free_order).to_have_value("2,1", timeout=20000)
            await_batch_gallery_colors(page, [(55, 205, 115), (170, 55, 210)],
                                       "native-dialogue-sprite-playback-frames")
            page.locator("#native-dialogue-sprite-insert").click()
            expect(free_order).to_have_value("2,1,2", timeout=20000)
            playback_gallery.locator("img").nth(1).click()
            expect(page.locator("#native-dialogue-sprite-position input")).to_have_value(
                "2 · nach Bild 2 (Zelle 1)", timeout=20000)
            page.keyboard.press("Escape")
            page.locator("#native-dialogue-sprite-move-position-up").click()
            expect(free_order).to_have_value("1,2,2", timeout=20000)
            await_batch_gallery_colors(page, [(170, 55, 210), (55, 205, 115),
                                              (55, 205, 115)],
                                       "native-dialogue-sprite-playback-frames")
            playback_gallery.locator("img").first.click()
            expect(page.locator("#native-dialogue-sprite-position input")).to_have_value(
                "1 · nach Bild 1 (Zelle 1)", timeout=20000)
            page.keyboard.press("Escape")
            page.locator("#native-dialogue-sprite-move-position-down").click()
            expect(free_order).to_have_value("2,1,2", timeout=20000)
            await_batch_gallery_colors(page, [(55, 205, 115), (170, 55, 210),
                                              (55, 205, 115)],
                                       "native-dialogue-sprite-playback-frames")
            playback_gallery.locator("img").nth(1).click()
            expect(page.locator("#native-dialogue-sprite-block-end input")).to_have_value(
                "2 · nach Bild 2 (Zelle 1)", timeout=20000)
            page.keyboard.press("Escape")
            select_option(page, "native-dialogue-sprite-block-end",
                          "3 · nach Bild 3 (Zelle 2)")
            page.locator("#native-dialogue-sprite-move-block-up").click()
            expect(free_order).to_have_value("1,2,2", timeout=20000)
            await_batch_gallery_colors(page, [(170, 55, 210), (55, 205, 115),
                                              (55, 205, 115)],
                                       "native-dialogue-sprite-playback-frames")
            playback_gallery.locator("img").first.click()
            page.keyboard.press("Escape")
            select_option(page, "native-dialogue-sprite-block-end",
                          "2 · nach Bild 2 (Zelle 2)")
            page.locator("#native-dialogue-sprite-move-block-down").click()
            expect(free_order).to_have_value("2,1,2", timeout=20000)
            await_batch_gallery_colors(page, [(55, 205, 115), (170, 55, 210),
                                              (55, 205, 115)],
                                       "native-dialogue-sprite-playback-frames")
            playback_gallery.locator("img").first.click()
            page.keyboard.press("Escape")
            select_option(page, "native-dialogue-sprite-block-end",
                          "2 · nach Bild 2 (Zelle 1)")
            expect(page.locator("#native-dialogue-sprite-copy-destination input")).to_have_value(
                "3 · nach Bild 3 (Zelle 2)", timeout=20000)
            page.locator("#native-dialogue-sprite-copy-block").click()
            expect(free_order).to_have_value("2,1,2,2,1", timeout=20000)
            expect(sprite_status).to_contain_text("5 Abspielbilder", timeout=20000)
            await_batch_gallery_colors(page, [(55, 205, 115), (170, 55, 210),
                                              (55, 205, 115), (55, 205, 115),
                                              (170, 55, 210)],
                                       "native-dialogue-sprite-playback-frames")
            playback_gallery.locator("img").nth(3).click()
            page.keyboard.press("Escape")
            select_option(page, "native-dialogue-sprite-block-end",
                          "5 · nach Bild 5 (Zelle 1)")
            page.locator("#native-dialogue-sprite-remove-block").click()
            expect(free_order).to_have_value("2,1,2", timeout=20000)
            expect(sprite_status).to_contain_text("3 Abspielbilder", timeout=20000)
            await_batch_gallery_colors(page, [(55, 205, 115), (170, 55, 210),
                                              (55, 205, 115)],
                                       "native-dialogue-sprite-playback-frames")
            playback_gallery.locator("img").first.click()
            page.keyboard.press("Escape")
            select_option(page, "native-dialogue-sprite-block-end",
                          "2 · nach Bild 2 (Zelle 1)")
            expect(page.locator("#native-dialogue-sprite-copy-destination input")).to_have_value(
                "3 · nach Bild 3 (Zelle 2)", timeout=20000)
            page.keyboard.press("Escape")
            page.locator("#native-dialogue-sprite-relocate-block").click()
            expect(free_order).to_have_value("2,2,1", timeout=20000)
            await_batch_gallery_colors(page, [(55, 205, 115), (55, 205, 115),
                                              (170, 55, 210)],
                                       "native-dialogue-sprite-playback-frames")
            playback_gallery.locator("img").first.click()
            page.keyboard.press("Escape")
            select_option(page, "native-dialogue-sprite-block-end",
                          "2 · nach Bild 2 (Zelle 2)")
            expect(page.locator("#native-dialogue-sprite-copy-destination input")).to_have_value(
                "3 · nach Bild 3 (Zelle 1)", timeout=20000)
            page.keyboard.press("Escape")
            page.locator("#native-dialogue-sprite-block-repetitions input").fill("2")
            page.locator("#native-dialogue-sprite-repeat-block").click()
            expect(free_order).to_have_value("2,2,1,2,2,2,2", timeout=20000)
            expect(sprite_status).to_contain_text("7 Abspielbilder", timeout=20000)
            await_batch_gallery_colors(page, [(55, 205, 115), (55, 205, 115),
                                              (170, 55, 210), (55, 205, 115),
                                              (55, 205, 115), (55, 205, 115),
                                              (55, 205, 115)],
                                       "native-dialogue-sprite-playback-frames")
            undo_button = page.locator("#native-dialogue-sprite-undo")
            expect(undo_button).to_be_enabled(timeout=20000)
            undo_button.click()
            expect(free_order).to_have_value("2,2,1", timeout=20000)
            expect(undo_button).to_be_enabled(timeout=20000)
            redo_button = page.locator("#native-dialogue-sprite-redo")
            expect(redo_button).to_be_enabled(timeout=20000)
            redo_button.click()
            expect(free_order).to_have_value("2,2,1,2,2,2,2", timeout=20000)
            expect(redo_button).to_be_disabled(timeout=20000)
            expect(undo_button).to_be_enabled(timeout=20000)
            await_batch_gallery_colors(page, [(55, 205, 115), (55, 205, 115),
                                              (170, 55, 210), (55, 205, 115),
                                              (55, 205, 115), (55, 205, 115),
                                              (55, 205, 115)],
                                       "native-dialogue-sprite-playback-frames")
            undo_button.click()
            expect(free_order).to_have_value("2,2,1", timeout=20000)
            expect(redo_button).to_be_enabled(timeout=20000)
            await_batch_gallery_colors(page, [(55, 205, 115), (55, 205, 115),
                                              (170, 55, 210)],
                                       "native-dialogue-sprite-playback-frames")
            playback_gallery.locator("img").first.click()
            page.keyboard.press("Escape")
            select_option(page, "native-dialogue-sprite-block-end",
                          "2 · nach Bild 2 (Zelle 2)")
            page.keyboard.press("Escape")
            page.locator("#native-dialogue-sprite-repeat-block").click()
            expect(free_order).to_have_value("2,2,1,2,2,2,2", timeout=20000)
            expect(redo_button).to_be_disabled(timeout=20000)
            playback_gallery.locator("img").first.click()
            page.keyboard.press("Escape")
            expect(page.locator("#native-dialogue-sprite-copy-destination input")).to_have_value(
                "7 · nach Bild 7 (Zelle 2)", timeout=20000)
            page.locator("#native-dialogue-sprite-copy-block").click()
            expect(free_order).to_have_value("2,2,1,2,2,2,2,2", timeout=20000)
            expect(page.locator("#native-dialogue-sprite-history-status")).to_contain_text(
                "Schritt", timeout=20000)
            history_picker = page.locator(
                "#native-dialogue-sprite-history-position input[role='combobox']")
            expect(history_picker).to_be_enabled(timeout=20000)
            history_picker.click()
            page.get_by_role(
                "option", name=re.compile(r"Auf 7 Bilder erweitert.*2,2,1,2,2,2,2")
            ).last.click(timeout=12000)
            expect(free_order).to_have_value("2,2,1,2,2,2,2", timeout=20000)
            expect(redo_button).to_be_enabled(timeout=20000)
            history_picker.click()
            page.get_by_role(
                "option", name=re.compile(r"Auf 8 Bilder erweitert.*2,2,1,2,2,2,2,2")
            ).click(timeout=12000)
            expect(free_order).to_have_value("2,2,1,2,2,2,2,2", timeout=20000)
            undo_button.click()
            expect(free_order).to_have_value("2,2,1,2,2,2,2", timeout=20000)
            undo_button.click()
            expect(free_order).to_have_value("2,2,1", timeout=20000)
            redo_button.click()
            expect(free_order).to_have_value("2,2,1,2,2,2,2", timeout=20000)
            redo_button.click()
            expect(free_order).to_have_value("2,2,1,2,2,2,2,2", timeout=20000)
            undo_button.click()
            expect(free_order).to_have_value("2,2,1,2,2,2,2", timeout=20000)
            page.locator("#native-dialogue-sprite-add").click()
            expect(batch_preview).to_have_value(
                re.compile(r"1\. Batch-B\.png → Batch_B_2.*"
                           r"2\. Batch-Repaired\.png → CustomEnding_2.*"
                           r"3\. Mouth-Strip_r1_c2\.png → Mouth_Strip_r1_c2.*"
                           r"4\. Mouth-Strip_r1_c2_repeat2\.png → Mouth_Strip_r1_c2_repeat2.*"
                           r"5\. Mouth-Strip_r1_c1\.png → Mouth_Strip_r1_c1.*"
                           r"6\. Mouth-Strip_r1_c2_repeat3\.png → Mouth_Strip_r1_c2_repeat3.*"
                           r"7\. Mouth-Strip_r1_c2_repeat4\.png → Mouth_Strip_r1_c2_repeat4.*"
                           r"8\. Mouth-Strip_r1_c2_repeat5\.png → Mouth_Strip_r1_c2_repeat5.*"
                           r"9\. Mouth-Strip_r1_c2_repeat6\.png → Mouth_Strip_r1_c2_repeat6\s*$", re.S),
                timeout=20000)
            await_batch_gallery_colors(page, [(225, 110, 40), (35, 205, 165),
                                              (55, 205, 115), (55, 205, 115),
                                              (170, 55, 210), (55, 205, 115),
                                              (55, 205, 115), (55, 205, 115),
                                              (55, 205, 115)])
            expect(readiness).to_contain_text("Import blockiert:", timeout=20000)
            page.locator("#native-dialogue-png-batch-resolve-ids").click()
            expect(readiness).to_contain_text("Importbereit: 9 PNG-Frame(s)", timeout=20000)
            batch_import.click()
            expect(ending_gallery.locator("img")).to_have_count(17, timeout=20000)
            page.locator("#native-project-export-button").click()
            expect(sequence_link.first).to_be_visible(timeout=20000)
            with page.expect_download() as sprite_info:
                sequence_link.first.click()
            sprite_file = evidence / "sprite-sheet-project.json"
            sprite_info.value.save_as(str(sprite_file))
            sprite_raw = sprite_file.read_text(encoding="utf-8")
            assert dialogue_ending_timeline(sprite_raw, first[1], "N")[1][-9:] == (
                ("9. Batch_B_2_2", 8), ("10. CustomEnding_2_2", 9),
                ("11. Mouth_Strip_r1_c2", 10),
                ("12. Mouth_Strip_r1_c2_repeat2", 11),
                ("13. Mouth_Strip_r1_c1", 12),
                ("14. Mouth_Strip_r1_c2_repeat3", 13),
                ("15. Mouth_Strip_r1_c2_repeat4", 14),
                ("16. Mouth_Strip_r1_c2_repeat5", 15),
                ("17. Mouth_Strip_r1_c2_repeat6", 16))
            (evidence / "result.json").write_text(json.dumps({
                "passed": True, "first": first[1], "second": second[1],
                "reimported_second_pose": "Speak", "independent_line_sequences": True,
                "independent_direction_sequences": True,
                "graphical_line_timeline": True,
                "native_dialogue_phases": True,
                "native_ending_gesture": True,
                "direct_png_ending_timeline": True,
                "direct_png_file_import": True,
                "isolated_shared_speaker_costume": True,
                "ordered_atomic_png_batch": True,
                "reordered_png_batch": True,
                "removed_staged_png_without_reupload": True,
                "restored_staged_png_without_reupload": True,
                "staged_png_pixel_thumbnail_order": True,
                "staged_png_animated_preview": True,
                "staged_png_frame_navigation": True,
                "staged_png_gallery_direct_selection": True,
                "staged_png_import_preflight": True,
                "staged_png_per_image_conflict_labels": True,
                "replaced_selected_staged_png_without_reupload": True,
                "edited_staged_native_frame_id_without_file_rename": True,
                "suggested_conflict_free_native_frame_ids": True,
                "resolved_all_staged_native_frame_id_conflicts": True,
                "imported_sprite_sheet_as_native_costume_frames": True,
                "previewed_sprite_sheet_cuts_before_staging": True,
                "selected_sprite_sheet_cells_before_staging": True,
                "reordered_sprite_sheet_cells_before_staging": True,
                "animated_selected_sprite_sheet_before_staging": True,
                "repeated_sprite_sheet_cell_before_native_import": True,
                "freely_positioned_sprite_sheet_repetitions": True,
            }, indent=2) + "\n", encoding="utf-8")
            print("Real Chromium Gradio dialogue-pose editor roundtrip passed")
        except Exception:
            page.screenshot(path=str(evidence / "failure.png"), full_page=True)
            for elem_id in ("native-project-file", "native-dialogue-line",
                            "native-dialogue-pose", "native-dialogue-animation",
                            "native-project-export-file"):
                node = page.locator("#" + elem_id)
                if node.count():
                    print(elem_id + ": " + node.first.evaluate(
                        "(el) => el.outerHTML.slice(0, 3000)"))
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
