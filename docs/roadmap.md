# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-16. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator ohne Zusatzruntime; maßgeblicher Umfang in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** **R06-Kamerafahrt/ZP01 mit [PR #242](https://github.com/nauen/adventure_studio/pull/242) abgeschlossen und auf `main` integriert** (Squash [`9676b0e`](https://github.com/nauen/adventure_studio/commit/9676b0e7760c2b31eaa72d5553bbd703cd3a07df)). Nach #190 keine NPC-Komfortarbeit. Konsolidierung dieses einen Pakets vor der nächsten Implementierung; priorisierte Restlücken Raumgrafik/Z-Masken/Walkboxen.
- **Abnahme:** Studio-Kamerafolge + Ego-Weltstart → JSON-v1/Story → produktiver ScummC-v6-Export → drei getrennt gebaute Spiele im **unveränderten ScummVM**. Kamera X=160→480→160 und Actor-Welt-X=390, ZP01-verdeckt während Hinweg/Fernziel/Rückweg je 0 Actor-Pixel gegen je 1540 in transparenter/falscher-BOXD-Kontrolle; zeitgestempelte Frames, PNG-Crops, Spiele/Logs. [Native Push 43861486561](https://github.com/nauen/adventure_studio/actions/runs/43861486561) und [nativer PR-Lauf 43861497378](https://github.com/nauen/adventure_studio/actions/runs/43861497378) vollständig grün auf Head `ee556e9` (PR nach vollständigem unveränderten Retry); ebenso Core Push/PR, Gradio Push/PR, Inventar-PR und Dialog-PR grün. Review-/Diff-Prüfung und Squash-Merge #242 erfolgt. **R06 bleibt insgesamt Teilfähigkeit.**
- **Blocker:** **Kein offenes Gate für das abgeschlossene R06-Kamerapaket.** Weiterhin echte native Grenze: stock-ScummVM-v6 rendert ZP05–ZP09 nicht, deshalb fail-closed beim Export; R08 allgemeine Polygone und größere/veränderliche R09-Walkboxnetze nicht generell nachgewiesen. Diese Grenzen nicht als erledigt werten.
- **Danach:** **Genau ein** weiteres natives Raumgrafik-/Z-Masken-/Walkbox-Produktpaket aus der Funktionsmatrix auswählen und gesondert mit Modell→Studio/JSON→ScummC→stock ScummVM sowie realen Kontrollen abnehmen. Vorher keine parallelen Features, kein NPC-Komfort. 

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
