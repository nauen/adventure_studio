# Adventure Studio – deterministic core (prototype)

Story-first adventure creation, with a strictly data-driven, testable engine.

## Product target

**Produce original SCUMM v6 game data that runs in ScummVM.** The author never
needs to know about compilers or game file formats. Compatibility with an
original DOS SCUMM interpreter is a *separate optional goal*, not an assumption.
AGS is **not** an export target. The first integration candidate is ScummC;
its outputs and game recognition must be tested with unmodified ScummVM before
we can claim a working exporter. See `docs/room-and-export-contract.md`.

## Run tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

The current proof of concept supports Boolean state, atomic actions, reachability,
dead-end detection, typed object/action changes, orphan consolidation with
container dependencies, structured change reports and atomic JSON persistence
with revision checks. It now also includes a story bible (`story.py`) with
chapters, scenes, characters, items and puzzles, a deterministic story compiler,
typed story changes and a strict JSON protocol for untrusted AI proposals.
It does **not** yet include an actual AI provider, a UI, graphics, or ScummVM export.
`targets.py` defines the SCUMM v6 target policy and a fail-closed export gate.

## SCUMM toolchain research

The CLI probe `PYTHONPATH=src python -m adventure_studio.scumm_probe GAME_DIRECTORY`
checks for non-empty matching `.000`/`.001` files and asks unmodified ScummVM
to detect them. This is an **early gate only**, not a playability test.

An experimental GitHub Actions workflow, `Experimental SCUMM v6 compatibility
probe`, builds the upstream ScummC sample on Ubuntu and attempts recognition
using stock ScummVM. It runs on relevant probe changes or manually. A red run
is diagnostic and not a product-release failure. Build success, game detection,
actual launch and save/load are separate acceptance gates.

The workflow tests **three distinct detection cases**: our normally linked
`studio.000/.001` files, the untouched upstream sample, and a separate
`tentacle.000/.001` research fixture created with ScummC's documented
`-key 0x69` compatibility option. The last case deliberately identifies as
Day of the Tentacle: it is useful for isolating detection failures, but is
**not** proof of native recognition, general ScummVM compatibility, or a
shippable game. Detection probes do not hide compiler/linker failures.

The experimental `scumm_launch.py` smoke test now starts the isolated
`tentacle` compatibility fixture in an Xvfb display for four seconds and
uploads its console log and screenshot (`.png`, plus raw `.xwd`) as Actions artifacts.
It is designed to expose immediate crashes. A surviving process and a
framebuffer screenshot do **not** establish that the game rendered correctly,
that scrolling works, or that gameplay is possible. These remain separate
integration milestones.

`scumm_assets.py` now emits an original 640×200 indexed BMP and a SCUMM-v6
`room` source with data-driven object hotspots, LookAt and PickUp handlers.
The experimental workflow attempts to compile the room and link it with the
upstream example's global startup scripts. This is **not yet** a standalone
game whose bootstrap was independently written by Adventure Studio. The
research adapter `scumm_bootstrap.py` retargets the original GPL demo's
bootstrap to our generated room, with exact-match safety checks. This requires
compatible upstream assets and carries the upstream code's license obligations.
The pipeline also replaces the upstream road
demo background with our generated image, rebuilds the *complete upstream demo*
and attempts stock ScummVM detection. That verifies parts of the exporter
chain without misrepresenting upstream game logic as our own. Linking our own
global scripts, actors and interactions is still unfinished.

## Boundaries

The AI should eventually propose typed project operations, not executable scripts.
Deterministic validation and state exploration decide whether a proposal may commit.
An incomplete state exploration must fail closed.

Use `adventure_studio.changes.apply_changes` to build a validated candidate
and inspect a complete diff before calling `adventure_studio.storage.save`.
The storage layer uses an atomic file replacement and a SHA-256 revision guard.
Concurrent writers must be serialized by a higher-level repository service;
the guard alone is not a multiprocess lock.

## Story-first workflow

1. Describe the plot using the immutable dataclasses in `story.py`.
2. `validate_story` checks references; `compile_story` translates a restricted
   puzzle vocabulary into generic actions; `verify_story` rejects softlocks.
3. An AI client can submit bounded JSON operations through
   `story_protocol.parse_operations`; no submitted code is evaluated.
4. `story_changes.edit_story` applies all operations on a candidate, validates
   the complete result and returns an explicit before/after report.

The current story compiler supports item pickup, scene-unlock puzzles and a
final puzzle goal. Dialogue trees, multi-step crafting, item consumption,
positioning and dynamic story generation are deliberately **not** implemented.

Dead-end analysis uses reverse reachability from winning states, so loops that
cannot reach a goal are classified as dead ends too. The current model remains
deliberately small: Boolean flags and predefined actions only.
