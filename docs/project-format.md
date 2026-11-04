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
