# SCUMM-v6 multilingual screenshot acceptance checklist

This is a **manual visual acceptance gate**, not a claim that the CI probe
recognizes glyphs. GitHub Actions proves that ScummC compiles and ScummVM
runs; pixel differences alone cannot prove a translated line is readable.

## Reproduce the evidence

1. Open the latest successful **SCUMM v6 multilingual gameplay probe** run on
   `feature/localized-scumm-story-20261105`.
2. Download the `multilingual-game-runtime-evidence` artifact.
3. Inspect the PNG files **at native size**; zoom in using nearest-neighbor
   scaling when checking a pixel font. Open `language-runtime-report.json` and
   `scummvm.log` alongside the images.
4. Record each result as pass/fail with a concrete visible defect, not as
   “CI green implies readable.”

The test game is the deliberately small English-source fixture
`examples/mini_story_language_en.json`; the text below does not describe an
arbitrary player's story.

| Screenshot | Intended event | Visible text or GUI evidence to inspect |
| --- | --- | --- |
| `de.png` | Select German with key `1` | `Die Kellertür ist jetzt offen.`; `ü` must be a distinct, legible glyph |
| `en.png` | Select English with key `2` | `The cellar door is open now.`; spacing and clipping must be acceptable |
| `fr.png` | Select French with key `3` | `La porte de la cave est ouverte.`; punctuation and spacing must be legible |
| `ja.png` | Select Japanese with key `4` | `地下室の扉が開きました。`; distinct Kana/Kanji, no tofu squares or clipped glyphs |
| `pl.png` | Select Polish with key `5` | `Drzwi do piwnicy są otwarte.`; `ą` must be legible |
| `room_after_pl.png` | Change to Cellar with key `0` without choosing a new language | Polish remains selected; room transition really occurred |
| `ja_after_room.png` | Select Japanese with key `4` inside Cellar | Japanese text appears and `JA` is active in the fixed GUI |
| `pl_returned_after_room.png` | Select Polish again with key `5` inside Cellar | Polish text appears and `PL` becomes active |
| `pl_after_room.png` | Repeat translated line with key `6` after the room change | The Polish key name `klucz` appears, not the English `key` |
| `pl_button_before.png` | Keep Polish selected in the second room | Fixed bottom GUI shows `PL` as active and all five language controls are present |
| `de_button_after.png` | Click `DE` in the bottom GUI | Selection changes to `DE` without a room jump or hidden controls |
| `en_button_after.png`, `fr_button_after.png`, `ja_button_after.png`, `pl_button_after.png` | Click each remaining language control in sequence inside Cellar | Each newly selected entry becomes active and the others remain visible |

For every text screenshot also check that adjacent letters and lines do not
overlap, that narrow glyphs have reasonable spacing, and that the whole
sentence fits the expected text area. Keep a separate note for graphics that
look like the correct characters but are too small to read at native size.

## Limits of the automated measurements

- `nonblank_captures_verified` rejects blank captures but does not identify
  the game scene or decode text.
- `graphical_button_selection_changed` is a pixel-change check after clicking
  the bottom GUI, not a semantic text-recognition check.
- `screen_gui_individual_click_pixel_changes` checks each adjacent selection
  pair for a visible change in the permanent GUI row; it still does not
  recognize which text the game rendered in its room.
- `screen_gui_across_rooms_pixel_change` compares all five language entries
  in the bottom control area **below** the 640×288 scene (`y >= 472` on the
  1024×768 Xvfb display). A
  low change count indicates stable pixels, not guaranteed click handling.
- `language_persistence_visually_verified` and `glyph_rendering_verified`
  remain `false` until a human or a separately validated recognition procedure
  confirms the actual displayed characters.

Do not merge the localization PR solely on the strength of the automated
pixel report. Preserve the screenshots and record this checklist's pass/fail
results before changing the opt-in feature into a default behavior.

## Save/load investigation (not yet an acceptance gate)

The isolated save-menu probe runs with its own `--config` and `--savepath`,
so it cannot alter a developer's existing ScummVM profile or saves. It
captures `polish-before-menu.png`, `save-menu-after-ctrl-f5.png`,
`after-escape.png`, and `menu-after-f5.png`. The JSON report distinguishes
keys being sent from actions actually verified. Neither a nonblank screenshot
nor a changed-pixel threshold proves that a save slot is usable.

In run [42233319743](https://github.com/nauen/adventure_studio/actions/runs/42233319743),
both menu shortcuts visibly opened a dark menu with many identical-looking
purple square glyphs. The menu labels were not legible in the captured
images. **Do not automate blind save/load clicks or report persistence as
passing based on these pictures.** A separate stock-font comparison is being
used to isolate whether the multilingual CHAR replacement caused this.

Once the controls are legible, the full integration gate must:

1. Select Polish and verify a new, nonempty save-slot file appears in the
   dedicated save directory after an actual menu action.
2. Switch to Japanese and change rooms; record a scene screenshot and the
   state of the language controls.
3. Load the newly saved slot and check the original room and Polish language
   independently. A mere process restart or successful `--save-slot` launch
   must not be counted as state restoration without visual evidence.
4. Preserve the menu, save-slot inventory, before/after scene screenshots,
   and ScummVM log as CI artifacts. Keep the feature opt-in until the gate
   and manual readability review both pass.
