# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-16. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator ohne Zusatzruntime; die 64-Fähigkeiten-Matrix beschreibt den belastbaren Umfang.
- **Jetzt:** **R08-Dreiecks-Walkbox [#243](https://github.com/nauen/adventure_studio/issues/243)/[PR #244](https://github.com/nauen/adventure_studio/pull/244) nativ abgenommen und auf `main` integriert** (Squash [`363c6c7`](https://github.com/nauen/adventure_studio/commit/363c6c7c604cccfe3129238fdd430efc8232256f)). Nach R06 [#242](https://github.com/nauen/adventure_studio/pull/242) Produktstatus und Funktionsmatrix konsolidiert; **kein** paralleles neues Paket und seit #190 kein NPC-Komfort.
- **Abnahme:** Drei Eckpunkte im echten Studio-Chrome-Editor → JSON-v1/Story-Reimport einschließlich vorhandener BOXM-Wege → produktiver ScummC-v6-BOXD-Export (letzter Dreieckspunkt als viertes Feld wiederholt) → drei separat exportierte Spiele im **unveränderten stock ScummVM**. Breites Dreieck erreicht das Fernziel, enges Dreieck stoppt Ego sichtbar, Rechteck-Kontrolle erreicht das Ziel; [native Push-Artefakt 14233928033](https://github.com/nauen/adventure_studio/actions/runs/43884600266/artifacts/14233928033), [PR-Artefakt 14232414825](https://github.com/nauen/adventure_studio/actions/runs/43884615699/artifacts/14232414825). Auf finalem Head `67af28d`: Core Push/PR, Dialog PR, Gradio PR (unveränderter Retry) sowie native Push-/PR-Gesamt-CI **vollständig grün, je 118/118 Schritte**. Diff-/Reviewprüfung und Merge durchgeführt. **R08 bleibt insgesamt Teilfähigkeit.**
- **Blocker:** Für das abgeschlossene R08-Dreieckspaket **keine offenen Pflichtgates**. Über den belegten Fall hinaus sind beliebige Polygonformen und komplexere/dynamische R08/R09-Netze nicht generell abgenommen; ZP05+ bleibt in stock ScummVM v6 inkompatibel und beim Export gesperrt.
- **Danach:** Zuerst übrige native Raumgrafik-/Z-Masken-/Walkbox-Lücken gezielt priorisieren; danach **genau ein** weiteres Paket vom Modell über Editor/JSON und ScummC bis zu echter stock-ScummVM-Evidenz entwickeln. Keine NPC-Komfortarbeit.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | Studio/JSON/Story-ZP01 bis ZP04 mit Walkbox-Zuordnung und jeweils getrennter Actor-Verdeckung in stock ScummVM nachgewiesen; PR #198/#204/#208, native Runs `43105298694`, `43251867709`, `43264467363` | ZP05 scheitert in stock ScummVM; ungemergter PR #216 als Negativbefund geschlossen. PR #218 verweigert ZP05+ vor Asset-Erzeugung und erhält Studio-Daten; PR #220 beweist zwei, PR #222 drei verschiedene Masken gleichzeitig über benachbarte Walkboxen und Rückweg; vier gleichzeitig seit #224 nativ mit Rückweg belegt; darüber hinausgehende Kombinationen und ZP05+ bleiben offen |
| P0.3 / R08–R10 – Walkbox/SCAL | `RoomAsset.walkboxes`, BOXM, SCAL, JSON und native Sicht-/Skalierungsprobe; R08.1 konvexe Box und R09 Vier-Boxen-Alternativen, Fünf-Boxen-T-Netz und zyklisches Sechs-Walkbox-Netz mit beiden Ausweichrouten bis stock ScummVM belegt | Allgemeine Polygone, größere/mehrfach dynamische Boxennetze und Perspektivvarianten offen; einmalige Tür-Abkürzung #226, reversibles Gate #229, natives Save/Load #230, zwei Räume #232 und zwei unabhängige Gates im selben Raum #236 belegt |
| P0.5 / A01–A07 – Actors/Costumes | COST, Framefolgen, COUNT und viele Gameplay-Teilproben vorhanden | Alle Actor-/Costume-Varianten und native Mehrsprecher-Animation noch nicht fertig |

Diese Teilstände ergeben sich aus
[`scumm_assets.py`](../src/adventure_studio/scumm_assets.py),
[`scumm_project.py`](../src/adventure_studio/scumm_project.py),
[`test_scumm_room_primitives.py`](../tests/test_scumm_room_primitives.py)
und den nativen Szenarien in
[`scummc-experiment.yml`](../.github/workflows/scummc-experiment.yml).
Die [Funktionsmatrix](SCUMM_V6_CAPABILITIES.md) benennt je ID die
unvollständigen Stufen. Ein grüner Fixture-Test ist keine universelle
SCUMM-v6-Abdeckung.

## Verbindliche Produktreihenfolge

1. **P1:** Vollständiger originaler nativer SCUMM-v6-Generator;
   keine zusätzliche Adventure-Studio-Runtime.
2. **P2:** Durchgängiger visueller Editor für die unterstützten nativen Daten.
3. **P3:** Filmischer Shot-/Cutscene-Editor auf belegten nativen Primitiven.
4. **P4:** KI-gestützte und überprüfbare Erstellung.
5. **P5:** Produktreife und Distribution.

## Freigaberegel pro Paket

1. Nutzerverhalten, Capability-ID und 0/1/2/N-Grenzen benennen.
2. Modell → Export → deterministische Tests implementieren.
3. Bei Gameplay die konkrete Wirkung im unveränderten ScummVM prüfen;
   bei Blockade exakt den fehlenden Nachweis nennen.
4. Core-, passende UI- und native CI abnehmen; nur grün und autorisiert mergen.
5. **Nur diese Roadmap, den aktuellen Status und die betroffenen
   Matrixzeilen aktualisieren.** Historische Nachweise bleiben im Archiv.

Ein offenes altes Paket wird nicht stillschweigend als fertig markiert;
eine klar abgegrenzte Teilabnahme ist zulässig, aber nicht dasselbe
wie vollständige native Feature-Unterstützung.
