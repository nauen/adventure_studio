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

**P0.5 – geordnete Interaktionsfolgen (Implementierung, native CI ausstehend):**
`interaction_sequences` verbindet ein Hotspot-Verb mit einer expliziten
Reihenfolge aus Actor-Animationen, `delaySeconds` und `setObjectState`.
Mehrere Actors und Objekte können in einer Sequenz referenziert werden;
Projekt-JSON, Referenzvalidierung und ScummC-Exporter sind angeschlossen.
Das bestehende native Actor-Projekt enthält eine authored `Close`-Aktion
mit zwei Cues und einer Objektreaktion. Noch kein visueller Gameplay-Nachweis
für die gesamte Sequenz. **Nächster Produktfokus:** Authoring und Bearbeitung
dieser Abläufe im Studio statt ausschließlich über Projekt-JSON.

**P0.5 – native Interaktionen im Studio bearbeiten (Implementierung, UI-/Gameplay-Gate offen):**
Der Gradio-Editor enthält einen separaten Bereich für validierte native
`GameDocument`-Dateien. Hier lassen sich Hotspot-Verb-Abläufe anlegen, Actor-
Animationen, Pausen und Objektzustände als Schritte anhängen, verschieben
oder entfernen und das Ergebnis als Projekt-JSON oder über den echten
ScummC-Pfad als Spiel-ZIP ausgeben. Bereits vorhandene Story-v4-Dateien
werden nicht stillschweigend als native Projekte behandelt. Service-
Roundtrip und Regressionstests sind lokal grün; Gradio-UI-Interaktion
und ein interaktiver ScummVM-Klickpfad wurden noch nicht geprüft.
**Nächstes Produktpaket:** Story-Authoring und native Actor-/Interaktions-
Authoringdaten in einem durchgängigen Projektmodell verbinden.

**P0.5 – Story/native Projekt-Integration (Implementierung, Gameplay offen):**
Im Studio lässt sich die aktuelle Story ausdrücklich in das native
`GameDocument` übersetzen. Vorhandene native Actor-/Costume-Daten und
Interaktionsregeln werden auf die frisch aus der Story generierten Räume
übertragen und dabei referenzvalidiert. Nach Storyänderungen wird beim
Projekt-Download und Spiel-Build erneut komponiert; gelöschte oder
umbenannte Objekte führen zu einem sichtbaren Fehler statt Datenverlust.
Das SCUMM-ZIP enthält sowohl die aktuelle `story.json` als auch die
kompilierte `project.json`. Die Gradio-UI startet im CI-Smoke (`42486144774`);
der neue Kompositionspfad wird per Integrationstest bis zur ScummC-Quelle
geprüft. Die aktuelle Umsetzung ist **noch kein gemeinsames persistentes
Story-/Native-Schema**: zusätzliche manuelle native Raumänderungen werden
beim bewussten Story-Abgleich nicht übernommen. Der echte ScummVM-Klickablauf
und das vollständige UI-Interaktionsgate fehlen weiterhin.
**Nächstes Produktpaket:** ein versioniertes gemeinsames Authoring-Dokument,
das Story- und Actor-/Costume-/Interaktionsdaten dauerhaft und verlustfrei
zusammen speichert und wieder lädt.

**P0.5 – gemeinsames Studio-Authoring-Dokument (Implementierung, CI ausstehend):**
Das Studio speichert und lädt nun `adventure.studio.json` mit einem
versionierten Story-Dokument und einer nativen Actor-/Costume-/Action-Ebene.
Die referenzgeprüfte Story-Übersetzung bleibt die einzige Quelle für Räume,
Bitmaps und Hotspots; die native Ebene wird ohne redundante generierte
Room-Ressourcen gespeichert. Der Studio-Editor stellt beide Ebenen nach
Laden wieder her, erlaubt weitere Schritte und kann daraus das native
SCUMM-Projekt bzw. Spiel-ZIP erzeugen. Bestehende Story-/native-JSON-Dateien
werden nicht migriert oder ersetzt. Lokaler Roundtrip mit Bearbeitung und
alle Regressionstests grün; vollständiger UI-Klicktest und nativer Gameplay-
Nachweis bleiben offen.
**Nächstes Produktpaket:** Actors und Costumes direkt im gemeinsamen Studio-
Projekt anlegen und bearbeiten, ohne eine externe native JSON-Datei als
Ausgangspunkt zu benötigen.

