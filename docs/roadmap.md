# Adventure Studio – Produkt- und Entwicklungsroadmap

> **Aktive Steuerung, Stand 2026-11-07:**
> [Produktvision](PRODUCT_VISION.md) · [Projektstatus und nächstes Arbeitspaket](PROJECT_STATUS.md) ·
> [SCUMM-v6-Funktionsmatrix](SCUMM_V6_CAPABILITIES.md) · [Arbeitsvertrag](../AGENTS.md).
> Die nachstehenden älteren Checkboxen dokumentieren historische Teilnachweise.
> Sie bedeuten **nicht**, dass die entsprechende vollständige SCUMM-v6-Funktion
> fertig ist. Für die aktuelle Abdeckung gilt die Funktionsmatrix.

## Aktuelle Produktphasen und Abnahme

1. **P1 – Vollständiger nativer SCUMM-v6-Generator (jetzt):**
   Raumgrafiken, Masken, Walkboxen, Objekte, Actors/Costumes, Animation,
   zeitabhängige Aktionen, Rätsel, Kamera, Cutscenes, Dialog, Audio und
   Persistenz werden als native Ressourcen/Skripte exportiert.
   Abnahme: pro erforderlicher Mechanik ein Compiler-/Format-Gate und
   ein konkreter ScummVM-Gameplay-Nachweis.
2. **P2 – Durchgängiger visueller Adventure-Editor:**
   Alle unterstützten P1-Daten aus dem Projektmodell authorbar.
3. **P3 – Cineastischer Shot-/Cutscene-Editor:**
   Filmbegriffe auf native Kamera-/Raum-/Costume-/Script-Bausteine abgebildet.
4. **P4 – KI-gestützte Spieleentwicklung:**
   Validierte, nachvollziehbare Änderungen statt unkontrolliertem Code.
5. **P5 – Produktreife:** Distribution, Bedienbarkeit, Stabilität, Qualität.

### Verbindlicher SCUMM-v6-Funktionsvertrag

Die [Referenzbibliothek](scumm-v6-reference/README.md) ist der dauerhafte
technische Zugang zu ScummC-/ScummVM-Primitiven und
[Abnahmeszenarien](scumm-v6-reference/SCENARIOS.md). Die
[Funktionsmatrix](SCUMM_V6_CAPABILITIES.md) bleibt **einziger**
64-ID-Katalog für Scope und I/T/V-Status. Der
[Quellenindex](scumm-v6-reference/capability_sources.json) wird gegen
die Matrix getestet; bereits analysierte Primitive werden wiederverwendet.
Die nächsten vertikalen Pakete bleiben P0.1–P0.3; wir ersetzen sie nicht
durch ein großes vorgeschaltetes Konformitätsspiel.

### Architektur- und Regression-Gates

[Architekturaudit](architecture-audit.md) ·
[Architekturverträge](architecture-contracts.md) ·
[ADR-0001](adr/0001-domain-and-export-boundaries.md) ·
[ADR-0002](adr/0002-limits-evidence-and-compatibility.md).

- [x] Bestand auf künstliche Demo-/Adapter-Limits geprüft; A0-Befunde
      dokumentiert; feste Story-/JSON-Koordinatenbegrenzungen entfernt.
- [x] Grenzfall-Regressionen für 0/1/2/N Dekorationen, Platzierungen,
      JSON-Sammlungen >128, Anforderungen >32 und Fail-Closed-Export;
      vorhandene JSON-/Export-Fälle unverändert grün.
- [x] Fachlich gültige Änderungen bei aktuellem Export-Limit editierbar;
      maschinenlesbare Blocker nach Zielprofil, Feature-Code und Objekt
      verfügbar. Unbekannte Compilergründe sind ausdrücklich generisch.
- [x] Studio-Raumvorschau benötigt keinen erfolgreichen SCUMM-Export mehr;
      sichtbare Authoring-Platzhalter werden nicht als Gameplay beworben.
- [x] Vorhandene Mengen-/Geometrie-/Layoutgrenzen nach ADR-0002
      [klassifiziert](architecture-audit.md); ohne nativen Quellbeleg gelten
      übrige Compilerquoten als vorläufige `EXPORTER_LIMIT`.
- [ ] Native Grenzen bei den jeweiligen P0.x-Arbeitspaketen mit
      ScummC/ScummVM-Quellen beweisen bzw. vorläufige Exporterquoten ersetzen.

