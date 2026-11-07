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
    # ScummVM v4+ rejects native saves when VAR_MAINMENU_KEY is disabled.
    # The actual upstream example initializes it to 319 in main(). Keep
    # that invariant when adapting a full upstream script for the fixture.
    if "script main (int bootParam)" in source and source.count("VAR_MAINMENU_KEY = 319;") != 1:
        raise ValueError("Upstream SCUMM main-menu save gate initialization changed")
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
    source = source.replace(marker, marker + definitions, 1)
    if len(icon_ids) <= 8:
        return source

    # The upstream Road GUI defines eight inventory verbs and two arrow
    # controls, but its inventory handler always renders slots 1..8. Extend
    # only larger games with a page offset and wire the existing arrows.
    global_marker = "int* invObj;\n"
    inventory_marker = "    script inventoryHandler(int obj) {\n"
    lookup_marker = "findInventory(hero,i+1)"
    input_marker = "        // A verb was clicked\n"
    if (source.count(global_marker) != 1 or source.count(inventory_marker) != 1
            or source.count(lookup_marker) != 1 or source.count(input_marker) != 1):
        raise ValueError("Unexpected upstream inventory paging layout")
    source = source.replace(global_marker, global_marker + "int inventoryPage;\n", 1)
    source = source.replace(inventory_marker,
                            inventory_marker +
                            "        if(inventoryPage * 8 >= getInventoryCount(hero)) inventoryPage = 0;\n", 1)
    source = source.replace(lookup_marker, "findInventory(hero,inventoryPage*8+i+1)", 1)
    source = source.replace(input_marker,
                            "        if(cmd == invUp || cmd == invDown) {\n"
                            "            if(cmd == invUp && inventoryPage > 0) inventoryPage--;\n"
                            "            if(cmd == invDown && (inventoryPage + 1) * 8 < getInventoryCount(hero)) inventoryPage++;\n"
                            "            inventoryHandler(0);\n"
                            "            return;\n"
                            "        }\n" + input_marker, 1)
    return source


def inject_multilingual_charset(source: str) -> str:
    """Use a verified custom CHAR for dialogue; preserve GUI font slot one.

    The upstream Road example has two text fonts and switches between them
    with initCharset(). Both must use the same byte-to-glyph mapping.
    """
    for original in ('chset chtest = "vera.char";',
                     'chset dialogCharset = "vera-small.char";'):
        if source.count(original) != 1:
            raise ValueError(f"Unexpected upstream charset layout: {original}")
        source = source.replace(original,
                                original.split(' = ')[0] + ' = "multilingual-font.char";', 1)
    return source


def inject_language_keys(source: str, header: str, catalog) -> tuple[str, str]:
    """Add an in-game keyboard language probe using one global SCUMM variable.

    Keys 1..9 choose a language and display the same translated sample line.
    This probes actual byte rendering, not yet localization of story objects.
    """
    from .localization import charset_plan, encode_scumm_literal, validate_catalog

    validate_catalog(catalog)
    if len(catalog.languages) > 9 or any(len(lang) != 2 for lang in catalog.languages):
        raise ValueError("Keyboard language probe supports one to nine two-letter languages")
    if not catalog.lines:
        raise ValueError("Language selector requires at least one translated line")
    declaration = "int GameLanguage;\n"
    header_marker = "// Dialog string list"
    switch_marker = "script keyboardHandler(int key) {\n        switch(key) {"
    init_marker = "        setupActors();"
    for body, marker in ((header, header_marker),
                         (source, switch_marker), (source, init_marker)):
        if body.count(marker) != 1:
            raise ValueError(f"Unexpected upstream language selector layout: {marker}")
    header = header.replace(header_marker, declaration + header_marker, 1)
    sample = catalog.lines[0]
    plan = charset_plan(catalog)
    lines = []
    for index, language in enumerate(catalog.languages, 1):
        code = int.from_bytes(language.encode("ascii"), "big")
        value = dict(sample.translations)[language]
        lines.extend((f"        case '{index}':",
                      f"            GameLanguage = {code};",
                      f"            egoSay({encode_scumm_literal(value, plan)});",
                      "            break;"))
    source = source.replace(switch_marker, switch_marker + "\n" + "\n".join(lines), 1)
    initial = int.from_bytes(catalog.source_language.encode("ascii"), "big")
    source = source.replace(init_marker, f"        GameLanguage = {initial};\n" + init_marker, 1)
    return source, header



