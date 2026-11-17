# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-17. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
historische Checkboxen sind keine aktiven Aufträge.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator ohne Zusatzruntime; die 64-Fähigkeiten-Matrix dokumentiert belegte Teilfähigkeiten und native Lücken.
- **Jetzt:** NPC-Komfort nach [#190](https://github.com/nauen/adventure_studio/pull/190) beendet; CI-Konsolidierung [#252](https://github.com/nauen/adventure_studio/pull/252) gemergt. **IM01/ZP03 [#250](https://github.com/nauen/adventure_studio/issues/250)/[PR #251](https://github.com/nauen/adventure_studio/pull/251) (Squash [`48ea235`](https://github.com/nauen/adventure_studio/commit/48ea23525e4f71b19e25a38ae407d9d86c17a17b)) nativ abgenommen und gemergt.** Kein zweites Produktpaket aktiv; nächste native Lücke erst nach dieser Konsolidierung auswählen.
- **Abnahme:** Finale Core-CI [44181354103](https://github.com/nauen/adventure_studio/actions/runs/44181354103) und vollständige [Studio-/Native-CI 44181364538](https://github.com/nauen/adventure_studio/actions/runs/44181364538) einschließlich vier grüner ScummVM-Shards. Echtes Chrome-PNG-Authoring → RoomHotspot/JSON-v1/Story-Reimport → produktiver ScummC-Export mit IM01 ZP01/ZP02/ZP03 → drei getrennte stock-ScummVM-Spiele: BOXD3 maskiert **0** Actor-Pixel, transparente ZP03 **1556**, falsche BOXD2-Zuordnung **1556**; [Screenshots, Spielressourcen und Report](https://github.com/nauen/adventure_studio/actions/runs/44181364538/artifacts/14372951461), [Studio-Browser-Evidenz](https://github.com/nauen/adventure_studio/actions/runs/44181364538/artifacts/14373241003). `native_im01_zp03_passed: true`.
- **Blocker:** Für das abgegrenzte IM01/ZP03-Paket **keiner**. R07/R08/R09 insgesamt weiterhin Teilfähigkeiten; stock-ScummVM-v6-ZP05+ inkompatibel und fail-closed. IM02/ZP03 noch nicht implementiert/abgenommen.
- **Danach:** Als einzelne nächste native Produktlücke **IM02/ZP03** (dritte unabhängig authorierbare Z-Maske für den zweiten Objektbildzustand) priorisieren: Studio-PNG → optionales Modell-/JSON-v1-/Story-Feld → produktiver IM02-ZP03-ScummC-Export → transparente und falsch zugeordnete stock-ScummVM-Kontrollspiele. Noch **nicht** begonnen; keine NPC-Komfortpakete.

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