### Aktueller Arbeitsvorrat (P1)

- [ ] **P0.1 (mit A0-Regression-Gates):** Binär-Roundtrip-Parser für ScummC-Raumdaten
      (RMIM/SMAP/ZPxx/OBIM/OBCD), mit Test-Fixture und Größen-/Offset-/ID-Prüfungen.
- [ ] **P0.2:** Z-Plane-/Maskenbilder in RoomAsset, JSON, Validierung und
      ScummC-Export; sichtbare Verdeckung in stock ScummVM.
- [ ] **P0.3:** Native Walkboxen, BOXM, SCAL und Perspektive;
      Actor-Weg und Maskenzuordnung in ScummVM geprüft.
- [ ] **P0.4:** Bewegte, zustandsabhängige, klickbare Objekte einschließlich
      Parent-State und aktualisierter Hitbox.
- [ ] **P0.5:** Native Actor-/Costume-Ressourcen, Animation, COUNT-Marker
      und zeitabhängige Skriptreaktionen.
  - [x] Teil-Gate: unabhängig erzeugte, original-v6-COST-Ressourcen mit
        Richtungs-/Framefolgen und expliziten `COUNT`-Kommandos via ScummC.
        Native Darstellung in ScummVM und positive/negative
        `getActorAnimCounter1`-Gameplay-Probe belegt
        ([COST-Vertrag](scumm-v6-native-costume-count-contract.md)).
  - [x] Teil-Gate: COST-Frames und Animationen in `GameDocument`-JSON v1
        authorbar, verlustfrei roundtrip-fähig und als ScummC-Inputs exportiert;
        native Actor-Symbol-/Spielbindung ist weiterhin offen.
  - [x] Teil-Gate: Mehrere Actor-Instanzen mit referenzierter COST, initialer
        Position und Blickrichtung; Modell/ScummC-Bootstrap-Bindung und
        nativer ScummVM-Start nachgewiesen. Eine benannte Startanimation
        löst COUNT-Ereignisse am projektdefinierten Actor aus (positive
        Zwei-COUNT- und negative Drei-COUNT-Kontrolle, Actions `42421713939`).
  - [x] Teil-Gate: Versionierte `ActorCountCondition` und `ObjectStateEffect`
        mit nativer Script-Ausgabe und einer aus Projekt-JSON geladenen,
        in stock ScummVM getesteten COUNT-Objektreaktion. Native CI
        `42461862069` mit JSON-Projektregel und manueller Negativkontrolle.
  - [x] Teil-Gate: deklaratives `AnimationInputRule`-Zeitfenster mit
        früh/spät getrennten nativen Objektzuständen. Stock-ScummVM-Probe
        bestätigt 0/1/2 Spieleraktionen einschließlich erneuter Eingabe
        **im selben Prozess**; CI `42467237997`.
  - [x] Teil-Gate: Dieselbe späte, deklarative Eingabe bleibt nach
        `Harbor → Cellar → Harbor` über normale `WalkTo`-Hotspots erhalten:
        Schlüssel weiterhin unsichtbar, Tür offen. Native CI `42468551627`.
  - [x] Teil-Gate: Initialanimation pro Actor nur einmal über ein globales
        natives SCUMM-Bit starten. Ein adversarialer COUNT-Wächter würde
        nach Wiedereintritt den Schlüssel wiederbeleben; die stock-ScummVM-
        Probe `42471602488` bestätigt, dass dies ausbleibt.
  - [ ] Allgemeine Actor-Zuordnung, Animations-Cue-/Condition-IR und
        projektgetriebene Aktionsfenster sind **nicht** durch das Fixture gelöst.
- [ ] **P1.1:** Native Kameraführung, Shot-Komposition und Cutscene-
      Kontrollfluss mit Skip-Endzustand.
  - [x] Teil-Gate: unbeschränkte native v6-Raum-Kamera-Cues
        (`setCameraAt`, `panCameraTo`, `waitForCamera`, `cameraFollowActor`),
        dokumentierter Binärpfad und zwei in stock ScummVM verglichene
        Bildkompositionen ([Kamera-Vertrag](scumm-v6-camera-cue-contract.md)).
        **Nicht** als Abschluss von P1.1 werten: Override/Skip, Shots und
        Actor-Choreografie sind weiterhin offen.

