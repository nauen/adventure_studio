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
   Der Story-Compiler verwendet als Standard `DeterministicStoryImageProvider`,
   damit seine bisherigen Raumhintergründe byteidentisch bleiben. Mit
   `compile_story_to_scumm(story, image_provider=...)` können geprüfte
   Alternativbilder über denselben Compilerpfad eingesetzt werden.
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

`palette_animation.py` implementiert dafür bereits eine **reine Vorschau**:
`PaletteCycle` beschreibt Bereich und Tick-Intervall, `palette_at_tick` liefert
aus der Originalpalette ein deterministisches Ergebnis. Überlappungen und
Zugriffe auf explizit geschützte Farbindizes werden abgewiesen.

Der SCUMM-v6-Exporter übersetzt `RoomAsset.palette_cycles` nun zusätzlich
in ScummC-Deklarationen `cycle NAME = {delay, flags, start, end};`. Das ist
die echte CYCL-Ressource, keine periodische Folge von neu generierten BMPs.
Flags 2 bedeutet Rückwärtsrotation. Das optionale Testspiel aus
`python -m adventure_studio.palette_demo examples/mini_story.json BUILD_DIR`
verwendet vier reservierte blaue Palettenfarben und unveränderte Pixelindices
im Wasserbecken. `scumm_palette_probe.py` prüft im CI-Bildschirmfoto, dass
ein Wasserpixel mindestens zwei Rampenfarben annimmt, während der Himmel
unverändert bleibt. Erst ein erfolgreicher ScummVM-Lauf bestätigt die
Laufzeitkompatibilität; bis dahin ist diese Stufe experimentell.

## Schrittweise Einführung

1. Offline-Fixtures und bisherige Generatoren unverändert weiterverwenden.
2. Bestehende Bildquellen über die Provider-Grenze schrittweise anbinden.
3. Vom Nutzer gelieferte ComfyUI-Workflows analysieren und einen konkreten
   lokalen/gehosteten Adapter mit Timeouts und Fehlerbehandlung bauen.
4. Palettenanimation als eigenen deklarativen Asset-Typ einführen, nach
   Browser-Vorschau und anschließend echtem SCUMM-Laufzeittest.

SCUMM-Kompatibilität und Ausführung in DOS bleiben separat zu prüfende
Gates; ein erfolgreicher ComfyUI-Aufruf ist kein Spielbarkeitsnachweis.
