# Adventure Studio – SCUMM-v6-Funktionsmatrix

Stand: 2026-11-07. **Zentrale Liste der nativen Fähigkeiten, die wir für
typische vollständige SCUMM-v6-Adventures benötigen.** Die Matrix ist
ein fortzuschreibender Katalog und noch kein Anspruch, sämtliche
proprietären Varianten und Sonderfälle vollständig erfasst zu haben.

**Verbindlicher Referenzvertrag:** [SCUMM-v6-Referenzbibliothek](scumm-v6-reference/README.md)
mit [nativen Primitiven](scumm-v6-reference/NATIVE_PRIMITIVES.md),
[Abnahmeszenarien](scumm-v6-reference/SCENARIOS.md) und einem
[maschinenlesbaren Quellenindex](scumm-v6-reference/capability_sources.json).
Diese **Matrix bleibt die einzige Quelle** für Funktions-IDs und
Fortschrittsstatus; die Referenzbibliothek wiederholt sie nicht.
`tests/test_scumm_reference_contract.py` prüft den Quellenindex auf
Vollständigkeit gegenüber den 64 IDs.

## Statusmodell

| Status | Bedeutung |
| --- | --- |
| **A** | Quellcodepfad analysiert; relevante Dokumentation verlinkt |
| **I** | Im allgemeinen Adventure-Studio-Projektmodell **und** Export vorhanden (ggf. begrenzt) |
| **T** | Ein gezielter automatisierter Test existiert und war grün |
| **V** | Funktion im tatsächlich exportierten Spiel in stock ScummVM visuell/interaktiv nachgewiesen |
| **–** | Nicht nachgewiesen oder noch offen; bedeutet nicht, dass der native Opcode fehlt |

Zellen markieren **belegte Teilfähigkeiten**, keine universelle
SCUMM-v6-Abdeckung. `I/T/V (Teil)` bedeutet bewusst eine begrenzte
Implementierung. Für „fertig“ müssen der ausgewiesene Zielumfang und
die konkreten Akzeptanzkriterien nachgewiesen sein. Bestehende
CI-Workflows gelten nicht automatisch als erfolgreiche aktuelle Runs.

Die folgenden Nachweise stammen aus den früheren
[Source-Audits](scumm-v6-source-audit.md),
[Ressourcen-Audits](scumm-v6-export-gap-analysis.md),
dem sichtbaren Projektmodell und der
[bestehenden Roadmap](roadmap.md). Bei Änderungen bitte Links auf
konkrete Tests/Commits ergänzen, nicht nur Statusbuchstaben setzen.

## 1. Räume, Grafiken und Bildkomposition

| ID | Fähigkeit | Analyse | Studio | Test | ScummVM | Nächstes Gate |
| --- | --- | --- | --- | --- | --- | --- |
| R01 | Indizierte Room-Bitmaps/Paletten | A | I | T | V (Teil) | Mehrere Größen/Paletten |
| R02 | SMAP-Strip-Encoding und Ressourcenblöcke | A | I via ScummC | T (Teil) | V (Teil) | Unabhängiger Binär-Roundtrip P0.1 |
| R03 | 8-Pixel-Breitenvalidierung | A | I | T | – | Zu Opcode/Masken-Gates erweitern |
| R04 | Mehrere Räume und Entry-/Exit-Scripts | A | I (Teil) | T | V (Teil) | Script-Lifetime bei Wechsel |
| R05 | Objektbilder mit mehreren States | A | I (Teil) | T | V (Teil) | N Zustände/Parent-States |
| R06 | ZPxx-Masken der Raumgrafik | A | – | – | – | P0.2, sichtbare Actor-Verdeckung |
| R07 | Objektbilder mit Z-Masken | A | – | – | – | Writer/Decoder-Fixture |
| R08 | Walkbox-Polygone und Maskennummern | A (Teil) | – | – | – | P0.3, BOXD-Export |
| R09 | Walkbox-Verbindungen/Wege | A (Teil) | – | – | – | P0.3, BOXM und Laufroute |
| R10 | Perspektive/SCAL und Box-Skalierung | A | – | – | – | P0.3, reale Actor-Skalierung |
| R11 | Actor-zu-Actor-Tiefe / Sam-&-Max-Sortierung | A | – | – | – | Sichtreihenfolge in v6 |
| R12 | Palette-Cycling/Wasser-Effekte | A | I (Teil) | T | V (Teil) | Andere Effektprofile |
| R13 | Raum-/Actor-Paletten, Shadow, Tint | A (Teil) | – | – | – | Native Operationen/Paletten |
| R14 | Raum-Wackeln, Fade und Übergangseffekte | A | – | – | – | Effekt-/Roomwechsel-Fixture |

