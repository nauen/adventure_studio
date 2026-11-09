# SCUMM v6: Perspektivische SCAL-Slots und Walkbox-Zuordnung

Stand 2026-11-07. Ziel ist die originale vertikale Skalierung des Actors,
wenn er in die Tiefe eines Raumes geht. Kein Studio-interner Renderer.

## Direkt geprüfter Quellenvertrag

| Quelle | Nachgewiesene Semantik |
| --- | --- |
| [ScummC `boxedit.c`](https://github.com/AlbanBedel/scummc/blob/master/boxedit.c) | `SCAL`: vier Slots à 8 Byte; pro Slot u16 Little-Endian `scale1`, `y1`, `scale2`, `y2`; Gesamtchunk 40 Byte. |
| ScummC `scc_roobj.c` | `boxd` liest die 20-Byte-Walkbox-Einträge und den angehängten `SCAL`-Chunk; Scale-Feld in der Box ist u16 Little-Endian. |
| [ScummVM `room.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/room.cpp) | Nichtnull-Slots aus `SCAL` werden mit `setScaleSlot(i, 0, y1, scale1, 0, y2, scale2)` initialisiert. |
| [ScummVM `boxes.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/boxes.cpp) | Scale-Feld mit Bit `0x8000` referenziert einen Slot: `((scale & 0x7fff) + 1)`. `getScaleFromSlot` interpoliert linear nach Y, danach Clamp auf 1–255. |
| [ScummVM `actor.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/actor.cpp) | `setupActorScale` verwendet bei aktiven Walkboxen `getScale(_walkbox, _pos.x, _pos.y)` für beide Kostümachsen. |

SCUMM v6 verwendet in diesem Raumformat vier, nicht beliebig viele Slots.
ScummC-BoxEdit setzt `0x8000 | slotIndexZeroBased`. Die separate
`scale_slot`-Eigenschaft im Studio vermeidet, dass der Benutzer diese
Kodierung selbst eingeben muss.

## Implementierter Authoring-/Exportvertrag

- `ScaleCurve(slot, scale1, y1, scale2, y2)` ist ein fachlich typisierter
  Slot für **vertikale** Perspektive; Slotnummern 1–4, Skalen 1–255,
  `0 <= y1 < y2 < Raumhöhe`. Mehrfachbelegung und unbekannte Slotverweise
  werden vor Dateiausgabe abgelehnt.
- `Walkbox.scale_slot` verweist optional auf den Slot. Ansonsten bleibt
  `Walkbox.scale` für die bisherige konstante Skalierung zuständig.
- Die Binärdatei enthält das unveränderte ScummC-Format mit vier SCAL-Slots
  (unbenutzte Slots null) und der `0x8000`-Referenz im BOXD-Eintrag.
- Das JSON-v1-Format bleibt rückwärtskompatibel. Neue optionale Felder
  `scale_curves` sowie `scale_slot` an einer Walkbox sind ausdrücklich
  validiert; das alte, rohe `scale_slots`-Bytefeld bleibt lesbar, darf aber
  nicht mit dem typisierten Modell gemischt werden.
- `demo_walk_to_y` ist ausschließlich ein optionaler Ziel-Y-Wert für den
  vorhandenen Demo-Walk-Testpfad. Das allgemeine, zukünftige
  Story-Action-IR wird dadurch **nicht** vorweggenommen.

## Native Abnahme

`scumm_scal_probe.py` erzeugt mit identischer Kurve drei Räume, in denen
die Figur zu verschiedenen Y-Tiefen läuft (100/125/145). Ein echter
ScummC-/Linker-Lauf und stock ScummVM zeichnen die Endbilder auf. Der
Vergleich zählt dunkle Kostümpixel im festen Spielbildausschnitt
`170x155+480+310`, der die Figur in allen drei Endpositionen enthält und
Bedienleiste sowie schwarzen Letterbox-Rand ausschließt. Die erste native
Durchführung (Actions 42403019595) ergab nach **Korrektur** des fehlerhaften
ursprünglichen Ausschnitts lokal an denselben CI-Screenshots **724, 1020,
1124** dunkle Pixel. Der ursprüngliche Ausschnitt hatte die kleinste Figur
ausgeschnitten und daher fälschlich 0 gezählt. Nun schlägt der native
Regressionstest fehl, wenn die kleinste Silhouette weniger als 300 Pixel
hat oder die Zuwächse unter 100 beziehungsweise 75 Pixel liegen.

Dieser Bildvergleich belegt eine sichtbare Skalenzunahme im originalen
ScummVM. Er beweist **keine pixelgenaue numerische Übereinstimmung** der
im Interpreter intern berechneten Skalierung; die theoretischen Werte
141/193/234 werden separat mit der originalen Interpolationsformel geprüft.

**Nicht impliziert:** horizontale Skalierung, SCUMM v7/v8-Slots,
unbegrenzte Slotzahlen, automatische Walkbox-Routenerzeugung oder eine
erwiesenermaßen stabile 3D-Kameraprojektion.