**P0.5 – Actor-/Costume-Authoring im Studio (Implementierung, CI ausstehend):**
Aus einem vom Autor geladenen PNG lässt sich jetzt im Studio eine echte
palettierte native Costume erzeugen. Das Studio legt damit Actors in
gewählten Story-Räumen an und erlaubt deren Position/Richtung zu ändern.
Jedes neue Costume enthält zunächst eine Standpose und eine per
Interaktionsfolge nutzbare `gesture`-Animation auf Index 24. Projekt-JSON,
gemeinsames `adventure.studio.json` und ScummC-COST-Export bleiben derselbe
Produktpfad. Ein Integrationstest belegt PNG → Costume/Actor → validiertes
Modell → ScummC-Quellen (Fake-Compiler); noch **kein** echter nativer Build
oder ScummVM-Nachweis der neu importierten Grafik.
**Nächstes Produktpaket:** mehrteilige Costume-Animationen und individuelle
Blickrichtungen aus mehreren importierten Frames im Editor definieren.

**P0.5 – mehrteilige Costume-Animationen im Studio (Implementierung, CI ausstehend):**
Bestehenden Costumes können jetzt mehrere echte PNG-Frames zugeordnet
werden. Ein gemeinsamer 31-Farben-Palettenvertrag erhält bereits importierte
Framefarben; zusätzliche unpassende Farben werden sichtbar abgewiesen.
Im Studio werden benannte Animationen mit eigenen nativen Indizes und
richtungsbezogenen Frame-/COUNT-Folgen definiert oder aktualisiert. Der
bestehende Interaktionseditor kann diese Animationen über ihren Namen
auslösen. Modell, versionierte Projektdatei und ScummC-COST-/Verbquellen
sind verbunden. Ein gezielter Studio-Integrationstest mit zwei PNGs und
einer `wave`-Animation ist grün; echter ScummC-Build und stock-ScummVM-
Gameplay dieser neuen Mehrframe-Costume sind noch offen.
**Nächstes Produktpaket:** visuelle Costume-Frame-/Animationsvorschau und
direkte Frame-Reihenfolge im Editor statt kommaseparierter Kommandoliste.

**P0.5 – visuelle Costume-Timeline (Implementierung, CI ausstehend):**
Der Studio-Editor zeigt die echten Costume-Frame-Pixel und COST-Kommandos
einer ausgewählten Richtung als geordnete Karten. Schritte können direkt
angeklickt, umsortiert, angehängt und entfernt werden. Die Speicherung
verändert ausschließlich die typisierten `CostumeDirection.commands`; das
SCUMM-Projekt und der Compilerpfad bleiben unverändert. Der bestehende
Studio-Integrationstest prüft Vorschaureihenfolge, Bearbeitung und die
resultierende `.scost`-Quellfolge; keine zusätzliche Engine-Testmatrix.
Eine animierte Echtzeitvorschau oder ein ScummVM-Nachweis der neuen
Mehrframe-Sequenzen liegt noch nicht vor.
**Nächstes Produktpaket:** eine abspielbare Editor-Vorschau über die
vorhandenen Frames und Richtungsauswahl, mit einstellbaren Framezeiten,
ohne eine zusätzliche Spiel-Runtime zu simulieren.

**P0.5 – abspielbare Costume-Vorschau (Implementierung, CI ausstehend):**
Die gewählte Richtung einer Costume-Animation lässt sich jetzt direkt
im Studio als GIF abspielen. Die Frames stammen unverändert aus den
importierten COST-Bilddaten; die relative native Frame-Position bleibt
erhalten. Eine frei wählbare Millisekunden-Dauer steuert ausschließlich
die Editor-Wiedergabe, **nicht** native SCUMM-Framezeiten oder Costume-
COUNT-Kommandos. Der bestehende Studio-Integrationstest prüft Ausgabe,
Frameanzahl und Wiedergabedauer. Keine eigene Spiel-Runtime.
Stock-ScummVM-Bild- und Gameplay-Nachweise bleiben offen.
**Nächstes Produktpaket:** native ScummC-Kompilierung und tatsächliche
Wiedergabe einer aus Studio-PNGs erzeugten Mehrframe-Costume in stock
ScummVM belegen, bevor weitere Komfortfunktionen priorisiert werden.

