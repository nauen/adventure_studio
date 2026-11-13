# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-13. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne zusätzliche Runtime; aktueller Nachweisumfang steht in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** **R06 – vier unabhängig Studio-authorierte PNG-Z-Masken ZP01–ZP04 gleichzeitig** in verbundenen Walkboxen 2–5 des **selben stock-ScummVM-v6-Spiels** nach [PR #224](https://github.com/nauen/adventure_studio/pull/224) gemergt (`d99c7a79`). Studio-Modell → RoomAsset/JSON/Story → produktive ScummC-ZP01–ZP04/BOXD-Masken `[0,1,2,3,4]` → Actor-Navigation zu vier Maskenbereichen und Rückweg. NPC-Komfort seit #190 beendet.
- **Abnahme:** [PR #224](https://github.com/nauen/adventure_studio/pull/224) finaler Head `4590d046`: [Core Push 43335928391](https://github.com/nauen/adventure_studio/actions/runs/43335928391) und [Core PR 43335934134](https://github.com/nauen/adventure_studio/actions/runs/43335934134) grün; vollständiger [nativer Push 43335928210](https://github.com/nauen/adventure_studio/actions/runs/43335928210) und [nativer PR 43335934414](https://github.com/nauen/adventure_studio/actions/runs/43335934414) **je 104/104 Schritte grün**. [Artifact 13997602214](https://github.com/nauen/adventure_studio/actions/runs/43335934414/artifacts/13997602214) enthält sechs getrennt exportierte Spiele, Studio-JSONs, ScummVM-Screenshots und Pixelreport. Actor-Pixel Box2/3/4/5 transparent `1616/1332/1516/1300`, mit allen vier Masken **`100/100/100/100`**; ZP01–ZP04 allein verdecken jeweils *nur* ihren Bereich. Rückweg Box4/5 transparent `1572/1300`, alle aktiv **`100/100`**, nur zugehörige ZP03/ZP04 `100/100` an ihrer jeweiligen Stelle. `native_simultaneous_four_room_masks_passed=true`.
- **Blocker:** **R06 als stock-v6-kompatibler Vier-Masken-Nachweis erfüllt, größere allgemeine R06-Varianten bleiben offen.** Stock-ScummVM-v6 `Gdi::getZPlanes()` dekodiert ZP00–ZP04; ZP05+ oder BOXD-Maskenindex >4 werden im nativen Export nach [#218](https://github.com/nauen/adventure_studio/pull/218) **vor** Schreiben der Dateien abgelehnt, ohne Projekt-/JSON-Daten zu verlieren. #224 erste zwei native Versuche rot wegen Kamera-/Klickkoordinaten; der letzte zielgerichtete Rückweg-Fix (`x=460`) besteht ohne Lockerung von Selektivität oder Gates. Ältere Screenshot-Timing-Fluktuationen bleiben dokumentiert; NPC-PR #80 weiterhin ausgesetzt.
- **Danach:** Genau **ein** priorisiertes Paket: **R09 – Walkbox-Passierbarkeit abhängig von einer Tür-/Hindernis-Aktion im selben Raum**: Autor legt zwei alternative native Wege um eine zunächst gesperrte Walkbox fest; vor Öffnen führt ScummVM den Actor über den freien BOXM-Weg, nach einer im Studio authorierten Tür-Aktion darf die Abkürzung genutzt werden, einschließlich Rückweg. Zuerst nativen SCUMM-v6-Befehl und ScummC-Abbildung für Walkbox-Flags/Verbindungen anhand vorhandener Referenz prüfen; nur bei tragfähigem nativem Vertrag Modell/JSON/Story → Export → stock-ScummVM-Spieltest implementieren. Kein NPC-Komfort, keine zusätzliche Runtime, kein paralleles Featurepaket.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | Studio/JSON/Story-ZP01 bis ZP04 mit Walkbox-Zuordnung und jeweils getrennter Actor-Verdeckung in stock ScummVM nachgewiesen; PR #198/#204/#208, native Runs `43105298694`, `43251867709`, `43264467363` | ZP05 scheitert in stock ScummVM; ungemergter PR #216 als Negativbefund geschlossen. PR #218 verweigert ZP05+ vor Asset-Erzeugung und erhält Studio-Daten; PR #220 beweist zwei, PR #222 drei verschiedene Masken gleichzeitig über benachbarte Walkboxen und Rückweg; vier gleichzeitig seit #224 nativ mit Rückweg belegt; darüber hinausgehende Kombinationen und ZP05+ bleiben offen |
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
