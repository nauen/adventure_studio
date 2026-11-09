import unittest
import tempfile
from pathlib import Path

from adventure_studio.localization import LanguageCatalog, LocalizedLine
from adventure_studio.scumm_bootstrap import (
    inject_inventory_declarations, inject_inventory_objects, inject_language_keys,
    inject_language_room_probe,
    inject_screen_language_verbs,
    read_icon_ids, retarget_upstream_bootstrap,
)


class BootstrapTests(unittest.TestCase):
    def test_language_selector_uses_persistent_global_state_and_five_key_codes(self):
        languages = ("de", "en", "fr", "ja", "pl")
        catalog = LanguageCatalog("de", languages, (
            LocalizedLine("probe", (
                ("de", "Grüße"), ("en", "Hello"), ("fr", "Bonjour"),
                ("ja", "こんにちは"), ("pl", "Cześć"),
            )),
        ))
        source = (
            "script keyboardHandler(int key) {\n        switch(key) {\n"
            "        }\n    }\n"
            "script gameStart() {\n        setupActors();\n    }\n"
        )
        header = "// Dialog string list\n"
        result, result_header = inject_language_keys(source, header, catalog)
        self.assertEqual(result_header.count("int GameLanguage;"), 1)
        self.assertEqual(result.count("GameLanguage = "), 6)
        self.assertIn("GameLanguage = 25701;\n        setupActors();", result)
        initialization = result.rindex("GameLanguage = 25701;")
        self.assertGreater(initialization, result.index("script gameStart()"))
        for index, language in enumerate(languages, 1):
            code = int.from_bytes(language.encode("ascii"), "big")
            self.assertIn(f"case '{index}':\n            GameLanguage = {code};", result)
        self.assertNotIn("GameLanguage = ", source)
        self.assertIn(r"\x", result)

    def test_opt_in_room_probe_keeps_language_and_repeats_selected_text(self):
        catalog = LanguageCatalog("de", ("de", "pl"), (
            LocalizedLine("probe", (("de", "Grüße"), ("pl", "Cześć"))),
        ))
        source = (
            "script keyboardHandler(int key) {\n        switch(key) {\n"
            "        }\n    }\n"
            "script gameStart() {\n        setupActors();\n    }\n"
        )
        selected, header = inject_language_keys(source, "// Dialog string list\n", catalog)
        changed = inject_language_room_probe(selected, "Cellar", catalog)
        self.assertTrue(changed.startswith("room Cellar;\n"))
        self.assertIn("case '0':\n            startRoom(Cellar);", changed)
        self.assertIn("case '6':\n            if (GameLanguage ==", changed)
        self.assertIn("case '7':\n            if (VAR_MAINMENU_KEY == 0)", changed)
        self.assertIn('egoSay("Menu key disabled")', changed)
        self.assertIn('egoSay("Menu key enabled")', changed)
        self.assertIn("/* pl */", changed)
        self.assertEqual(changed.count("GameLanguage = "), selected.count("GameLanguage = "))
        self.assertEqual(header.count("int GameLanguage;"), 1)
        with self.assertRaisesRegex(ValueError, "already reserved"):
            inject_language_room_probe(changed, "Cellar", catalog)
        with self.assertRaisesRegex(ValueError, "Invalid language probe destination"):
            inject_language_room_probe(selected, "Bad;code", catalog)

    def test_room_probe_uses_distinct_object_line_when_available(self):
        catalog = LanguageCatalog("en", ("en", "pl"), (
            LocalizedLine("room.cellar.goal", (("en", "Goal reached"), ("pl", "Cel"))),
            LocalizedLine("room.harbor.object.key.label", (("en", "key"), ("pl", "klucz"))),
        ))
        source = "script keyboardHandler(int key) {\n        switch(key) {\n        }\n    }"
        selected, _ = inject_language_keys(source + "\n        setupActors();", "// Dialog string list\n", catalog)
        changed = inject_language_room_probe(selected, "Cellar", catalog)
        post_room_probe = changed.split("case '6':", 1)[1].split("break;", 1)[0]
        self.assertIn('egoSay("klucz")', post_room_probe)
        self.assertNotIn('egoSay("Cel")', post_room_probe)

    def test_screen_fixed_gui_uses_persistent_verb_area(self):
        catalog = LanguageCatalog("en", ("de", "en", "fr", "ja", "pl"), (
            LocalizedLine("probe", tuple((code, "Hello") for code in ("de", "en", "fr", "ja", "pl"))),
        ))
        source = (
            "script keyboardHandler(int key) {\n        switch(key) {\n        }\n    }\n"
            "        setupActors();\n        setupVerbs();\n"
            "        dimInt(invObj,8);\n"
            "    // turn on all the verb for the interface\n"
            "        verbsOn = !!show;\n"
            "        // A verb was clicked\n"
        )
        header = "// Dialog string list\n// The inventory arrows\n"
        source, header = inject_language_keys(source, header, catalog)
        fixed, fixed_header = inject_screen_language_verbs(source, header, catalog)
        self.assertIn("verb LanguageJa @ 123;", fixed_header)
        self.assertIn('setVerbName("PL");', fixed)
        self.assertIn("setVerbXY(114,141);", fixed)
        self.assertIn("if(cmd == LanguageDe)", fixed)
        self.assertIn("GameLanguage = 25701;", fixed)
        self.assertIn("refreshLanguageVerbs();", fixed)
        self.assertIn("setVerbOn();", fixed)
        # Every GUI control must select its own persistent language, and the
        # keyboard path must refresh the same selection highlight.
        for index, language in enumerate(catalog.languages, 1):
            code = int.from_bytes(language.encode("ascii"), "big")
            verb = f"Language{language.title()}"
            self.assertIn(f"verb {verb} @", fixed_header)
            self.assertIn(f"if(cmd == {verb}) {{\n            GameLanguage = {code};", fixed)
            self.assertIn(f"if(GameLanguage == {code}) setVerbColor(VERB_HI_COLOR);", fixed)
            key_branch = fixed.split(f"case '{index}':", 1)[1].split("break;", 1)[0]
            self.assertIn(f"GameLanguage = {code};\n            refreshLanguageVerbs();", key_branch)
        self.assertEqual(fixed.count("if(cmd == Language"), len(catalog.languages))
        self.assertEqual(fixed.count("setVerbHiColor(VERB_HI_COLOR);"), len(catalog.languages))
        with self.assertRaisesRegex(ValueError, "upstream screen-language GUI layout"):
            inject_screen_language_verbs("invalid", header, catalog)

    def test_language_selector_rejects_missing_bootstrap_hooks(self):
        catalog = LanguageCatalog("de", ("de",), (
            LocalizedLine("probe", (("de", "Hallo"),)),
        ))
        with self.assertRaisesRegex(ValueError, "Unexpected upstream language selector layout"):
            inject_language_keys("script unrelated() {}", "// Dialog string list", catalog)

    def test_inventory_ids_can_be_read_from_generated_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "inventory-ids.txt"
            manifest.write_text("Badge,Key\n", encoding="ascii")
            self.assertEqual(read_icon_ids(f"@{manifest}"), ("Badge", "Key"))
            self.assertEqual(read_icon_ids(""), ())
            with self.assertRaisesRegex(ValueError, "duplicated"):
                read_icon_ids("Key,Key")
    def test_inventory_resource_is_declared_and_injected(self):
        source = 'room ResRoom {\n    // the inventory icons\n    object axe {}\n}'
        header = 'room ResRoom {\n    // Inventory objects\n    object axe;\n}'
        self.assertIn('states = { { 0, 0, "Inv_Key.bmp" } };', inject_inventory_objects(source, ('Key',)))
        self.assertIn('object KeyIcon;', inject_inventory_declarations(header, ('Key',)))

    def test_inventory_patch_rejects_unknown_layout_and_names(self):
        with self.assertRaisesRegex(ValueError, 'upstream inventory layout'):
            inject_inventory_objects('room ResRoom {}', ('Key',))
        with self.assertRaisesRegex(ValueError, 'identifier'):
            inject_inventory_objects('    // the inventory icons\n', ('Bad;code',))

    def test_nine_inventory_icons_enable_paging_using_existing_arrows(self):
        source = (
            "int* invObj;\nroom ResRoom {\n"
            "    // the inventory icons\n"
            "    script inputHandler(int area,int cmd, int btn) {\n"
            "        // A verb was clicked\n"
            "    }\n"
            "    script setInventoryIcon(int icon, int slot) {\n    }\n"
            "    script inventoryHandler(int obj) {\n        int i, count;\n"
            "        obj = findInventory(hero,i+1);\n"
            "    }\n"
            "    //\n    // Dialogs stuff\n}"
        )
        small = inject_inventory_objects(source, tuple(f"Item{i}" for i in range(8)))
        self.assertNotIn("inventoryPage", small)
        extended = inject_inventory_objects(source, tuple(f"Item{i}" for i in range(9)))
        self.assertEqual(extended.count("object Item8Icon"), 1)
        self.assertIn("int inventoryPage;", extended)
        self.assertIn("findInventory(hero,inventoryPage*8+i+1)", extended)
        self.assertIn("if(inventoryPage * 8 >= getInventoryCount(hero)) inventoryPage = 0;", extended)
        self.assertIn("if(cmd == invUp && inventoryPage > 0) inventoryPage--;", extended)
        self.assertIn("if(cmd == invDown && (inventoryPage + 1) * 8 < getInventoryCount(hero)) inventoryPage++;", extended)
        self.assertLess(extended.index("script inventoryHandler"), extended.index("script inputHandler"))
        with self.assertRaisesRegex(ValueError, "paging layout"):
            inject_inventory_objects(source.replace("findInventory(hero,i+1)", "findInventory(hero,i)"),
                                     tuple(f"Item{i}" for i in range(9)))
    def test_retarget_without_touching_other_logic(self):
        source = "room Road;\nloadRoom(Road);\nlockRoom(Road);\nstartRoom(Road);\nint untouched;\n"
        result = retarget_upstream_bootstrap(source, "Harbor")
        self.assertIn("startRoom(Harbor);", result)
        self.assertIn("int untouched;", result)
        self.assertNotIn("Road", result)

    def test_full_bootstrap_must_preserve_save_menu_enabling(self):
        source = ("room Road;\nloadRoom(Road);\nlockRoom(Road);\n"
                  "startRoom(Road);\nscript main (int bootParam) {\n"
                  "VAR_MAINMENU_KEY = 319;\n}\n")
        self.assertIn("VAR_MAINMENU_KEY = 319;",
                      retarget_upstream_bootstrap(source, "Harbor"))
        with self.assertRaisesRegex(ValueError, "save gate initialization"):
            retarget_upstream_bootstrap(source.replace("319", "0"), "Harbor")

    def test_upstream_drift_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Unexpected upstream"):
            retarget_upstream_bootstrap("room Road;", "Harbor")

    def test_invalid_name_rejected(self):
        with self.assertRaisesRegex(ValueError, "Invalid room"):
            retarget_upstream_bootstrap("", "Harbor); evil()")


if __name__ == "__main__":
    unittest.main()

