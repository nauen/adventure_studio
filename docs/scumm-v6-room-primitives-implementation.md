# P0.1–P0.3: Implementierung und verbleibende native Nachweise

Stand: 2026-11-07. Das Produktziel bleibt ein originaler SCUMM-v6-Export,
kein eigener Interpreter. Dieses Dokument trennt implementierte Verträge
von tatsächlich nachgewiesenem ScummVM-Verhalten.

## Quellenvertrag (ScummC)

- `scc_roobj.c` `scc_roobj_set_zplane`: die Raumdeklaration
  `zplane = { "RoomZ01.bmp", ... };` belegt die Plane-Indizes 1–9.
  `scc.h` definiert `SCC_MAX_IM_PLANES = 10`, Index 0 ist reserviert.
  `scc_roobj_gen_rmim` interpretiert jeden nichtnull Bildindex als
  gesetztes Maskenbit und schreibt `ZP01` usw. in `IM00`.
- `scc_roobj.c` `scc_roobj_set_boxd`: `boxd = "Room.box";`
  liest hier einen **kleingeschriebenen** `boxd`-Block (ein Byte Namenslänge,
  anschließend 20 Bytes pro Box), fügt Box 0 selbst hinzu und übernimmt
  `BOXM`-/`SCAL`-Blöcke aus derselben Datei. Die alternative **großgeschriebene**
  `BOXD`-Form lädt die folgenden Matrix-/Skalenblöcke dagegen nicht mit.
  Ein Boxeintrag hat vier Ecken (je x/y als i16 LE), danach je ein Byte
  Maske und Flags, danach u16 LE Scale.
- `write.c` `scc_write_boxm`: eine Matrixzeile besteht aus
  `(Start, Ende, nächster Boxindex)`-Tripeln und einem `0xff`-Terminator.
  `SCAL` ist hier ein Chunk von genau 40 Bytes (8 Header + 32 Daten).
- `code.c` und `scc_roobj.c`: `SMAP` nutzt u32-LE-Strip-Offsets,
  `ZPxx` u16-LE-Offsets; Chunks nutzen Big-Endian-Gesamtlängen.

Quelle: [ScummC](https://github.com/AlbanBedel/scummc), insbesondere
`scc_roobj.c`, `scc.h`, `write.c`, `code.c`, `scc_parse.y`.

## Implementierter Vertrag

1. `scumm_binary.verify_room_binary` prüft einen verlinkten `LECF`-/
   `ROOM`-Chunkbaum, Headergrenzen, Raum- und Objektstrip-Offsets,
   fortlaufende Z-Plane-IDs sowie die Zuordnung `OBIM`↔`OBCD`.
   `xor_key=0x69` unterstützt das in den Testspielen erzeugte `.001`.
   Das ist ein **struktureller** Parser, kein Bildcodec-Decoder.
2. `RoomAsset.zplanes` und optionale JSON-v1-Felder speichern binäre
   raumgroße Masken. Der Export schreibt 2-Farb-BMPs und die native
   `zplane`-Deklaration; fehlerhafte Größe, Bits und Indizes werden verworfen.
3. `RoomAsset.walkboxes`, `box_routes`, `scale_slots` speichern
   Koordinaten, Flags, Skalierung und explizite Next-Hop-Tabelle.
   Der Export schreibt die ScummC-BOXD-Eingabedatei mit BOXM und SCAL.
   Ohne vorgegebene Route wird **keine** implizite Verbindung zwischen
   zwei Boxen behauptet: nur die Eigendiagonale ist erreichbar.
4. Die neuen JSON-Felder sind optional; frühere Projektdateien bleiben
   unverändert serialisierbar. Unit-Tests prüfen Binärgrenzen, native
   Dateistruktur, Roundtrip und ungültige Eingaben.

## Evidenzgrenze und offene Gate-Kriterien

Die lokale strukturelle Prüfung hat einen bestehenden, extern mit ScummC
erzeugten `tentacle.001`-Export mit `0x69`-XOR erfolgreich geparst.
Diese vorhandene Binärdatei gehört **nicht** zum Repository und ist deshalb
kein CI-Testfixture. Die eingecheckten Unit-Tests erzeugen kleine,
deterministische Chunkdaten; sie prüfen keine Pixelausgabe.

Noch **nicht nachgewiesen** und darum nicht als abgeschlossen markieren:

- P0.2: mit den neuen Z-Masken tatsächlich übersetztes, verlinktes Spiel
  und sichtbare Verdeckung einer bewegten Figur in stock ScummVM.
- P0.3: ScummVM-Lauf einer Figur über mehrere verbundene Walkboxen,
  Tiefenbezug und sichtbare Skalierung anhand echter SCAL-Daten.
- P0.1: ein für CI reproduzierbar gebautes natives ScummC-Fixture und
  Pixelcodec-Roundtrip (die bisherige Prüfroutine ist bewusst nur strukturell).

Als nächste *technische Abnahme* sind daher ein kleiner Compiler-/Runtime-
Probe mit einer maskierten Vordergrundkante, zwei begehbaren Boxen und
expliziten Next-Hop-Routen erforderlich. Ohne diesen Lauf wäre die Aussage
„vollständig SCUMM-v6-kompatibel“ unbelegt.

Die bestehende experimentelle GitHub-Action
`.github/workflows/scummc-experiment.yml` ist um einen separaten
Compiler-/Linker-/Binärstruktur-Smoke für die neuen Raumdaten erweitert.
Der Job muss erst erfolgreich auf GitHub gelaufen sein, bevor dieser
Compilerbeleg als bestanden gilt. Er ersetzt keine visuelle ScummVM-Probe.
