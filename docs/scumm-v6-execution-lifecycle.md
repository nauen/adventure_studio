# SCUMM v6: Frame-Timing, Raumwechsel und bewegte Interaktionsobjekte

Stand: 2026-11-07. **Quellcode-Audit, kein Laufzeitnachweis im Originalinterpreter.**
Dieses Dokument vertieft den [Source-Audit](scumm-v6-source-audit.md) anhand
konkreter Ausführungspfade in ScummVM. Ziel ist ein Generator für *echte*
SCUMM-v6-Ressourcen und Skripte, nicht ein proprietärer Adventure-Studio-Runner.

## Quellen und Prüfbarkeit

Gelesen wurden die folgenden ScummVM-Dateien. Die Blob-SHAs bezeichnen den
untersuchten Dateiinhalt und verhindern, dass ein später veränderter `master`
unbemerkt als identischer Befund gilt.

| Datei | Blob-SHA | Relevante Routinen |
| --- | --- | --- |
| [`scumm.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/scumm.cpp) | `88e087d765ee1065b22b59403bf3511f590a6a2f` | `scummLoop`, `scummLoop_handleDrawing`, `scummLoop_handleActors` |
| [`actor.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/actor.cpp) | `7c48e4923aa7efb49d1095398beffe292bc87ffa` | `processActors`, `Actor::animateCostume` |
| [`costume.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/costume.cpp) | `aab00a030b9cf678cb87baacbe5136d6cd34746d` | `ClassicCostumeLoader::increaseAnim` |
| [`script.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/script.cpp) | `bd3c285c2e4ffc41154216f6ebdeee40567e7ee7` | `runAllScripts`, `killScriptsAndResources` |
| [`room.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/room.cpp) | `9145b8960781fa07a3c2c3a3ad4ffb72b7d267b4` | `startScene` |
| [`verbs.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/verbs.cpp) | `1637dd33c0e797480a5f158e4110567849c10e3d` | `checkExecVerbs` |
| [`object.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/object.cpp) | `0e97ae972a1abfa8c2277fac2d8ed65f00dff412` | `findObject`, `setObjectState` |
| [`script_v6.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/script_v6.cpp) | `e1e99d50bb617db32093f3b150984d45732610e9` | `o6_drawObject`, `o6_drawObjectAt` |

Die Beobachtungen betreffen die gegenwärtig gelesenen ScummVM-Pfade, sofern
nicht anders vermerkt. ScummVM ist eine Open-Source-Reimplementierung; für eine
Behauptung über *exakt identisches* Timing auf jeder Originalplattform braucht
es zusätzliche Referenztests.

## 1. Exakte Reihenfolge: Skript, Bild, Costume-COUNT

`ScummEngine::scummLoop` verarbeitet für v6 die relevanten Phasen in dieser
Reihenfolge:

1. Timer fortschreiben; wartende Skripte durch `decreaseScriptDelay` näher an
   ihre Fortsetzung bringen.
2. `processInput()` ausführen.
3. `runAllScripts()`, danach `checkExecVerbs()`; der Eingabepfad kann dabei
   seinerseits Skripte starten.
4. `checkAndRunSentenceScript()`.
5. Bei aktiver Raumdarstellung `walkActors()`, `moveCamera()`,
   `updateObjectStates()` und `scummLoop_handleDrawing()`.
6. `scummLoop_handleActors()` ruft `processActors()` auf.
7. Danach optional `VAR_MAIN_SCRIPT` ausführen, Palette/Bild darstellen.

**Entscheidende Unterreihenfolge in `processActors`:** Bei Version 0 wird
`animateCostume()` vor `drawActorCostume()` aufgerufen. Bei allen anderen
Versionen und damit **v6 genau umgekehrt**:

```cpp
a->drawActorCostume();
a->animateCostume();
```

`Actor::animateCostume()` erhöht zunächst `_animProgress`, führt die
Animationsfortschaltung nur bei Erreichen von `_animSpeed` aus und lässt dann
den Costume-Loader die Animationskanäle durchlaufen. In
`ClassicCostumeLoader::increaseAnim()` erhöht der Befehl `0x7C` (`COUNT`)
`a->_cost.animCounter`; Costume-Kommandos `0x71` bis `0x78` können bei v6
Sounds in die Queue geben. Da mehrere Costume-Slots durchlaufen werden,
darf der Generator **nicht** unterstellen, dass eine Aktualisierung höchstens
einen `COUNT` trifft.

**Folgerung für animierte Rätsel:** Ein normales, bereits laufendes Skript,
das während `runAllScripts()` den Animationszähler prüft, sieht die spätere
`COUNT`-Fortschaltung aus `processActors()` desselben Loop-Durchgangs noch
nicht. Bei der nächsten Skriptausführung kann es die neue Zahl lesen. Das
Bild des jeweiligen Durchgangs wurde vor der Costume-Fortschaltung gezeichnet.
Es gibt in diesem Pfad **keinen generischen Callback „Animationsframe erreicht“**.
Die Autorenschnittstelle muss Zählerabfrage, Skriptpausen und mögliche
mehrfache Zählersprünge berücksichtigen.

