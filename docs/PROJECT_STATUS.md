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
- **Jetzt:** Nach #190–#193 liefert [PR #194](https://github.com/nauen/adventure_studio/pull/194) genau R08.1 – eine frei authorierte konvexe Vierpunkt-Walkbox in Studio, JSON und nativem BOXD. NPC-Komfort beendet.
- **Abnahme:** [Native Run 43079024249](https://github.com/nauen/adventure_studio/actions/runs/43079024249) grün: raumweite Box erreicht die entfernte Raumhälfte, begrenzte Box verhindert den Übergang; Actor links mit 1.612 Pixeln sichtbar. [Evidenzartefakt](https://github.com/nauen/adventure_studio/actions/runs/43079024249/artifacts/13884270940). Echter Chromium-Authoring-/Export-/Reimport-Test und Core grün.
- **Blocker:** Allgemeine R08-Polygonvarianten und Mehrboxennetze/R09 nicht belegt; PR #194 bis Gesamt-CI/Merge offen. #187-Tab-Abbruch und #80-Mehrsprecher bleiben separat.
- **Danach:** Genau R09 – native BOXM-Verbindungen und Laufwege mehrerer Walkboxen; R10/SCAL und O03 nachgeordnet.

## Zuletzt tatsächlich geliefert

| PR | Nutzerfunktion | Evidenz/Grenze |
| --- | --- | --- |
| [#194](https://github.com/nauen/adventure_studio/pull/194) | Freie konvexe Walkbox im Studio authorieren und als native Actor-Laufgrenze verwenden | Native `43079024249` grün; freier/gesperrter Zielraum im stock ScummVM unterschieden; R08.1, **nicht** alle R08/R09-Varianten; Merge ausstehend |
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
