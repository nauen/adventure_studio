# Adventure Studio – aktueller Arbeitsstand

Stand: 2026-11-11. **Einstieg für die nächste Arbeitssitzung.**
Produktziel: [PRODUCT_VISION](PRODUCT_VISION.md) · aktive
[Roadmap](roadmap.md) · einzige [SCUMM-v6-Funktionsmatrix](SCUMM_V6_CAPABILITIES.md) ·
[Referenzvertrag](scumm-v6-reference/README.md) · [Arbeitsvertrag](../AGENTS.md).
Das frühere ausführliche Sitzungsprotokoll liegt unverändert in
[PROJECT_HISTORY](PROJECT_HISTORY.md); dessen historische
„Nächstes“-Anweisungen steuern die Entwicklung nicht mehr.

## Ein aktiver Produktpfad

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator, nachgewiesen am tatsächlichen Spielverhalten.
- **Jetzt:** [PR #190](https://github.com/nauen/adventure_studio/pull/190) für atomare NPC-Sprechentwurfsübernahme abschließen, danach [PR #191](https://github.com/nauen/adventure_studio/pull/191) konsolidieren. Kein weiteres NPC-Komfortpaket. #190 ändert keine v6-Opcodes und begründet daher keinen neuen nativen Capability-Abschluss.
- **Abnahme:** Als **genau eine** native Fähigkeit R06 – vom frei authorierbaren Raum-Z-Masken-Modell über ZPxx-Export bis zur Actor-Verdeckung im unveränderten ScummVM, einschließlich automatisierter relevanter Modell-/Binärprüfung und echter Spielprobe. Die vorhandene Verdeckungs-Fixture ist nur Teilnachweis.
- **Blocker:** CI von #190 noch nicht vollständig abgenommen (Core grün, Chromium-/Dialog-Gates bei letzter Prüfung offen); #187 benötigt weiterhin die menschliche Tab-Abbruchprüfung. #80 bleibt für native Einzel-/Mehrsprecher-Animation offen. Bei R06 fehlende allgemeine Authoring- oder Gameplay-Evidenz explizit dokumentieren.
- **Danach:** R08 – frei authorierbare Walkbox-Polygone mit BOXD und realen Actor-Laufgrenzen. R09/R10 und O03 erst später und separat.

## Zuletzt tatsächlich geliefert

| PR | Nutzerfunktion | Evidenz/Grenze |
| --- | --- | --- |
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
