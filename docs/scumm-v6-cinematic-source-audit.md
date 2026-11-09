# SCUMM v6: filmische Inszenierung und Cutscene-Editor – Source-Audit

Stand: 2026-11-07. **Quellcodeanalyse von ScummVM und ScummC, keine Prüfung am proprietären Originalinterpreter.**

## Ziel und Abgrenzung

Adventure Studio soll cineastische Point-and-Click-Spiele wie *Sam & Max Hit the
Road* und *Day of the Tentacle* erzeugen. Die Editoroberfläche darf moderne
Filmbegriffe anbieten (Totale, Nahaufnahme, Schnitt, Schwenk), muss sie aber
auf **echte SCUMM-v6-Ressourcen und -Opcodes** abbilden. Keine zusätzliche
Runtime, kein unvalidierter Kamera-Zoom-Opcode.

Dieser Audit ergänzt
[den Runtime-Audit](scumm-v6-source-audit.md) und
[den Lifecycle-Audit](scumm-v6-execution-lifecycle.md).

### Untersuchte Originaldateien

| Projekt | Datei | Blob-SHA |
| --- | --- | --- |
| ScummVM | [`engines/scumm/camera.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/camera.cpp) | `d8227e16fbb8162c3a3285e63856848464753b08` |
| ScummVM | [`engines/scumm/script_v6.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/script_v6.cpp) | `e1e99d50bb617db32093f3b150984d45732610e9` |
| ScummVM | [`engines/scumm/scumm.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/scumm.cpp) | `88e087d765ee1065b22b59403bf3511f590a6a2f` |
| ScummVM | [`engines/scumm/room.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/room.cpp) | `9145b8960781fa07a3c2c3a3ad4ffb72b7d267b4` |
| ScummVM | [`engines/scumm/script.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/script.cpp) | `bd3c285c2e4ffc41154216f6ebdeee40567e7ee7` |
| ScummVM | [`engines/scumm/actor.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/actor.cpp) | `7c48e4923aa7efb49d1095398beffe292bc87ffa` |
| ScummC | [`scc_func.h`](https://github.com/AlbanBedel/scummc/blob/master/scc_func.h) | `88b10a76a9e907ec44db7f4c0a4b7b43f25afd6f` |
| ScummC | [`examples/road/road.scc`](https://github.com/AlbanBedel/scummc/blob/master/examples/road/road.scc) | `10fcb8df2e5e8a125763e176cadcf087843a16dd` |

Die Blob-SHAs fixieren jeweils den Inhalt einer Datei, **nicht** den gesamten
Repository-Commit. Verhaltensbehauptungen unterscheiden daher im Folgenden
Quellcodebeobachtung, technisch abgeleitete Gestaltungsregel und unbewiesene
Annahme.

## 1. Kamera ist in v6 primär eine horizontale Ansicht auf einen Raum

`script_v6.cpp` ordnet folgende v6-Opcodes zu:

| SCUMM-v6-Opcode | ScummVM | ScummC (nach `scc_func.h`) | Semantik |
| --- | --- | --- | --- |
| `0x78` | `o6_panCameraTo` | `panCameraTo(x)` | Ziel der horizontalen Kamerafahrt setzen |
| `0x79` | `o6_actorFollowCamera` | `cameraFollowActor(actor)` | Actor-Follow-Modus |
| `0x7A` | `o6_setCameraAt` | `setCameraAt(x)` | Kamera direkt auf X setzen |
| `0xA9` + Subopcode `SO_WAIT_FOR_CAMERA` | `o6_wait` | `waitForCamera()` (`0xA9AA` in ScummC) | Skript warten lassen, bis die Kamera X-Zielstrip erreicht |

**Versionsfalle:** Ab SCUMM v7 lesen `panCameraTo` und `setCameraAt`
zusätzlich Y-Werte. Für **v6** verwenden die Handler jeweils nur einen
X-Wert (`panCameraTo(pop(), 0)` und `setCameraAtEx(pop())`). Eine freie
zweidimensionale Kamerafahrt ist deshalb **kein nativer v6-Vertrag**.

`camera.cpp` konkretisiert:

- `panCameraTo(x)` setzt `camera._dest.x` und den Panning-Modus.
- `setCameraAtEx(x)` setzt für v6 den normalen Modus, aktuelle Position
  und Zielposition; das ist keine animierte Fahrt.
- `actorFollowCamera(actor)` aktiviert die Verfolgung und behandelt den
  Übergang aus dem vorigen Follow-Zustand.
- `moveCamera()` quantisiert die aktuelle Position auf 8-Pixel-Strips.
  Ohne Snap-Verhalten läuft sie für den betrachteten Pfad mit Schritten
  von acht Pixeln in Richtung `_dest.x`; Kamera-Limits begrenzen den Bereich.
- `waitForCamera()` prüft bei v6
  `camera._cur.x / 8 != camera._dest.x / 8`. Es wartet auf **Strip-Gleichheit**,
  nicht auf eine beliebige Millisekunden-Dauer.
- `VAR_SCROLL_SCRIPT` kann bei Positionsänderungen ein Skript auslösen.

**Editor-Regel:** Die Kamera-Timeline bekommt native Operationen `snap`,
`pan`, `follow`, `wait` und horizontale Grenzen. Zeitangaben sind nur
Darstellungshilfen; die Ausgabe darf keine nicht existente
„camera tween duration“-Operation erfinden. Das Tempo ergibt sich aus der
SCUMM-Laufzeitlogik, gegebenenfalls vorhandenen nativen Snap-Variablen.

## 2. Filmischer Schnitt ist nicht dasselbe wie Kameraschwenk

Ein Schnitt von einer Totale in eine Nahaufnahme kann in v6 nicht pauschal
als Änderung einer universellen Zoom-Kameraparameterzahl beschrieben werden.
Im geprüften v6-Kamerapfad existiert **kein nachgewiesener nativer Zoom- oder
Lens-Opcode**. Auch `SO_SCALE` in `o6_actorOps` skaliert einen Actor, **nicht**
die ganze Szene mitsamt Hintergrund.

Native Bausteine für einen filmischen Einstellungswechsel sind:

1. **Anderer Raum mit eigener Bildkomposition:** `o6_loadRoom` / ScummC
   `startRoom`, Room-Entry/Exit-Skripte, neue Hintergrund- und Objektdaten.
2. **Andere Ansicht innerhalb eines breiten Raums:** `setCameraAt` für
   einen harten horizontalen Wechsel; ggf. eigene Grafik im Raum.
3. **Anderer Bildzustand:** Objektzustände oder andere Actor-Costumes zeigen
   Nahansichten, Reaktionen oder Details, solange Ressourcenformat und
   Zeichnungsschichten dies zulassen.
4. **Übergangseffekt:** `SO_ROOM_FADE` und die Room-Transition-Logik stellen
   vorhandene Effektmöglichkeiten bereit, die separat auf Bytecode und
   korrekte Werte geprüft werden müssen.

**Kennzeichnung:** „Totale“, „Halbtotale“, „Nahaufnahme“, „Detail“ und
„Porträt“ sind **Editor-Metadaten für Kompositionen**, keine fünf
SCUMM-Kameramodi. Die Wahl, ob ein Shot als Raumwechsel, Kamerasprung,
Costume-/Objektzustand oder Kombination kompiliert wird, muss explizit
sichtbar und nachvollziehbar bleiben.

## 3. Bildwirkung: weitere native v6-Befehle

Der Handler `o6_roomOps()` enthält nachweisbar:

| Handler-Suboperation | Wirkung | Filmische Verwendung / Grenze |
| --- | --- | --- |
| `SO_ROOM_SCROLL` | setzt `VAR_CAMERA_MIN_X` und `VAR_CAMERA_MAX_X` nach Clamping | horizontale Bewegungsgrenzen |
| `SO_ROOM_SCREEN` | `initScreens(a,b)` | Bild-/Screen-Aufteilung; nicht als Zoom missverstehen |
| `SO_ROOM_PALETTE` | `setPalColor(...)` | gezielte Farbgestaltung |
| `SO_ROOM_SHAKE_ON` / `_OFF` | `setShake(1/0)` | Erschütterung, Explosion, dramatischer Effekt |
| `SO_ROOM_INTENSITY` | `darkenPalette(...)` | Abdunkeln/Helligkeit |
| `SO_ROOM_FADE` | Übergangseffekte setzen oder `fadeIn` auslösen | Blenden/Übergänge |
| `SO_RGB_ROOM_INTENSITY` | `darkenPalette` mit Farbkomponenten | farbige Stimmungswechsel |
| `SO_ROOM_SHADOW` | `setShadowPalette` | abgestufte Schattenpalette |
| `SO_ROOM_TRANSFORM` | `palManipulateInit` | Palettenmanipulation |
| `SO_CYCLE_SPEED` | Palette-Cycle-Geschwindigkeit | bewegte Licht-/Wassereffekte |
| `SO_ROOM_NEW_PALETTE` | `setCurrentPalette` | kompletter Palettenwechsel |

ScummC deklariert u. a. `setRoomScroll`, `setRoomIntensity`,
`setRoomPalette`, `fadeOut`, `fadeIn` und actorbezogenes `setActorScale`.
Damit ist **nicht** bewiesen, dass jede Suboperation über eine korrekte,
benannte ScummC-Funktion für v6 verfügbar ist. Einzelne Handler, Compiler-
Funktionssignaturen und tatsächlich emittierte Stackreihenfolge müssen noch
funktionweise gegengeprüft werden. Insbesondere ist nicht jede grafische
Palette-Operation ein „Filmfilter“ ohne Nebenwirkungen.

## 4. Choreografie von Darstellern und Kamera

Der v6-Handler `o6_actorOps` unterstützt unter anderem Costume-Wechsel,
Walk-Speed, Talk-/Stand-/Walk-Animationszuordnung, Actor-Elevation,
Paletteneinträge, Sprechfarbe, Breite, `SO_SCALE`, Z-Clipping,
Box-Verhalten, Animationsgeschwindigkeit und Sprechtext-Offset.
`SO_SCALE` ruft für v6 `a->setScale(i,i)` auf; es ist also eine
**Actor-Skalierung**, kein Kamera-Zoom.

Der sinnvolle native Aufbau für eine Sequenz lautet daher:

- Akteure platzieren und Blickrichtung bzw. Costume auswählen.
- Bewegung und Animationsphasen mit SCUMM-Skriptbefehlen starten.
- Nur dort `waitForActor`, `waitForCamera`, `waitForMessage`,
  Script-Delay oder Costume-Zähler verwenden, wo tatsächlich eine
  Abhängigkeit besteht.
- Parallel laufende Handlungen bewusst über Script-Slots organisieren,
  statt jede Aktion automatisch sequenziell zu blockieren.
- Eintritt in einen anderen Raum als echten Lebensdauer- und
  Ressourcenwechsel behandeln (siehe Lifecycle-Audit).

Insbesondere bei einem Auto, das losfährt, kann die sichtbare Bewegung
aus Actor-Costumes, Objekten oder anderen Raumkompositionen bestehen.
Welche Methode ein konkretes LucasArts-Spiel verwendet, ist **nicht**
allein aus den Existenzbeweisen dieser Opcodes ableitbar.

## 5. Cutscene ist ein Kontrollfluss-Konstrukt, kein Videoclip

`o6_cutscene` ruft `beginCutscene(args)`, `o6_endCutscene` ruft
`endCutscene()` auf. In `script.cpp` verwaltet `beginCutscene` einen
Cutscene-Stack, den Script-Slot und gegebenenfalls einen globalen
`VAR_CUTSCENE_START_SCRIPT`. `endCutscene` räumt den Stack auf, setzt
`VAR_OVERRIDE` zurück und kann `VAR_CUTSCENE_END_SCRIPT` starten.

`beginOverride()` merkt **Bytecode-Position und Script-Slot** als
Überspringziel und überspringt im Interpreter die auf den Opcode folgende
Sprunganweisung. `abortCutscene()` kann später zu diesem Zustand
zurückkehren. Diese Konstruktion ist wesentlich für überspringbare
Filmsequenzen. Ein beliebiges Editor-„Skip zum nächsten Shot“ könnte
Spielvariablen, Inventar, Raumzustand oder Script-Lifetime beschädigen.

**Editor-Kontrakt:** Jede überspringbare Sequenz benötigt ein modelliertes
Endergebnis (Raum, Actor-Positionen, Objektzustände, Variablen,
Inventar- und Tonzustand). Der Skip-Pfad muss dieses Ergebnis **mit
normalen SCUMM-Kommandos** herstellen und korrekt in den Cutscene-
Kontrollfluss eingebunden sein. Ein eigener Studio-Callback wäre falsch.

## 6. Beispiel: Filmische Abfahrt vor Sams Büro

Das folgende Beispiel ist eine **Entwurfsskizze**, kein Nachweis der
Originalskripte von *Sam & Max*:

| Shot | Bild und Dramaturgie | V6-Abbildung | Auflösung von Abhängigkeiten |
| --- | --- | --- | --- |
| 1 – Totale | Haus und Straße, Sam und Max sichtbar | Straßenraum + Costumes, Kamera auf passende X-Position | Entry-Script positioniert Darsteller |
| 2 – Annäherung | Beide gehen zum Auto | Native Actor-Walk-Kommandos | `waitForActor`, sofern nächster Shot abhängig |
| 3 – Detail | Türgriff/Autotür in Großaufnahme | Neuer Bildzustand oder Nahaufnahme-Raum | Skript/Objektzustand statt freier Kamerazoom |
| 4 – Innenaufnahme | Schlüssel dreht sich, Motor springt an | Eigene Raumkomposition/Costume, Sound | Sound und Costume-Schritte synchronisieren |
| 5 – Abfahrt | Auto setzt sich in Bewegung | Actor- oder Objektanimation; ggf. Kamerapan | Sichtbarkeit und Hitbox separat beachten |
| 6 – Schnitt | Straße aus neuer Perspektive | `startRoom`, native Exit-/Entry-Skripte | Raumscripte werden beim Wechsel beendet |
| 7 – Verfolgung | Kamera folgt Auto | `cameraFollowActor`, falls Auto Actor ist | `waitForCamera` nur bei wirklicher Fahrt |

Die tatsächliche Aufteilung in Räume und Costumes entscheidet über
Ressourcenbudget, Objekt-Klickbarkeit und den Export. Deshalb darf ein
Cutscene-Editor „Shot“ **nicht automatisch** mit „Raum“ gleichsetzen.

## 7. Datenmodell für einen nativen v6-Cutscene-Editor

**Autorensicht** (filmartig):

- `Sequence`: Einstieg, Ende, Skip-Endzustand, native Cutscene-Grenze.
- `Shot`: Einstellungsbezeichnung, Komposition, Startbedingung,
  sichtbare Actor/Objekt-Zustände; technische V6-Realisierungsart.
- `Track`: Kamera, Actor-Bewegung, Costume, Dialog, Sound, Palette,
  Objektzustand, Script/Variable.
- `Cue`: Startoperation und native Wartebedingung (nicht künstlicher
  Frame-Callback).
- `Transition`: Schnitt/Sprung, echter Raumwechsel oder verfügbare
  Room-Fade-Operation.

**Compiler-Vertrag**:

1. Jeder Shot wird auf eine verifizierte v6-Kombination aus
   Raum-/Objekt-/Costume-Ressourcen und Opcodes abgebildet.
2. Jeder Cue benennt die genau verwendete ScummC-Funktion beziehungsweise
   den nativen Bytecode-Pfad.
3. Der Compiler kennt Script-Slot- und Raumwechselgrenzen; er darf keine
   implizit weiterlaufenden raumlokalen Coroutines erzeugen.
4. Parallele Tracks werden als explizite, native Skript-Koordination
   realisiert, nicht als neue Laufzeit-Timeline.
5. Skip-/Abbruchpfade besitzen denselben notwendigen logischen Endzustand
   wie die normal abgeschlossene Sequenz.
6. Der Export muss ausschließlich mit einer SCUMM-v6-Engine laufen;
   Storyboard- und Shot-Begriffe bleiben Editor-Metadaten.

## 8. Offene Untersuchungen mit konkreter Reihenfolge

| Prio | Quelle/Frage | Ergebnis, das wir brauchen |
| --- | --- | --- |
| P0 | ScummC `scc_func.h` → Encoder `scc_code.c` für alle hier gelisteten Funktionen | Typen, Stackreihenfolge, Opcode/Subopcode, v6-Kompatibilität |
| P0 | ScummC Rooms/Costumes/Objekte und ScummVM Resource-Loader | Welche Ressourcen für Close-up-Shots wechseln müssen |
| P0 | Cutscene-Override und `abortCutscene` vollständig | Deterministischer Skip-Endzustand mit Inventar/Actors/Audio |
| P0 | Zeichnungsreihenfolge: Actor/Objekt/Mask/Z-Clip | Verdeckungen, Vordergrund, Porträtkomposition |
| P1 | Sound/iMUSE-Timing und Skript-Wartebedingungen | Filmische Audio-Cues und Übergänge ohne Studio-Runtime |
| P1 | Dialog und Portrait-Layouts in `print`/Charset/Actor-Talk | Nahaufnahmen mit Sprache, Text und Reaktionen |
| P1 | Originalspielressourcen, soweit rechtmäßig verfügbar | Prüfen, wie Sam-&-Max-/DOTT-Szenen tatsächlich aufgebaut sind |

**Nächste Arbeit:** zuerst die v6-Compiler-Opcode-Matrix und die
Ressourcenpfade zu Close-up- und Raumkompositionen fertig analysieren.
Erst danach einen Editor-Prototyp oder ein gezieltes Export-Regressionstest-
Fixture bauen. Ein allgemeines Konformitätsspiel ist dafür **keine
Voraussetzung**.
