# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-11. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator für originale SCUMM-v6-Spiele ohne zusätzliche Adventure-Studio-Runtime. Die [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md) führt den belegten Umfang.
- **Jetzt:** [PR #190](https://github.com/nauen/adventure_studio/pull/190) mit Core-/Chromium-/nativen CI-Gates abschließen; anschließend [PR #191](https://github.com/nauen/adventure_studio/pull/191) als Konsolidierung von PRs, CI, Matrix, Roadmap und Status prüfen. Keine weitere NPC-Komfortfunktion.
- **Abnahme:** Danach genau **R06 – frei authorierbare Raum-Z-Maske** als ein vertikales Produktpaket: Ein Autor definiert eine Raum-Verdeckung im nativen Modell, exportiert sie als ZPxx und beobachtet im unveränderten ScummVM, wie der Actor beim Durchlaufen korrekt vor/hinter der gezeichneten Raumebene erscheint. Normale und leere Masken sowie mindestens zwei unterscheidbare Verdeckungsbereiche risikogerecht prüfen; vorhandene ZPxx-Teilbelege wiederverwenden. Kein allgemeiner R06-Abschluss allein aufgrund der bestehenden Fixture.
- **Blocker:** #190 hat noch offene relevante CI-Gates; die menschliche Tab-Abbruchabnahme aus #187 ist offen. Bei R06 gilt fehlende echte ScummVM-Spielverhaltens-Evidenz als offener Blocker, nicht als fertige Funktion.
- **Danach:** Genau **R08 – frei definierbare Walkbox-Polygone** als nächstes Paket (BOXD und Actor-Grenzen im echten Spiel). Erst nach R06-Abnahme starten; R09-Wege und R10-Skalierung anschließend gesondert priorisieren. P0.4/O03-Objektbewegung bleibt nachgeordnet.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | `RoomAsset.zplanes`, JSON, ScummC-ZPxx und native Verdeckungsprobe vorhanden | Freies Authoring, mehr als eine Ebene und Varianten/Grenzen nicht als voll verifiziert behaupten |
| P0.3 / R08–R10 – Walkbox/SCAL | `RoomAsset.walkboxes`, BOXM, SCAL, JSON und native Sicht-/Skalierungsprobe vorhanden | Allgemeine Wege-/Boxennetze, frei erstellte Polygone und Perspektivvarianten offen |
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
