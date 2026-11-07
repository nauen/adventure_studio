# Wiederverwendbare native SCUMM-v6-Primitiven

**Technische Arbeitsreferenz, keine Behauptung vollständiger Implementierung.**
Quelle sind die bereits anhand konkreter ScummC-/ScummVM-Dateien geprüften
[Runtime](../scumm-v6-source-audit.md)-,
[Lifecycle](../scumm-v6-execution-lifecycle.md)-,
[Cinematic](../scumm-v6-cinematic-source-audit.md)-,
[Compositing](../scumm-v6-compositing-compiler-audit.md)- und
[Ressourcen](../scumm-v6-export-gap-analysis.md)-Audits.

Die Codepfade gelten für die dort dokumentierten Blob-SHAs. `master`-URLs
in den Audits sind Wegweiser, **keine** Aussage über zukünftige Versionen.
`A` bedeutet gelesener Pfad; erst `I/T/V` in der
[Funktionsmatrix](../SCUMM_V6_CAPABILITIES.md) belegen die Umsetzung.

## 1. Script und Scheduler – Basisschicht aller Spielmechaniken

| Funktion / IDs | ScummC-Seite | ScummVM-v6-Seite | Verbindliche Semantik / Risiko |
| --- | --- | --- | --- |
| Script starten, warten und unterbrechen (`S01`,`S02`) | `scc_func.h`, `scc_code.c`; v6-Funktionstabelle | `script_v6.cpp`, `script.cpp` (`runAllScripts`), `scumm.cpp` (`scummLoop`) | Script-Slots und `breakHere` erlauben kooperative Abläufe; aus einem Frame keine beliebige synchrone „Parallelität“ ableiten. |
| Script nach Room-Wechsel (`R04`,`S01`) | Room-Entry/Exit- und Object-Scripts in ScummC-Writer | `room.cpp` (`startScene`), `script.cpp` (`killScriptsAndResources`) | Lokale Scripts/Objekte und globale Zustände haben unterschiedliche Lebensdauer; Rückwege ausdrücklich testen. |
| Bedingungen und globale Zustände (`O02`,`O08`,`P01`) | Native Script-Ausdrücke/Variablen, `scc_func.h` | `script_v6.cpp`, `object.cpp` | Änderungen müssen deterministisch nach Verlassen/Wiederbetreten des Raums erhalten bleiben. |
| Cutscene-Umklammerung/Override (`S03`,`S04`) | v6-Cutscene-/Override-Aufrufe, `scc_func.h` | `script_v6.cpp`, `script.cpp` | Skip muss den **fertigen logischen Endzustand** herstellen, nicht nur die Animation abbrechen; genaue Encoder-/Skip-Gates offen. |

Der ursprüngliche Script-Scheduler gehört zur **SCUMM-Engine**, nicht zu
Adventure Studio. Unser Editor liefert deklarative Abläufe, das Backend
kompiliert native Scriptoperationen; es gibt keine zweite Event-Engine.

## 2. Camera und Szenenschnitt

| Primitive / IDs | ScummC | ScummVM | Wiederverwendbarer Vertrag |
| --- | --- | --- | --- |
| Setzen der Kamera (`S05`) | `setCameraAt(x)` in der v6-Funktionstabelle `scc_func.h` | `script_v6.cpp` → `o6_setCameraAt`, `camera.cpp` | Für v6 ist die nachgewiesene Kamerafunktion **horizontal**; kein generischer XY-Zoom. |
| Pan (`S06`) | `panCameraTo(x)`, `scc_func.h` | `script_v6.cpp`, `camera.cpp` | Ziel-X anfahren; nachfolgende Aktion mit `waitForCamera()` ausdrücklich synchronisieren. |
| Warte auf Kamera (`S06`) | `waitForCamera()` (`0xA9AA` laut Source-Audit) | `o6_wait`/`SO_WAIT_FOR_CAMERA` | V6 vergleicht horizontale Strip-Positionen, nicht ein frei interpoliertes 2D-Kameramodell. |
| Kamera folgt Actor (`S07`) | ScummC-v6-Zuordnung weiter konkretisieren | `camera.cpp`, `script_v6.cpp` | Follow-Modus und dessen Ende separat nachweisen, bevor ein UI-Steuerelement als vollständig gilt. |
| Total/Nahaufnahme/Schnitt (`S08`,`R14`) | Raumwechsel, andere Raum-/Objektbilder, Übergangsscripts | `room.cpp`, `gfx.cpp`, Kamera- und Scriptpfade | Ein Close-up ist in v6 ggf. ein **anders komponierter Raum bzw. Bildzustand**; kein belegter nativer Zoom-Opcode. |

