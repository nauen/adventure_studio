# Versioniertes SCUMM-Projektformat (experimentell)

`adventure_studio.scumm_project` ist die erste datenbasierte Schnittstelle
zwischen Adventure-Konfiguration und deterministischem SCUMM-Exporter.

- `format_version = 1` und `id` identifizieren das Projekt.
- `rooms` enthalten Raumgeometrie, 8-Bit-Palette, Pixelressourcen,
  Hotspots, Zustandswechsel, Raumausgänge und das explizite Spielziel.
- Pixelressourcen sind vorerst als Base64-Daten gespeichert. Das ist ein
  **technisches Zwischenformat**, kein Autoren- oder KI-Chat-Format.
- Ungültige Referenzen, fremde Felder, ausführbare Skriptfelder, ungültige
  Bildformate und nicht unterstützte Versionsnummern werden abgewiesen.
- Vor der Erstellung von Spieldateien werden alle Raumreferenzen geprüft.

## Verwendung

Aus einem validierten Projekt lässt sich ein kanonisches JSON-Dokument
erzeugen. Ein vorhandenes Dokument kann anschließend kompiliert werden:

```bash
PYTHONPATH=src python -m adventure_studio.scumm_project project.json build/game
```

Der aktuelle Export erzeugt ScummC-Raumquellen und BMP-Ressourcen. Der
experimentelle GitHub-Workflow übernimmt weiterhin die externe ScummC-
Kompilierung und das Linking. Weder die private Game-Logik noch KI-Antworten
werden direkt als SCUMM-Skript eingebettet.

## Akzeptanztests

- Kanonisches JSON wird ohne Änderungen eingelesen und wieder ausgegeben.
- Zwei verschiedene Abenteuerkonfigurationen erzeugen unterschiedliche,
  jeweils deterministische Dateien mit denselben Generatorbausteinen.
- Bei ungültigen Raumverweisen wird **vor** der Dateierzeugung abgebrochen.

Nächste Architekturaufgabe: die erzählerischen `Story`-Objekte in dieses
Projektformat überführen und Bild-, Layout- und Kostüm-Erzeugung getrennt
konfigurieren, damit Autoren keine Base64-Daten sehen müssen.

## Erste Story-Übersetzung

`adventure_studio.story_to_scumm.compile_story_to_scumm(story)` übersetzt einen
bewusst begrenzten Teil des erzählerischen `Story`-Modells direkt in ein
`GameDocument`: ein Kapitel, zwei bis drei linear verbundene Szenen, ein bis
drei Gegenstände insgesamt, eine oder zwei aufeinanderfolgende Türen und ein
Zielraum. Bei mehreren benötigten Gegenständen wird die erste Voraussetzung
als Werkzeug verwendet; die übrigen müssen bereits im Inventar sein.
Dekorative Gegenstände bleiben als Hotspots erhalten.
Die grafische Darstellung ist vorerst eine klar erkennbare,
deterministisch erzeugte Platzhaltergrafik; keine KI-Bildgenerierung.

Weitere Figuren, verzweigte Puzzles oder komplexe Szenenfolgen werden
explizit abgewiesen. Sie werden **nicht** stillschweigend aus der Geschichte
entfernt. Story-Referenzen und Softlocks werden bereits vor dem SCUMM-Export
mit dem deterministischen Rätsellöser überprüft.

### Direkter Story-Build

`examples/mini_story.json` ist eine vollständige, versionierte Story-Datei,
die keine Engine-Quellen oder Grafikdaten enthält. Aus ihr entsteht ein
SCUMM-Projekt inklusive Inventarmanifest und BMP-Ressourcen:

```bash
PYTHONPATH=src python -m adventure_studio.story_document examples/mini_story.json build/story
```

