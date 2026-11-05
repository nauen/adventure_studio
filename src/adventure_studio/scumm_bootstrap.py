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


def inject_inventory_objects(source: str, icon_ids: tuple[str, ...]) -> str:
    """Extend external example's ResRoom with data-driven inventory icons."""
    marker = "    // the inventory icons\n"
    if source.count(marker) != 1:
        raise ValueError("Unexpected upstream inventory layout")
    if len(icon_ids) != len(set(icon_ids)):
        raise ValueError("Duplicate inventory icon identifier")
    for icon_id in icon_ids:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", icon_id):
            raise ValueError("Invalid inventory icon identifier")
    definitions = "".join(
        f'    object {icon_id}Icon {{\n'
        '        x = 0;\n        w = 40;\n        h = 16;\n'
        f'        name = "{icon_id}";\n'
        f'        states = {{ {{ 0, 0, "Inv_{icon_id}.bmp" }} }};\n'
        '        state = 1;\n    }\n'
        for icon_id in icon_ids
    )
    return source.replace(marker, marker + definitions, 1)


def inject_inventory_declarations(header: str, icon_ids: tuple[str, ...]) -> str:
    marker = "    // Inventory objects\n"
    if header.count(marker) != 1:
        raise ValueError("Unexpected upstream inventory header layout")
    for icon_id in icon_ids:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", icon_id):
            raise ValueError("Invalid inventory icon identifier")
    return header.replace(marker, marker + "".join(f"    object {icon_id}Icon;\n" for icon_id in icon_ids), 1)


def read_icon_ids(argument: str) -> tuple[str, ...]:
    if argument.startswith("@"):
        argument = Path(argument[1:]).read_text(encoding="ascii").strip()
    ids = tuple(argument.split(",")) if argument else ()
    if len(ids) != len(set(ids)) or any(not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", icon) for icon in ids):
        raise ValueError("Invalid or duplicated inventory icon IDs")
    return ids


def main() -> int:
    if len(sys.argv) not in (4, 6):
        print("Usage: python -m adventure_studio.scumm_bootstrap INPUT OUTPUT ROOM_NAME [HEADER_INPUT ICON_IDS]")
        return 2
    original = Path(sys.argv[1]).read_text(encoding="utf-8")
    result = retarget_upstream_bootstrap(original, sys.argv[3])
    if len(sys.argv) == 6:
        icon_ids = read_icon_ids(sys.argv[5])
        result = inject_inventory_objects(result, icon_ids)
        header = Path(sys.argv[4]).read_text(encoding="utf-8")
        patched_header = inject_inventory_declarations(header, icon_ids)
        Path(sys.argv[2]).with_name("common.sch").write_text(patched_header, encoding="utf-8")
    Path(sys.argv[2]).write_text(result, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
