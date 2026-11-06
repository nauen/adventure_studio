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

## Native ScummVM save/load integration gate

The isolated probe uses its own `--config` and `--savepath`, preserving the
developer's ScummVM profile and existing saves. It selects Polish with key
`5`, changes to Cellar with key `0`, opens the native global menu, creates
slot `tentacle.s01`, restarts ScummVM with `--save-slot=1`, and captures the
restored room and fixed language controls.

The **SCUMM v6 multilingual gameplay probe** workflow now fails unless all
three fields in `save-load-menu-report.json` are true:

- `save_created_verified`: a nonempty `tentacle.s01` exists.
- `load_restored_room_verified`: the loaded scene is close to the saved
  scene and differs substantially from the initial bootstrap room.
- `load_restored_language_verified`: the fixed language GUI differs from
  its default selection before saving and matches the selected state after
  loading. This checks the visible active-language highlight, not a direct
  dump of the internal `GameLanguage` variable.

The full gate passed in run
[42271624051](https://github.com/nauen/adventure_studio/actions/runs/42271624051).
The archive includes `before-polish-selection.png`,
`polish-in-initial-room.png`, `polish-before-menu.png`,
`save-menu-after-ctrl-f5.png`, `after-save-confirmation.png`,
`after-loading-slot-1.png`, and per-attempt screenshots named
`after-save-confirmation-attempt-N.png`. The report includes `save_attempts`
and `save_attempts_without_slot` so a successful retry does not hide an
earlier rejection.

### Intermittent native save rejection

The engine has sometimes shown **"This game cannot be saved at this time"**
after a visible room transition, for example in run
[42257549127](https://github.com/nauen/adventure_studio/actions/runs/42257549127).
The bounded retry waits after dismissing this dialog but is not a proven
fix for the underlying condition.
Six independent sessions in run
[42284700791](https://github.com/nauen/adventure_studio/actions/runs/42284700791)
reproduced two failures despite three save attempts each. Comparing native
menu screenshots showed an extra black **original SCUMM menu** behind the
orange ScummVM GMM in those failures; successful runs showed the purple room
behind the GMM. The probe now checks that background before attempting Save.

The test input changed from a rapid `xdotool key ctrl+F5` to explicitly
holding `Control_L` before sending `F5`, then releasing it with a delay.
With this change, all six stress sessions in
[42287757595](https://github.com/nauen/adventure_studio/actions/runs/42287757595)
saved and restored the room and language on their first attempts. This
supports a keyboard-modifier timing race as the trigger, but one clean
stress run cannot establish that the issue is permanently eliminated.
When the first or second save attempt fails, the opt-in fixture also presses
test key `7` after dismissing the menu: it prints either `Menu key enabled`
or `Menu key disabled` based on `VAR_MAINMENU_KEY`. The resulting screenshot
is named `save-gate-variable-after-rejection-N.png`. This diagnoses the
script-visible menu variable without depending on ScummVM's debugger hotkey;
it cannot directly inspect the engine's private current-room field.

In ScummVM 2.8.0, `ScummEngine::canSaveGameStateCurrently()` in
`engines/scumm/saveload.cpp` denies saves in SCUMM v4+ when the current
room is `0`, or when the `VAR_MAINMENU_KEY` variable is defined but contains
`0`. The ScummC Road bootstrap initializes `VAR_MAINMENU_KEY = 319`.
The ScummVM v6 variable mapping uses index **65** for that variable.

To identify which condition fails, reproduce the game state and open the
ScummVM debugger with `Ctrl+Alt+D` *before* opening the save menu. Query:

```text
scumm_room
scumm_vars[65]
```

The room must be nonzero and `scumm_vars[65]` should be `319`. Capture
the debugger output in the failing and successful states, then enter
`exit` to resume. Do not change either variable through the debugger as
part of the evidence collection. If both values satisfy the save gate,
inspect the active menu configuration and the exact engine version next.

This debugger check is **manual**: an attempt to automate `Ctrl+Alt+D` and
read the console through Xvfb in run
[42279547835](https://github.com/nauen/adventure_studio/actions/runs/42279547835)
did not yield readable debugger output. It is intentionally not part of the
automated Save/Load acceptance gate.

This is still an opt-in research fixture. The manual font legibility checks
above remain required before enabling localization by default.
