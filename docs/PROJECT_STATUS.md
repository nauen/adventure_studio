# Adventure Studio – aktueller Arbeitsstand

Stand: 2026-11-12. **Einstieg für die nächste Arbeitssitzung.**
Produktziel: [PRODUCT_VISION](PRODUCT_VISION.md) · aktive
[Roadmap](roadmap.md) · einzige [SCUMM-v6-Funktionsmatrix](SCUMM_V6_CAPABILITIES.md) ·
[Referenzvertrag](scumm-v6-reference/README.md) · [Arbeitsvertrag](../AGENTS.md).
Das frühere ausführliche Sitzungsprotokoll liegt unverändert in
[PROJECT_HISTORY](PROJECT_HISTORY.md); dessen historische
„Nächstes“-Anweisungen steuern die Entwicklung nicht mehr.

## Ein aktiver Produktpfad

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator mit realem stock-ScummVM-Spielverhalten.
- **Jetzt:** Genau R06.3 – dritte separat authorierte Raum-Z-Maske ZP03 mit BOXD-Index 3 und sichtbarer Actor-Verdeckung in stock ScummVM abnehmen. R08.2 PR #202 (`58022c5`) und Konsolidierung PR #203 (`be255329`) sind gemergt; keine NPC-Komfortarbeit.
- **Abnahme:** Studio-ZP01/ZP02/ZP03 → Projekt-JSON/Story → natives ScummC ZP01/ZP02/ZP03 und BOXD → drei getrennte Maskenvarianten plus transparenter Kontrollfall in unverändertem ScummVM. Core- und native CI auf dem finalen Head müssen grün sein; R06.3-Implementierung der Gegenprobe ist eingereicht, native Evidenz noch offen.
- **Blocker:** Stock-ScummVM-Gegenprobe für die dritte Ebene und die finalen Pflichtchecks stehen aus. Die bereits vorhandene Eingabe von Maskennummern ist kein neues Produktfeature.
- **Danach:** Erst nach vollständiger R06.3-Abnahme die nächste einzelne native Raum-/Walkbox-/Z-Maskenlücke bearbeiten.

## Zuletzt tatsächlich geliefert

| PR | Nutzerfunktion | Evidenz/Grenze |
| --- | --- | --- |
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
