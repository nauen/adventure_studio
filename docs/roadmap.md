# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-12. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne zusätzliche Runtime; belegte Teilfähigkeiten in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** **R09 Vier-Walkbox-Verzweigung** mit [PR #210](https://github.com/nauen/adventure_studio/pull/210) als Squash `7421c384` in `main` gemergt. Zwei unabhängig authorierte BOXM-Netze führen den Actor über 1→2→4 beziehungsweise 1→3→4 zum selben Fernziel; ohne Verbindung bleibt er im Nahbereich. Jetzt den belegten Teilumfang konsolidieren, keinen NPC-Komfort weiterentwickeln.
- **Abnahme:** Studio-`author_room_walkbox` / `author_room_box_connections` → RoomAsset/JSON/Story → nativer BOXD/BOXM-Writer → stock ScummVM: oberer und unterer Weg jeweils Fernziel erreicht (First-Hop 2 beziehungsweise 3), isolierte Kontrolle erreicht Fernziel nicht und zeigt **1612** dunkle Actor-Pixel im Nahbereich. `native_branching_boxm_passed=true`. [Native Run 43268042542](https://github.com/nauen/adventure_studio/actions/runs/43268042542) vollständig erfolgreich (**98/98 Schritte**), [Core 43268042749](https://github.com/nauen/adventure_studio/actions/runs/43268042749) grün; [R09-Screenshots und Projekt-JSONs](https://github.com/nauen/adventure_studio/actions/runs/43268042542/artifacts/13967425948).
- **Blocker:** Für R09-Vier-Boxen-Teilabnahme keiner. Noch **nicht** belegt: zwei gleichzeitig auswählbare Ziele innerhalb eines verzweigten Netzes, größere/zyklische BOXM-Netze, beliebige Walkbox-Polygone sowie die vollständige R06-Abdeckung über ZP04 hinaus. PR #80 bleibt als separater NPC-Mehrzeilen-Blocker ungeklärt.
- **Danach:** Genau **ein** natives Folgepaket: **R09 – Fünf-Walkbox-T-Abzweig mit zwei verschiedenen Laufzielen in einem exportierten Spiel**, beide Ziele über explizite BOXM-Next-Hops erreichbar, ein Ziel bei fehlender Verbindung unerreichbar. Modell → JSON/Story → BOXD/BOXM → reale Actor-Navigation zu beiden Zielen in stock ScummVM; keine Auto-Routing-UI, keine neuen Engine-Primitiven.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | Studio/JSON/Story-ZP01 bis ZP04 mit Walkbox-Zuordnung und jeweils getrennter Actor-Verdeckung in stock ScummVM nachgewiesen; PR #198/#204/#208, native Runs `43105298694`, `43251867709`, `43264467363` | Mehr als vier Ebenen und allgemeine Engine-Varianten nicht als vollständig verifiziert behaupten |
| P0.3 / R08–R10 – Walkbox/SCAL | `RoomAsset.walkboxes`, BOXM, SCAL, JSON und native Sicht-/Skalierungsprobe; R08.1 konvexe Box und R09 zwei alternative Vier-Boxen-Routen bis stock ScummVM belegt | Allgemeine Polygone, Wege-/Boxennetze und Perspektivvarianten offen |
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
