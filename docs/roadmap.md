# Adventure Studio – aktive Produktroadmap

## Verbindliche Paketreihenfolge nach #271-Merge (2026-11-23)

- **Hauptziel:** vollständiger nativer SCUMM-v6-Generator ohne eigene Runtime; einzig Gameplay im unveränderten ScummVM und Pflicht-CI rechtfertigen die Abnahme.
- **Integriert:** #266, #264, #267, #269 sowie die native Zwei-Actor-Kameraübergabe [#271](https://github.com/nauen/adventure_studio/pull/271), Merge `d526b4f`. Die frühere Angabe „#271 offen“ unten ist überholt.
- **Jetzt = eine Fähigkeit:** [R06 #272 / PR #273](https://github.com/nauen/adventure_studio/pull/273) — gleichzeitig gegenläufige native Actor-Walks durch ZP01–ZP04 und vollständige Kamerafahrt.
- **Abnahme:** echter Studio/JSON-v1/Story/ScummC-v6-Pfad, drei unabhängig kompilierte Original-ScummVM-Kontrollspiele, zeitgestempelte Pixelbelege für gleichzeitige gegenläufige Bewegung, alle vier Masken, Kamera-Hin-/Rückfahrt, negative Regressionen sowie grüne Core-/Native-Gates auf exakt dem letzten Head.
- **Blocker:** #273 besitzt laut PR derzeit nur implementierte CI-Verdrahtung, keine final bestätigte grüne stock-ScummVM-Abnahme. Nicht mergen; keine nachfolgenden gestapelten Fähigkeiten vorziehen. Keine ZP05+-Freigabe.
- **Danach = ein Folgepaket:** [R06 #274 / PR #275](https://github.com/nauen/adventure_studio/pull/275) — A→B-Kamerafokuswechsel während beide Actors gegensinnig laufen, **erst nach** vollständiger Abnahme von #273; alle weiteren R06-PRs bleiben zurückgestellt.

## Frühere Roadmap-Steuerung (historisch; nicht aktiv)

## Roadmap-Steuerung – aktuelles Einzelpaket (2026-11-23)

- **Hauptziel:** vollständiger nativer SCUMM-v6-Generator. Abnahme ausschließlich durch echtes Verhalten im unveränderten ScummVM und passende Pflicht-CI.
- **Bereits integriert:** #266 (R06 Masken/Bewegung), #264 (R08 konkaver Walkbox-Korridor), #267 (R09 reversible Gates) und #269 (R06 zwei unabhängig bewegte Actors, Issue #268).
- **Jetzt = 1 Fähigkeit:** R06 [#270](https://github.com/nauen/adventure_studio/issues/270) / offener [PR #271](https://github.com/nauen/adventure_studio/pull/271). Kamera folgt Actor A, übergibt während überlappender Actor-Bewegung an Actor B und fährt zurück; vier ZP01–ZP04 bleiben weltfest, alle acht Actor-Maskenpaare gegen transparente/Wrong-BOXD-Kontrollen nachweisen.
- **Abnahme:** echtes Studio/JSON-v1/Story → produktiver ScummC-v6-Export → drei unabhängig gelinkte Spiele → native zeitgestempelte ScummVM-Screenshots, unabhängige Actor-Weltpositionen, messbare Fokusübergabe, Kamerarückweg, acht Z-Maskenkontrollen und vollständige Core-/Native-Pflicht-CI auf finalem Head. Alter Gameplay-Beleg [45088766893](https://github.com/nauen/adventure_studio/actions/runs/45088766893) ist keine Merge-Freigabe.
- **Aktueller Blocker:** fehlgeschlagene Core-/Geometry-/Story-Gates auf Head fd278018 (Runs 45090596656 und 45090602659), gezielte Fix-Commits auf dem bestehenden PR-Branch gepusht. Bis aktuelle grüne CI vorliegt: **nicht mergen, kein neues Paket**.
- **Danach = 1 Folgepaket:** erst nach #271-Abnahme genau eine offene native Matrixlücke nach Nutzerwert und Abhängigkeiten auswählen; kein NPC-Komfort, keine ZP05+-Unterstützung behaupten.

## Historische Roadmap-Stände (keine aktuelle Paketreihenfolge)


## Aktueller integrierter Stand und nächste native Abnahme (2026-11-22)

- **R06:** PR #266, native laufende Actor-Route über vier weltfeste ZP01–ZP04-Masken und vollständige Kamerarückfahrt, integriert.
- **R08:** PR #264, konkaver L-förmiger Korridor aus verbundenen nativen Walkboxes, integriert.
- **R09:** PR #267, zwei reversible native Walkbox-Gates einschließlich Raumwechsel und Rückkehr, integriert mit vollständiger nativer CI #45064059570 und Merge `b5c7cc28`.
- **Jetzt aktiv:** R06 Folgepaket [#268](https://github.com/nauen/adventure_studio/issues/268): zwei voneinander unabhängige bewegte Actors hinter vier weltfesten Raum-Z-Masken im selben stock-ScummVM-Spiel. **Noch nicht implementiert oder abgenommen.** ZP05+ bleibt ausdrücklich fail-closed.


## Konsolidierung und unmittelbar gestartetes R06-Folgepaket (2026-11-22)

- **Hauptziel:** vollständiger nativer SCUMM-v6-Generator ohne Zusatzruntime.
- **Integriert:** R06 PR #262 (`128c9ff`) mit vier gleichzeitigen weltfesten ZP01–ZP04-Masken und nativer Kamerafahrt; R06 bleibt insgesamt Teilfähigkeit.
- **Offene Integration:** R09 PR #260 (Story-Pflichtgate nach R06-Integration laut PR noch rot), R08 PR #264 (L-Korridor, echte Actor-Knickroute und finale Pflicht-CI noch offen). Keine dieser Teilfähigkeiten als fertig oder gemergt ausgeben.
- **Jetzt, explizit priorisiert:** genau ein neues natives R06-Paket [#265](https://github.com/nauen/adventure_studio/issues/265): laufender Actor durch alle vier Masken während Kamera-Hin-/Rückfahrt. Die vorherigen getrennten Actor-Standpositionen nicht als Bewegungsnachweis umdeuten.
- **Abnahme:** echtes Studio → JSON-v1/Story → ScummC/BOXD/BOXM → unverändertes ScummVM; gemessene Actor-/Kamerapositionen, unabhängige transparente und Wrong-Box-Kontrollen, Screenshots/Logs/Report, grüne Core-/Chromium-/Native-Pflichtgates.
- **Blocker/Nicht-Ziele:** kein belegter neuer Gameplay-Nachweis für #265; R09/R08-Merge-Gates bleiben offen; ZP05+ stock-v6 fail-closed; kein NPC-Komfort.
- **Danach:** erst #265 vollständig nativ abnehmen und offene Integrationsgates klären, dann genau ein Folgepaket wählen.


Stand: 2026-11-22. Nur die nächste Produktentscheidung wird hier gesteuert;
die einzige 64-Fähigkeiten-Matrix ist [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator ohne zusätzliche Adventure-Studio-Runtime.
- **Jetzt:** **R06 / [Issue #261](https://github.com/nauen/adventure_studio/issues/261), [PR #262](https://github.com/nauen/adventure_studio/pull/262)**: vier gleichzeitig authorierte Raum-Z-Masken ZP01–ZP04 plus fünf Walkboxen bleiben bei nativer Kamerafahrt X=160→480→160 weltfest. Keine NPC-Komfortarbeit seit #190; kein paralleles R07/R08/R09-Paket.
- **Abnahme:** Vier echte Studio-PNGs → RoomAsset/JSON-v1/Story → produktiver ScummC-v6-/BOXD-Export → **zwölf separat kompilierte Spiele** in unverändertem stock ScummVM (für jede Z-Ebene: maskiert, transparent, falsche Walkbox). Jede Ebene muss den Actor auf Hin- und Rückfahrt verdecken; beide Kontrollen müssen ihn zeigen, der vollständige Kamera-Rückweg muss beobachtet werden. Native Logs, JSON-Report, Screenshots und Browser-Authoring-Evidenz als Artefakte.
- **Blocker:** [Native 45019052534](https://github.com/nauen/adventure_studio/actions/runs/45019052534) hat **alle zwölf echten stock-ScummVM-Spiele** kompiliert, gestartet und mit Zeitstempeln dokumentiert: ZP01–ZP03 je 0 verdeckte Actor-Pixel, ZP04 296 gegenüber 1540 in beiden Kontrollen, jeweils auf Hin-/Rückfahrt. [Artefakt](https://github.com/nauen/adventure_studio/actions/runs/45019052534/artifacts/14752699463). Das abschließende CI-Gate war trotzdem rot, weil der statische Start-/Endbild-Vergleich `scroll_color_signature_passed` bei beabsichtigter X=160→480→160-Rückkehr definitionsgemäß falsch ist (`scroll_expected=false`). Der Selektor verlangt jetzt **echte Frame-Variation plus gemessenen vollständigen Kameraverlauf**; der separate ZP01-Basistest berücksichtigt den belegten 32er-Kamera-Samplingversatz. Finales Core/Native/Studio-Gate nach dem Fix noch offen. ZP05+ bleibt stock-v6-fail-closed.
- **Danach:** Erst nach R06-ScummVM-Nachweis und grünen Pflichtgates das einzelne R09-Walkbox-Raumrückkehrpaket [PR #260](https://github.com/nauen/adventure_studio/pull/260) konsolidieren und abnehmen. Keine anderen parallelen Features.

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
