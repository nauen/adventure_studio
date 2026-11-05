# Adventure Studio – Produkt- und Entwicklungsroadmap

Stand: 2026-11-04. Dieses Dokument ist die Arbeitsgrundlage für die Umsetzung.

## Produktziel

Eine storyorientierte, KI-gestützte Entwicklungsumgebung für Point-and-Click-
Adventures. Nutzer beschreiben und ändern Handlung, Kapitel, Räume, Figuren,
Gegenstände, Dialoge und Rätsel in natürlicher Sprache. Adventure Studio hält
ein einheitliches, strukturiertes Projektmodell, prüft Änderungen
deterministisch und erzeugt **originale SCUMM-v6-Spieldaten**. Das primäre
Laufzeitziel ist ScummVM; klassische DOS-Interpreter sind optional und werden
gesondert geprüft. AGS ist kein Ausgabeformat.

## Architekturinvarianten

1. **Eine Datenquelle:** Die Story und der Spielzustand liegen in einem
   versionierten, typisierten Modell; Grafiken referenzieren stabile IDs.
2. **Kein KI-generierter Laufzeitcode:** KI-Ausgaben sind deklarative und
   validierte Modelloperationen. Ein deterministischer Compiler erzeugt SCUMM.
3. **Atomare Änderungen:** Entwurf, Vorher/Nachher-Diff, Referenzprüfung,
   Erreichbarkeitsanalyse, Konsolidierung und erst danach Commit.
4. **Bereinigung mit Transparenz:** Verwaiste Daten werden ausgewiesen;
   sicher automatisch löschbare Daten können entfernt werden. Inhaltlich
   relevante Elemente werden nicht stillschweigend gelöscht.
5. **Reproduzierbarkeit:** Gleiche Projekt- und Toolchain-Versionen müssen
   identische exportierte Ressourcen erzeugen. Alle Compilergrenzen haben Tests.
6. **Ehrliche Kompatibilität:** Asset-Generierung, Binärlinking, Erkennung,
   Spielstart, grafische Darstellung, Interaktion, Scrolling und Save/Load
   sind unabhängige Gates. Ein grüner Workflow allein ist kein Gameplay-Beweis.
7. **Grenzflächen statt Spaghetti:** UI, KI-Adapter, Modell, Validierung,
   Ressourcen-Generator und SCUMM-Exporter bleiben voneinander getrennt.

## Meilensteine und Akzeptanzkriterien

### M0 – Technisches Fundament (teilweise abgeschlossen)

- [x] Typisierte Zustands-/Storymodelle, atomare Änderungen und Tests.
- [x] SCUMM-v6-Ressourcen aus deterministisch erzeugtem Bitmap/Raumskript.
- [x] Compiler und Linker über ScummC in CI erfolgreich ausgeführt.
- [x] ScummVM startet eine separate DOTT-Kompatibilitäts-Testvariante.
- [ ] Eigene Erkennung in unveränderter ScummVM (separater Kompatibilitätsblocker).

### M1 – Spielbarer Raum (aktiv)

- [ ] Spielfigur ist sichtbar und animiert.
- [ ] Spielfigur kann kontrolliert laufen; Walkboxes und Grenzen funktionieren.
- [ ] Zwei Bildschirmbreiten werden korrekt horizontal gescrollt.
- [ ] Ein Gegenstand erscheint an der richtigen Position und hat einen Hotspot.
- [x] Erster eigener Gegenstand wird als SCUMM-Bitmap gerendert und im
      Kamerabild nachgewiesen (goldener Schlüssel; Pixelprüfung integriert).
