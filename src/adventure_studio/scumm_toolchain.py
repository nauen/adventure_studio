"""External ScummC adapter for a validated, story-derived GameDocument.

Only resource names from the validated project are used; no project-defined
shell commands, arbitrary scripts or user-supplied compiler flags are accepted.
The upstream GPL demo bootstrap remains external and research-only.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

from .scumm_bootstrap import (inject_inventory_declarations, inject_inventory_objects,
                              inject_multilingual_charset, retarget_upstream_bootstrap)
from .scumm_font_probe import verify_char_resource
from .scumm_project import parse_document


def _tool(upstream: Path, name: str) -> Path:
    preferred = upstream / name
    if preferred.is_file() and os.access(preferred, os.X_OK):
        return preferred.resolve()
    candidates = sorted(p for p in upstream.rglob(name) if p.is_file() and os.access(p, os.X_OK))
    if not candidates:
        raise ValueError(f"Missing ScummC executable: {name}")
    return candidates[0].resolve()


def compile_story_game(build_directory: Path, upstream: Path, output: Path,
                       runner: Callable = subprocess.run) -> Path:
    """Compile and link all validated rooms; return a loadable research fixture."""
    document = parse_document((build_directory / "project.json").read_text(encoding="utf-8"))
    resources = build_directory / "resources"
    icon_ids = tuple(sorted(h.id for room in document.rooms for h in room.hotspots if h.pickup))
    manifest = (resources / "inventory-ids.txt").read_text(encoding="ascii").strip()
    if manifest != ",".join(icon_ids):
        raise ValueError("Inventory manifest does not match validated project")
    for room in document.rooms:
        for suffix in (".scc", ".bmp"):
            if not (resources / f"{room.name}{suffix}").is_file():
                raise ValueError(f"Missing room resource: {room.name}{suffix}")
        if room.music_id is not None and not (resources / f"{room.music_id}.soun").is_file():
            raise ValueError(f"Missing music resource: {room.music_id}.soun")
    road = upstream / "examples" / "road"
    original = (road / "common.scc").read_text(encoding="utf-8")
    header = (road / "common.sch").read_text(encoding="utf-8")
    start = document.rooms[0].name
    bootstrap = retarget_upstream_bootstrap(original, start)
    custom_font = resources / "multilingual-font.char"
    if custom_font.exists():
        # Glyphs needed by the stock 7-bit UI and story text must be present.
        # This rejects truncated or malformed resources before the linker runs.
        verify_char_resource(custom_font, set(range(32, 127)))
        bootstrap = inject_multilingual_charset(bootstrap)
        shutil.copyfile(custom_font, road / custom_font.name)
    (resources / "bootstrap.scc").write_text(inject_inventory_objects(bootstrap, icon_ids), encoding="utf-8")
    (resources / "common.sch").write_text(inject_inventory_declarations(header, icon_ids), encoding="utf-8")
    for name in icon_ids:
        icon = resources / f"Inv_{name}.bmp"
        if not icon.is_file():
            raise ValueError(f"Missing inventory icon: {name}")
        shutil.copyfile(icon, road / icon.name)

    compiler = _tool(upstream, "scc")
    linker = _tool(upstream, "sld")
    include_args = ["-I", str(upstream / "include"), "-I", str(resources), "-I", str(road)]
    objects = []
    for room in document.rooms:
        target = resources / f"{room.name}.roobj"
        runner([str(compiler), "-V", "6", *include_args, "-R", str(resources),
                "-o", str(target), str(resources / f"{room.name}.scc")], check=True)
        if not target.is_file() or target.stat().st_size == 0:
            raise RuntimeError(f"ScummC did not produce {target.name}")
        objects.append(target)

    bootstrap_object = resources / "bootstrap.roobj"
    runner([str(compiler), "-V", "6", *include_args, "-R", str(road),
            "-o", str(bootstrap_object), str(resources / "bootstrap.scc")], check=True)
    if not bootstrap_object.is_file() or bootstrap_object.stat().st_size == 0:
        raise RuntimeError("ScummC did not compile the bootstrap")

    output.mkdir(parents=True, exist_ok=True)
    target = output / "tentacle"
    runner([str(linker), "-o", str(target), "-key", "0x69",
            str(bootstrap_object), *(str(obj) for obj in objects)], check=True, cwd=road)
    for suffix in (".000", ".001"):
        binary = target.with_suffix(suffix)
        if not binary.is_file() or binary.stat().st_size == 0:
            raise RuntimeError(f"Linker did not produce {binary.name}")
    shutil.copyfile(resources / "game-goal.json", output / "game-goal.json")
    return output


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: python -m adventure_studio.scumm_toolchain STORY_BUILD_DIRECTORY SCUMMC_DIRECTORY GAME_OUTPUT_DIRECTORY")
        return 2
    print(compile_story_game(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
