# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-12. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne zusätzliche Runtime; der belegte Stand steht in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** Nach R09-Sechs-Walkbox-Zyklus (PR #214/#215, beide gemergt) wurde **R06.5 – fünfte Raum-Z-Maske ZP05** auf dem produktiven Studio-PNG → RoomAsset/JSON/Story → ScummC/BOXD → stock-ScummVM-Pfad geprüft. [PR #216](https://github.com/nauen/adventure_studio/pull/216) ist **Draft, nicht gemergt**: Export und Modell funktionieren, die neue Verdeckung nativ **nicht**. Kein NPC-Komfort und keine zweite parallele Fähigkeit.
- **Abnahme:** **Negativer echter Runtime-Nachweis**, keine R06.5-Abnahme: getrennte Kontrollszene **1556** sichtbare Actor-Pixel; opake ZP01–ZP04 jeweils **0**; allein opake ZP05 **1556**. Die Studio-JSONs enthalten fünf PNG-Z-Ebenen und BOXD-Maskenindex 5, jedoch verhält sich der originale ScummVM-Interpreter bei ZP05 wie bei der Kontrolle. [Roter nativer Run 43280112818](https://github.com/nauen/adventure_studio/actions/runs/43280112818), [Screenshots/JSONs 13971624727](https://github.com/nauen/adventure_studio/actions/runs/43279932399/artifacts/13971624727); [Core-Run 43280112772](https://github.com/nauen/adventure_studio/actions/runs/43280112772) grün. Die Fehlfunktion ist auch in den zwei früheren nativen Läufen `43279932399` und `43279995420` reproduziert.
- **Blocker:** **Stock-ScummVM-SCUMM-v6-Pfad erkennt keine ZP05-Maske**: `engines/scumm/gfx.cpp`, `Gdi::getZPlanes()`, verwendet ein festes Tag-Array nur für `ZP00`–`ZP04`, auch auf aktuellem upstream Master. Für ZP05 ist die native Maskendekodierung nicht belegt und die Gegenprobe explizit fehlgeschlagen. R06 bleibt **Teilfähigkeit mit vier nachgewiesenen Ebenen**; keine Umgehung per gepatchter Runtime, kein stiller Masken-Fallback oder Abnahme durch Compiler-Erfolg. Der frühere SCAL-Testfluktuationsfall `43272151083` bleibt separat; NPC-PR #80 ist ausgesetzt.
- **Danach:** Zuerst **Entscheidung über den Zielvertrag**: Stock-ScummVM-v6 ohne Engine-Patch beibehalten (dann ZP05 als unzulässigen nativen Export explizit ablehnen und ein anderes kompatibles Raumgrafik-/Walkbox-Produktpaket priorisieren) **oder** eine andere, eigenständig nachzuweisende kompatible native Darstellung begründen. Bis zur Entscheidung keine zweite native Feature-Implementierung beginnen.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | Studio/JSON/Story-ZP01 bis ZP04 mit Walkbox-Zuordnung und jeweils getrennter Actor-Verdeckung in stock ScummVM nachgewiesen; PR #198/#204/#208, native Runs `43105298694`, `43251867709`, `43264467363` | ZP05 scheitert in stock ScummVM: `Gdi::getZPlanes()` taggt nur ZP00–ZP04; PR #216 Draft/rot, keine fünfte Verdeckung behaupten |
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
