# Versioniertes SCUMM-Projektformat (experimentell)

## Gemeinsame Adventure-Studio-Projektdatei

Im Gradio-Studio kann das vollständige Authoring-Projekt als
`adventure.studio.json` gespeichert und wieder geöffnet werden. Die Datei
hat eine eigene, explizite `format_version: 1` und enthält zwei Bereiche:

- `story` enthält eine vollständige gültige Story-Dokument-Hülle
  (Version 1–4).
- `native` enthält ausschließlich die zusätzlichen optionalen Felder
  `costumes`, `actors`, `animation_rules`, `animation_input_rules`,
  `animation_triggers` und `interaction_sequences` aus dem `GameDocument`.
  Das Objekt darf leer sein, solange keine nativen Daten angelegt wurden.
Generierte Raumbilder und Hotspots werden aus der Story erneut erzeugt;
sie werden nicht redundant als zweite editierbare Quelle gespeichert.

Beim Laden und Speichern validiert der Studio-Editor alle nativen Referenzen
gegen die jeweils aktuelle Story-Übersetzung. Nicht unterstützte Felder oder
ungültige Referenzen verhindern den Export sichtbar. Das native
`GameDocument`-JSON und die bisherigen Story-JSON-Versionen bleiben separat
lesbar. Ein `.studio.json` ist **kein** direktes ScummC-Eingabeformat; der
Studio-Export erzeugt daraus weiterhin das native `project.json`.

## Geordnete Interaktionsfolgen (P0.5)

`GameDocument` v1 unterstützt optional `interaction_sequences`. Ein
Hotspot-Verb (`Push`, `Pull`, `Open`, `Close`) löst die Schritte **in ihrer
definierten Reihenfolge** aus. Der Export verwendet ausschließlich bereits
vorhandene native ScummC-Aktionen, keine zusätzliche Runtime:

```json
{"room":"Harbor","hotspot_id":"Key","verb":"Close","steps":[{"type":"animate_actor","actor_id":"Guide","animation":"gesture"},{"type":"delay_seconds","seconds":1},{"type":"set_object_state","hotspot_id":"Door","state":2}]}
```

Mehrere Actor-Cues sind in einer Folge kombinierbar. Animationen brauchen
einen benannten Costume-Index und die Actor-Richtung; alle referenzierten
Actors und Objekte müssen im selben Raum liegen. Zustände sind 0–2,
Wartezeiten positive ganze Sekunden. Ein Verb darf nur einmal belegt sein,
auch über `animation_input_rules` und `animation_triggers` hinweg. Unbekannte
Schritttypen werden abgewiesen. Das bestehende v1-Format bleibt kompatibel.

Die Folge ist zunächst ein linearer Verbablauf; Cutscene-Skip, parallele
Animationen und graphische Authoring-Oberfläche sind noch nicht implementiert.
Die vorhandene Actor-Projekt-Fixture enthält eine solche Folge; der native
Kompilierungs-/Spielstart-Gate verifiziert noch **nicht** das Anklicken und
den zeitlichen Verlauf der Folge in ScummVM.

## Wiederholbare Actor-Animationen durch Spielaktionen (P0.5)

`GameDocument` v1 erlaubt optional `animation_triggers`. Jeder Eintrag
verbindet einen Raum-Hotspot und ein Verb (`Push`, `Pull`, `Open`, `Close`)
mit einem Actor und einer benannten Animation seiner Costume:

```json
{"actor_id":"Guide","room":"Harbor","hotspot_id":"Key","verb":"Pull","animation":"gesture"}
```

Bei jeder Aktion ruft das generierte native Verb-Script die ausgewählte
`animateActor`-Animation erneut auf. Eine `initial_animation` ist dafür
nicht nötig. Costume-Index und Actor-Richtung werden referenzgeprüft;
doppelte Verbbelegungen sind ungültig. Ohne `animation_triggers` bleibt
das bestehende JSON-v1-Format unverändert. COUNT-Wächter einer einmaligen
Startanimation werden nicht automatisch neu eingerichtet.

## Typisierte COUNT-Reaktionen im Projektmodell (P0.5)

