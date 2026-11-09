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

## SCUMM v6 export semantics (primary target)

| Feature | Required SCUMM implementation |
| --- | --- |
| Wide room | Strip-based background with camera scrolling (validate format limits) |
| Walk navigation | Walkboxes and adjacency |
| Occlusion | SCUMM masks and actor draw ordering |
| Interactions | Room objects and SCUMM v6 scripts |
| Animated backgrounds | Version-specific resource handling; must be proven |
| Assets | Palette-encoded backgrounds, costumes, sound resources |

### Comparative design references (AGS, **not** an export target)

- Camera and room scrolling: https://adventuregamestudio.github.io/ags-manual/Camera.html
- Viewports: https://adventuregamestudio.github.io/ags-manual/Viewport.html
- Room editor and masks: https://adventuregamestudio.github.io/ags-manual/EditorRoom.html
- Screen auto-sizing: https://adventuregamestudio.github.io/ags-manual/Screen.html

### SCUMM references

- ScummC toolchain and box editor: https://github.com/AlbanBedel/scummc
- ScummVM SCUMM graphics implementation: https://github.com/scummvm/scummvm/blob/master/engines/scumm/gfx.cpp
- ScummVM smooth-scrolling setting: https://github.com/scummvm/scummvm/blob/master/doc/docportal/settings/game.rst

## Compatibility decisions and verification gates

1. **Canonical output is SCUMM v6 game data for ScummVM**, not AGS. The editor
   and story model are engine-neutral internally, but the first exporter only
   targets SCUMM v6. ScummC is a candidate toolchain, not a completed backend.
2. Original DOS interpreter support is a second, stricter compatibility profile
   for the same family of game data. Never infer DOS compatibility merely from
   ScummVM success.
3. Each backend needs a capability manifest. Unsupported rendering/action
   features cause an explicit export error; never silently degrade a puzzle.
4. Automated export acceptance fixture: one ordinary room, one 2x-width
   scrolling room, a walkable polygon, a walkbehind, an interactive object,
   one room transition, one item pickup and save/load.
5. Ensure sprite/animation frame atlases and generated graphics are checked for
   palette, size, naming and memory limits of the selected backend.
6. Test actual ScummVM detection and playability on a specified baseline
   release, plus at least one older supported release when feasible. A compiled
   game existing on disk does not prove ScummVM compatibility. No promise of
   compatibility with *every* ScummVM build.
7. The export readiness guard stays false until both SCUMM output and launch
   have been automatically integration-tested. Do not silently substitute AGS.

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
