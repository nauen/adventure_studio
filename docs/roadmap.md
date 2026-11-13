# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-13. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne Zusatzruntime; verbindlicher Gesamtumfang in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** **R09 – dieselbe native Tür-Walkbox reversibel sperren/freigeben**, [PR #229](https://github.com/nauen/adventure_studio/pull/229), Head `20904784`, **offen**. Eine Studio-Checkbox `reversible_walkbox` → UseRule/JSON-v1/Story → ScummC-v6 `getObjectState`/`setObjectState`, `setBoxFlags([2],128/0)` und `createBoxMatrix()`; echte Inventar-Use-Aktion schaltet dieselbe Route mehrfach um. Kein neuer NPC-Komfort nach #190.
- **Abnahme:** Gezielte native reversible R09-Spielprobe auf finalem PR-Head in **beiden** stock-ScummVM-Läufen erfolgreich: [PR-Run 43350834908 / Artifact 14003917389](https://github.com/nauen/adventure_studio/actions/runs/43350834908/artifacts/14003917389), [Push-Run 43350824948 / Artifact 14003832258](https://github.com/nauen/adventure_studio/actions/runs/43350824948/artifacts/14003832258), mit Umweg → Abkürzung → erneutem Umweg → Abkürzung und immer-offener Kontrolle. Core Push/PR, Dialog, Inventar und Chromium grün. **Gesamtabnahme und Merge ausstehend**, da beide native Gesamt-Workflows noch laufen; #226 bleibt bereits vollständig gemergte Vorgängerfähigkeit.
- **Blocker:** Zwei native Gesamt-CI-Gates auf `20904784` noch `in_progress` (nach erfolgreichem Test dreier Z-Masken aktuell vier simultane Z-Masken). Bis alle Pflichtgates grün sind, **PR #229 nicht mergen und nicht als vollständig geliefert markieren**. R09 bleibt eine Teilfähigkeit: unabhängige Mehrfach-Gates, allgemeine dynamische Netze sowie Gate-Zustand nach nativem Save/Load und Raum-Rückkehr sind nicht separat abgenommen; ZP05+ bleibt in stock ScummVM gesperrt.
- **Danach:** **Erst nach grünem Merge und Dokument-Konsolidierung genau ein neues Produktpaket:** R09 – reversiblen Gate-Zustand über natives **Save/Load** erhalten und in stock ScummVM gegen eine Kontrollvariante beweisen (Modell → Export → Gameplay). **Raum-Rückkehr** und mehrere Gates bleiben spätere, getrennte Pakete. Keine zusätzliche Runtime, kein NPC-Komfort.

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
