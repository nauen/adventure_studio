# Adventure Studio – deterministic core (prototype)

Story-first adventure creation, with a strictly data-driven, testable engine.

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
