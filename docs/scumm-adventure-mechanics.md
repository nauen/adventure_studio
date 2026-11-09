# Adventure Studio: Mechanik-Katalog für klassische SCUMM-Adventures

Status: Anforderungsentwurf, 2026-11-07. Dieses Dokument definiert **gewünschte
Spielerlebnisse**, nicht bereits implementierte Features oder bestätigte
SCUMM-v6-Opcode-Unterstützung. Die technische Gegenprüfung steht in
[`scumm-v6-runtime-contract.md`](scumm-v6-runtime-contract.md).

## 1. Ziel und Grenzen

Adventure Studio soll typische, auch komplexe Point-and-Click-Adventures
vollständig als **originale SCUMM-v6-Spieldaten** erzeugen können. Das
Autorenmodell bleibt deklarativ; der deterministische Generator übersetzt
validierte Daten in Skripte und Ressourcen. **Keine Engine-Patches**, kein
beliebiger KI-generierter Laufzeitcode und keine bloß optisch ähnliche
Neuentwicklung der SCUMM-Laufzeit.

Referenz für charakteristische Situationen sind unter anderem *Sam & Max Hit
the Road* und *Day of the Tentacle* (SCUMM v6). Ältere Abenteuer wie *Monkey
Island 2* und *Indiana Jones and the Fate of Atlantis* dienen als
Spielmechanik-Referenz, nicht als Beweis für v6-Implementierungsdetails.

Das Produktziel hat drei getrennte Nachweisstufen:

1. **Ausdrucksfähigkeit:** Die Situation ist vollständig im Autorenmodell
   darstellbar, ohne projektspezifischen Quellcode.
2. **Exportfähigkeit:** Der Compiler erzeugt valide SCUMM-v6-Ressourcen und
   Skripte mit dokumentierter Semantik.
3. **Laufzeitverhalten:** Die Situation funktioniert tatsächlich im
   unveränderten ScummVM-Interpreter, einschließlich Abbruch, Szenenwechsel,
   Save/Load und Wiederholung, soweit anwendbar.

## 2. Grundprinzip: Vorgänge statt nur Zustände

Eine Adventure-Interaktion ist nicht notwendig ein sofortiger Zustandswechsel.
Sie kann aus mehreren nebenläufigen, unterbrechbaren Vorgängen bestehen.

- **Ereignis**: Klick auf Objekt, Betreten einer Region, Zeitablauf,
  Animationsmarkierung, Dialogantwort, Zustandsänderung, Skriptende.
- **Vorbedingung**: Aussage über Inventar, Figuren, Objekt-, Raum- und globale
  Zustände, numerische Werte, laufende Sequenzen und Zeitfenster.
- **Aktion**: Bewegung, Animation, Objekttransformation, Text, Audio,
  Kamera, Inventar, Skriptstart, Raumwechsel oder Spielmoduswechsel.
- **Ablauf**: Geordnete, parallele oder verzweigende Aktionen; ausdrücklich
  deklarierte Wartepunkte, Zuständigkeit und Unterbrechungssemantik.
- **Persistenter Zustand**: Der Zustand, den weitere Szenen, Figuren und
  gespeicherte Spielstände beobachten.

Nicht jeder Vorgang wird als neue Laufzeitabstraktion implementiert. Die
vorgeschlagene Modellsemantik muss auf **tatsächlich vorhandene SCUMM-v6-
Mechanismen** abgebildet werden; andernfalls gilt der Vorgang zunächst als
nicht unterstützt.

## 3. Konkrete Referenzabläufe

### 3.1 Zwei Figuren steigen in ein Auto und fahren weg

1. Benutze Auto: Interaktion wird angenommen und normales Eingabeschema
   gegebenenfalls eingeschränkt.
2. Fahrer läuft zum definierten Einstiegs-/Blickpunkt.
3. Beifahrer läuft gegebenenfalls gleichzeitig zum zweiten Einstieg.
4. Einsteige-, Tür- und Fahrzeuganimation werden synchronisiert; Figuren
   können währenddessen verdeckt oder ausgeblendet werden.
5. Motorgeräusch startet; Fahrzeug setzt sich in Bewegung; Kamera folgt oder
   bleibt zurück.
