# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-13. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne Zusatzruntime; verbindlicher Gesamtumfang in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** **Genau eine R09-Teilfähigkeit in [Draft-PR #230](https://github.com/nauen/adventure_studio/pull/230)**: den reversiblen nativen Tür-Walkbox-Zustand über echtes **ScummVM-Save/Load** erhalten. Das in #229 gemergte Studio-`reversible_walkbox`-Modell → UseRule/JSON-v1/Story → produktiver ScummC-v6-Export bleibt die Grundlage; #230 ergänzt native Save/Reload- und Actor-Routenproben. Kein NPC-Komfort nach #190.
- **Abnahme:** Nach mehrfacher echter Inventar-Use-Aktion `tentacle.s01` über die native ScummVM-Oberfläche sichern; in einem **neu gestarteten, unveränderten ScummVM** laden; sichtbar offene Tür und Actor-Abkürzung gegen eine immer-offene Kontrolle messen; mit erneutem Use das Gate schließen und den Umweg per Actor-Pixeln beweisen. #230: zwei Core-Läufe auf `ff56320` grün; die [native PR-CI 43359845966](https://github.com/nauen/adventure_studio/actions/runs/43359845966) läuft. Der erste [native Lauf 43358206674](https://github.com/nauen/adventure_studio/actions/runs/43358206674) bewies echten Save-Slot, Neustart/Load und neun offene Actor-Routenbilder, **nicht** die vollständige Abnahme; Kamera-Bildprüfung in `ff56320` korrigiert.
- **Blocker:** **#230 noch Draft, nicht gemergt und nicht nativ endabgenommen.** Nach erfolgreichem Save/Load, sichtbarem Türzustand und post-load Use in [Run 43359031034](https://github.com/nauen/adventure_studio/actions/runs/43359031034) scheiterte der native Test ausschließlich an zeitlich versetzten letzten drei Actor-Routenbildern. Fix `ff56320` vergleicht die sechs gleichen Laufphasen gegen die unabhängige offene Kontrolle; Negativtests bleiben strikt. Die **gesamte native CI 43359845966** muss nun bestanden werden; [Dialog-CI 43359030972](https://github.com/nauen/adventure_studio/actions/runs/43359030972) ist **vollständig grün** auf dem Vorgänger-Head; neuer Lauf auf `ff56320` aktiv. Keine künstliche Testabschwächung. R09 insgesamt bleibt Teilfähigkeit: unabhängige Mehrfach-Gates, allgemein dynamische Netze und separate Raum-Rückkehr fehlen; ZP05+ bleibt in stock v6 gesperrt.
- **Danach:** **Erst** nach vollständiger nativer Save/Load-Evidenz, grünen Gesamtgates und Merge von #230 genau **ein** weiteres priorisiertes Walkbox-Paket beginnen (z. B. Gate-Zustand nach Raum-Rückkehr). Keine Zusatzruntime, kein NPC-Komfort.

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
