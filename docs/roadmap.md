# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-12. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne zusätzliche Runtime; belegte Teilfähigkeiten stehen in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** **R09 – zwei unterschiedliche Laufziele in einem Fünf-Walkbox-T-Netz** nach [PR #212](https://github.com/nauen/adventure_studio/pull/212), Squash `a09592c4`, in `main` integriert. Der bestehende Studio-Walkbox-/Verbindungseditor authoriert fünf konvexe Boxen mit `1-2; 2-3; 3-4; 3-5`. Modell/JSON/Story/BOXD/BOXM steuern die native Actor-Bewegung zum oberen und unteren Ziel und zurück. NPC-Komfort bleibt ausgesetzt.
- **Abnahme:** Ein exportiertes Spiel, derselbe unveränderte ScummVM-Prozess: obere Zielregion **1464** dunkle Actor-Pixel, nach Spieler-Klick unten **1272**, nach Rückklick oben **1304**. Separater Kontroll-Export ohne Verbindung `3-5` zeigt im unteren Zielausschnitt nur **142** statt 1272 Pixel. `native_two_goal_t_branch_passed=true`; [Pixelreport/Screenshots/JSONs](https://github.com/nauen/adventure_studio/actions/runs/43272211665/artifacts/13968093482). Finale [native CI 43272211665](https://github.com/nauen/adventure_studio/actions/runs/43272211665) **98/98 Schritte**, [Core 43272211675](https://github.com/nauen/adventure_studio/actions/runs/43272211675) und [Dialog 43272211687](https://github.com/nauen/adventure_studio/actions/runs/43272211687) grün.
- **Blocker:** Kein offenes Pflichtgate für diese R09-Teilfähigkeit. R09 insgesamt bleibt unvollständig: zyklische/größere Netze und weitere native Routingvarianten ohne Gameplay-Nachweis. Ein älterer paralleler Push-Lauf `43272151083` derselben Revision scheiterte an einer unveränderten SCAL-Costume-Pixel-Schwelle (704/1020/1068); die identische Probe war im final grünen PR-Run erfolgreich. Teststabilitätsrisiko dokumentiert, nicht verdeckt. PR #80 bleibt als NPC-Blocker gesondert ausgesetzt; R06 jenseits ZP04 und R07-Mehrzustandsvarianten ebenfalls offen.
- **Danach:** Genau **eine** neue native R09-Lücke priorisiert: **zyklisches Sechs-Walkbox-Netz mit zwei verschiedenen Wegen zwischen denselben Start-/Zielboxen**. Studio-Modell → JSON/Story → BOXD/BOXM → Actor erreicht in stock ScummVM das Ziel über eine Alternativroute, wenn eine einzelne Kante entfernt wird; bei beiden getrennten Wegen bleibt das Ziel unerreichbar. Keine neue Runtime, kein NPC-Komfort, keine allgemeine Graphvollständigkeit behaupten.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | Studio/JSON/Story-ZP01 bis ZP04 mit Walkbox-Zuordnung und jeweils getrennter Actor-Verdeckung in stock ScummVM nachgewiesen; PR #198/#204/#208, native Runs `43105298694`, `43251867709`, `43264467363` | Mehr als vier Ebenen und allgemeine Engine-Varianten nicht als vollständig verifiziert behaupten |
| P0.3 / R08–R10 – Walkbox/SCAL | `RoomAsset.walkboxes`, BOXM, SCAL, JSON und native Sicht-/Skalierungsprobe; R08.1 konvexe Box und R09 Vier-Boxen-Alternativen und Fünf-Boxen-T-Netz mit zwei Laufzielen im selben stock-ScummVM-Prozess belegt | Allgemeine Polygone, Wege-/Boxennetze und Perspektivvarianten offen |
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
