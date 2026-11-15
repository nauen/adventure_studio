# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-15. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator ohne Zusatzruntime; maßgeblicher Umfang in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** Nach #190 kein NPC-Komfort; #236/#237/#241 sind konsolidierte Vorarbeiten. **Einzig aktiv: [#239](https://github.com/nauen/adventure_studio/issues/239) / [Draft #242](https://github.com/nauen/adventure_studio/pull/242)**, R06: weltfeste ZP01-Actor-Verdeckung bei expliziter Kamera X=160→480→160. Studio-Editor und Modell speichern Weltstart, stationären Actor, `set:160;hold:360;pan:480;wait;hold:120;pan:160;wait`, ZP01 und Walkboxen. JSON-v1, Story-Komposition und produktiver ScummC-v6-Export sind implementiert; die neue Runtime-Wirkung ist noch nicht abgenommen.
- **Abnahme:** Für [#239](https://github.com/nauen/adventure_studio/issues/239) explizit authorierter breiter Raum mit ZP01-/Walkbox-Zuordnung und Kamera-Cues `set` → `pan` → `wait` → Rück-Pan/`wait`; verlustfreier RoomAsset-/GameDocument-/JSON-v1-/Story-Roundtrip und produktiver ScummC-v6-Export. Im **unveränderten ScummVM** vor, während, nach dem Pan und auf dem Rückweg Actor-Verdeckung an **Welt-X** anhand dokumentierter Screenshotzeitpunkte, Welt-/Bildschirmkoordinaten und Pixelvergleich gegen separat exportiertes transparentes Kontrollspiel messen. Falsche Walkbox-Maske und bildschirmfeste Fehlverdeckung als Negativfälle; Spiele, Projekt-JSONs, Screenshots, Logs und Report als CI-Artefakt. Relevante Core-/Editor- und native Push-/PR-Gesamt-CI am finalen Code-Head grün, Diff/Reviewthreads geprüft. **Noch nicht abgenommen**; bisherige R09-Evidenz [14119962981](https://github.com/nauen/adventure_studio/actions/runs/43609245425/artifacts/14119962981) gehört ausschließlich zum abgeschlossenen #236.
- **Blocker:** Die drei separat exportierten ScummVM-Spiele (maskiert, transparent, falsche Walkbox) mit beobachteten Kameraphasen, Actor-Crops und vollständiger Rückkehr sind **noch nicht erfolgreich** im stock ScummVM abgenommen. Die fünf aktuellen CI-Workflows des [Draft #242](https://github.com/nauen/adventure_studio/pull/242) waren zuletzt `queued` ([native CI](https://github.com/nauen/adventure_studio/actions/runs/43729819096)); veraltete Head-SHAs und ältere grüne Kamera-/Masken-Einzelproben sind keine Freigabe. Die früher roten Story-Zweitraum- und Dialog-Pflichtgates sind als Bestandsrisiken dokumentiert, nicht zum neuen NPC-Paket umzudeuten. ZP05+ in stock v6 bleibt sicher gesperrt.
- **Danach:** Erst #239 anhand der vier Phasen vor/während/nach Pan und Rückweg gegen separat exportierte transparente Kontrolle vollständig mit stock-ScummVM-Screenshots, Logs, Koordinaten-/Pixelreport und final grüner Gesamt-CI nachweisen, dann R06-Status und Roadmap konsolidieren. **Erst danach** ein weiteres Raumgrafik-/Z-Masken-/Walkbox-Paket. Kein NPC-Komfort, keine parallelen Features.

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