Detaillierte Abhängigkeiten: [Export-Lückenanalyse](scumm-v6-export-gap-analysis.md).
Diese Liste ist **kein Abschluss** des v6-Funktionsumfangs; weitere
Funktionen werden anhand der Capability-Matrix priorisiert.

## Historische, detaillierte Entwicklungsmeilensteine

Stand: 2026-11-04. Dieses Dokument ist die Arbeitsgrundlage für die Umsetzung.

**Mechanik-Erweiterung (2026-11-07):** Der vollständige Anforderungskatalog
für typische, auch zeitabhängige klassische Adventure-Spielabläufe steht in
[`scumm-adventure-mechanics.md`](scumm-adventure-mechanics.md). Die erste
quellenbasierte Zuordnung zu originalen v6-Operationen und offenen
Kompatibilitätsfragen steht in
[`scumm-v6-runtime-contract.md`](scumm-v6-runtime-contract.md).
Diese Dokumente sind Forschungs-/Entwurfsstände, keine als implementiert
markierten Produktfeatures.
Die vertiefte Prüfung konkreter ScummVM- und ScummC-Quellcodepfade ist in
[`scumm-v6-source-audit.md`](scumm-v6-source-audit.md) dokumentiert.

## Produktziel

Eine storyorientierte, KI-gestützte Entwicklungsumgebung für Point-and-Click-
Adventures. Nutzer beschreiben und ändern Handlung, Kapitel, Räume, Figuren,
Gegenstände, Dialoge und Rätsel in natürlicher Sprache. Adventure Studio hält
ein einheitliches, strukturiertes Projektmodell, prüft Änderungen
deterministisch und erzeugt **originale SCUMM-v6-Spieldaten**. Das primäre
Laufzeitziel ist ScummVM; klassische DOS-Interpreter sind optional und werden
gesondert geprüft. AGS ist kein Ausgabeformat.

## Architekturinvarianten

1. **Eine Datenquelle:** Die Story und der Spielzustand liegen in einem
   versionierten, typisierten Modell; Grafiken referenzieren stabile IDs.
2. **Kein KI-generierter Laufzeitcode:** KI-Ausgaben sind deklarative und
   validierte Modelloperationen. Ein deterministischer Compiler erzeugt SCUMM.
3. **Atomare Änderungen:** Entwurf, Vorher/Nachher-Diff, Referenzprüfung,
   Erreichbarkeitsanalyse, Konsolidierung und erst danach Commit.
4. **Bereinigung mit Transparenz:** Verwaiste Daten werden ausgewiesen;
   sicher automatisch löschbare Daten können entfernt werden. Inhaltlich
   relevante Elemente werden nicht stillschweigend gelöscht.
5. **Reproduzierbarkeit:** Gleiche Projekt- und Toolchain-Versionen müssen
   identische exportierte Ressourcen erzeugen. Alle Compilergrenzen haben Tests.
6. **Ehrliche Kompatibilität:** Asset-Generierung, Binärlinking, Erkennung,
   Spielstart, grafische Darstellung, Interaktion, Scrolling und Save/Load
   sind unabhängige Gates. Ein grüner Workflow allein ist kein Gameplay-Beweis.
7. **Grenzflächen statt Spaghetti:** UI, KI-Adapter, Modell, Validierung,
   Ressourcen-Generator und SCUMM-Exporter bleiben voneinander getrennt.

## Mehrsprachigkeit (SCUMM-v6-Kompatibilitätsblock)

Ein verlinktes Spiel soll die Sprachen Deutsch, Englisch, Französisch,
Polnisch und Japanisch zur Laufzeit anbieten. Text-IDs bleiben unabhängig
von der Sprache und referenzieren dieselbe Spielmechanik. Die technische
Analyse und die offenen Nachweispunkte stehen in
[`docs/localization-compatibility.md`](localization-compatibility.md).

- [x] Strikter, versionierter Unicode-Übersetzungskatalog mit vollständigen
      Sprachvarianten und deterministischer Zeichensatzbedarfsanalyse.
- [x] Stabile Sprach-IDs und ScummC-Quelltextfragment mit fünf bedingten
      Textzweigen; Polnisch und Japanisch mit eigenen Testfällen.
