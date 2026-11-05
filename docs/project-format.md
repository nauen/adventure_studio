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

`adventure_studio.story_to_scumm.compile_story_to_scumm(story)` übersetzt nun
einen bewusst begrenzten Teil des erzählerischen `Story`-Modells direkt in ein
`GameDocument`: ein Kapitel, zwei Szenen, ein bis drei aufnehmbare Gegenstände,
ein Inventar-Tür-Rätsel und ein Zielraum. Bei mehreren benötigten Gegenständen
wird die erste Voraussetzung als Werkzeug verwendet; die übrigen müssen bereits
im Inventar sein. Dekorative Gegenstände bleiben als Hotspots erhalten.
Die grafische Darstellung ist vorerst eine klar erkennbare,
deterministisch erzeugte Platzhaltergrafik; keine KI-Bildgenerierung.

Weitere Figuren, mehrere unabhängige Puzzles oder komplexe Szenenfolgen werden
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
ScummVM-Spielidentifikator. Für die Story-Variante ist damit ein vollständiges
Ein-Schlüssel-Rätsel nachgewiesen; die Mehr-Gegenstand-Bedingungen sind bisher
deterministisch getestet, aber noch nicht im ScummVM-Gameplay durchgespielt.
