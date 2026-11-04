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
- [ ] Automatisierte Screenshots belegen zwei verschiedene Kamerapositionen.
- [ ] Konsolenlogs und Artefakte stehen in GitHub Actions zur Verfügung.

### M2 – Geschlossenes Mini-Adventure

- [ ] Schlüssel aufnehmen, ins Inventar übertragen und visuell bestätigen.
- [ ] Verschlossene Tür, Schlüsselprüfung, Türöffnung und Raumwechsel.
- [ ] Ein explizites Spielziel mit deterministisch testbarem Lösungsweg.
- [ ] Ungültige Handlungen und Softlocks werden getestet.

### M3 – Adventure aus Daten

- [ ] Vollständiges M2-Beispiel ausschließlich aus dem Projektmodell exportieren.
- [ ] Keine projektindividuellen handgeschriebenen Runtime-Skripte nötig.
- [ ] Zwei unterschiedliche Projekte aus denselben Generatorbausteinen bauen.
- [ ] Konsistenter reproduzierbarer Export, dokumentierte Ressourcenstruktur.

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

M1: Spielfigur sichtbar machen, kontrollierte Kamerabewegung auslösen und
Screenshots des Anfangs und des Endes mit deterministischen Prüfungen vergleichen.
