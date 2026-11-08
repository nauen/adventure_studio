# Adventure Studio – Projektstatus und Chat-Übergabe

Stand: 2026-11-07. **Dies ist die kurze Einstiegseite für jede neue
Arbeitssitzung.** Sie ersetzt nicht die [Roadmap](roadmap.md) oder die
[SCUMM-v6-Funktionsmatrix](SCUMM_V6_CAPABILITIES.md).

## Nordstern

Ein vollständiger, originaler SCUMM-v6-Generator für klassische
Point-and-Click-Adventures. Technischer Output: native Ressourcen und
Bytecode, lauffähig in ScummVM ohne eigene Adventure-Studio-Engine.
Die kreative Oberfläche soll später auch komplexe, cineastische
Sequenzen authoren können.

## Gesichert vorhandene Grundlagen

- Versionierte Story-/Projektmodelle, deterministische Validierung
  und ScummC-Quelltextausgabe.
- Indizierte Raumhintergründe, einfache Hotspots und Bildzustände,
  Inventar-/Use-/Combine-Regeln, begrenzte Dialogvarianten,
  Palettenzyklen und Musikexperimente.
- Separate ScummC-/ScummVM-Workflows mit Bild-/Interaktionsprüfungen
  für definierte Demo-Szenarien. Einzelne erfolgreiche Proben
  **beweisen nicht** automatisch vollständige Generatorabdeckung.
- Eine erste Gradio-Oberfläche und JSON-/ZIP-Exportpfade.

Codebelege im Repository: `src/adventure_studio/scumm_assets.py`,
`scumm_project.py`, `story_to_scumm.py`, `scumm_launch.py` und deren Tests.

## Größte bekannte Lücken

1. Vollständige Z-Masken, Walkbox-/BOXM-/SCAL-Daten und
   nativer Ressourcen-Roundtrip fehlen im allgemeinen Raumdatenmodell.
2. Vollständige Actor-Costumes samt Animation, `COUNT`-Timing,
   mehreren Figuren und bewegten, interaktiven Objekten fehlen
   als durchgängige authorbare Features.
3. Native Schnitt-/Kamera-/Cutscene-Choreografie und sichere
   Skip-Endzustände fehlen im Studio-Editor.
4. Viele weitere SCUMM-v6-Bereiche sind nur teilweise untersucht;
   Details in der Funktionsmatrix. Die Gesamtkompatibilität ist offen.

## Letzte grundlegende Entscheidungen

- SCUMM v6 ist **Zielbinary und Laufzeitvertrag**, keine selbstgebaute
  Nachbildung der Mechanik.
- ScummVM-/ScummC-Quellcode ist die Primärreferenz; der konkrete
  Compiler-/Interpreterpfad wird dokumentiert, bevor Funktionen
  als kompatibel eingestuft werden.
- Editor-Shots sind Authoring-Metadaten, die nur native Räume,
  Bildzustände, Scripts und Kamera-Operationen erzeugen.
- Ein großes, generisches „Konformitätsspiel“ ist aktuell nicht
  Voraussetzung. Kleine native Export-Fixtures belegen konkrete Gates.
- Pull Requests sind interne GitHub-Technik. Bei grünen Checks und
  unkritischen, abgeschlossenen Änderungen kann der Agent wie gewünscht
  selbstständig mergen.

## Architektur-Audit und künftige Qualitätsregeln (2026-11-07)

Der [Architekturaudit](architecture-audit.md) hat konkrete
Demo-/Adapter-Grenzen und Verantwortungskonflikte dokumentiert.
Wesentliche Befunde: begrenzte lineare Story-Routen,
fixe Pickup-Farben/Platzierungen, harte Dialog-/Regelquoten,
absolute Koordinaten im Story-Fachmodell und die Kopplung
zwischen Authoring- und Exportvalidierung.

