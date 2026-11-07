# Architekturverträge und Entwicklungsgates

Stand: 2026-11-07. Dieses Dokument legt **Grenzen und Verantwortung**
fest. Es ist keine Behauptung, dass die vorgeschlagene Adventure-IR
bereits implementiert ist. Quellen:
[Architekturaudit](architecture-audit.md),
[ADR-0001](adr/0001-domain-and-export-boundaries.md) und
[ADR-0002](adr/0002-limits-evidence-and-compatibility.md).

## Verantwortungsgrenzen

| Ebene | Aufgabe | Darf nicht |
| --- | --- | --- |
| Authoring/Studio/KI | Spielideen, Story-Entitäten und editierbare Parameter | SCUMM-Codefragmente als einziges Wahrheitsmodell speichern |
| Fachliches Adventure-Modell | stabile IDs, Beziehungen, Zustände, Regeln | zeitweilige Demo-/Layout-Grenzen als Weltgesetz festlegen |
| Fachliche Validierung | Referenzintegrität, fachliche Regeln, Zyklus-/Erreichbarkeit | Exportfähigkeit mit Storygültigkeit verwechseln |
| Adventure-IR (geplant) | explizite Bedingungen, Aktionen, Effekte, Ereignisse | eigene Runtime-Semantik erfinden |
| SCUMM-v6-Backend | native Opcode-/Resource-Zuordnung | nicht belegte v6-Opcodes oder stilles Weglassen |
| ScummC-/Toolchain | Quelltext kompilieren/linken, Ressourcen schreiben | Editorzustand mutieren |
| Tests/ScummVM | Format-, Rendering- und Gameplay-Nachweise | aus einem grünen Fixture auf volle Abdeckung schließen |

## Stabilitäts- und Erweiterungsvertrag

- IDs bleiben stabil; Referenzen dürfen beim Umbau nicht stillschweigend
  auf andere Objekte zeigen.
- 0, 1, 2 und viele Elemente müssen modellseitig sinnvoll sein, soweit
  dies fachlich möglich und nicht durch native Grenzen ausgeschlossen ist.
- Zusätzliche Bedingungen, Actor- oder Objektzustände werden als Daten
  ergänzt; nicht als neue hardkodierte Sonderfallfunktion pro Demo.
- Validierungsfehler nennen Zielprofil, betroffene ID und konkrete Grenze.
- Limit-Kategorien nach ADR-0002; native Limits mit Quellcodebeleg.
- JSON-Schema-Versionierung und Abwärtskompatibilität vor Feldänderungen.

## Entwicklungsdefinition „fertig“

1. Verhalten und SCUMM-v6-Quelle benannt.
2. Modelländerung und Exportpfad beschrieben.
3. Characterization Tests für Altverhalten vorhanden.
4. Tests für 0/1/2/N und Grenze + 1, soweit sinnvoll.
5. Compiler-Strukturtest, bei Gameplay außerdem stock-ScummVM-Test.
6. Keine stillen Fallbacks oder für den Nutzer unsichtbares Weglassen.
7. Dokumentation, Capabilities und Status aktualisiert.

## Beispiele für vertikale Entwicklung

**Z-Masken:** RoomAsset erhält Z-Plane-Daten; Validator prüft
Dimensionen/Indizes; ScummC-Backend schreibt native Maskenquellen;
ein Binärparser prüft ZPxx; ein ScummVM-Fixture zeigt Verdeckung.

**Komplexes Rätsel:** Fachliche Bedingungen und Effekte werden
typisiert; der Compiler bildet sie auf native Skriptvariablen,
Inventory-/Object-Opcodes ab; mehrere Szenen und Rückwege behalten
ihre Zustände. Keine Beschränkung auf „Tür mit drei Schlüsseln“ im
allgemeinen Datenmodell.

**Cutscene:** Shots sind Editor-Daten. Die Ausgabe besteht aus
Räumen, Kamera-Opcodes, Costume- und Scriptabläufen. Skip-Endzustand
und Script-Lifetime sind Teil der Akzeptanzkriterien.

## Review-Praxis

Die [Pull-Request-Vorlage](../.github/pull_request_template.md)
fragt diese Regeln ab. Auch bei selbstständigen Merges ist der
Check vor der Freigabe durchzuführen. Für Dokumentationsänderungen
ohne Laufzeitänderung genügt die Markierung „nicht anwendbar“
bei Gameplay-Gates; Test-Erfolg wird nicht erfunden.