- [x] Automatisierte Screenshots belegen zwei verschiedene Kamerapositionen
      (CI-Lauf #41850260115: Blau-zu-Orange-Marker, 92 428 geänderte Pixel).
- [x] Konsolenlogs und Screenshot-Artefakte stehen in GitHub Actions zur Verfügung.

### M2 – Geschlossenes Mini-Adventure

- [x] Schlüssel aufnehmen, ins Inventar übertragen und visuell bestätigen
      (CI-Lauf #41863693962).
- [x] Verschlossene Tür, Schlüsselprüfung, sichtbarer Offen-Zustand und
      separater Klick für den Raumwechsel (CI-Lauf #41876135550).
- [x] Teilziel: deklarative `UseRule` kompiliert und echtes „Use Key with Door“
      entfernt den Tür-Sprite in ScummVM (CI-Lauf #41870570921).
- [x] Teilziel: echtes `startRoom(Cellar)` und sichtbarer Zielraum in stock
      ScummVM nachgewiesen (CI-Lauf #41872141558).
- [x] Deklaratives Ziel „Keller erreichen“, genau ein Zielraum und prüfbares
      Zielmanifest (`game-goal.json`); lokale Validierung und Tests grün.
- [x] Zielmanifestauswertung und Zielraum in ScummVM-CI bestätigt
      (CI-Lauf #41876135550); Abschlussdialog wird kompiliert, aber nicht
      gesondert als Textinhalt aus dem Frame erkannt.
- [x] Geöffnete Tür und aufgenommener Schlüssel bleiben beim Verlassen und
      erneuten Betreten des Hafens erhalten (CI-Lauf #42020306920).
- [ ] Save/Load erhält diese Zustände; bislang nicht geprüft.
- [x] Negativfall „verschlossene Tür ohne Schlüssel“ im Gameplay-Test sowie
      Softlock-Erkennung im deterministischen Story-Solver geprüft.

### M3 – Adventure aus Daten

- [ ] Vollständiges M2-Beispiel ausschließlich aus dem Projektmodell exportieren.
- [ ] Keine projektindividuellen handgeschriebenen Runtime-Skripte nötig.
- [x] Zwei unterschiedliche SCUMM-Raumprojekte aus denselben Generatorbausteinen
      bauen (Datenmodell- und Dateivergleichstest sowie Story-JSON-Variante in
      stock ScummVM gestartet: CI-Lauf #42020306920).
- [x] Kanonisches JSON-Projektformat v1 mit deterministischem Export,
      strikter Feldprüfung und Dokumentation (`docs/project-format.md`).
- [x] Erster begrenzter Story-zu-SCUMM-Adapter: Kapitel, zwei Szenen,
      Schlüssel, Dekoration, Tür-Rätsel und Zielraum werden ohne Rohgrafikdaten
      des Autors übersetzt (`story_to_scumm.py`, lokale Tests).
- [x] Versionierter Story-JSON-Eingang mit strikter Validierung, kanonischem
      Export und bytegleichen Wiederholungs-Builds (`story_document.py`).
- [x] Bis zu drei erforderliche Inventargegenstände werden als deklarative
      Inventarbedingungen und automatisch abgeleitete Icon-Ressourcen übersetzt.
- [x] ScummVM-CI für den unabhängigen Story-JSON-Build und das getrennte
      `story-playable-preview`-Artefakt erfolgreich (#42020306920).
- [x] Vollständige Schlüssel-Tür-Rätselinteraktion des aus Story-JSON
      kompilierten Adventures in stock ScummVM erfolgreich (#42021639269).
- [x] Dynamischer ScummC-Compiler-/Linker-Adapter liest Raum- und Inventarliste
      aus dem Projekt, statt projektspezifische Namen im CI-Workflow zu pflegen
      (`scumm_toolchain.py`, lokale Boundary-Tests).
- [ ] Rätsel mit zwei oder drei erforderlichen Gegenständen ebenfalls als
      vollständigen ScummVM-Gameplay-Test nachweisen.
- [ ] Adapter auf weitere Rätseltypen, mehrere Kapitel, Figuren und Dialoge
      erweitern; die aktuelle Platzhaltergrafik durch einen Asset-Generator
      ersetzen und End-to-End-Spielbarkeit eines adaptierten Projekts testen.

### M4 – Grafik- und Animationspipeline

- [ ] Einheitliche Stile, Figuren- und Raumvarianten, Paletten und Animationen.
- [ ] KI-Bilder vor Verwendung deterministisch auf Format und Grenzen prüfen.
- [ ] Objektpositionen sind editierbar; Hotspots folgen stabilen Objekt-IDs.

### M5 – KI-Story-Regie

- [ ] Plot-, Kapitel- und Szenenentwürfe als validierte Operationen.
- [ ] Änderungswünsche zu Gegenständen, Rezepten, Dialogen und Rätseln.
- [ ] Ergebnisbericht: hinzugefügt, geändert, entfernt, Konflikte und Tests.
- [ ] Konflikte werden gezielt geklärt; Rollback und Revisionen sind möglich.

### M6 – Gradio Studio und MCP

- [ ] Story-Chat, Kapitelbaum, Raumvorschau, Objektinspektor, Testbericht.
- [ ] Manuelle Korrektur ohne Änderungen am generierten SCUMM-Quelltext.
- [ ] API/MCP-Operationen greifen auf dieselben validierten Modelle zu.

### M7 – Freigabefähiger Export

- [ ] Spielstart, Interaktion, Save/Load und Kompatibilität für dokumentierte
      ScummVM-Versionen getestet.
- [ ] Originale Erkennung oder offen dokumentierte erforderliche Integration,
      ohne fremde Spielidentitäten als reguläre Lösung zu verkaufen.
- [ ] DOS-Export nur bei unabhängig nachgewiesener Laufzeitunterstützung.
- [ ] Lizenzen der ScummC-Beispiele und Abhängigkeiten geklärt.

## Arbeitsrhythmus

Jeder Meilenstein wird anhand seiner Akzeptanzkriterien umgesetzt. Innerhalb
des laufenden Arbeitsauftrags werden technische Unteraufgaben und Fehlerkorrekturen
ohne wiederholte Freigabe erledigt. Produktentscheidungen, fehlende Rechte und
grundlegende Kompatibilitätskonflikte sind explizite Stoppsignale. Status wird
mit konkreten Commits, Testresultaten und verbleibenden Blockern berichtet.

## Aktuelle Priorität

M2: Nachgewiesene Aufnahme und Verwendung des Schlüssels erweitern um eine
persistente Türöffnung, einen Raumwechsel und ein explizites Spielziel.
M1 bleibt offen für Steuerung, Walkboxes und die Überprüfung flüssigen Scrollings.
