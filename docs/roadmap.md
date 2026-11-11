# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-11. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

| Rang | Paket | Produktnutzen und Abnahme | Zustand |
| --- | --- | --- | --- |
| 0 | [PR #190](https://github.com/nauen/adventure_studio/pull/190): mehrere NPC-Sprechentwürfe gemeinsam übernehmen | Alle offenen Folgen atomar ins native Projekt speichern und exportieren | **Gemergt** (`f638cc68`); Core `43068566462`, Chromium `43068566433`, native `43068566317` grün |
| **1** | **P0.4 / O03: bewegliches, anklickbares Objekt** | Ein sichtbares Objekt zur Laufzeit versetzen; Klick gilt danach an der neuen, nicht an der alten Position; native v6-Spielprobe | **Nächstes Produktpaket** |
| 2 | P0.4 / O04–O02: Eltern-/Kind- und Zustandsbilder | Mehrere sichtbare Zustände mit korrekter Interaktion und nativer Spielprobe | Offen; nach O03 neu priorisieren |
| 3 | A05 / R06–R10: allgemeine Verdeckung und Laufbereiche | Frei authorierte Masken/Walkboxen und verifizierte Actor-Bewegung jenseits des Fixtures | Grundlagen vorhanden, allgemeiner Authoring-/Gameplay-Nachweis offen |
| 4 | S02–S04 / A08: parallele Actor- und Cutscene-Abläufe | Koordinierte Figurenaktionen, Überspringen mit korrektem Endzustand | Offen |

**Der nächste Implementierungsschnitt ist P0.4/O03.** Er baut auf den
vorhandenen Room-Hotspots, Objektzuständen und nativen ScummC-Routinen auf.
Vor dem Code wird der bereits dokumentierte `drawObjectAt`-Vertrag auf
die fehlende v6-Variante geprüft; keine neue allgemeine Quellenrecherche.
Der kleinste akzeptierte Nutzerpfad ist ein Editor-/Projektzustand mit
einem verschobenen Objekt, dessen Darstellung **und** Trefferbereich
nach der Verschiebung im unveränderten ScummVM funktionieren.

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
