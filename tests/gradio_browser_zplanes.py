"""Real Chromium authoring proof for two ZPxx PNG masks and walkbox layer selection."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import expect, sync_playwright

from adventure_studio.scumm_assets import destination_fixture
from adventure_studio.scumm_project import GameDocument, canonical_json, parse_document
from adventure_studio.scumm_room_fixture import native_room


def main() -> None:
    evidence = Path(os.environ.get("ADVENTURE_STUDIO_ZPLANES_EVIDENCE",
                                  "/tmp/studio-zplanes-evidence"))
    evidence.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        room = native_room(occlusion=False)
        width, height = room.geometry.room_width, room.geometry.room_height
        fixture = root / "project.json"
        fixture.write_text(canonical_json(GameDocument("two_zplanes", (
            room, destination_fixture()))), encoding="utf-8")
        first, second = root / "first.png", root / "second.png"
        Image.new("L", (width, height), color=0).save(first)
        mask = Image.new("L", (width, height), color=0)
        for y in range(60, 110):
            for x in range(width // 2 + 1, width):
                mask.putpixel((x, y), 255)
        mask.save(second)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="chrome", headless=True,
                                                 args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1440, "height": 900},
                                    accept_downloads=True)
            try:
                page.goto("http://127.0.0.1:7860/", wait_until="domcontentloaded",
                          timeout=30000)
                page.get_by_role("tab", name="Native Interaktionsabläufe").click()
                page.locator("#native-project-file input[type=file]").set_input_files(str(fixture))
                report = page.locator("#native-project-report textarea, #native-project-report input")
                expect(report).to_have_value("Natives Projekt geladen und validiert",
                                             timeout=30000)
                for index, image in ((1, first), (2, second)):
                    if index > 1:
                        # Gradio replaces the dropzone with a file row after the first upload.
                        # Clear the first selection before opening the second file chooser.
                        page.locator("#native-zplane-file").locator("button").last.click()
                        expect(page.locator("#native-zplane-file")).to_contain_text("Click to Upload")
                    page.locator("#native-zplane-index input").fill(str(index))
                    with page.expect_file_chooser() as file_chooser:
                        page.locator("#native-zplane-file").click()
                    file_chooser.value.set_files(str(image))
                    page.locator("#native-zplane-add").click()
                    expect(report).to_have_value(re.compile(fr"Z-Ebene {index}.*gespeichert"),
                                                 timeout=30000)
                page.locator("#native-zplane-box-index input").fill("2")
                page.locator("#native-zplane-box-layer input").fill("2")
                page.locator("#native-zplane-box-add").click()
                expect(report).to_have_value(re.compile(r"Walkbox 2 verwendet Z-Ebene 2"),
                                             timeout=30000)
                page.locator("#native-project-export-button").click()
                link = page.locator("#native-project-export-file a[download]")
                expect(link.first).to_be_visible(timeout=30000)
                with page.expect_download() as downloading:
                    link.first.click()
                saved = evidence / "authored-two-zplanes.json"
                downloading.value.save_as(str(saved))
                exported = next(item for item in parse_document(saved.read_text()).rooms
                                if item.name == "Harbor")
                assert len(exported.zplanes) == 2
                assert exported.walkboxes[1].mask == 2
                assert sum(exported.zplanes[0].pixels) == 0
                assert sum(exported.zplanes[1].pixels) > 0
                assert exported.box_routes == room.box_routes
                page.screenshot(path=str(evidence / "authored-two-zplanes.png"),
                                full_page=True)
                (evidence / "result.json").write_text(json.dumps({
                    "studio_two_zplanes": True, "walkbox_zplane": 2,
                    "box_routes_preserved": True}, indent=2) + "\n", encoding="utf-8")
                print("Two Z-plane PNGs and native BOXD layer selected in real Chrome")
            except Exception:
                if not page.is_closed():
                    page.screenshot(path=str(evidence / "failure.png"), full_page=True)
                raise
            finally:
                browser.close()


if __name__ == "__main__":
    main()