**Studio-PNG-Nativpfad (2026-11-08, Nachweis ausstehend):** Der bestehende
experimentelle ScummC-/ScummVM-Workflow baut nun zusätzlich aus zwei
wirklichen PNGs über die produktiven Studio-Funktionen eine mehrteilige
`wave`-COST-Animation mit vier Richtungen und Actor-Startanimation. Er
exportiert das versionierte Projekt, kompiliert es und startet das Spiel in
stock ScummVM; Compilerquellen, Projekt-JSON und Bilder werden als Artefakte
aufbewahrt. Lokal ist die ScummC-Quellgenerierung geprüft; **CI-Ausführung,
Kompilierung, Spielstart und sichtbarer Framewechsel sind noch nicht
nachgewiesen**. Das nächste Gate bleibt die Auswertung dieses nativen
Laufs und ein tatsächlicher Framewechsel-Nachweis, bevor die Fähigkeit als
in ScummVM verifiziert eingestuft wird.

**Actor-Startanimation im Studio (2026-11-08):** Die Gradio-Oberfläche kann
für einen bestehenden Actor jetzt eine seiner nativen COST-Animationen als
einmalige Startanimation auswählen oder die Startanimation deaktivieren.
Auswahl und Änderung bleiben im gemeinsamen Projekt-JSON erhalten; der
bestehende SCUMM-v6-Exporter gibt `animateActor` mit dem bereits validierten
Animationsindex aus. Es ist keine neue Runtime-Funktion. Native Wiedergabe
von importierten PNG-Mehrframe-Costumes bleibt bis zum echten
ScummVM-Bildnachweis offen.

**Actor zur Laufzeit versetzen (2026-11-08):** In einer geordneten
Studio-Objektinteraktion lässt sich jetzt ein Actor an eine neue X-/Y-Position
im selben Raum setzen. Der typisierte `move_actor`-Schritt wird im
versionierten Projekt-JSON gespeichert und als natives
`putActorAt(actor, x, y, room)` zusammen mit den bisherigen Animations-,
Warte- und Objektzustandsschritten ausgegeben. Der Studio-Editor bietet
die Aktion direkt an. Geprüft sind Modell-/Exportpfad und die bestehende
Regression; **die interaktive Auslösung im stock ScummVM ist noch offen**.
Nächstes Produktpaket: tatsächliches Mehrframe- und Actor-Bewegungs-
Gameplay im nativen Compiler-/Interpreterpfad nachweisen.

**Laufbewegung als Story-Interaktion (2026-11-08):** Zusätzlich zum
sofortigen `move_actor`-Versetzen kann das Studio jetzt einen Actor per
`walk_actor` im selben Raum zu einer Zielposition schicken. Das
versionierte JSON und der SCUMM-v6-Exporter verwenden das bereits für
den Demo-Spieler belegte native `walkActorTo`; nachfolgende Aktionen
laufen bewusst ohne implizite Ankunftssperre weiter. Die visuelle
Spielprobe und eine später explizite `waitForActor`-Choreografie bleiben
offen. Das nächste Produktgate bleibt echter ScummVM-Nachweis für
Actor-Laufbewegung und die importierten Mehrframe-Costumes.

**Warten auf Actor-Ankunft (2026-11-08):** Der Studio-Interaktionseditor
hat nun einen expliziten `wait_actor`-Schritt. Auf einen
`walk_actor`-Laufauftrag kann so ein natives `waitForActor(actor)` folgen,
bevor weitere Animations- oder Objektaktionen ausgeführt werden.
Das Projekt-JSON bewahrt die Reihenfolge; nur im selben Raum vorhandene
Actors sind gültig. Die ScummC-Signatur ist im unveränderten upstream
`examples/road/road.scc` und `examples/openquest/officeroom.scc` belegt.
Ein interaktiver ScummVM-Nachweis der neu authorbaren Actor-Choreografie
bleibt offen. Nächstes Gate: diese Abfolge und importierte Mehrframe-
Costumes im echten Spiel beobachten.

**Actor-Blickrichtung zur Laufzeit (2026-11-08):** Der Studio-Ablauf
enthält nun `face_actor` als eigenständige Aktion mit N/E/S/W-Auswahl.
Projekt-JSON und Validator halten Actor- und Raumreferenz fest; ScummC
verwendet das in upstream `examples/road/road.scc` belegte Paar
`setCurrentActor`/`setActorDirection` und stellt danach `VAR_EGO` als
aktiven Actor wieder her. Der Schritt ist mit Bewegung, Ankunfts-Wait,
Animation und Objektzustand kombinierbar. Die interaktive ScummVM-
Choreografie ist weiterhin nicht als V belegt.

