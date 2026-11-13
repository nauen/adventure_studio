# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-13. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator ohne Zusatzruntime; maßgeblicher Umfang in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** **#232 gemergt (Squash `97d2ae2`); NPC-Komfort endet mit #190.** Zwei unabhängig reversible Tür-/Walkbox-Gates im selben Studio-Spiel, aber in unterschiedlichen Räumen (Harbor/Cellar), vollständig vom Studio-Modell über JSON-v1/Story und produktiven ScummC-v6-Export bis stock ScummVM belegt. **Jetzt Konsolidierung und Priorisierung der noch offenen nativen Lücken; kein paralleles Featurepaket.**
- **Abnahme:** **#232 vollständig abgenommen:** echte Inventar-Use-Aktionen, native Actor-Umwege und Shortcuts für beide Gates, separat exportierte immer-offene Kontrollen; [Gameplay-Evidenz 14017224104](https://github.com/nauen/adventure_studio/actions/runs/43383977443/artifacts/14017224104) und [14022682760](https://github.com/nauen/adventure_studio/actions/runs/43391064553/artifacts/14022682760). Auf finalem Head `d8886e4` sind [native Push 43408629655](https://github.com/nauen/adventure_studio/actions/runs/43408629655), [native PR 43408635264](https://github.com/nauen/adventure_studio/actions/runs/43408635264), Core Push/PR und Dialog-PR erfolgreich; keine offenen Review-Threads. Squash-Merge `97d2ae2`. #230 Save/Load und #231 Raumrückkehr bleiben gesondert belegt.
- **Blocker:** **R09 und R06 weiterhin Teilfähigkeiten:** zwei unabhängig reversible Gates **im selben Raum** und allgemeine dynamische Walkbox-Netze sind noch nicht nativ belegt; ZP05+ bleibt in stock ScummVM v6 inkompatibel und wird beim Export sicher abgelehnt. Der bekannte timingabhängige PNG-Screenshot-Flake bleibt als CI-Stabilitätsrisiko dokumentiert; kein Umgehen von Pflichtgates.
- **Danach:** **Genau eine nächste native R09-Fähigkeit:** zwei unabhängig reversible Tür-/Walkbox-Gates **im selben Raum** im Studio authorieren und Modell/Validierung → JSON-v1/Story → produktiver ScummC-v6-Export → stock ScummVM anhand echter Use-Aktionen, Actor-Umweg/Shortcut und separater Negativkontrollen vollständig nachweisen. Erst nach vollständiger grüner CI und erneuter Konsolidierung ein weiteres Raumgrafik-/Z-Masken-/Walkbox-Paket auswählen. Kein NPC-Komfort.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | Studio/JSON/Story-ZP01 bis ZP04 mit Walkbox-Zuordnung und jeweils getrennter Actor-Verdeckung in stock ScummVM nachgewiesen; PR #198/#204/#208, native Runs `43105298694`, `43251867709`, `43264467363` | ZP05 scheitert in stock ScummVM; ungemergter PR #216 als Negativbefund geschlossen. PR #218 verweigert ZP05+ vor Asset-Erzeugung und erhält Studio-Daten; PR #220 beweist zwei, PR #222 drei verschiedene Masken gleichzeitig über benachbarte Walkboxen und Rückweg; vier gleichzeitig seit #224 nativ mit Rückweg belegt; darüber hinausgehende Kombinationen und ZP05+ bleiben offen |
| P0.3 / R08–R10 – Walkbox/SCAL | `RoomAsset.walkboxes`, BOXM, SCAL, JSON und native Sicht-/Skalierungsprobe; R08.1 konvexe Box und R09 Vier-Boxen-Alternativen, Fünf-Boxen-T-Netz und zyklisches Sechs-Walkbox-Netz mit beiden Ausweichrouten bis stock ScummVM belegt | Allgemeine Polygone, größere/mehrfach dynamische Boxennetze und Perspektivvarianten offen; einmalige Tür-Abkürzung #226, reversibles Gate #229 und natives Save/Load #230 belegt |
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
