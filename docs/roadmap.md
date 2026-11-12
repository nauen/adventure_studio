# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-12. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne zusätzliche Runtime; belegter Umfang in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** R08.2 abgeschlossen: [PR #202](https://github.com/nauen/adventure_studio/pull/202), Squash-Merge `58022c5`. Eine dritte Walkbox wird in einem verbundenen Netz zunächst isoliert ergänzt; alte BOXM-Next-Hops bleiben erhalten, die neue Kante wird erst explizit gesetzt. Als **einziges nächstes natives Paket** priorisiert: R08.3 – authorierbare Walkbox-Maskennummer mit begrenztem ZP01/2-Effekt.
- **Abnahme:** Für R08.2 Studio-Modell → JSON/Story → BOXD/BOXM → stock ScummVM verbunden/getrennt nachgewiesen; sechs finale GitHub-Checks auf Head `4bfd0b2` grün (2× Core, 2× Chromium, Dialog und native Gesamtprobe). Für R08.3 zuerst native Maskennummer-Semantik und 0/1/2-Fälle verifizieren, dann Studio → Modell → Export und echte Actor-Verdeckung in unverändertem ScummVM gegenüberstellen.
- **Blocker:** R08.2 hat keinen offenen Blocker. R08.3 ist bislang **nur priorisiert, nicht implementiert**; Walkbox-Maskennummern und allgemeine Polygone sind noch keine bestätigte Studio-Funktion.
- **Danach:** Erst nach vollständiger R08.3-Evidenz und grünen Pflichtgates das nächste einzelne native Raum-/Walkbox-/Z-Masken-Paket nehmen; NPC-Komfort bleibt ausgesetzt.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | Studio/JSON/Story-ZP01/ZP02 mit Walkbox-Zuordnung und getrennter Actor-Verdeckung in stock ScummVM nachgewiesen; PR #198, Merge `0809336c`, Run `43105298694` | Mehr als zwei Ebenen und allgemeine Engine-Varianten nicht als vollständig verifiziert behaupten |
| P0.3 / R08–R10 – Walkbox/SCAL | `RoomAsset.walkboxes`, BOXM, SCAL, JSON und native Sicht-/Skalierungsprobe; R08.1 mit frei authorierter konvexer Box und nativer Laufgrenze belegt | Allgemeine Polygone, Wege-/Boxennetze und Perspektivvarianten offen |
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
