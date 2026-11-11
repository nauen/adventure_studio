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
- **Jetzt:** Genau R09 – Verbindungen zwischen mehreren Walkboxen und native BOXM-Next-Hop-Routen im Studio authorieren ([PR #196](https://github.com/nauen/adventure_studio/pull/196), in Prüfung). R08.1 ist mit #194 in `main` gemergt (`7acc7fb3`); NPC-Komfort nach #190 beendet.
- **Abnahme:** R09: echte Studio-Eingabe von Box-Verbindungen → RoomAsset/JSON einschließlich Story-Verknüpfung → BOXM → sichtbarer Unterschied zwischen verbundenen und getrennten Actor-Klickrouten in stock ScummVM. Aktuell Modell-/Export-Core-Tests grün; Browser-/ScummVM-Evidenz noch ausstehend. R08.1-Nachweis: [native CI 43081496152](https://github.com/nauen/adventure_studio/actions/runs/43081496152).
- **Blocker:** R09-ScummVM-Routingvergleich und Chromium-Abnahme auf dem finalen PR-Head ausstehend; erst danach Merge. Allgemeine Mehrboxen-/SCAL-Varianten und #80/#187 bleiben getrennt offen.
- **Danach:** Nach vollständigem R09-Nachweis und Merge genau R10 – Perspektivskalierung (SCAL) im nativen Spiel. Kein paralleles R10-/NPC-Paket.

## Zuletzt tatsächlich geliefert

| PR | Nutzerfunktion | Evidenz/Grenze |
| --- | --- | --- |
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