**Wichtig:** Das zweistellige Rezept `Use A with B` ist als
binäre Interaktion fachlich plausibel. Allgemeine Rätsel dürfen
aber mehr als zwei Bedingungen besitzen. Native SCUMM-Limits
sind von künstlichen Demo-/Layout-Limits getrennt zu führen.

Gültige Architekturleitlinien:
[Architekturverträge](architecture-contracts.md),
[ADR-0001](adr/0001-domain-and-export-boundaries.md),
[ADR-0002](adr/0002-limits-evidence-and-compatibility.md).
Eine [PR-Checkliste](../.github/pull_request_template.md) sichert
Regression, Versionsverträglichkeit und native Nachweise ab.

**Stabilisierung umgesetzt (2026-11-07):** Platzierungen werden im fachlichen
Story-Modell und im JSON-Parser nicht mehr auf die 640×200-Demogeometrie
begrenzt. Der aktuelle Exportadapter prüft seine konkrete Raumgeometrie
weiterhin und verweigert nicht darstellbare Exporte ausdrücklich. Die
Studio-Editierfassade lässt fachlich gültige Änderungen (auch mehr als vier
Dekoobjekte) mit Exportwarnung speichern; explizite Platzierungen bleiben
selbst bei nicht exportierbaren Stories lesbar. Regressionen: 203 Unit-Tests
lokal grün, darunter neue Grenztests und unveränderte Exportfixtures.

**Architekturstabilisierung abgeschlossen (weiteres Paket):** Das Studio
liefert nun typisierte Export-Blocker (`code`, `entity_kind`, `entity_id`,
`target_id`, `reason`), einschließlich mehrerer gleichzeitig bekannter
Hindernisse. Nicht klassifizierte Adapterfehler bleiben als
`ADAPTER_REJECTED` sichtbar, statt als native Limits ausgegeben zu werden.
Die Raumvorschau benutzt einen unabhängigen Authoring-Layoutpfad und
zeigt auch nicht exportierbare Projekte; sie ist ausdrücklich **keine**
Spielsimulation. Die Demo-Bildquelle wird von Exporter und Vorschau geteilt,
ohne dass die Vorschau den Compiler benötigt. Die zuvor künstlichen
JSON-Grenzen von 128 Entitäten bzw. 32 Bedingungen sind entfernt; das
1-MB-Eingabelimit bleibt als Ressourcenschutz bestehen. Grenzklassifikation:
[Audit-Nachtrag](architecture-audit.md). Regressionen: 208 Unit-Tests
lokal grün. **Keine** neue native SCUMM-v6-Funktion ist damit belegt.

**Unverändert als Produktentwicklung offen:** Allgemeine Action-/Condition-
IR, dynamische Raumgeometrie und vollständige native SCUMM-v6-Fähigkeiten.
Der Diagnosebericht beschreibt alle aktuell statisch erkannten Blocker;
für noch nicht typisierte Compilerfälle wird die allgemeine Ablehnung
zurückgegeben. Diese Fähigkeiten gehören zu den nächsten vertikalen
SCUMM-Paketen, nicht zum abgeschlossenen A0-Stabilisierungsgate.

## Verbindlicher SCUMM-v6-Referenzvertrag (2026-11-07)

Die [Referenzbibliothek](scumm-v6-reference/README.md) verbindet den
**einen** [64-ID-Funktionskatalog](SCUMM_V6_CAPABILITIES.md) mit
[technischen ScummC-/ScummVM-Primitiven](scumm-v6-reference/NATIVE_PRIMITIVES.md),
[konkreten Abnahmeszenarien](scumm-v6-reference/SCENARIOS.md) und einem
[maschinenlesbaren Quellenindex](scumm-v6-reference/capability_sources.json).
Das Produktziel ist damit für die Implementierung festgelegt. Vorhandene
Source-Audits werden wiederverwendet; neue Quellcodeanalyse ist nur bei
fehlendem v6-Encoder-/Decoder-/Sonderfallbeleg oder Versionswechsel nötig.
Die Referenz beschreibt den Zielumfang, **nicht** 64 bereits fertige
Funktionen. Ein kleines natives Test-Fixture pro Grundbaustein genügt;
ein großes neues Konformitätsspiel ist kein Gate.

