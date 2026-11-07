# SCUMM v6: Writer/Decoder-Abgleich und Adventure-Studio-Lückenanalyse

Stand: 2026-11-07. **Quellcode-Befund und Implementierungsplanung.**
Kein neu erzeugtes Spieldaten-Binary und kein vollständiger
Roundtrip-Nachweis. Fortsetzung von
[Ressourcen-Binäraudit](scumm-v6-room-resource-binary-audit.md),
[Kompositions-Audit](scumm-v6-compositing-compiler-audit.md) und
[Cinematic-Audit](scumm-v6-cinematic-source-audit.md).

## 1. Was die Original-Implementierungen tatsächlich verbinden

| Datenblock / Information | ScummC schreibt | ScummVM liest/verwendet | Befund |
| --- | --- | --- | --- |
| `RMHD` | `scc_roobj_write`: Raummaße, Objektanzahl | Room-Initialisierung | Strukturelle Zuordnung vorhanden |
| `PALS`, `TRNS`, `CYCL` | Raum-Palette, Transparenzindex, Palettenzyklen | Room-Grafik/Palette | Writerseite nachvollzogen; Parameter- und Byte-Test offen |
| `RMIM` → `RMIH`/`IM00`/`SMAP` | `scc_roobj_gen_rmim` + `scc_write_rmim` | `Gdi::drawBitmap` sucht `SMAP`, dekodiert Strips | Formatpfad verifiziert; Pixel-Roundtrip offen |
| `RMIM` → `ZP01`, `ZP02` … | Z-Plane-Bitmap → Bitpack → `scc_code_zbuf` → `scc_write_rmim` | `Gdi::getZPlanes` sucht v6-`ZP0n`, Renderer nutzt Masken | Strukturelle Zuordnung vorhanden; Maximalzahl/Visualtest offen |
| `obim` → `imhd` + `IM01`… | `scc_write_imob` + `scc_write_imnn` | Objekt-Bildheader, Image-Count und GDI-Bildpfad | Bildzustands-IDs ab 1 belegt |
| `obcd` → `cdhd`/`verb`/`obna` | `scc_write_obob` + `scc_write_verb_block` | Objektposition, Besitzer, Klassen, Verb-Skripte | Trennung von Grafik und Logik belegt |
| `BOXD`/`BOXM`/`SCAL` | `scc_roobj_write` schreibt Daten oder Defaults | Walkbox/Skalierungs- und Z-Masken-Pfade | Grundformat vorhanden; Zielspiel-spezifische Plausibilität offen |
| `ENCD`/`EXCD`, lokale/global gebundene Skripte | ScummC Room/Scripts | Entry-/Exit- und Script-Slot-Logik | Skript-Lifetime separat untersucht |

### Relevante Originalquellen

