# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-12. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne zusätzliche Runtime; maßgeblich bleibt die [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** **R06.4 nativ abgenommen** und [PR #208](https://github.com/nauen/adventure_studio/pull/208) als Squash `a3822677` gemergt. Vier unabhängige Raum-Z-PNG-Masken sind über den bestehenden Studio-/Modell-/JSON-/Story-Pfad und ScummC-ZP01–ZP04 mit BOXD-Index 1–4 nutzbar. Nach der nativen Abnahme jetzt nur Stand konsolidieren und **genau eine** weitere native Raumgrafik-/Walkbox-Lücke vorbereiten; NPC-Komfort bleibt ausgesetzt.
- **Abnahme:** Vier separat importierte Studio-PNGs → RoomAsset/JSON/Story → `ZP01` bis `ZP04` mit passender BOXD-Walkbox-Auswahl → **stock ScummVM**: transparente Kontrolle **1484** sichtbare Actor-Pixel; vier voneinander unabhängige Maskenzustände jeweils **0** sichtbare Actor-Pixel. `four_layers_visually_verified=true`. [Nativer Run 43264467363](https://github.com/nauen/adventure_studio/actions/runs/43264467363) vollständig grün (**98/98 Schritte**), [Core-Run 43264467380](https://github.com/nauen/adventure_studio/actions/runs/43264467380) grün; [Pixelreport und Screenshots](https://github.com/nauen/adventure_studio/actions/runs/43264467363/artifacts/13964179377).
- **Blocker:** Kein offenes R06.4-Pflichtgate. R06 bleibt **Teilfähigkeit**: ZP05–ZP09 und weitere Raum-/Masken-/Walkbox-Konstellationen sind nicht in stock ScummVM nachgewiesen. Offene R07-Mehrzustandsvarianten und komplexere R08/R09-Netze gelten ebenfalls nicht als vollständig; PR #80 (NPC-Mehrzeilen-Dialog) bleibt separat gesperrt.
- **Danach:** **Ein** nächstes natives Produktpaket priorisiert: **R09 – verzweigtes Vier-Walkbox-Netz** aus bereits unterstützten konvexen Boxen, einschließlich eindeutig authorierter BOXM-Next-Hops und realer Actor-Navigation über beide Wege in stock ScummVM. Erst nach eigener Modell→Export→Gameplay-Abnahme und grünen CI als weitere R09-Teilfähigkeit markieren; kein allgemeiner Polygon- oder Auto-Routing-Anspruch.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | Studio/JSON/Story-ZP01 bis ZP04 mit Walkbox-Zuordnung und jeweils getrennter Actor-Verdeckung in stock ScummVM nachgewiesen; PR #198/#204/#208, native Runs `43105298694`, `43251867709`, `43264467363` | Mehr als vier Ebenen und allgemeine Engine-Varianten nicht als vollständig verifiziert behaupten |
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
