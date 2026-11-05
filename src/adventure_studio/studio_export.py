"""Deterministic, explicit SCUMM export for the local Studio UI.

No compiler download, no implicit network requests. The external ScummC tree
is staged in a private temporary directory because the legacy linker uses
working-directory resources and the adapter copies generated inventory icons.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from .scumm_toolchain import compile_story_game
from .story_document import build_story_document, canonical_story_json, parse_story_document


def export_playable(raw: str, scummc_directory: Path, zip_path: Path,
                    runner=subprocess.run) -> Path:
    """Validate, compile, then publish one ZIP; failed builds leave no ZIP."""
    canonical = canonical_story_json(parse_story_document(raw))
    upstream = Path(scummc_directory).resolve()
    if not (upstream / "examples" / "road" / "common.scc").is_file():
        raise ValueError("ScummC directory needs examples/road/common.scc")
    if zip_path.exists():
        raise ValueError("Output ZIP already exists; choose a new name")
    if not zip_path.parent.is_dir():
        raise ValueError("Output ZIP parent directory does not exist")
    with tempfile.TemporaryDirectory(prefix="adventure-studio-scumm-") as tmp:
        staging = Path(tmp)
        build = staging / "build"
        game = staging / "game"
        cloned = staging / "scummc"
        # The upstream ScummC examples are mutable scratch inputs; cloning
        # protects the user's checkout from generated inventory BMPs.
        shutil.copytree(upstream, cloned)
        build_story_document(canonical, build)
        compile_story_game(build, cloned, game, runner=runner)
        files = {"tentacle.000": (game / "tentacle.000").read_bytes(),
                 "tentacle.001": (game / "tentacle.001").read_bytes(),
                 "story.json": canonical.encode("utf-8"),
                 "README.txt": ("Adventure Studio SCUMM v6 research preview\n"
                                "ScummVM: scummvm --path=. tentacle\n"
                                "This uses a temporary DOTT compatibility identity.\n").encode("utf-8")}
        # Fixed file ordering and metadata make the resulting ZIP reproducible.
        temporary_zip = staging / "adventure.zip"
        with ZipFile(temporary_zip, "w", compression=ZIP_DEFLATED) as archive:
            for filename, payload in sorted(files.items()):
                entry = ZipInfo(filename, date_time=(1980, 1, 1, 0, 0, 0))
                entry.compress_type = ZIP_DEFLATED
                entry.external_attr = 0o644 << 16
                archive.writestr(entry, payload)
        shutil.copyfile(temporary_zip, zip_path)
    return zip_path
