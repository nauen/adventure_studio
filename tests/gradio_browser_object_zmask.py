"""Real Chromium proof for authoring an object-image IM01 Z-mask."""

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
        fixture.write_text(canonical_json(GameDocument(
            "object_zmask_browser", (room, destination_fixture()))), encoding="utf-8")
        mask = root / "door-mask.png"
        Image.new("L", (16, 16), 255).save(mask)
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
                selection = page.locator("#native-hotspot input[role=\"combobox\"]")
                selection.click()
                selection.fill("Door")
                page.get_by_role("option", name="Door", exact=True).click(timeout=12000)
                with page.expect_file_chooser() as chooser:
                    page.locator("#native-object-zplane-file").click()
                chooser.value.set_files(str(mask))
                page.locator("#native-object-zplane-add").click()
                expect(report).to_have_value(re.compile(r"Objekt-Z-Maske für Door importiert"),
                                             timeout=30000)
                # R07.2: prove the first mask survives project export and
                # reload, then author the second mask in a fresh editor session.
                page.locator("#native-project-export-button").click()
                first_link = page.locator("#native-project-export-file a[download]")
                expect(first_link.first).to_be_visible(timeout=30000)
                with page.expect_download() as first_download:
                    first_link.first.click()
                first_saved = evidence / "first-state-object-zmask.json"
                first_download.value.save_as(str(first_saved))
                first_project = parse_document(first_saved.read_text())
                first_object = next(h for room in first_project.rooms if room.name == "Harbor"
                                    for h in room.hotspots if h.id == "Door")
                assert first_object.object_zplane_pixels == bytes([1]) * 256

                page.goto("http://127.0.0.1:7860/", wait_until="domcontentloaded",
                          timeout=30000)
                page.get_by_role("tab", name="Native Interaktionsabläufe").click()
                page.locator("#native-project-file input[type=file]").set_input_files(str(first_saved))
                report = page.locator("#native-project-report textarea, #native-project-report input")
                expect(report).to_have_value("Natives Projekt geladen und validiert", timeout=30000)
                selection = page.locator("#native-hotspot input[role=combobox]")
                selection.click()
                selection.fill("Door")
                page.get_by_role("option", name="Door", exact=True).click(timeout=12000)
                open_mask = root / "door-open-mask.png"
                Image.new("L", (16, 16), 0).save(open_mask)
                state_selection = page.locator("#native-object-zplane-state input[role=combobox]")
                state_selection.click()
                page.get_by_role("option", name="Offenes Bild (2)", exact=True).click(timeout=12000)
                expect(state_selection).to_have_value("Offenes Bild (2)", timeout=12000)
                with page.expect_file_chooser() as second_chooser:
                    page.locator("#native-object-zplane-file").click()
                second_chooser.value.set_files(str(open_mask))
                page.locator("#native-object-zplane-add").click()
                expect(report).to_have_value(
                    re.compile(r"Objekt-Z-Maske für Door, Bildzustand 2 importiert"),
                    timeout=30000,
                )
                page.locator("#native-project-export-button").click()
                link = page.locator("#native-project-export-file a[download]")
                expect(link.first).to_be_visible(timeout=30000)
                with page.expect_download() as downloading:
                    link.first.click()
                saved = evidence / "authored-object-zmask.json"
                downloading.value.save_as(str(saved))
                parsed = parse_document(saved.read_text())
                obj = next(h for room in parsed.rooms if room.name == "Harbor"
                           for h in room.hotspots if h.id == "Door")
                assert obj.object_zplane_pixels == bytes([1]) * 256
                assert obj.open_object_zplane_pixels == bytes(256)
                # R07.3: a fresh editor session must reimport both existing
                # image-state masks and allow a new independently chosen IM01
                # ZP02 through the real upload control.
                page.goto("http://127.0.0.1:7860/", wait_until="domcontentloaded",
                          timeout=30000)
                page.get_by_role("tab", name="Native Interaktionsabläufe").click()
                page.locator("#native-project-file input[type=file]").set_input_files(str(saved))
                report = page.locator("#native-project-report textarea, #native-project-report input")
                expect(report).to_have_value("Natives Projekt geladen und validiert",
                                             timeout=30000)
                selection = page.locator("#native-hotspot input[role=combobox]")
                selection.click()
                selection.fill("Door")
                page.get_by_role("option", name="Door", exact=True).click(timeout=12000)
                state_selection = page.locator("#native-object-zplane-state input[role=combobox]")
                expect(state_selection).to_have_value("Grundbild (1)", timeout=12000)
                layer_selection = page.locator("#native-object-zplane-layer input[role=combobox]")
                layer_selection.click()
                page.get_by_role("option", name="ZP02 (2)", exact=True).click(timeout=12000)
                expect(layer_selection).to_have_value("ZP02 (2)",
                                                      timeout=12000)
                with page.expect_file_chooser() as zp02_chooser:
                    page.locator("#native-object-zplane-file").click()
                zp02_chooser.value.set_files(str(mask))
                page.locator("#native-object-zplane-add").click()
                expect(report).to_have_value(re.compile(r"IM01 ZP02 importiert"),
                                             timeout=30000)
                page.locator("#native-project-export-button").click()
                final_link = page.locator("#native-project-export-file a[download]")
                expect(final_link.first).to_be_visible(timeout=30000)
                with page.expect_download() as zp02_download:
                    final_link.first.click()
                zp02_saved = evidence / "authored-im01-two-zplanes.json"
                zp02_download.value.save_as(str(zp02_saved))
                merged = next(h for r in parse_document(zp02_saved.read_text()).rooms
                              if r.name == "Harbor" for h in r.hotspots if h.id == "Door")
                assert merged.object_zplane_pixels == bytes([1]) * 256
                assert merged.object_zplane2_pixels == bytes([1]) * 256
                assert merged.open_object_zplane_pixels == bytes(256)
                # R07.4: import the two-layer IM01 project in another real
                # editor session, then independently author open-state IM02 ZP02.
                page.goto("http://127.0.0.1:7860/", wait_until="domcontentloaded",
                          timeout=30000)
                page.get_by_role("tab", name="Native Interaktionsabläufe").click()
                page.locator("#native-project-file input[type=file]").set_input_files(str(zp02_saved))
                report = page.locator("#native-project-report textarea, #native-project-report input")
                expect(report).to_have_value("Natives Projekt geladen und validiert",
                                             timeout=30000)
                selection = page.locator("#native-hotspot input[role=combobox]")
                selection.click()
                selection.fill("Door")
                page.get_by_role("option", name="Door", exact=True).click(timeout=12000)
                state_selection = page.locator("#native-object-zplane-state input[role=combobox]")
                state_selection.click()
                page.get_by_role("option", name="Offenes Bild (2)", exact=True).click(timeout=12000)
                expect(state_selection).to_have_value("Offenes Bild (2)", timeout=12000)
                layer_selection = page.locator("#native-object-zplane-layer input[role=combobox]")
                layer_selection.click()
                page.get_by_role("option", name="ZP02 (2)", exact=True).click(timeout=12000)
                expect(layer_selection).to_have_value("ZP02 (2)", timeout=12000)
                with page.expect_file_chooser() as im02_chooser:
                    page.locator("#native-object-zplane-file").click()
                im02_chooser.value.set_files(str(mask))
                page.locator("#native-object-zplane-add").click()
                expect(report).to_have_value(re.compile(r"IM02 ZP02 importiert"), timeout=30000)
                page.locator("#native-project-export-button").click()
                im02_link = page.locator("#native-project-export-file a[download]")
                expect(im02_link.first).to_be_visible(timeout=30000)
                with page.expect_download() as im02_dl:
                    im02_link.first.click()
                im02_saved = evidence / "authored-im02-zp02.json"
                im02_dl.value.save_as(str(im02_saved))
                im02_obj = next(h for r in parse_document(im02_saved.read_text()).rooms
                                if r.name == "Harbor" for h in r.hotspots if h.id == "Door")
                assert im02_obj.object_zplane_pixels == bytes([1]) * 256
                assert im02_obj.object_zplane2_pixels == bytes([1]) * 256
                assert im02_obj.open_object_zplane_pixels == bytes(256)
                assert im02_obj.open_object_zplane2_pixels == bytes([1]) * 256

                # R07.5: preserve the two image states after a full reimport,
                # then author a third independent IM01 Z-plane in Chrome.
                page.goto("http://127.0.0.1:7860/", wait_until="domcontentloaded",
                          timeout=30000)
                page.get_by_role("tab", name="Native Interaktionsabläufe").click()
                page.locator("#native-project-file input[type=file]").set_input_files(str(im02_saved))
                report = page.locator("#native-project-report textarea, #native-project-report input")
                expect(report).to_have_value("Natives Projekt geladen und validiert", timeout=30000)
                selection = page.locator("#native-hotspot input[role=combobox]")
                selection.click()
                selection.fill("Door")
                page.get_by_role("option", name="Door", exact=True).click(timeout=12000)
                state_selection = page.locator("#native-object-zplane-state input[role=combobox]")
                expect(state_selection).to_have_value("Grundbild (1)", timeout=12000)
                layer_selection = page.locator("#native-object-zplane-layer input[role=combobox]")
                layer_selection.click()
                page.get_by_role("option", name="ZP03 (3)", exact=True).click(timeout=12000)
                expect(layer_selection).to_have_value("ZP03 (3)", timeout=12000)
                with page.expect_file_chooser() as zp03_chooser:
                    page.locator("#native-object-zplane-file").click()
                zp03_chooser.value.set_files(str(mask))
                page.locator("#native-object-zplane-add").click()
                expect(report).to_have_value(re.compile(r"IM01 ZP03 importiert"), timeout=30000)
                page.locator("#native-project-export-button").click()
                link = page.locator("#native-project-export-file a[download]")
                expect(link.first).to_be_visible(timeout=30000)
                with page.expect_download() as exported:
                    link.first.click()
                zp03_saved = evidence / "authored-im01-zp03.json"
                exported.value.save_as(str(zp03_saved))
                result = next(h for r in parse_document(zp03_saved.read_text()).rooms
                              if r.name == "Harbor" for h in r.hotspots if h.id == "Door")
                assert result.object_zplane_pixels == bytes([1]) * 256
                assert result.object_zplane2_pixels == bytes([1]) * 256
                assert result.object_zplane3_pixels == bytes([1]) * 256
                assert result.open_object_zplane_pixels == bytes(256)
                assert result.open_object_zplane2_pixels == bytes([1]) * 256
                # R07.6: reimport five independent masks, author IM02/ZP03 in Chrome.
                page.goto("http://127.0.0.1:7860/", wait_until="domcontentloaded",
                          timeout=30000)
                page.get_by_role("tab", name="Native Interaktionsabläufe").click()
                page.locator("#native-project-file input[type=file]").set_input_files(str(zp03_saved))
                report = page.locator("#native-project-report textarea, #native-project-report input")
                expect(report).to_have_value("Natives Projekt geladen und validiert", timeout=30000)
                selection = page.locator("#native-hotspot input[role=combobox]")
                selection.click()
                selection.fill("Door")
                page.get_by_role("option", name="Door", exact=True).click(timeout=12000)
                state_selection = page.locator("#native-object-zplane-state input[role=combobox]")
                state_selection.click()
                page.get_by_role("option", name="Offenes Bild (2)", exact=True).click(timeout=12000)
                layer_selection = page.locator("#native-object-zplane-layer input[role=combobox]")
                layer_selection.click()
                page.get_by_role("option", name="ZP03 (3)", exact=True).click(timeout=12000)
                with page.expect_file_chooser() as chooser:
                    page.locator("#native-object-zplane-file").click()
                chooser.value.set_files(str(mask))
                page.locator("#native-object-zplane-add").click()
                expect(report).to_have_value(re.compile(r"IM02 ZP03 importiert"), timeout=30000)
                page.locator("#native-project-export-button").click()
                link = page.locator("#native-project-export-file a[download]")
                expect(link.first).to_be_visible(timeout=30000)
                with page.expect_download() as exported:
                    link.first.click()
                final_file = evidence / "authored-im02-zp03.json"
                exported.value.save_as(str(final_file))
                final_obj = next(h for r in parse_document(final_file.read_text()).rooms
                                 if r.name == "Harbor" for h in r.hotspots if h.id == "Door")
                assert final_obj.object_zplane_pixels == bytes([1]) * 256
                assert final_obj.object_zplane2_pixels == bytes([1]) * 256
                assert final_obj.object_zplane3_pixels == bytes([1]) * 256
                assert final_obj.open_object_zplane_pixels == bytes(256)
                assert final_obj.open_object_zplane2_pixels == bytes([1]) * 256
                assert final_obj.open_object_zplane3_pixels == bytes([1]) * 256
                page.screenshot(path=str(evidence / "authored-im02-zp03.png"), full_page=True)
                page.screenshot(path=str(evidence / "authored-im01-zp03.png"), full_page=True)
                page.screenshot(path=str(evidence / "authored-im02-zp02.png"), full_page=True)
                page.screenshot(path=str(evidence / "authored-im01-zp02.png"),
                                full_page=True)
                page.screenshot(path=str(evidence / "authored-object-zmask.png"),
                                full_page=True)
                (evidence / "result.json").write_text(json.dumps(
                    {"real_chrome_object_zmask": True,
                     "real_chrome_im01_zp02": True,
                     "real_chrome_im02_zp02": True,
                     "real_chrome_im02_zp03": True,
                     "im02_mask_preserved": True, "object": "Door"},
                    indent=2) + "\n", encoding="utf-8")
            except Exception:
                if not page.is_closed():
                    page.screenshot(path=str(evidence / "failure.png"), full_page=True)
                raise
            finally:
                browser.close()


if __name__ == "__main__":
    main()
