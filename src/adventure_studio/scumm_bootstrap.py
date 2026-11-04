"""Retarget an explicit external GPL ScummC demo bootstrap for integration tests.

The Adventure Studio repository does not bundle that upstream runtime.
This is a research adapter, not the final independently written bootstrap.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def retarget_upstream_bootstrap(source: str, room_name: str) -> str:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", room_name):
        raise ValueError("Invalid room identifier")
    original = (
        "room Road;",
        "loadRoom(Road);",
        "lockRoom(Road);",
        "startRoom(Road);",
    )
    for expression in original:
        if source.count(expression) != 1:
            raise ValueError(f"Unexpected upstream bootstrap layout: {expression}")
    for expression in original:
        source = source.replace(expression, expression.replace("Road", room_name))
    return source


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: python -m adventure_studio.scumm_bootstrap INPUT OUTPUT ROOM_NAME")
        return 2
    original = Path(sys.argv[1]).read_text(encoding="utf-8")
    result = retarget_upstream_bootstrap(original, sys.argv[3])
    Path(sys.argv[2]).write_text(result, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
