# Adventure Studio: SCUMM-v6-Laufzeitvertrag und Quellcodebefunde

Status: erste **quellenbasierte technische Bestandsaufnahme**, 2026-11-07.
Zugehöriger Anforderungskatalog:
[`scumm-adventure-mechanics.md`](scumm-adventure-mechanics.md).

**Weiterführende Quellcodeprüfung:**
[`scumm-v6-source-audit.md`](scumm-v6-source-audit.md) verfolgt die konkreten
Interpreter- und Compilerfunktionen. Sie präzisiert insbesondere, dass
`waitForAnimation` in ScummVM auf `_needRedraw` prüft, und identifiziert
`COUNT` im originalen Costume-Format als möglichen Synchronisationsweg.

## 1. Ziel und Evidenzstufen

**Wir erzeugen originale SCUMM-v6-Spielressourcen und -Skripte für eine
unveränderte SCUMM-Laufzeit.** Adventure Studio darf keine eigene Scheduler-,
Eingabe- oder Animationssemantik voraussetzen, die im Zielinterpreter fehlt.

Vier strikt getrennte Evidenzstufen:

| Kennung | Bedeutung |
| --- | --- |
| `VM` | In der ScummVM-v6-Opcode-Tabelle oder Implementierung nachgewiesen |
| `SCUMMC` | Von ScummC-Dokumentation/Grammatik als Quellkonstrukt beschrieben |
| `SPIELTEST` | Aus Adventure Studio erzeugter Code nachweislich in unverändertem ScummVM ausgeführt |
| `OFFEN` | Eine benötigte Semantik ist nicht belegt; kein Feature-Versprechen |

`VM` plus `SCUMMC` ist **nicht** dasselbe wie `SPIELTEST`.
Eine VM-Operation kann in einer Spielvariante anders funktionieren oder
durch Fehler/Limitierungen der Toolchain unerreichbar sein.

Die Quellenangaben beziehen sich auf den recherchierten Stand; die spätere
Implementierung muss **ScummVM-Commit und ScummC-Revision pinnen**, denn
`master` ist keine stabile Versionsspezifikation.

## 2. Primärquellen

1. **ScummVM, SCUMM-v6-Opcode-Implementierung:**
   <https://github.com/scummvm/scummvm/blob/master/engines/scumm/script_v6.cpp>
2. **ScummVM, Skriptverwaltung/Skript-Slots:**
   <https://github.com/scummvm/scummvm/blob/master/engines/scumm/script.cpp>
3. **ScummVM, Scumm-Save/Load:**
   <https://github.com/scummvm/scummvm/blob/master/engines/scumm/saveload.cpp>
4. **ScummVM, Kostüm-/Animationsdecoder:**
   <https://github.com/scummvm/scummvm/blob/master/engines/scumm/costume.cpp>
5. **ScummVM, SCUMM-v6-Opcode-Referenz:**
   <https://www.scummvm.org/old/docs/specs/scrp-v6.php>
6. **ScummC, Compiler/Linker/Asset-Tools und Kompatibilitätswarnungen:**
   <https://github.com/AlbanBedel/scummc/blob/master/README.md>
7. **ScummC, Grammatik und Ressourcen:**
   <https://github.com/AlbanBedel/scummc/wiki/ScummC-Grammar>
8. **ScummC, v6-Funktions- und Opcode-Zuordnung:**
   <https://github.com/AlbanBedel/scummc/wiki/Scumm-6-functions>
9. **ScummC, Engine-gesteuerte Skriptarten:**
   <https://github.com/AlbanBedel/scummc/wiki/Scumm-scripts>

ScummC ist ein unabhängig entwickeltes Tool, **nicht** der originale
LucasArts-Quellcompiler. Seine Funktionsnamen sind teils bewusst gegenüber
ScummVM umbenannt; für einen Vertrag ist daher der **v6-Opcode und sein
Bytecode-/Laufzeitverhalten** maßgeblich, nicht ein intuitiver API-Name.

