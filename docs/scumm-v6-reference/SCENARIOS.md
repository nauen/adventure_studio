# Verbindliche Abenteuer-Szenarien und Akzeptanzfälle

Die Szenarien beschreiben **Spielergebnisse**, nicht einzelne Sonderfall-
Implementierungen. Als Produktumfang gelten alle Fähigkeiten in der
[SCUMM-v6-Matrix](../SCUMM_V6_CAPABILITIES.md). Die folgende Reihenfolge
macht gemeinsame Grundbausteine sichtbar, damit wir sie einmal implementieren
und in vielen Szenen wiederverwenden können.

## Gemeinsamer Baukasten

1. **Weltzustand:** typisierte Variablen, Flags, Objekt-/Actor-/Inventarzustände,
   Raum- und Script-Lifetime (`S01`,`P01`,`O02`,`O05`).
2. **Aktion/Bedienung:** Player-Input, Verbs, Use/Combine/Talk, Hitbox und
   Bedingungen/Effects (`O01`,`O03`,`O06`,`O07`,`O10`).
3. **Zeitlicher Ablauf:** parallele native Scripts, Wait/Break, Actor-
   Bewegung, Costume-Animation/Counter, Ereignis-Phasen (`S02`,`A03`,
   `A04`,`A06`,`A07`).
4. **Bild/Inszenierung:** native Räume, Masken, Walkboxen, Objektstates,
   Actors, Kamera-/Cutscene-Scripts (`R01`–`R14`,`S03`–`S09`).
5. **Kommunikation/Persistenz:** Dialogverzweigung, Audio- und Musikzustand,
   Save/Load (`D01`–`D04`,`U01`–`U03`,`P02`).

Diese Bausteine sind **keine zusätzliche Runtime**. Sie bilden Daten und
Aktionen auf die referenzierten nativen SCUMM-v6-Ressourcen/Skripte ab.

## A. Vor dem Haus ins Auto steigen und wegfahren

**Spielergebnis:** Figuren gehen zum Auto, steigen animiert ein, die Figuren
sind anschließend nicht mehr sichtbar, das Auto fährt weg; die nächste Szene
beginnt konsistent. Für Abbruch/Skip existiert derselbe Endzustand.

- **ID-Abhängigkeiten:** `A01`–`A04`, `A08`,`A09`,`O02`,`O03`,`S01`–`S04`,
  `R04`,`S08`.
- **Benötigte Daten:** Actor- und Autozustand, Costume/Animationen, Dreh- und
  Walk-Ziel, Scriptslots, Sichtbarkeit, neue Raumkennung, Zeitlinie mit Cues.
- **Abnahme:** Normalablauf und Skip erreichen denselben Objekt-/Inventar-/
  Roomzustand. Ein zweiter Actor kann parallel laufen; beim Wiedereintritt
  bleiben alle Zustände konsistent.
- **Status:** Konzeptionelles Akzeptanzszenario, **kein** Nachweis, dass die
  Sequenz bereits exportiert wird.

## B. Fahrgeschäft mit Interaktion während der Bewegung

**Spielergebnis:** Wagen/Animation läuft, die Eingabe bleibt bewusst aktiv;
das Objekt ist nur in einer definierten Phase erreichbar. Bei `Use Gegenstand
mit Kabel` im Zeitfenster folgt Kurzschluss/Zustandswechsel; sonst gibt es
eine definierte Reaktion. Kein zufälliges Ergebnis durch Frame-Race.

- **ID-Abhängigkeiten:** `A04`,`A06`,`A07`,`O02`,`O03`,`O06`,`S02`,`S10`,`P01`.
- **Daten:** native Scriptphase/Counter, Objekt-Hitbox je Zustand, Inventar,
  bedingter Use-Effekt, Abbruch-/Wiederholungsregel.
- **Abnahme:** Interaktion *vor*, *während* und *nach* dem Fenster; Wiederholen,
  Raumwechsel und ggf. Save/Load; identisches Ergebnis unter reproduzierbaren
  Tick-/Scheduler-Bedingungen.
- **Offenes Engine-Gate:** COUNT-Semantik, tatsächlicher Inputpfad während
  Scripts und Hitbox-Update im exportierten v6-Spiel beweisen. `waitForAnimation`
  ist laut Audit **kein** universeller Frame-Event-Trigger.

  **Implementierungsstand:** Die optionale Projekt-JSON-Struktur
  `animation_input_rules` bindet einen nativen Objekt-Verbfall (`Push`, `Pull`,
  `Open`, `Close`) an einen Actor-`COUNT`-Grenzwert. `on_time` gilt bei
  `getActorAnimCounter1(actor) < before_count`, `too_late` ab der Grenze;
  beide Ausgänge sind typisierte Objektzustandsänderungen. Die Eingabe
  wird nicht künstlich gesperrt. Roundtrip, Referenzen, Ablehnung fremder
  Script-Felder und generierter ScummC-Quelltext sind unit-getestet.
  **Native Probe:** Zwei getrennte stock-ScummVM-Läufe wählen den `Push`-Verb
  in der Road-UI und klicken auf den Schlüssel: Beim ersten Lauf nach COUNT 1,
  vor COUNT 2 verschwindet die Tür; beim zweiten Lauf nach COUNT 2 verschwindet
  der Schlüssel. Bildschirmfarben der Tür und des Schlüssels sind die
  expliziten Positiv-/Negativassertions. Die isolierte Probe hält die Figur
  neben dem Interaktionsziel und verlangsamt ihre Costume-Animation; diese
  Fixture-Parameter sind keine Editor-Limits. Ein erweitertes natives
  Acceptance-Gate prüft zusätzlich **keinen Klick** und **zwei Klicks im
  selben Spielprozess**: Der erste verändert die Tür vor COUNT 2, der
  zweite verändert anschließend den Schlüssel nach COUNT 2. Damit ist
  das erneute Auswerten der COUNT-Bedingung für diesen Übergang belegt.
  Ein weiterer stock-ScummVM-Lauf nutzt nach der späten Eingabe die
  tatsächliche `WalkTo`-Tür nach `Cellar` und die Treppe zurück nach
  `Harbor`. Der Schlüssel bleibt nach Wiedereintritt verschwunden,
  während die Tür offen bleibt; die normale Room-Entry-Logik läuft
  erneut. Ein zusätzlicher COUNT-Wächter würde den Schlüssel bei
  erneutem Initialanimationsstart wieder sichtbar machen. Ein natives,
  globales SCUMM-Bit verhindert diesen Replay beim Wiedereintritt;
  die stock-ScummVM-Probe bestätigt den unveränderten Schlüsselzustand.
  Noch offen sind beliebige Mehrfachaktionen und weitere Zeitfenster,
  **explizit angeforderte** Animations-Neustarts, Save/Load und das
  vollständige Fahrgeschäft-Szenario.

