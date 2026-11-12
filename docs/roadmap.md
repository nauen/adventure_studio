# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-12. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne zusätzliche Runtime; aktueller Nachweisumfang steht in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** **R06 – drei unabhängige simultane Raum-Z-Masken ZP01/ZP02/ZP03** aus [PR #222](https://github.com/nauen/adventure_studio/pull/222), Squash `f50acd6c`, in `main`. Studio-PNG-Import → RoomAsset/JSON/Story → produktive ScummC-Quellen/BOXD-Masken `[0,1,2,3]` → **ein** stock-ScummVM-Spielprozess mit drei selektiven Actor-Verdeckungen und nativem Rückweg. NPC-Komfort seit [#190](https://github.com/nauen/adventure_studio/pull/190) beendet.
- **Abnahme:** [PR #222](https://github.com/nauen/adventure_studio/pull/222): Core Push [43328218021](https://github.com/nauen/adventure_studio/actions/runs/43328218021) und PR [43328228946](https://github.com/nauen/adventure_studio/actions/runs/43328228946) grün; vollständiger [nativer PR-Lauf 43328228844](https://github.com/nauen/adventure_studio/actions/runs/43328228844) auf finalem Head `db988226` **102/102 Schritte grün**. [Artifact 13993702524](https://github.com/nauen/adventure_studio/actions/runs/43328228844/artifacts/13993702524): fünf separat gelinkte Spiele, authentische ScummVM-Screenshots, Studio-JSONs und Pixelreport. ZP01 allein verdeckt Walkbox 2 `1516→0` Actor-Pixel, ZP02 allein Walkbox 3 `1552→100`, ZP03 allein Walkbox 4 `1664→108`; **alle drei aktiv** `0/100/108` in den drei Bereichen, Rückweg `100/0` gegenüber transparent `1332/1416`. `native_simultaneous_three_room_masks_passed=true`.
- **Blocker:** R06 weiterhin **Teilfähigkeit**: In stock ScummVM v6 werden nur ZP00–ZP04 dekodiert; ZP05+ sowie Walkbox-Maskenindex >4 verweigert der native Export vor dem Schreiben ([#218](https://github.com/nauen/adventure_studio/pull/218)). Vier unterschiedliche Z-Masken **gleichzeitig** im selben Spiel nicht belegt; einzelne ZP01–04 und drei simultane ZP01–03 dagegen nativ belegt. #222 hatte zunächst rote Gameplay-Proben durch unpassende Walkbox-/Klick- und Screenshot-Positionen; nach Korrektur der authored Geometrie/Zielpunkte/Messfläche bestanden die unveränderten Selektivitäts-Schwellen. Ältere PNG-Frame-/Screenshot-Fluktuationen bleiben beobachtungsbedürftig; kein Gate abgebaut, NPC-PR #80 ausgesetzt.
- **Danach:** Genau **ein** priorisiertes Folgepaket: **R06 – vier unabhängig Studio-authorierte ZP01/ZP02/ZP03/ZP04 gleichzeitig in vier benachbarten Walkboxen eines exportierten SCUMM-v6-Spiels.** Über RoomAsset/JSON/Story → produktiven ScummC-/BOXD-Export (Maskenindizes 1/2/3/4) bis stock ScummVM prüfen: Actor besucht alle vier Bereiche, läuft zurück und die vier Z-Masken verdecken jeweils selektiv gegenüber transparenten und einzeln opaken Kontrollspielen. Kein ZP05+, kein neuer Runtime-Code, keine NPC-Komfortarbeit, kein weiteres Paket parallel.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | Studio/JSON/Story-ZP01 bis ZP04 mit Walkbox-Zuordnung und jeweils getrennter Actor-Verdeckung in stock ScummVM nachgewiesen; PR #198/#204/#208, native Runs `43105298694`, `43251867709`, `43264467363` | ZP05 scheitert in stock ScummVM; ungemergter PR #216 als Negativbefund geschlossen. PR #218 verweigert ZP05+ vor Asset-Erzeugung und erhält Studio-Daten; PR #220 beweist zwei, PR #222 drei verschiedene Masken gleichzeitig über benachbarte Walkboxen und Rückweg; vier gleichzeitig bleiben offen |
| P0.3 / R08–R10 – Walkbox/SCAL | `RoomAsset.walkboxes`, BOXM, SCAL, JSON und native Sicht-/Skalierungsprobe; R08.1 konvexe Box und R09 Vier-Boxen-Alternativen, Fünf-Boxen-T-Netz und zyklisches Sechs-Walkbox-Netz mit beiden Ausweichrouten bis stock ScummVM belegt | Allgemeine Polygone, Wege-/Boxennetze und Perspektivvarianten offen |
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