## 3. Die tatsächliche Architektur: Skripte und Skript-Slots

### 3.1 Mehrere gleichzeitig aktive Skripte sind nativ

| Bytecode / ScummC | Befund | Konsequenz für Adventure Studio |
| --- | --- | --- |
| `0x5E` `startScript(flags, script, args)` | `VM`, `SCUMMC` | Separaten Skriptvorgang starten |
| `0x5F`, `0xBF` | `VM`, `SCUMMC` | Kurzformen für Start ohne/mit Flags |
| `0x60` `startObject` | `VM` | Objektgebundene Skripte starten |
| `0x77` `stopObjectScript` | `VM`, `SCUMMC` | Objektvorgang gezielt stoppen |
| `0x7C` `stopScript` | `VM`, `SCUMMC` | Globalen/lokalen Vorgang stoppen |
| `0x8B` `isScriptRunning` | `VM`, `SCUMMC` | Laufstatus abfragen |
| `0x6C` `breakHere` | `VM`, `SCUMMC` | Ausführungszeit an andere Skripte abgeben |
| `0xCA` `delayFrames` | `VM`, `SCUMMC` | Für eine definierte Zahl von Durchläufen aussetzen |
| `0xB0`–`0xB2` `delay*` | `VM`, `SCUMMC` | Zeitbasierte Aussetzung |
| `0x6A` `freezeUnfreeze` | `VM`, `SCUMMC` | Skripte mit Freeze-Zählung anhalten/fortsetzen |
| `0xD5` `jumpToScript` | `VM`, `SCUMMC` | Skriptkontext durch nächsten Vorgang ersetzen |

Laut ScummC-Dokumentation haben `startScript`-Flags mindestens zwei
bedeutende Bits: **freeze-resistant** und **recursive**. Ohne rekursiven
Start wird eine laufende Instanz derselben Skriptnummer vor dem neuen Start
beendet. Ein mehrfacher `freeze` benötigt entsprechend mehrfaches
`unfreeze`. Dies ist entscheidend für Hintergrundabläufe, Abbruch und
Dialogpausen. Die tatsächliche Slot-Belegung ist im Code von
`ScummEngine::runObjectScript` sichtbar.

**Nicht modellieren als:** native Threads mit garantierter Parallelität,
atomare Transaktionen oder unabhängige Timer. Die SCUMM-VM führt Skripte
kooperativ aus; Ablaufreihenfolge, Skript-Slots und Yield-Punkte sind Teil
der Engine-Semantik.

### 3.2 Vorhandene Warteoperationen

Unter `0xA9` sind in ScummC unter anderem beschrieben:

- `waitForActor`: bis Actor nicht mehr läuft (`0xA9A8`).
- `waitForMessage`: solange Text angezeigt wird (`0xA9A9`).
- `waitForCamera`: bis Kamerabewegung endet (`0xA9AA`).
- `waitForSentence`: bis Sentence-Skript endet (`0xA9AB`).
- `waitForAnimation`: in ScummC dokumentiert (`0xA9E2`), dort jedoch
  **mit Fragezeichen** bei der Semantik. Im untersuchten ScummVM-Quellstand
  wartet der Befehl tatsächlich, solange der Actor im aktuellen Raum ist
  und `_needRedraw` gesetzt ist – **nicht** explizit bis zum Animationsende.

**Wichtig:** Ein frei definierbares `on_frame(45)` oder `on_marker("contact")`
ist **nicht** als Standard-v6-Callback nachgewiesen. Wir dürfen diese
Autorensemantik erst anbieten, wenn sie aus originalen Kostümkommandos,
Actor-Variablen oder einem vom Compiler erzeugten Skriptzustandsautomaten
verifizierbar und zuverlässig übersetzbar ist.

## 4. Eingabe läuft über die SCUMM-Skripte

