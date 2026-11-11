# Adventure Studio – aktueller Arbeitsstand

Stand: 2026-11-11. **Einstieg für die nächste Arbeitssitzung.**
Produktziel: [PRODUCT_VISION](PRODUCT_VISION.md) · aktive
[Roadmap](roadmap.md) · einzige [SCUMM-v6-Funktionsmatrix](SCUMM_V6_CAPABILITIES.md) ·
[Referenzvertrag](scumm-v6-reference/README.md) · [Arbeitsvertrag](../AGENTS.md).
Das frühere ausführliche Sitzungsprotokoll liegt unverändert in
[PROJECT_HISTORY](PROJECT_HISTORY.md); dessen historische
„Nächstes“-Anweisungen steuern die Entwicklung nicht mehr.

## Ein aktiver Produktpfad

**Jetzt, Priorität 1:** P0.4/O03 – ein zur Laufzeit verschobenes
Objekt muss im nativen Spiel sichtbar sein und an der **neuen** Position
anklickbar bleiben; die alte Hitbox darf nicht weiter reagieren.
Auf vorhandenen Room-Hotspot-/Objektzustandsdaten und dokumentiertem
ScummC-v6-Vertrag aufbauen. Mindestabnahme: allgemeine Modelloperation,
native Ausgabe, automatisierter Strukturtest und echte ScummVM-Klickprobe.

**Blocker/Risiken:**

- Offene native Einzelsprecher-/Mehrsprecher-Animation aus PR #80
  nicht durch grüne Editor-Tests als gelöst deklarieren.
- Menschliche Browser-Abnahme des tatsächlichen Abbrechens beim
  Tab-Verlassen aus PR #187 fehlt; Editor-CI bestätigt bislang nur
  den automatisierbaren Zustand.
- P0.1–P0.3 besitzen bereits Modell-, Export- und native Teilnachweise,
  sind aber nicht pauschal vollständig. Die früheren offenen Checkboxen
  sind kein Grund, diese Grundlagen neu zu implementieren.

## Zuletzt tatsächlich geliefert

| PR | Nutzerfunktion | Evidenz/Grenze |
| --- | --- | --- |
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
