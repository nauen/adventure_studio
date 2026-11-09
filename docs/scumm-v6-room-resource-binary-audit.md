# SCUMM v6: Binärpfad für Räume, Bilder, Masken und Objektzustände

Stand: 2026-11-07. **Quellcode-Audit, noch kein vollständig ausgeführter
Export-Regressionstest.** Ergänzt den
[Kompositions-/Compiler-Audit](scumm-v6-compositing-compiler-audit.md).

## Quellen und Geltung

Die folgenden konkreten Dateien wurden direkt aus den Repositories gelesen.
SHA bezeichnet den Git-**Blob** (Dateiinhalt), nicht den ganzen Repository-Commit.

| Projekt | Datei | Blob-SHA | Rolle |
| --- | --- | --- | --- |
| ScummC | [`scc_roobj.c`](https://github.com/AlbanBedel/scummc/blob/master/scc_roobj.c) | `d18b5c856463affc61573a715999d5d63c59247f` | tatsächlicher Raum-/Objektgenerator |
| ScummC | [`code.c`](https://github.com/AlbanBedel/scummc/blob/master/code.c) | `b6e7e6d1a13eba8f12c4aa2d0e0135a4e2fa7970` | SMAP-/Z-Masken-Encoder |
| ScummC | [`scc_img.c`](https://github.com/AlbanBedel/scummc/blob/master/scc_img.c) | `0efaee160950ecb68c33114a442304846d947168` | BMP-/GIF-Eingabe |
| ScummC | [`write.c`](https://github.com/AlbanBedel/scummc/blob/master/write.c) | `9611b78f6d5b009129104f72f2738bfab459595d` | ältere Schreibfunktionen / Formatvergleich |
| ScummC | [`scc_parse.y`](https://github.com/AlbanBedel/scummc/blob/master/scc_parse.y) | `25d5494b0365f2578bc013308f95681b319af65a` | Sprach-/Ressourceneingabe |
| ScummC | [`scvm_res.c`](https://github.com/AlbanBedel/scummc/blob/master/scvm_res.c) | `b342a0e240fc391839f4bd02e7307e6b344d077d` | eigene Referenz-Lesepfade |
| ScummVM | [`gfx.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/gfx.cpp) | `bf85f13c3ab30c5c761083bc20af593404af1213` | eigentlicher Bild-/Z-Masken-Decoder |
| ScummVM | [`object.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/object.cpp) | `0e97ae972a1abfa8c2277fac2d8ed65f00dff412` | Objekt-Laufzeitdaten/Hitbox |

**Wichtige Codebasen-Unterscheidung:** `write.c` enthält auch den Writer
`scc_write_room`, aber der direkt in `scc_roobj.c` untersuchte
`scc_roobj_write`-Pfad ist der relevante ScummC-Room-Object-Ausgabepfad.
Die Formate sind verwandt, jedoch sollten wir nicht allein den älteren
`write.c`-Writer als Beweis für den aktuellen Export verwenden.

## 1. Ende-zu-Ende-Graph des Writers

In `scc_roobj_write` werden die Ressourcen schrittweise aufgebaut:

1. `scc_roobj_gen_pals(ro)` entnimmt die Palette des Raum-Bildes.
2. `scc_roobj_gen_rmim(ro)` erzeugt das komprimierte Room-Bild samt Z-Masken.
3. `scc_roobj_make_obj_parent(ro)` löst Objekt-Elternbeziehungen in Indizes auf.
4. Pro Objekt erzeugt `scc_roobj_obj_gen_imnn(obj)` die Bildzustände.
5. Der Writer berechnet alle Blockgrößen und schreibt die Raumressource.
6. `scc_write_imob()` erzeugt pro Objekt Bilddaten; `scc_write_obob()`
   liefert Kontroll-/Verb-/Interaktionsdaten.

**Blockstruktur im untersuchten ScummC-Ausgabepfad:**

```text
room (ScummC-Objektcontainer, inklusive Versionsbyte)
  RMHD    Maße / Objektanzahl
  STAB    optional: Symboltabelle
  CYCL    Palettenzyklen
  TRNS    Transparenzindex
  PALS    Palettenblock
  RMIM    Raumgrafik
    RMIH  Z-Plane-Metadaten
    IM00
      SMAP  8-Pixel-Streifen des Hintergrunds
      ZP01, ZP02, ...  Z-Masken der Raumgrafik
  obim    je Objekt: imhd + IM01/IM02/... (SMAP, optionale Z-Masken)
  obcd    je Objekt: cdhd + verb + obna
  [Room-Local-Scripts]
  BOXD    Walkbox-Definitionen
  BOXM    Walkbox-Verbindungsmatrix
  SCAL    Skalierungsdaten
  scrp    globale Skripte im Container
  [weitere Ressourcen wie Costume/Sound]
```

Im Writer sind die äußeren `obim`, `obcd` und `room`-Tags kleingeschrieben;
innere Tags wie `RMHD`, `RMIM`, `SMAP`, `ZPxx` dagegen groß. Das ist kein
frei austauschbares Styling: Format-Tags und Blockgrößen sind binäre
Bestandteile des Exportprotokolls. Die endgültige Bündelung/Linkstufe
ist hier noch nicht vollständig überprüft.

## 2. Hintergrundbild: SMAP-Encoder

`scc_roobj_gen_rmim` ruft
`scc_code_image(image.data, image.w, image.w, image.h, -1, &smap)`.
`scc_code_image` (`code.c`) arbeitet in **vertikalen 8-Pixel-Streifen**:

- Die Breite muss durch acht teilbar sein; sonst gibt der Encoder 0 zurück
  und meldet den Fehler. Der Generator muss das als harte Validierung
  behandeln, nicht als nachträgliche Warnung.
- Für jeden Strip werden mehrere vorhandene Kompressionskodierer verglichen.
  Der Encoder wählt den kompaktesten gemessenen Datenstrom.
- Zu Beginn steht eine Tabelle von `stripes * 4` Bytes mit
  **32-Bit-Little-Endian-Offsets**; der Encoder speichert `pos + 8`.
  Der Offset bezieht sich damit auf den um den Chunk-Header erweiterten
  Datenanfang (wichtig beim Nachbau).
- Danach folgen je Strip Codec-/Shift-Kennung und komprimierte Nutzdaten;
  der Datenblock wird auf gerade Länge aufgefüllt.
- Bei einem Raum-Bild wird `transparentColor=-1` genutzt, also der
  opake Codec-Pfad; Objektgrafiken verwenden in diesem konkreten
  `scc_roobj_state_gen_imnn`-Pfad ebenfalls `-1`. Ein allgemeines
  Transparent-Object-Versprechen wäre ohne Prüfung dieses Details falsch.

Der ScummVM-Decoder liest für reguläre v6-Räume `SMAP` in `Gdi::drawBitmap`
und dekodiert diese Strips mit den passenden Grafikroutinen. Der Anschluss
des Encoders an `SMAP` ist damit **strukturell belegt**, aber ein
Byte-für-Byte-Roundtrip-Test mit konkreten Pixelwerten steht noch aus.

## 3. Z-Masken: getrennte Bitmap-Eingaben und ZPxx-Kompression

`scc_roobj_set_zplane(ro, idx, path)` legt eine Z-Plane aus einer Bilddatei
an. Der Code fordert `idx >= 1` und `< SCC_MAX_IM_PLANES` sowie eine
durch acht teilbare Breite; mehr als zwei Palettenfarben führen zunächst
nur zu einer Warnung.

**Nicht triviale Grenze:** `scc_roobj_gen_rmim` zählt die Z-Ebenen von
Index **1 aufsteigend bis zur ersten Lücke**. Ein Satz mit `ZP01` und
`ZP03`, aber ohne `ZP02`, würde deshalb in diesem Writer **nicht**
einfach beide Ebenen exportieren. Adventure Studio muss eine zusammenhängende
Indexfolge verlangen.

Für jede Ebene bildet der Generator acht Bildpixel zu einem Maskenbyte ab:
Pixel != 0 setzt das Bit `1 << (7 - (pixelIndex % 8))`. Anschließend
ruft er `scc_code_zbuf()` auf.

`scc_code_zbuf` verarbeitet ebenfalls acht Pixel breite Strips:

- zunächst Platz für eine Tabelle aus `strides * 2` Bytes;
- **16-Bit-Little-Endian-Offsets** pro Strip (`pos + 8`), bei einem
  leeren/compressionlosen Strip Offset 0;
- danach die durch `compMask` komprimierten Maskenbytes.

Die Writer-Funktion `scc_write_rmim` in `write.c` verdeutlicht die
`SMAP`-/`ZP0n`-Chunk-Tags und Big-Endian-Chunkgrößen. Der direkte
`scc_roobj_write`-Pfad verwendet denselben `scc_roobj_gen_rmim`-Builder;
die genaue Schreibfunktion für den RMIM-Block muss beim finalen Fixture
mit der tatsächlichen Containerstufe verifiziert werden.

Auf der Gegenseite liest `Gdi::getZPlanes` für die reguläre v6-Familie
die Tags `ZP01`, `ZP02`, `ZP03` usw. (mit eigener Behandlung anderer
Engine-Versionen), während `Gdi::drawBitmap` die decodierten Masken
auf die Z-Plane-Puffer abbildet. **Version/Spielprofil matters:**
die in `gfx.cpp` sichtbare Tag-Tabelle umfasst nur die ersten
wenigen Z-Ebenen. Deshalb sollte der Editor nicht allein anhand
`SCC_MAX_IM_PLANES` 15 funktionierende v6-Maskenebenen versprechen.

## 4. Objektbilder und interaktive Objektdefinitionen sind getrennt

ScummC verwaltet pro Objekt mehrere `state`-Bilder. Der Builder
`scc_roobj_obj_gen_imnn` beginnt die IDs bei **1** und ruft pro State
`scc_roobj_state_gen_imnn` auf; diese Routine erzeugt einen eigenen
SMAP-Datenstrom und optional maskierte Z-Plane-Daten.

`scc_write_imob` schreibt:

- einen Bild-Header `imhd` mit Objekt-ID, Anzahl Bilder, Anzahl
  Z-Ebenen, X/Y, Breite/Höhe;
- die Hotspot-Koordinaten der einzelnen Zustände;
- Blöcke `IM01`, `IM02` usw. mit den jeweiligen Bildern und Z-Masken.

`scc_write_obob` schreibt unabhängig davon die interaktiven Daten:

- `cdhd`: Objekt-ID, Anfangszustand, Besitzer, Klassen;
- für v6 zusätzlich Position, Ausdehnung, Parent-State/Parent,
  Zusatzfelder und Actor-Richtung;
- `verb`: die zugehörigen Objekt-Skripte;
- `obna`: Objektname.

**Kompatibilitätsregel:** Ein animiertes Dekor-Objekt, eine klickbare
Autotür und ein unsichtbarer Trigger sind nicht dasselbe. Grafische
Bildzustände gehören in `obim`; Hotspot-/Verb-/Parent-Informationen
in den entsprechenden Objekt- und Script-Pfad. Der Editor muss diese
Schichten zusammendenken, aber der Export muss sie **getrennt** schreiben.

## 5. Walkboxen und Perspektive im binären Raum

`scc_roobj_write` hängt `BOXD`, `BOXM` und `SCAL` an den Raum an.
Fehlen sie, schreibt er Defaultdaten; die eingebauten Dummy-Walkboxen
sind keine sinnvolle automatische Perspektivkonfiguration für
filmisch inszenierte Szenen.

Die alte `write.c`-Implementierung von `scc_write_boxd` zeigt pro Box
Eckkoordinaten, Maskennummer, Flags und Scale-Wert. In der eigentlichen
`scc_roobj_write`-Stufe hängt das genaue Layout vom dort verwendeten
Box-Writer und dem Zielversionsfeld ab.

**Editor-Regel:** Perspektive/Walkbarkeit brauchen eigene Datenquellen
und Validierung; eine schöne Raumgrafik allein definiert weder
Kollision noch Z-Zuordnung noch Actor-Skalierung.

## 6. Verifizierbare Export-Invarianten (für spätere Tests)

| Regel | Quelle | Validierung in Adventure Studio |
| --- | --- | --- |
| Bildbreite ist Vielfaches von 8 | `scc_code_image`, `scc_roobj_set_zplane` | harter Fehler vor Compilerlauf |
| Z-Ebenen ab 1 ohne Lücke | `scc_roobj_gen_rmim` | ZP01..ZPn zusammenhängend |
| SMAP-Offsets sind 32-bit LE | `scc_code_image` | Offsets gegen Blockgröße testen |
| ZPxx-Offsets sind 16-bit LE | `scc_code_zbuf` | Offset 0 korrekt behandeln |
| Binär-Chunks besitzen 4-Byte-Tags und 32-bit-BE-Größen | Writer | Struktur-Parser vor Spielexport |
| Objektzustände beginnen bei IM01 | `scc_roobj_obj_gen_imnn`, `scc_write_imob` | state-Mapping explizit prüfen |
| Objektbild und Objektskript sind getrennt | `scc_write_imob`, `scc_write_obob` | OBIM/OBCD-Paar und IDs validieren |
| Z-Masken und Walkbox-Masken müssen zusammenpassen | ScummVM `gfx.cpp` und Actor-Pfad | Plausibilitätscheck gegen Raum-Z-Ebenen |

## 7. Noch nicht bewiesen / nächster Schritt

1. Den finalen Schreibpfad der `RMIM`-/`SMAP`-/`ZPxx`-Daten in
   `scc_roobj_write` vollständig gegen die im ScummVM-Loader erwarteten
   Chunkgrenzen abgleichen, einschließlich Object-Image-Subchunkgrößen.
2. Den `scc_roobj_write`-Output durch einen unabhängigen Binärblock-
   Parser laufen lassen und die Offsets mit kodierten Beispielbildern
   gezielt prüfen.
3. Prüfen, ob Objekt-Transparenz/Maskierung im konkreten aktuellen
   ScummC-Objektwriter vollständig unterstützt ist oder ob zusätzliche
   Regeln/Codeergänzungen erforderlich sind.
4. Die möglichen Z-Ebenen auf die **tatsächlich von SCUMM v6/ScummVM
   unterstützte Zahl** begrenzen – nicht auf ein abstraktes ScummC-Maximum.
5. Danach einen minimalen nativen Raum mit mehreren Objektzuständen,
   Maske und Actor-Scale als gezielte Ressourcen-Funktionstestdatei
   erzeugen. Das ist **kein generisches Konformitätsspiel**.

**Zwischenergebnis:** Der Generator braucht keinen eigenen Bild-Renderer.
ScummC enthält bereits die entscheidenden Ressourcen-Encoder. Wir müssen
ihre Einschränkungen in das Datenmodell und die Validierung übernehmen und
die tatsächlichen Ausgabe-Chunks verlässlich testen.