Das ist ausdrücklich **keine Garantie**, dass sämtliche denkbaren
Skriptabfragen erst im nächsten Videoframe laufen: `checkExecVerbs`, der
Sentence-Pfad und `VAR_MAIN_SCRIPT` liegen an anderen Stellen im Loop und
können Skripte unmittelbar ausführen. Auch ist ein Loop-Durchgang nicht
automatisch ein Costume-Animationsschritt (`_animSpeed`).

### Gezielter Konformitätstest A

Ein minimaler v6-Costume mit zwei sichtbaren Posen und `COUNT` an bekannter
Position muss protokollieren: (a) gezeichnete Pose, (b) Zähler vor und nach
dem `animateCostume`-Pfad, (c) erste Erkennung durch ein laufendes Skript,
(d) Wirkung von Animationsgeschwindigkeit und zwei `COUNT`-Kommandos in
einem Update. Gegen ScummVM ausführen; danach, soweit verfügbar, gegen
einen Original-v6-Interpreter prüfen. Erst dann sind Editor-Zeitleiste und
„im richtigen Moment benutzen“-Fenster kalibrierbar.

## 2. Raumwechsel: Skripte haben verschiedene Lebensdauern

`ScummEngine::startScene(room, actor, objectNr)` führt unter anderem aus:

1. Sprechen stoppen, Übergangseffekt vorbereiten.
2. Den *gerade laufenden* Script-Slot, falls dessen Herkunft `WIO_ROOM`,
   `WIO_FLOBJECT` oder `WIO_LOCAL` ist, einschließlich script-lokaler
   Arrays abbrechen. Bei aktivem Cutscene-Override ist dies für v5+
   im Code ein Fehlerfall.
3. `VAR_NEW_ROOM` setzen, **Exit-Script des alten Raums ausführen**.
4. `killScriptsAndResources()` ausführen. Die Routine setzt alle Slots mit
   `WIO_ROOM`, `WIO_FLOBJECT` oder `WIO_LOCAL` auf `ssDead` und räumt deren
   Arrays auf; sie behandelt aktive Overrides mit einer Warnung.
5. Raumbezogene Grafik, Objektlisten, Ressourcen und Sichtbarkeit zurücksetzen
   beziehungsweise neu laden; Raumvariablen setzen.
6. Actor am Eintrittspunkt positionieren und **Entry-Script des neuen Raums**
   ausführen (je nach Aufrufkontext/Version weitere Positionierung).

Globale Skripte sind hier nicht pauschal als `WIO_LOCAL` markiert und werden
von diesem Kill-Filter nicht allein wegen eines Raumwechsels beendet.
Das ist **keine** Aussage, dass jeder globale Skriptauftrag unabhängig von
allen anderen Aktionen ewig läuft; explizite Stop-, Freeze- und
Ressourcenregeln gelten weiterhin.

**Generator-Kontrakt:** Raum-Skript, globales Skript und Objekt-Verbskript
brauchen im Projektmodell unterscheidbare SCUMM-Herkunft. Ein übergreifender
Vorgang (etwa Auto besteigen, Abfahrt, dann neue Szene) muss den Übergang
gezielt aus einer zulässigen Skriptlebensdauer organisieren. Eine erfundene
„Coroutine über Raumwechsel hinweg“ wäre keine SCUMM-Kompatibilität.
Exit- und Entry-Script sind native Bestandteile der Sequenz.

### Gezielter Konformitätstest B

Drei Skripte starten: ein globales, ein raumlokales und ein Objektskript,
jeweils mit einem `breakHere` und anschließendem Zählerinkrement. Während
sie pausieren, Raumwechsel auslösen. Kontrollieren, welche Fortsetzungen
ausfallen, ob Exit vor Entry ausgeführt wird und ob Override-Fälle den
erwarteten Fehler/Warnpfad nehmen.

## 3. Bewegte Objekte: Objektzustand **und** Hitbox

Für v6 sind die Bytecode-Operationen unterschiedlich:

| v6-Opcode | ScummVM-Handler | Wirkung |
| --- | --- | --- |
| `0x61` | `o6_drawObject` | Objekt und Bildzustand vom Stack lesen; Zustand 0 auf 1 normalisieren; `setObjectState(obj, state, -1, -1)` |
| `0x62` | `o6_drawObjectAt` | Objekt, X und Y vom Stack lesen; `setObjectState(obj, 1, x, y)` |

