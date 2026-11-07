# Source-Audit: ScummC + ScummVM, originale SCUMM-v6-Semantik

Stand: 2026-11-07. **Quellcodeanalyse, keine Implementierung und kein
Laufzeitnachweis.** Grundlage ist der Mechanik-Katalog
[`scumm-adventure-mechanics.md`](scumm-adventure-mechanics.md).

Dieses Dokument präzisiert und korrigiert die erste
[`scumm-v6-runtime-contract.md`](scumm-v6-runtime-contract.md)-Bestandsaufnahme.
Insbesondere darf `waitForAnimation` **nicht** als generisches Warten auf
das Ende einer Animation verstanden werden.

## 1. Untersuchte Quellstände und Verantwortung

ScummVM implementiert die **Laufzeit**; ScummC erzeugt **Bytecode und
Ressourcen**. Ein in ScummVM vorhandener Opcode ist nicht automatisch
von ScummC korrekt emitierbar, und ein akzeptierter Bytecode beweist
noch keine funktionierende Spielsituation.

Aus GitHub gelesene Dateien (Blob-SHA als reproduzierbarer Dateiverweis;
für weitere Entwicklungsarbeit müssen zusätzlich vollständige
Repository-Commit-SHAs gepinnt werden):

| Projekt | Originaldatei | Blob-SHA |
| --- | --- | --- |
| ScummVM | [`script_v6.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/script_v6.cpp) | `e1e99d50bb617db32093f3b150984d45732610e9` |
| ScummVM | [`script.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/script.cpp) | `bd3c285c2e4ffc41154216f6ebdeee40567e7ee7` |
| ScummVM | [`scumm.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/scumm.cpp) | `88e087d765ee1065b22b59403bf3511f590a6a2f` |
| ScummVM | [`verbs.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/verbs.cpp) | `1637dd33c0e797480a5f158e4110567849c10e3d` |
| ScummVM | [`actor.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/actor.cpp) | `7c48e4923aa7efb49d1095398beffe292bc87ffa` |
| ScummVM | [`costume.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/costume.cpp) | `aab00a030b9cf678cb87baacbe5136d6cd34746d` |
| ScummVM | [`saveload.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/saveload.cpp) | `d1d7a7646b6212826466dcc7b5c4e156cb71fc16` |
| ScummC | [`scc_func.h`](https://github.com/AlbanBedel/scummc/blob/master/scc_func.h) | `88b10a76a9e907ec44db7f4c0a4b7b43f25afd6f` |
| ScummC | [`scc_code.c`](https://github.com/AlbanBedel/scummc/blob/master/scc_code.c) | Compileraufruf/Opcode-Encoding geprüft |
| ScummC | [`cost_parse.y`](https://github.com/AlbanBedel/scummc/blob/master/cost_parse.y) | `c2b8fc3939566d0dcef6b148f5e0b7a9907b38f4` |
| ScummC | [`examples/road/common.scc`](https://github.com/AlbanBedel/scummc/blob/master/examples/road/common.scc) | `9014ecfa2365646c852d6942174893d6c67eb72d` |
| ScummC | [`examples/openquest/skyline.scc`](https://github.com/AlbanBedel/scummc/blob/master/examples/openquest/skyline.scc) | Native Cutscene-/Actor-Praxis geprüft |

Diese Prüfung betrachtet ScummVM als dokumentierte Open-Source-Implementierung
der SCUMM-VM. **Identisches Verhalten des proprietären originalen
LucasArts-Interpreters** ist damit noch nicht automatisch nachgewiesen.

## 2. Ablauf eines SCUMM-v6-Frames: nicht frei definierbar

In `ScummEngine::scummLoop(int delta)` (`scumm.cpp`) lässt sich die
für v6 relevante Reihenfolge nachvollziehen:

1. Zeitvariablen aktualisieren und ausstehende Skript-Delays abbauen.
2. `processInput()` nimmt Eingaben an und aktualisiert Eingabestatus.
3. Für v6 (`_game.version < 7`) `runAllScripts()`, danach
   `checkExecVerbs()`.
4. `checkAndRunSentenceScript()` verarbeitet den Sentence-Pfad.
5. `walkActors()`, `moveCamera()`, `updateObjectStates()`.
6. Darstellung und Actor-Animation; `VAR_MAIN_SCRIPT` kann eine weitere
   Skript-Ausführung anstoßen.

Die Reihenfolge ist für **Zeitfenster und Interaktion während Animationen**
wesentlich. Ein Skript kann in einem Frame eine Variable prüfen, bevor die
gezeichnete Actor-Pose für denselben Frame fortgeschritten ist. Das genaue
Costume-Update muss für die Zielversion im Actor-Drawing-Pfad festgelegt
werden, bevor eine Frame-Index-API versprochen wird.

Die Eingabe- und Skriptphasen **nicht** durch einen eigenen Echtzeit-Loop
in Adventure Studio ersetzen. Ein compilerseitiges Ereignisfenster muss
mit der originalen VM-Reihenfolge funktionieren.

## 3. Skript-Scheduler – präzise Befunde

### 3.1 Ausführung

`ScummEngine::runAllScripts()` (`script.cpp`) setzt für alle Slots
`didexec=false` und durchläuft ausführbare Slots. Für reguläres v6 wird
eine Prioritätsrunde verwendet; die separaten `cycle`-Prioritäten im Code
sind im Wesentlichen für spätere HE-Versionen relevant.

Jeder Slot speichert unter anderem Skriptnummer, Ausführungsposition,
`status`, `where`, `recursive`, `freezeResistant`, `freezeCount`,
`delayFrameCount` und `cutsceneOverride`.

`startScript()` in `script_v6.cpp` ruft mit den zwei Flag-Bits
`runScript(script, freezeResistant, recursive, args)` auf.

- **Nicht rekursiv:** `runScript` stoppt eine ältere Instanz derselben
  Skriptnummer, bevor eine neue Instanz startet.
- **Rekursiv:** Mehrfachinstanzen sind möglich, solange Slots verfügbar
  sind; sie brauchen eigenen Zustand und klare Lebensdauerregeln.
- **`breakHere`:** aktualisiert den Skriptpointer und setzt den aktuell
  laufenden Skriptkontext zurück, damit andere Slots laufen können.
- **Delay:** Skript-Slot wird pausiert; der Delay wird in `scummLoop`
  schrittweise abgebaut.
- **Freeze:** `freezeScripts` berücksichtigt den `freezeResistant`-Status;
  mehrfaches Freezen wird durch `freezeCount` gezählt. Auch Sentence-
  Queues besitzen einen Freeze-Zähler.

**Kritischer Befund:** `stopScript` und `stopObjectScript` lösen für
SCUMM-Versionen ab 5 einen Interpreterfehler aus, wenn das zu stoppende
Skript eine aktive Cutscene/Override besitzt. Wir dürfen daher keine
beliebige allgemeine `cancel()`-Semantik über alle Skriptarten annehmen.

### 3.2 `wait` ist eine Rücksprung-/Yield-Operation

`ScummEngine_v6::o6_wait()` liest einen Sub-Opcode. Ist die jeweilige
Wartebedingung noch aktiv, setzt es den Ausführungspointer um ein
relatives Offset zurück und ruft `o6_breakHere()`. Im nächsten
Skriptdurchlauf wird der Zustand erneut geprüft.

| Native Warteart | Bedingung im Interpreter |
| --- | --- |
| `SO_WAIT_FOR_ACTOR` | Actor bewegt sich (`_moving` bei v6) |
| `SO_WAIT_FOR_MESSAGE` | `VAR_HAVE_MSG` ist gesetzt |
| `SO_WAIT_FOR_CAMERA` | Für v6 liegt Kamera-`cur.x/8` nicht bei `dest.x/8` |
| `SO_WAIT_FOR_SENTENCE` | Sentence-Queue oder Sentence-Skript aktiv |
| `SO_WAIT_FOR_ANIMATION` | Actor ist im aktuellen Raum und `_needRedraw` ist gesetzt |
| `SO_WAIT_FOR_TURN` | Actor dreht sich noch (`MF_TURN`) |

**Warnung:** `SO_WAIT_FOR_ANIMATION` testet bei ScummVM **`_needRedraw`**,
nicht ein explizites Animation-Ende-Flag. Es ist falsch, diesen Befehl
ohne zusätzlichen Test als „warte bis die Animation vollständig fertig ist“
zu übersetzen. Das gilt insbesondere für ein Timingrätsel!

## 4. Originales Costume-Format: `COUNT` als synchronisierbares Signal

Dies ist der wichtigste Befund für das Achterbahnbeispiel.

### 4.1 Compilerseite

`cost_parse.y` enthält explizit diese Costume-Kommandos:

- `SHOW` (`0x7A`), `HIDE` (`0x79`), `NOP` (`0x7B`),
- `COUNT` (`0x7C`),
- `SOUND(n)` (`0x70` als interne Kommandogruppe; Soundindex 1–8),
- Bildreferenzen pro Limb/Animationssequenz.

Der Parser erzeugt für `COUNT` ausdrücklich `COST_CMD_COUNT`. Die
Compilergrenzen enthalten `COST_MAX_LIMBS` sowie bis zu 63 Animationen
und maximal 127 Limb-Kommandos pro Eintrag im untersuchten Parser;
die Grenzen sind **ScummC-spezifisch** und müssen im tatsächlichen
Asset-Contract gesondert validiert werden.

### 4.2 Interpreterseite

`ClassicCostumeLoader::increaseAnim()` (`costume.cpp`) verarbeitet
`0x7C` durch Erhöhen von `Actor::_cost.animCounter`. Der v6-Opcode
`0xAB` (`o6_getActorAnimCounter`) macht diesen Wert für Skripte
abfragbar. Außerdem behandelt der Decoder bei v6 Sound-Kommandos
`0x71`–`0x78` durch `addSoundToQueue`.

`Actor::animateCostume()` ruft den Costume-Decoder abhängig von
`_animSpeed`/`_animProgress` auf und setzt bei geänderten Bildern
`_needRedraw`.

**Folgerung:** Ein framebezogenes, **native SCUMM-kompatibles**
Synchronisationssignal ist grundsätzlich denkbar: gezieltes `COUNT` im
Costume-Datenstrom, Auswertung von `getActorAnimCounter` im Skript.

**Noch offen:** Zählerinitialisierung beim Start neuer Animationen,
Überläufe, Wiederholung von Limb-Sequenzen, mehrere Limbs, genaue
Reihenfolge zwischen Costume-Update und Skriptabfrage sowie die Fähigkeit
des ScummC-`cost`-Generators, die konkrete gewünschte Animation
unverändert auszugeben. Ein Counter ist **nicht** automatisch ein
benanntes `on_frame`-Ereignis.

### 4.3 Präzise Aussage für Adventure Studio

Erst nach einem Interpreter-Probe-Test könnte ein deklarativer Marker
kompiliert werden als:

1. Costume-Kommandostelle mit `COUNT`.
2. Ein SCUMM-Skript vergleicht den Actor-Animationszähler mit einem
   vorher bekannten Wert.
3. Eine Gameplay-Variable repräsentiert das aktive Interaktionsfenster.
4. Das originale Verb-/Sentence-Skript kann während des Fensters reagieren.

Das ist näher an SCUMM als ein neu erfundener Runtime-Callback.

## 5. Eingabe: DOTT und Sam & Max sind unterschiedlich

`checkExecVerbs()` in `verbs.cpp` beendet sich sofort bei
`_userPut <= 0` oder ohne Eingabe. Für reguläre v6-Spiele unterscheidet
es Tastatur, Verb-Leiste und Raumklick. `runInputScript()` in `script.cpp`
startet `VAR_VERB_SCRIPT` mit Eingabebereich, Kommando und Modus.

**Wesentliche Spielvariante:** Für `GID_SAMNMAX` führt der v6-
Interpreter den Mausklick ausdrücklich vereinfacht über
`kSceneClickArea` aus. Der Quellcode kommentiert dies als Unterschied
zur klassischen DOTT-Verb-Oberfläche.

Deshalb müssen wir **zwei Dinge trennen**:

- **SCUMM-v6-VM-Fähigkeit:** Skriptbasierte Eingabeverarbeitung.
- **Spiel-Bootstrap:** Wie Verben, Maus und `VAR_VERB_SCRIPT` zu
  Autorenspielaktionen werden.

Ein Wechsel von DOTT- zu Sam-&-Max-artiger Oberfläche ist nicht nur
ein Austausch von Bildern. Er betrifft die Eingabe-Skripte und teilweise
den von ScummVM gewählten spielabhängigen Pfad.

Für zeitabhängige Interaktionen gilt zusätzlich: Wenn `_userPut` durch
eine Cutscene auf 0 gesetzt wurde, kommen normale Klicks nicht durch
den `checkExecVerbs`-Pfad. Eine spielbare Fahrt darf daher nicht einfach
in einer alle Eingaben blockierenden Cutscene stattfinden.

## 6. Cutscene, Skip, Abbruch: echte Kontrollflussregeln

`ScummEngine::beginCutscene()` vermerkt im aktuellen Skript den aktiven
Cutscene-/Override-Zustand und erhöht einen Cutscene-Stack. Start- und
End-Hooks werden aus `VAR_CUTSCENE_START_SCRIPT` beziehungsweise
`VAR_CUTSCENE_END_SCRIPT` aufgerufen.

`beginOverride()` speichert den Bytecode-Offset und das aktuelle Skript;
`abortCutscene()` kann den Skriptpointer direkt an die gespeicherte
Stelle verschieben und `VAR_OVERRIDE=1` setzen.

Das ist **kein** Aufruf einer frei benannten `onSkip()`-Funktion.
Unser Compiler muss die echten Bytecode-Sprünge und die danach
erforderlichen Weltzustandsänderungen korrekt erzeugen.

Das ScummC-Beispiel `examples/openquest/skyline.scc` verwendet tatsächlich
`cutscene`, `try/override`, Actor-Kostüm, Laufbewegung, `waitForActor`
und Sprache. `examples/road/common.scc` implementiert Input-, Sentence-,
Inventar- und Cutscene-Start-/Endskripte. Diese Originalbeispiele sind
für unser eigenes Bootstrap-Design wichtiger als frei erfundene
Pseudo-APIs.

## 7. Save/Load: Quellcode zeigt mehr als die alte Bestandsaufnahme

In `saveload.cpp` wird `ScriptSlot` unter anderem mit Ausführungs-Offset,
Delay, Skriptnummer, `delayFrameCount`, Status, Script-Typ,
`freezeResistant`, `recursive`, `freezeCount`, `cutsceneOverride` und
Zyklus serialisiert. Auch die Slot-Liste wird gespeichert.

Cutscene-Stack, Override-Offsets und aktuelle Sentence-Zustände werden
ebenfalls in der SCUMM-Serialisierung behandelt. `Actor::saveLoadWithSerializer`
serialisiert unter anderem `animCounter`, Costume-/Frame-/AnimSpeed-
Felder und die Bewegungsdaten.

**Schlussfolgerung:** ScummVM ist grundsätzlich darauf ausgelegt,
laufende SCUMM-Skripte und Actor-Zustände zu speichern. Unsere alte
Formulierung „vollständig offen“ war zu vorsichtig.

**Trotzdem offen:** Ein wirkliches Adventure-Studio-Save/Load-Feldexperiment
mit eigens erzeugten Costume-Kommandos, Zustandsfenstern und
Cutscene-Sprüngen; Kompatibilität zum originalen DOS-Interpreter;
spielabhängige ScummVM-Sonderbehandlungen.

## 8. ScummC: Wie Code wirklich entsteht

`scc_func.h` enthält eine **Compiler-Funktionstabelle** mit Namen,
Opcode, Argumentanzahl, Typen und impliziten Spezialargumenten.
Beispiele im Quellcode:

| Name | Kodierung | Besonderheit |
| --- | --- | --- |
| `startScript` | `0x5E` | Flags, Skript, Argumentliste |
| `waitForActor` | `0xA9A8` | impliziter relativer Rücksprung-Offset |
| `waitForAnimation` | `0xA9E2` | ebenfalls impliziter Rücksprung-Offset |
| `setObjectState` | `0x70` | zwei normale Werte |
| `setActorAnimVar` | `0x9DC6` | Actor-Operations-Subopcode |

In `scc_code.c` erzeugt der Compiler bei Opcodes bis `0xFF` ein Byte,
bei Sub-Op-Codes eine zweibyteige Kodierung. Für
`SCC_FA_SELF_OFF` wird der negative relative Offset anhand der
emittierten Codelänge geschrieben. Dies ist notwendig, damit die
Interpreter-`wait`-Operation beim nächsten Skriptdurchlauf erneut
auf dem richtigen Bytecode beginnt.

**Konsequenz:** Adventure Studio darf nicht „SCUMM-Funktionen“ durch
unkontrolliertes String-Zusammenfügen approximieren. Der Generator soll
typisierte SCUMM-Aktionen mit genau dem ScummC-Funktionsvertrag
übersetzen und vor dem Linken alle Parameter und Varianten prüfen.

## 9. Abgleich mit dem aktuellen Adventure Studio

Aktuell erzeugt `src/adventure_studio/scumm_assets.py` Raumobjekte,
Objektzustände, Verben, Inventarkombinationen und einige Dialogskripte.
Die Datei sagt selbst, dass das experimentelle **externe Bootstrap**
Verben, Actor und Benutzeroberfläche liefert. Diese Grenze bleibt wichtig.

Der bisherige Echtspieltest beweist einzelne Spielaktionen über ein
angepasstes DOTT-kompatibles ScummC-Fixture. Er beweist **noch nicht**:

- ein selbstständiges originales Adventure-Studio-Bootstrap;
- Actor-Kostümkommandos `COUNT`/`SOUND` mit korrekter Phase;
- unabhängig aktive und sicher abbrechbare Script-Ketten;
- Eingaben während laufender Actor-Animationen;
- Skip von verschachtelten Cutscenes;
- Save/Load mitten in solchen neuen Vorgängen;
- spielunabhängige Erkennung neuer Game-IDs in unverändertem ScummVM.

Diese Unterscheidung verhindert, dass wir aus vorhandenen Quellfunktionen
versehentlich bereits fertige Generatorfähigkeiten ableiten.

## 10. Architekturentscheidungen aus dem Audit

1. **Originaler Scheduler zuerst.** Aus Autorenvorgängen werden
   SCUMM-Skriptstarts, Warteoperationen und explizite Abbruchpfade.
2. **Keine allgemeine `cancel()`-Operation über Cutscene-Skripte.**
   Aktive Overrides müssen vor Skriptende korrekt aufgelöst werden.
3. **Keine naive `waitForAnimation=Ende`-Abbildung.** Für Synchronisierung
   zuerst `COUNT`/Animationszähler, `waitForActor` und explizite
   Zustandsvariablen erforschen.
4. **Originales Verb-/Sentence-Modell.** Eingaben werden von SCUMM-
   Skripten verarbeitet, nicht von einem zweiten Engine-Loop.
5. **Getrennte Bootstrap-Profile.** DOTT-artige und Sam-&-Max-artige
   Oberflächen können unterschiedliche Engine-Pfade nutzen; zunächst
   auf einen präzisen Zielmodus festlegen.
6. **Save/Load als VM-Feature nutzen.** Das eigene Vorgangsmodell muss
   sich auf tatsächlich serialisierte SCUMM-Zustände abbilden lassen.
7. **Ressourcencompiler ernst nehmen.** Costume-`COUNT` und `SOUND` aus
   dem echten ScummC-Parser nutzen; Limits und Bytecode-Formate gegen
   die tatsächlich verwendete Toolchain validieren.

## 11. Noch ungeklärte Codepfade vor einer Implementierung

| Frage | Nächste Quell-/Experimentprüfung |
| --- | --- |
| Wann genau wird `COUNT` relativ zu `runAllScripts` ausgeführt? | Actor-Update-/Zeichenpfad in `scumm.cpp`, `actor.cpp`, `costume.cpp` bis auf Tickebene verfolgen |
| Kann `COUNT` sicher ein ein-Frame-Fenster markieren? | `cost`-Fixture erzeugen, Skriptzähler ausgeben, mehrere Laufgeschwindigkeiten prüfen |
| Was ist eine sichere Skript-Abbruchpolitik? | `stopScript`, `stopObjectScript`, `begin/endCutscene`, `abortCutscene` + aktive/nestende Overrides verfolgen |
| Wie werden laufende lokale Skripte beim Raumwechsel behandelt? | `startScene`, Ressourcenauslagerung, `runExitScript`/`runEntryScript` prüfen |
| Kann ein Hotspot einem bewegten Actor folgen? | `findObject`, `drawObjectAt`, Actor-/Objektkoordinaten und Klick-Dispatch prüfen |
| Welche Spiel-Erkennung gilt für eigene Projekte? | ScummVM-Detection-Tabellen/ScummC-Patches und separates Original-DOS-Profil |
| Welche ScummC-Kostümlimits sind wirklich akzeptabel? | `cost_parse.y` + `scc_cost.c` gegen ClassicCostumeLoader-V6-Formate prüfen |

## 12. Vorgehen ab hier

**Noch keine neue Gameplay-Abstraktion implementieren.** Zuerst die
offenen Codepfade zu (a) Costume-Counter/Timing,
(b) Eingabe während Animation und (c) Cutscene-Abbruch vollständig
verfolgen. Danach ein minimales Original-SCUMM-v6-Fixture spezifizieren,
das die Semantik überprüft, **bevor** das Autorenmodell erweitert wird.

Das ist die zu bevorzugende Richtung: SCUMM-Code und -Datenvertrag
bestimmen das Adventure-Studio-Modell, nicht umgekehrt.