def inject_language_room_probe(source: str, destination: str, catalog) -> str:
    """Add opt-in test keys: room 0, language 6, save-gate state 7.

    This is only for the runtime fixture, never for regular game controls.
    The source must already contain the language keyboard selector.
    """
    from .localization import scumm_language_dispatch, validate_catalog

    validate_catalog(catalog)
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", destination):
        raise ValueError("Invalid language probe destination")
    marker = "script keyboardHandler(int key) {\n        switch(key) {"
    if source.count(marker) != 1:
        raise ValueError("Missing language keyboard handler")
    if any(source.count(f"case '{key}':") for key in ("0", "6", "7")):
        raise ValueError("Language probe keys already reserved")
    if not catalog.lines:
        raise ValueError("Language probe needs a translated line")
    # After the room transition, choose a line that differs from the new
    # room's entry goal. Reprinting the goal produced identical screenshots
    # and could not establish whether the keyboard handler ran at all.
    probe_id = next((line.id for line in catalog.lines
                     if line.id.endswith(".object.key.label")), catalog.lines[0].id)
    dispatch = scumm_language_dispatch(catalog, probe_id)
    branches = "".join("            " + line + "\n" for line in dispatch.splitlines())
    probe = (
        "\n        case '0':\n"
        f"            startRoom({destination});\n"
        "            break;\n"
        "        case '6':\n"
        + branches
        + "            break;\n"
        "        case '7':\n"
        "            if (VAR_MAINMENU_KEY == 0) egoSay(\"Menu key disabled\");\n"
        "            else egoSay(\"Menu key enabled\");\n"
        "            break;"
    )
    source = source.replace(marker, marker + probe, 1)
    return f"room {destination};\n" + source


def inject_screen_language_verbs(source: str, header: str, catalog) -> tuple[str, str]:
    """Add screen-fixed language verbs to ScummC's shared bottom GUI.

    Unlike room objects these verbs are positioned in the permanent verb
    interface and remain reachable when the camera scrolls. The adapter is
    deliberately tied to the validated upstream road bootstrap markers.
    """
    from .localization import validate_catalog

    validate_catalog(catalog)
    if not (1 <= len(catalog.languages) <= 5):
        raise ValueError("Screen language GUI supports one to five languages")
    verbs = [(f"Language{language.title()}", language,
              int.from_bytes(language.encode("ascii"), "big"))
             for language in catalog.languages]
    markers = (
        (header, "// The inventory arrows\n"),
        (source, "        dimInt(invObj,8);\n"),
        (source, "    // turn on all the verb for the interface"),
        (source, "        verbsOn = !!show;\n"),
        (source, "        // A verb was clicked\n"),
        (source, "        setupVerbs();\n"),
    )
    if any(body.count(marker) != 1 for body, marker in markers):
        raise ValueError("Unexpected upstream screen-language GUI layout")
    header = header.replace(
        "// The inventory arrows\n",
        "".join(f"verb {name} @ {120 + index};\n"
                for index, (name, _lang, _code) in enumerate(verbs))
        + "// The inventory arrows\n", 1)
    setup = "".join(
        f"        setCurrentVerb({name});\n"
        f"        initVerb();\n"
        f'        setVerbName("{language.upper()}");\n'
        f"        setVerbXY({10 + index * 26},141);\n"
        "        setVerbColor(VERB_COLOR);\n"
        "        setVerbHiColor(VERB_HI_COLOR);\n"
        for index, (name, language, _code) in enumerate(verbs))
    source = source.replace("        dimInt(invObj,8);\n",
                            "        dimInt(invObj,8);\n" + setup, 1)
    refresh = (
        "    script refreshLanguageVerbs() {\n"
        + "".join(
            f"        setCurrentVerb({name});\n"
            f"        if(GameLanguage == {code}) setVerbColor(VERB_HI_COLOR);\n"
            "        else setVerbColor(VERB_COLOR);\n"
            "        redrawVerb();\n"
            for name, _language, code in verbs)
        + "    }\n\n")
    source = source.replace("    // turn on all the verb for the interface",
                            refresh + "    // turn on all the verb for the interface", 1)
    show = "".join(
        f"        setCurrentVerb({name});\n"
        "        if(show) setVerbOn();\n"
        "        else setVerbOff();\n"
        "        redrawVerb();\n"
        for name, _language, _code in verbs)
    source = source.replace("        verbsOn = !!show;\n", show + "        verbsOn = !!show;\n", 1)
    clicks = "".join(
        f"        if(cmd == {name}) {{\n"
        f"            GameLanguage = {code};\n"
        "            refreshLanguageVerbs();\n"
        "            return;\n"
        "        }\n"
        for name, _language, code in verbs)
    source = source.replace("        // A verb was clicked\n",
                            clicks + "        // A verb was clicked\n", 1)
    source = source.replace("        setupVerbs();\n",
                            "        setupVerbs();\n        refreshLanguageVerbs();\n", 1)
    for _name, _language, code in verbs:
        marker = f"            GameLanguage = {code};\n            egoSay("
        if source.count(marker) != 1:
            raise ValueError("Unexpected keyboard branch for screen-language GUI")
        source = source.replace(marker,
                                f"            GameLanguage = {code};\n"
                                "            refreshLanguageVerbs();\n            egoSay(", 1)
    return source, header


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