`GameDocument` v1 unterstützt optional `animation_rules`. Eine Regel besitzt
eine `condition` mit `actor_id` und `minimum_count` sowie einen `effect` mit
`room`, `hotspot_id` und `state` (0, 1 oder 2). Die Daten verweisen auf einen
Actor mit explizit indizierter `initial_animation` und einen Hotspot im
gleichen Raum. Eine nicht-loopende Anfangsanimation muss genügend explizite
`COUNT`-Kommandos in ihrer Startrichtung enthalten. Fremde JSON-Felder,
falsche Typen und ungültige Referenzen werden abgewiesen.

Beispiel einer Regel innerhalb eines Projekts mit Actor `Companion`,
Raum `Harbor` und Objekt `Key`:

```json
{"condition":{"actor_id":"Companion","minimum_count":2},"effect":{"room":"Harbor","hotspot_id":"Key","state":0}}
```

Der ScummC-Adapter erzeugt einen nativen lokalen Script-Slot mit
`getActorAnimCounter1`, `breakScript` und `setObjectState`. Er wird nach
dem `animateActor`-Aufruf des Actors gestartet. Es entsteht keine eigene
Runtime und kein aus dem JSON ausgeführter Quellcode. Alte Projekte ohne
`animation_rules` behalten ihre kanonische v1-Ausgabe.

Der erste vertikale Pfad deckt nur Objektzustandsänderungen nach der
initialen Actor-Animation ab; freier Ereignisgraph, Input-Fenster,
Raumwechsel während des Waits und Cutscene-Skip sind gesonderte Aufgaben.
Die native Projektregel wurde in stock ScummVM als Objektzustandswechsel
nach dem zweiten COUNT-Ereignis bestätigt (Actions `42461862069`).

`adventure_studio.scumm_project` ist die erste datenbasierte Schnittstelle
zwischen Adventure-Konfiguration und deterministischem SCUMM-Exporter.

- `format_version = 1` und `id` identifizieren das Projekt.
- `rooms` enthalten Raumgeometrie, 8-Bit-Palette, Pixelressourcen,
  Hotspots, Zustandswechsel, Raumausgänge und das explizite Spielziel.
- Pixelressourcen sind vorerst als Base64-Daten gespeichert. Das ist ein
  **technisches Zwischenformat**, kein Autoren- oder KI-Chat-Format.
- Ungültige Referenzen, fremde Felder, ausführbare Skriptfelder, ungültige
  Bildformate und nicht unterstützte Versionsnummern werden abgewiesen.
- Vor der Erstellung von Spieldateien werden alle Raumreferenzen geprüft.

## Verwendung

Aus einem validierten Projekt lässt sich ein kanonisches JSON-Dokument
erzeugen. Ein vorhandenes Dokument kann anschließend kompiliert werden:

```bash
PYTHONPATH=src python -m adventure_studio.scumm_project project.json build/game
```

Der aktuelle Export erzeugt ScummC-Raumquellen und BMP-Ressourcen. Der
experimentelle GitHub-Workflow übernimmt weiterhin die externe ScummC-
Kompilierung und das Linking. Weder die private Game-Logik noch KI-Antworten
werden direkt als SCUMM-Skript eingebettet.

## Akzeptanztests

- Kanonisches JSON wird ohne Änderungen eingelesen und wieder ausgegeben.
- Zwei verschiedene Abenteuerkonfigurationen erzeugen unterschiedliche,
  jeweils deterministische Dateien mit denselben Generatorbausteinen.
- Bei ungültigen Raumverweisen wird **vor** der Dateierzeugung abgebrochen.

Nächste Architekturaufgabe: die erzählerischen `Story`-Objekte in dieses
Projektformat überführen und Bild-, Layout- und Kostüm-Erzeugung getrennt
konfigurieren, damit Autoren keine Base64-Daten sehen müssen.

## Erste Story-Übersetzung

`adventure_studio.story_to_scumm.compile_story_to_scumm(story)` übersetzt einen
bewusst begrenzten Teil des erzählerischen `Story`-Modells direkt in ein
`GameDocument`: ein Kapitel, zwei bis drei linear verbundene Szenen, ein bis
drei Gegenstände insgesamt, eine oder zwei aufeinanderfolgende Türen und ein
Zielraum. Bei mehreren benötigten Gegenständen wird die erste Voraussetzung
als Werkzeug verwendet; die übrigen müssen bereits im Inventar sein.
Dekorative Gegenstände bleiben als Hotspots erhalten.
Die grafische Darstellung ist vorerst eine klar erkennbare,
deterministisch erzeugte Platzhaltergrafik; keine KI-Bildgenerierung.