## 3. Actors, Costumes und Frame-Timing

| Primitive / IDs | Compiler/Resource | Engine-Laufzeit | Wiederverwendbarer Vertrag |
| --- | --- | --- | --- |
| Costume-Daten und Animation (`A01`,`A04`) | `cost_parse.y`, `scc_cost.c`, `scc_func.h` | `costume.cpp`, `actor.cpp` | Native Ressourcen und Animationszustände; Writer/Decoder-End-to-End bislang nur teilweise belegt. |
| Position, Richtung, Laufbewegung (`A02`,`A03`) | v6-Actor-Funktionsgruppe `scc_func.h` | `actor.cpp`, `script_v6.cpp` | Actor-Bewegung folgt Walkboxen/Skalierung; Raumsortierung gehört zur Laufzeit. |
| Costume-Counter (`A06`,`A07`) | Costume-Kommandos/`COUNT`; `cost_parse.y` | `ClassicCostumeLoader::increaseAnim`, `Actor::animateCostume` | `Actor::_cost.animCounter` kann bei bestimmten Costume-Kommandos erhöht werden; **kein** Beweis, dass jede grafische Framegrenze eine solche Zählung auslöst. |
| Warten auf Actor/Animation (`A06`,`S02`) | v6-Wait-Aufrufe in `scc_func.h` | `ScummEngine_v6::o6_wait` | `SO_WAIT_FOR_ACTOR` prüft Bewegung, `SO_WAIT_FOR_ANIMATION` in geprüftem Pfad `_needRedraw`; beides **nicht** gleich „warte auf Bild N“. |
| Mehrere Actors, Occlusion (`A05`,`A08`,`R11`) | Costume-/Box-/Z-Masken-Ressourcen | `actor.cpp` (`processActors`), `gfx.cpp` | Renderreihenfolge und *Sam & Max*-Sonderfall getrennt beachten; kein allgemeines frei sortierbares Layer-System. |

**Zeitfensterregel:** Eine Interaktion im fahrenden Wagen benötigt einen
konkreten, zugänglichen Spielzustand, eine Input-Verarbeitung während
laufender Scripts und eine native Zeit-/Phasenbedingung (z. B. belegter
Costume-Counter). Der Compiler darf nicht aus reinen UI-Millisekunden
eine neue VM-Semantik ableiten.

## 4. Raum, Objekte, Hitboxen und Inventar

| Primitive / IDs | ScummC-Writer | ScummVM-Decoder/Handler | Vertrag |
| --- | --- | --- | --- |
| SMAP/Room-Strips (`R01`,`R02`,`R03`) | `scc_roobj.c`, `code.c`, `write.c` | `gfx.cpp`, `room.cpp` | Native Chunk-Baum-Struktur/Offsets und indizierte Streifen; Binär-Roundtrip bleibt P0.1. |
| ZPxx und Objekt-Z-Masken (`R06`,`R07`) | `scc_code_zbuf`, `scc_write_rmim` | `Gdi::getZPlanes`, `gfx.cpp` | Effektive v6-Ebenenzahl offen: ScummC-Ausgabekapazität ≠ bewiesene ScummVM-Kapazität. |
| BOXM/SCAL/Walkbox (`R08`,`R09`,`R10`) | Room-/Box-Writer | `actor.cpp`, `room.cpp` | Native Gehflächen, Verbindungen und Perspektive; keine reine GUI-Koordinate. |
| Objektstates und Position (`R05`,`O02`,`O03`,`O04`) | OBIM/OBCD/Object-Scripts | `object.cpp` (`setObjectState`, `findObject`), `o6_drawObjectAt` | Bild, Zustand, neue Hitbox, Parent-/Unberührbar-Zustände müssen zusammenpassen. |
| Inventory, Use, Combine (`O05`,`O06`,`O07`,`O09`) | Native Pickup-/Owner-/Use-/Scriptfunktionen | `verbs.cpp`, `script_v6.cpp`, `object.cpp` | Inventar-Owner/Objektzustand bleibt VM-verwaltet; 2er-Use ist eine Operatorregel, nicht eine Rätselbegrenzung. |
| Eingabemodell (`O01`,`O10`) | Spielabhängige Verb-/Input-Scripts | `verbs.cpp` (`checkExecVerbs`), `script_v6.cpp` | *Sam & Max*-Modus nicht pauschal für jedes v6-Adventure gleichsetzen. |

