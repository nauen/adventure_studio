# Room and export contract (research, 2026-11-04)

This is a design contract for a future spatial model, **not yet implemented**.

## Main finding

Do not model a wide, scrolling room as two separate story scenes. Keep one
logical room with a world-space background, a smaller camera/viewport, and
objects positioned in room/world coordinates. The renderer or exporter maps
world coordinates to viewport pixels.

Example: a 640 x 200 background and a 320 x 200 viewport yield up to
320 pixels of horizontal camera movement.

## Engine-neutral room model

Required eventual fields:

- `room_id` stable narrative identity
- `background` asset ID, width, height and source/provenance
- `viewport` width, height (screen-space)
- `camera` mode (`follow_player`, `fixed`, `scripted`), bounds, optional deadzone
- `walkable` polygons in world-space
- `occluders` / walkbehind polygons and baseline depth
- `hotspots` polygons with semantic object/interaction refs
- `placed_objects` with anchors, bounding boxes, z-order and sprite asset refs
- `entry_points` for room transitions
- `regions` with optional visual/lighting/audio metadata
- `animation_sets` as named state/direction sequences, not one file per frame

All coordinates use **room/world pixels**, not screen pixels. Separate narrative
objects and their placement, so an item can be created before its art exists.
Use one stable object ID in story, interaction and placement layers.

## Exporter-specific behavior

| Feature | AGS | SCUMM v6 / ScummC |
| --- | --- | --- |
| Wide room | Background larger than camera/viewport; auto tracking supported | Strip-based graphics and scroll semantics; investigate limits per version |
| Walk navigation | Walkable area masks | Walkboxes/box adjacency |
| Occlusion | Walkbehind masks with baselines | SCUMM masks and actor draw ordering |
| Interactions | Room objects/hotspots + scripts | Room objects + SCUMM scripts |
| Animated backgrounds | AGS room background frames | Resource/version-specific; validate by backend |
| Assets | AGS sprite resources | Palette/format/costume resources; toolchain-specific |

### AGS references

- Camera and room scrolling: https://adventuregamestudio.github.io/ags-manual/Camera.html
- Viewports: https://adventuregamestudio.github.io/ags-manual/Viewport.html
- Room editor and masks: https://adventuregamestudio.github.io/ags-manual/EditorRoom.html
- Screen auto-sizing: https://adventuregamestudio.github.io/ags-manual/Screen.html
- ScummVM AGS compatibility: https://www.scummvm.org/compatibility/2026.4.0/ags%3Aags/

### SCUMM references

- ScummC toolchain and box editor: https://github.com/AlbanBedel/scummc
- ScummVM SCUMM graphics implementation: https://github.com/scummvm/scummvm/blob/master/engines/scumm/gfx.cpp
- ScummVM smooth-scrolling setting: https://github.com/scummvm/scummvm/blob/master/doc/docportal/settings/game.rst

## Compatibility decisions and verification gates

1. Initial production target: a stable AGS 3.x format that the selected ScummVM
   runtime supports. Confirm by running an actual exported game, not by
   assuming generic AGS compatibility covers every feature.
2. SCUMM v6 is a **separate experimental backend**, not a promise of equivalent
   behavior. ScummC documents a patched ScummVM or a game-ID workaround.
3. Each backend needs a capability manifest. Unsupported rendering/action
   features cause an explicit export error; never silently degrade a puzzle.
4. Automated export acceptance fixture: one ordinary room, one 2x-width
   scrolling room, a walkable polygon, a walkbehind, an interactive object,
   one room transition, one item pickup and save/load.
5. Ensure sprite/animation frame atlases and generated graphics are checked for
   palette, size, naming and memory limits of the selected backend.
6. Test actual ScummVM detection and playability on the target release. A
   compiled game existing on disk does not prove ScummVM compatibility.

## Important distinctions

*A scene* is a narrative unit. *A room* is a spatial game map. One room can
contain multiple scenes, and a scene can involve multiple rooms. Keep these as
separate identities from the start.

Do not generate technical room coordinates from story text alone. Locations
such as 'key on table' are semantic placement relationships; coordinates can
be resolved after art generation and verified against walkability and hotspots.

## Open research before implementing a SCUMM exporter

- SCUMM v6 resource dimension constraints, palette requirements and costume
  animation conventions for ScummC output.
- Exact walkbox adjacency/scaling semantics and clipping of scrolling masks.
- Whether the target ScummVM version will recognize custom ScummC game data
  without a local patch; do not assume so.
- Licensing obligations of any reused compiler or artwork tools.
