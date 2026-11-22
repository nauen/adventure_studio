# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-22. Die vollständige native Funktionsmatrix steht in
[SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger originaler SCUMM-v6-Adventure-Generator ohne eigene zusätzliche Laufzeit.
- **Jetzt:** **R09 / [Issue #259](https://github.com/nauen/adventure_studio/issues/259), [PR #260](https://github.com/nauen/adventure_studio/pull/260)** – zwei unabhängig reversible BOXD2/3-Gates bleiben nach echter Raumrückkehr getrennt geschaltet. R06 vier weltfeste ZP01–ZP04-Masken bei Kamera X=160→480→160 ist mit [Native/Studio 45022278434](https://github.com/nauen/adventure_studio/actions/runs/45022278434) grün und auf `main` gemergt ([#262](https://github.com/nauen/adventure_studio/pull/262), Squash `128c9ff`). Kein NPC-Komfort seit #190.
- **Abnahme:** Studio/Story → JSON-v1 → produktiver ScummC-v6-Export → stock ScummVM. Beide Schaltfolgen `00→10→11→01→00` und `00→01→11→10→00`, je fünf reale `Tavern→Shed→Tavern`-Rückkehren und separat kompiliertes always-open-Kontrollspiel mit gemessenen BOXD2/3-Flags, Actor-Routen und Screenshot-/Zeitbelegen.
- **Blocker:** [R09 Native 44959056163](https://github.com/nauen/adventure_studio/actions/runs/44959056163) war auf altem R09-Head `e06ad562` erfolgreich. Nach R06-Merge divergiere der Branch; das kombinierte R09-Head bewahrt R06-Kameraabnahme und ergänzt echte Room-Return-Evidenz samt ausreichender Geometry-Laufzeit. Alle aktuellen Core-/Native-/Studio-Pflichtgates müssen erneut grün werden, bevor #260 integriert wird. ZP05+ bleiben stock-v6-fail-closed.
- **Danach:** Genau ein weiteres natives Raumgrafik-/Walkbox-Paket nach der Fähigkeitsmatrix priorisieren. Keine parallele R07/R08- oder NPC-Komfortarbeit.

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
