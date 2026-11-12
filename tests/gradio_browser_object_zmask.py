"""Real Chrome proof: author an object-local PNG Z-mask and export native JSON."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import expect, sync_playwright

from adventure_studio.scumm_assets import destination_fixture, scrolling_fixture
from adventure_studio.scumm_project import GameDocument, canonical_json, parse_document


def main() -> None:
    evidence = Path(os.environ.get("ADVENTURE_STUDIO_OBJECT_ZMASK_EVIDENCE",
                                  "/tmp/studio-object-zmask-evidence"))
    evidence.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        room = scrolling_fixture()
        fixture = root / "project.json"
        fixture.write_text(canonical_json(GameDocument("object_zmask", (
            room, destination_fixture()))), encoding="utf-8")
        png = root / "door-zmask.png"
        Image.new("L", (16, 16), 255).save(png)
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
                page.locator("#native-object-zmask-id textarea, #native-object-zmask-id input").fill("Door")
                with page.expect_file_chooser() as chooser:
                    page.locator("#native-object-zmask-file").click()
                chooser.value.set_files(str(png))
                page.locator("#native-object-zmask-add").click()
                expect(report).to_have_value(re.compile(r"Objekt-Z-Maske für Door gespeichert"),
                                             timeout=30000)
                page.locator("#native-project-export-button").click()
                link = page.locator("#native-project-export-file a[download]")
                expect(link.first).to_be_visible(timeout=30000)
                with page.expect_download() as downloading:
                    link.first.click()
                saved = evidence / "authored-object-zmask.json"
                downloading.value.save_as(str(saved))
                exported = parse_document(saved.read_text())
                harbor = next(room for room in exported.rooms if room.name == "Harbor")
                door = next(obj for obj in harbor.hotspots if obj.id == "Door")
                assert len(door.object_zmask_pixels) == 256
                assert sum(door.object_zmask_pixels) == 256
                assert next(obj for obj in harbor.hotspots if obj.id == "Key").object_zmask_pixels is None
                page.screenshot(path=str(evidence / "authored-object-zmask.png"), full_page=True)
                (evidence / "result.json").write_text(
                    json.dumps({"chrome_object_zmask_authoring": True,
                                "object": "Door", "mask_pixels": 256}, indent=2) + "\n",
                    encoding="utf-8")
                print("Studio object Z-mask authoring → native JSON passed in real Chromium")
            except Exception:
                if not page.is_closed():
                    page.screenshot(path=str(evidence / "failure.png"), full_page=True)
                raise
            finally:
                browser.close()


if __name__ == "__main__":
    main()