**Native Mehrframe-Animation – ausführbarer Bildnachweis (2026-11-08):**
Die bestehende Studio-PNG-Actor-Probe sammelt jetzt während eines einzigen
stock-ScummVM-Spielstarts mehrere Szenenbilder und verlangt sichtbare
Pixel beider unterschiedlich gefärbten COST-Frames. Ein bloßer Spielstart
oder identisches Standbild reicht nicht mehr aus. Der experimentelle
ScummC-Workflow läuft für diese Probe nun auch bei passenden Pull Requests;
die Einzelbilder werden als CI-Artefakte bereitgestellt. **Bis zu einem
erfolgreichen nativen Lauf bleibt die V-Einstufung offen.** Das folgende
Paket ist die Auswertung und bei Bedarf Korrektur der konkreten nativen
Spielgrafik, danach der Actor-Lauf-/Wait-/Dreh-Choreografie.

**Erster tatsächlicher CI-Lauf und konkreter Fix (2026-11-08):** Der native
Lauf `42493144908` kompiliert die Studio-COST, startet ScummVM und liefert
24 Bilder; die erwarteten PNG-Farben erscheinen darin jedoch nicht. Die
Original-ScummC-COST-Palette enthält **absolute Raum-Palettenindizes**,
deren RGB-Werte im bisherigen Export nicht in die Room-BMP übernommen
wurden. Der Export gleicht deshalb nun die belegten COST-Farben aller
gebundenen Actors über einen gemeinsamen, deterministischen Indexplan ab
und ergänzt die Räume, ohne das Authoring-JSON zu verändern. Belegte
Room-Artwork-Indizes bleiben reserviert; bei erschöpften Plätzen wird der
Exporter-Blocker ausdrücklich gemeldet. Ein gezielter BMP-Palettenvergleich
ist grün. Im erneuten nativen Lauf `42493988461` sind beide Costume-Farben
in 26 ScummVM-Aufnahmen sichtbar und wechseln ihre Dominanz. Die
Abnahme fordert nun ausdrücklich diesen zeitlichen Wechsel statt nur
zweier irgendwann vorhandener Farben. Der finale native Lauf
`42494840322` ist grün: Die aus Studio-PNGs exportierten Costume-Frames
wechseln sichtbar im unveränderten ScummVM. PR #54 wurde nach den
vollständigen CI-Prüfungen gemergt (`bbba784`). Die gesamte Actor-
Choreografie durch Spielereingaben bleibt weiter als V offen.

**Studio-Interaktionseditor (2026-11-08):** Ein bestehender Schritt lässt
sich nun auswählen, in die vorhandenen Aktionsfelder zurückladen und am
selben Platz ersetzen. Actor, Animation, Bewegung, Blickrichtung, Pause
und Objektzustand nutzen weiterhin das validierte Projektmodell und den
existierenden nativen Exportpfad. Das Bearbeiten erfordert kein Löschen
und erneutes Anhängen und verändert nicht das auslösende Hotspot-Verb.
**Nächstes Produktgate:** Eine vollständige, vom Studio authorbare
Actor-Lauf-/Wait-/Dreh-/Animationsfolge durch einen tatsächlichen
ScummVM-Verb-Klick nachweisen.

**Native Klick-Choreografie (ScummVM-Teilnachweis, 2026-11-08):** Ein
End-to-End-Spiel wird aus dem gleichen `append_sequence_step`-Pfad wie der
Studio-Editor erzeugt. Der reale `Close`-Klick auf den Schlüssel soll
`Guide` versetzen, laufen lassen, auf die Ankunft warten, drehen,
animieren und anschließend die Tür öffnen. Die Actions-Probe archiviert
Projekt-JSON, generierten SCUMM-Quelltext, Bilder vor/nach dem Klick und
den Zustandsbericht. Im unveränderten ScummVM öffnet der reale Klick die
vorher geschlossene Tür nach der generierten sechsstufigen Folge (CI
`42501905023`, `response_seconds=3.44`). **Das ist ein Teilnachweis des
geketteten Verbablaufs**, kein Einzelbeweis für jeden Animationframe oder
jede Walkbox-Position. Als nächstes sind solche visuellen Actor-
Zwischenzustände und Wiederholung/Abbruch im Spiel gezielt zu prüfen.

