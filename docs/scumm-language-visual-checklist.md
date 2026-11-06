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
| `ja.png` | Select Japanese with key `4` | `地下室の扉が開きました。`; distinct Kana/Kanji, no tofu squares or clipped glyphs |
| `pl.png` | Select Polish with key `5` | `Drzwi do piwnicy są otwarte.`; `ą` must be legible |
| `room_after_pl.png` | Change to Cellar with key `0` without choosing a new language | Polish remains selected; room transition really occurred |
| `pl_after_room.png` | Repeat translated line with key `6` after the room change | The Polish key name `klucz` appears, not the English `key` |
| `pl_button_before.png` | Keep Polish selected in the second room | Fixed bottom GUI shows `PL` as active and all five language controls are present |
| `de_button_after.png` | Click `DE` in the bottom GUI | Selection changes to `DE` without a room jump or hidden controls |

For every text screenshot also check that adjacent letters and lines do not
overlap, that narrow glyphs have reasonable spacing, and that the whole
sentence fits the expected text area. Keep a separate note for graphics that
look like the correct characters but are too small to read at native size.

## Limits of the automated measurements

- `nonblank_captures_verified` rejects blank captures but does not identify
  the game scene or decode text.
- `graphical_button_selection_changed` is a pixel-change check after clicking
  the bottom GUI, not a semantic text-recognition check.
- `screen_gui_across_rooms_pixel_change` compares only the bottom control area
  **below** the 640×288 scene (`y >= 472` on the 1024×768 Xvfb display). A
  low change count indicates stable pixels, not guaranteed click handling.
- `language_persistence_visually_verified` and `glyph_rendering_verified`
  remain `false` until a human or a separately validated recognition procedure
  confirms the actual displayed characters.

Do not merge the localization PR solely on the strength of the automated
pixel report. Preserve the screenshots and record this checklist's pass/fail
results before changing the opt-in feature into a default behavior.