In `setObjectState` verändert `drawObjectAt` die Felder `_objs[i].x_pos`
und `_objs[i].y_pos` um **jeweils `x * 8` beziehungsweise `y * 8`**,
sofern X nicht dem Sonderwert `-1` oder `0x7FFFFFFF` entspricht. Danach
kommt das Objekt in die Draw-Queue und sein State wird gesetzt.
Die Koordinaten sind also **nicht unbesehen Pixelwerte**.

`findObject(x, y)` prüft lokale, berührbare Objekte gegen aktuelle
`x_pos`, `y_pos`, `width`, `height` und berücksichtigt die Sichtbarkeit
innerhalb einer Parent-State-Hierarchie. Für die typischen v6-Spiele
verwendet es Rechtecke mit exklusiver rechter/unterer Grenze; gesonderte
spätere Spiele (z. B. DIG/CMI) behandeln die Grenze anders. Deshalb ist
ein mit `drawObjectAt` bewegtes Objekt auch an seinem aktualisierten Ort
anklickbar – **wenn** der normale Eingabe-/Verbpfad es als Ziel auflöst.

Ein `drawBlastObject` ist ein eigener v6-Opcode und darf nicht automatisch
mit dem Zustand/der Hitbox eines regulären Raumobjekts gleichgesetzt werden.
Für rein grafisch bewegte Kulissen gegenüber echten interaktiven Objekten
braucht der Editor eine klare Unterscheidung.

**Besonderheit Sam & Max:** `checkExecVerbs()` leitet einen Mausklick für
`GID_SAMNMAX` direkt als `runInputScript(kSceneClickArea, 0, code)` weiter.
Für die normale Verboberfläche von DOTT wird dagegen erst geprüft, ob ein
Verb an der Mausposition liegt; andernfalls erfolgt der Szenen-Klickpfad.
Die konkrete Zielobjekt-Auswahl liegt damit auch in **Spielskripten** und
darf nicht als globales, unveränderliches Klickschema im Studio kodiert
werden. „Klick auf Achterbahn während der Fahrt“ erfordert insbesondere
passende räumliche Objekt-/Input-Logik und nicht nur ein sichtbares Sprite.

### Gezielter Konformitätstest C

Ein Raumobjekt bei (x1,y1) zeichnen, später per `drawObjectAt` nach (x2,y2)
verschieben. Vorher und nachher `findObject`-Treffer und native
Szenenklick-/Verbskripte prüfen. Dasselbe Objekt mit Zustand/Parent-State
verstecken und im Skript wieder aktivieren. Für Sam & Max und DOTT getrennte
Eingabe-Skriptszenarien testen.

## 4. Konsequenzen für Adventure Studio (noch **keine** Implementierung)

| Priorität | Editor-/Compilervertrag | Nachweis bevor „fertig“ |
| --- | --- | --- |
| P0 | Native Costume-Kommandos, `COUNT`-Zähler, Animationsgeschwindigkeit, v6-Abfragelogik | Test A, exakte Ressourcen/Bytecode, ScummVM |
| P0 | Native `WIO_ROOM`/`WIO_LOCAL`/`WIO_FLOBJECT`-Lebensdauer und Entry/Exit-Skripte | Test B, Raumwechsel bei pausierenden Skripten |
| P0 | Native `drawObjectAt`-Koordinateneinheit und `findObject`-Hitbox | Test C, Klick auf bewegtes Objekt |
| P0 | Unterschiedliche native Eingabe-Skripte für Sam & Max und DOTT unterstützen | Test C, beide Spieleprofile |
| P1 | Visueller Sequenzeditor als **Compiler-Oberfläche** für Script-/Costume-Events | Exportiertes v6 läuft ohne Studio-Runtime |
| P1 | Prüfer für ungültige Cutscene-Overrides beim Raumwechsel | Negativtest mit expliziter Fehlermeldung |

### Offene Punkte

- **Originalinterpreter:** Bisher keine binäre Gegenprobe zu LucasArts-v6.
- **ScummC-Emitter:** Dieser Nachtrag verifiziert Interpreterpfade. Für jede
  Designer-Aktion muss noch der tatsächliche Syntax-/Bytecode-Pfad in
  `scc_code.c`, `scc_func.h` und Costume-Assembler bis zur Ressource
  rückverfolgt und mit einem Export-Test belegt werden.
- **Zielerfassung:** `findObject` allein ist kein vollständiger Beweis für
  Sam-&-Max-Skriptregeln bei Mausbewegung und Klick.
- **Timing:** Bei gleichzeitigen `COUNT`-Markern, schneller Animation und
  während eines Eingabeskripts ausgelösten Aktionen müssen die exakten
  Sichtbarkeitsgrenzen im Laufzeittest bestimmt werden.

Das nächste Implementierungspaket sollte daher ein **kleines natives
Konformitätsspiel** mit den drei Tests sein – nicht ein neues
Editor-Animationssystem ohne Bytecode-Gegenprobe.
