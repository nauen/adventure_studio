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

Diese Funktionen **erzeugen derzeit weder eine .CHAR-Schriftdatei noch ein
spielbares mehrsprachiges SCUMM-Spiel**. Das Unicode-zu-Glyphen-Mapping ist
eine Anforderung an den späteren Font-Compiler, nicht der Beweis, dass
ScummVM die Zeichen richtig zeichnet. Insbesondere für Japanisch sind
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
