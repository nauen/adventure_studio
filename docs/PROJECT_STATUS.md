# Adventure Studio – aktueller Arbeitsstand

Stand: 2026-11-12. **Einstieg für die nächste Arbeitssitzung.**
Produktziel: [PRODUCT_VISION](PRODUCT_VISION.md) · aktive
[Roadmap](roadmap.md) · einzige [SCUMM-v6-Funktionsmatrix](SCUMM_V6_CAPABILITIES.md) ·
[Referenzvertrag](scumm-v6-reference/README.md) · [Arbeitsvertrag](../AGENTS.md).
Das frühere ausführliche Sitzungsprotokoll liegt unverändert in
[PROJECT_HISTORY](PROJECT_HISTORY.md); dessen historische
„Nächstes“-Anweisungen steuern die Entwicklung nicht mehr.

## Ein aktiver Produktpfad

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator mit realem Gameplay im unveränderten ScummVM, ohne zusätzliche Adventure-Studio-Runtime.
- **Jetzt:** R09 – zwei unterschiedlich authorierte Routen durch ein Vier-Walkbox-Netz (1→2→4 und 1→3→4) samt blockierter Kontrolle über Studio/RoomAsset/JSON/Story/BOXD/BOXM bis stock ScummVM abgenommen; [PR #210](https://github.com/nauen/adventure_studio/pull/210) als `7421c384` gemergt. Aktuellen Teilstand konsolidieren, NPC-Komfort ausgesetzt.
- **Abnahme:** [Nativer Run 43268042542](https://github.com/nauen/adventure_studio/actions/runs/43268042542) 98/98 Schritte erfolgreich; [Core Run 43268042749](https://github.com/nauen/adventure_studio/actions/runs/43268042749) grün. Unterschiedliche BOXM-Next-Hops **2** und **3** führen beide zum Fernziel; ohne Netz bleibt die Figur mit **1612** dunklen Actor-Pixeln an der nahen Laufgrenze stehen. `native_branching_boxm_passed=true`; [Screenshots, Pixel-/Routenreport und drei Projekt-JSONs](https://github.com/nauen/adventure_studio/actions/runs/43268042542/artifacts/13967425948).
- **Blocker:** R09.2-Vier-Boxen-Teilprobe ohne offenes Pflichtgate, R09 bleibt aber **Teilfähigkeit**. Zwei verschiedene Ziele in demselben verzweigten Netz, größere/zyklische Netze und allgemeine Polygone sind noch nicht nativ belegt. PR #80 bleibt separat wegen nicht nachgewiesener NPC-Mehrzeilen-Sprechfolge offen.
- **Danach:** Genau **R09-Fünf-Walkbox-T-Abzweig zu zwei verschiedenen Laufzielen in einem Spiel**: produktiver Studio-Editor → RoomAsset/JSON/Story → BOXD/BOXM → stock ScummVM; beide Ziele erreichen, einen getrennten Zweig kontrolliert nicht erreichen. Kein NPC-Komfort, keine Auto-Routenführung.

## Zuletzt tatsächlich geliefert

| PR | Nutzerfunktion | Evidenz/Grenze |
| --- | --- | --- |
| [#210](https://github.com/nauen/adventure_studio/pull/210) | Vier native Walkboxen als alternative Studio-Verbindungsnetze 1→2→4 oder 1→3→4 authorieren und in ScummVM jeweils das Fernziel erreichen | Core `43268042749` und gesamte native CI `43268042542` (98 Schritte) grün; zwei unterschiedliche BOXM-First-Hops und isolierte Kontrolle, 1612 dunkle Actor-Pixel am Rand; [Artifakt 13967425948](https://github.com/nauen/adventure_studio/actions/runs/43268042542/artifacts/13967425948); Squash `7421c384`. Nur R09-Teilfunktion | 
| [#208](https://github.com/nauen/adventure_studio/pull/208) | Vier unabhängig authorierte Raum-Z-PNGs als ZP01–ZP04 einschließlich BOXD-Maskenindex 4 mit sichtbarer Actor-Verdeckung | [Stock-ScummVM Run 43264467363](https://github.com/nauen/adventure_studio/actions/runs/43264467363) 98/98 Schritte grün; Kontrolle 1484 Actor-Pixel gegen ZP01–04 jeweils 0; [Artifact 13964179377](https://github.com/nauen/adventure_studio/actions/runs/43264467363/artifacts/13964179377); Core 43264467380 grün; Squash-Merge `a3822677`. Nur R06.4-Teilnachweis | 
| [#206](https://github.com/nauen/adventure_studio/pull/206) | Eigene PNG-Z-Maske für den zweiten nativen Objektbildzustand im Editor authorieren, Grundbildmaske unabhängig behalten | Sieben finale Checks am Head `48134c0` grün (Core 2×, Chromium 2×, Dialog, Inventar, native), [native Run 43260630627](https://github.com/nauen/adventure_studio/actions/runs/43260630627), [Chromium 43260617357](https://github.com/nauen/adventure_studio/actions/runs/43260617357) und [43260633388](https://github.com/nauen/adventure_studio/actions/runs/43260633388); Squash-Merge `6350537`. R07 bleibt auf zwei Bildzustände und eine ZP01 je Zustand begrenzte Teilfähigkeit |
| [#204](https://github.com/nauen/adventure_studio/pull/204) | Dritte unabhängig wählbare Raum-Z-Maske ZP03 vom Studio-PNG bis zur Actor-Verdeckung in stock ScummVM | Vier finale Checks am Head `90ec4b0` grün (Core 2×, native 2×), Runs `43251867709` und `43251882252`, PNG-Costume-Regression repariert; Squash-Merge `c78d817`. R06 bleibt Teilfähigkeit: mehr als drei Ebenen nicht bewiesen |
| [#202](https://github.com/nauen/adventure_studio/pull/202) | Vorhandenes Walkbox-Netz um eine zunächst isolierte Box erweitern; neue Verbindung explizit authorieren | Sechs finale Checks auf `4bfd0b2` grün (Core 2×, Chromium 2×, Dialog, native); nativer Run `43242184897`, Chromium `43242185359` und `43242172287`; Squash-Merge `58022c5`; R08/R09 bleiben Teilfähigkeiten |
| [#198](https://github.com/nauen/adventure_studio/pull/198) | Zwei PNG-Z-Masken im Studio mit Walkbox-ZPxx-Auswahl authorieren und in stock ScummVM getrennt verdecken | Fünf finale Checks am Head `2cba5d7` grün (Core 2×, Chromium, Dialog, native); [native Run 43105298694](https://github.com/nauen/adventure_studio/actions/runs/43105298694), [Screenshot-Artefakt 13893353897](https://github.com/nauen/adventure_studio/actions/runs/43105298694/artifacts/13893353897); Merge `0809336c`; begrenzte R06-Teilfähigkeit |
| [#197](https://github.com/nauen/adventure_studio/pull/197) | SCAL-Kurven und Walkbox-Slots über Studio authorieren | Sechs finale CI-Checks inklusive stock ScummVM und Chromium grün; Merge `b66287a`, native Run `43093101278` |
| [#196](https://github.com/nauen/adventure_studio/pull/196) | Benachbarte Walkboxen verbinden, native BOXM-Next-Hop-Wege authorieren | Finale Core-, Chromium-, Dialog- und stock-ScummVM-CI grün; Merge `d917ead4`, nativer Run `43087563847` |
| [#194](https://github.com/nauen/adventure_studio/pull/194) | Konvexe Vierpunkt-Walkbox im Editor authorieren und native Laufgrenze erreichen | Core, Dialog, Chromium und ScummVM-CI grün; Merge `7acc7fb3`; nur R08.1-Teilfähigkeit |
| [#193](https://github.com/nauen/adventure_studio/pull/193) | PNG-Z-Maske authorieren, exportieren und Actor-Verdeckung in stock ScummVM sehen | Native `43073010730` grün; 350 Pixel verdeckt, Scope auf belegte PNG-Maskenfähigkeit begrenzt |
| [#190](https://github.com/nauen/adventure_studio/pull/190) | Alle offenen NPC-Sprechfolgen atomar ins native Projekt übernehmen | Core `43068566462`, Chromium `43068566433`, native `43068566317` grün; `main` `f638cc68` |
| [#189](https://github.com/nauen/adventure_studio/pull/189) | Einzelnen offenen NPC-Sprechentwurf verwerfen, andere behalten | Core `43062376826`, Chromium `43062376847` grün; `main` `65fbd16` |
| [#188](https://github.com/nauen/adventure_studio/pull/188) | Offene Sprechfolgen ohne Projektwechsel wieder öffnen | Core `43052463816`, Chromium `43052463728` grün; `main` `fe62c4c` |
| [#187](https://github.com/nauen/adventure_studio/pull/187) | Browser-Tab-Warnung bei offenen Sprechentwürfen | Core/Chromium grün; menschliche Abbruchprüfung offen |

**Wichtig:** Dies sind nutzbare Editorfunktionen, keine neue native
SCUMM-v6-Capability. Die nächsten Pakete richten sich wieder nach dem
nativen Spielverhalten und der [Roadmap](roadmap.md).

## Nachweisregeln

- „Untersucht“, „implementiert“, „getestet“ und „in stock ScummVM
  verifiziert“ bleiben unterschiedliche Stufen.
- Ein kompletter Generator wird erst behauptet, wenn die relevanten
  64 Fähigkeiten samt Szenarien nachgewiesen sind.
- Keine neue Task-Kette aus historischen „Nächstes“-Abschnitten ableiten.
- Neue Erkenntnisse einmal hier und in der betroffenen Matrixzeile
  erfassen; lange Chronologie nur im [Archiv](PROJECT_HISTORY.md).
