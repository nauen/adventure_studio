# Adventure Studio – aktueller Arbeitsstand

Stand: 2026-11-12. **Einstieg für die nächste Arbeitssitzung.**
Produktziel: [PRODUCT_VISION](PRODUCT_VISION.md) · aktive
[Roadmap](roadmap.md) · einzige [SCUMM-v6-Funktionsmatrix](SCUMM_V6_CAPABILITIES.md) ·
[Referenzvertrag](scumm-v6-reference/README.md) · [Arbeitsvertrag](../AGENTS.md).
Das frühere ausführliche Sitzungsprotokoll liegt unverändert in
[PROJECT_HISTORY](PROJECT_HISTORY.md); dessen historische
„Nächstes“-Anweisungen steuern die Entwicklung nicht mehr.

## Ein aktiver Produktpfad

- **Hauptziel:** Vollständiger originaler SCUMM-v6-Generator mit echtem Gameplay in unverändertem ScummVM, ohne zusätzliche Adventure-Studio-Runtime.
- **Jetzt:** **R06: gleichzeitige ZP01-/ZP02-Verdeckung** im produktiven Studio-/ScummC-/BOXD-/stock-ScummVM-Pfad nach [PR #220](https://github.com/nauen/adventure_studio/pull/220) gemergt (`15b55685`). Zwei unabhängige PNG-Masken in benachbarten Walkboxen, Klicknavigation zur Mitte und zurück zum Fernziel; NPC-Komfort bleibt seit #190 beendet.
- **Abnahme:** PR #220 (Squash `15b55685`): [nativer Push-Lauf 43290193684](https://github.com/nauen/adventure_studio/actions/runs/43290193684) und [PR-Retry 43290206567](https://github.com/nauen/adventure_studio/actions/runs/43290206567) jeweils 100/100 Schritte grün auf finalem Head `a4dc8c3`; [Screenshots, vier Studio-JSONs und Pixelreport](https://github.com/nauen/adventure_studio/actions/runs/43290193684/artifacts/13975459593). Realer Actor im gleichen Spiel: transparent Mitte/Ferne/Rückweg `1440/1528/1128`, ZP01 allein `100/1436/1128`, ZP02 allein `1440/0/24`, simultan `100/0/24`; `native_simultaneous_room_masks_passed=true`; JSON/Story- und BOXD-Maskenindizes `[0,1,2]` belegt. Core `43290193837`/`43290206880` grün.
- **Blocker:** R06 bleibt Teilfähigkeit: maximal ZP01–ZP04 stock-v6-nativ renderbar, ZP05+ explizit vor dem Schreiben verweigert (#218). Drei oder vier unterschiedliche Masken **simultan** noch nicht nativ geprüft. Erster #220-PR-Gesamtlauf scheiterte an unveränderter PNG-Actor-Frame-Abtastung; unveränderter Retry 100/100 grün. Frühere Screenshot-/Timing-Fluktuationen weiterhin dokumentiert, keine Gate-Abschwächung. R07-Objektbilder und NPC-PR #80 getrennt offen.
- **Danach:** Genau **ein** Folgepaket: **R06 – drei unterschiedliche gleichzeitig aktive Studio-PNG-Z-Masken ZP01/ZP02/ZP03 auf drei verbundenen Walkboxen in einem exportierten Spiel. Modell/JSON/Story und BOXD-Maskenindizes 1/2/3 erhalten; Actor besucht alle drei Verdeckungsbereiche in einem stock-ScummVM-Spielprozess und läuft zurück. Vergleich mit transparenten beziehungsweise einzeln aktiven Masken; kein ZP05+, kein NPC-Komfort, kein zweites Featurepaket.**

## Zuletzt tatsächlich geliefert

| PR | Nutzerfunktion | Evidenz/Grenze |
| --- | --- | --- |
| [#220](https://github.com/nauen/adventure_studio/pull/220) | Zwei unterschiedliche Studio-PNG-Raum-Z-Masken ZP01/ZP02 gleichzeitig auf benachbarten Walkboxen; navigierbarer Actor bis Fernziel, Mitte und zurück | Stock-ScummVM-Push 43290193684 und unveränderter PR-Retry 43290206567 je 100/100 grün, Screenshots/Pixelreport Artifact 13975459593, vier Kontrollspielvarianten; Core 43290193837/43290206880 grün; Squash `15b55685`. Zwei simultane Ebenen belegt, R06 bleibt Teilfähigkeit |
| [#218](https://github.com/nauen/adventure_studio/pull/218) | Stock-v6-Z-Maskenexport verweigert ZP05+ beziehungsweise Walkbox-Maskenindex >4 mit raumbezogenem Fehler, ohne Teildateien; Studio-/JSON-Projekte mit fünf Ebenen bleiben verlustfrei editierbar | Core `43282575317` / Dialog `43282575394` grün; nativer PR-Lauf `43282575410` im Retry **98/98 grün**. [Artifact 13972832770](https://github.com/nauen/adventure_studio/actions/runs/43282575410/artifacts/13972832770): transparente Kontrolle 1556, ZP01–04 je 0 Actor-Pixel; fünfte PNG im Modell erhalten, Export abgewiesen ohne Dateien. Squash `45270469`. Ältere Bildabtastungsfehler unverändert dokumentiert; ZP05 **nicht** nativ funktionsfähig | 
| [#214](https://github.com/nauen/adventure_studio/pull/214) | Sechs Walkboxen als Zyklus verbinden; unterbrochenen Weg nativ umgehen und bei zwei Trennungen sichtbar stehen bleiben | [ScummVM Run 43276225187](https://github.com/nauen/adventure_studio/actions/runs/43276225187) / [Artifact 13969904348](https://github.com/nauen/adventure_studio/actions/runs/43276225187/artifacts/13969904348): positive Actor-Pixel am Ziel je 1556 (voll/oben getrennt/unten getrennt), blockiert 1612 im Nahbereich; zwei native Gesamtläufe je 98/98 grün, Core 43276225269 grün, Squash `911a3976`. R09 bleibt Teilfähigkeit | 
| [#212](https://github.com/nauen/adventure_studio/pull/212) | Fünf Walkboxen als T-Netz verbinden; Spielfigur erreicht in **einem** ScummVM-Spielprozess zwei unterschiedliche Ziele und läuft zurück | Positiv: Ziel oben 1464, unten 1272, oben erneut 1304 dunkle Actor-Pixel; abgetrennte `3-5`-Kante: unten nur 142 Pixel. [Artifact 13968093482](https://github.com/nauen/adventure_studio/actions/runs/43272211665/artifacts/13968093482), Core 43272211675 / Dialog 43272211687 / native 43272211665 98/98 grün; Squash `a09592c4`. R09 bleibt Teilfähigkeit; älterer SCAL-Push-Flake dokumentiert | 
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