**Nächster Implementierungsschritt bleibt P0.1** (nativer Binär-Roundtrip),
dann P0.2/0.3. Neue Features werden anhand des Katalogs und der
Szenarien abgenommen, nicht anhand zusätzlicher spontaner Demo-Limits.

## Nächste drei priorisierte Pakete

**Fortschritt 2026-11-07 nach den ursprünglichen P0.x-Planungen:**
Der SCUMM-v6-Raumparser (P0.1), native Z-Masken (P0.2) sowie Walkboxen,
BOXM und vertikale SCAL-Slots (P0.3) wurden in nachfolgenden vertikalen
Paketen umgesetzt und im unveränderten ScummVM geprüft; für konkrete
Nachweise siehe `scumm-v6-perspective-scal-contract.md` und die GitHub-
Actions-Läufe von PR #26/#27. Ein weiterer Teilbaustein der cineastischen
Funktionen ist das typisierte `camera_cues`-Raummodell mit nativem
`setCameraAt`, `panCameraTo`, `waitForCamera` und `cameraFollowActor`.
Die unabhängigen ScummVM-Bildkompositionen sind im Actions-Lauf
`42405122040` verifiziert ([Kamera-Vertrag](scumm-v6-camera-cue-contract.md)).
**Das nächste noch offene Schwerpunktpaket ist P0.4/P0.5:** native
bewegte Objekte und Actor-/Costume-Animationen mit zeitlichen Phasen;
vollständige Cutscene-Skip-Zustände bleiben P1.1 offen.

**Nächster P0.5-Teilnachweis (2026-11-07):** Ein allgemeiner
[`CostumeAsset`-Ressourcenvertrag](scumm-v6-native-costume-count-contract.md)
liefert eigene Bildframes, vier Blickrichtungen, Stand-/Walk-/Init- und
Aktionsanimationen sowie explizite `COUNT`-Kommandos in ScummCs v6-`COST`.
Die erzeugte Figur wurde in stock ScummVM gerendert; eine Counter-Scriptprobe
schaltet den Objektzustand nach zwei markierten Ereignissen, während eine
Gegenprobe mit drei erwarteten Ereignissen den Ausgangszustand bewahrt.
Die native CI-Evidenz liegt in Actions `42408510454` und deren Artefakten.
**Offen und priorisiert:** freie Actor-Instanzen samt Costume-Bindung im
Projektmodell, generischer Action-/Condition-/Ereignisablauf sowie echte
Spielereingabe während laufender Animation. P0.5 insgesamt ist nicht fertig.

**Weiterer P0.5-Modellschritt (2026-11-07):** `GameDocument` speichert nun
beliebig viele validierte `CostumeAsset`-Ressourcen als versioniertes JSON
(inklusive Frame-Pixeln, Blickrichtungen, nativen Animations-IDs und `COUNT`).
`export_document` schreibt zu den Räumen auch die zugehörigen `.scost`-
und Frame-BMP-Compiler-Eingaben. Bestehende JSON-v1-Projekte ohne Costumes
bleiben bitgenau unverändert. Dieses Gate belegt **noch keine freie
Actor-Instanz und keine Verknüpfung des COST im Spiel**; das nächste Paket
ist die native Actor-Symbol-/Costume-Bindung über den ScummC-Bootstrap.

