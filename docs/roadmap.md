# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-13. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne Zusatzruntime; verbindlicher Umfang in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** Genau **ein** R09-Paket in [PR #232](https://github.com/nauen/adventure_studio/pull/232): zwei unabhängige reversible native Tür-/Walkbox-Gates in Harbor und Cellar **desselben** Studio-Spiels. JSON-v1/Story/ScummC-Export und echtes Stock-ScummVM-Gameplay belegt; NPC-Komfort nach #190 beendet.
- **Abnahme:** Zwei unabhängige native Tür-Use-Aktionen und Actor-Umweg/Abkürzung in Harbor und Cellar desselben Studio-Spiels gegen ein separat exportiertes immer-offenes Kontrollspiel sind über Modell → JSON-v1/Story → ScummC-v6 → unverändertes Stock-ScummVM belegt: [Gameplay-Evidenz 14017224104](https://github.com/nauen/adventure_studio/actions/runs/43383977443/artifacts/14017224104). Auf Head `1cbebcd6` sind Core Push/PR grün, Dialog-PR **43/43 grün** und die [native Push-Gesamt-CI 43383977443](https://github.com/nauen/adventure_studio/actions/runs/43383977443) **112/112 grün**, einschließlich Save/Load, echter Raumrückkehr, korrigiertem Story-Übergang nach Cellar und [PNG-Animationsbeweis 14019755579](https://github.com/nauen/adventure_studio/actions/runs/43383977443/artifacts/14019755579). Die native PR-Gesamt-CI ist noch nicht abgenommen.
- **Blocker:** Die [native PR-CI 43383983753](https://github.com/nauen/adventure_studio/actions/runs/43383983753) scheiterte im ersten Versuch an der bestehenden zeitabhängigen PNG-Animations-Screenshotprobe (`observed=[False, True]` bei 23 Samples), obwohl dieselbe Probe im Push-Lauf erfolgreich war; der fehlgeschlagene Job läuft auf unverändertem Head erneut. Der vorherige sechste Save/Load-Kamera-Sample-Fehler ist behoben, nicht mehr aktueller Blocker. Nach einem Dokumentations-Commit sind alle Pflicht-CI-Prüfungen auf dem neuen Head erneut abzunehmen; kein Merge und kein Folgepaket ohne vollständige grüne Core-, Dialog- und native Push-/PR-CI.
- **Danach:** Erst nach konsistent dokumentiertem R09-Nachweis, vollständig grüner CI auf dem endgültigen Head und Squash-Merge von #232 **genau eine** nächste offene R09-/R06-Raumgrafik-/Z-Masken-/Walkbox-Fähigkeit priorisieren. Mehrere dynamische Gates im selben Raum, allgemeine dynamische Boxennetze und ZP05+ sind durch R09 nicht belegt; NPC-Komfort bleibt nach #190 beendet.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | Studio/JSON/Story-ZP01 bis ZP04 mit Walkbox-Zuordnung und jeweils getrennter Actor-Verdeckung in stock ScummVM nachgewiesen; PR #198/#204/#208, native Runs `43105298694`, `43251867709`, `43264467363` | ZP05 scheitert in stock ScummVM; ungemergter PR #216 als Negativbefund geschlossen. PR #218 verweigert ZP05+ vor Asset-Erzeugung und erhält Studio-Daten; PR #220 beweist zwei, PR #222 drei verschiedene Masken gleichzeitig über benachbarte Walkboxen und Rückweg; vier gleichzeitig seit #224 nativ mit Rückweg belegt; darüber hinausgehende Kombinationen und ZP05+ bleiben offen |
| P0.3 / R08–R10 – Walkbox/SCAL | `RoomAsset.walkboxes`, BOXM, SCAL, JSON und native Sicht-/Skalierungsprobe; R08.1 konvexe Box und R09 Vier-Boxen-Alternativen, Fünf-Boxen-T-Netz und zyklisches Sechs-Walkbox-Netz mit beiden Ausweichrouten bis stock ScummVM belegt | Allgemeine Polygone, größere/mehrfach dynamische Boxennetze und Perspektivvarianten offen; einmalige Tür-Abkürzung #226, reversibles Gate #229 und natives Save/Load #230 belegt |
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