## 2. Actors, Costumes und Animationen

| ID | Fähigkeit | Analyse | Studio | Test | ScummVM | Nächstes Gate |
| --- | --- | --- | --- | --- | --- | --- |
| A01 | Native Actor-Costume-Ressourcen | A | I (COST + Projekt-JSON/Actor-Bindung; PNG-Import und Actor-Anlage im Studio) | T | V (Fixture und sichtbare Studio-PNG-Frames in ScummVM, CI `42494840322`; Verb-Interaktion offen) | Unabhängigere Actor-Spielbindung und Interaktionsablauf |
| A02 | Actor-Platzierung/Richtung/Teleport | A (Teil) | I (Anfangsposition/Richtung; Actor im selben Raum versetzen und per `face_actor` N/E/S/W drehen) | T | V (Teil: Mehr-Actor-Fixture und erfolgreiches Verb-Klick-Script mit Versetzen/Drehen, CI `42501905023`; Zwischenbilder offen) | Actor-Position und Drehung in ScummVM einzeln visuell nachweisen, freier Spieler-Actor |
| A03 | Actor-Walk/Pathfinding/Speed | A | I (Demo sowie freie `walk_actor`- und `wait_actor`-Interaktionsschritte zu Raumkoordinaten bzw. Ankunft) | T (Teil) | V (Teil: Demo und abgeschlossener Studio-Verbablauf mit Walk/Wait, CI `42501905023`; konkreter Weg/Ankunftspunkt nicht isoliert belegt) | Laufpfad und Ankunfts-Wait des Projekt-Actors visuell nachweisen |
| A04 | Stand-/Walk-/Talk-Costume-Frames | A | I (Frames/Richtungen, Startanimation einschließlich Studio-Auswahl/Deaktivierung, deklarative Verb-Animationen; Studio-PNG-Frames, Mehrframe-COST-Folgen, visuelle Timeline und GIF-Editor-Wiedergabe; Story+Actors speicherbar) | T (Teil) | V (Teil: Erststart, Room-Reentry, sichtbarer Mehrframe-Wechsel aus Studio-PNGs `42494840322` und abgeschlossener Verb-Ablauf `42501905023`; dessen Animationsframes noch nicht isoliert belegt) | Wiederholte Verb-Animation und Zwischenframes im laufenden Spiel prüfen |
| A05 | Actor-Skalierung/Z-Clip/Verdeckung | A | – | – | – | R06/R10 + Actor |
| A06 | Costume-`COUNT` und Abfrage | A | I (COST-Cues) | T | V (Ego- und Projekt-Actor-Fixtures) | Allgemeiner Action-/Condition-Export |
| A07 | Aktion während laufender Animation | A (Teil) | I (COUNT → Objektzustand; deklarative Push/Pull/Open/Close-Eingabegrenze mit zwei Zustandsausgängen) | T (JSON/ScummC + 0/1/2-Klick-, Rückkehr- und Save/Load-Fälle) | V (Teil: Push früh/spät/wiederholt; kein COUNT-Replay beim Room-Reentry oder nach Save/Load) | Mehrfach-Window-Reaktionen, explizite Animations-Neustarts, Save/Load während aktiver Animation und allgemeine Action-/Condition-IR |
| A08 | Mehrere synchronisierte Actors | A (Teil) | – | – | – | Koordinierte Scriptslots |
| A09 | Figur/Objekt-Einstieg, Abfahrt, Reaktion | A (Konzept) | – | – | – | Filmische End-to-End-Sequenz |
| A10 | Actor-Talk-Position/Blase/Portrait | A (Teil) | – | – | – | Text-/Costume-/Talk-Fixture |

## 3. Objekte, Verbsteuerung und Inventar