Weitere Figuren, verzweigte Puzzles oder komplexe Szenenfolgen werden
explizit abgewiesen. Sie werden **nicht** stillschweigend aus der Geschichte
entfernt. Story-Referenzen und Softlocks werden bereits vor dem SCUMM-Export
mit dem deterministischen Rätsellöser überprüft.

### Direkter Story-Build

`examples/mini_story.json` ist eine vollständige, versionierte Story-Datei,
die keine Engine-Quellen oder Grafikdaten enthält. Aus ihr entsteht ein
SCUMM-Projekt inklusive Inventarmanifest und BMP-Ressourcen:

```bash
PYTHONPATH=src python -m adventure_studio.story_document examples/mini_story.json build/story
```

Die GitHub-Action **Experimental SCUMM v6 compatibility probe** baut zusätzlich
dieses Story-Beispiel mit ScummC, prüft Start, Kamerabild, Inventar-Aufnahme,
Türöffnung und Raumwechsel in einer echten ScummVM und stellt die Dateien als
`story-playable-preview` bereit (grüner Lauf #42021639269).
Die externe Compiler-/Linker-Anbindung ist in `scumm_toolchain.py` gekapselt.
Sie liest Raumliste und Inventar-IDs aus dem validierten Projekt, statt
Raumnamen oder Spielgegenstände im GitHub-Workflow fest einzutragen.
Das bleibt ein experimenteller DOTT-Kompatibilitäts-Build, kein eigenständiger
ScummVM-Spielidentifikator. Auch ein, zwei und drei Inventarvoraussetzungen
sowie die lineare Drei-Raum-Kette inklusive Rückweg wurden inzwischen in der
echten ScummVM gespielt und visuell geprüft (zuletzt CI #42029750897).

### Story-Rezepte (Format v2, zunächst nur Modell und Solver)

`format_version: 2` ergänzt das Pflichtfeld `story.recipes`. Ein Rezept ist
reine deklarative Datenstruktur mit `id`, `title`, zwei `ingredients` und
`result_item_id`. Zutaten sind `pickup`- oder bereits hergestellte `crafted`-
Gegenstände; das Ergebnis ist ein `crafted`-Gegenstand. Beim Kombinieren
werden beide Zutaten aus dem Inventar entfernt, das Ergebnis wird hinzugefügt.
Einmal eingesammelte Zutaten erscheinen danach nicht wieder am Boden.

`examples/recipe_story.json` enthält eine kaputte Küche, eine verschimmelte
Ananas, eine Flasche und ein daraus herstellbares Rätselobjekt. Der reine
Rätsellöser prüft Erreichbarkeit und Sackgassen:

```bash
PYTHONPATH=src python -m adventure_studio.story_document examples/recipe_story.json --validate-only
```

Bestehende Story-Dateien ohne Rezepte bleiben im strikten Format v1 und
behalten ihren unveränderten kanonischen JSON-Aufbau. Rezept-Dateien werden
als v2 serialisiert. Der begrenzte Export mit zwei Zutaten, einem Ergebnis
und einer Zieltür wurde inzwischen in ScummVM integriert und getestet.

Die Konsolidierung von KI-Änderungen entfernt jetzt unreferenzierte technische
`pickup`-Gegenstände aus dem vorgeschlagenen Story-Modell und meldet ihre IDs
im Feld `consolidated` des Änderungsberichts. Bewusst als `decoration`
modellierte Erzähldetails bleiben erhalten. Ein loses Sammelobjekt ohne
Mechanik wird im derzeitigen Modell nicht als `pickup` unterstützt.

### Objektpositionen (Story-Format v3)

`format_version: 3` enthält zusätzlich `story.placements`, eine Liste mit
stabilen Gegenstandsreferenzen und Ganzzahlkoordinaten. Beispiel:

```json
{"item_id":"Key","x":270,"y":130}
```

Die Position ist optional; ohne sie bleibt die bestehende automatische
Platzierung unverändert. Einträge gelten nur für physische `pickup`- und
`decoration`-Gegenstände, nicht für erzeugte Inventarergebnisse. Jedes Item
darf höchstens eine Position besitzen. Modell und SCUMM-Exporter prüfen
Referenzen sowie die tatsächlichen Raumgrenzen, einschließlich 320-Pixel-
Zielräumen. Änderungen laufen als `PutEntity("placement", Placement(...))`
durch dieselbe atomare Story- und Konsolidierungspipeline. Das Gradio Studio
kann Positionen anhand von Klickkoordinaten oder X/Y-Feldern vorschlagen und
erst nach Diff und Bestätigung übernehmen.

Storys der Versionen 1 und 2 bleiben ohne Migration lesbar. Die kanonische
Ausgabe verwendet erst dann v3, wenn mindestens eine Position definiert ist.

### Dialoge und Asset-Referenzen (Story-Format v4)

`format_version: 4` ergänzt vier streng validierte Sammlungen:

| Sammlung | Felder | Bedeutung |
| --- | --- | --- |
| `dialogues` | `id`, `scene_id`, `entry_node_id` | Gespräch mit Einstieg |
| `dialogue_nodes` | `id`, `dialogue_id`, `speaker_id`, `text`, `next_node_id` | gesprochener Text und direkter Folgeeintrag |
| `dialogue_choices` | `id`, `node_id`, `text`, `next_node_id` | auswählbare Antwort mit optionaler Fortsetzung |
| `assets` | `id`, `target_kind`, `target_id`, `asset_kind`, `source_id`, `digest` | referenzierte externe Asset-Datei |

`next_node_id: null` beendet einen Gesprächsweg. Knoten besitzen entweder
einen direkten Nachfolger oder Auswahlantworten. Alle Knoten müssen vom
Einstieg erreichbar sein, und von jedem Knoten muss mindestens ein Ende
erreichbar sein. Sprecher müssen als Charakter in der gleichen Szene
existieren. Die Asset-Arten sind `scene/background`, `character/portrait`,
`character/walk_sprite`, `item/object_sprite` und `dialogue_node/voice`.
Jede Ziel-/Art-Kombination ist eindeutig. `digest` enthält einen 64-stelligen
SHA-256-Hexwert, nicht die Binärdaten. Bilddateien werden noch nicht geladen.

Die Storyformat-Version steigt nur bei vorhandenen v4-Einträgen auf v4.
Die älteren Versionen bleiben ohne Migration lesbar. Beim Konsolidieren
werden Asset-Referenzen auf automatisch entfernte, nicht mehr benötigte
`pickup`-Gegenstände ebenfalls entfernt und im Änderungsbericht gezeigt.

**Exportgrenze:** Der erste begrenzte SCUMM-v6-Adapter kann Figuren als
sichtbare Platzhalter-Hotspots und je Figur ein Gespräch mit bis zu 16
einleitenden Zeilen erzeugen. Lineare Gespräche verwenden `TalkTo`, `egoSay`
und `waitForMessage` und haben ScummC erfolgreich passiert.

Eine erste **experimentelle Antwortauswahl** erweitert den generischen
`RoomAsset`-Baustein um typisierte `TalkRule`/`TalkChoice`-Einträge. Bis zu
drei Antworten erscheinen nach `TalkTo` als verborgene/anschließend
eingeblendete, anklickbare Raumobjekte. Ausgewählte Antworten schließen
das Menü und geben höchstens 16 weitere lineare Zeilen aus.
Verschachtelte Antworten und Sprecherwechsel werden weiterhin abgewiesen.
Diese UI ist noch kein klassisches SCUMM-Dialogmenü, und ein eigener
ScummC-/ScummVM-Nachweis für die neue Auswahl steht aus.

Die dargestellten Texte kommen bisher aus `egoSay` – es gibt noch keine
animierte SCUMM-Figur und keine NPC-Sprechblase. Externe Asset-Referenzen
werden weiterhin ausdrücklich zurückgewiesen. Gradio kann diese Daten
trotzdem validieren, vergleichen und als Story-JSON exportieren; der
Änderungsbericht zeigt die Einschränkung.