## 5. Dialog, Sound und Persistenz

| IDs | Nachweise / primäre Pfade | Vertrag / offenes Gate |
| --- | --- | --- |
| `D01`–`D04` | `script_v6.cpp`, `verbs.cpp`, bestehende [Source-Audits](../scumm-v6-source-audit.md) | Gesprächsgraph, Antwortverzweigung, Sprecherwechsel und Textressourcen getrennt beweisen; Demo-Talk-Hotspot ≠ vollständiges Dialogsystem. |
| `U01`–`U03` | Audio-/Music-Audits und ScummVM-Soundpfade im [Quellenindex](../SCUMM_V6_CAPABILITIES.md) | MIDI/Sound/iMUSE/VOC sind unterschiedliche native Ressourcen-/Timing-Gates; nicht aus MIDI-Probe auf vollständiges iMUSE schließen. |
| `P01`–`P03` | `saveload.cpp`, `script.cpp`, `object.cpp` | Native Variablen/Inventar/Actors speichern und beim Laden konsistent wiederherstellen; Endbedingung nicht mit Demo-`goal_text` gleichsetzen. |

## Quellcode-Fixpunkte (aus den vorhandenen Audits)

- **ScummVM:** [`script_v6.cpp`](https://github.com/scummvm/scummvm/blob/e1e99d50bb617db32093f3b150984d45732610e9/engines/scumm/script_v6.cpp),
  [`script.cpp`](https://github.com/scummvm/scummvm/blob/bd3c285c2e4ffc41154216f6ebdeee40567e7ee7/engines/scumm/script.cpp),
  [`actor.cpp`](https://github.com/scummvm/scummvm/blob/7c48e4923aa7efb49d1095398beffe292bc87ffa/engines/scumm/actor.cpp),
  [`costume.cpp`](https://github.com/scummvm/scummvm/blob/aab00a030b9cf678cb87baacbe5136d6cd34746d/engines/scumm/costume.cpp),
  [`camera.cpp`](https://github.com/scummvm/scummvm/blob/d8227e16fbb8162c3a3285e63856848464753b08/engines/scumm/camera.cpp),
  [`gfx.cpp`](https://github.com/scummvm/scummvm/blob/bf85f13c3ab30c5c761083bc20af593404af1213/engines/scumm/gfx.cpp).
- **ScummC:** [`scc_func.h`](https://github.com/AlbanBedel/scummc/blob/88b10a76a9e907ec44db7f4c0a4b7b43f25afd6f/scc_func.h),
  [`scc_code.c`](https://github.com/AlbanBedel/scummc/blob/165c6d932eb69acd1bc9380f867b071ae2a18ef0/scc_code.c),
  [`scc_roobj.c`](https://github.com/AlbanBedel/scummc/blob/d18b5c856463affc61573a715999d5d63c59247f/scc_roobj.c),
  [`scc_cost.c`](https://github.com/AlbanBedel/scummc/blob/f387827acb5ba5517164e746337fb06c6b45af51/scc_cost.c).

Die Liste ist ein **wiederverwendbarer Einstieg**, keine erneute Prüfung
dieser Git-Objekte in diesem Arbeitspaket. Wo nur Decoder oder Compiler
untersucht sind, bleibt das Gegenstück offen und wird beim entsprechenden
Feature-Paket gezielt geschlossen.
