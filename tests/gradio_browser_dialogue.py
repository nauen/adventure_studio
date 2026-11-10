"""Real Chromium acceptance of native dialogue pose authoring in Gradio.

Uses a generated SCUMM-v6 project, the actual browser controls, and a
download/reimport cycle. Run only from the Gradio UI CI with a live server.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from adventure_studio.scumm_project import parse_document
from adventure_studio.studio_sequences import (
    dialogue_animation_lines, dialogue_speaking_frame_selection,
)


def select_option(page, elem_id: str, label: str) -> None:
    """Select a Gradio Dropdown option by the text visible to authors."""
    dropdown = page.locator("#" + elem_id)
    dropdown.click()
    page.get_by_text(label, exact=True).last.click(timeout=12000)


def displayed_value(page, elem_id: str) -> str:
    dropdown = page.locator("#" + elem_id)
    entry = dropdown.locator("input")
    if entry.count() and entry.first.input_value():
        return entry.first.input_value()
    return dropdown.inner_text()


def await_selection(page, elem_id: str, label: str) -> None:
    expect.poll(lambda: displayed_value(page, elem_id), timeout=15000).to_contain(label)


def main() -> None:
    fixture = Path(os.environ["ADVENTURE_STUDIO_BROWSER_PROJECT"]).resolve()
    evidence = Path(os.environ.get("ADVENTURE_STUDIO_BROWSER_EVIDENCE", "/tmp/studio-browser-evidence"))
    evidence.mkdir(parents=True, exist_ok=True)
    raw = fixture.read_text(encoding="utf-8")
    names = [(label, identity) for label, identity in dialogue_animation_lines(raw)
             if label.startswith("SpeakerWitness")]
    if len(names) != 2:
        raise AssertionError(f"Expected two real authored NPC lines: {names}")
    first, second = names
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
            expect(page.locator("#native-project-report")).to_contain_text(
                "Natives Projekt geladen und validiert", timeout=30000)

            select_option(page, "native-dialogue-line", first[0])
            await_selection(page, "native-dialogue-pose", "Speak")
            await_selection(page, "native-dialogue-animation", "gesture")
            page.screenshot(path=str(evidence / "first-line.png"), full_page=True)

            select_option(page, "native-dialogue-line", second[0])
            await_selection(page, "native-dialogue-pose", "SpeakAlt")
            await_selection(page, "native-dialogue-animation", "pose_SpeakAlt")
            page.screenshot(path=str(evidence / "second-line.png"), full_page=True)

            # Edit the second line using the actual PNG selector and button,
            # while retaining the first line's native talk-start pose.
            select_option(page, "native-dialogue-pose", "Speak")
            page.locator("#native-dialogue-pose-apply").click()
            await_selection(page, "native-dialogue-pose", "Speak")
            await_selection(page, "native-dialogue-animation", "gesture")

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
            assert dialogue_speaking_frame_selection(data, first[1])[1] == "Speak"
            assert dialogue_speaking_frame_selection(data, second[1])[1] == "Speak"

            page.locator("#native-project-file input[type=file]").set_input_files(
                str(saved))
            expect(page.locator("#native-project-report")).to_contain_text(
                "Natives Projekt geladen und validiert", timeout=30000)
            select_option(page, "native-dialogue-line", second[0])
            await_selection(page, "native-dialogue-pose", "Speak")
            select_option(page, "native-dialogue-line", first[0])
            await_selection(page, "native-dialogue-pose", "Speak")
            page.screenshot(path=str(evidence / "reimported.png"), full_page=True)
            (evidence / "result.json").write_text(json.dumps({
                "passed": True, "first": first[1], "second": second[1],
                "reimported_second_pose": "Speak",
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