**P0.5 Mehr-Actor-Integrationsschritt (2026-11-07):** Das Projektmodell hat
nun referenzgeprüfte Actor-Instanzen mit Costume-ID, Anfangsraum, Position,
Blickrichtung und optionalem Namen. JSON-v1-Roundtrip bleibt kompatibel,
und der ScummC-Forschungsadapter erzeugt globale `actor`-Symbole,
native Costume-Deklarationen, `initActor`/`setActorCostume` und Platzierung
für mehrere Actors. Ein gemeinsames Costume wird nur einmal kompiliert.
CI prüft einen SCUMM-v6-Spielstart mit zwei NPCs und gemeinsamem COST;
der native Ergebnisstatus ist erst nach grünem Actions-Lauf zu setzen.
**Noch offen:** freier Spieler-Actor jenseits des Road-Fixture-Symbols `hero`,
echte Spielgrafik-Evidenz für jede Figur, Animations-Cues, Action/Condition-IR
und Interaktion während laufender Animation. Der externe Bootstrap wird
nicht zur Produktarchitektur erklärt.

**P0.5-Teilbaustein (COUNT-Laufzeitgate erfolgreich, kein vollständiges Animations-Gate):**
`ActorAsset.initial_animation` referenziert optional eine benannte,
explizit numerierte native COST-Animation mit passender Startrichtung.
GameDocument-v1-JSON bleibt rückwärtskompatibel; der Forschungsadapter
erzeugt `animateActor(actor,index)` im Einstiegsscript des Startraums
nach der Actor-Initialisierung (nicht vor `startRoom`).
Der Mehr-Actor-CI-Probe startet eine solche Animation. Der eigenständige
COUNT-Laufzeitnachweis ist inzwischen erfolgreich; vollständige
Frame-Phasen, Spielerinteraktion und allgemeine Animations-Choreografie
sind damit noch nicht belegt.

**COUNT-Folgegate in ScummVM abgenommen (`42421713939`):** Eine isolierte
positive und negative ScummVM-Probe beobachtet nun
`getActorAnimCounter1(Companion)` des projektdefinierten Actors. Bei zwei
COUNT-Ereignissen muss der native Schlüsselzustand wechseln; die
Drei-Ereignis-Kontrolle darf ihn nicht wechseln. Die CI-Artefakte enthalten
beide Raumskripte, Screenshots und den Pixelbericht. Die positive und
negative Kontrolle sind im unveränderten ScummVM grün. Sichtbare
Animationsphasen, Eingaben während der Animation und eine allgemeine
Ereignis-IR bleiben gesonderte offene Gates.

**Behobener Fixture-Fehler (zuvor rot `42420046842`):** Der Raumscript-Pfad funktionierte
(bei COUNT-Schwelle 0 verschwindet der Schlüssel, 0 Pixel). Bei Schwellen
1, 2 und 3 bleiben dagegen jeweils 112 Schlüsselpixel sichtbar. Damit
ist noch **kein einziges COUNT-Ereignis** für den projektdefinierten
Actor belegt, obwohl die separate Ego-COST-Probe weiterhin grün war.
Raumzuordnung, Costume und aktiver Frame 24 wurden daraufhin separat
nachgewiesen. Die Ursache lag in der nur für `S` vorhandenen COUNT-Geste
des Mehr-Actor-Test-Costumes. Die vollständige N/E/S/W-Sequenz liefert
nun die erwarteten nativen Ereignisse. Die fixierte Testfixture ist
kein Beleg für beliebige Richtungswechsel während einer Animation.

**P0.5-Vertikalschnitt (native CI-Abnahme erfolgreich `42461862069`):**
`GameDocument.animation_rules` modelliert eine `ActorCountCondition`
(Actor und COUNT-Schwelle) mit einem `ObjectStateEffect` (Raum-Hotspot und
Zustand) als versioniertes, deklaratives JSON. Der ScummC-Adapter gibt
lokale native COUNT-Wächter-Scripts nach dem Anfangsanimationsaufruf aus.
Die Referenzen und die Erreichbarkeit des COUNT-Schwellwerts in einer
nicht-loopenden Anfangsanimation werden geprüft. Bestehendes v1-JSON
bleibt unverändert. Die neue CI-Probe kompiliert auch eine solche aus
Projekt-JSON geladene Regel und prüft den resultierenden Objektzustand
in stock ScummVM. Die positive JSON-Regel und die bisherige negative
Fixture-Kontrolle sind grün. Allgemeine Action-/Condition-IR, parallele Interaktion und
mehrstufige Animationsabläufe sind nicht abgeschlossen.