Die ursprüngliche Laufzeit nutzt nicht automatisch eine allgemeine
`onClick`-Callback-API.

Laut ScummC-Engine-Dokumentation gibt es diese besonders relevanten
**systemgesteuerten Skripte**:

| Engine-Anschluss | Aufgabe |
| --- | --- |
| `VAR_VERB_SCRIPT` | Maus-/Tastatureingabe an Verb, Raum, Tastatur delegieren |
| `VAR_SENTENCE_SCRIPT` | Aus den gewählten Verben/Objekten gebildete Aktion behandeln |
| `VAR_INVENTORY_SCRIPT` | Inventar-/Besitzer-/Namensänderungen behandeln |
| `VAR_PRE_ENTRY_SCRIPT` / `VAR_POST_ENTRY_SCRIPT` | Raumstart vor/nach lokalen Skripten |
| `VAR_PRE_EXIT_SCRIPT` / `VAR_POST_EXIT_SCRIPT` | Raumwechsel vor/nach lokalen Skripten |
| `VAR_CAMERA_SCRIPT` | Reaktion auf Kamerabewegung |
| `VAR_CUTSCENE_START_SCRIPT` / `VAR_CUTSCENE_END_SCRIPT` | Cutscene-Grenzen |

Der Verb-Handler erhält laut ScummC-Skriptbeschreibung eine Eingabeart
(Verb-/Raumbereich/Tastatur), Kommando und Taste. Das Sentence-Skript erhält
Verb, erstes und zweites Objekt. `doSentence` (v6 `0x83`) ist ein eigener
Engine-Vorgang, nicht nur ein direkter Funktionsaufruf.

**Folge für Achterbahn/Minispiele:** Eingaben während einer Sequenz müssen
auf einem **originalen** Eingabeweg angenommen werden, etwa über
zustandsabhängige Verb-/Raum-/Tastaturverarbeitung. Ob und wie Cutscene-
Freeze dabei wirkt, ist pro Ablauf zu testen. Wir dürfen nicht von einer
zusätzlichen Input-Schicht außerhalb von SCUMM ausgehen.

## 5. Räume, Objekte und Actors

### 5.1 Räume und Raumressourcen

Die ScummC-Grammatik definiert unter anderem:

- `image` für Raumhintergrund;
- `zplane` für Masken;
- `boxd`/`boxm` für Walkbox-Geometrie und Verbindungen;
- `scal` für Skalierungsdaten;
- `trans` für Transparenz;
- lokale und globale `script`, `object`, `cost`, `chset`, `sound`, `voice`.

Es existieren v6-Operationen für `loadRoom`, `loadRoomWithEgo`,
`panCameraTo`, `actorFollowCamera`, `setCameraAt`, `walkActorTo`,
`walkActorToObj`, `putActorAtXY` und `putActorAtObject` (`VM`).

**Generator-Konsequenz:** Nicht zwei Erzähl-Szenen für die zwei Hälften
eines scrollenden Raums erzeugen. Room- und Weltkoordinaten bleiben
grundsätzlich getrennt von Bildschirmkoordinaten.

### 5.2 Objekte sind Original-SCUMM-Objekte

ScummC-Objekte besitzen nach Dokumentation: `x/y`, `w/h`, `hs_x/hs_y`,
Richtung, visuelle `states`, `owner`, `parent`, `parent_state` und `class`.
Das Elternobjekt muss im selben Raum liegen; `parent_state` kann steuern,
wann ein Kindobjekt vorhanden ist. Das ist ein **originaler** Mechanismus
für Schrank/Tür/Innengegenstand, nicht eine neu zu erfindende Hierarchie.