Die GitHub-Action **Experimental SCUMM v6 compatibility probe** baut zusätzlich
dieses Story-Beispiel mit ScummC, prüft Start, Kamerabild, Inventar-Aufnahme,
Türöffnung und Raumwechsel in einer echten ScummVM und stellt die Dateien als
`story-playable-preview` bereit (grüner Lauf #42021639269).
Die externe Compiler-/Linker-Anbindung ist in `scumm_toolchain.py` gekapselt.
Sie liest Raumliste und Inventar-IDs aus dem validierten Projekt, statt
Raumnamen oder Spielgegenstände im GitHub-Workflow fest einzutragen.
Das bleibt ein experimenteller DOTT-Kompatibilitäts-Build, kein eigenständiger
ScummVM-Spielidentifikator. Auch ein, zwei und drei Inventarvoraussetzungen
sowie die lineare Drei-Raum-Kette inklusive Rückweg wurden inzwischen in der
echten ScummVM gespielt und visuell geprüft (zuletzt CI #42029750897).

### Story-Rezepte (Format v2, zunächst nur Modell und Solver)

`format_version: 2` ergänzt das Pflichtfeld `story.recipes`. Ein Rezept ist
reine deklarative Datenstruktur mit `id`, `title`, zwei `ingredients` und
`result_item_id`. Zutaten sind `pickup`- oder bereits hergestellte `crafted`-
Gegenstände; das Ergebnis ist ein `crafted`-Gegenstand. Beim Kombinieren
werden beide Zutaten aus dem Inventar entfernt, das Ergebnis wird hinzugefügt.
Einmal eingesammelte Zutaten erscheinen danach nicht wieder am Boden.

`examples/recipe_story.json` enthält eine kaputte Küche, eine verschimmelte
Ananas, eine Flasche und ein daraus herstellbares Rätselobjekt. Der reine
Rätsellöser prüft Erreichbarkeit und Sackgassen:

```bash
PYTHONPATH=src python -m adventure_studio.story_document examples/recipe_story.json --validate-only
```

Bestehende Story-Dateien ohne Rezepte bleiben im strikten Format v1 und
behalten ihren unveränderten kanonischen JSON-Aufbau. Rezept-Dateien werden
als v2 serialisiert. Der begrenzte Export mit zwei Zutaten, einem Ergebnis
und einer Zieltür wurde inzwischen in ScummVM integriert und getestet.

Die Konsolidierung von KI-Änderungen entfernt jetzt unreferenzierte technische
`pickup`-Gegenstände aus dem vorgeschlagenen Story-Modell und meldet ihre IDs
im Feld `consolidated` des Änderungsberichts. Bewusst als `decoration`
modellierte Erzähldetails bleiben erhalten. Ein loses Sammelobjekt ohne
Mechanik wird im derzeitigen Modell nicht als `pickup` unterstützt.

### Objektpositionen (Story-Format v3)

`format_version: 3` enthält zusätzlich `story.placements`, eine Liste mit
stabilen Gegenstandsreferenzen und Ganzzahlkoordinaten. Beispiel:

```json
{"item_id":"Key","x":270,"y":130}
```

Die Position ist optional; ohne sie bleibt die bestehende automatische
Platzierung unverändert. Einträge gelten nur für physische `pickup`- und
`decoration`-Gegenstände, nicht für erzeugte Inventarergebnisse. Jedes Item
darf höchstens eine Position besitzen. Modell und SCUMM-Exporter prüfen
Referenzen sowie die tatsächlichen Raumgrenzen, einschließlich 320-Pixel-
Zielräumen. Änderungen laufen als `PutEntity("placement", Placement(...))`
durch dieselbe atomare Story- und Konsolidierungspipeline. Das Gradio Studio
kann Positionen anhand von Klickkoordinaten oder X/Y-Feldern vorschlagen und
erst nach Diff und Bestätigung übernehmen.

Storys der Versionen 1 und 2 bleiben ohne Migration lesbar. Die kanonische
Ausgabe verwendet erst dann v3, wenn mindestens eine Position definiert ist.
