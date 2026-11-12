# Adventure Studio – aktive Produktroadmap

Stand: 2026-11-12. Diese Seite steuert **nur die nächsten Produktentscheidungen**.
Das Hauptziel steht in [PRODUCT_VISION](PRODUCT_VISION.md), die einzige
64-Fähigkeiten-Matrix in [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).
Die frühere ausführliche Roadmap bleibt vollständig als
[historisches Entwicklungsprotokoll](roadmap-history.md) erhalten;
ihre alten „Nächstes“-Abschnitte und Checkboxen sind **keine aktiven Aufträge**.

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger Generator originaler SCUMM-v6-Spiele ohne zusätzliche Runtime; aktueller Nachweisumfang steht in der [64-Fähigkeiten-Matrix](SCUMM_V6_CAPABILITIES.md).
- **Jetzt:** **R06 – sicherer nativer Z-Maskenexport für stock ScummVM v6** nach [PR #218](https://github.com/nauen/adventure_studio/pull/218), Squash `45270469`, in `main` integriert. Der Studio-Editor behält fünf oder mehr PNG-Z-Masken im Fachmodell/JSON verlustfrei; der native ScummC-/BOXD-Export verweigert ZP05+ und Walkbox-Maskenindex >4 mit raumbezogenem Fehler **vor dem Schreiben**, einschließlich Vorvalidierung aller Räume im gesamten Spiel. Der gescheiterte [ZP05-Draft #216](https://github.com/nauen/adventure_studio/pull/216) ist ungemergt geschlossen; keine NPC-Komfortarbeit.
- **Abnahme:** Produktiver Studio-PNG-Import → RoomAsset/JSON → Exportvalidierung; gültige Masken ZP01–ZP04 → ScummC → **stock ScummVM**: transparente Kontrolle **1556** sichtbare Actor-Pixel, jede der vier aktiven Masken **0**. Ein fünftes PNG bleibt im gespeicherten Projekt, aber die Exportquelle/BOXD-Spieldateien werden **explizit verweigert**, ohne Teildateien. `four_layers_visually_verified=true`, `fifth_studio_png_preserved=true`, `fifth_native_export_refused=true`, `native_assets_written=false`. [Screenshots/JSON/Report, Artifact 13972832770](https://github.com/nauen/adventure_studio/actions/runs/43282575410/artifacts/13972832770). Core [43282575317](https://github.com/nauen/adventure_studio/actions/runs/43282575317) und Dialog [43282575394](https://github.com/nauen/adventure_studio/actions/runs/43282575394) grün; vollständiger [nativer PR-Run 43282575410](https://github.com/nauen/adventure_studio/actions/runs/43282575410) nach dokumentiertem unverändertem Retry **98/98 grün**.
- **Blocker:** R06 bleibt **Teilfähigkeit**: Stock-ScummVM-v6-`Gdi::getZPlanes()` erkennt nur `ZP00`–`ZP04`; ZP05 ist kein funktionsfähiger nativer Export. Vor der Exportsperre ergab [PR #216](https://github.com/nauen/adventure_studio/pull/216) Kontrolle/ZP05 je 1556 sichtbare Actor-Pixel, ZP01–04 je 0; daraus folgt **kein** positiver ZP05-Nachweis. Andere Kombinationen mehrerer Raum-Z-Ebenen gleichzeitig noch nicht gezielt nachgewiesen. Auf identischem PR218-Head waren ein erster Push-Run `43282475132` (PNG-Actor-Frame-Abtastung) und ein erster PR-Versuch `43282575410` (allgemeiner Masken-/SCAL-Bildvergleich) rot; beide unveränderten Prüfungen bestanden im vollständig grünen PR-Retry. Separate Teststabilitätsrisiken, kein Schwellen-/Testabbau. PR #80 bleibt als NPC-Blocker unberührt.
- **Danach:** Genau **ein** natives Raumgrafik-/Walkbox-Paket priorisiert: **R06 – zwei unterschiedliche gleichzeitig aktive, unabhängig PNG-authorierte Z-Masken ZP01 und ZP02 auf zwei benachbarten Walkboxen im selben exportierten Spiel**. Modell/Walkbox-Auswahl → JSON/Story → ScummC-ZP01/ZP02 und BOXD-Maskenindizes 1/2 → stock-ScummVM-Spielerbewegung in beide Bereiche mit jeweils sichtbarer Verdeckung und passenden transparenten Kontrollen. Keine neue Engine, kein ZP05-Export und kein NPC-Komfort.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | Studio/JSON/Story-ZP01 bis ZP04 mit Walkbox-Zuordnung und jeweils getrennter Actor-Verdeckung in stock ScummVM nachgewiesen; PR #198/#204/#208, native Runs `43105298694`, `43251867709`, `43264467363` | ZP05 scheitert in stock ScummVM; ungemergter PR #216 als Negativbefund geschlossen. PR #218 verweigert ZP05+ im produktiven nativen Export mit verständlichem Fehler, erhält die Studio-Daten; simultane Verdeckung verschiedener Masken noch offen |
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
