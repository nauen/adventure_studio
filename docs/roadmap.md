# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-21. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
historische Checkboxen sind keine aktiven Aufträge.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator ohne Zusatzruntime; die 64-Fähigkeiten-Matrix ist die einzige Funktions- und Statusquelle.
- **Jetzt:** **R06 / Issue #261** – vier simultane Raum-Z-Masken ZP01–ZP04 müssen während einer expliziten horizontalen Kamerafahrt und vollständigem Rückweg weltfest bleiben. Das ist die neue Kombination aus den bereits getrennt bewiesenen Fähigkeiten #224 (vier Masken gleichzeitig) und #242 (weltfeste ZP01-Maske beim Pan).
- **Abnahme:** Reales Studio-Authoring von vier PNG-Masken, fünf Walkboxen/BOXM-Verbindungen und Kamera-Cues; verlustfreier RoomAsset-/JSON-v1-/Story-Roundtrip; produktiver ScummC-v6-Export; unverändertes stock ScummVM. Vier Actor-Weltpositionen (je eine pro Maske) werden in jeweils drei getrennten Spielen geprüft: alle vier Masken aktiv, transparente Kontrolle und gezielte falsche Walkbox-Zuordnung. Pro Spiel Kamera X=160→480→160 mit zeitgestempelten Phasen vor Pan, sichtbarer Hinfahrt, Fernziel, sichtbarem Rückpan und abgeschlossenem Rückweg. Die Pixelvergleiche müssen für jede Maske bei beiden sichtbaren Panrichtungen die korrekte Verdeckung gegen beide Kontrollen beweisen. Projekt-JSONs, PNGs, ScummC-Ressourcen, native Spiele, Screenshots, Logs und Report als CI-Artefakte.
- **Blocker:** Issue #261 ist auf Branch feature/r06-four-mask-camera-pan gestartet; Probe, Unit-Evidenztests, Browser-Authoring-Test und CI-Einbindung sind vorhanden, aber noch nicht auf CI/stock ScummVM ausgeführt. Bis zum nativen Ergebnis bleibt R06 Teilfähigkeit. ZP05–ZP09 bleiben fail-closed. Der separate R09-PR [#260](https://github.com/nauen/adventure_studio/pull/260) ist weiterhin offen; sein kombinierter Zwei-Gate-Raumrückkehrtest läuft in [Run 44959056163](https://github.com/nauen/adventure_studio/actions/runs/44959056163). Dieser offene Integrationslauf verhindert nicht den Start von R06.
- **Danach:** Nach vollständiger R06-Evidenz und Integration genau ein weiteres natives Paket auswählen. Kein NPC-Komfort, keine parallelen R07-/R08-Erweiterungen.
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
