# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-18. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
historische Checkboxen sind keine aktiven Aufträge.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator ohne Zusatzruntime; die 64-Fähigkeiten-Matrix trennt bestätigte Teilfähigkeiten von offenen nativen Lücken.
- **Jetzt:** **R07 IM01/ZP04 [#255](https://github.com/nauen/adventure_studio/issues/255) / [PR #256](https://github.com/nauen/adventure_studio/pull/256) vollständig nativ abgenommen und gemergt** (Squash [`d834f77`](https://github.com/nauen/adventure_studio/commit/d834f77faab5a31773bbe004ce1be0da9b6eb8a3)); auch IM01/ZP03 [#251](https://github.com/nauen/adventure_studio/pull/251) und IM02/ZP03 [#254](https://github.com/nauen/adventure_studio/pull/254) abgeschlossen. **Kein weiteres Paket begonnen; NPC-Komfort seit [#190](https://github.com/nauen/adventure_studio/pull/190) beendet.**
- **Abnahme:** Echtes Studio-/Chromium-PNG → `RoomHotspot.object_zplane4_pixels` → optionales JSON-v1-/Story-Feld → produktiver ScummC-IM01-Export mit unabhängigen `Z01.bmp`–`Z04.bmp` → drei getrennte stock-ScummVM-Spiele: BOXD4 maskiert **0**, transparente ZP04 **1476**, falsch BOXD3 **1476** sichtbare Actor-Pixel; `native_im01_zp04_passed: true`. [Native Spiel-/Screenshot-/Pixel-Evidenz](https://github.com/nauen/adventure_studio/actions/runs/44208821207/artifacts/14385274768), [echte Browser-Evidenz](https://github.com/nauen/adventure_studio/actions/runs/44208821207/artifacts/14385815321). [Core-CI 44208784590](https://github.com/nauen/adventure_studio/actions/runs/44208784590) und [vollständige Integration 44208821207 (Versuch 2)](https://github.com/nauen/adventure_studio/actions/runs/44208821207) einschließlich aller nativen Shards, Studio, Dialogue und Inventory grün; der initiale unabhängige Palette-Retry-Blocker ist beseitigt.
- **Blocker:** Für IM01/ZP04 **keiner**. R07/R08/R09 insgesamt weiterhin Teilfähigkeiten; stock-v6-ZP05+ inkompatibel und fail-closed.
- **Danach:** **Nach dieser Statuskonsolidierung** exakt eine nächste native Raumgrafik-/Z-Masken-/Walkbox-Lücke aus der 64-Fähigkeiten-Matrix priorisieren; erst dann ein neues Paket starten. Keine NPC-Komfortpakete.

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
