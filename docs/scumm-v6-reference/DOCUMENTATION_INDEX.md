# Dokumentationsübersicht – Adventure Studio und SCUMM v6

**Hier anfangen.** Die Dateien liegen überwiegend im übergeordneten
[`docs/`-Ordner](../); die Referenzbibliothek unter `docs/scumm-v6-reference/`.
Alle Links führen direkt zum Dokument. Die bestehenden Dateien bleiben an
ihrem Ort, damit bereits verwendete Verweise gültig bleiben.

## 1. Was bauen wir und woran arbeiten wir gerade?

| Dokument | Wofür verwenden? |
| --- | --- |
| [Produktvision](../PRODUCT_VISION.md) | Unveränderliches Ziel: vollständiger nativer SCUMM-v6-Generator. |
| [Projektstatus und nächster Schritt](../PROJECT_STATUS.md) | Aktuelle Übergabe und **das** nächste Arbeitspaket. |
| [SCUMM-v6-Funktionsmatrix](../SCUMM_V6_CAPABILITIES.md) | Einziger Katalog aller 64 Fähigkeiten und ihrer Nachweisstufen. |
| [Roadmap](../roadmap.md) | Abhängigkeiten und Entwicklungsphasen. |
| [Arbeitsvertrag für Agenten](../../AGENTS.md) | Verbindliche Regeln für Entwicklung, Tests und Merges. |

## 2. Technische Referenz: Was kann SCUMM v6?

| Dokument | Schwerpunkt |
| --- | --- |
| [Referenzbibliothek – Startseite](README.md) | Gültigkeit, Quellen, Umgang mit bereits erforschten Funktionen. |
| [Native Grundprimitiven](NATIVE_PRIMITIVES.md) | Script, Scheduler, Kamera, Actor, Costume, Raum, Objekte und Zustände. |
| [SCUMM-v6-Laufzeitvertrag](../scumm-v6-runtime-contract.md) | Grundverhalten der originalen Laufzeitumgebung. |
| [Source-Audit: ScummC und ScummVM](../scumm-v6-source-audit.md) | Opcode-/Interpreterpfade mit Quellcodebelegen. |
| [Frame-Timing und Script-Lifecycle](../scumm-v6-execution-lifecycle.md) | Timing, bewegte Interaktionsobjekte und Room-Wechsel. |
| [Kamera und filmische Inszenierung](../scumm-v6-cinematic-source-audit.md) | Cutscenes, Kamerawechsel, Waits und Überspringen. |
| [Bildkomposition und Compilerpfad](../scumm-v6-compositing-compiler-audit.md) | **Z-Masken, Actor-Tiefe, SCAL, native Zeichnungsreihenfolge.** |
| [Raumressourcen als Binärformat](../scumm-v6-room-resource-binary-audit.md) | RMIM, SMAP, ZPxx, OBIM/OBCD und Offsets. |
| [Writer-/Decoder-Lückenanalyse](../scumm-v6-export-gap-analysis.md) | Was ScummC schreibt, was ScummVM liest und was uns noch fehlt. |

## 3. Welche Spielabläufe muss das Studio ermöglichen?

| Dokument | Schwerpunkt |
| --- | --- |
| [Sechs verbindliche Abnahmeszenarien](SCENARIOS.md) | Autoabfahrt, zeitkritische Achterbahn-Interaktion, Nahaufnahmen, Rätsel, bewegte Hotspots und Verdeckung. |
| [Adventure-Mechaniken](../scumm-adventure-mechanics.md) | Breiterer Mechanikkatalog klassischer Adventures. |
| [Quellenindex je Capability-ID](capability_sources.json) | Maschinenlesbare Zuordnung aller Funktions-IDs zu technischen Belegen. |

## 4. Datenformate, Werkzeuge und Inhalte

| Dokument | Schwerpunkt |
| --- | --- |
| [Room and Export Contract](../room-and-export-contract.md) | **Raum-/Exportvertrag und frühe Toolchain-Annahmen.** |
| [Projektformat](../project-format.md) | Versionierung und JSON-Datenmodell. |
| [Bildgenerierung](../image-generation.md) | Asset-Pipeline, Paletten und Bildquellen. |
| [Audio-Architektur](../audio-architecture.md) | Sound, Musik und offene Integrationsfragen. |
| [Lokalisierung und Kompatibilität](../localization-compatibility.md) | Mehrsprachige Ressourcen und Zeichensätze. |
| [Sprach-/Visual-Checkliste](../scumm-language-visual-checklist.md) | Visuelle Prüfungen der Sprachausgabe. |

## 5. Architekturentscheidungen und Qualitätssicherung

| Dokument | Schwerpunkt |
| --- | --- |
| [Architektur-Audit](../architecture-audit.md) | Auffälligkeiten, künstliche Limits und deren Einordnung. |
| [Architekturverträge](../architecture-contracts.md) | Zuständigkeiten von Fachmodell, Backend und Tests. |
| [ADR-0001: Modell-/Exportgrenzen](../adr/0001-domain-and-export-boundaries.md) | Warum gültige Stories nicht vom Demo-Exporter abhängen dürfen. |
| [ADR-0002: Limits und Belege](../adr/0002-limits-evidence-and-compatibility.md) | Nativ-/Exporter-/Fixture-/UI-Limits und Rückwärtskompatibilität. |

## Orientierung in zwei Schritten

1. **Du möchtest wissen, was zu bauen ist?** Starte bei der
   [Funktionsmatrix](../SCUMM_V6_CAPABILITIES.md) und den
   [Abnahmeszenarien](SCENARIOS.md).
2. **Du möchtest eine Funktion technisch umsetzen?** Nimm ihre ID aus der
   Matrix, den Beleg aus dem [Quellenindex](capability_sources.json) und die
   wiederverwendbare Erklärung aus den [nativen Primitiven](NATIVE_PRIMITIVES.md).
   Nur fehlende Details müssen anschließend im Quellcode nachgeprüft werden.
