# Architektur-Audit: generischer Adventure-Kern vs. Demo-Adapter

Stand: 2026-11-07. **Read-only-Quellcodeprüfung**, keine Migration und kein
Refactoring durchgeführt. Ziel: Rückbauten wegen temporärer
Demo-Grenzen verhindern, ohne eine große hypothetische Engine zu bauen.

## Untersuchte Primärquellen

| Datei | Blob-SHA | Beobachteter Verantwortungsbereich |
| --- | --- | --- |
| [`story.py`](https://github.com/nauen/adventure_studio/blob/main/src/adventure_studio/story.py) | `40c986ee055aa0074e1bada9dcd61f0ef3142ca3` | fachliche Story-Entitäten, Validierung und Solver |
| [`story_document.py`](https://github.com/nauen/adventure_studio/blob/main/src/adventure_studio/story_document.py) | `70eb1721e050b0779e02c606765e315899bd0682` | Story-JSON v1–v4, Parse/Kanonisierung |
| [`scumm_assets.py`](https://github.com/nauen/adventure_studio/blob/main/src/adventure_studio/scumm_assets.py) | `4a99e588a11d357290ce6206bd4fb5026c5cba0` | RoomAsset, Hotspots, ScummC-Quelltext und BMP-Export |
| [`scumm_project.py`](https://github.com/nauen/adventure_studio/blob/main/src/adventure_studio/scumm_project.py) | `a4d74a2b342a23df0f2ac7d70c5f8b95c29d37c6` | GameDocument-JSON v1 und Room-Export |
| [`story_to_scumm.py`](https://github.com/nauen/adventure_studio/blob/main/src/adventure_studio/story_to_scumm.py) | `8db321f3d9515460cd1c6e273d9e015e37804d78` | begrenzter Story-zu-RoomAsset-Adapter |
| [`studio_service.py`](https://github.com/nauen/adventure_studio/blob/main/src/adventure_studio/studio_service.py) | `e8c9bab4e328948914738583a691d8027a1a8bd0` | Editierfassade, Vorschlag und Exportwarnung |
| [`targets.py`](https://github.com/nauen/adventure_studio/blob/main/src/adventure_studio/targets.py) | `263b4620bd256f3ed629cef95451d89cb25a82dd` | Raumgeometrie und Target-Konfiguration |

## 1. Was architektonisch bereits gut gelöst ist

- `Story` verwendet immutable Dataclasses und stabile IDs. Beziehungen
  werden vor Änderungen validiert.
- `story_changes.py` kapselt atomare Änderungsoperationen und Berichte;
  der Editor manipuliert nicht frei generierten SCUMM-Quelltext.
- `story_document.py` akzeptiert explizit Story-Formatversionen 1–4.
  Bestehende Dokumente sind daher nicht einfach unversionierter JSON-Text.
- `RoomAsset` und `GameDocument` trennen indizierte Ressourcenwerte
  von ScummC-Quelltext und Binärdateien.
- Feste Demo-Grenzen schlagen sichtbar mit `ValueError` fehl; bislang
  werden nicht unterstützte Narrative nicht stillschweigend exportiert.
- In `targets.py` heißt es ausdrücklich, dass nicht nachgewiesene
  SCUMM-Limits nicht als vermeintlich allgemeine Engine-Limits
  eingeführt werden sollen.

**Konsequenz:** Kein Totalumbau. Diese Grenzen und Tests sind ein gutes
Fundament, wenn wir die Verantwortlichkeiten sauberer ziehen.

## 2. Gefundene künstliche Grenzen und Risiken

| ID | Stelle | Tatsächliche Begrenzung | Bewertung / Ziel |
| --- | --- | --- | --- |
| F01 | `story_to_scumm.py:243–258` | Exakt ein Kapitel, ein oder zwei lineare Tür-Rätsel, eine unverzweigte Route und 1–3 lokale Pickups je Tür | **Demo-/Adapter-Limit**, nicht die Definition eines SCUMM-Adventures. Allgemeiner Zustands-/Aktionsgraph nötig. |
| F02 | `story_to_scumm.py:19–28, 280–309` | Fixe Palette, höchstens vier Dekoobjekte, fester Layoutabstand und insgesamt begrenzte Pickup-Farben | **Fixture-/Layout-Limit**. Künftig authorbare Platzierung und Palette, keine künstliche Story-Grenze. |
| F03 | `story_to_scumm.py:100–150` | Nur ein linearer Dialog je Actor; begrenzte Zahl an Antworten und Zeilen | **Aktueller Compiler-Limit**. `Story` kennt bereits Dialoggraphen; Export muss folgen, ohne sie auf Hotspots dauerhaft zu reduzieren. |
| F04 | `story.py:165–167` | Item-Placement auf X=0–624/Y=0–184 beschränkt | **Fachmodell leakt Demo-Geometrie**. Positionsgültigkeit gehört zur referenzierten Scene/Room-Geometrie. |
| F05 | `scumm_assets.py:159–168` | 1–3 Antworten je TalkRule, höchstens 16 Öffnungs-/Antwortzeilen | **Compiler-/UI-Limit**, nicht als universelle Gesprächslogik behandeln. Native Zielgrenzen getrennt nachweisen. |
| F06 | `scumm_project.py:94, 122, 137–164, 203` | Bis 64 Räume, 16 Kombi-/Dialog-/Palettenregeln und 16 Anforderungen | **Ungeklärte Herkunft**: SCUMM-Grenze oder Schutzlimit? Mit ScummC/ScummVM belegen, sonst Adapter-Quota. |
| F07 | `scumm_project.py:107` | Genau ein Raum mit `goal_text` | **Demo-Abnahmekonvention**. Normale Spiele brauchen nicht genau einen textmarkierten Endraum. |
| F08 | `studio_service.py:19–27, 62–67` | Editierpfad ruft `compile_story_to_scumm` für Exportwarnung auf; bestimmte unexportierbare Inhalte werden nur warnend behandelt, andere werfen Fehler | **Grenzverletzungsrisiko**: Authoring-Validierung und Exportfähigkeit nicht gleichsetzen. Fachlich gültige Stories müssen speicherbar bleiben. |
| F09 | `scumm_assets.py:19–84, 266+` | RoomHotspot, UseRule, CombineRule, TalkRule bilden einige Gameplay-Fälle direkt im Compilerquelltext ab | **Struktur wachstumsgefährdet**: verifizierte native Effekt-/Bedingungs-IR sinnvoll, bevor weitere Spezialregeln wachsen. |
| F10 | `story.py:58–64, 179–192` | Rezept hat **genau zwei unterschiedliche Zutaten** | **Nicht automatisch ein Fehler**: die native Aktion „A mit B benutzen“ ist binär. Mehrstufige Rezepte können aus mehreren binären Aktionen bestehen. N-äre Sammelbedingungen sind ein anderes Konzept. |

Weitere technische Beschränkungen (8-Pixel-Bildbreite,
Costume-/Z-Plane-Formate, SCUMM-Slotgrenzen) sind **keine**
willkürlichen Limits, sofern durch den Originalcode belegt. Sie bleiben
als Target-Validierung erhalten.

## 3. Architekturrisiken nach Auswirkung

### Hoch: Exportprobe wird zum fachlichen Datenschema

Das Storymodell kann mehrere Kapitel/Szenen und Dialoggraphen ausdrücken,
der Story-zu-SCUMM-Adapter aber nur eine schmale lineare Route. Wenn die
Autorensicht dauerhaft die Probe-Grenzen übernimmt, wächst der Compiler
nicht zu einem vollständigen Adventure-Generator.

**Entscheidung:** Fachlich valide Projekte dürfen gespeichert werden,
auch wenn ihr Export vorläufig nicht unterstützt wird. Der Export liefert
eine **strukturierte Liste unsupported Features** mit Stable IDs,
statt den Story-Inhalt zu beschneiden. Eine spätere Compiler-IR übersetzt
allgemeine Aktionen und Zustandsbedingungen in native SCUMM-Befehle.

### Hoch: Quoten ohne Herkunft

Die Zahlen 3/4/16/64 sind teils bewusst begrenzte Proben. Neue
Versionen sollten solche Quoten mit Namen, Scope und Evidenz führen:
`NATIVE_LIMIT`, `EXPORTER_LIMIT`, `FIXTURE_LIMIT`, `UI_LIMIT`.
Erst ein Quellcode-/Binary-Nachweis macht daraus ein natives Limit.

### Mittel: Zwei verschiedene Projektmodelle

`Story` ist eine semantische Story-Bibel; `GameDocument/RoomAsset` ist
ein exportnaher Zwischenstand. Das ist legitim, aber ein klarer,
typisierter Übergang fehlt für zukünftige Actors, Animationen,
Z-Planes, Trigger und Cutscenes. Die Grenze sollte explizit sein:

`Story / Authoring -> validierte Adventure-IR -> native SCUMM-v6-IR / Assets`.

Diese IR-Stufen sind **vorgeschlagene Verträge**, kein bereits vorhandener
Code und keine Aufforderung, beide sofort zu implementieren.

## 4. Priorisierter Refactoring-Plan – ohne Big Bang

| Reihenfolge | Maßnahme | Sicherer Abnahmevertrag |
| --- | --- | --- |
| A0 | Bestehende Grenzen klassifizieren und in Tests festhalten | Alle F01–F10 haben Typ/Begründung; kein Altprojekt verändert |
| A1 | Exportfähigkeitsbericht von fachlicher Story-Validierung trennen | Fachlich valide Story mit 3 Kapiteln bleibt speicherbar; Export gibt genaue Blocker zurück |
| A2 | Positionsvalidierung an Scene-/Room-Geometrie binden | 320-/640-/größere Room-Tests ohne Demo-Pixelkonstanten im Fachmodell |
| A3 | Native SCUMM-Bedingungs-/Aktions-IR in kleinem vertikalen Paket definieren | Mindestens 1, 3 und 10 Bedingungen; Compile-Ausgabe native v6, keine runtime-erfundene Operation |
| A4 | Story-Adapter von linearen Türen auf expliziten Spielgraphen erweitern | Zwei alternative Routen und mehrere Räume, unveränderte Alt-Fixtures |
| A5 | Native Actor-/Animation-/Cutscene-Authoring-Modelle gemäß Capabilities | Erst nach nativen Compiler-/Ressourcenverträgen |

**Reihenfolge zum nächsten Coding-Paket:** A0 und die Tests der vorhandenen
Grenzen direkt mit P0.1 (Ressourcenparser) verbinden. A1/A2 bei der
nächsten tatsächlichen Änderung des Story-Adapters angehen; kein
großflächiges Umbauen ohne Nutzwert. Das priorisierte P0.1 bleibt das
nächste freigegebene Implementierungspaket.

## 5. Regressionstrategie gegen wiederkehrende Rückbauten

Vor einer Erweiterung erst **Characterization Tests** für die bisherige
Schnittstelle. Dann neue Fälle ergänzen, statt vorhandene zu ersetzen:

- 0/1/2/5/20 Objekte und mehrere Räume (jeweils unter belegten Engine-Limits).
- 1/2/3/10 Bedingungen; zwei binäre Kombinationen hintereinander;
  ein einzelner binärer Use-Verb bleibt weiterhin unterstützt.
- Lineare Route, Verzweigung, Rückweg, unerreichbare Szene.
- Dialog mit 0/1/3/mehr Antworten: vorläufiger Compiler darf präzise
  „nicht unterstützt“ liefern, aber Autorendokument darf nicht verloren gehen.
- JSON v1–v4: Parse/Kanonisierung, identischer semantischer Inhalt,
  bekannte Eingabedokumente bleiben lesbar.
- Gleiche Quellen + Toolchain = gleiche exportierte Datei-Hashes.
- Native Ressourcen- und Script-Gates: Binärparser, ScummC, stock ScummVM.

**Property-/parametrisierte Tests** prüfen Invarianten über viele
Kombinationen. Zahlen müssen beim Target-Export an echten SCUMM-Limits
gemessen werden; Testdaten jenseits der Grenze müssen klar scheitern.

## 6. Nicht entscheiden, bevor weitere Quellen geprüft sind

- Welcher echte SCUMM-v6-Maximalwert für Objekt-/Room-/Skriptressourcen
  gilt, statt der aktuellen 16/64-Probe-Grenzen.
- Welche ursprünglichen Dialog-/Costume-/Kamera-Funktionen durch ScummC
  bereits komplett emitierbar sind.
- Welche bestehende Story-JSON-Version bei Erweiterung migriert werden
  muss: eine Schemaänderung darf nicht stillschweigend `v4` überschreiben.

Siehe [ADR-0001](adr/0001-domain-and-export-boundaries.md) und
[ADR-0002](adr/0002-limits-evidence-and-compatibility.md).
