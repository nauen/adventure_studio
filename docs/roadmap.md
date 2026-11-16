# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-16. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator ohne Zusatzruntime; die 64-Fähigkeiten-Matrix trennt native Nachweise und offene Lücken.
- **Jetzt:** R06-Kamera #242, R08-Dreiecks-Walkbox #244, R07-IM01/ZP02 #246 und **R07-IM02/ZP02 [#248](https://github.com/nauen/adventure_studio/pull/248)** integriert. Letzteres mit Squash [`6d23500`](https://github.com/nauen/adventure_studio/commit/6d235004b168a71b42f1ce6f4d6715be9a177ce4) abgeschlossen. Jetzt nur CI-Konsolidierung [#249](https://github.com/nauen/adventure_studio/pull/249) abnehmen, keine zweite native Fähigkeit und kein NPC-Komfort.
- **Abnahme:** IM02/ZP02 im geöffneten Objektzustand über echten Studio-PNG-Import, unabhängigen JSON-v1/Story-Roundtrip, produktiven ScummC-Writer bis stock ScummVM bestätigt: maskiert BOXD2 **0** Actor-Pixel, transparente ZP02 **1476**, falscher BOXD1 **1476**. [Gameplay-Artefakt](https://github.com/nauen/adventure_studio/actions/runs/43923787336/artifacts/14256040233). Finaler Head `e377a25`: sieben relevante Workflows grün inklusive [Native Gesamt-CI](https://github.com/nauen/adventure_studio/actions/runs/43930792577); PR #248 gemergt. **R07 als Ganzes bleibt Teilfähigkeit.**
- **Blocker:** Für das einzelne IM02/ZP02-Paket keine offenen Pflichtgates. ZP05+ stock-v6-inkompatibel/fail-closed; zusätzliche Objektbildzustände und Ebenen, allgemeine R08-Polygone sowie komplexere R09-Netze nicht pauschal belegt. CI-Umstellung #249 separat prüfpflichtig.
- **Danach:** Genau eine noch offene native Raumgrafik-/Z-Masken-/Walkbox-Fähigkeit nach Nutzerwert und Evidenzbedarf wählen und erst nach durchgängigem Modell→Studio→JSON/Story→ScummC→stock-ScummVM-Nachweis abnehmen. Keine parallele Produktimplementierung.

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