6. Am definierten Ereignis oder nach dem Abschluss der Abfahrt wird eine
   Zielszene beziehungsweise Straßenkarte geladen.
7. Inventare, Figurenzustände und Zielpositionen bleiben konsistent.

Benötigt: Interaktionsposition, zwei unabhängige Figuren, Synchronisation,
parallele Aktionen, Objekt-/Figurensichtbarkeit, Kamera, Sound, Übergang,
Eingabesicherung und deterministischen Endzustand.

### 3.2 Achterbahn mit Eingriff am offenen Kabel

1. Fahrsequenz startet, während besondere Eingaben weiter erlaubt sind.
2. Figur/Fahrzeug und Hintergrund bewegen sich. Es gibt eine kurze Phase,
   in der die Figur die Kabel erreichen kann.
3. Nur während dieser Phase ist die vorgesehene Aktion wirksam.
4. Erfolgreicher Eingriff beendet/verzweigt die normale Fahrt an einem
   definierten Punkt; Kurzschlussgrafik, Audio und Weltzustand ändern sich.
5. Zu frühe, zu späte oder unzulässige Eingaben führen zu definierten
   Fehlschlägen und gegebenenfalls einem erneuten Versuch.

Benötigt: Spielphase, zeitgebundene Bedingungen, gegebenenfalls beweglicher
Hotspot, Eingaben während laufender Skripte, Animations-/Positionsereignis,
Priorität und Abbruch, korrekte Wiederholung. **Frame-Marker sind zunächst
eine mögliche Autorensemantik, nicht als native SCUMM-v6-Funktion belegt.**

### 3.3 Maschine mit Hebeln, Druck und Überhitzung

Die Maschine besitzt gekoppelte Zustandsvariablen (Motor, Ventil, Druck,
Temperatur). Hebel und Regler ändern Werte; ein Hintergrundvorgang bewertet
den Zustand wiederholt. Eine korrekte Kombination löst eine Animation und
einen Raumzugang aus. Falsche Einstellungen lösen Fehleranimationen oder
einen zurücksetzbaren Zustand aus. Eine Nahansicht kann eine andere
Interaktionsoberfläche als der normale Adventure-Raum verwenden.

### 3.4 NPC patrouilliert und wird abgelenkt

Der NPC läuft auf einer Route, bemerkt ein Geräusch, unterbricht die Patrouille,
untersucht eine Position und kehrt zurück oder alarmiert weitere Figuren.
Währenddessen kann der Spieler handeln. Ein Gespräch kann die Patrouille
pausieren, abbrechen oder erst nach der nächsten Wegmarke beginnen.

### 3.5 Bewegter Gegenstand: Schlüssel am Gürtel

Ein anklickbarer Gegenstand folgt einer Figur beziehungsweise einem
Animationspunkt. Das Ziel wird beim Klick identifiziert; erst anschließend
wird entschieden, ob die Spielerfigur sofort handelt, hinläuft, verfolgt
oder die Interaktion mangels Erreichbarkeit verwirft. Besitzwechsel,
Sichtbarkeit und Gegenstandsidentität dürfen nicht auseinanderlaufen.

### 3.6 Gegenstand fällt, Spieler fängt ihn

Ein sichtbarer Gegenstand wird animiert. Ein begrenztes Eingriffsfenster
und eine räumliche Trefferbedingung bestimmen den Erfolg. Nach Landung
entsteht ein normaler Raum-Hotspot oder das Objekt zerbricht. Kein
unbeabsichtigter doppelter Besitz bei Klick auf einen bereits entfernten
Gegenstand.

### 3.7 Mehrere Figuren beeinflussen einander und dieselbe Welt

Jede Spielfigur hat Position, Sichtbarkeit, Animation und gegebenenfalls
eigenes Inventar. Globale Ereignisse beeinflussen andere Zeiten/Räume.
Bei Figurenwechsel werden offene Aktionen definiert behandelt; Gegenstände
lassen sich nur über ausdrücklich vorgesehene Übergänge übertragen.

### 3.8 Dialog unterbricht den Raumablauf

