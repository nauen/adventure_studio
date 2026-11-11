# Adventure Studio – aktueller Arbeitsstand

Stand: 2026-11-11. **Einstieg für die nächste Arbeitssitzung.**
Produktziel: [PRODUCT_VISION](PRODUCT_VISION.md) · aktive
[Roadmap](roadmap.md) · einzige [SCUMM-v6-Funktionsmatrix](SCUMM_V6_CAPABILITIES.md) ·
[Referenzvertrag](scumm-v6-reference/README.md) · [Arbeitsvertrag](../AGENTS.md).
Das frühere ausführliche Sitzungsprotokoll liegt unverändert in
[PROJECT_HISTORY](PROJECT_HISTORY.md); dessen historische
„Nächstes“-Anweisungen steuern die Entwicklung nicht mehr.

## Ein aktiver Produktpfad

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator mit realem stock-ScummVM-Spielverhalten.
- **Jetzt:** R08.1 ist mit [PR #194](https://github.com/nauen/adventure_studio/pull/194) in `main` integriert (Squash-Merge `7acc7fb3`). Nach #190 und Konsolidierung #191/#192 sowie PNG-Z-Maske #193 sind NPC-Komfortpakete beendet.
- **Abnahme:** Frei authorierte konvexe Vierpunkt-Walkbox: Editor → RoomAsset/JSON einschließlich Story-Verknüpfung → BOXD → in stock ScummVM sichtbare Actor-Laufgrenze. [Native CI 43081496152](https://github.com/nauen/adventure_studio/actions/runs/43081496152), [Chromium CI 43081496021](https://github.com/nauen/adventure_studio/actions/runs/43081496021), Core und Dialog grün.
- **Blocker:** R08.1 selbst ohne offenen CI-Blocker. Beliebige Polygone, Mehrboxennetze, automatische BOXM-Routen und allgemeine SCAL-Varianten bleiben unbewiesen; menschliche #187-Abnahme und #80 bleiben separat offen.
- **Danach:** Genau R09 – authorierbare Verbindungen zwischen mehreren Walkboxen → BOXM → echte Actor-Klickrouten in stock ScummVM. Kein paralleles R10-/NPC-Paket.

## Zuletzt tatsächlich geliefert

| PR | Nutzerfunktion | Evidenz/Grenze |
| --- | --- | --- |
| [#194](https://github.com/nauen/adventure_studio/pull/194) | Freie konvexe Walkbox im Studio authorieren und als native Actor-Laufgrenze verwenden | Native `43079024249` grün; freier/gesperrter Zielraum im stock ScummVM unterschieden; R08.1, **nicht** alle R08/R09-Varianten; Merge ausstehend |
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
