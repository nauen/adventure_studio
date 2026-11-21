"""Real Chromium authoring proof for four room Z-planes and native camera cues."""
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
    evidence = Path(os.environ.get("ADVENTURE_STUDIO_ZPLANES_EVIDENCE",
                                  "/tmp/studio-zplanes-evidence"))
    evidence.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        fixture = root / "project.json"
        fixture.write_text(canonical_json(GameDocument("four_zplanes_camera", (
            scrolling_fixture(), destination_fixture()))), encoding="utf-8")
        masks = []
        regions = ((160, 320), (320, 400), (400, 500), (500, 640))
        for index, (start, end) in enumerate(regions, 1):
            image = Image.new("L", (640, 200), color=0)
            for y in range(60, 110):
                for x in range(start, end):
                    image.putpixel((x, y), 255)
            path = root / f"zp{index:02d}.png"
            image.save(path)
            masks.append(path)

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

                corners = page.locator(
                    "#native-walkbox-corners textarea, #native-walkbox-corners input")
                for index, shape in (
                    (1, "0,70; 160,70; 160,150; 0,150"),
                    (2, "160,70; 320,70; 320,150; 160,150"),
                    (3, "320,70; 400,70; 400,150; 320,150"),
                    (4, "400,70; 500,70; 500,150; 400,150"),
                    (5, "500,70; 639,70; 639,150; 500,150"),
                ):
                    page.locator("#native-walkbox-index input").fill(str(index))
                    corners.fill(shape)
                    page.locator("#native-walkbox-add").click()
                    expect(report).to_have_value(
                        re.compile(fr"Walkbox {index}.*gespeichert"), timeout=30000)

                routes = page.locator(
                    "#native-box-routes-connections textarea, #native-box-routes-connections input")
                routes.fill("1-2; 2-3; 3-4; 4-5")
                page.locator("#native-box-routes-add").click()
                expect(report).to_have_value(re.compile(r"BOXM-Wege.*gespeichert"),
                                             timeout=30000)

                for index, image in enumerate(masks, 1):
                    if index > 1:
                        page.locator("#native-zplane-file").locator("button").last.click()
                        expect(page.locator("#native-zplane-file")).to_contain_text(
                            "Click to Upload")
                    page.locator("#native-zplane-index input").fill(str(index))
                    with page.expect_file_chooser() as file_chooser:
                        page.locator("#native-zplane-file").click()
                    file_chooser.value.set_files(str(image))
                    page.locator("#native-zplane-add").click()
                    expect(report).to_have_value(
                        re.compile(fr"Z-Ebene {index}.*gespeichert"), timeout=30000)

                for box_index, plane_index in enumerate((1, 2, 3, 4), start=2):
                    page.locator("#native-zplane-box-index input").fill(str(box_index))
                    page.locator("#native-zplane-box-layer input").fill(str(plane_index))
                    page.locator("#native-zplane-box-add").click()
                    expect(report).to_have_value(
                        re.compile(fr"Walkbox {box_index} verwendet Z-Ebene {plane_index}"),
                        timeout=30000)

                stationary = page.locator("#native-camera-stationary input")
                expect(stationary).not_to_be_checked()
                stationary.check()
                expect(stationary).to_be_checked()
                page.locator("#native-camera-ego-x input").fill("240")
                page.locator("#native-camera-ego-y input").fill("100")
                cues = "set:160;hold:360;pan:480;wait;hold:120;pan:160;wait"
                page.locator("#native-camera-cues textarea").fill(cues)
                page.locator("#native-camera-add").click()
                expect(report).to_have_value(
                    re.compile(r"Ego-Weltstart und native Kamerafolge"), timeout=30000)

                page.locator("#native-project-export-button").click()
                link = page.locator("#native-project-export-file a[download]")
                expect(link.first).to_be_visible(timeout=30000)
                with page.expect_download() as downloading:
                    link.first.click()
                saved = evidence / "authored-four-zplanes-camera.json"
                downloading.value.save_as(str(saved))
                exported = next(item for item in parse_document(saved.read_text()).rooms
                                if item.name == "Harbor")
                assert len(exported.zplanes) == 4
                assert [box.mask for box in exported.walkboxes] == [0, 1, 2, 3, 4]
                assert len(exported.walkboxes) == 5
                assert exported.box_routes[1][2] == 2
                assert exported.box_routes[2][3] == 3
                assert exported.box_routes[3][4] == 4
                assert exported.box_routes[4][5] == 5
                assert (exported.ego_start_x, exported.ego_start_y) == (240, 100)
                assert exported.demo_walk_to_x is None
                assert [(cue.operation, cue.x, cue.ticks) for cue in exported.camera_cues] == [
                    ("set", 160, None), ("hold", None, 360), ("pan", 480, None),
                    ("wait", None, None), ("hold", None, 120), ("pan", 160, None),
                    ("wait", None, None)]
                for index, (start, end) in enumerate(regions):
                    plane = exported.zplanes[index]
                    assert plane.index == index + 1
                    assert plane.pixels == bytes(
                        1 if start <= x < end and 60 <= y < 110 else 0
                        for y in range(200) for x in range(640))

                # Reopen the exported project in the actual Studio UI. Edit one
                # camera cue, then prove all four PNGs and BOXD/BOXM assignments survive.
                page.locator("#native-project-file").locator("button").last.click()
                expect(page.locator("#native-project-file")).to_contain_text("Click to Upload")
                with page.expect_file_chooser() as chooser:
                    page.locator("#native-project-file").click()
                chooser.value.set_files(str(saved))
                expect(report).to_have_value("Natives Projekt geladen und validiert",
                                             timeout=30000)
                expect(page.locator("#native-camera-ego-x input")).to_have_value("240",
                                                                                timeout=30000)
                expect(page.locator("#native-camera-cues textarea")).to_have_value(cues)
                expect(page.locator("#native-camera-stationary input")).to_be_checked()
                edited_cues = "set:160;hold:120;pan:480;wait;hold:120;pan:160;wait"
                page.locator("#native-camera-cues textarea").fill(edited_cues)
                page.locator("#native-camera-add").click()
                expect(report).to_have_value(
                    re.compile(r"Ego-Weltstart und native Kamerafolge"), timeout=30000)
                page.locator("#native-project-export-button").click()
                expect(link.first).to_be_visible(timeout=30000)
                with page.expect_download() as edited_download:
                    link.first.click()
                edited = evidence / "authored-four-zplanes-camera-edited.json"
                edited_download.value.save_as(str(edited))
                revised = next(item for item in parse_document(edited.read_text()).rooms
                               if item.name == "Harbor")
                assert revised.camera_cues[1].ticks == 120
                assert revised.zplanes == exported.zplanes
                assert revised.walkboxes == exported.walkboxes
                assert revised.box_routes == exported.box_routes
                page.screenshot(path=str(evidence / "authored-four-zplanes-camera.png"),
                                full_page=True)
                (evidence / "result.json").write_text(json.dumps({
                    "studio_four_room_zplanes": True,
                    "walkbox_mask_assignments": [1, 2, 3, 4],
                    "box_routes_preserved": True,
                    "studio_camera_roundtrip": True,
                    "studio_camera_reload_and_edit": True,
                }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                print("Four Z-plane PNGs, BOXD/BOXM and camera cues authored in real Chrome")
            except Exception:
                if not page.is_closed():
                    page.screenshot(path=str(evidence / "failure.png"), full_page=True)
                raise
            finally:
                browser.close()


if __name__ == "__main__":
    main()
