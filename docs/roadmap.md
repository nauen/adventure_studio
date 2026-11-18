# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-18. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
historische Checkboxen sind keine aktiven Aufträge.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator ohne Zusatzruntime; die 64-Fähigkeiten-Matrix bleibt die einzige Funktions- und Statusquelle.
- **Jetzt:** **R07 IM02/ZP04 abgeschlossen und auf `main` gemergt**: [PR #258](https://github.com/nauen/adventure_studio/pull/258), Squash [`7527b8d`](https://github.com/nauen/adventure_studio/commit/7527b8d06662de15450b2ab581d5688f74b9b9c8). Nächste Priorität ist **R09: zwei unabhängig reversible Walkbox-Gates im selben Raum über einen echten Raumwechsel hinweg erhalten**; noch nicht implementiert oder abgenommen. NPC-Komfort seit [#190](https://github.com/nauen/adventure_studio/pull/190) beendet.
- **Abnahme:** IM02/ZP04: echtes Studio-/Chromium-PNG → `RoomHotspot.open_object_zplane4_pixels` → JSON-v1/Story → produktiver ScummC-IM02-Writer (`OpenZ01.bmp`–`OpenZ04.bmp`) → **drei** unveränderte stock-ScummVM-Spiele. BOXD4 **0**, transparente ZP04 **1476**, falsche BOXD3 **1476** Actor-Pixel; `native_im02_zp04_passed: true`. [Native Evidenz](https://github.com/nauen/adventure_studio/actions/runs/44218026305/artifacts/14388748875) · [Browser-Evidenz](https://github.com/nauen/adventure_studio/actions/runs/44218026305/artifacts/14388114712) · [Core 44217985572](https://github.com/nauen/adventure_studio/actions/runs/44217985572) · [vollständige Integration 44218026305](https://github.com/nauen/adventure_studio/actions/runs/44218026305): Studio, Dialogue, Inventory, 4/4 native Shards erfolgreich auf finalem Head `f0c990de`.
- **Blocker:** Für #258 keiner. Für das **nächste** R09-Paket fehlt noch die vertikale Implementierung und eigenständige ScummVM-Evidenz für zwei unabhängig geschaltete Gates mit Raumverlassen/-wiederkehr; bisherige #231-Raumrückkehr betrifft nur ein Gate, #236 zwei Gates ohne diesen kombinierten Rückkehrnachweis. R07/R08/R09 bleiben insgesamt Teilfähigkeiten; stock-v6-ZP05+ bleibt fail-closed.
- **Danach:** Erst das eine priorisierte R09-Raumrückkehrpaket Modell → Studio/JSON/Story → nativer ScummC → echte Actor-Routen und Kontrollspiel in stock ScummVM vollständig abnehmen, dann **ein** weiteres Paket wählen. Keine parallelen Features.


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