Antwortoptionen besitzen Bedingungen, Einmaligkeits- und Wiederholregeln.
Während des Gesprächs können Sprecher Animationen ausführen. Andere
Skripte laufen je nach Design weiter oder werden angehalten. Beim Ende
oder Abbruch wird der vorherige Spielmodus kontrolliert wiederhergestellt.

## 4. Mechanik-Matrix

**Status aller Zeilen:** Anforderung, nicht als implementiert bestätigt.
Die IDs sind stabil und können später auf Tests, Compilerbausteine und
Nachweisläufe verweisen.

| ID | Spielsituation | Unverzichtbare Engine-Semantik |
| --- | --- | --- |
| W01 | Figur läuft zu einem Raumobjekt | Wegfindung, Zielpunkt, Orientierung, Wartebedingung |
| W02 | Tür schließt, bevor Figur ankommt | Ziel-Neuprüfung, Abbruch oder alternative Reaktion |
| W03 | Figur läuft hinter einem Vordergrundobjekt | Renderreihenfolge, Masken/Layers |
| W04 | Figur erscheint in der Ferne kleiner | Walkbox-/Aktor-Skalierung |
| W05 | Raum scrollt bei Bewegung | Kamera-/Actor-Follow, Scrollgrenzen |
| W06 | Spieler betritt bewegliche Plattform | Figuren-/Objektkoordination, Positionsbezug |
| W07 | Fahrstuhl fährt zwischen Etagen | Bewegungsablauf, Ein-/Ausstieg, Etagenzustand |
| W08 | Zwei Figuren steigen in ein Auto | Parallele Wege, synchronisierte Animation, Wechsel |
| W09 | NPC verlässt Raum und erscheint anderswo | Globale Präsenz/Position, Raumwechsel |
| I01 | Gegenstand vom Boden aufnehmen | Lauf-/Greifsequenz, Besitzübergabe an Ereignispunkt |
| I02 | Zwei Gegenstände kombinieren | Typisierte Operation, Verbrauch, neues Ergebnis |
| I03 | Gegenstand einem NPC geben | Reichweite, Reaktion, Übergabeanimation, Besitzwechsel |
| I04 | NPC gibt Gegenstand zurück | NPC-Animation, neue Inventarinstanz, Bedingungen |
| I05 | Gegenstand ist am Gürtel einer Figur | Beweglicher/gebundener Hotspot, Besitz |
| I06 | Vogel trägt Schlüssel fort | Bewegliches Ziel, Sichtbarkeit, Objekttransport |
| I07 | Gegenstand fällt und kann gefangen werden | Treffer-/Zeitfenster, Zustand bei Landung |
| I08 | Schrank enthält erst nach Öffnen Objekt | Mehrstufiger Objektzustand, Hotspot-Aktivierung |
| I09 | Gegenstand verwandelt sich | Sprite-/Zustandswechsel, Identität, Inventarkonsistenz |
| I10 | Spieler kann Gegenstand nur heimlich nehmen | Sichtlinien-/NPC-Zustandsbedingung |
| T01 | Achterbahnfahrt mit Kabelkontakt | Laufende Sequenz, Eingriffsfenster, Verzweigung |
| T02 | Schalter muss im richtigen Moment gedrückt werden | Animations-/Zustandsereignis, zeitliche Bedingung |
| T03 | Zwei Knöpfe müssen gemeinsam aktiv sein | Gleichzeitige/überlappende Zustände |
| T04 | Tür schließt nach Frist | Timer, Unterbrechung und Rücksetzung |
| T05 | Wasser steigt kontinuierlich | Wiederholter Skriptzustand, Szenengrafik, Geometrie |
| T06 | Maschine läuft während Spieler interagiert | Parallele Skripte, atomare Zustandswechsel |
| T07 | Spieler manipuliert rotierende Maschine | Bewegte Interaktionsfläche, Interaktionsphase |
| T08 | Normale Fahrt wird durch Kurzschluss ersetzt | Kontrollierter Abbruch und Nachfolgeskript |
| T09 | Ein Ereignis tritt nur einmal ein | Persistentes Ereignis-Latch |
| T10 | Ereignis kann nach Neustart erneut auftreten | Reset-/Retry-Regeln, keine Restskripte |
| N01 | Wache patrouilliert | Autonome NPC-Schleife, Wegpunkte |
| N02 | NPC untersucht ein Geräusch | Ereignis, Priorität, Unterbrechung, Rückkehr |
| N03 | NPC entdeckt Spieler | Sicht-/Entfernungsbedingung, Alarmzustand |
| N04 | NPC nimmt Gespräch während Handlung an | Interaktionspolitik, Pause/Fortsetzung |
| N05 | Zwei NPCs reden parallel | Nebenläufige Sprecher-/Animationssteuerung |
| N06 | NPC verfolgt Spieler | Zielaktualisierung, Wegfindung, Abbruch |
| D01 | Dialogoption wird durch Wissen freigeschaltet | Bedingte Antworten, persistentes Wissen |
| D02 | Antwort nur einmal wählbar | Dialoghistorie, Optionsfilter |
| D03 | Gespräch wird unterbrochen | Dialog- und Spielmoduszustand |
| D04 | Dialog verändert NPC-Verhalten | Weltvariablen, Ereignisnachrichten |
| D05 | Sprecher wechselt und gestikuliert | Sprache, Text, Kostümanimation, Synchronisation |
| C01 | Geskriptete Ankunft/Abfahrt | Reihenfolge, Kamera, Figuren, Objektanimation |
| C02 | Cutscene mit parallelen Bewegungen | Skript-Scheduling und Wartepunkte |
| C03 | Spieler kann Cutscene überspringen | Skip-Pfad, identischer persistenter Endzustand |
| C04 | Cutscene enthält spielbaren Moment | Temporärer Eingabemodus, Kontrollübergang |
| C05 | Raumwechsel während laufendem Skript | Skriptlebensdauer und Ressourcenfreigabe |
| U01 | Nahansicht von Maschine/Buch/Karte | Eigener Raum-/UI-Kontext und Rückkehr |
| U02 | Fahrzeug-Minispiel | Direkte Eingaben, Takt, Trefferregeln |
| U03 | Inventar hat viele Gegenstände | Paging, Besitzer, Verfügbarkeit |
| U04 | Verb-/Cursor-Modus wechselt | Eingabeinterpretation, Hotspot-/Objektklassen |
| U05 | Handlung beeinflusst Musik | Sound-/Musikzustand, Ereignisgrenze |
| P01 | Spielstand mitten im Puzzle | Wiederherstellbare Variablen, Figuren, Objekte |
| P02 | Save/Load während Ablauf | Wiederanlaufpolitik oder gesperrter Speicherpunkt |
| P03 | Figurenwechsel während Hintergrundvorgang | Hintergrundskript- und Weltlebensdauer |
| P04 | Mehrere alternative Lösungswege | Nichtlineare Bedingungen, Softlockprüfung |
| P05 | Lokalisierung mit Sprache und Text | Stabile Text-/Sound-IDs, Timing-/Layoutgrenzen |

