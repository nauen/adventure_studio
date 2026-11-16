# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-16. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator ohne Zusatzruntime; die [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md) beschreibt nachgewiesene Teilumfänge und native Lücken.
- **Jetzt:** Nach R06 [#242](https://github.com/nauen/adventure_studio/pull/242), R08-Dreiecks-Walkbox [#244](https://github.com/nauen/adventure_studio/pull/244) und **R07-Objekt-IM01/ZP02 [#245](https://github.com/nauen/adventure_studio/issues/245)/[#246](https://github.com/nauen/adventure_studio/pull/246)** (Squash [`7b38872`](https://github.com/nauen/adventure_studio/commit/7b3887210c5df52e71062bc4e1c0eab5e4fcccbc)) den Stand konsolidiert. **Kein neues aktives Featurepaket**; seit #190 kein NPC-Komfort.
- **Abnahme:** R07-IM01/ZP02 über echtes Studio-Chrome-Authoring und JSON-v1/Story-Reimport mit erhaltener IM01/ZP01 und IM02/ZP01 → produktiver ScummC-v6-IM01-Writer mit separaten ZP01-/ZP02-BMPs → drei unabhängig exportierte Spiele im **unveränderten stock ScummVM**: Maskierung 0 Actor-Pixel bei BOXD-Index 2; transparente ZP02 und falscher BOXD-Index je 1476 sichtbare Actor-Pixel. [Native PR-Run](https://github.com/nauen/adventure_studio/actions/runs/43906300863), [native Screenshots und Spiel-Binärdateien](https://github.com/nauen/adventure_studio/actions/runs/43906300863/artifacts/14244672820); auf finalem Head `fb83a41` Core Push/PR, Gradio Push/PR, Inventar PR, Dialog PR nach unverändertem Retry und volle native PR-CI **118/118 grün**. Review/Diff geprüft, Merge abgeschlossen. **R07 insgesamt bleibt Teilfähigkeit.**
- **Blocker:** Für das konkrete R07-IM01/ZP02-Paket **keine offenen Pflichtgates**. Stock-ScummVM-v6-ZP05+ bleibt inkompatibel und beim nativen Export gesperrt; weitere Objektbildzustände und zusätzliche Maskenebenen je Zustand, allgemeine R08-Polygone und komplexe R09-Netze sind nicht pauschal belegt.
- **Danach:** Die verbleibenden nativen Raumgrafik-/Z-Masken-/Walkbox-Lücken zuerst nach Nutzerwert und fehlendem Runtime-Beleg priorisieren; anschließend **genau ein** neues Modell→Studio→JSON/Story→ScummC→stock-ScummVM-Paket. Keine parallele Implementierung und kein NPC-Komfort.

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
