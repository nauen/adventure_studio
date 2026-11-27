# Adventure Studio – Produktvision und unverrückbares Ziel

Stand: 2026-11-27. Dieses Dokument beschreibt **das Produktziel**, nicht den
aktuellen Implementierungsstand. Für den Stand siehe [PROJECT_STATUS](PROJECT_STATUS.md),
für die technische Abdeckung [SCUMM-v6-Funktionsmatrix](SCUMM_V6_CAPABILITIES.md).

## Ziel

Adventure Studio ist eine Entwicklungsumgebung, mit der Menschen vollständige
klassische Point-and-Click-Adventures erstellen können – mit Spielmechaniken,
Rätseln, Inventar, mehreren Figuren, Dialogen, Animationen, Sound, Musik und
filmisch inszenierten Cutscenes, wie man sie aus SCUMM-v6-Spielen kennt.

**Erstes verbindliches Produktziel:** Ein **vollständiger nativer
SCUMM-v6-Generator**. Er erzeugt originale Spieldaten und Bytecode, die ohne
eine zusätzliche Adventure-Studio-Runtime in ScummVM ausgeführt werden.
ScummC dient als Compiler-/Ressourcen-Referenz und Integrationswerkzeug;
ScummVM als offene Implementierung der Laufzeit. Kompatibilität mit
LucasArts-Originalinterpretern ist ein gesondertes, zu beweisendes Ziel.

Ein einfaches Test-Adventure ist nur ein Entwicklungsmittel. Der Anspruch
ist **nicht**, lediglich Türen, Schlüssel und einige Dialoge zu beherrschen,
sondern typische vollständige Adventures gestalten zu können.

## Konkrete Anwendungserlebnisse

1. **Rätsel erstellen:** Gegenstände kombinieren, Zustände verändern,
   Aktionen in der richtigen Reihenfolge ausführen, Zeitfenster und
   Interaktionen während laufender Animationen definieren.
2. **Welten gestalten:** Räume, Hotspots, begehbare Zonen, Perspektive,
   Vordergrundmasken, bewegliche Objekte, Türen und Übergänge authoren.
3. **Figuren inszenieren:** Actors, Costumes, Lauf-, Sprech- und
   Aktionsanimationen, Reaktionen und mehrere parallele Figuren steuern.
4. **Filmische Sequenzen gestalten:** Totale, Nahaufnahme, Detail,
   Szenenschnitt, Kameraschwenk, Überblendung, Actor-Choreografie,
   Audio-Cues und überspringbare Cutscenes kombinieren.
5. **Spielregeln testen:** Das tatsächlich erzeugte native Spiel starten
   und Spiellogik, Spielzustand sowie Darstellung prüfen.
6. **Später KI-gestützt authoren:** Wünsche in deklarative,
   nachvollziehbare Modelländerungen übersetzen; Menschen behalten
   die Kontrolle über Gestaltung und Freigabe.

## Architekturgrundsätze

- **SCUMM-v6-Kompatibilität ist die technische Grenze.** Filmbegriffe wie
  „Nahaufnahme“ dürfen Editor-Abstraktionen sein, aber keine erfundenen
  Bytecode-Operationen. Jeder exportierte Effekt braucht eine native
  Ressourcen-/Script-Abbildung.
- **Projektmodell als Single Source of Truth:** Stabile IDs,
  versionierte Schemas und nachvollziehbare Referenzen.
- **Deterministischer Export:** Derselbe Projektstand und dieselben
  Toolchain-Versionen erzeugen denselben SCUMM-Output.
- **Editor und KI sind Clients des Modells:** Kein unkontrollierter
  KI-generierter Laufzeitcode und keine separate Spiel-Engine.
- **Echte Nachweise statt grüner Etiketten:** Analyse, Compiler-Erfolg,
  Interpreterstart und funktionierende Spielmechanik sind
  unterschiedliche Evidenzstufen.
- **Spielergebnis vor Infrastruktur:** Neue Technik ist nur dann
  vorrangig, wenn sie eine benötigte Spielfunktion ermöglicht oder
  eine konkrete Kompatibilitätslücke schließt.

## Verbindlicher erster Produktmeilenstein: vollständiges Referenzadventure

Ein über den regulären Adventure-Studio-Autorenworkflow erstelltes,
mehrraumiges Point-and-Click-Adventure mit eigener Grafik, begehbaren
Bereichen, Tiefenwirkung, NPCs, Inventar, Rätseln, Dialogen und einem
erreichbaren Spielende. Es muss als Projekt speicherbar und erneut
bearbeitbar sein und ohne Zusatzruntime in stock ScummVM spielbar sein.
Es ist ein vertikaler Produktnachweis, **keine** Reduktion des langfristigen
SCUMM-v6-Scopes auf ein kleines Testspiel.

Produktprioritäten in dieser Reihenfolge (vorhandene Funktionen nicht
erneut implementieren):

1. Räume mit eigenen Hintergrundbildern gestalten.
2. Begehbare Bereiche, Perspektive, Tiefenebenen und Verdeckung definieren.
3. Räume durch Türen und Übergänge verbinden.
4. Spielfiguren und NPCs platzieren und sinnvoll handeln lassen.
5. Gegenstände, Inventar und kombinierbare Objekte authoren.
6. Rätsel, Bedingungen, Spielvariablen und Konsequenzen definieren.
7. Dialoge und eine zusammenhängende Geschichte gestalten.
8. Das vollständige Adventure exportieren, in ScummVM durchspielen und das Spielende erreichen.

Die Funktionen müssen gemeinsam im normalen Projektworkflow funktionieren.
Eine Spezialfähigkeit (z. B. dynamische Sprechend- oder Initialpose) erhält
erst Priorität, wenn ein konkretes benötigtes Szenario sie voraussetzt.
Die Funktionsmatrix bleibt der technische Katalog, nicht die Aufgabenreihenfolge.

## Reihenfolge der Produktphasen

1. Durchgängiger Autorenworkflow und vollständiges natives Referenzadventure; fehlende Mechaniken und Ressourcenexport bedarfsgerecht ergänzen.
2. Vollständige native SCUMM-v6-Abdeckung und Ausbau des visuellen Editors anhand weiterer konkreter Spielszenarien.
3. Cineastischer Shot-/Cutscene-Editor auf dem nativen Compilervertrag.
4. KI-gestützte, überprüfbare Spielentwicklung.
5. Produktreife und komfortable Distribution.

Vorhandene Arbeiten an KI, UI, Sprachen oder Audio werden nicht
zurückgesetzt. Sie dürfen das **erste Hauptziel** aber nicht verdecken.

## Nicht als erreicht zu behaupten

Die vollständige Engine-Abdeckung, ein fertiger cineastischer Editor,
Originalinterpreter-Kompatibilität oder eine komplette Spielentwicklung
aus natürlicher Sprache sind noch **nicht nachgewiesen**.

Die eigentliche Fortschrittsmessung erfolgt in
[SCUMM_V6_CAPABILITIES.md](SCUMM_V6_CAPABILITIES.md) und den
Akzeptanzkriterien der [Roadmap](roadmap.md).