| Bytecode | Wirkung |
| --- | --- |
| `0x6F` / `0x70` | Objektzustand lesen/setzen |
| `0x71` / `0x72` | Besitz setzen/abfragen |
| `0x6D` / `0x6E` | Objektklassen prüfen/setzten |
| `0x61` / `0x62` | Objekt zeichnen/positionieren |
| `0x84` | `pickupObject`: in ScummC als Eigentumswechsel zu `VAR_EGO`, Objektstatus und Inventarskript beschrieben |
| `0x8D` / `0x8E` | Objektkoordinate abfragen |
| `0xA0` | Objekt suchen |

**Begrenzung:** `parent` beschreibt keine beliebige Bindung an einen
Actor-Knochen oder Animationsframe. Ein Schlüssel, der einem Gürtel folgt,
ist damit **noch nicht** gelöst. Optionen wie Actor-Kostümteil, periodisches
Positionieren eines Raumobjekts oder hit-test im Sentence-Skript erfordern
einen separaten Probeaufbau.

### 5.3 Actor, Kostüme und Laufverhalten

Bestätigte VM-/ScummC-Bausteine sind `animateActor` (`0x82`),
`setActorCostume` (Actor-Operation), `setActorAnimSpeed`,
`setActorWalkScript`, `setActorTalkScript`, Layer, Walkbox-Flags,
Walkgeschwindigkeit, Kostüm-Animationvariablen und Actor-Animationszähler.

ScummC erzeugt Kostüme mit dem separaten `cost`-Compiler. Die Grammatik
beschreibt Bilder, Limbs, Animationssequenzen und räumliche Bild-Offsets.
Es ist **nicht** zulässig, beliebige Sprite-Sheet-Frames ohne Prüfung als
SCUMM-Kostümanimation anzunehmen. Insbesondere brauchen wir einen realen
Test, wie das `cost`-Format Animationsende, wiederholte Animationen,
Bewegung und synchronisierte Effekte verarbeitet.

## 6. Cutscene, Eingriff und Skip – native Werkzeuge

`0x68` beginnt eine Cutscene, `0x67` beendet sie. ScummC kennt einen
`cutscene (...) { ... }`-Block und
`try { ... } override { ... }` mit `0x95`/`0x96`-Override-Befehlen.
Bei einer Skip-Eingabe kann der Interpreter in den Override-Pfad springen;
ScummC dokumentiert dabei `VAR_OVERRIDE`.

Für eine normale Auto-Abfahrt bieten sich die **originalen** Cutscene-
Operationen an. Ein reiner Skip darf den Fahrzeug-/Raum-/Figurenzustand
nicht inkonsistent hinterlassen.

**Achterbahn mit aktivem Eingriff:** Solange der Spieler während der Fahrt
handeln muss, dürfen wir sie nicht einfach in eine alle Eingaben blockierende
Cutscene kapseln. Die erste Hypothese ist ein normal gestartetes,
kooperativ laufendes Skript mit zustandsabhängiger Input-Verarbeitung.
Falls eine Cutscene einzelne Eingaben zulassen kann, muss dies im Zielprofil
gesondert nachgewiesen werden.

## 7. SCUMM-native Umsetzung der beiden Schlüsselszenen

### A. Auto fährt weg – geplanter Bytecode-Vertrag

| Phase | Originale Operation/Fähigkeit | Status |
| --- | --- | --- |
| Auto anklicken | Objekt-Verb-/Sentence-Skript | `VM` + `SCUMMC` |
| Sam zum Auto schicken | `walkActorToObj` | `VM` |
| Auf Ankunft warten | `waitForActor` | `SCUMMC`, Interpreterprüfung offen |
| Max unabhängig bewegen | `startScript` + Actor-Walk | `VM`; Zusammenspiel offen |
| Einsteigen/Auto bewegen | `animateActor` / Objektzustände, ggf. Script-Bewegung | `VM`; konkrete Darstellung offen |
| Motor-/Fahrtgeräusch | `startSound` (`0x74`) | `VM`; Soundressource offen |
| Kamera schwenken | `panCameraTo` / `actorFollowCamera` | `VM` |
| Spielereingabe sperren | `cutscene`/Input-Freeze, geeigneter Umfang | `SCUMMC`; Verhalten offen |
| Fahrtende und Szenenwechsel | `loadRoomWithEgo` oder entsprechende Übergangsoperation | `VM` |
| Skip | `try`/`override` | `SCUMMC`; Endzustand muss geprüft werden |

