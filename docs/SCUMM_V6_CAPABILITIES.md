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
| A01 | Native Actor-Costume-Ressourcen | A | I (COST + Projekt-JSON/Export) | T | V (Fixture) | Actor-Symbolbindung/Link im Spiel offen |
| A02 | Actor-Platzierung/Richtung/Teleport | A (Teil) | – | – | – | Native Actor-Daten im Modell |
| A03 | Actor-Walk/Pathfinding/Speed | A | I (Demo) | T (Teil) | V (Teil) | Modell + Walkboxen |
| A04 | Stand-/Walk-/Talk-Costume-Frames | A | I (Frames/Richtungen) | T | V (Teil) | Animationssteuerung im Projektmodell |
| A05 | Actor-Skalierung/Z-Clip/Verdeckung | A | – | – | – | R06/R10 + Actor |
| A06 | Costume-`COUNT` und Abfrage | A | I (COST-Cues) | T | V (Fixture) | Allgemeiner Action-/Condition-Export |
| A07 | Aktion während laufender Animation | A (Teil) | – | – | – | Script/Cue + Zähler |
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
| S01 | Native Script-/Objektscript-Lifetime | A | I (Teil) | – | – | Raumwechsel-/Slot-Test |
| S02 | Parallele Scripts/`breakHere`/Wait/Freeze | A | – | – | – | Scheduler-Szenarien |
| S03 | Cutscene-Stack/`begin`/`end` | A | – | – | – | Native Sequenz |
| S04 | Skip-/Override-Endzustand | A | – | – | – | Kontrollfluss/Inventarzustand |
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
| D02 | Verzweigte Gespräche/Antwortoptionen | A (Teil) | I (Demo) | T (Teil) | offen | Native Menüdarstellung |
| D03 | Mehrere Sprecher/Costume-Lippensync | A (Teil) | – | – | – | Actor-/Audio-Koordination |
| D04 | Mehrsprachige Textressourcen | A (Teil) | I (Probe) | T (Teil) | offen | Alle Sprachen im Spiel |
| U01 | MIDI-/Soundresource | A (Teil) | I (Probe) | T | V (Teil) | Spielereignisgesteuert |
| U02 | iMUSE-/Music-State-Übergänge | A (Teil) | I (Plan) | T (Plan) | – | Hook-/Beat-Nachweis |
| U03 | VOC-Sprache und Soundeffekte | A (Teil) | – | – | – | Ressourcen/Timing |
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
