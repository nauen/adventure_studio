# Adventure Studio – Arbeitsvertrag für Coding-Agenten

Dieses Dokument gilt für Arbeit am Repository `nauen/adventure_studio`.

## Reihenfolge vor jeder Entwicklungsaufgabe

1. `docs/PRODUCT_VISION.md` – unveränderliches Hauptziel.
2. `docs/PROJECT_STATUS.md` – aktueller Projektstand und nächstes Paket.
3. `docs/SCUMM_V6_CAPABILITIES.md` – genaue Funktionsabdeckung.
4. `docs/roadmap.md` – Abhängigkeiten, Phasen, Akzeptanzkriterien.
5. `docs/architecture-contracts.md` und relevante ADRs – Modell-/Exportgrenzen. 
6. Die für das konkrete Thema einschlägigen Source-Audits.

Vor Änderungen außerdem `git status`, aktuelle PRs/CI und die betroffenen
Tests prüfen. Vorhandene Änderungen respektieren; keinen fremden
Worktree-Zustand zurücksetzen.

## Produktgrenze

Erstes Ziel ist ein **vollständiger originaler SCUMM-v6-Generator** für
klassische Adventures im Stil von *Sam & Max* und *Day of the Tentacle*.
Generierte Spiele dürfen **keine eigene Adventure-Studio-Runtime** benötigen.
ScummC und ScummVM sind die maßgeblichen offenen Quellcode-Referenzen.
Original-LucasArts-Interpreter-Kompatibilität nicht ohne eigene
Gegenprobe behaupten.

Die moderne Editoroberfläche darf abstrakte Konzepte (Shot, Nahaufnahme,
Animations-Ereignis) haben, **muss aber** deren native SCUMM-v6-Abbildung
nachweisen. Kein neuer Engine-Befehl ohne Versions-/Bytecode-Beweis.

## Modell- und Exportgrenzen

- Fachlich gültige Stories nicht auf aktuelle Test- oder Layoutgrenzen reduzieren.
  Nicht unterstützte Exporte als konkrete Blocker ausweisen.
- Jede Mengenbegrenzung einer Klasse zuordnen: native Grenze,
  Exporter-, Fixture-, UI-Limit oder begründete Fachregel (ADR-0002).
- Vor Architekturänderungen Characterization-/Kompatibilitätstests
  des bestehenden Modells und der JSON-Versionen einplanen.
- [Architekturaudit](docs/architecture-audit.md) und
  [ADR-0001](docs/adr/0001-domain-and-export-boundaries.md) beachten.

## Wahl des Arbeitspakets

- Das oberste unverblockierte, nutzbare Arbeitspaket aus
  `PROJECT_STATUS.md` priorisieren.
- Technische Schulden nur vorziehen, wenn ein konkreter
  Kompatibilitäts-, Test- oder Entwicklungsblocker vorliegt.
- Kleine vertikale Pakete: validiertes Modell → ScummC-/SCUMM-Export →
  deterministischer Test → Interpreternachweis, soweit erforderlich.
- Keine neue Architekturschicht einführen, bevor der native
  Compiler-/Interpreterpfad untersucht ist.
- Bei unklarer Semantik die entsprechende Primärquelle lesen und
  Unsicherheit ausdrücklich dokumentieren.

## Evidenz- und Statusregeln

Vier Stufen getrennt führen:

1. **Untersucht:** Quellcode-/Formatbefund mit Referenz.
2. **Implementiert:** Im Adventure-Studio-Generator modelliert und ausgegeben.
3. **Getestet:** Automatisierter Test mit eindeutigem Zweck grün.
4. **In ScummVM verifiziert:** Konkretes generiertes Spiel zeigt
   das erwartete Gameplay/Rendering im unveränderten Interpreter.

Der Status „fertig“ ist für spielrelevante Funktionen erst auf Stufe 4
mit erfüllten Akzeptanzkriterien zulässig. Compiler-Erfolg oder
Screenshots anderer Features nicht als Gameplay-Nachweis umetikettieren.

## Workflow

1. Betroffene Dateien, Versionsgrenzen und passende Tests prüfen.
2. Code/Docs gezielt ändern; keine Platzhalter oder stillen Fallbacks.
3. Testen; nicht ausgeführte Tests explizit nennen.
4. Bei erfolgreicher Prüfung selbstständig über GitHub in `main`
   mergen, wenn dies innerhalb der erteilten Projektautorisierung
   möglich ist und keine Schutzregel blockiert.
5. `docs/SCUMM_V6_CAPABILITIES.md`, `docs/PROJECT_STATUS.md` und
   `docs/roadmap.md` **bei tatsächlichem Fortschritt** aktualisieren.
6. Ergebnis, Evidenz, offene Risiken, Merge-Commit und nächstes
   Arbeitspaket knapp melden.

## Dokumentationshygiene

- Produktziel und Status nicht in vielen abweichenden Kopien führen.
- Source-Audits sind Belege; sie sind keine ungeprüften To-do-Listen.
- Keine neuen Einzelanalysen ohne Verlinkung zu einer Capability
  oder einem priorisierten Paket.
- Keine voreiligen `[x]`: Teilnachweise und fehlende Test-Gates
  bleiben sichtbar.
- Die ersten vier Dateien dieses Vertrags sind nach jedem Chat
  der Einstieg, auch wenn Chatverlauf oder Kontext verloren gingen.
