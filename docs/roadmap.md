# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-12. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne zusätzliche Runtime; belegter Umfang in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** Genau R07.1 – PNG-Z-Maske für den ersten Bildzustand eines nativen Raumobjekts im Studio authorieren, im OBIM/IM01/ZP01 exportieren und Actor-Verdeckung in unverändertem ScummVM nachweisen. R06.2/ZP01+ZP02 wurde mit PR #198 und fünf grünen Checks gemergt (`0809336`); keine NPC-Komfortpakete nach #190.
- **Abnahme:** Realer Studio-PNG-Klickpfad → validiertes RoomHotspot-Objektmaskenfeld in JSON und Story-Komposition ohne Verlust → ScummC-Objektbildzustand mit nativem ZP01 → sichtbarer maskierter Actor im unveränderten ScummVM gegenüber identischer Variante ohne Objektmaske. Core-, Chromium- und native CI auf finalem R07.1-Commit grün.
- **Blocker:** R07.1-Gameplay-Evidenz und finale CI stehen aus. Erster Objektbildzustand ist der bewusst begrenzte Umfang; weitere Zustände/Z-Ebenen, allgemeine Decoder-/Engine-Varianten offen.
- **Danach:** Erst nach vollständig grüner R07.1-CI und Merge genau das nächste aus der Capability-Matrix priorisierte native Raum-/Walkbox-Paket; keine parallele NPC-Komfortarbeit.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | PNG-Authoring über Studio/JSON/ZPxx und native Actor-Verdeckung für zwei einzeln wählbare Ebenen belegt (PR #198) | Allgemeine Ebenenzahlen und Engine-Varianten offen |
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
