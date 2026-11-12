# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-12. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne zusätzliche Runtime; maßgeblich bleibt die [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** **R09 – zyklisches Sechs-Walkbox-Netz mit Ausweichroute** ist nach [PR #214](https://github.com/nauen/adventure_studio/pull/214), Squash `911a3976`, in `main` integriert. Der vorhandene Studio-Walkbox-/Verbindungseditor authoriert den Zyklus `1-2-4-6-5-3-1`; nach Entfernen einer Kante wählt BOXM die andere Route. Keine NPC-Komfortarbeit.
- **Abnahme:** Studio-Authoring → RoomAsset/JSON/Story → nativer `boxd`/BOXM-Export → ScummC → stock ScummVM. Voller Zyklus: BOXM 1→6=2, Fernziel erreicht. Oberen Zweig `2-4` getrennt: 1→6=3, Fernziel unten erreicht. Unteren Zweig `3-5` getrennt: 1→6=2, Fernziel oben erreicht; in allen drei Fällen **1556** dunkle Actor-Pixel im Fernziel-Crop. Beide Zweige getrennt: keine Fernziel-Signatur, Actor bleibt mit **1612** dunklen Pixeln im Nahbereich stehen. `native_six_box_cycle_detour_passed=true`; [Screenshots, vier Studio-Projekt-JSONs und Report](https://github.com/nauen/adventure_studio/actions/runs/43276225187/artifacts/13969904348); [native PR-CI 43276225187](https://github.com/nauen/adventure_studio/actions/runs/43276225187) und [parallele native CI 43276158637](https://github.com/nauen/adventure_studio/actions/runs/43276158637) beide **98/98 grün**, [Core 43276225269](https://github.com/nauen/adventure_studio/actions/runs/43276225269) grün.
- **Blocker:** Kein R09-Sechs-Boxen-Pflichtgate offen. R09 als Ganzes bleibt **Teilfähigkeit**: beliebig große/komplexe Graphen und dynamisch im laufenden Spiel veränderte Walkbox-Verbindungen sind nicht belegt. R06: native Nachweise nur bis ZP04; R07-Varianten offen. Der bereits dokumentierte ältere SCAL-Pixel-Schwellenfluktuationsfall `43272151083` bleibt gesondertes Teststabilitätsrisiko, kein Grund für Status-Beschönigung. NPC-Mehrzeilen-PR #80 separat gesperrt.
- **Danach:** Genau **ein** natives Raumgrafik-Paket priorisiert: **R06.5 fünfte unabhängig im Studio importierte PNG-Z-Maske ZP05**, mit Maskenindex 5 einer authorierten Walkbox zugewiesen und sichtbarer Actor-Verdeckung in stock ScummVM. Modell→JSON/Story→ZP05/BOXD→echte Pixel-/Kontroll-Evidenz. Keine Aussage über ZP06–ZP09 oder beliebige Kombinationen, keine NPC-Komfortarbeit.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | Studio/JSON/Story-ZP01 bis ZP04 mit Walkbox-Zuordnung und jeweils getrennter Actor-Verdeckung in stock ScummVM nachgewiesen; PR #198/#204/#208, native Runs `43105298694`, `43251867709`, `43264467363` | Mehr als vier Ebenen und allgemeine Engine-Varianten nicht als vollständig verifiziert behaupten |
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