**Zustandsgebundene Interaktionsfolgen (2026-11-08, Teilnachweis):**
Eine vorhandene Hotspot-/Verbfolge kann im Studio optional nur bei einem
konkreten Raumobjektzustand (0–2 im derzeitigen Exportvertrag) ausgeführt
werden. Modell, JSON-v1-Roundtrip und Gradio-Editor verwenden dieselbe
Bedingung; der ScummC-Export setzt ein natives `getObjectState`-Gate vor
die geordneten Aktionen. Ohne Bedingung bleibt die bisherige JSON-Ausgabe
unverändert. Der bestehende reale Klick-Actor-Ablauf mit Türzustand 1 als
Voraussetzung lief im unveränderten ScummVM erfolgreich (CI `42505166878`,
PR #57 gemergt). Der negative Zustand und die Wiederholung waren noch offen.

**Mehrere Zustandsvarianten je Verb (2026-11-08, ScummVM nachgewiesen):** Im Studio
können bestehende Folgen für einen weiteren Zustand desselben Raumobjekts
dupliziert und unabhängig bearbeitet werden. Der Export führt sie unter
einem einzigen nativen `case` mit disjunkten Zustandsvergleichen aus und
akzeptiert optional eine bedingungslose Fallback-Folge. Mehrdeutige
Varianten werden schon im Projektmodell abgewiesen. Der native
Spielablauf führte dieselbe `Close`-Aktion dreimal aus: Türzustand
1 → 2 → 1 → 2, einschließlich Rückkehr zur ersten Actor-Choreografie.
CI `42506834029`, Artefakt `native-v6-studio-actor-sequence`. Beim ersten
Lauf zeigte sich ein wandernder Kameraausschnitt; die Klickprobe bestimmt
deshalb vor jeder Eingabe die aktuelle Hotspot-Position neu, ohne die
Studio-Produktlogik zu ändern.
**Neues Teilpaket:** Studio-Verbfolgen können optional mit Escape übersprungen
werden. ScummC emittiert native `try`/`override`-Blöcke; der Override setzt
die letzten dokumentierten Raumobjekt-Zustände, Actor-Zielpositionen und
Blickrichtungen. Das veränderte native Klickszenario sendet Escape während
eines Actor-Ablaufs und prüft den Türzustand (CI `42508973832`, PR #59).

**Aktuelles Produktpaket:** Studio-Interaktionsfolgen können nun einen
aufnehmbaren Gegenstand als nativen `pickupObject`-Schritt enthalten – auch
innerhalb einer bedingten Variante. Beim Escape-Skip wird dieser Effekt
ebenfalls angewendet, sodass die Inventaraufnahme nicht an einer übersprungenen
Wartezeit verloren geht. Die native Probe ergänzt deshalb die zweite
Zustandsvariante um einen eigenen Token und kontrolliert dessen Inventar-Icon
nach Escape. Vollständige Ton-/Raumwechsel-Skip-Zustände bleiben offen.

**Nächstes Produktpaket:** Eine `Inventar kombinieren`-Aktion kann im
Studio an ein bestehendes Raumrezept gebunden werden. Die normale Sequenz
prüft den Besitz beider Eingangsobjekte, verbraucht sie und erzeugt das
Rezeptresultat mit nativen SCUMM-Befehlen. Der Escape-Pfad übernimmt die
vorherigen Aufnahmen und die Kombination in derselben Reihenfolge. Das
Stock-ScummVM-Szenario überprüft dafür ein aus Token und Shard erzeugtes
Badge nach Escape; der CI-Nachweis steht bei Erstellung noch aus. Audio-
und Raumwechsel-Endzustände bleiben außerhalb dieses Pakets.

**Folgepaket Raumwechsel am Sequenzende (2026-11-08, Implementierung):**
Im Studio kann `Raum wechseln` als letzter Schritt einer Hotspot-/Verbfolge
auf einen existierenden Projekt-Raum zeigen. Der JSON-v1-Vertrag nimmt
optional `change_room` auf; frühere Projekte bleiben unverändert. Der
ScummC-Exporter gibt `startRoom` erst **nach** den bisherigen Schritten und
bei überspringbaren Folgen erst **nach** `try`/`override` aus, damit Actor-,
Objekt- und Inventar-Endzustände vor dem Wechsel angewendet werden. 287 lokale
Tests grün, darunter Editor-/JSON-/ScummC- und Ungültigzielprüfungen.
**Native Abnahme ergänzt:** Die bestehende echte `Close`-Spielprobe führt
nach der Inventarkombination eine separate Studio-`Door`-Sequenz aus,
überspringt ihre sechssekündige Wartezeit, betritt `Cellar`, kehrt über
`Stairs` nach `Harbor` zurück und prüft offene Tür sowie Badge im Inventar.
Die neue Zusammensetzung bestand im unveränderten ScummVM (Actions
`42514653114`, Actor-Choreografie-Schritt). Der erste Gesamtlauf hatte
einen nachgelagerten zeitabhängigen PNG-Costume-Fehler; dessen Wiederholung
hat den PNG-Schritt bestanden. Gesamtworkflow und weitere CI-Gates sind
gesondert abzuschließen. **Keine vollständige S04-Abnahme**, da native
Audio-Endzustände offen sind.
**Nächstes Produktpaket:** Sequenz-Audio-Cues und ihr definierter Escape-
Endzustand über Studio/JSON/ScummC/stock ScummVM nutzbar machen.

**Sequenz-Audio-Produktpaket (2026-11-08, Implementierung):** Das Gradio-Studio
nimmt echte MIDI-Dateien entgegen und bindet sie als versionierte, eingebettete
`music_assets` an einen Raum. Der normale native ZIP-Export erzeugt mit
ScummCs `soun -gmd` die benötigte SOUN-Ressource ohne eine externe Studio-
Runtime; fehlende/ungültige Ressourcen werden nicht still übergangen.
Interaktionssequenzen besitzen nun `Musik starten` und `Musik stoppen`, mit
nativen `startMusic`/`stopMusic`-Schritten. Der Escape-Override übernimmt
den **letzten** Musikeffekt vor einem möglichen terminalen Raumwechsel.
JSON-v1-Projekte ohne Audio bleiben unverändert. 288 lokale Tests grün.
Die native Actor-Klickprobe kompilierte das Studio-MIDI zu `SOUN`, lief im
unveränderten ScummVM und erfasste drei zeitlich abgegrenzte PCM-Fenster
(Actions `42517210707`, Actor-Schritt erfolgreich): Aktivität vor dem
Escape-Stopp `0,9482`, danach `0,2686`, nach erneutem Start `0,9830`.
Der relative Stop-/Wiederstart-Unterschied ist ein **verbindliches
CI-Gate** und wurde im finalen PR-Lauf `42517572328` (Wiederholung nach
einem nicht reproduzierten älteren Tür-Smoke-Fehlschlag) erneut bestanden.
Alle Pflichtworkflows des Pakets sind grün.
Die allgemeine iMUSE-/Beat-/Taktabdeckung bleibt offen.
**Nächstes Produktpaket nach der CI-Abnahme:** frei authorbare Soundeffekte
mit eigenen Ressourcen und synchronisierten Spielereignissen.

**Studio-VOC-Soundeffekte (2026-11-08, Implementierung und lokale Tests):**
Pro Raum lassen sich originale Creative-Voice-(`.voc`)-Dateien mit eindeutiger
Sound-ID importieren. Die Studio-Sequenzaktionen `Sound starten` und
`Sound stoppen` erzeugen native `startSound`-/`stopSound`-Aufrufe; der
Escape-Override übernimmt für **jede** beteiligte Sound-ID die letzte
Aktion. JSON-v1-Roundtrip und Projekt-ZIP enthalten die binären VOC-Daten,
der reguläre ScummC-Export kompiliert sie über `soun -voc` zu SOUN.
289 lokale Tests grün, einschließlich zweier unabhängiger Sound-Endzustände
in derselben Sequenz und Fake-Toolchain-Export. Eine zusätzliche native
Hotspot-Klickprobe mit PCM-Vorher-/Während-/Nachher-Fenster ist als
CI-Gate vorbereitet; **stock-ScummVM-Nachweis noch ausstehend**.
VOC-Sprachvarianten, Untertitel und Synchronisierung mit Actor-Lippensprache
bleiben offen.

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
