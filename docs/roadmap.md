# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-12. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne zusätzliche Runtime; aktueller Nachweisumfang steht in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** **R06 – zwei simultane Raum-Z-Masken ZP01/ZP02** aus [PR #220](https://github.com/nauen/adventure_studio/pull/220) nach nativer Abnahme gemergt (`15b55685`). Studio-authorierte getrennte PNG-Masken werden Walkboxen 2/3 zugeordnet und über RoomAsset, JSON/Story, produktiven ScummC/BOXD-Export im selben stock-ScummVM-Spiel wirksam. NPC-Komfort bleibt seit [#190](https://github.com/nauen/adventure_studio/pull/190) beendet.
- **Abnahme:** PR #220 (Squash `15b55685`): [nativer Push-Lauf 43290193684](https://github.com/nauen/adventure_studio/actions/runs/43290193684) und [PR-Retry 43290206567](https://github.com/nauen/adventure_studio/actions/runs/43290206567) jeweils 100/100 Schritte grün auf finalem Head `a4dc8c3`; [Screenshots, vier Studio-JSONs und Pixelreport](https://github.com/nauen/adventure_studio/actions/runs/43290193684/artifacts/13975459593). Walkbox-Masken `[0,1,2]` bleiben bis zum nativen BOXD erhalten. Actor-Pixel Mitte/Ferne/Rückweg: transparent `1440/1528/1128`, nur ZP01 `100/1436/1128`, nur ZP02 `1440/0/24`, **beide aktiv `100/0/24`**; `native_simultaneous_room_masks_passed=true`. Core `43290193837` und `43290206880` grün.
- **Blocker:** R06 bleibt **Teilfähigkeit**: Stock-ScummVM-v6 dekodiert ZP00–ZP04; ZP05+ und Walkbox-Maskenindex >4 werden vom nativen Export weiterhin vor dem Schreiben verweigert ([#218](https://github.com/nauen/adventure_studio/pull/218)). Drei oder vier verschiedene Z-Masken *gleichzeitig* im selben Spiel nicht nachgewiesen; einzelne ZP01–ZP04 sind belegt. Ein unveränderter PNG-Actor-Frame-Test war im ersten PR-Lauf zu #220 instabil; derselbe finale Head bestand im unveränderten Retry. Keine Tests/Schwellen abgeschwächt. NPC-PR #80 weiterhin ausgesetzt.
- **Danach:** Genau **ein** natives Folgepaket: **R06 – drei unterschiedliche gleichzeitig aktive Studio-PNG-Z-Masken ZP01/ZP02/ZP03 auf drei verbundenen Walkboxen in einem exportierten Spiel. Modell/JSON/Story und BOXD-Maskenindizes 1/2/3 erhalten; Actor besucht alle drei Verdeckungsbereiche in einem stock-ScummVM-Spielprozess und läuft zurück. Vergleich mit transparenten beziehungsweise einzeln aktiven Masken; kein ZP05+, kein NPC-Komfort, kein zweites Featurepaket.**

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | Studio/JSON/Story-ZP01 bis ZP04 mit Walkbox-Zuordnung und jeweils getrennter Actor-Verdeckung in stock ScummVM nachgewiesen; PR #198/#204/#208, native Runs `43105298694`, `43251867709`, `43264467363` | ZP05 scheitert in stock ScummVM; ungemergter PR #216 als Negativbefund geschlossen. PR #218 verweigert ZP05+ vor Asset-Erzeugung und erhält Studio-Daten; PR #220 beweist zwei verschiedene Masken gleichzeitig über Walkboxen und Rückweg, drei oder vier gleichzeitig bleiben offen |
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