| ID | Fähigkeit | Analyse | Studio | Test | ScummVM | Nächstes Gate |
| --- | --- | --- | --- | --- | --- | --- |
| O01 | Room-Hotspots und Verbs | A | I (Teil) | T | V (Teil) | Weitere Verben/Profiles |
| O02 | Objekt-Sichtbarkeit/Zustandswechsel | A | I (Teil) | T | V (Teil) | Parent-State-Hierarchie |
| O03 | `drawObjectAt` und bewegte Hitbox | A | – | – | – | Position+Klick gemeinsam |
| O04 | Objekt-Parent/Child/Untouchable | A | – | – | – | OBCD-Attribute, Klicktest |
| O05 | Aufnehmen/Inventory-Owner | A | I (Teil) | T | V (Teil) | Varianten/Grenzen |
| O06 | Use Objekt mit Objekt | A | I (Teil) | T | V (Teil) | Bedingungs-/Script-Regeln |
| O07 | Inventar-Kombinationsrezepte | A (Teil) | I (Teil) | T (Teil) | offen | Prüfen: aktuell grünes Gameplay |
| O08 | Mehrstufige Zustands-/Rätselketten | A | I (Teil) | T | V (Teil) | Generische Zustandsgraphen |
| O09 | Dynamisches Inventar-Layout/Scrollen | A (Teil) | I (Demo) | T (Teil) | offen | Allgemeines Item-Layout |
| O10 | Sam-&-Max-Klickmodell versus Verb-UI | A | – | – | – | Spielprofilspezifische Input-Scripts |

## 4. Scripts, Cutscenes und Kamera

| ID | Fähigkeit | Analyse | Studio | Test | ScummVM | Nächstes Gate |
| --- | --- | --- | --- | --- | --- | --- |
| S01 | Native Script-/Objektscript-Lifetime | A | I (Teil: Studio-Verbfolgen mit Zustandsalternativen und optionalem Escape-Skip) | T (Teil: JSON-/ScummC-Vertrag und Skip-Commit) | V (Teil: drei Klicks desselben Verbs schalten native Objektzustände 1 → 2 → 1 → 2, CI `42506834029`) | Raumwechsel-/Slot-Test und allgemeinere Abbruchfälle |
| S02 | Parallele Scripts/`breakHere`/Wait/Freeze | A | – | – | – | Scheduler-Szenarien |
| S03 | Cutscene-Stack/`begin`/`end` | A | – | – | – | Native Sequenz |
| S04 | Skip-/Override-Endzustand | A | I (Teil: Studio-Verbsequenz mit Objekt-/Actor-/Inventar-/Raum-Endzustand, letztem Musik-Cue und letztem Cue je VOC-Sound-ID) | T (Teil: ScummC-`try`/`override`, JSON-Roundtrip, terminales `startRoom`, Musik- und Sound-Commit) | V (Teil: Escape mit Actor-/Inventareffekt, `Harbor → Cellar → Harbor` und MIDI-Stop/Wiederstart mit PCM-Gate, CI `42517572328`; VOC-Soundstop per PCM-Gate, CI `42522610786`) | Allgemeinere Abbrüche |
| S05 | Kamerasprung `setCameraAt` | A | I (Raum-Cues) | T | V (Raum) | Allgemeiner Shot-/Cutscene-Export |
| S06 | Horizontaler Pan + `waitForCamera` | A | I (Raum-Cues) | T | V (Raum) | Multi-Track-/Cutscene-Synchronisation |
| S07 | Camera-Follows-Actor | A | – | – | – | Follow/Abbruch |
| S08 | Shot: Totale/Nahaufnahme/Schnitt | A (Konzept) | – | – | – | Native Raum-/Bild-Komposition |
| S09 | Parallel laufende Aktionen in Cutscene | A (Teil) | – | – | – | Multi-Track-Export |
| S10 | Interaktion im bewegten Fahrgeschäft | A (Teil) | – | – | – | COUNT/Input/Objekt-Test |

## 5. Dialog, Audio und Persistenz