**Keine** selbst erfundene `parallel`-VM-Instruktion: Der Generator kann
mehrere native `startScript`-Operationen erzeugen und mit nativen Waits/
Scriptzuständen koordinieren.

### B. Achterbahn/Kabel – geplanter Bytecode-Vertrag

1. Ein **laufendes Skript** ändert die Fahrphase und die sichtbaren
   Darstellungen; es gibt seine Rechenzeit an die VM zurück.
2. Eine native Input-Verarbeitung akzeptiert die betreffende Aktion.
3. Das Sentence-/Objektskript prüft eine **SCUMM-Variable** wie
   `ride_phase == near_wires`, nicht die Farbe eines Screenshots.
4. Bei Erfolg wird ein persistentes Event-Latch gesetzt. Das laufende
   Skript bemerkt dies und verzweigt zur Kurzschlussfolge.
5. Bei Fehlschlag beendet oder wiederholt die Sequenz gemäß Regeln.
6. Für die genaue Phasengrenze werden zuerst die bereits vorhandenen
   Animation-/Wait-/Counter-Funktionen technisch geprüft. Nur wenn
   zwingend nötig und kompatibel, erzeugen wir eine deterministische
   vom Skript gesteuerte Frame-Phasenmaschine.

Das ist eine **technische Implementierungshypothese**, noch kein
ScummVM-Spieltest. Es wäre falsch, einen universellen `on_frame`-Handler
als bereits vorhandene VM-Funktion zu dokumentieren.

## 8. Save/Load und Skriptlebensdauer

ScummVM behandelt Save/Load in `engines/scumm/saveload.cpp` mit eigenem
Serializer und Spiel-/Versionsbedingungen. Daraus folgt **nicht**, dass
alle beliebigen neuen Vorgangsmodelle unseres Autorsystems automatisch
korrekt gespeichert werden.

Zu prüfen sind insbesondere:

1. Aktive Skript-Slots, Wartezustand, Verzögerungszähler, Freeze-Zustände.
2. Actor-Bewegung/Kostümzustand und sichtbare Objektzustände.
3. Besitz-/Inventarvariablen und globales Event-Latch.
4. Raumwechsel während parallel laufender Vorgänge.
5. Override-/Cutscene-/Eingabemodus beim Laden.

Vor einer Zusage „Save/Load mitten in der Achterbahn“ ist ein **gezielter
Test** nötig. Alternativ kann das Spiel das Speichern während dieser
Sequenz bewusst verhindern, sofern der originalen Engine-Semantik entsprechend.

## 9. Harte Kompatibilitätsgrenze: ScummC und unverändertes ScummVM

Die ScummC-README warnt ausdrücklich: Eigene ScummC-Spiele werden regulär
mit einer **ScummVM-Erkennungserweiterung** erkannt; alternativ kann man
eine Day-of-the-Tentacle-Identität (`tentacle`, Key `0x69`) als
Kompatibilitätstrick verwenden. Letzteres aktiviert möglicherweise
spielspezifische Interpreterpfade und beweist **keine generische
Erkennung oder Release-Tauglichkeit**.

Unser bisheriger CI-Ansatz nutzt diese isolierte DOTT-Testidentität.
Das bleibt ein nützlicher **Laufzeitnachweis einzelner Ressourcen und
Operationen**, darf aber nicht als abgeschlossene native Erkennung
verkauft werden. Die finale Erkennung selbst bleibt ein separates Gate.

Weitere Risiken:

- Bestimmte v6-Operationen können in ScummC unvollständig oder anders benannt
  sein, obwohl ScummVM den Bytecode unterstützt.