## 5. Benötigte Autorensemantik (Ziel, nicht SCUMM-Syntax)

### Zustands- und Objektmodell

- Räume mit Geometrie, Walkboxes, Skalierung, Masken und Kamera-Randbedingungen.
- Figuren mit Raum, Position, Richtung, Kostüm/Animation, Zustand und Inventar.
- Objekte mit stabiler ID, Besitz (Raum/Figur/Inventar), visuellen Zuständen,
  Interaktionspunkten, Hotspots und gegebenenfalls Bindung an eine Figur.
- Globale und lokale Variablen, numerische Bereiche und abgeleitete Bedingungen.
- Dialoggraph mit bedingten und persistenten Optionen.
- Musik-/Sound-/Sprachressourcen mit stabilen Referenzen.

### Ablaufmodell

- Sequenzielles Starten, paralleles Starten, Warten auf Skriptende,
  Objektzustand, Figurenankunft, Timer, Animation oder externes Ereignis.
- Kontrollierte Verzweigung und explizite Priorität bei Konflikten.
- Definierte Regeln für Abbruch, Skip, Neustart, Wiederholung, Raumwechsel,
  Figurenwechsel und Speichern/Laden.
- Interaktionsmodi: normale Verben, Dialog, Nahansicht, eingeschränktes
  Zeitfenster, direkte Steuerung, nicht interaktive Cutscene.
