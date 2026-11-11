# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-11. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne zusätzliche Runtime; belegter Umfang in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** Nach NPC-Abschluss #190, Konsolidierung #191/#192 und PNG-Z-Maske #193 liefert [PR #194](https://github.com/nauen/adventure_studio/pull/194) genau **R08.1 – eine frei gezeichnete konvexe Vierpunkt-Walkbox** durch Studio → Projekt-JSON → natives BOXD. Kein neues NPC-Komfortpaket.
- **Abnahme:** Echter Chromium-Editorlauf mit Authoring und JSON-Roundtrip; native [CI 43079024249](https://github.com/nauen/adventure_studio/actions/runs/43079024249) grün: dieselbe Actor-Zielkoordinate wird mit der raumweiten Walkbox erreicht (Scroll in die entfernte Raumhälfte), mit der begrenzten Walkbox nicht; Actor bleibt links sichtbar (1.612 gemessene Actor-Pixel), `native_walkbox_boundary_passed=true`. [Native Evidenz](https://github.com/nauen/adventure_studio/actions/runs/43079024249/artifacts/13884270940).
- **Blocker:** R08.1 belegt **eine** authorierte konvexe Walkbox mit realer nativer Laufgrenze, nicht beliebige Polygone, Mehrboxennetze oder R09-Routing. #187 (menschlicher Tab-Abbruch) und #80 (Mehrsprecher-Animation) bleiben getrennt. PR #194 bleibt bis grüner Gesamt-CI und Merge offen.
- **Danach:** Erst nach R08.1-Abnahme/Merge genau **R09 – mehrere Walkboxen, Verbindungen und native Actor-Routen via BOXM** auswählen; R10/SCAL und O03 folgen später.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | PNG-Authoring über Studio/JSON/ZPxx und native Actor-Verdeckung für eine Ebene belegt | Mehrere Ebenen und allgemeine Varianten/Grenzen nicht als voll verifiziert behaupten |
| P0.3 / R08–R10 – Walkbox/SCAL | `RoomAsset.walkboxes`, BOXM, SCAL, JSON und native Sicht-/Skalierungsprobe; R08.1 mit frei authorierter konvexer Box und nativer Laufgrenze belegt | Allgemeine Polygone, Wege-/Boxennetze und Perspektivvarianten offen |
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