- Spielabhängige ScummVM-Workarounds machen eine genaue Zielversion nötig.
- Alte und neue Originalinterpreter dürfen nicht mit derselben
  Kompatibilitätsaussage zusammengefasst werden.
- Ressourcenlimits, Anzahl der Skript-Slots, Kostümlimits und Savegame-
  Grenzen müssen separat anhand des gepinnten Quellstands validiert werden.

## 10. Konkreter Forschungs- und Implementierungsplan

### Gate R0: eingefrorene Original-Semantik

- ScummVM-Commit und ScummC-Commit pinnen.
- V6-Opcode-/ScummC-Funktionstabelle maschinenlesbar abgleichen.
- Für benötigte Funktionen die tatsächlichen Zustands-, Yield- und
  Abbruchregeln aus der Implementierung dokumentieren.
- Noch nicht geprüfte Funktionen **nicht** in den Compilervertrag aufnehmen.

### Gate R1: Native Skriptabläufe

- Zwei parallele Skripte mit `startScript` und unabhängigen Actor-Aktionen.
- Nachweis: Ein Skript darf warten, ohne das andere zu blockieren.
- Stop-/Freeze-/Restart-Tests einschließlich mehrfacher Starts.

### Gate R2: Originale Eingabeverarbeitung während Hintergrundablauf

- Eine laufende, periodische Raumaktion und gleichzeitig eine zulässige
  Verb-/Objektaktion.
- Nachweis: Die Eingabe beeinflusst den Skriptzustand im nächsten
  wohldefinierten Verarbeitungsschritt.

### Gate R3: Inszenierte Abfahrt

- Gehen, warten, zwei Figuren, Objektzustand, Kamera, Sound, Raumwechsel.
- Normale Abfahrt **und** Skip-Pfad ergeben denselben Endzustand.

### Gate R4: Zeitfenster ohne Fremd-Engine

- Originale SCUMM-Eingabe während einer laufenden Sequenz.
- Negative Fälle: zu früh, zu spät, mehrfach, ungültiges Ziel.
- Positiver Fall: Zustandswechsel und Folgeanimation ohne verlorene
  oder doppelt ausgeführte Aktionen.

### Gate R5: Laufzeit-Persistenz

- Save/Load vor und nach R3/R4, anschließend mitten in einem
  geeigneten, laufenden Skript (falls original unterstützt).

### Gate R6: Bewegliche Ziele und NPCs

- Native Kostüm-/Actor-Animation, gebundener oder scriptgeführter
  Hotspot, Patrouillenwechsel und Abbruch.
- Erst nach tatsächlichem Nachweis einen allgemeinen Compilerbaustein
  für bewegliche Interaktionsziele freigeben.

## 11. Entscheidungen nach dieser Erstuntersuchung

1. **Kein Ersatz-Scheduler** in Adventure Studio; Skriptgraphen werden auf
   originalen SCUMM-v6-Start-, Wait-, Freeze- und Stop-Operationen abgebildet.
2. **Keine generische `on_frame`-API versprechen**, bevor ein nativer
   Kostüm-/Script-Ereignisweg belegt ist.
3. **Verben, Sentences und Inventar** über die originalen Engine-Skripte
   verwalten, nicht über eine zweite, parallele Eingabemaschine.
4. **Objektzustände, Besitz und Elternobjekte** zunächst mit den vorhandenen
   SCUMM-Objektfunktionen abbilden.
5. **Cutscene-Skip** mit den originalen Cutscene-/Override-Mechanismen
   erforschen; spielbare Sequenzen separat behandeln.
6. **Kein falscher Kompatibilitätsbeweis** durch DOTT-Tarnidentität.

Diese Regeln sind die Ausgangsbasis für den nächsten Compilerentwurf –
nicht bereits die Erlaubnis, all diese Mechaniken als unterstützt auszuweisen.