- [x] Deterministische CHAR-Bitmap-Vorbereitung mit überprüfter Font-Cmap,
      ScummC-Konverter-Aufruf und Ressourcenslot-Prüfung; unabhängiger
      `font-smoke.yml`-Workflow für alle fünf Sprachen vorbereitet.
- [ ] Font-Glyphen für die benötigten Bytecodes als SCUMM-CHAR-Ressource
      erzeugen und **im Interpreter** nachweisen; erfolgreiches Konvertieren
      allein genügt nicht.
- [ ] Laufzeit-Sprachwahl, Raumwechsel und Save/Load in stock ScummVM prüfen.
- [ ] Sprachausgabe (VOC) je Sprachvariante unabhängig verifizieren.
- [ ] Erst nach grünen Interpretertests ins normale Story-/SCUMM-Exportmodell
      integrieren; bis dahin keine scheinbar spielbare Unicode-Ausgabe.

## Meilensteine und Akzeptanzkriterien

### M0 – Technisches Fundament (teilweise abgeschlossen)

- [x] Typisierte Zustands-/Storymodelle, atomare Änderungen und Tests.
- [x] SCUMM-v6-Ressourcen aus deterministisch erzeugtem Bitmap/Raumskript.
- [x] Compiler und Linker über ScummC in CI erfolgreich ausgeführt.
- [x] ScummVM startet eine separate DOTT-Kompatibilitäts-Testvariante.
- [ ] Eigene Erkennung in unveränderter ScummVM (separater Kompatibilitätsblocker).

### M1 – Spielbarer Raum (aktiv)

- [ ] Spielfigur ist sichtbar und animiert.
- [ ] Spielfigur kann kontrolliert laufen; Walkboxes und Grenzen funktionieren.
- [ ] Zwei Bildschirmbreiten werden korrekt horizontal gescrollt.
- [ ] Ein Gegenstand erscheint an der richtigen Position und hat einen Hotspot.
- [x] Erster eigener Gegenstand wird als SCUMM-Bitmap gerendert und im
      Kamerabild nachgewiesen (goldener Schlüssel; Pixelprüfung integriert).