| ID | Fähigkeit | Analyse | Studio | Test | ScummVM | Nächstes Gate |
| --- | --- | --- | --- | --- | --- | --- |
| D01 | Einfache Textausgabe | A (Teil) | I | T | V (Teil) | Echte NPC-Talk-UI |
| D02 | Verzweigte Gespräche/Antwortoptionen | A (Teil) | I (Teil: mehrstufige NPC-Auswahlgraphen und Rücksprung zu Einstiegsoptionen; VOC-Sprachvarianten auch in späteren Stufen) | T (Teil: JSON-/Editor-/SCUMM-Quelltest, 297 lokal) | V (Teil: native Mehrstufen-/Rückwegprobe mit sichtbar wechselnden Antwortobjekten und sauberem Dialogende, CI `42536777733`; VOC-Dialogprobe CI `42533774527`) | Echte Menü-UI, Sprecherwechsel |
| D03 | Mehrere Sprecher/Costume-Lippensync | A (Teil) | I (Teil: Sprecher pro Dialogzeile, Actor-Blickrichtung und PNG-Sprechpose aus dem Studio; Frames direkt an der nativen Dialogzeile auswählbar und mit einem Klick als Geste gebunden; Schutz vor geteilter Costume; COST-Slots `stand` 12, `talk_start` 16, `talk_stop` 20, Geste 24 und weitere zeilenspezifische Posen und eigenständige, je N/E/S/W editierbare Mehrframe-Sprechfolgen ab 28 ohne Überschreiben bestehender Talk-Frames; `actorSay`/`animateActor`/optionaler Stand-Endzustand; im Costume-Editor je Blickrichtung ein eigener importierter PNG-Frame oder eine native, wiederholte Mehrframe-Sprechfolge für `gesture`/`talk_start` setzbar) | T (Teil: JSON-Roundtrip, zwei native Sprecher, Stand-/Talk-Slot-Validierung, SCUMM-Quelltest, PNG-zu-COST-Dialogpfad sowie zwei unterschiedliche Posen derselben Figur mit stabiler Indexwiederverwendung; Richtungszuweisung und Mehrframe-Sprechfolge mit Erhalt der anderen Richtungen, JSON-Roundtrip und COST-Quellprüfung; eigenständige, wiederbearbeitbare COST-Sequenzen für zwei Zeilen derselben Figur im Modell/SCUMM-Quelltest; richtungsbezogener Erhalt der drei anderen Kanäle und der zweiten Zeile; grafische Zeilen-/Richtungs-Timeline mit Frame-Anhängen, -Verschieben, -Entfernen und GIF-Editorvorschau; pro Dialogzeile einstellbarer nativer Gesture-Vorlauf und Mindestlaufzeit als `delay`-Ticks mit Legacy-Defaults 1/60; optionale Abschluss-COST-Animation nach `waitForMessage` mit positiver Tick-Laufzeit vor der Standpose; eigene Abschluss-PNG-Timeline und direkter PNG-Dateiimport mit Palettenvalidierung für Sprech- und Abschlussfolge je Dialogzeile/Richtung; sichere Copy-on-write-Vereinzelung einer geteilten Costume für den gewählten Sprecher mit Erhalt der anderen Actors; atomarer 1..N-PNG-Stapelimport in Auswahlreihenfolge und Voranzeige nativer Frame-IDs für zeilenspezifische Sprech-/Abschlussfolgen; grafisches Umordnen der Upload-Auswahl vor dem atomaren Stapelimport mit synchroner Vorschau und Zurücksetzen bei Dateiauswahl; gezieltes Ausschließen einzelner hochgeladener PNGs aus der Importauswahl ohne erneuten Upload, mit stabiler Reihenfolge, atomarem COST-Export und Ablehnung leerer Auswahl; Wiederaufnehmen ausgeschlossener, weiterhin hochgeladener PNGs ans Folgenende ohne neuen Upload, inklusive 0-zu-1 und erneuter Bearbeitung) | V (Teil: **sichtbare NPC-Sprechpose und Rückkehr zur Standpose im unveränderten ScummVM nachgewiesen**: 256 rote Gestenpixel statt 0 initial, anschließend 6 aufeinanderfolgende Frames mit 0 Gestenpixeln; GitHub-Commit `1edcf0c5`, Dialog-CI erfolgreich; zusätzlich zwei farblich unterscheidbare Sprechposen derselben Figur im nativen ScummVM-Dialogschritt auf PR #81 erfolgreich; reale automatisierte Chromium-Gradio-Bedienfolge inklusive Projektimport, Pose-Zuweisung, JSON-Export und Reimport erfolgreich, zusätzlich statische PNG-Pose-Vorschau aus nativen Palette-/Frame-Pixeln im Chromium-Browser mit roter und grüner Pixelprüfung nach Zeilenwechsel und Reimport nachgewiesen; menschliche UI-Abnahme offen; zusätzliche native Richtungs-Sprechpose als separates COST-Einzelbild je N/E/S/W im Gradio-Editor mit Pixel- und Richtungsbeschriftungsprüfung umgesetzt, native Dreh-/Sprech-Gameplay mit vier unterschiedlichen Farbframes und sechs stabilen Standframes bestanden (CI `42883775730`, Job `130066624232`, Code-Commit `6902dc7`; außerdem **zwei unterschiedliche Sprechframes innerhalb derselben Dialogzeile** mit Rückkehr zu sechs Standframes in stock ScummVM, CI `42886572422`, Job `130076341678`, Merge `634afb6`; **zwei eigenständige Mehrframe-Zeilen derselben Figur** in stock ScummVM mit anschließendem Standzustand nachgewiesen, Run `42890566896`, Job `130090292878`, Merge `482375e`; Gradio-Chromium-Export/Reimport zweier Zeilensequenzen ebenfalls bestanden; **Richtungskanäle zweier NPC-Zeilen** mit W-rot/grün und E-blau/gelb im stock ScummVM, inklusive Gradio-Chromium-Authoring und JSON-Reimport, bestanden: CI `42895287701`, Job `130106686621`, Merge `270be816`; **grafische Zeilen-/Richtungs-Timeline** mit Anhängen, Verschieben, Entfernen, GIF-Editorvorschau und Export/Reimport im Chromium bestanden (CI `42898953018`, PR #95, Merge `3410035`; **zwei native Sprechphasen pro Dialogzeile** mit 12/90-Tick-W und unveränderter 1/60-Tick-E-Geste im stock ScummVM bestanden, inklusive Chromium-Export/Reimport: CI `42901243477`, Job `130127449346`, Merge `208e619`; **optionale native Abschlussgeste je Zeile** mit magentafarbenem COST-Frame nach W-Rot/Grün und vor E-Blau/Gelb samt Standrückkehr im stock ScummVM und Chromium-Authoring bestanden: Run `42904734152`, Job `130139641706`, Merge `ead868b`; **direkt im Gradio-Dialogeditor erzeugte Abschluss-PNG-Folge** mit eigenem COST-Slot, Chromium-Export/Reimport und magentafarbenem Abschlussframe nach W-Sprechen und vor E-Sprechen im stock ScummVM bestanden: PR #101, Jobs `130151091545` und `130151090189`, Merge `8557ea0`; **direkter PNG-Dateiimport im NPC-Dialogeditor** für Sprech-/Abschlussfolge mit Chromium-Upload/Export/Reimport und nativer Magenta-Abschlussgeste zwischen W-/E-Sprechen und Standrückkehr im stock ScummVM bestanden: PR #103, Jobs `130161049750` / `130161082960` / `130161083496`, Merge `1cc99f7`; **Copy-on-write-Vereinzelung einer geteilten Sprecher-Costume direkt im Dialogeditor** mit Erhalt anderer Actor-Ressourcen, Chromium-PNG-Import/Export und nativer Magenta-Abschlussgeste samt Standrückkehr im stock ScummVM bestanden: PR #105, native Jobs `130167489043` / `130167388424`, Browser `130167488068` / `130167388133`, Merge `1595e1c`; **geordneter 1..N-PNG-Stapelimport direkt im Dialogeditor** mit Dateinamen-/Frame-ID-Vorschau, Chromium-Mehrfachupload/Export und zweiframiger nativer Abschlussanimation vor Ost-Sprechen samt Standrückkehr im stock ScummVM bestanden: PR #107, native Job `130175052358`, Chromium `130175056189` / `130175014763`, Merge `a685897`; **grafische Umsortierung der vorab hochgeladenen PNG-Folge** mit Chromium-Auswahl-/Verschiebeprüfung, geordneter Vorschau und Export/Reimport in zwei UI-Läufen und bestehendem nativen zweiframigem Abschlussdialog samt Standpose im stock ScummVM bestanden: PR #109, Chromium Jobs `130181832614` / `130181718511`, native Jobs `130181832477` / `130181719158`, Merge `e974946`; **einzelne hochgeladene PNGs vor dem nativen Stapelimport gezielt ausgeschlossen** bei stabiler Sortierung: zwei erfolgreiche Chromium-Abläufe mit Drei-Dateien-Auswahl, Ausschluss des dritten Bilds und JSON-Export/Reimport, ein stock-ScummVM-Lauf mit bestehender zweiframiger Abschlussgeste und Standrückkehr bestanden: PR #111, Chromium Jobs `130188492998` / `130188465475`, native Job `130188494313`, Merge `33c28f5`))) | Chromium-/stock-ScummVM-Abnahme der PNG-Wiederaufnahme (CI offen), menschliche Gradio-Abnahme, eigenständiger Sichtnachweis für angehängte dritte Zeile, vollständiger Lippensync |
| D04 | Mehrsprachige Textressourcen | A (Teil) | I (Teil: Story-Katalog und VOC-Untertitel mit gemeinsamem CHAR und `GameLanguage` im nativen Export) | T (Teil: gemeinsamer Export-/Sprachverzweigungs-Test, 293 lokal) | V (Teil: gemeinsames deutsches Objektlabel und VOC-Untertitel mit PCM-Escape in stock ScummVM, CI `42531065406`) | Vollständige Story-Übersetzung, Sprecher-Sprachaufnahmen an Dialogknoten |
| U01 | MIDI-/Soundresource | A (Teil) | I (Teil: Studio-MIDI-Import, SOUN-Export, Raumreferenz) | T (Teil: JSON-/Exporter-Test) | V (Teil: Studio-MIDI als native SOUN mit Stop/Start-PCM-Gate in stock ScummVM, CI `42517572328`) | Weitere Soundformate und allgemeines iMUSE |
| U02 | iMUSE-/Music-State-Übergänge | A (Teil) | I (Plan) | T (Plan) | – | Hook-/Beat-Nachweis |
| U03 | VOC-Sprache und Soundeffekte | A (Teil) | I (Teil: VOC-Import, Unicode-Sprachzeilen, eigene Sprach-VOC-/Untertitel-Varianten sowie VOC-Zuordnung zu NPC-Dialogzeilen und Antworten) | T (Teil: JSON-/Exporter-/Unicode-/Dialog-Audiobindungstests, 295 lokal) | V (Teil: VOC-Effekt CI `42522610786`; ASCII-Sprachzeile CI `42524819678`; Umlaut + VOC-Escape CI `42526681259`; Sprachvariante CI `42528788315`; native NPC-Dialog-Stimme und Antwortauswahl CI `42533774527`) | Actor-Lipsync und vollständige Dialoggraphen |
| P01 | Globale Variablen/Objektzustände | A | I (Teil) | T | V (Teil) | Langzeit-/Room-Scope |
| P02 | Save/Load kompletter Spielzustand | A (Teil) | I (Probe) | T (Teil) | offen | Raum+Inventar+Actors |
| P03 | Spielziel/Quest-Fortschritt | A (Projekt) | I (Teil) | T | V (Teil) | Verschiedene Enden |

## 6. Editor-/Compiler-Qualitäten (nicht VM-Opcodes)

| ID | Fähigkeit | Stand | Nächstes Gate |
| --- | --- | --- | --- |
| E01 | Versioniertes JSON-/Story-Modell | I/T (Teil) | Vollständige SCUMM-Mechaniken |
| E02 | Deterministischer SCUMM-Compiler/Linker | I/T (Teil) | Native Gesamt-Abdeckung |
| E03 | Unabhängiger Ressourcen-Binärparser | Offen | P0.1 |
| E04 | Visueller Raum-/Hotspot-Editor | I/T (Demo) | Masken/Walkbox-UI |
| E05 | Actor-/Costume-Editor | Offen | A01–A08 |
| E06 | Cinematic Shot-/Cutscene-Editor | Offen | S03–S09 |
| E07 | Interaktive ScummVM-Vorschau | Probe | Reproduzierbar im Studio |
| E08 | KI-gestützte, validierte Änderungen | I/T (Teil) | Größere Spielmechaniken |
| E09 | Eigene Spielkennung in stock ScummVM | Offen | Separates Kompatibilitäts-Gate |
| E10 | Original-Interpreter-Kompatibilität | Nicht nachgewiesen | Optionales eigenes Gate |

## Bearbeitungsregeln

1. Jede neue Fähigkeit bekommt eine **stabile ID** und ein Testziel.
2. Analyse-Link ist Pflicht, bevor native Kompatibilität behauptet wird.
3. `I` bezieht sich auf **allgemeinen Export**, nicht nur hartkodierte
   Fixture- oder Probe-Module; solche Ausnahmen als „Demo/Probe“ markieren.
4. Für `V` konkrete CI-Run-/Screenshot-/Interaktionsbelege angeben.
5. Nach jedem Arbeitspaket nur die **tatsächlich geänderten** Zeilen
   aktualisieren und den neuen Status in `PROJECT_STATUS.md` spiegeln.
6. Offene Mechaniken anhand der Quellcodebefunde priorisieren,
   nicht anhand der Anzahl früherer grüner Workflows.

Die konkrete Implementierungsreihenfolge für die nächsten Arbeitspakete
steht in [PROJECT_STATUS.md](PROJECT_STATUS.md).
