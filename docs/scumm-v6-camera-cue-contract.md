# Native SCUMM-v6-Kamera-Cues: erster Choreografie-Baustein

Stand 2026-11-07. Dies ist **kein** vollständiger Cutscene-Editor und
behauptet weder Zoom noch vertikale Kamerafahrten.

## Nachgewiesene v6-Primitiven

- ScummC `scc_func.h`: `setCameraAt(x)` (`0x7A`) und
  `panCameraTo(x)` (`0x78`) erwarten in **v6 je einen X-Parameter**.
  `waitForCamera()` ist der v6-Warteaufruf (`0xA9AA`).
- ScummC `examples/road/road.scc` demonstriert die funktionierende
  Reihenfolge `setCameraAt(0); panCameraTo(440); waitForCamera();`
  und anschließend `cameraFollowActor(VAR_EGO)`.
- ScummVM `engines/scumm/script_v6.cpp` und `camera.cpp` implementieren
  horizontales Setzen, Fahren und Warten. Näheres im vorhandenen
  [`NATIVE_PRIMITIVES.md`](scumm-v6-reference/NATIVE_PRIMITIVES.md).

## Authoring und Export

`RoomAsset.camera_cues` enthält eine **beliebig lange geordnete Sequenz**
aus `CameraCue(operation, x)`:

| `operation` | `x` | Originaler ScummC-v6-Code |
| --- | --- | --- |
| `set` | Raum-X | `setCameraAt(x);` |
| `pan` | Raum-X | `panCameraTo(x);` |
| `wait` | fehlt | `waitForCamera();` |
| `follow_ego` | fehlt | `cameraFollowActor(VAR_EGO);` |

Die JSON-v1-Datei darf optional `camera_cues` enthalten. Andere Keys,
ungültige Operationen, falsche Parametertypen und X außerhalb der
Raumkoordinaten werden abgelehnt. Bestehende Räume ohne Cues behalten
unverändert den bisherigen `cameraFollowActor(VAR_EGO)`-Start.

Es handelt sich bewusst um eine **geordnete native Sequenz**, nicht um
eine zeitbasierte Editor-Timeline. `wait` ist ein expliziter Cue; ohne
ihn können nachfolgende Aktionen während eines Pans beginnen.

## Native Testgrenze

`scumm_camera_probe.py` baut zwei bis auf die Kamera identische Räume
mit ScummC und startet beide in stock ScummVM. Einmal bleibt die Kamera
auf X=160, einmal fährt sie nach X=480 und wartet; ein Vergleich der
Endbilder muss mindestens 10.000 unterschiedliche Bildpixel nachweisen.
Das belegt eine sichtbare Kamera-Komposition. Erst der erfolgreiche
GitHub-Actions-Lauf bestätigt dieses Runtime-Gate.

**Noch offen:** Native begin/end-/Override-Cutscenes mit Skip-Endzustand,
Actor-Kostüme/COUNT-Timing, Schnitt zwischen Shots/Räumen und unabhängige
parallel laufende Tracks. Diese Capability-IDs bleiben offen.
