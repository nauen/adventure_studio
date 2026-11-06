# Sprachumschaltung in einem SCUMM-v6-Spiel

## Ziel und belegte Grundlagen

Ein einziges verlinktes SCUMM-Spiel enthält deutsche, englische, französische,
polnische und japanische Texte. Die Sprache wird im Spiel über eine globale
Variable gewählt, nicht durch mehrere getrennte Downloads.

- ScummC unterstützt globale Integer, `if`-Verzweigungen und Textliterale.
- Text ist im Skript-Bytecode eingebettet; `\\xNN` kodiert einzelne Bytes.
- `chset`-Ressourcen und der ScummC-`char`-Konverter sind vorhanden.
- Ein Bytewert ist **kein Unicode-Zeichen**: Ein exakt passender Zeichensatz
  muss mit dem Spiel ausgeliefert und im Interpreter geladen werden.
- `0xfe` und `0xff` haben in SCUMM-Strings Steuerfunktion und dürfen nicht
  unkontrolliert als Glyphen verwendet werden.

Quellen: [ScummC-Grammatik](https://github.com/AlbanBedel/scummc/wiki/ScummC-Grammar),
[SCUMM-Strings](https://github.com/AlbanBedel/scummc/wiki/Scumm-6-strings),
[ScummVM-Zeichensatzimplementierung](https://github.com/scummvm/scummvm/blob/master/engines/scumm/charset.cpp).

## Implementiert: format_version 1 des Übersetzungskatalogs

`adventure_studio.localization` ist derzeit eine eigenständige, strikt
validierte Datenmodellgrenze. Alle Werte sind Unicode und haben stabile
Text-IDs. Jede Übersetzung muss existieren; sonst schlägt die Prüfung fehl.
Die kanonische JSON-Darstellung ist reproduzierbar.

`charset_plan()` erstellt eine Liste der benötigten zusätzlichen Glyphen.
ASCII bleibt identisch; höchstens 126 zusätzliche Unicode-Zeichen werden
deterministisch auf reservierte Bytecodes `0x80..0xfd` abgebildet.
`encode_scumm_literal()` erzeugt daraus ScummC-`\\xNN`-Literale.

`scumm_language_dispatch()` erzeugt bedingte `egoSay`-Anweisungen für
`GameLanguage`, wobei die Zahl der beiden ISO-639-1-Buchstaben als stabiler
16-Bit-Wert verwendet wird (statt von einer Position in der Sprachenliste
abzuhängen). Unbekannte Sprachwerte fallen auf die Quellsprache zurück.

Diese Funktionen allein erzeugen noch kein Spiel. Die nachgelagerte
`scumm_language_package`- und `scumm_toolchain`-Integration verlinkt jedoch
inzwischen eine reale .CHAR-Ressource und ein spielbares mehrsprachiges
SCUMM-v6-Adventure. Das beweist weiterhin **nicht**, dass alle Glyphen in
ScummVM richtig und lesbar gezeichnet werden. Insbesondere für Japanisch sind
Zeichenbreite und die Zahl verschiedener Schriftzeichen offene Grenzen.

## Erste echte CHAR-Ressource (experimentell)

`scumm_font.py` erzeugt ein 3-Farben-BMP mit Rahmen um jeden Byte-Slot,
wie es der ursprüngliche ScummC-`char -ibmp`-Importer erwartet. Jeder Glyph
wird aus einer vorhandenen Latin- bzw. japanischen TrueType/OpenType-Schrift
gerendert; die `cmap`-Tabelle wird vorher geprüft. Nicht vorhandene Glyphen
werden niemals durch ein Ersatzkästchen ersetzt. Über den unabhängigen
Workflow `font-smoke.yml` wird ScummC gebaut und dieses BMP mit dem echten
`char`-Konverter in eine `.char`-Datei umgewandelt. Der Test prüft danach
die Ressourcensignatur und die Slot-Belegung, legt Quell-BMP, CHAR-Datei
und Glyphenliste als GitHub-Artefakte ab.

Die Probe umfasst explizit Deutsch, Englisch, Französisch, Polnisch und
Japanisch (`examples/language_probe.json`). Eine bestandene CHAR-Konvertierung
ist **noch kein Nachweis für korrekte Darstellung in ScummVM**. Dieser
folgt erst, wenn die Ressourcen auch ins verlinkte Spiel eingebunden und
Pixel-/Texterkennungsprüfungen durchgeführt wurden.

## Opt-in für den tatsächlichen Spiel-Link (vorbereiteter Adapter)

Der deterministische Befehl
`python -m adventure_studio.scumm_language_package CATALOG LATIN_FONT CJK_FONT SCUMMC_CHAR RESOURCES`
erstellt den kanonischen Katalog, die kompilierte CHAR-Datei, den BMP-Quellfont,
den Glyphenbericht und `language-package.json` mit SHA-256-Prüfsummen und
exakter Byte-/Glyphenzuordnung. Der GitHub-Font-Workflow produziert jetzt
dieses komplette Paket als Artefakt. Die Generierung erfolgt zuerst in einem
temporären Verzeichnis; bei einem Compiler- oder Fontfehler wird kein
unvollständiges Paket veröffentlicht.

Wenn die bereits geprüfte `multilingual-font.char` im Build-Verzeichnis unter
`resources/multilingual-font.char` vorhanden ist, prüft `scumm_toolchain`
den CHAR-Header und alle ASCII-Glyph-Slots **vor** dem Kompilieren. Danach
ersetzt der Adapter beide Text-Zeichensatzreferenzen (`chtest` und
`dialogCharset`) des externen ScummC-Demobootstraps durch diese Datei.
Der GUI-Zeichensatz an festem Slot 1 bleibt unangetastet. Ohne die optionale
Datei wird das bisherige Bootstrap unverändert verwendet. Ein defekter CHAR
führt zum Abbruch statt zu einem stillen Rückfall auf die Demo-Schrift.
Wenn die Paketmanifest-Datei vorliegt, prüft der Linker-Adapter zusätzlich
die SHA-256-Prüfsummen und die Zeichenbelegung gegen den Katalog.

Mit einem geprüften Sprachpaket fügt der Bootstrap-Adapter jetzt eine
globale SCUMM-Variable `GameLanguage` und eine begrenzte Tastaturauswahl
(`1` bis `9`, alphabetisch sortierte Sprachcodes) hinzu. Beim Spielstart
wird die Quellsprache initialisiert; eine Ziffer ändert die Sprache und
gibt als kontrollierte Laufzeitprobe die erste übersetzte Katalogzeile
mit den Bytewerten des gebündelten Fonts aus. Die Variable gehört zum
Spielzustand und wird beim normalen Raumwechsel nicht neu gesetzt.
Dies ist **noch kein grafisches Auswahlmenü**. Ein vollständig ausgefüllter
Story-Katalog kann mit `--localize-story` nun Dialoge, Objekte,
Beschreibungen und Rätseltexte in SCUMM verzweigen. ScummC-Kompilierung
und ScummVM-Start des Sprachpfads sind im isolierten GitHub-Lauf belegt;
die Glyphenlesbarkeit ist weiterhin offen.

Der unabhängige GitHub-Workflow `language-runtime.yml` baut dafür den
unveränderten ScummC, erzeugt ein echtes Sprachpaket, verlinkt damit
ein kleines Adventure und startet es in stock ScummVM. Nach den Tasten
`1` (Deutsch), `4` (Japanisch) und `5` (Polnisch) werden Screenshots und
Engine-Log abgelegt. Der Test prüft zunächst, ob der Interpreter läuft
und die Screenshots erzeugt. **Die Glyphen selbst werden noch nicht durch
OCR oder Pixelreferenzen verifiziert**; diese Schranke bleibt offen. Der
Laufzeitbericht misst zusätzlich Bildunterschiede zwischen deutscher,
japanischer und polnischer Auswahl sowie nach dem Raumwechsel. Pixelunterschiede
sind Diagnosedaten und ausdrücklich kein Zeichen-/Spracherkennungsbeweis.
Die Nach-Raumwechsel-Taste `6` gibt nun einen anderen lokalisierten
Objektnamen aus als die Zielmeldung beim Raumeintritt. Bleibt der sichtbare
Bildschirm darauf unverändert, schlägt die Laufzeitprobe fehl; dadurch kann
ein bisher pixelgleiches, nicht aussagekräftiges Bildpaar nicht mehr als
bestanden durchgehen.

Die ersten tatsächlichen Screenshots zeigten überlappende UI-Zeilen mit der
ursprünglichen 14-Pixel-Schrift. Daher verwendet der SCUMM-Font-Generator
nun 9-Pixel-Glyphen mit 11×12 nutzbaren Pixeln und weiterhin einem
getrennten Führungsrand für den ScummC-Importer. Die kleinere Schrift beseitigte die beobachtete Zeilenüberlagerung.
Ein grüner Prozess-Exit allein ist ausdrücklich kein Beweis für korrekt
dargestellte Sonderzeichen; die Glyphenlesbarkeit bleibt separat zu prüfen.

**Noch nicht abgeschlossen:** Der Standard-Story-Export liefert den
Übersetzungskatalog und die CHAR-Datei noch nicht automatisch gemeinsam aus.
Die lokalisierte Kompilierung ist explizit zuschaltbar, aber eine grafische
Sprachauswahl, der Pixelnachweis polnischer bzw. japanischer Glyphen und der Test
von Sprachwechseln im selben Raum stehen noch aus.

## Optionaler Story-Text-Compiler (vor Runtime-Abnahme)

`story_localization.py` inventarisiert stabile Text-IDs für Objektbezeichnungen,
Beschreibungen, Dialoge, Auswahltexte, Rätselantworten und Zieltexte. Das
Gradio-Studio kann eine fünfsprachige, bewusst unvollständige Vorlage als JSON
ausgeben und einen ausgefüllten Katalog gegen die aktuelle Story prüfen.
Der Übersetzungsentwurf übernimmt eindeutig zuordenbare Originaltexte aus dem
Unicode-Storymodell (etwa Gegenstandsnamen und Dialogzeilen). Synthetische
Compilertexte und mehrdeutige ASCII-Normalisierungen bleiben in der aktuellen
Adaptergrenze als technische Texte erhalten. Die ursprüngliche Story selbst
wird dabei nicht verändert.
Fehlende Sprachfelder bleiben `null`; ein unvollständiger Katalog besteht
weder die strikte Validierung noch die Zeichensatzbedarfsprüfung.

Mit dem expliziten Compiler-Schalter `--localize-story` werden
`egoSay`-Zeilen als bedingte SCUMM-v6-Sprachzweige erzeugt. Voraussetzung
ist ein vollständiger Katalog mit exakt passenden Originaltexten und einem
bereits geprüften CHAR-Paket. Der normale Export bleibt unverändert.
Objektnamen werden beim Betreten eines Raums über `setObjectName` an den
Sprachzustand angepasst. Ein kleines raumlokales `watchLanguage`-Skript
beobachtet zusätzlich `GameLanguage` und setzt die Namen bei einem
Sprachwechsel im bereits geladenen Raum neu. Die Laufzeitkompilierung dieses
Monitor-Skripts wird im GitHub-ScummVM-Test abgesichert. Die bislang fest codierte
Tür-Fehlermeldung hat nun eine eigene stabile Übersetzungs-ID. Die Darstellung
bleibt gesondert im Interpreter zu verifizieren.

`story_language_fixture.py` erzeugt einen begrenzten Integrationskatalog,
in dem **alle neun Texte** der Zeichentest-Geschichte in fünf Sprachen
vorliegen. Für den echten ScummVM-Test wird eine separate englische
`mini_story_language_en.json` mit **sieben** sichtbaren Story-Texten verwendet;
auch diese sind in allen fünf Sprachen vollständig übersetzt. Objektnamen,
Beschreibungen, Tür-/Rätselantworten und Zieltexte sind abgedeckt.
Das sind vollständige Übersetzungen **dieser kleinen Testspiele**, keine
automatische Übersetzung eines beliebigen Nutzer-Adventures. Der isolierte
`language-runtime.yml`-Workflow soll damit den echten ScummC-Compiler,
ScummVM und Raumwechsel prüfen; ein grüner Python-Test ersetzt diesen
Engine-Nachweis nicht.


## Experimentelle anklickbare Sprachauswahl

`scumm_toolchain --localize-story --language-buttons` ergänzt jeden Raum
um fünf anklickbare, per 8-Bit-BMP gezeichnete Sprachfelder `DE`, `EN`,
`FR`, `JA` und `PL`. Jeder Raum erhält eigene Bitmap-Ressourcen in seiner
vorhandenen Palette; ein `WalkTo` auf das Feld setzt `GameLanguage`.
Das `watchLanguage`-Skript aktualisiert die Markierung des aktiven Feldes
und die übersetzten Objektnamen. Ohne den expliziten Schalter bleibt
der bisherige Build unverändert. Die Zifferntasten bleiben während der
Erprobung zusätzlich verfügbar.

Diese erste Fassung verwendet **Raumobjekte**, keine dauerhaft am
Bildschirm fixierte GUI. Sie kann bei horizontal scrollenden Räumen aus
dem sichtbaren Bereich wandern. Die ScummC-Kompilierung, tatsächliche
Anklickbarkeit und Lesbarkeit der kleinen Bitmap-Beschriftungen müssen
im Runtime-Test beziehungsweise anhand der Screenshots geprüft werden.

## Verbindliche Kompatibilitäts-Gates vor Aktivierung im Spiel-Export

1. ScummC kompilieren und einen minimalen Raum mit `GameLanguage` und fünf
   Textzweigen verlinken; alle fünf Sprachpfade in stock ScummVM auslösen.
2. Eine CHAR-Ressource erzeugen, deren Bytepositionen mit `charset_plan()`
   übereinstimmen. Automatisch die tatsächlich renderbaren Glyphen prüfen.
3. Im virtuellen Bildschirm Deutsch (Umlaute), Französisch (Akzente),
   Polnisch (ą, ę, ł, ó, ś, ź, ż) und Japanisch (Kana und Kanji) pixelgenau
   überprüfen. Eine fehlende Glyphe muss den Build als fehlgeschlagen markieren.
4. Prüfen, ob 16-Bit-Sprachkennungen im SCUMM-Interpreter als vorzeichenlose
   Werte und im Savegame erhalten bleiben; Language-Auswahl nach Save/Load
   und Raumwechsel wiederholen.
5. Sprachausgabe erst nach separaten VOC-/Synchronisations-Tests zuschalten.
6. Test auf einer alten, festgelegten ScummVM-Version wiederholen; DOS erst
   dann als kompatibles Ziel ausweisen, wenn dort der gleiche Ablauf besteht.

Die bisherigen Python-Tests prüfen Datenintegrität, deterministische Bytes,
Injektionsschutz, Sprachfallback und die Kapazitätsgrenze – **nicht** die
visuelle Ausgabe von Polnisch/Japanisch in ScummVM.
