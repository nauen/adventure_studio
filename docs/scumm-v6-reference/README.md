# SCUMM-v6-Referenzbibliothek – verbindlicher Generatorvertrag

**Gültig ab 2026-11-07.** Ziel: einmal recherchierte native Semantik für weitere
Adventure-Studio-Features wiederverwenden. **Kein zweiter Funktionskatalog:**
Die 64 stabilen IDs und der Implementierungsstatus stehen ausschließlich in
[`SCUMM_V6_CAPABILITIES.md`](../SCUMM_V6_CAPABILITIES.md). Die
[Produktvision](../PRODUCT_VISION.md) legt das unveränderliche Ziel fest.

**Dokumente finden:** [Thematisch sortierte Dokumentationsübersicht](DOCUMENTATION_INDEX.md)
mit direkten Links zu sämtlichen relevanten Audits und Verträgen –
insbesondere [Bildkomposition](../scumm-v6-compositing-compiler-audit.md)
und [Room/Export](../room-and-export-contract.md).

## Verbindlicher Scope

Adventure Studio erzeugt vollständige klassische Point-and-Click-Adventures
mit **nativen SCUMM-v6-Ressourcen und -Skripten** für die vorhandene
ScummVM-SCUMM-Engine, ohne zusätzliche Adventure-Studio-Runtime.
Benötigt sind Räume/Masken/Walkboxen, Actors/Costumes/Animationen,
Objektzustände/Inventar, Scripts und parallel laufende Aktionen, Dialog,
Audio, Speichern/Laden sowie Kamera- und Cutscene-Choreografie.
Das sind feste Produktanforderungen, **keine optionalen Demo-Ideen**.

SCUMM-v6-Spielvarianten können voneinander abweichen (z. B. *Sam & Max*
gegenüber anderer Verbsteuerung). Eine unterstützte Spielvariante wird im
Target-/Compilervertrag explizit bezeichnet. ScummVM-Verhalten allein
beweist keine Kompatibilität mit dem proprietären LucasArts-Interpreter.

## Bibliotheksstruktur und Autorität

| Ort | Rolle | Verbindlichkeit |
| --- | --- | --- |
| [`SCUMM_V6_CAPABILITIES.md`](../SCUMM_V6_CAPABILITIES.md) | **Einzige** Liste aller Funktions-IDs, Status A/I/T/V und nächsten Gates | Master-Katalog |
| [`capability_sources.json`](capability_sources.json) | Maschinenlesbarer Index: pro ID mindestens ein bestehender Audit-/Vertragsbeleg | Index, keine zweite Statusliste |
| [`NATIVE_PRIMITIVES.md`](NATIVE_PRIMITIVES.md) | Wiederverwendbare Opcode-/Script-/Resource-Semantik mit Voraussetzungen und Grenzen | Technische Designreferenz |
| [`SCENARIOS.md`](SCENARIOS.md) | Typische Spielszenen, Grundbausteine und nachweisbare Abnahme | Produkt-Akzeptanzvertrag |
| Vorhandene `scumm-v6-*-audit.md` | Details mit Quellcodepfad, Blob-SHA und offenen Fragen | Ermittlungs-/Belegarchiv |
| [`PROJECT_STATUS.md`](../PROJECT_STATUS.md) | Tatsächlicher Stand und **ein** nächstes Arbeitspaket | Operative Steuerung |

## Einmal analysieren, vielfach verwenden

1. **ID nachschlagen.** Produktverhalten und Status aus der Funktionsmatrix;
   Quellenpfad über `capability_sources.json`; technische Semantik hier.
2. **Beleg anwenden.** Wenn für die gewünschte Variante eine geprüfte
   ScummC-Signatur, der v6-Interpreterpfad und passende Einschränkungen
   bereits dokumentiert sind, **keine neue allgemeine Engine-Recherche**.
3. **Nur Lücke untersuchen.** Fehlt Encoder, Ressourcenwriter, v6-Abzweig,
   Timing-/Versionsbeweis oder Sonderfall, gezielt diese Stelle lesen und
   den Beleg mit Commit/Blob-SHA ergänzen. Kein hypothetischer Opcode.
4. **Generische Funktion implementieren.** Typisiertes Modell → native
   ScummC-Ressource/Script → deterministischer Strukturtest → für Gameplay
   stock-ScummVM-Prüfung. Kein neues hartkodiertes Szenario als Engine-Ersatz.
5. **Status einmal aktualisieren.** Nur die betreffende Funktionszeile der
   Matrix und das nächste Paket in `PROJECT_STATUS.md` ändern.

## Erkenntnisgrad ist nicht Fertigstellungsgrad

- **A / analysiert:** Quellcode-/Compilerpfad mit Versionsbezug beschrieben.
  Nicht automatisch native Ausgabe oder geprüfte Gameplay-Semantik.
- **I / implementiert:** Die Fähigkeit ist modellseitig authorbar und wird
  als native v6-Daten/Skripte exportiert; Demoproben explizit kennzeichnen.
- **T / getestet:** Der konkrete Vertrag hat einen reproduzierbaren Test.
- **V / verifiziert:** Das exportierte Spiel zeigt die erwartete Interaktion
  in unverändertem ScummVM; CI-Run und Test/Artefakt verlinken.

Ein einzelner Compilerlauf genügt **nicht** für V. Ein bestehender A-Beleg
muss nicht für jeden späteren Editor-Dialog neu analysiert werden. Bei
ScummC-/ScummVM-Versionswechseln oder neuen Zielvarianten ist der Beleg
gezielt erneut zu bewerten.

## Grenz- und Architekturvertrag

- **Domain** modelliert mögliche Adventure-Handlungen, nicht die Grenzen
  eines bisherigen Auto-Layouts. `Use A with B` ist binär; Bedingungen für
  Rätsel dürfen N-är sein.
- **Backend** exportiert nur belegte v6-Befehle. Ein noch nicht tragfähiges
  Target liefert typisierte Export-Blocker; keine stillen Fallbacks.
- **Editor-Shots** sind Kompositionshilfen. Totale/Nahaufnahme werden durch
  native Räume, Bildzustände, Actors, Kamera- und Skriptoperationen umgesetzt,
  **nicht** durch einen erfundenen Zoom-Opcode.
- **Zeitfenster** verwenden echte Spielzustände, Script-Slots und/oder
  Costume-Counter. `waitForAnimation` darf nicht ohne Beleg als Wait auf
  einen beliebigen Costume-Frame interpretiert werden.
- **Prototypen** und native Engine-Grenzen sind nach
  [ADR-0002](../adr/0002-limits-evidence-and-compatibility.md) getrennt.

## Änderungsregel

Neue Mechanik: bestehende ID verwenden; andernfalls ID im Master-Katalog
hinzufügen, Quellenindex ergänzen und eine konkrete Akzeptanzszene angeben.
`tests/test_scumm_reference_contract.py` prüft ID-Vollständigkeit,
existierende Belegdateien und eindeutige Kennungen. Die nächste
Implementierung soll aus einem offenen Szenario/Gate folgen, nicht aus
einem neuen Brainstorming über das Gesamtziel.
