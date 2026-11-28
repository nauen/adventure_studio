"""Real Chrome: import a room PNG, save the combined project and reopen it."""
from pathlib import Path
import json
import os
import re
import tempfile

from PIL import Image
from playwright.sync_api import expect, sync_playwright
from adventure_studio.scumm_project import parse_document
from adventure_studio.studio_project import parse_studio_project


def run(width, evidence):
    evidence.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory, sync_playwright() as playwright:
        png = Path(directory) / "room.png"
        color = (18, 166, 111)
        Image.new("RGB", (width, 200), color).save(png)
        browser = playwright.chromium.launch(channel="chrome", headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1440, "height": 900}, accept_downloads=True)
        try:
            page.goto("http://127.0.0.1:7860/", wait_until="domcontentloaded", timeout=30000)
            page.get_by_role("tab", name="Native Interaktionsabläufe").click()
            report = page.locator("#native-project-report textarea, #native-project-report input")
            page.locator("#native-sync").click()
            expect(report).to_have_value(re.compile(r"Story-Räume übernommen"), timeout=30000)
            with page.expect_file_chooser() as chooser:
                page.locator("#native-background-file").click()
            chooser.value.set_files(str(png))
            if width > 640:
                page.locator("#native-background-expand input[type=checkbox]").check()
            page.locator("#native-background-add").click()
            expect(report).to_have_value(re.compile(r"Raumhintergrund für Harbor gespeichert"), timeout=30000)
            page.locator("#native-hotspot input").click()
            page.get_by_role("option", name="Door", exact=True).click()
            expect(page.locator("#native-exit-x input")).to_have_value("450", timeout=30000)
            page.locator("#native-exit-x input").fill("480")
            page.locator("#native-exit-y input").fill("80")
            page.locator("#native-exit-save").click()
            expect(report).to_have_value(re.compile(r"Raumausgang Door für Harbor gespeichert"), timeout=30000)
            page.locator("#studio-project-save").click()
            link = page.locator("#studio-project-download a[download]")
            expect(link.first).to_be_visible(timeout=30000)
            with page.expect_download() as downloading:
                link.first.click()
            saved = evidence / "adventure.studio.json"
            downloading.value.save_as(str(saved))
            _, raw = parse_studio_project(saved.read_text(encoding="utf-8"))
            room = parse_document(raw).rooms[0]
            assert room.authored_background and room.geometry.room_width == width
            assert set(room.pixels) == {room.palette.index(color)}
            door = next(h for h in room.hotspots if h.id == "Door")
            assert (door.x, door.y, door.authored_exit_position) == (480, 80, True)
            page.goto("http://127.0.0.1:7860/", wait_until="domcontentloaded", timeout=30000)
            page.locator("#studio-project-file input[type=file]").set_input_files(str(saved))
            page.get_by_role("tab", name="Native Interaktionsabläufe").click()
            expect(report).to_have_value(re.compile(r"Story, Actors, Costumes und Interaktionen gemeinsam geladen"), timeout=30000)
            page.locator("#native-sync").click()
            expect(report).to_have_value(re.compile(r"Story-Räume übernommen"), timeout=30000)
            preview = page.locator("#native-background-preview")
            preview.scroll_into_view_if_needed()
            expect(preview.locator("img").first).to_be_visible(timeout=30000)
            page.wait_for_function(
                """width => {
                    const img = document.querySelector('#native-background-preview img');
                    return img && img.naturalWidth === width && img.naturalHeight === 200;
                }""", arg=width, timeout=30000)
            page.locator("#studio-project-save").click()
            expect(link.first).to_be_visible(timeout=30000)
            with page.expect_download() as downloading:
                link.first.click()
            reopened = evidence / "reopened.studio.json"
            downloading.value.save_as(str(reopened))
            assert parse_studio_project(reopened.read_text(encoding="utf-8"))[1] == raw
            page.screenshot(path=str(evidence / "reopened.png"), full_page=True)
            (evidence / "result.json").write_text(json.dumps({"real_chrome_background_roundtrip": True, "room_width": width}), encoding="utf-8")
        except Exception:
            page.screenshot(path=str(evidence / "failure.png"), full_page=True)
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    evidence = Path(os.environ.get("ADVENTURE_STUDIO_BACKGROUND_EVIDENCE",
                                  "/tmp/studio-background-evidence"))
    run(640, evidence)
    run(960, evidence / "extended")
