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
- **Abnahme:** **#231 native Gameplay-Abnahme bestanden** auf Head `a1a71a3`: echter `Harbor → Cellar → Harbor`-Wechsel für offen und geschlossen, Türzustand, anschließende native Actor-Route und unabhängiges immer-offenes Kontrollspiel; [PR-Gameplay-Artefakt 14009903850](https://github.com/nauen/adventure_studio/actions/runs/43364491391/artifacts/14009903850), [Push-Gameplay-Artefakt 14009957348](https://github.com/nauen/adventure_studio/actions/runs/43364435874/artifacts/14009957348). Core Push/PR und Dialog grün; **native PR-Gesamt-CI 43364491391 vollständig erfolgreich (110/110 Schritte)**, einschließlich Studio-PNG-Animationsprobe. **Native Push-Gesamt-CI 43364435874**: Versuch 1 scheiterte bei der bestehenden PNG-Animationsprobe (`observed=[False, True]`), Versuch 2 läuft; die neue native Raumrückkehr-Probe ist auch im Wiederholungslauf bestanden. Kein Merge vor grüner Push-Gesamt-CI. #230 Save/Load vollständig abgenommen und gemergt.
- **Blocker:** **Nur noch vollständig grüne native Push-Gesamt-CI (Wiederholungslauf) und anschließender Merge von #231 ausstehend; PR-Gesamt-CI bereits grün (110/110).** Stock-ScummVM-Raumrückkehr-Gameplay ist nachgewiesen, aber Gesamt-CI ist noch nicht grün. R09 bleibt eine Teilfähigkeit: unabhängige Mehrfach-Gates und allgemein dynamische Walkbox-Netze offen; ZP05+ in stock ScummVM v6 gesperrt. Kein NPC-Komfort.
- **Danach:** **Erst** wenn beide nativen Gesamtworkflows und alle Pflichtgates erfolgreich sind, #231 mergen und Status/Matrix final konsolidieren. Anschließend genau **eine** nächste priorisierte native R09-Lücke (zwei unabhängige Gates) bearbeiten.

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
