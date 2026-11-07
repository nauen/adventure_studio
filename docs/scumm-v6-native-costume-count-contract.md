# Native SCUMM-v6 COST-Assets und explizite COUNT-Ereignisse

Stand 2026-11-07. **Erster Ressourcenbaustein für P0.5; kein fertig
in ScummVM ausgeführtes Actor-Timing.**

## Quellenvertrag

- ScummC [`cost_parse.y`](https://github.com/AlbanBedel/scummc/blob/master/cost_parse.y)
  erzeugt den `COST`-Chunk aus `.scost`. Das Kommando `COUNT` schreibt den
  nativen Token `0x7C` in die Costume-Sequenz, statt ein Bild darzustellen.
  `SHOW`, `HIDE`, `NOP` sind weitere explizite Costume-Kommandos.
- ScummC `man/tools/cost.xml`: `cost` erzeugt standardmäßig **v6 COST**;
  `-akos` wäre eine andere, hier ausdrücklich nicht verwendete v7-Ausgabe.
  Die Argumente `-o`, `-I` und `.scost` sind dokumentiert.
- ScummC `examples/road/devil.scost` und `examples/openquest/costumes/*.scost`
  belegen die Syntax `palette([...]);`, `picture` mit BMP und Position,
  `limb body;` sowie `anim NAME @ INDEX` mit Richtungen N/E/S/W.
- ScummVM `engines/scumm/costume.cpp`: Der Costume-Interpreter aktualisiert
  bei einer `COUNT`-Operation den Animationszähler des Actors. Es gibt
  **keine automatische Ereigniszahl für jeden gerenderten Frame**.

## Implementiertes Modell

- `CostumeAsset` besitzt eine indizierte Palette, beliebig viele
  `CostumeFrame`-Einträge und beliebig viele benannte `CostumeAnimation`-Einträge.
- Eine Animation enthält pro vorhandener Richtung eine geordnete Liste von
  Frames und nativen Steuerkommandos. `COUNT` kann mehrfach an beliebigen
  Stellen stehen. `loop` steuert das native `!LOOP`-Flag.
- Strikte Validierung verhindert fehlende Frame-Referenzen, ungültige
  Richtungskombinationen, doppelte IDs und ungültige Palette-/BMP-Werte.
- `write_costume_sources` schreibt deterministisch `.scost` und unabhängige
  8-Bit-BMPs. Es erzeugt **keinen eigenen Interpreter**. Erst der originale
  ScummC-`cost`-Compiler erzeugt den binären `COST`-Chunk.
- Das isolierte Testasset `NativeGesture` enthält vollständige N/E/S/W-
  `walk`, `stand` und `init`-Animationen und zusätzlich `Pose0, COUNT,
  Pose1, COUNT, Pose2` in einer separaten Gesture-Animation. Ein
  GitHub-Actions-Gate ruft ScummC auf und prüft Chunk-Signatur und Länge.
- Der Ressourcen-Integrationstest ersetzt *ausschließlich in der isolierten
  Probe* das Costume des externen GPL-Game-Bootstraps, kompiliert und linkt
  neu und startet das Spiel in stock ScummVM. Die in der Screenshotprobe
  tatsächlich gezeichnete Figur muss mindestens 1.200 dunkle Pixel in der
  **horizontal bewegungstoleranten** Costume-Bildregion besitzen. Im ersten
  nativen Lauf wurden 1.536 Pixel gemessen (Actions `42407361581`). Dies ist ein **sichtbarer
  COST-Resource-Nachweis**, nicht bereits ein Animations-Counter-Test.
- Die Bilddateien verwenden **lokale Palette-Indizes 0–31** und genau die
  gewählte 32-Farben-COST-Palette. Dies vermeidet die zuvor beobachtete
  ScummC-Warnung über unterschiedliche BMP-/COST-Palettengrößen.
- Die isolierte `--count`-Probe verwendet dasselbe generierte Costume und
  verifiziert in stock ScummVM einen Original-v6-Scriptpfad:
  `animateActor(VAR_EGO,24)` → `getActorAnimCounter1(VAR_EGO)` →
  `breakScript()` → `setObjectState(Key,0)`. Mit mindestens **zwei**
  markierten COUNT-Ereignissen verschwindet der Schlüssel (0 sichtbare
  Schlüsselpixel). Die **Negativkontrolle** verlangt drei Ereignisse;
  dann bleiben 112 Schlüsselpixel sichtbar. Nachweis:
  GitHub Actions `42408292339`; dieselben Gates wurden mit korrigierter
  lokaler BMP-Palette im Lauf `42408510454` erneut bestanden.

## Noch offen für die eigentliche Gameplay-Abnahme

1. Die generierte COST-Ressource im allgemeinen Projektmodell einem
   **eigenständig exportierten** Actor zuweisen, statt im Fixture den
   externen Bootstrap auszutauschen; Animationen gezielt auslösen.
2. Den nachgewiesenen `getActorAnimCounter1`-Wartepfad als **allgemeinen
   versionierten Action-/Condition-Baustein** im Projekt-/Story-Modell
   verfügbar machen; der Proof verwendet derzeit noch ein isoliertes
   natives Testscript statt einer beliebigen Editor-Aktion.
3. Mehrere Actors, gegenseitige Scripts, Eingabe-Zeitfenster, Skip- und
   Save/Load-Zustand separat implementieren und als spielbare Abläufe prüfen.

Bis diese Schritte bestanden sind, bleiben `A01`, `A04`, `A06`, `A07`
in der Fähigkeitsmatrix **nur teilweise implementiert**. Der native
`COUNT`-Gameplay-Nachweis für das konkrete Fixture ist vorhanden; die
allgemeine Autorenfunktion ist es noch nicht.
