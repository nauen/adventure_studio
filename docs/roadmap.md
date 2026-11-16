# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-16. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator ohne Zusatzruntime; maßgeblicher Umfang in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** Nach #190 kein NPC-Komfort; #236/#237/#241 konsolidiert. **Einzig aktiv: [#239](https://github.com/nauen/adventure_studio/issues/239) / [Draft #242](https://github.com/nauen/adventure_studio/pull/242)**: R06 weltfeste ZP01-Verdeckung bei Kamera X=160→480→160. Studio-Editor/Modell, JSON-v1/Story und produktiver ScummC-v6-Export sind verbunden. Der native PR-Gesamtlauf [43741024299](https://github.com/nauen/adventure_studio/actions/runs/43741024299) auf `0318e6e` ist grün; vollständige Freigabe am aktuellen Head bleibt offen.
- **Abnahme:** Die vier Kamera-Phasen samt vollständigem Rückweg wurden auf `0318e6e` im unveränderten ScummVM gemessen: [R06-Artefakt 14179684475](https://github.com/nauen/adventure_studio/actions/runs/43741024299/artifacts/14179684475), drei separat exportierte Spiele (maskiert, transparent, falsche Walkbox), Actor-Welt-X=390, zeitgestempelte Welt-/Kamera-/Bildschirm-X, PNG-Screenshots/Crops, native Ressourcen und Logs. Hinweg X=344, fern X=480, Rückweg X=360 zeigen jeweils 0 maskierte gegenüber je 1540 Kontroll-Actor-Pixeln; Endrückkehr X=160. `native_world_anchored_zp01_pan_and_return_passed=true`. **Gesamt-Abnahme erst bei final grüner Core-/Gradio-/Inventar-/Dialog- und nativer Push-/PR-CI, Diff-/Reviewprüfung und Merge; R06 insgesamt bleibt Teilfähigkeit.**
- **Blocker:** Auf älterem `0318e6e` native PR-CI grün, aber Core und Gradio rot wegen zweier Testfehler (kompaktes kanonisches JSON; importierter Demo-Lauf muss im Editor explizit stationär gestellt werden). [28d2f2d](https://github.com/nauen/adventure_studio/commit/28d2f2de3433f7db597f881ef051d600d86fcea5)/[a3bb351](https://github.com/nauen/adventure_studio/commit/a3bb351abf1f4132137ccc0449fc8301811545ad) korrigieren das ohne geänderte Akzeptanzschwellen; Core Push/PR auf `a3bb351` grün, andere Pflicht-CI noch nicht final bestätigt. Nativer Push-Lauf auf `0318e6e` rot durch alten PNG-Animations-Flake und nachgelagerten Musik-Artefakt-Upload, nicht durch den R06-Nachweis. ZP05+ bleibt stock-v6-gesperrt; R09-Netze über belegte Fälle hinaus offen.
- **Danach:** Nur #239 nach Abschluss aller finalen Push-/PR-Pflichtgates, Diff/Review und Merge konsolidieren; **erst dann** ein weiteres priorisiertes natives Raumgrafik-/Z-Masken-/Walkbox-Paket. Keine parallele Funktion und kein NPC-Komfort.

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