**P0.5-Eingabefolge (stock ScummVM, CI `42467237997`):** Ein
versioniertes `AnimationInputRule` erzeugt native `Push`-/`Pull`-/`Open`-/
`Close`-Verbfälle, die vor beziehungsweise nach einer COUNT-Grenze
unterschiedliche Objektzustände setzen. Der reproduzierbare native
Gameplay-Test prüft 0, 1 und 2 Eingaben: Ohne Klick bleiben Schlüssel
sichtbar und Tür nach COUNT 1 offen; ein früher Klick entfernt die Tür,
ein später Klick den Schlüssel,
und bei einem frühen und einem späteren Klick **im selben Spielprozess**
werden beide zeitabhängigen Aktionen nacheinander ausgeführt. Das
ist kein Nachweis für beliebige Wiederholung, mehrfach gestartete
Animationen, Raumwechsel oder Save/Load. Der seither ergänzte
Raumwechsel-Nachweis folgt unmittelbar darunter.

**P0.5-Raumwechsel-Teilnachweis (native CI `42468551627`):** Nach einer
verspäteten `Push`-Aktion verschwindet der Schlüssel; die offene Tür
ermöglicht den regulären `WalkTo`-Wechsel `Harbor → Cellar`. Über den
Treppe-Hotspot kehrt der Spieler nach `Harbor` zurück. Die native
ScummVM-Probe bestätigt, dass der Schlüssel weiterhin unsichtbar
und die Tür offen ist. Die bisherigen 0/1/2-Klick-Tests bleiben grün.
Der seither verifizierte Initialanimations-Lifecycle folgt direkt
darunter. Save/Load und das vollständige Fahrgeschäft bleiben offen.

**P0.5-Initialanimations-Lifecycle (stock ScummVM `42471602488`):**
`ActorAsset.initial_animation` startet nun durch ein pro Actor deklariertes
globales SCUMM-Bit genau beim ersten Eintritt in seinen Anfangsraum.
Beim Wiedereintritt wird weder die Anfangsanimation noch der daran
gebundene COUNT-Wächter erneut ausgelöst. Ein zusätzlicher nativer
Negativ-Wächter würde den zuvor entfernten Schlüssel nach einem
Doppelstart wieder sichtbar machen; der unveränderte ScummVM-Lauf
bestätigt, dass er verborgen bleibt. Der Guard umfasst alle an die
Animation gebundenen COUNT-Wächter. Die alten JSON-v1-Projekte bleiben
unverändert. Das nachfolgende Gate prüft nun auch Save/Load eines
**abgeschlossenen** COUNT-/Objektzustands. Weiter offen bleiben explizite
wiederholbare Animationen sowie Save/Load mitten in einer aktiven Animation.

**P0.5-Save/Load-Gate in stock ScummVM bestanden (`42477804196`):** Die
isolierte Actor-Fixture führt einen nativen Save/Load-Ablauf aus: späte
`Push`-Aktion, Prüfung der Key-/Door-Bilder, Speichern über den ScummVM-
Dialog, Neustart mit `--save-slot=1`, erneute Bildprüfung und regulärer
`Harbor → Cellar → Harbor`-Rückweg. Der COUNT-Replay-Negativwächter deckt
einen verlorenen Initialanimations-Guard auf. Der native CI-Schritt und
die zugehörige Artefaktaufbewahrung sind erfolgreich. Save/Load **während**
einer noch laufenden Animation ist davon nicht abgedeckt.
Die vormals auf einzelne Testfälle hartcodierten Screenshot-Frame-Namen in
den gemeinsamen Door-/Key-Pixelhelfern wurden durch eine gemeinsame sichere
Frame-Namensvalidierung ersetzt. Neue native Szenarien erfordern damit keine
Änderung an den allgemeinen Bildprüfhelfern mehr.

