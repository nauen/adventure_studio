# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-12. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne zusätzliche Runtime; belegter Umfang in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** R06.3 mit [PR #204](https://github.com/nauen/adventure_studio/pull/204) **gemergt** (Squash `c78d817`); nativen Room-/Walkbox-/Z-Masken-Stand konsolidieren und **genau eine** nächste Lücke anhand der Capability-Matrix eingrenzen, ohne sie vor der Konsolidierung zu implementieren. R08.2 wurde in PR #202 und die frühere Konsolidierung in PR #203 gemergt.
- **Abnahme:** Drei separat authorierte PNG-Z-Masken → RoomAsset/JSON/Story → ZP01/ZP02/ZP03 mit BOXD-Index 1/2/3 → unverändertes ScummVM: jede verdeckt unabhängig Actor-Pixel, transparenter Kontrollfall nicht. Vier finale Pflichtchecks auf PR-Head `90ec4b0` grün (Core 2×, native 2×), native Runs [43251867709](https://github.com/nauen/adventure_studio/actions/runs/43251867709) und [43251882252](https://github.com/nauen/adventure_studio/actions/runs/43251882252). PNG-Costume-Regression ebenfalls in beiden nativen Läufen grün. **Nur drei Ebenen verifiziert**, keine allgemeine ZPxx-Zusage.
- **Blocker:** Für R06.3 keiner; die verifizierte Teilfähigkeit ist integriert. Für weitere Ebenen, allgemeine Boxnetze und Objektzustands-Z-Masken fehlt eine jeweils eigene native Gegenprobe. Vor neuer Implementierung zuerst eine begrenzte Fähigkeit auswählen.
- **Danach:** Einzelne native Lücke priorisieren (Kandidat: R07, Objektbild-Z-Maske für einen weiteren Bildzustand; Alternativen R06 weitere Ebene oder R08/R09 komplexere Boxnetze). Erst anschließend **ein** Paket Modell → Export → stock ScummVM → grüne CI; keine NPC-Komfortarbeit.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | Studio/JSON/Story-ZP01/ZP02/ZP03 mit Walkbox-Zuordnung und getrennter Actor-Verdeckung in stock ScummVM nachgewiesen; PR #198 und PR #204, Merge `0809336c` / `c78d817`, Runs `43105298694`, `43251867709`, `43251882252` | Mehr als drei Ebenen und allgemeine Engine-Varianten nicht als vollständig verifiziert behaupten |
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
