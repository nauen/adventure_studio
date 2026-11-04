# Adventure Studio – deterministic core (prototype)

Story-first adventure creation, with a strictly data-driven, testable engine.

## Run tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

The current proof of concept supports Boolean state, atomic actions, reachability,
dead-end detection, optional-object consolidation and structured change reports.
It does **not** yet include AI, a UI, persistence, graphics, or ScummVM export.

## Boundaries

The AI should eventually propose typed project operations, not executable scripts.
Deterministic validation and state exploration decide whether a proposal may commit.
An incomplete state exploration must fail closed.

Dead-end analysis uses reverse reachability from winning states, so loops that
cannot reach a goal are classified as dead ends too. The current model remains
deliberately small: Boolean flags and predefined actions only.