**P0.5-Produktfunktion (nativer ScummC-/Spielstart belegt, CI `42481225873`):** `animation_triggers`
ermöglichen wiederholbare Actor-Animationen über einen frei gewählten
Hotspot-Verbfall im versionierten `GameDocument`. Der native Export startet
die benannte, indizierte Costume-Animation bei jeder Aktion erneut, unabhängig
vom einmaligen Erststart-Guard. Das Actor-Projekt enthält eine authored
`Pull`-Aktion, die mit dem zweiten Actor ohne `initial_animation` kompiliert
und gelinkt wurde. Die wiederholte Interaktion bleibt bis zum Gameplay-Nachweis
als offen gekennzeichnet. **Nächstes Produktpaket:** kombinierbare
Animations-Cues und Reaktionen über mehrere Actors und Objekte.

Die ältere Liste unten bleibt als historischer Arbeitsvorrat erhalten;
ihre ungekreuzten Kästchen sind nicht der aktuelle Capability-Nachweis.

1. **P0.1 – Binär-Roundtrip-Prüfer für ScummC-Räume; bestehende Modellgrenzen sind initial durch Regressionstests charakterisiert.**
   Chunk-Baum, Tag-/Größenprüfung, SMAP-/ZPxx-Offsets,
   OBIM/OBCD-IDs; erst wenn das bestehende Fixture valide parsebar
   ist, als erledigt markieren.
2. **P0.2 – Z-Masken im RoomAsset/JSON und ScummC-Export.**
   Masken-Indizes/Größen validieren, Bitmapquellen schreiben und
   sichtbare Verdeckung in ScummVM belegen.
3. **P0.3 – Walkbox-/BOXM-/SCAL-Modell.**
   Native Walkability, Tiefenzuordnung und Perspektivskalierung
   in einem exportierten Raum prüfen.

Abhängigkeiten und weitere Pakete:
[Lückenanalyse](scumm-v6-export-gap-analysis.md).

## Definition of Done pro Arbeitspaket

- Das betroffene SCUMM-v6-Verhalten ist benannt und quellenbasiert
  abgeglichen.
- Projektmodell, Export und Datenvalidierung sind konsistent.
- Unit-/Strukturtests laufen; bei spielrelevanten Funktionen zusätzlich
  eine **stock-ScummVM-Laufzeitprüfung** (oder ausdrücklich offener Gate).
- Keine nicht verwandten Features als abgeschlossen markieren.
- Funktionsmatrix, Status und Roadmap sind bei tatsächlicher
  Statusänderung synchronisiert.
- Änderungen sind nach Prüfung in `main` enthalten und der GitHub-Link
  ist in der Übergabe genannt.

## Einstieg für den nächsten Chat/Agenten

1. `AGENTS.md` lesen; dann Vision, **diesen Status**, Capabilities
   und Roadmap lesen.
2. `main`, laufende Branches/PRs und CI-Status prüfen.
3. Vorhandene Implementierungen und die letzten Commit-Diffs
   ansehen; weder abgeschlossene Arbeit wiederholen noch neue
   Lücken aus unvollständiger Erinnerung erfinden.
4. Das oberste unverblockierte Paket bearbeiten und Tests ausführen.
5. Nach Merge **diese Datei aktualisieren**: Ist-Stand, Nachweise,
   noch offene Risiken und nächstes Paket.

## Quellenindex

- Mechanikziel: [Adventure-Mechaniken](scumm-adventure-mechanics.md).
- Native Laufzeit: [Source-Audit](scumm-v6-source-audit.md),
  [Execution/Lifecycle](scumm-v6-execution-lifecycle.md).
- Filmische Inszenierung: [Cinematic-Audit](scumm-v6-cinematic-source-audit.md).
- Grafiken und Compiler: [Compositing-Audit](scumm-v6-compositing-compiler-audit.md),
  [Binär-Ressourcen](scumm-v6-room-resource-binary-audit.md),
  [Export-Lücken](scumm-v6-export-gap-analysis.md).
