# Bildgenerierung und Palettenanimation (Architekturentscheidung)

## Ziel und aktueller Stand

Adventure Studio nimmt storygetriebene Bildaufträge entgegen. Der spätere
Bildanbieter liefert **fertige Pixel-Art in der richtigen Auflösung und
indizierten Farbpalette**. Die vorhandene deterministische Grafikgenerierung
bleibt bis zur Bereitstellung der echten ComfyUI-Workflows der Standard.
Es gibt **noch keine** ComfyUI- oder RunComfy-Verbindung.

## Grenzen und Verantwortlichkeiten

1. Die Story-Schicht gibt stabile Asset-IDs, Beschreibungen und Zielabmessungen
   vor. Identische, bereits freigegebene Assets werden wiederverwendet.
2. Ein austauschbarer `ImageProvider` liefert `IndexedImage` mit Pixelindizes,
   Palette, Abmessungen und `source_id`. Der vorhandene
   `FixtureImageProvider` ist offline und benötigt keine Credentials.
3. Die Validierung kontrolliert Anzahl und Werte der Paletteneinträge,
   Bufferlänge, Pixelindex-Grenzen und Abmessungen. Der Content-Hash deckt
   Pixelindizes und RGB-Palette inklusive deren Reihenfolge ab.
4. Der SCUMM-Exporter verwendet diese Bytes unabhängig vom Ursprung.
   Das Spiel-Build darf keinen generativen Workflow starten.
5. Ein späterer ComfyUI-Adapter sendet einen versionierten Workflow an einen
   konfigurierten lokalen oder gehosteten Dienst, holt das Ergebnis ab und
   prüft es **vor** der Freigabe. Zugangsdaten dürfen weder ins Projektmodell
   noch in Logs oder CI-Artefakte gelangen.

`source_id` bezeichnet bei Testassets nur ihre Herkunft; bei echten
Generierungen sind zusätzlich Workflow-Hash, Modellkennung, Seed, Parameter
und Freigabestatus in einem versionierten Asset-Manifest zu speichern.
Der Bildanbieter selbst bestimmt die Pixel-Art-Auflösung und Farbpalette;
Adventure Studio darf Ergebnisse nicht stillschweigend neu quantisieren.
Ein nicht indiziertes Bild benötigt einen **explizit beauftragten**
Konvertierungsschritt mit eigenem Prüfbericht.

## Palettenanimation

SCUMM v6 bietet mit `setRoomCycleDelay`, `setRoomPalette` und
`setRoomRGBIntensity` relevante Palettenfunktionen. Ein statisches
KI-generiertes Bild wird dadurch jedoch nicht von selbst zu einer guten
Cycle-Animation. Zunächst müssen passende Farbindex-Muster und reservierte
Palettenbereiche **gezielt konstruiert** werden. Geplante Tests: disjunkte
Farbindexbereiche, unveränderte UI-/Figurenfarben, reproduzierbare
Animationsschritte, sichtbare Bildunterschiede im echten ScummVM.

## Schrittweise Einführung

1. Offline-Fixtures und bisherige Generatoren unverändert weiterverwenden.
2. Bestehende Bildquellen über die Provider-Grenze schrittweise anbinden.
3. Vom Nutzer gelieferte ComfyUI-Workflows analysieren und einen konkreten
   lokalen/gehosteten Adapter mit Timeouts und Fehlerbehandlung bauen.
4. Palettenanimation als eigenen deklarativen Asset-Typ einführen, nach
   Browser-Vorschau und anschließend echtem SCUMM-Laufzeittest.

SCUMM-Kompatibilität und Ausführung in DOS bleiben separat zu prüfende
Gates; ein erfolgreicher ComfyUI-Aufruf ist kein Spielbarkeitsnachweis.