- [x] Automatisierte Screenshots belegen zwei verschiedene Kamerapositionen
      (CI-Lauf #41850260115: Blau-zu-Orange-Marker, 92 428 geänderte Pixel).
- [x] Konsolenlogs und Screenshot-Artefakte stehen in GitHub Actions zur Verfügung.

### M2 – Geschlossenes Mini-Adventure

- [x] Schlüssel aufnehmen, ins Inventar übertragen und visuell bestätigen
      (CI-Lauf #41863693962).
- [x] Verschlossene Tür, Schlüsselprüfung, sichtbarer Offen-Zustand und
      separater Klick für den Raumwechsel (CI-Lauf #41876135550).
- [x] Teilziel: deklarative `UseRule` kompiliert und echtes „Use Key with Door“
      entfernt den Tür-Sprite in ScummVM (CI-Lauf #41870570921).
- [x] Teilziel: echtes `startRoom(Cellar)` und sichtbarer Zielraum in stock
      ScummVM nachgewiesen (CI-Lauf #41872141558).
- [x] Deklaratives Ziel „Keller erreichen“, genau ein Zielraum und prüfbares
      Zielmanifest (`game-goal.json`); lokale Validierung und Tests grün.
- [x] Zielmanifestauswertung und Zielraum in ScummVM-CI bestätigt
      (CI-Lauf #41876135550); Abschlussdialog wird kompiliert, aber nicht
      gesondert als Textinhalt aus dem Frame erkannt.
- [x] Geöffnete Tür und aufgenommener Schlüssel bleiben beim Verlassen und
      erneuten Betreten des Hafens erhalten (CI-Lauf #42020306920).
- [ ] Save/Load erhält diese Zustände; bislang nicht geprüft.
- [x] Negativfall „verschlossene Tür ohne Schlüssel“ im Gameplay-Test sowie
      Softlock-Erkennung im deterministischen Story-Solver geprüft.

### M3 – Adventure aus Daten

- [ ] Vollständiges M2-Beispiel ausschließlich aus dem Projektmodell exportieren.
- [ ] Keine projektindividuellen handgeschriebenen Runtime-Skripte nötig.
- [x] Zwei unterschiedliche SCUMM-Raumprojekte aus denselben Generatorbausteinen
      bauen (Datenmodell- und Dateivergleichstest sowie Story-JSON-Variante in
      stock ScummVM gestartet: CI-Lauf #42020306920).
- [x] Kanonisches JSON-Projektformat v1 mit deterministischem Export,
      strikter Feldprüfung und Dokumentation (`docs/project-format.md`).
- [x] Erster begrenzter Story-zu-SCUMM-Adapter: Kapitel, zwei Szenen,
      Schlüssel, Dekoration, Tür-Rätsel und Zielraum werden ohne Rohgrafikdaten
      des Autors übersetzt (`story_to_scumm.py`, lokale Tests).
- [x] Versionierter Story-JSON-Eingang mit strikter Validierung, kanonischem
      Export und bytegleichen Wiederholungs-Builds (`story_document.py`).
- [x] Bis zu drei erforderliche Inventargegenstände werden als deklarative
      Inventarbedingungen und automatisch abgeleitete Icon-Ressourcen übersetzt.
- [x] ScummVM-CI für den unabhängigen Story-JSON-Build und das getrennte
      `story-playable-preview`-Artefakt erfolgreich (#42020306920).
- [x] Vollständige Schlüssel-Tür-Rätselinteraktion des aus Story-JSON
      kompilierten Adventures in stock ScummVM erfolgreich (#42021639269).
- [x] Dynamischer ScummC-Compiler-/Linker-Adapter liest Raum- und Inventarliste
      aus dem Projekt, statt projektspezifische Namen im CI-Workflow zu pflegen
      (`scumm_toolchain.py`, lokale Boundary-Tests und erfolgreicher ScummVM-
      Gameplay-Lauf #42022413382).
- [x] Zwei erforderliche Gegenstände als vollständigen Story-JSON-zu-ScummVM-
      Gameplay-Test nachgewiesen: Schlüssel allein öffnet die Tür nicht,
      zusätzlicher Gegenstand wird in das Inventar übernommen, danach öffnet
      die Tür und der Zielraum wird betreten (CI-Lauf #42023767043).
- [x] Drei erforderliche Gegenstände in stock ScummVM nachgewiesen: sowohl
      Schlüssel allein als auch Schlüssel und Abzeichen ohne Münze lassen die
      Tür verschlossen; erst das vollständige Inventar öffnet den Zielraum
      (CI-Lauf #42024978434).
- [x] Lineare Rätselkette mit zwei Türen und drei Szenen: Story-JSON-Export,
      verknüpfte Ressourcen und ScummVM-Start erfolgreich (CI #42026108989).
- [x] Vollständigen Spielweg durch beide Türen der Rätselkette in ScummVM
      nachgewiesen: Hafenhaus-Schlüssel, erster Raumwechsel, Keller-Abzeichen,
      zweite Tür und finaler Archivraum (CI-Lauf #42028572233).
- [x] Persistente Zustände und Rückwege über mehrere verknüpfte Räume hinweg
      in stock ScummVM geprüft: Archiv → Keller → Hafenhaus; beide Türen
      bleiben geöffnet, beide Gegenstände bleiben im Inventar und erscheinen
      nicht erneut in den Räumen (CI-Lauf #42029750897).
- [x] Deklaratives Story-Rezeptmodell v2: exakt zwei Zutaten, ein hergestelltes
      Ergebnis, einmalige Entnahme vom Boden, atomare KI-Änderungen,
      deterministische Spielbarkeitsprüfung auch bei Verbrauchs-Softlocks und
      Bereinigung nicht mehr referenzierter Pickups mit Änderungsbericht
      (ohne SCUMM-Laufzeitexport).
- [ ] Inventar-zu-Inventar-Kombinationen in SCUMM v6 kompilieren und den
      kompletten Spielablauf bis zum Ziel in ScummVM nachweisen.
- [ ] Adapter auf weitere Rätseltypen, mehrere Kapitel, Figuren und Dialoge
      erweitern; die aktuelle Platzhaltergrafik durch einen Asset-Generator
      ersetzen und End-to-End-Spielbarkeit eines adaptierten Projekts testen.

### M4 – Grafik- und Animationspipeline

- [ ] Einheitliche Stile, Figuren- und Raumvarianten, Paletten und Animationen.
- [ ] KI-Bilder vor Verwendung deterministisch auf Format und Grenzen prüfen.
- [x] Erste Objektpositionen sind editierbar; `Story`-Format v3 enthält
      optionale `placements` mit stabilen Item-IDs, strikter Referenz-/
      Geometrieprüfung, atomarem Änderungsbericht und abwärtskompatiblem
      JSON. Der SCUMM-Exporter setzt die Objekt-Hotspots entsprechend.
- [x] Provider-unabhängiger Vertrag für fertige 8-Bit-Indexbilder, inklusive
      Palette, Abmessungen, Herkunft und reproduzierbarem Content-Hash;
      Offline-Fixture-Provider mit Validierung und Tests (`image_pipeline.py`).
- [x] Story-zu-SCUMM-Compiler liest Raumhintergründe über die Provider-Grenze;
      Standard bleibt der bisherige byteidentische Offline-Generator. Externe
      Fixture-Provider werden ohne Änderung der SCUMM-Exportkette unterstützt.
- [ ] Einen späteren ComfyUI-/RunComfy-Adapter für **vorhandene, vom Nutzer
      bereitgestellte Workflows** ergänzen; aktuell keine Verbindung, keine
      Modellwahl und keine Netzwerkaufrufe im Build.
- [ ] Generierte Assets unveränderlich zwischenspeichern (Workflow-Version,
      Modell, Seed, Quell-ID), damit Story- und SCUMM-Builds dieselben Bilder
      wiederverwenden und keine stillschweigende Neugenerierung auslösen.
- [ ] Palette-Cycling für geeignete Szeneneffekte als gesonderten,
      deterministischen SCUMM-v6-Compilerbaustein entwickeln und in ScummVM
      mit visuellen Prüfungen validieren.
- [x] Erste deterministische, providerunabhängige Palettenzyklus-Vorschau
      (`palette_animation.py`): Bereichs-/Timingprüfung, geschützte Indizes,
      disjunkte Zyklen, Vorwärts-/Rückwärtsrotation und Tests.
- [x] Deklarative Palettenzyklen werden als SCUMM-v6-`CYCL`-Ressourcen
      aus `RoomAsset` erzeugt und in das kanonische Projekt-JSON übernommen;
      reservierte Transparenz- und Sprite-Indizes dürfen nicht rotieren.
- [x] Separates opt-in-Wasserfixture und ScummVM-Screenshot-Probe in CI
      integriert, inklusive JSON-Auswertung von animiertem Wasser und
      unveränderter Himmelsfarbe (`palette_demo.py`, `scumm_palette_probe.py`).
- [x] **CI-Gate:** Stock ScummVM bestätigt vier wechselnde Wasserfarben bei
      statischem Himmel (CI #42047861523, erneut #42048814497).

Die KI-Bildworkflows sind **selbst für Pixel-Art-Stil, Zielauflösung und
Farbpalette zuständig**. Adventure Studio quantisiert oder skaliert ein
gültiges Provider-Ergebnis nicht erneut. Die Engine prüft lediglich, ob
die tatsächlich gelieferten Pixel die SCUMM-Grenzen erfüllen. Farbindizes
für Palette-Cycling sind eine zusätzliche, explizit definierte Bearbeitung:
ein hübsches Pixel-Art-Bild ist nicht automatisch farbzyklusfähig.

### M4b – Musik, Soundeffekte und Sprachausgabe

- [x] Architekturentscheidung: ereignisgesteuerte, iMUSE-orientierte Musikregie
      statt bloß einer starren Hintergrundmusik je Raum
      (`docs/audio-architecture.md`).
- [x] Typisierter, deterministischer Musikplan mit Tracks, Ereignissen,
      Übergangsanforderungen (`immediate`/`beat`/`bar`) und Bericht über
      unreferenzierte Tracks (`music_director.py` samt Tests).
- [ ] Erstes originales MIDI-/ScummC-Soundresource-Fixture in stock ScummVM
      hörbar überprüfen; Ton- oder MIDI-Nachweis in CI, kein reiner Buildcheck.
- [x] Originales MIDI-SMF-Teststück und optionales SCUMM-v6-Einstiegsmusik-
      Fixture generieren (`music_demo.py`); `soun -gmd`- und
      ScummVM-Audioerfassungsgates in CI vorbereitet.
- [x] Originale MIDI-Ressource und reale nicht-stumme PCM-Ausgabe in ScummVM
      gemessen (CI #42048814497). Kontrollspiel ohne Musik als nächstes
      Nachweis-Gate ergänzt; Ergebnis noch offen.
- [ ] Spielereignisse steuern Start, Stop und musikalischen Zustandswechsel.
- [ ] iMUSE-Beat-/Takt- und Hook-Übergänge als **eigene** Kompatibilitäts-Gates
      nachweisen; keine unbemerkte Herabstufung auf harte Schnitte.
- [ ] Wiederverwendbare Soundeffekte und klassische VOC-Sprache mit
      Untertiteln, später optionalen Generator-Providern und Provenienz.

### M5 – KI-Story-Regie

- [x] Erste **providerunabhängige Story-Regie**: natürlichsprachlicher
      Änderungswunsch plus kanonischer Projektstand als Eingabe, untrusted
      JSON-Operationen als Ausgabe. Die deterministische Pipeline prüft
      sämtliche Änderungen atomar, konsolidiert, verifiziert die Spielbarkeit,
      testet die SCUMM-Exportgrenze und zeigt den Diff vor Bestätigung.
      Keine KI-Ausführung oder generierten Skripte.
- [x] Optionaler OpenAI-Responses-Adapter mit explizitem Opt-in über
      `OPENAI_API_KEY`, ohne Server-Speicherung (`store=false`) und ohne
      Abhängigkeit des Kerns vom Anbieter. Offline-Import fremder
      Operations-JSON bleibt möglich; echte API-Integration ist noch nicht
      mit Zugangsdaten end-to-end geprüft.
- [ ] Plot-, Kapitel- und Szenenentwürfe als validierte Operationen.
- [ ] Änderungswünsche zu Gegenständen, Rezepten, Dialogen und Rätseln.
- [ ] Ergebnisbericht: hinzugefügt, geändert, entfernt, Konflikte und Tests.
- [ ] Konflikte werden gezielt geklärt; Rollback und Revisionen sind möglich.

### M6 – Gradio Studio und MCP

- [x] Erste **Projektübersicht** als deterministisches, UI-unabhängiges
      Inventar (`studio_catalog.py`): Kapitel, Szenen, Charaktere samt
      Bildstatus, Gegenstände/Positionen, Rätsel, Rezeptkombinationen,
      Hintergrundvorschau-Galerie und ein direkt aus dem Storymodell
      abgeleiteter Beziehungsgraph mit Referenzen und Raumübergängen.
      Die Ansicht aktualisiert sich nach jedem bestätigten Edit.
- [ ] Visuelle Story-Bibel: Charakterporträts, Sprite-Sheets,
      Animationen und Raumhintergründe über **stabile Asset-Referenzen**
      im versionierten Datenmodell verknüpfen; den Bildstatus inklusive
      Erzeugungs-/Versionsinformation je Figur und Szene anzeigen.
- [x] **Storyformat v4:** Überprüfbare Referenzen für Hintergründe,
      Porträts, Lauf- und Objektsprites sowie Sprache mit Asset-ID,
      Zielobjekt, Quell-ID und SHA-256. Die Dateien selbst werden noch
      nicht geladen oder neu generiert.
- [x] **Dialog-Datenmodell v4:** Gespräche, Sprechende, Dialogknoten und
      Antwortverzweigungen mit deterministischer Erreichbarkeits- und
      Sackgassenprüfung. Die Übersicht zeigt Texte, Referenzen und Graph;
      bestehende Dialogzeilen sind im Gradio-Editor änderbar.
- [x] **Export-Grenze:** Dialoge/Assets können gespeichert werden;
      unimplementierte Inhalte werden beim SCUMM-Build ausdrücklich
      abgewiesen und im Änderungsbericht als Exportwarnung angezeigt.
- [x] **Erster SCUMM-Dialog-Compiler:** Figuren als Platzhalter-Hotspots,
      je Figur ein einfacher linearer Dialog (bis zu 16 Zeilen), `TalkTo`,
      `egoSay` und `waitForMessage`; Quellen und Projekt-JSON sind getestet.
      ScummC-Kompilierung bestätigt (#42101258027), vollständiger manueller
      ScummVM-Dialogklick steht noch aus.
- [x] Erster begrenzter **Antwortauswahl-Compiler** als typisierter,
      datenbasierter `TalkRule`-/`TalkChoice`-Baustein. Bis zu drei temporär
      eingeblendete, anklickbare Antwortobjekte; Auswahl löst lineare
      Folgezeilen aus. Quelltext-/JSON-Roundtrip-Tests grün; ScummC hat die
      Auswahl-Ressourcen kompiliert (#42103638725). Ein separater visueller
      ScummVM-Klicktest prüft nun den Zustandswechsel von verborgenen zu
      sichtbaren und wieder verborgenen Antworten; Ergebnis noch offen.
- [x] **Isolierter Dialog-CI-Workflow:** `.github/workflows/dialogue-smoke.yml`
      kompiliert ausschließlich das versionierte Dialogfixture und prüft
      die ScummVM-Eingabe mit Screenshots und JSON-Report. Unabhängig von
      den längeren Musik-/Palette-/Raumwechseltests; Laufzeitergebnis offen.
- [ ] Echte NPC-Sprechblasen, klassisches SCUMM-Gesprächsmenü, Sprecherwechsel,
      Kostüm-/Animationsresourcen und Voice-Cues mit Stock ScummVM prüfen.
- [ ] Dialogmodell als eigene versionierte Struktur: Sprechende,
      Dialogknoten, Antwortoptionen, Bedingungen, Effekte, Untertitel
      und optionale Sprach-Assets. Dialoggraph und Verzweigungen
      deterministisch auf fehlende Referenzen, unerreichbare Knoten
      und Sackgassen prüfen. Erst danach SCUMM-v6-Ausgabe erweitern.
- [ ] Interaktiver Graph mit Filtern (Kapitel, Szenen, Charaktere,
      Gegenstände, Aktionen/Dialoge), Detailauswahl und Navigation
      zum jeweiligen Editorfeld; zum Start ist der SVG-Graph lesbar.
- [x] Erste **optionale lokale Gradio-Oberfläche** mit Story-JSON-Import,
      Kapitel-/Szenenübersicht, Raumvorschau samt Hotspot-Markierungen,
      Szenen- und Gegenstandseditor, neuen Dekorationsobjekten,
      deterministischem Änderungs-/Prüfbericht und JSON-Export.
      Die UI importiert die Gradio-Abhängigkeit erst beim Start und benutzt
      `studio_service.py` als testbare, UI-unabhängige Grenze.
- [x] Manuelle Textkorrekturen ohne Änderungen am generierten SCUMM-Quelltext;
      atomare Modelländerung mit `edit_story` und zusätzlichem SCUMM-Adaptercheck.
- [x] Erste Rätselbearbeitung: Titel und notwendige Inventar-IDs ändern;
      Änderungen werden vor dem Übernehmen mit Diff, Story-Solver und
      SCUMM-Adapter geprüft. Stale Vorschläge dürfen nicht stillschweigend
      gegen einen neueren Storyzustand übernommen werden.
- [ ] Vollständiger Rätsel-, Kapitel- und Dialogeditor, Drag-and-drop-Positionierung und
      eine tatsächlich live gestartete ScummVM-Spielvorschau.
- [ ] Browser-UI nach dem ersten Gradio-CI-Smoke interaktiv evaluieren;
      separate `.github/workflows/studio.yml` installiert das optionale
      Studio-Profil und baut die echten Gradio-Blocks samt Callback-Graph auf.
- [x] Experimenteller SCUMM-ZIP-Export aus Gradio mit einer **vorhandenen
      lokalen ScummC-Toolchain**. Validierte Story und spielbare Dateien
      werden in einem ZIP ausgeliefert; der Compiler arbeitet auf einer
      temporären Kopie der Toolchain, um Nutzerdateien nicht zu verändern.
      Deterministischer ZIP-Inhalt und Fehlerfall sind lokal getestet.
- [ ] Compiler-Setup und Plattformfähigkeit für Endnutzer vereinfachen:
      Build-Service oder gekapselte Toolchain, ohne implizite Downloads im
      lokalen Editor und mit getrennten Lizenz-/Versionsgrenzen.
- [x] Erste **gekapselte Codespaces-Toolchain**: gepinntes ScummC wird beim
      erstmaligen Codespaces-Setup separat gebaut. Der Gradio-Editor erhält
      den Pfad automatisch, während sein Export weiterhin ohne neue Downloads
