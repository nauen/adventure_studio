# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-13. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne Zusatzruntime; verbindlicher Gesamtumfang in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** **Genau eine aktive R09-Teilfähigkeit in [Draft-PR #231](https://github.com/nauen/adventure_studio/pull/231):** reversibler nativer Tür-Walkbox-Zustand über echten Raumwechsel `Harbor → Cellar → Harbor` und Rückkehr, sowohl geöffnet als auch geschlossen. Bestehendes Studio-Modell `reversible_walkbox` + separat authorierter Passage-Hotspot → JSON/Story → produktiver ScummC-v6-Export. #230 natives Save/Load ist auf `main` integriert (`726e003`); kein NPC-Komfort nach #190.
- **Abnahme:** **#231 noch offen:** Die neue native Probe muss in unverändertem stock ScummVM nach zwei echten Raumwechseln dieselbe offene Abkürzung und denselben geschlossenen Umweg wie vor dem Verlassen messen, gegen ein unabhängig exportiertes immer-offenes Kontrollspiel; echte Inventar-Use-Aktion dazwischen und sichtbarer Türzustand werden geprüft. Core Push/PR auf `a1a71a3` bereits grün; native Push-/PR-CI und Dialog-Pflichtgate laufen. **#230 vollständig abgenommen:** [native CI 43359845966](https://github.com/nauen/adventure_studio/actions/runs/43359845966) 108/108 grün, [Evidenz 14006824948](https://github.com/nauen/adventure_studio/actions/runs/43359845966/artifacts/14006824948).
- **Blocker:** **PR #231 Draft; nativer Raum-Rückkehr-Nachweis und vollständige CI noch ausstehend.** Ohne grüne Gameplay-Evidenz kein Merge. R09 insgesamt bleibt Teilfähigkeit: unabhängige Mehrfach-Gates und allgemein dynamische Netze offen. ZP05+ bleibt im unveränderten stock-ScummVM-v6 gesperrt. Keine Zusatzruntime und kein NPC-Komfort.
- **Danach:** **Erst** nach erfolgreicher echter Raum-Rückkehr-Spielprobe, allen grünen Pflichtgates und Merge von #231 genau **eine** weitere priorisierte R09-/R08-Lücke angehen (z. B. zwei unabhängig geschaltete Gates). Kein paralleles Featurepaket.

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