- ScummC [`scc_roobj.c`](https://github.com/AlbanBedel/scummc/blob/master/scc_roobj.c), Blob `d18b5c856463affc61573a715999d5d63c59247f`:
  `scc_roobj_gen_rmim`, `scc_roobj_state_gen_imnn`,
  `scc_write_imob`, `scc_write_obob`, `scc_roobj_write`.
- ScummC [`code.c`](https://github.com/AlbanBedel/scummc/blob/master/code.c), Blob `b6e7e6d1a13eba8f12c4aa2d0e0135a4e2fa7970`:
  `scc_code_image`, `scc_code_zbuf`.
- ScummC [`write.c`](https://github.com/AlbanBedel/scummc/blob/master/write.c), Blob `9611b78f6d5b009129104f72f2738bfab459595d`:
  `scc_write_rmim` und `scc_write_imnn`.
- ScummVM [`gfx.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/gfx.cpp), Blob `bf85f13c3ab30c5c761083bc20af593404af1213`:
  `Gdi::getZPlanes`, `Gdi::drawBitmap`.
- ScummVM [`object.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/object.cpp), Blob `0e97ae972a1abfa8c2277fac2d8ed65f00dff412`:
  `getObjectImageCount`, `findObject`, Objekt-Orts-/Statuspfade.

**Präzisierung zum vorigen Audit:** `scc_roobj_write` ruft tatsächlich
`scc_write_rmim(fd, rmim)` und pro Objekt `scc_write_imob`/
`scc_write_obob` auf. Die zugehörigen Builder kommen aus
`scc_roobj.c`, die gemeinsame RMIM-Serialisierungsroutine aus `write.c`.
Das ist ein direkter Quellcodepfad, nicht nur eine vermutete Ähnlichkeit.
Die endgültige Bündel-/Linker-Stufe bleibt gesondert zu überprüfen.

## 2. Konkrete Binärdetails, die der Studio-Export beachten muss

### 2.1 SMAP und Hintergrund

ScummC teilt die indizierte Grafik in vertikale 8-Pixel-Streifen auf.
Die `SMAP`-Nutzdaten beginnen mit einer Tabelle aus 32-Bit-Little-Endian-
Strip-Offsets. Pro Strip folgen Codec-Kennung und komprimierte Pixel.
Die Teilblockgrößen werden im SCUMM-Chunkformat (4-Byte-Tag und
32-Bit-Big-Endian-Länge) serialisiert. ScummVM sucht im v6-GDI-Pfad
`SMAP` und dekodiert die Strips.

**Zu prüfen:** Größen- und Offsetsystem an der Grenze zwischen
`RMIM`/`IM00`/`SMAP`, dann ein Bild mit klar unterscheidbaren
Pixelmustern zum Roundtrip durch ScummVM verwenden.

### 2.2 Z-Masken und Z-Plane-Anzahl

`scc_roobj_gen_rmim` sammelt Masken nur ab `ZP01` **lückenlos**.
Der Encoder packt acht Maskenpixel in ein Byte (höchstes Bit zuerst),
`scc_code_zbuf` schreibt 16-Bit-Little-Endian-Strip-Offsets.
`Gdi::getZPlanes` sucht in der normalen v6-Version die entsprechenden
`ZP0n`-Tags, während andere Versionen andere Formate verwenden.

**Wichtige offene Grenze:** Die im ScummVM-Pfad sichtbar hartkodierte
Z-Tag-Tabelle enthält nur `ZP00` bis `ZP04`, während ScummC eine höhere
theoretische Maximalzahl kennt. Der Generator darf daraus **nicht**
automatisch 15 funktionierende v6-Maskenebenen ableiten. Zuerst die
effektive Anzahl im v6-Renderer/Room-Header prüfen, danach konservativ
validieren.

### 2.3 Objektbild versus Hotspot

Ein `obim`-Bildblock kann mehrere Zustände `IM01`, `IM02` ... enthalten.
`getObjectImageCount` liest für v6 aus dem `IMHD`-Header explizit die
`old.image_count`-Variante. Der getrennte `obcd`-Block enthält die
Interaktionsdaten. Verschiebt ein Skript mit `drawObjectAt` das Objekt,
verändert es die laufzeitseitige Position – die Hitbox ergibt sich damit
nicht aus dem SMAP-Pixelbild allein.

**Zu prüfen:** Mehrere Bildzustände, ein Parent-State und ein geklicktes
Objekt nach Ortsänderung; Export muss jeweils Bild-/Objekt-ID konsistent
halten. Ein Bild ohne `obcd`-Interaktionsdaten ist noch kein Hotspot.

## 3. Tatsächlicher Stand von Adventure Studio (`main`)

Aktueller GitHub-Stand aus diesen Projektdateien gelesen:

- [`scumm_assets.py`](https://github.com/nauen/adventure_studio/blob/main/src/adventure_studio/scumm_assets.py), Blob `4a99e588a11d357290ce6206bd4fb5026c5cba0`.
- [`scumm_project.py`](https://github.com/nauen/adventure_studio/blob/main/src/adventure_studio/scumm_project.py), Blob `a4d74a2b342a23df0f2ac7d70c5f8b95c29d37c6`.
- [`story_to_scumm.py`](https://github.com/nauen/adventure_studio/blob/main/src/adventure_studio/story_to_scumm.py): Story-/Rezept-Übersetzer, hier aufrufseitig geprüft.
- [`scumm_launch.py`](https://github.com/nauen/adventure_studio/blob/main/src/adventure_studio/scumm_launch.py), Blob `588041a25a6c0f828874c20d26d00026089eed2f`: ScummVM-Laufzeit-/Screenshot-Smoketests.

**Gesichert vorhanden:**

- `RoomAsset` modelliert Raumgröße, Palette, indexierte Pixel,
  `RoomHotspot`, einfache Objektzustands-Grafiken, Use-/Combine-/Talk-
  Regeln, Musikreferenz und Palettenzyklen.
- `_validate` erzwingt bereits eine durch acht teilbare Raumbreite,
  passende Pixelzahl/Palette und validierte Objektkoordinaten.
- `write_room_sources` schreibt indizierte BMPs und ScummC-Quelltext;
  `scummc_room_source` emittiert `image = ...`, `object`, `states`,
  Verb-Skripte und Room-Skripte.
- `scumm_project.py` bietet ein serialisiertes `GameDocument` mit
  Validierung und Export in diese Quelldateien.
- `scumm_launch.py` enthält einen echten ScummVM-basierten
  Screenshot-/Interaktions-Testpfad für vorhandene Demo-Szenarien.

**Nicht im aktuellen `RoomAsset`-Datenvertrag nachgewiesen:**

- importierte Z-Plane-/Maskenbilder und deren Ebenenindizes;
- explizite Walkbox-Polygone, `BOXM`-Verbindungen und `SCAL`-Daten;
- Actor-Costume-Spuren, eigene Actor-Zeitleisten und native
  Animation-`COUNT`-Synchronisation;
- filmische Kamera-Shots/Übergänge, synchronisierte Multitrack-Cutscenes,
  native Skip-Endzustände;
- frei authorbare Objekt-Parent-State-Hierarchien und unabhängig
  animierte/verschobene interaktive Objekte.

Das ist ein **Funktionsumfang-Befund des sichtbaren Datenmodells**, keine
Behauptung, dass im gesamten Repository niemals ein Experiment zu einem
dieser Themen existiert. Insbesondere dürfen vorhandene Test-/Probe-Module
nicht mit einem allgemein verfügbaren Editor-Feature gleichgesetzt werden.

## 4. Priorisierte Implementierungspakete

| Reihenfolge | Arbeitspaket | Ergebnis / Abnahme |
| --- | --- | --- |
| P0.1 | Binär-Roundtrip-Audit-Tool für ScummC-Room-Ausgabe | Chunk-Baum samt Größen/Offsets/IDs maschinenlesbar; prüft SMAP, ZP01, OBIM/OBCD |
| P0.2 | `RoomAsset` um Z-Masken mit strenger v6-Validierung erweitern | `zplane[n]` im ScummC-Raumquelltext, BMP-Ausgabe, ein Masken-Smoketest |
| P0.3 | Walkbox-/BOXM-/SCAL-Modell plus Export | Native Perspektiv-/Z-Clip-Szene in ScummVM sichtbar |
| P0.4 | Objektzustände + Parent/Bewegung vollständig modellieren | `drawObjectAt`, Hitbox, Objektzustände und Klickpfad verifiziert |
| P0.5 | Costumes und Actor-Animation inklusive `COUNT` | V6-Kostümressourcen mit reproduzierbarer Skriptsynchronisation |
| P1.1 | Shot-/Cutscene-IR auf bereits geprüfte native Befehle abbilden | Schwenk, harter Schnitt, Raumwechsel, Skip-Endzustand laufen ohne neue Runtime |
| P1.2 | Kinoartige Autorensicht und Preview | Visuelle Bedienung erzeugt exakt die native IR und denselben Export |

**Entscheidung:** Das nächste Coding-Paket sollte **P0.1 → P0.2** sein.
Eine fehlerfreie SMAP-/ZP-/Objekt-Binärverarbeitung ist die Grundlage für
Masken und filmische Bildkomposition. Ein vollständiges eigenständiges
„Konformitätsspiel“ ist aktuell nicht nötig; gezielte Export-Fixtures
im bestehenden Testpfad sind wertvoller.

## 5. Offen und ausdrücklich nicht als bestanden markiert

1. Header-/Offset-Abgleich der finalen Linker-Ausgabe mit tatsächlich
   geladenen ScummVM-Daten ist noch nicht als automatischer Test umgesetzt.
2. Objekte mit transparenter Grafik benötigen einen eigenen Encoder-/
   Decoder-Nachweis; `scc_roobj_state_gen_imnn` ruft für untersuchte
   Zustandsgrafiken `scc_code_image(..., -1, ...)` auf.
3. Die maximale native Zahl der Maskenebenen sowie der genaue Zusammenhang
   zu Walkbox-Maskennummern sind noch zu verifizieren.
4. Save/Load und das Überspringen von Cutscenes bei dynamischen Shots
   brauchen später eigene zustandsorientierte Tests.

**Ergebnis:** Wir kennen jetzt die nativen Writer-/Decoder-Bausteine und
den konkreten Abstand zum vorhandenen Adventure-Studio-Datenmodell.
Die nächste Arbeit ist gezielte Implementierung am Exportpfad – **kein
Neuentwurf einer proprietären SCUMM-Engine**.
