# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-13. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne zusätzliche Runtime; aktueller Nachweisumfang steht in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** **R09 – eine durch eine echte Tür-/Inventar-Use-Aktion dynamisch passierbare native Walkbox** nach [PR #226](https://github.com/nauen/adventure_studio/pull/226), Squash `6f3b4f3e`, gemergt. Studio-Editor verknüpft eine vorhandene Open-State-Tür mit Walkbox 2 → typisierte `UseRule.unlock_walkbox` → Projekt-JSON/Story-Komposition → produktiver ScummC-v6-Export (`setBoxFlags`/`createBoxMatrix`, BOXD/BOXM) → Actor nimmt vor der Türaktion einen Umweg und danach eine Abkürzung in stock ScummVM, erreicht Fernziel und kehrt zurück. Keine zusätzliche Runtime; NPC-Komfort seit #190 beendet.
- **Abnahme:** [#226](https://github.com/nauen/adventure_studio/pull/226) finaler Head `059e2d39`: [nativer PR-Lauf 43343593048](https://github.com/nauen/adventure_studio/actions/runs/43343593048) **106/106 Schritte grün**, [Artifact 14000139036](https://github.com/nauen/adventure_studio/actions/runs/43343593048/artifacts/14000139036) mit zwei unabhängig exportierten Spielvarianten (`door-gated`, `always-open`), Original-ScummVM-Logs, Bildern und Pixelreport `native_r09_door_walkbox_gate_passed=true`. Vor Türöffnung neun echte Actor-Y-Unterschiede von **40 bis 54,5 px** (Umweg), nach Inventar-Use **0 px** (Abkürzung). Engine protokolliert `setBoxFlags(2, 0x80)` → `setBoxFlags(2, 0x00)`; beide Spiele erreichen Fernziel und Rückweg. Core Push/PR `43343585809`/`43343591652`, Gradio `43343591596`, Dialog `43343591683` und Inventar `43343591801` grün; Squash `6f3b4f3e`.
- **Blocker:** **Genau eine Tür-/Walkbox-Kopplung in einem Raum belegt, kein allgemeiner R09-Abschluss.** Zwei unabhängige dynamische Türsperren, Schließen nach Öffnen und native Zustandswiederherstellung bei Save/Load beziehungsweise Raum-Rückkehr sind noch nicht als vollständige Gameplay-Szenarien nachgewiesen. Im nativen Push-Lauf `43343585773` wurde ein älterer, unveränderter PNG-Costume-Frame-Sampling-Flake `[False, True]` beobachtet und unverändert erneut gestartet; der finale native PR-Lauf ist 106/106 grün. **R06-Grenze bleibt**: stock-v6 rendert ZP00–ZP04, ZP05+ wird für nativen Export vor Dateierzeugung abgelehnt (#218).
- **Danach:** **Erst nach der R09-Einzelabnahme genau ein weiteres R09-Paket:** Zwei **unabhängige** Türaktionen steuern zwei unterschiedliche Walkbox-Sperren im selben nativen Raum. Je Tür vor/nach Use die jeweils geänderte Route im unveränderten ScummVM sichtbar belegen und kontrollieren, dass die andere Sperre unabhängig bleibt; Modell → JSON/Story → Export → echte Actor-Wege/Rückweg, mit negativer Kontrolle. Kein NPC-Komfort, keine zusätzliche Runtime, keine Parallelpakete.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | Studio/JSON/Story-ZP01 bis ZP04 mit Walkbox-Zuordnung und jeweils getrennter Actor-Verdeckung in stock ScummVM nachgewiesen; PR #198/#204/#208, native Runs `43105298694`, `43251867709`, `43264467363` | ZP05 scheitert in stock ScummVM; ungemergter PR #216 als Negativbefund geschlossen. PR #218 verweigert ZP05+ vor Asset-Erzeugung und erhält Studio-Daten; PR #220 beweist zwei, PR #222 drei verschiedene Masken gleichzeitig über benachbarte Walkboxen und Rückweg; vier gleichzeitig seit #224 nativ mit Rückweg belegt; darüber hinausgehende Kombinationen und ZP05+ bleiben offen |
| P0.3 / R08–R10 – Walkbox/SCAL | `RoomAsset.walkboxes`, BOXM, SCAL, JSON und native Sicht-/Skalierungsprobe; R08.1 konvexe Box und R09 Vier-/Fünf-/Sechs-Boxen-Netze sowie seit #226 eine echte Tür-Use-Aktion, die native Walkbox 2 sperrt/freigibt und den Actor im selben ScummVM-Spiel zum Umweg beziehungsweise zur Abkürzung bewegt | Allgemeine Polygone/Netze, zwei unabhängige Türsperren, Schließen und Save/Load-Verhalten noch offen |
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
