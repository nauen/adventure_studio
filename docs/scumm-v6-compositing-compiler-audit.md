# SCUMM v6: Bildkomposition, Z-Masken und ScummC-Compilerpfad

Stand: 2026-11-07. **Direkte Quellcodeanalyse, kein erfolgreich kompilierter
Spiel-Export und keine Verifikation gegen einen proprietären LucasArts-Interpreter.**
Dieser Nachtrag vertieft den
[cineastischen Source-Audit](scumm-v6-cinematic-source-audit.md).

## 1. Referenzquellen

Die folgenden Inhalte wurden aus GitHub gelesen; die SHAs beziehen sich auf
Datei-Blobs und nicht auf einen gemeinsamen Repository-Commit.

| Projekt | Originaldatei | Blob-SHA |
| --- | --- | --- |
| ScummVM | [`actor.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/actor.cpp) | `7c48e4923aa7efb49d1095398beffe292bc87ffa` |
| ScummVM | [`gfx.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/gfx.cpp) | `bf85f13c3ab30c5c761083bc20af593404af1213` |
| ScummVM | [`costume.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/costume.cpp) | `aab00a030b9cf678cb87baacbe5136d6cd34746d` |
| ScummVM | [`object.cpp`](https://github.com/scummvm/scummvm/blob/master/engines/scumm/object.cpp) | `0e97ae972a1abfa8c2277fac2d8ed65f00dff412` |
| ScummC | [`scc_func.h`](https://github.com/AlbanBedel/scummc/blob/master/scc_func.h) | `88b10a76a9e907ec44db7f4c0a4b7b43f25afd6f` |
| ScummC | [`scc_code.c`](https://github.com/AlbanBedel/scummc/blob/master/scc_code.c) | `165c6d932eb69acd1bc9380f867b071ae2a18ef0` |
| ScummC | [`scc_cost.c`](https://github.com/AlbanBedel/scummc/blob/master/scc_cost.c) | `f387827acb5ba5517164e746337fb06c6b45af51` |

## 2. Zeichnungsreihenfolge: v6 ist kein allgemeines Layer-System

In `ScummEngine::processActors()` (`actor.cpp`) werden zunächst die im
aktuellen Raum befindlichen Actors gesammelt. Für normale v6-Spiele wird
ein Sortierwert aus `actor.y - actor.layer * 2000` gebildet. **Für Sam & Max
existiert ein eigener Sortierzweig**: primär Y-Position, bei gleichem Y
eine actornummerabhängige Auflösung; der Code kommentiert ausdrücklich
das stabile Verhalten dieser speziellen Sortierung.

Für HE90+ und v0 bestehen wiederum andere Zweige. Es wäre daher falsch,
die v6-Komposition aus der späteren HE-Layer-Semantik abzuleiten.

Nach dem Sortieren zeichnet `processActors` Actors, bei v6 jeweils mit
`drawActorCostume()` und anschließend `animateCostume()`. Der Costume-Stand
und die Script-Ereignisse sind im
[Execution-Lifecycle-Audit](scumm-v6-execution-lifecycle.md) erläutert.

**Editor-Folge:** Ein Shot darf „Figur A vor Figur B“ anzeigen, aber die
technische Prüfung muss die tatsächlichen Actor-Positionen, die v6-Sortierung
und den Zielspielmodus (`Sam & Max` versus allgemeines v6) beachten. Eine
beliebige Canvas-Layer-Zahl allein würde den Export nicht festlegen.

## 3. Masken: Vordergrundverdeckung ist Teil der Raumressource

`Gdi::drawBitmap()` (`gfx.cpp`) liest bei regulären Raum-/Objektgrafiken
SMAP- und Z-Plane-Daten (`getZPlanes`). Die Engine verwaltet die
Maskenpuffer streifenbasiert; `ScummEngine::getMaskBuffer(x,y,z)`
übersetzt die horizontale Bildschirmposition unter Berücksichtigung
des Kameraoffsets in 8-Pixel-Strips und fragt den jeweiligen Maskenpuffer
ab.

Der klassische Costume-Renderer verwendet seinen Z-Pufferwert bei der
Bitmap-Dekodierung als Maskenebene. Die Kombination aus **Raummaske +
Costume-Z-Band** bestimmt, welche Pixel einer Figur verdeckt werden.

In `Actor::prepareDrawActorCostume()` ergibt sich der Z-Wert bei v6 aus:

1. Expliziter `_forceClip`-Wert, falls gesetzt.
2. Sonst `0`, wenn der Actor die Klasse `kObjectClassNeverClip` besitzt.
3. Sonst `getMaskFromBox(_walkbox)`, begrenzt auf die tatsächlich
   verfügbaren Z-Puffer.

**Das ist nicht identisch mit der Actor-zu-Actor-Sortierung.** Eine Person
kann vor einer anderen gezeichnet werden und dennoch hinter einem
maskierten Vordergrundobjekt verschwinden. Beides muss für einen
filmischen Shot korrekt authorbar sein.

### Anwendungsfall: Nahaufnahme hinter einer Autoscheibe

- Hintergrund und Auto-Innenraum als Raum-/Objektbild vorbereiten.
- Entsprechende Z-Maske für Scheibenrahmen oder Armaturen definieren.
- Schauspieler-Costume in passender Größe und an passender Position zeichnen.
- Actor-Walkbox bzw. erzwungenes Z-Clip-Verhalten mit den vorhandenen
  Maskenebenen abstimmen.
- Nur dann einen klickbaren Hotspot überlagern, wenn ein echtes
  Raumobjekt mit passender Hitbox existiert; reine Masken sind keine
  Interaktionsobjekte.

Der konkrete ScummC-Ressourcen-Writer für SMAP/Z-Planes ist im vorliegenden
Nachtrag **noch nicht bis zum finalen Binärlayout nachverfolgt**. Die
ScummVM-Decoderbeobachtung ist folglich noch kein Beleg für einen
funktionsfähigen Generator für alle Maskenvarianten.

## 4. Skalierung: Actor-Größe und Walkbox-Perspektive

`Actor::setupActorScale()` liest in v6 die Walkbox-Skalierung und
setzt `_scalex` und `_scaley`. Bei `GID_SAMNMAX` existiert eine
Sonderbehandlung für Walkboxen mit `kBoxIgnoreScale`: Dort bleibt die
bereits explizit gesetzte Actor-Skalierung erhalten (der Code erwähnt
als Beispiel den Mystery Vortex).

`Actor::prepareDrawActorCostume()` übergibt die beiden Skalierungswerte
an den Costume-Renderer. Ein vergrößerter Actor ist somit **kein**
vergrößerter Raum und kein Kamerazoom. Für echte Close-up-Kompositionen
brauchen wir unter Umständen neue Hintergrundgrafiken, ein eigenes
Costume und die korrekte Skalierungs-/Walkbox-Einstellung.

Wichtig: Skriptseitiges `setActorScale` kann von der nachfolgenden
Walkbox-Berechnung beeinflusst werden. Der Editor darf nicht versprechen,
ein fester Scale-Wert bleibe bei jedem Actor und in jeder Box unverändert.

## 5. ScummC: Von Funktionsaufruf zu v6-Bytecode

`scc_func.h` definiert die eingebauten Funktionen als Tupel mit
Symbolname, Opcode, Rückgabekennzeichen, Argumentzahl, Anzahl versteckter
Argumente und Argumenttypen. Außerdem gibt es **versionsspezifische
Tabellen** (darunter `scc_func_v6_only`).

`scc_call_gen_code()` in `scc_code.c` führt den normalen Compilerpfad aus:

1. Bei Funktionen mit verborgenem Listen-Operationsparameter den
   passenden Wert auf den Stack legen.
2. Explizite Nicht-Referenzargumente in Aufrufreihenfolge kompilieren.
3. Fehlende Werte gegebenenfalls aus den Funktionsdefaults pushen.
4. Bei Listen-Operationen die Listengröße pushen.
5. Den Opcode schreiben: ein Byte bei Werten bis `0xFF`, bei einem
   kombinierten Wert zwei Bytes in **High-Byte/Low-Byte-Reihenfolge**.
6. Referenzargumente nach dem Opcode schreiben.
7. Für `SCC_FA_SELF_OFF` einen relativen, vom Compiler berechneten
   Rücksprung-Offset anhängen.
8. Je nach Rückgabetyp das Ergebnis konsumieren oder pushen.

Diese Details verbieten es, ein einzelnes `scc_func.h`-Opcodefeld
unkritisch als fertigen Bytecode zu interpretieren. Der Stack wird von
den ScummVM-Handlern häufig **in umgekehrter Reihenfolge** gepoppt.

### Nachgewiesene Zuordnung der hier relevanten Aufrufe

| ScummC-Funktion (v6) | Signatur / Encoding in `scc_func.h` | Interpreter-Wirkung | Status |
| --- | --- | --- | --- |
| `panCameraTo(x)` | `0x78`, 1 Wert | v6 liest X und setzt Zielposition | Quellpfad abgeglichen |
| `cameraFollowActor(actor)` | `0x79`, 1 Wert | Actor-Follow-Modus | Quellpfad abgeglichen |
| `setCameraAt(x)` | `0x7A`, 1 Wert in v6-only-Tabelle | unmittelbare X-Position | Quellpfad abgeglichen |
| `waitForCamera()` | `0xA9AA`, ohne explizite Werte | `o6_wait`, `SO_WAIT_FOR_CAMERA` | Encoding im Compiler nachvollzogen |
| `drawObjectAt(obj,x,y)` | `0x62`, 3 Werte | Handler poppt Y, X, Objekt; State/Hitbox aktualisieren | Argumentreihenfolge abgeglichen |
| `setActorScale(scale)` | `0x9D5C`, 1 Wert im Actor-Subopcode-Kontext | `SO_SCALE` setzt X/Y; Walkbox-Regeln beachten | Kontext und Versionszuordnung prüfen |
| `beginCutscene(args...)` | `0x68`, Listenargument | Cutscene-Stack aufbauen | Listenencoding prüfen |
| `endCutscene()` | `0x67` | Cutscene-Stack abbauen | Quellpfad abgeglichen |
| `fadeIn(value)` / `fadeOut(value)` | `0xC9` plus verborgenes Subopcode-Argument in v6-only-Tabelle | Kernel-/Übergangsfunktionen | Stack-/Subopcode-Pfad weiter prüfen |

**Besondere Warnung:** `setActorScale` erscheint in `scc_func.h`
auch als anders encodierte v6-only-Kernel-Funktion (`0xC9` mit
Subopcode `0x6B` und zwei Werten). Der gleichnamige Eintrag ist daher
**überladen**. Der Studio-Compiler muss Actor-Kontext und
Version bei der Funktionsauflösung berücksichtigen. Eine einzelne
globale Zuordnung `setActorScale → 0x9D5C` wäre unvollständig.

Bei `drawObjectAt` bestätigt die Compilerreihenfolge (Objekt, X, Y)
den Interpreterpfad (Pop Y, Pop X, Pop Objekt). Daraus folgt noch nicht,
dass alle Export-Ressourcen und Hotspot-Attribute stimmen.

## 6. Shot-Komposition: erforderliche Ressourcen statt erfundener Kamera

Für den cineastischen Editor ergeben sich drei unterscheidbare Aufgaben:

| Autorabsicht | Native Umsetzung | Export-Prüfpunkt |
| --- | --- | --- |
| Actor bewegt sich hinter Zaun | Z-Maske im Raum + Walkbox/Z-Clip | Richtige Z-Plane in binärer Room-Ressource |
| Zwei Figuren überkreuzen sich | Y-/Actor-Sortierung mit Sam-&-Max-Sonderfall | Sichtreihenfolge in v6 |
| Figur wird im Hintergrund kleiner | Walkbox-Skalierung / Actor-Scale | Kein unerwartetes Überschreiben durch Box |
| Große Kopfaufnahme | andere Bildkomposition/Costume, ggf. anderer Raum | Native Room-/Costume-Ressource |
| Autotür fährt über Vordergrund | veränderliche Objektzustände plus Maske | Render- und Hitboxdaten getrennt validiert |
| Kamerafahrt über breites Panorama | `panCameraTo` + optional `waitForCamera` | v6 nur horizontale Kamera |

### Vertragsentwurf für ein Shot-Projektmodell

- Ein Shot referenziert **native Raumressource, Kamera-X, Actors,
  Costume-States, Objekte, Masken-/Walkboxdaten** und Scripts.
- Die Schnitt-Eigenschaft legt konkret fest, ob eine X-Kameraversetzung,
  ein Roomwechsel oder ein Wechsel von Artwork/Objektzuständen stattfindet.
- Ein Kompositionsprüfer kontrolliert für jeden Actor die Walkbox,
  berechnete Skalierung und gewählte Z-Maske.
- Sam-&-Max-Sortierung ist als eigenes Zielspielprofil dokumentiert,
  nicht als universelle, frei definierbare Layer-Strategie.
- Der Compiler nutzt die ScummC-Signatur inklusive Versionsfilter,
  Argumenttypen, versteckter Werte und Kontext.
- Alle im Editor sichtbaren Zoom-/Portrait- oder Tiefenoptionen müssen
  eine transparente, native Ressourcenabbildung besitzen oder im
  v6-Modus als nicht unterstützt erscheinen.

## 7. Noch offen / nächstes Arbeitspaket

1. **Ressourcen-Ende-zu-Ende:** ScummC-Room-, Objekt- und Costume-Writer
   bis zum erzeugten SMAP-/Z-Plane-/Maskenlayout verfolgen und mit
   ScummVM-Decoderstrukturen abgleichen.
2. **Opcode-Resolver:** Auflösung der allgemeinen und v6-only-Tabellen
   anhand von Funktionskontext, Typen und Version exakt dokumentieren.
3. **Cutscene-Bildaufbau:** `processDrawQue`, Objektzustände,
   Actor-Zeichnung und Dirty-Rect-Reset vollständig als Frame-Reihenfolge
   aufschreiben; daraus ein reproduzierbares Rendering-Audit ableiten.
4. **Dialogporträts:** Textmasken, Talk-Position, Actor-Frames und
   Untertitel über Charset-/Print-Subopcodes prüfen.
5. **Validierung:** Erst danach kleine, gezielte Export-Fixtures bauen,
   statt jetzt schon ein generisches Konformitätsspiel zu entwerfen.

**Befund:** Der Quellcode zeigt ausreichend native Bausteine für komplexe
filmische Einstellungen. Er beweist bislang **nicht**, dass Adventure Studio
die korrekten v6-Ressourcen für Z-Masken und Close-up-Kompositionen schon
schreiben kann. Diese Lücke ist ein konkretes Compiler-/Ressourcenpaket,
kein Anlass für eine neue Engine.
