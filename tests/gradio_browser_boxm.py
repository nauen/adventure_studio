"""Direct real-Chromium acceptance for native BOXM route authoring."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from adventure_studio.scumm_assets import destination_fixture, scrolling_fixture
from adventure_studio.scumm_project import GameDocument, canonical_json, parse_document


def main() -> None:
    evidence = Path(os.environ.get("ADVENTURE_STUDIO_BOXM_EVIDENCE",
                                  "/tmp/studio-boxm-evidence"))
    evidence.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        fixture = Path(temporary) / "boxm-project.json"
        fixture.write_text(
            canonical_json(GameDocument("boxm_browser",
                                        (scrolling_fixture(), destination_fixture()))),
            encoding="utf-8")
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
                report = page.locator(
                    "#native-project-report textarea, #native-project-report input")
                expect(report).to_have_value("Natives Projekt geladen und validiert",
                                             timeout=30000)
                corners = page.locator(
                    "#native-walkbox-corners textarea, #native-walkbox-corners input")
                corners.fill("0,70; 110,70; 110,150; 0,150")
                page.locator("#native-walkbox-add").click()
                expect(report).to_have_value("Walkbox 1 für Harbor gespeichert und validiert; BOXD wird beim Export erzeugt. Für eine dauerhafte Datei das native Projekt-JSON exportieren.",
                                             timeout=30000)
                page.locator("#native-walkbox-index input").fill("2")
                corners.fill("110,70; 639,70; 639,150; 110,150")
                page.locator("#native-walkbox-add").click()
                expect(report).to_have_value("Walkbox 2 für Harbor gespeichert und validiert; BOXD wird beim Export erzeugt. Für eine dauerhafte Datei das native Projekt-JSON exportieren.",
                                             timeout=30000)
                route_input = page.locator(
                    "#native-box-routes-connections textarea, #native-box-routes-connections input")
                route_input.fill("1-2")
                page.locator("#native-box-routes-add").click()
                expect(report).to_have_value(
                    "BOXM-Wege für Harbor gespeichert; native Next-Hop-Matrix wird beim Export erzeugt. Für dauerhafte Sicherung das Projekt-JSON exportieren.",
                    timeout=30000)
                page.locator("#native-project-export-button").click()
                link = page.locator("#native-project-export-file a[download]")
                expect(link.first).to_be_visible(timeout=30000)
                with page.expect_download() as downloading:
                    link.first.click()
                saved = evidence / "authored-boxm-project.json"
                downloading.value.save_as(str(saved))
                room = next(item for item in parse_document(saved.read_text()).rooms
                            if item.name == "Harbor")
                assert len(room.walkboxes) == 2
                assert room.box_routes[1][2] == 2
                assert room.box_routes[2][1] == 1
                page.screenshot(path=str(evidence / "authored-boxm.png"), full_page=True)
                (evidence / "result.json").write_text(
                    json.dumps({"boxm_studio_roundtrip": True,
                                "routes": [list(row) for row in room.box_routes]},
                               sort_keys=True, indent=2) + "\n", encoding="utf-8")
                print("Native BOXM Studio click-path and JSON roundtrip passed")
            except Exception:
                if not page.is_closed():
                    page.screenshot(path=str(evidence / "failure.png"), full_page=True)
                raise
            finally:
                browser.close()


if __name__ == "__main__":
    main()
