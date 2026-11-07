# ADR-0002: Limit-Klassen, Evidenzstufen und Abwärtskompatibilität

- **Status:** Angenommen als Qualitätsleitlinie, 2026-11-07.
- **Betroffen:** Modellvalidierung, Compiler, Tests, CI, GitHub-Reviews.

## Kontext

Im Bestand stehen Limits wie zwei Tür-Rätsel, höchstens drei
Pickup-Farben, vier Dekoobjekte, drei Antworten, 16 Regeln und
64 Räume. Einige sind Demo-/Layout-Schranken, andere könnten
echten SCUMM-Constraints entsprechen. Ohne Herkunftsnachweis
wirken temporäre Grenzen wie allgemeine Architektur.

## Entscheidung

Jede Mengen- oder Formatgrenze erhält genau eine Klasse:

| Klasse | Bedeutung | Behandlung |
| --- | --- | --- |
| `NATIVE_LIMIT` | in ScummC/ScummVM/v6-Ressourcen nachgewiesen | im Target-Validator zwingend |
| `EXPORTER_LIMIT` | Backend unterstützt nur Teilumfang | Blocker beim Export, kein fachliches Verbot |
| `FIXTURE_LIMIT` | Testmaterial/Layout ist begrenzt | nur im entsprechenden Fixture/Probe |
| `UI_LIMIT` | Bedienoberfläche zeigt noch nicht alle Daten | UI-Hinweis, kein Datenverlust |
| `DOMAIN_RULE` | fachlich notwendige Invariante (z. B. binäres Use) | im Fachmodell mit Begründung |

Kein festes Limit darf ohne Herkunft/Scope in eine allgemeine
Adventure-Modellvalidierung übernommen werden.

## Qualitätstore

1. **Quellcode:** Native Funktion/Format mit Datei und Version belegt.
2. **Modell:** Gültige und ungültige Konfigurationen typisiert geprüft.
3. **Compiler:** Struktur- und deterministische Exporttests.
4. **Laufzeit:** Relevante Funktion im exportierten Spiel mit
   stock ScummVM nachgewiesen.
5. **Regression:** Vorhandene Beispiele/JSON-Versionen funktionieren
   weiterhin oder bekommen eine explizite Migration.

Bei einem nicht ausgeführten Gate lautet der Status „offen“, nicht
„bestanden“. Einzelne Tests für ein Demo zählen nicht als
allgemeine Engine-Abdeckung.

## Backward Compatibility

- Keine Feldumdeutung in bestehenden JSON-Versionen.
- Neue semantische Felder erhalten einen neuen Formatvertrag oder
  eine rückwärtskompatible optionale Erweiterung mit Tests.
- Alte v1–v4-Story-Dokumente und GameDocument-v1-Projekte
  gehören zur Regression-Suite.
- `parse -> canonical -> parse` muss identische relevante
  Spielsemantik erhalten. Der gewünschte Versionswechsel ist
  explizit zu testen.
- Vor einer Änderung Test-Fixtures aufbewahren und danach
  alte wie neue Varianten prüfen.

## Entscheidung für das Entwicklungstempo

Wir behalten **kleine vertikale Arbeitspakete** bei. Vor deren
Implementierung sind aber die voraussichtlich benötigten
fachlichen Fälle und die vorhandenen Engine-Grenzen bekannt.
Kein Big-Bang-Refactoring allein zur theoretischen Generalisierung.

## Abnahme

Ein PR mit verändertem Modell oder Export enthält:

- Welche neuen SCUMM-v6-Fähigkeiten unterstützt werden.
- Welche Grenzen nativ/fachlich/temporär sind.
- Tests für kleine, größere und ungültige Eingaben.
- Nachweis alter Projektformate und vorheriger Gameplay-Fixtures.
- Explizite Aktualisierung von `SCUMM_V6_CAPABILITIES.md`
  und `PROJECT_STATUS.md`, sofern sich der Stand geändert hat.