## C. Kinoartige Cutscene mit Totale, Nahaufnahme und Detail

**Spielergebnis:** Totale → Actor bewegt sich → Perspektivschnitt/Detailbild
→ Reaktion einer zweiten Figur → Kamera schwenkt zurück. Musik/Sprache sind
zeitlich passend; Skip führt zu einem definierten Zustand.

- **ID-Abhängigkeiten:** `R01`,`R04`,`R05`,`R14`,`A01`–`A04`,`A08`,`S02`–`S09`,
  `D01`,`U01`–`U03`.
- **Daten:** Shots als Editor-Metadaten, native Raum-/Bildzustände,
  Kamera-X, Actors, Timeline/Cues, Waits, Audio-/Script-Start, Skip-Commit.
- **Abnahme:** Sichtbare zwei unterschiedliche Bildkompositionen, nativer
  X-Pan und `waitForCamera`, parallele Actor-Reaktion, identischer Endzustand
  nach Skip. Kein „Zoom“ behaupten, wo nur Raum-/Bildschnitt vorliegt.

## D. Klassisches Inventar- und Rätselnetz

**Spielergebnis:** Objekte aus mehreren Räumen aufnehmen, beliebige
Gegenstände kombinieren, mehrteilige Bedingungen erfüllen, Wege öffnen,
zurückkehren; Objekt- und Puzzlefortschritt bleibt gespeichert.

- **ID-Abhängigkeiten:** `O01`–`O09`,`R04`,`P01`–`P03`.
- **Grenzfälle:** null/ein/zwei/viele Hotspots, mehrere Rezepte, eine/N
  unabhängige Bedingungen, Rückwege, verbrauchte Objekte, nicht passendes Use.
- **Abnahme:** Keine still fallengelassenen Objekte, Zustandswechsel in
  nativen Object-States, Revisit- und Save/Load-Reproduzierbarkeit.

## E. Bewegtes Objekt, das seine Klickfläche mitnimmt

**Spielergebnis:** Eine Figur oder ein Fahrzeug bewegt sich im Raum; der
Player kann das **sichtbar neue** Ziel anklicken. Alte Pixelposition darf
keinen unsichtbaren Hotspot behalten.

- **ID-Abhängigkeiten:** `O02`–`O04`,`S01`,`S02`,`R05`.
- **Abnahme:** Positionen A/B/C mit Klicktest an neuer und alter Stelle,
  Objektzustands- und Parent-Flags, erneuter Room-Eintritt.

## F. Zwei Figuren überkreuzen sich vor/hinter Vordergrundobjekten

**Spielergebnis:** Actor-Z-Reihenfolge, Masken, Boxen und Skalierung erzeugen
korrekte Verdeckung; Bewegungen verändern die Reihenfolge sichtbar.

- **ID-Abhängigkeiten:** `R06`–`R11`,`A01`–`A05`.
- **Abnahme:** Masken-Testpixel, native BOXM/SCAL, Walkroute, Überkreuzung
mit geprüfter v6-Spielvariante (*Sam & Max* gesondert).

## Qualitätsgates für jedes Szenario

| Gate | Minimaler Nachweis |
| --- | --- |
| **Verhalten** | Spielergebnis, Eingaben und Endzustände sind beschrieben; 0/1/2/N-Fälle benannt. |
| **Native Abbildung** | Funktions-IDs, ScummC-Emitter und v6-Interpreterpfad sind referenziert; keine eigene Runtime. |
| **Daten** | Versioniertes Projektmodell und ausdrückliche, maschinenlesbare Blocker für noch nicht unterstützte Teile. |
| **Automatisierte Prüfung** | Deterministischer Compiler-/Ressourcen-/Interaktionstest, einschließlich Negativfällen. |
| **Laufzeit** | Ein kleines exportiertes Fixture in stock ScummVM mit konkretem beobachtbarem Erfolg. |
| **Dokumentation** | Nur Status der tatsächlich bewiesenen IDs ändern; offene Gates bleiben offen. |

**Kein großes Pflicht-Konformitätsspiel:** Pro Grundbaustein ein kurzes
minimal reproduzierbares natives Fixture. Zusammengesetzte Szenarien dienen
später als vertikale Integrations-/Produktabnahmen. Damit die Entwicklung
praktisch bleibt, werden bei Änderungen nur die betroffenen Nachweise
ausgeführt bzw. nachgezogen.
