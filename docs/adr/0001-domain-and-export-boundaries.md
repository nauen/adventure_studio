# ADR-0001: Fachmodell, Adventure-IR und native SCUMM-v6-Grenze

- **Status:** Angenommen als Architekturleitlinie, 2026-11-07.
- **Betroffen:** Story-Editor, Validator, Story-to-SCUMM-Adapter, Compiler.

## Kontext

`Story` kann mehr Inhalte ausdrücken als der bisherige
`compile_story_to_scumm`-Adapter exportiert. Der Adapter unterstützt
heute bewusst nur kleine lineare Tür-/Inventar-Demos. Werden dessen
Grenzen in die fachliche Authoring-Schicht verschoben, folgen
später aufwendige Rückbauten.

## Entscheidung

1. Das fachliche Story-/Adventure-Modell definiert **mögliche
   Adventures** und deren referenzielle Gültigkeit. Es übernimmt
   keine willkürlichen Grenzen eines Demo-Layouts.
2. Exportfähigkeit ist **ein eigener, maschinenlesbarer Bericht**
   mit Feature-ID, betroffener Entität, Zielprofil und Grund.
3. Gameplay-Logik wird schrittweise in einer typisierten,
   deterministischen Adventure-IR mit Bedingungen, Aktionen,
   Effekten und stabilen IDs ausgedrückt.
4. Die SCUMM-Backend-Grenze bildet nur **belegte native v6-Operationen
   und Ressourcen** ab. Unbekannte Mechanik bedeutet einen
   ausdrücklichen Exportfehler, nicht generierte Fantasie-Bytecodes.
5. Der bestehende Adapter bleibt zunächst funktionsfähig;
   die IR wächst in vertikalen Features. Kein Big-Bang-Rewrite.

## Warum keine alles-könnende generische Engine?

Das Ziel ist eine bessere Authoring- und Compiler-Struktur,
**nicht** eine alternative Runtime. Die IR ist ein typisierter
Kompilierungsvertrag, kein eigenständiges Ausführungsmodell mit
frei erfundenen Semantiken.

## Konsequenzen

- Mehrstufige Rätsel werden als Zustand, Bedingungen und native
  Aktionen modelliert. `Use A with B` kann weiterhin ein binärer
  Operator sein; N-äre Anforderungen gehören zu Bedingungen.
- Ein unexportierbares, fachlich gültiges Projekt bleibt editier-
  und speicherbar. Im Export werden präzise Blocker angezeigt.
- Vor der Änderung bestehender JSON-Strukturen wird die Schema-
  Versionierung und Migrationsstrategie geprüft.
- Codeänderungen müssen bisherige Fixtures erhalten und zusätzlich
  breitere Fälle testen.

## Alternativen

- **Demo-Modell weiter ausbauen:** kurzfristig einfach, führt erneut
  zu Sonderregeln und Rückbau.
- **Große neue Universalengine:** unnötige Laufzeitkomplexität und
  Risiko der SCUMM-Inkompatibilität.

## Abnahmekriterien für die spätere Implementierung

1. Ein fachlich gültiges, noch nicht exportierbares Projekt wird
   ohne Datenverlust bearbeitet und gespeichert.
2. Der Exportbericht benennt alle bekannten Blocker ohne
   Quelltext-Hacks oder Ausnahme-Textanalyse.
3. Ein bestehendes lineares Adventure exportiert unverändert.
4. Eine neue native Mechanik lässt sich ergänzen, ohne bestehende
   `Story`-/`RoomAsset`-Felder umzudeuten.
