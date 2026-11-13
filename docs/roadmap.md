# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-13. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne zusätzliche Runtime; aktueller Nachweisumfang steht in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** **R09 – Tür schaltet eine native Walkbox-Abkürzung frei**, [PR #226](https://github.com/nauen/adventure_studio/pull/226) gemergt (`6f3b4f3e`). Im bestehenden nativen Studio-Editor eine vorhandene Tür-UseRule mit Walkbox 2 verbinden → `UseRule.unlock_walkbox`/JSON/Story → produktiver ScummC-v6-Export `setBoxFlags([2],128/0)` + `createBoxMatrix()` → stock ScummVM nimmt vor der echten Schlüsselaktion den unteren Umweg, danach die obere Abkürzung und läuft zurück. Keine zusätzliche Runtime; NPC-Komfort seit #190 beendet.
- **Abnahme:** [PR #226](https://github.com/nauen/adventure_studio/pull/226) auf finalem Head `059e2d39`: [Core PR 43343591652](https://github.com/nauen/adventure_studio/actions/runs/43343591652) und [Push 43343585809](https://github.com/nauen/adventure_studio/actions/runs/43343585809) grün; [Gradio/Chrome 43343591596](https://github.com/nauen/adventure_studio/actions/runs/43343591596), [Dialog 43343591683](https://github.com/nauen/adventure_studio/actions/runs/43343591683) und [Inventar 43343591801](https://github.com/nauen/adventure_studio/actions/runs/43343591801) grün; vollständige [native PR-CI 43343593048](https://github.com/nauen/adventure_studio/actions/runs/43343593048) **106/106 Schritte grün**. [Artifact 14000139036](https://github.com/nauen/adventure_studio/actions/runs/43343593048/artifacts/14000139036): zwei echte Studio-Spielvarianten, Screenshots/Logs/JSON. Actor-Y bei initial gesperrter Tür `412/410/410/406/409/403/401/397/397` vs immer offene Kontrollroute `358/359/359/360/359/360/359/360/360.5`; nach Tür-Use beide **360**, Fernziel und Rückweg mit stock-ScummVM-Farbsignatur. Native Logs `setBoxFlags(2, 0x80)` → `setBoxFlags(2, 0x00)`; `native_r09_door_walkbox_gate_passed=true`.
- **Blocker:** **R09 weiterhin Teilfähigkeit:** Das freigeschaltete einmalige Tür-Gate ist nativ belegt, aber dynamisches erneutes Sperren, mehrere unabhängig geschaltete Gates und allgemein veränderte Boxennetze nicht. Die Projektregel verwendet den tatsächlich gespeicherten Türzustand beim Raumeintritt; native Save/Load- und Room-Reentry-Folgeeffekte dieser neuen Option sind nicht gesondert abgenommen. Der native Push-Lauf hatte einen unveränderten PNG-Actor-Screenshot-Fehlschlag im ersten Versuch; der Push-Retry ist noch offen, der vollständige native PR-Lauf ist grün. Frühere ZP05+-Sperre (#218) bleibt unverändert, keine Gate-Lockerung, kein NPC-Komfort.
- **Danach:** Genau **ein** priorisiertes Folgepaket: **R09 – reversibles Tür-Gate schließen und erneut öffnen**: Studio-Autor kann dieselbe Walkbox nach einer zweiten vorhandenen Tür-/Hindernisaktion wieder sperren und danach erneut öffnen; modellierte Türzustände, JSON/Story und native `setBoxFlags`/BOXM aktualisieren die Route in beide Richtungen. Abnahme als ein stock-ScummVM-Spiel mit Actor-Umweg → Abkürzung → erneutem Umweg und Rückweg gegen offene/geschlossene Kontrolle, einschließlich relevanter Save-/Room-Return-Zustände. Kein neues Engine-Skript, keine Zusatz-Runtime, kein NPC-Komfort, kein anderes Paket parallel.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | Studio/JSON/Story-ZP01 bis ZP04 mit Walkbox-Zuordnung und jeweils getrennter Actor-Verdeckung in stock ScummVM nachgewiesen; PR #198/#204/#208, native Runs `43105298694`, `43251867709`, `43264467363` | ZP05 scheitert in stock ScummVM; ungemergter PR #216 als Negativbefund geschlossen. PR #218 verweigert ZP05+ vor Asset-Erzeugung und erhält Studio-Daten; PR #220 beweist zwei, PR #222 drei verschiedene Masken gleichzeitig über benachbarte Walkboxen und Rückweg; vier gleichzeitig seit #224 nativ mit Rückweg belegt; darüber hinausgehende Kombinationen und ZP05+ bleiben offen |
| P0.3 / R08–R10 – Walkbox/SCAL | `RoomAsset.walkboxes`, BOXM, SCAL, JSON und native Sicht-/Skalierungsprobe; R08.1 konvexe Box und R09 Vier-Boxen-Alternativen, Fünf-Boxen-T-Netz und zyklisches Sechs-Walkbox-Netz mit beiden Ausweichrouten bis stock ScummVM belegt | Allgemeine Polygone, größere/mehrfach dynamische Boxennetze und Perspektivvarianten offen; einmaliges Tür-gesteuertes native Abkürzen über #226 belegt |
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
