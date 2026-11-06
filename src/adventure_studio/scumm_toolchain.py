"""External ScummC adapter for a validated, story-derived GameDocument.

Only resource names from the validated project are used; no project-defined
shell commands, arbitrary scripts or user-supplied compiler flags are accepted.
The upstream GPL demo bootstrap remains external and research-only.
"""

from __future__ import annotations

import os
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

from .scumm_bootstrap import (inject_inventory_declarations, inject_inventory_objects,
                              inject_language_keys, inject_language_room_probe, inject_multilingual_charset,
                              inject_screen_language_verbs, retarget_upstream_bootstrap)
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
                       runner: Callable = subprocess.run,
                       language_room_probe: bool = False,
                       localize_story: bool = False,
                       graphical_language_buttons: bool = False,
                       screen_language_gui: bool = False) -> Path:
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
    language_catalog = None
    custom_font = resources / "multilingual-font.char"
    if custom_font.exists():
        # Glyphs needed by the stock 7-bit UI and story text must be present.
        # This rejects truncated or malformed resources before the linker runs.
        verify_char_resource(custom_font, set(range(32, 127)))
        manifest_path = resources / "language-package.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            catalog_file = resources / "language-catalog.json"
            if (not catalog_file.is_file()
                    or manifest.get("format_version") != 1
                    or manifest.get("char_sha256") != hashlib.sha256(custom_font.read_bytes()).hexdigest()
                    or manifest.get("catalog_sha256") != hashlib.sha256(catalog_file.read_bytes()).hexdigest()):
                raise ValueError("Language package checksum mismatch")
            from .localization import charset_plan, parse_catalog
            catalog = parse_catalog(catalog_file.read_text(encoding="utf-8"))
            plan = charset_plan(catalog)
            expected = {f"{code:02X}": chr(code) for code in range(32, 127)}
            expected.update({f"{code:02X}": glyph for glyph, code in plan.extra_glyphs})
            if manifest.get("languages") != list(catalog.languages) or manifest.get("glyph_map") != expected:
                raise ValueError("Language package glyph map mismatch")
            verify_char_resource(custom_font, {code for _, code in plan.extra_glyphs} | set(range(32, 127)))
            language_catalog = catalog
        bootstrap = inject_multilingual_charset(bootstrap)
        shutil.copyfile(custom_font, road / custom_font.name)
    if (graphical_language_buttons or screen_language_gui) and not localize_story:
        raise ValueError("Graphical language selectors require --localize-story")
    if graphical_language_buttons and screen_language_gui:
        raise ValueError("Choose one graphical language selector mode")
    if localize_story:
        if language_catalog is None:
            raise ValueError("Localized story export requires a verified language package")
        from .story_localization import validate_story_catalog
        from .scumm_assets import scummc_room_source
        if graphical_language_buttons:
            from .scumm_language_buttons import write_button_sprites
        validate_story_catalog(document, language_catalog)
        for room in document.rooms:
            (resources / f"{room.name}.scc").write_text(
                scummc_room_source(room, language_catalog,
                                   graphical_language_buttons=graphical_language_buttons),
                encoding="utf-8")
            if graphical_language_buttons:
                write_button_sprites(room, language_catalog, resources)
    if language_room_probe and (language_catalog is None or len(document.rooms) < 2):
        raise ValueError("Room language probe needs a language package and two rooms")
    if language_catalog is not None:
        bootstrap, header = inject_language_keys(bootstrap, header, language_catalog)
        if language_room_probe:
            bootstrap = inject_language_room_probe(bootstrap, document.rooms[1].name,
                                                   language_catalog)
        if screen_language_gui:
            bootstrap, header = inject_screen_language_verbs(bootstrap, header,
                                                             language_catalog)
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
    options = sys.argv[4:]
    allowed = {"--language-room-probe", "--localize-story", "--language-buttons",
               "--screen-language-gui"}
    if len(sys.argv) < 4 or len(options) != len(set(options)) or set(options) - allowed:
        print("Usage: python -m adventure_studio.scumm_toolchain STORY_BUILD_DIRECTORY SCUMMC_DIRECTORY GAME_OUTPUT_DIRECTORY [--language-room-probe] [--localize-story] [--language-buttons] [--screen-language-gui]")
        return 2
    print(compile_story_game(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]),
                             language_room_probe="--language-room-probe" in options,
                             localize_story="--localize-story" in options,
                             graphical_language_buttons="--language-buttons" in options,
                             screen_language_gui="--screen-language-gui" in options))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

