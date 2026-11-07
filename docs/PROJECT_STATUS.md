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

**Noch nicht implementiert:** Der allgemeine Action-/Condition-Vertrag,
strukturierte Export-Blocker und Geometrieentkopplung sind geplante
Refactorings, kein bereits abgeschlossener Generatorfortschritt.

## Nächste drei priorisierte Pakete

1. **A0 + P0.1 – Bestehende Modellgrenzen charakterisieren und Binär-Roundtrip-Prüfer für ScummC-Räume.**
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
