# Adventure Studio – deterministic core (prototype)

Story-first adventure creation, with a strictly data-driven, testable engine.

## Run tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

The current proof of concept supports Boolean state, atomic actions, reachability,
dead-end detection, typed object/action changes, orphan consolidation with
container dependencies, structured change reports and atomic JSON persistence
with revision checks. It does **not** yet include AI, a UI, graphics, or ScummVM export.

## Boundaries

The AI should eventually propose typed project operations, not executable scripts.
Deterministic validation and state exploration decide whether a proposal may commit.
An incomplete state exploration must fail closed.

Use `adventure_studio.changes.apply_changes` to build a validated candidate
and inspect a complete diff before calling `adventure_studio.storage.save`.
The storage layer uses an atomic file replacement and a SHA-256 revision guard.
Concurrent writers must be serialized by a higher-level repository service;
the guard alone is not a multiprocess lock.

Dead-end analysis uses reverse reachability from winning states, so loops that
cannot reach a goal are classified as dead ends too. The current model remains
deliberately small: Boolean flags and predefined actions only.