- Einheitliche Zuordnung von Eingabeereignis, getroffenem Objekt,
  Annahmezeitpunkt, Ausführungszeitpunkt und möglicher Ziel-Neuprüfung.

### Persistenz- und Korrektheitsanforderungen

- Sichtbarer Objektzustand und logischer Besitz dürfen niemals divergieren.
- Gescheiterte oder unterbrochene Aktionen hinterlassen keinen halb
  ausgeführten Weltzustand.
- Zeitabhängige Prüfungen müssen gegen unterschiedliche Laufzeitgeschwindigkeit
  und ausgelassene Renderframes robust sein.
- Jeder Endzustand einer Cutscene muss auch über den Skip-Pfad entstehen.
- Der Story-Solver muss zumindest kritische Endzustands-, Verbrauchs- und
  Erreichbarkeitsinvarianten prüfen; vollständige Zeit-/Nebenläufigkeits-
  Verifikation bedarf eigener, begrenzter Analysen.
- Gleiche Eingangsdaten und Toolchain erzeugen die gleichen Ressourcen.

## 6. Ausdrücklich offene SCUMM-v6-Fragen

Diese Mechaniken dürfen nicht allein aus den Begriffen des Autorensystems
als native Engine-Fähigkeiten abgeleitet werden:

1. Können Animationen zuverlässige, für Skripte beobachtbare Frame-Marker
   liefern, oder müssen Abläufe mit Skript-/Actor-Zuständen synchronisieren?
2. Wie interagieren Script-Slots, `wait`, Delay, Freeze, Cutscene, Raumwechsel
   und Script-Stopp tatsächlich miteinander?
3. Welche Arten beweglicher Hotspots und actor-relativer Objektpositionen
   sind ohne zusätzliche Engine-Erweiterung möglich?
4. Wann werden Eingaben im normalen Verb-System verarbeitet und wann
   können Minispiel-/Cutscene-Skripte sie selbst auswerten?
5. Welche Zustände werden im originalen Savegame gespeichert, und was ist
   bei laufenden Skripten reproduzierbar wiederherstellbar?
6. Welche Raum-/Objekt-/Kostüm-/Soundressourcen kann ScummC zuverlässig
   erzeugen, und wo fehlen Compilerfeatures trotz Runtime-Opcode?
7. Welche SCUMM-v6-Variante wird als genaues Profil festgelegt? Spiele
   können trotz gleicher Hauptversion verschiedene Features verwenden.

## 7. Arbeitsmethode und Abnahmekriterien

Für jede Mechanik-ID wird ein **Contract-Test** entwickelt:

1. Das Autorenmodell beschreibt die Situation vollständig ohne Rohskripte.
2. Der Compiler erzeugt nachprüfbare SCUMM-v6-Ressourcen.
3. Ein Interpreter-Test prüft die sichtbare Zustandsfolge und die möglichen
   Spieleraktionen, nicht nur den erfolgreichen Start.
4. Negative Fälle werden ausgelöst (falsche Eingabe, zu spät, Abbruch,
   Raumwechsel, zweiter Versuch).
5. Wo relevant: Save/Load vor, während und nach der Situation.

Priorität für die technische Grundlagenarbeit:

1. **Abbildung auf originalen Skript-Scheduler und Eingabemodell** klären.
2. Eine kurze Auto-Abfahrt als sequenzielle/teilweise parallele Inszenierung.
3. Eine Maschine, die weiterläuft, während Eingaben möglich sind.
4. Ein echtes zeitliches Interaktionsfenster während einer Animation.
5. Ein patrouillierender, unterbrechbarer NPC.
6. Erst danach bewegte Hotspots, Figurenwechsel und komplexe Minispiele.

Die Reihenfolge ist vorläufig und bedeutet nicht, dass die Beispiele
spielindividuell fest verdrahtet werden sollen. Aus den Referenzszenarien
werden gemeinsame, wiederverwendbare Compilerbausteine abgeleitet.
