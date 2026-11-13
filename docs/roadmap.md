# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-13. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne Zusatzruntime; verbindlicher Gesamtumfang in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** **#231 ist per Squash `8840a22` auf `main` integriert.** Die native R09-Raumrückkehr eines reversiblen Tür-Walkbox-Gates ist abgeschlossen: Studio-Modell `reversible_walkbox` und Passage-Hotspot → JSON-v1/Story → produktiver ScummC-v6-Export → Stock-ScummVM. **Jetzt Konsolidierung und native R09-Lückenpriorisierung; noch kein zweites Featurepaket.** NPC-Komfort bleibt nach #190 beendet.
- **Abnahme:** **#231 vollständig abgenommen und gemergt:** echter `Harbor → Cellar → Harbor`-Wechsel mit offenem und geschlossenem Gate, echte Use-Aktionen, native Actor-Abkürzung/Umweg gegen unabhängige immer-offene Kontrollspiele. [PR-Gameplay-Artefakt 14009903850](https://github.com/nauen/adventure_studio/actions/runs/43364491391/artifacts/14009903850), [Push-Gameplay-Artefakt 14009957348](https://github.com/nauen/adventure_studio/actions/runs/43364435874/artifacts/14009957348). [Native PR-Gesamt-CI 43364491391](https://github.com/nauen/adventure_studio/actions/runs/43364491391) **110/110 erfolgreich** und [native Push-Gesamt-CI 43364435874](https://github.com/nauen/adventure_studio/actions/runs/43364435874) **im zweiten Versuch 110/110 erfolgreich**, inklusive unveränderter Studio-PNG-Animationsprobe; Core Push/PR und Dialog ebenfalls grün. Squash `8840a22`. #230 Save/Load bereits als `726e003` integriert.
- **Blocker:** **Kein offenes CI- oder Merge-Gate für #231.** R09 bleibt bewusst **Teilfähigkeit**: zwei unabhängige dynamische Gate-Zustände und allgemein dynamische Walkbox-Netze sind nicht nativ nachgewiesen; Stock-ScummVM-v6-ZP05+ bleibt inkompatibel. Kein NPC-Komfort.
- **Danach:** **Ein einziges nächstes natives R09-Paket priorisieren:** zwei unabhängig schaltbare Tür-/Walkbox-Gates im selben Spiel, mit echtem Studio-Modell → JSON/Story → ScummC-v6-Export → unverändertem ScummVM und separaten Actor-Routen-/Negativkontrollen. Erst nach Implementierung, nativer Evidenz und vollständig grüner CI das darauffolgende Paket beginnen.

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
