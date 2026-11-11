# Adventure Studio – SCUMM-v6-Funktionsmatrix

Stand: 2026-11-07. **Zentrale Liste der nativen Fähigkeiten, die wir für
typische vollständige SCUMM-v6-Adventures benötigen.** Die Matrix ist
ein fortzuschreibender Katalog und noch kein Anspruch, sämtliche
proprietären Varianten und Sonderfälle vollständig erfasst zu haben.

**Verbindlicher Referenzvertrag:** [SCUMM-v6-Referenzbibliothek](scumm-v6-reference/README.md)
mit [nativen Primitiven](scumm-v6-reference/NATIVE_PRIMITIVES.md),
[Abnahmeszenarien](scumm-v6-reference/SCENARIOS.md) und einem
[maschinenlesbaren Quellenindex](scumm-v6-reference/capability_sources.json).
Diese **Matrix bleibt die einzige Quelle** für Funktions-IDs und
Fortschrittsstatus; die Referenzbibliothek wiederholt sie nicht.
`tests/test_scumm_reference_contract.py` prüft den Quellenindex auf
Vollständigkeit gegenüber den 64 IDs.

**D03 – Editor-Ergänzung (2026-11-11, Abnahme ausstehend):**
Mehrere ungespeicherte NPC-Sprechfolgen können über die vorhandene
native Writer-/Validatorroutine gemeinsam in den Projektstand
übernommen werden. Ein Fehler blockiert die gesamte Übernahme;
eine explizite Bestätigung ist erforderlich. Kein neuer Opcode,
keine Änderung am Projektformat oder D03-Capability-Status.

**D03 – Editor-Ergänzung (PR #189, Core-/Chromium-CI bestanden):**
Ungespeicherte NPC-Sprechfolgen können aus der Entwurfsübersicht
einzeln nach ausdrücklicher Bestätigung verworfen werden. Andere
Sitzungsentwürfe bleiben erhalten; für das aktive Ziel erscheint
die gespeicherte Folge. Kein neuer nativer Opcode, keine Änderung
an COST-/SCUMM-v6-Ausgabe und kein geänderter D03-Capability-Status.

**D03 – Editor-Ergänzung (PR #187, CI-Abnahme bestanden):**
Die Gradio-6-Oberfläche bindet eine `beforeunload`-Warnung für
aktive und zwischengespeicherte NPC-Sprechfolgenentwürfe ein.
Core-/Chromium-CI je zweimal grün (Runs `43046439156`,
`43046446969`, `43046439114`, `43046447015`).
Menschliche Browser-Abnahme offen; D03-Capability-Status und
nativer COST-/SCUMM-v6-Export unverändert.

**D03 – aktuelle Editor-Ergänzung (PR #186, CI-Abnahme bestanden):**
Nach dem Speichern einer NPC-Sprechfolge während einer offenen
Projektwechselwarnung zeigt der Editor nur die verbleibenden
ungespeicherten Zeilen/Richtungen; bei vollständigem Speichern
wird dies ausdrücklich bestätigt. Kein automatischer Projektwechsel,
keine Änderung an Projektformat, COST-/Opcode-Ausgabe oder
Capability-Status. Core-/Chromium-CI je zweimal grün (Runs
`43029799583`, `43029813622`, `43029799611`, `43029813958`).
Native stock-ScummVM-Abnahme von PR #185 bleibt gültig.
Menschliche UI-Abnahme offen. Nächstes Editorpaket: Beim
Browser-Tab-Verlassen vor ungespeicherten Entwürfen warnen.

**D03 – aktuelle Editor-Ergänzung (PR #185, CI-Abnahme bestanden):**
Die Projektwechselwarnung kann eine betroffene ungespeicherte
Sprechfolge mit Zeilen-ID und Blickrichtung direkt im bestehenden
NPC-Editor auswählen, einschließlich der korrekten Costume-
Vorschau. Der Wechsel öffnet lediglich den Sitzungsentwurf;
native Projekt- und COST-/Opcode-Daten sowie Capability-Status
bleiben unverändert. Core-, Chromium- und stock-ScummVM-CI
je zweimal grün (Runs `43026977699`, `43026985048`,
`43026977821`, `43026985072`, `43026977775`,
`43026986314`). Menschliche UI-Abnahme offen.
Nächstes Editorpaket: die offene Verlustliste nach Speichern
einer betroffenen Folge neu berechnen.

**D03 – aktuelle Editor-Ergänzung (PR #184, CI-Abnahme bestanden):**
Vor dem Projektdateiwechsel nennt der Editor alle offenen
NPC-Sprechfolgenentwürfe mit Zeile, Blickrichtung und stabiler
ID, inklusive der aktiven Eingabe. Die Liste ist nur Anzeige,
keine Änderung an Projektformat, nativer COST-/Opcode-Ausgabe
oder Capability-Status. Core-/Chromium-CI je zweimal grün
(Runs `43024142670`, `43024150087`, `43024142817`,
`43024150372`); stock-ScummVM-CI nach gezieltem Timing-Retry
grün (`43024149992`). Menschliche UI-Abnahme offen.
Nächstes Editorpaket: betroffene Zeile/Richtung aus der
Warnung direkt zur Bearbeitung öffnen.

**D03 – aktuelle Editor-Ergänzung (PR #183, CI-Abnahme bestanden):**
Ein Wechsel der nativen Projektdatei erfordert bei noch offenen
NPC-Sprechfolgenentwürfen eine ausdrückliche Bestätigung.
Abbrechen erhält den bestehenden Projekt- und Sitzungsspeicher;
Bestätigen lädt die neue Datei und setzt den Entwurfsspeicher zurück.
Kein neuer Opcode, keine Änderung an COST-/Projektformat oder
Capability-Status. Core-, Chromium- und stock-ScummVM-CI je
zweimal grün (Runs `43013379811`, `43013386797`,
`43013379816`, `43013386909`, `43013379961`,
`43013386770`). Menschliche UI-Abnahme offen.
Nächstes Editorpaket: Betroffene Dialogzeilen und Blickrichtungen
im Bestätigungsdialog aufzählen.

**D03 – aktuelle Editor-Ergänzung (PR #182, CI-Abnahme bestanden):**
Ungespeicherte NPC-Sprechfolgenentwürfe bleiben je Dialogzeile und
Blickrichtung innerhalb der Editor-Sitzung beim Zielwechsel erhalten.
Auch Frame-Wiederholungen werden wiederhergestellt. Ein neu geladenes
Projekt startet ohne Entwürfe aus der vorherigen Datei. Kein Eingriff
in Projektformat, native COST-/Opcode-Ausgabe oder Capability-Status.
Core-CI zweimal, Chromium-CI zweimal und stock-ScummVM-CI grün
(Runs `43010611586`, `43010618494`, `43010611601`,
`43010618610`, `43010618465`). Menschliche UI-Abnahme offen.
Nächstes Editorpaket: Vor einem Projektdateiwechsel über noch
ungespeicherte Sprechfolgenentwürfe informieren.

**D03 – aktuelle Editor-Ergänzung (PR #181, CI-Abnahme bestanden):**
Der NPC-Sprechfolgeneditor unterscheidet den noch nicht gespeicherten
Entwurf vom nativen Projektstand der gewählten Dialogzeile und
Blickrichtung, auch nach Speichern oder Verwerfen. Frame-Reihenfolge
und Wiederholungen bleiben beim Vergleich relevant. Keine Änderung
an Projektformat, COST-/Opcode-Ausgabe oder Capability-Status.
Core-CI zweimal, Chromium-CI zweimal und stock-ScummVM-CI grün
(Runs `42997451056`, `42997457816`, `42997454461`,
`42997457721`, `42997457852`). Menschliche UI-Abnahme offen.
Nächstes Editorpaket: Ungespeicherte Entwürfe bei Zielwechsel
vor unbeabsichtigtem Verlust schützen.

## Statusmodell

| Status | Bedeutung |
| --- | --- |
| **A** | Quellcodepfad analysiert; relevante Dokumentation verlinkt |
| **I** | Im allgemeinen Adventure-Studio-Projektmodell **und** Export vorhanden (ggf. begrenzt) |
| **T** | Ein gezielter automatisierter Test existiert und war grün |
| **V** | Funktion im tatsächlich exportierten Spiel in stock ScummVM visuell/interaktiv nachgewiesen |
| **–** | Nicht nachgewiesen oder noch offen; bedeutet nicht, dass der native Opcode fehlt |

Zellen markieren **belegte Teilfähigkeiten**, keine universelle
SCUMM-v6-Abdeckung. `I/T/V (Teil)` bedeutet bewusst eine begrenzte
Implementierung. Für „fertig“ müssen der ausgewiesene Zielumfang und
die konkreten Akzeptanzkriterien nachgewiesen sein. Bestehende
CI-Workflows gelten nicht automatisch als erfolgreiche aktuelle Runs.

**D03 – aktuelle Editor-Ergänzung (PR #180, CI-Abnahme bestanden):**
Der Editor kann ungespeicherte NPC-Sprechfolgenänderungen bewusst
verwerfen und die vorhandene native Folge der gewählten Dialogzeile
und Richtung aus dem Projekt wiederherstellen. Veraltete Editor-
Vorschauen werden geleert. Keine Projekt-/Costume-/Opcode-Änderung,
kein Capability-Statuswechsel. Core-/Chromium-CI je zweimal und
stock-ScummVM-CI grün (Merge `2ecc5143`, Runs `42991905022`,
`42991905238`, `42991905095`). Menschliche UI-Abnahme offen.
Nächstes Editorpaket: Entwurf gegenüber gespeichertem Stand als
ungespeichert/identisch kennzeichnen.

**D03 – aktuelle Editor-Ergänzung (PR #179, CI-Abnahme bestanden):**
Ein ausgewählter nummerierter NPC-Sprechfolgeschritt kann direkt
hinter sich dupliziert werden; die Frame-ID muss nicht erneut
ausgewählt werden. Nur der Editorentwurf ändert sich, native
COST-/SCUMM-v6-Ausgabe und Capability-Status bleiben unverändert.
Core-/Chromium-CI je zweimal und stock-ScummVM-CI grün
(Merge `bdf03581`, Runs `42989783006`, `42989782942`,
`42989783195`). Menschliche UI-Abnahme offen. Nächstes Paket:
Editorentwurf verwerfen und gespeicherte Folge wiederherstellen.

**D03 – aktuelle Editor-Ergänzung (PR #178, CI-Abnahme bestanden):**
Der Editor kann einen importierten PNG-Sprechframe unmittelbar vor
oder nach dem gewählten nummerierten Schritt einfügen. Wiederholte
Frames und beliebige gültige Einfügepositionen bleiben erhalten;
kein Schreibvorgang bis zur separaten Speichern-Aktion. Keine
Modell-/COST-/Opcode-Änderung und kein Capability-Statuswechsel.
Core-CI zweimal grün, Chromium im ersten und gezielten dritten
Lauf grün (ein später unabhängiger Sprite-Redo-Testfehler im
zweiten), stock-ScummVM-CI grün (Merge `21ceb449`, Runs
`42986776661`, `42986776696`, `42986776677`). Menschliche
UI-Abnahme offen. Nächstes Paket: ausgewählten Schritt duplizieren.

**D03 – aktuelle Editor-Ergänzung (PR #177, CI-Abnahme bestanden):**
Ein nummerierter NPC-Sprechfolgeschritt kann im Editor durch einen
anderen vorhandenen Costume-Frame ersetzt werden. Index und übrige
Folge bleiben erhalten; die Aktion schreibt keine Modell-/COST-
oder SCUMM-v6-Projektdaten. Kein neuer Opcode und keine Änderung
des Capability-Status. Core-/Chromium-CI je zweimal grün,
stock-ScummVM-CI nach gezielter Wiederholung des bekannten
Frame-Abtast-Timingfehlers grün (Merge `ec865541`, Runs
`42985182737`, `42985183040`, `42985182780`). Menschliche
UI-Abnahme offen. Nächstes Paket: Frame vor/nach gewähltem
Sprechschritt einfügen.

**D03 – aktuelle Editor-Ergänzung (PR #176, CI-Abnahme bestanden):**
Die nummerierte NPC-Sprechfolgenauswahl rendert die tatsächliche
Costume-Pixelpose des ausgewählten Entwurfsschritts. Auch beim
Ändern der Folge bleiben Schritt und Bild gekoppelt; es wird
nichts gespeichert oder an der nativen Engine geändert.
Kein neuer Opcode, keine Änderung des Capability-Status.
Core-/Chromium-CI je zweimal und stock-ScummVM-CI grün
(Merge `1aa9a3e4`, Runs `42983378901`, `42983378864`,
`42983378851`). Menschliche UI-Abnahme offen. Nächstes Paket:
einen vorhandenen nummerierten Schritt direkt durch einen anderen
Costume-Frame ersetzen.

**D03 – aktuelle Editor-Ergänzung (PR #175, CI-Abnahme bestanden):**
Die PNG-Frame-Auswahl des NPC-Sprechfolgeneditors zeigt die
gewählte Pose vor dem Anhängen mit echten Costume-Pixeln. Auswahl
und Bild reagieren auf Projekt-/Sprecherwechsel. Kein Modell-/COST-
oder Opcode-Eingriff und keine Änderung des Capability-Status.
Core-/Chromium-CI je zweimal grün (Merge `b41ae487`, Runs
`42981767588`, `42981767768`). Kein neuer ScummVM-Run für
den rein lesenden UI-Diff; letzter nativer Lauf `42979576719`.
Menschliche UI-Abnahme offen. Nächstes Editorpaket: Pixelbild des
gewählten bereits eingefügten Folgenschritts anzeigen.

**D03 – aktuelle Editor-Ergänzung (PR #174, CI-Abnahme bestanden):**
Sprechfolgen können jetzt im NPC-Dialogeditor per Frame-Dropdown
und nummerierter Schrittauswahl ohne Komma-Texteingabe erstellt,
verschoben und entfernt werden (auch wiederholte Frames).
Erst die vorhandenen Speicher-/Vorlagenaktionen schreiben das
Projekt; keine Modell-/COST-/SCUMM-v6-Opcode-Änderung und keine
Statusänderung der Capability. Core-/Chromium-CI je zweimal,
stock-ScummVM-CI grün (Merge `94a83464`, Runs `42979576693`,
`42979576683`, `42979576719`). Menschliche UI-Abnahme offen.
Nächstes Editorpaket: ausgewählte Pose vor dem Anhängen visuell
mit echten Costume-Pixeln zeigen.

**D03 – aktuelle Editor-Ergänzung (PR #173, CI-Abnahme bestanden):**
Der NPC-Dialogeditor kann jetzt auch die noch ungespeicherte
Sprechframe-Folge mit echten COST-Pixeln und einstellbarer Bilddauer
animieren. Die Vorschau validiert Frame-IDs, Ziel und Costume wie
der Speichervorgang, ändert aber keinerlei Projektdaten. Kein neuer
SCUMM-v6-Opcode; die Engine-Abspielrate wird nicht nachgestellt
und der Capability-Status bleibt unverändert. Core-/Chromium-CI
je zweimal, stock-ScummVM-CI grün (Merge `c6204ef8`, Runs
`42977464651`, `42977464576`, `42977464512`). Menschliche
UI-Abnahme offen. Als Nächstes die Framefolge klickbar erstellen
und umsortieren.

**D03 – aktuelle Editor-Ergänzung (PR #172, CI-Abnahme bestanden):**
Gespeicherte NPC-Sprechfolgenvorlagen zeigen vor ihrer Anwendung
zusätzlich eine echte COST-Pixelanimation mit nativen Frame-Versätzen,
gespeicherter Frame-Reihenfolge und frei wählbarer Editor-Bilddauer.
Projekt, zugewiesene Animation und nativer SCUMM-v6-Export bleiben
unverändert; die Engine-Abspielrate wird nicht simuliert. Kein neuer
Opcode und keine Änderung des Capability-Status. Core-/Chromium-CI
je zweimal, stock-ScummVM-CI grün (Merge `a155af14`, Runs
`42975787067`, `42975787111`, `42975787000`). Menschliche
UI-Abnahme offen. Nächstes Editorpaket: ungespeicherte Sprechfolge
vor der Übernahme visuell abspielen.

**D03 – aktuelle Editor-Ergänzung (PR #171, CI-Abnahme bestanden):**
Der NPC-Dialogeditor zeigt vor Anwendung einer gespeicherten
Sprechfolgenvorlage Costume, Framezahl, native Frame-Reihenfolge
und Zielkompatibilität. Bei fehlendem oder fremdem Costume-Ziel
ist die Anwendung deaktiviert; native COST-/SCUMM-v6-Ausgabe und
Capability-Status bleiben unverändert. Core-/Chromium-CI je zweimal
und stock-ScummVM-CI grün (Merge `68d0d207`, Runs `42974596952`,
`42974618351`, `42974597034`, `42974618382`, `42974618367`).
Menschliche UI-Abnahme offen. Nächstes Editorpaket: visuelle
Animationsvorschau der Vorlagenframes.

**D03 – aktuelle Editor-Ergänzung (PR #170, CI-Abnahme bestanden):**
Persistente Sprechfolgenvorlagen können validiert ins editierbare
PNG-Frame-Eingabefeld geladen werden, ohne die native Animation
oder das Projekt zu verändern. Erst das separate Aktualisieren
speichert den Vorlageninhalt. Kein neuer SCUMM-v6-Opcode und keine
Änderung des Capability-Status. Core-/Chromium-CI je zweimal grün,
stock-ScummVM-CI im gezielten Wiederholungslauf nach bekanntem
Timing-Fehler grün (Merge `7798745a`, Runs `42973044194`,
`42973066066`, `42973044123`, `42973065810` Versuch 2,
`42973065817` Versuch 2). Menschliche UI-Abnahme offen.
Nächstes Editorpaket: Vorlageninhalt und Costume vor Anwendung anzeigen.

**D03 – aktuelle Editor-Ergänzung (PR #169, CI-Abnahme bestanden):**
Der Inhalt persistenter NPC-Sprechfolgenvorlagen kann über das
Studio mit validierten Frame-IDs ersetzt werden. Die Bearbeitung
verändert keine bereits zugewiesenen COST-Animationen und fügt
keine nativen Ressourcen hinzu. Core-/Chromium-CI jeweils zweimal,
stock-ScummVM-CI grün (Merge `9dfc6676`, Runs `42972075904`,
`42972095162`, `42972075837`, `42972095157`, `42972095201`).
Menschliche UI-Abnahme offen. Nächste Editorfunktion: Vorlageninhalt
zum Bearbeiten in das Eingabefeld laden.

**D03 – aktuelle Editor-Ergänzung (PR #168, CI-Abnahme bestanden):**
Persistente NPC-Sprechfolgenvorlagen können im Gradio-Editor
umbenannt und gelöscht werden. Namen werden auf Duplikate geprüft;
Löschen ändert keine bereits zugewiesenen COST-Animationen.
Das optionale Projekt-JSON-Feld und der native Exportvertrag bleiben
unverändert. Core-/Chromium-CI je zweimal und stock-ScummVM-CI
bestanden (Merge `9bd627c7`, Runs `42971106128`, `42971131395`,
`42971106080`, `42971131510`, `42971131455`). Menschliche
UI-Abnahme offen. Nächstes Editorpaket: Vorlageninhalt aktualisieren.

**D03 – aktuelle Editor-Ergänzung (PR #167, CI-Abnahme bestanden):**
Benannte NPC-Sprechfolgenvorlagen bleiben nun über Studio-Sitzungen
erhalten: optionales, validiertes Projekt-JSON-Feld mit Costume und
nativen PNG-Frame-IDs, beim Reimport wieder in der UI auswählbar.
Bestehende v1-Dateien ohne Vorlagen bleiben lesbar; native COST-
Ressourcen und SCUMM-v6-Capability-Status unverändert. Core-/Chromium-
CI je zweimal, stock-ScummVM-Inventar-CI grün, stock-ScummVM-Dialog-
CI im Wiederholungslauf nach Timing-Fehler grün (Merge `1584c606`,
Runs `42969447126`, `42969455639`, `42969447250`, `42969455636`,
`42969455797`, `42969455654` Versuch 2). Menschliche UI-Abnahme
offen. Nächstes Editorpaket: Vorlagen umbenennen und entfernen.

**D03 – aktuelle Editor-Ergänzung (PR #166, CI-Abnahme bestanden):**
Benannte Sprechfolgenvorlagen können innerhalb einer Studio-Sitzung
zwischen NPC-Dialogzeilen derselben Costume angewendet werden.
Validierte native Frame-IDs werden pro Zielzeile über den bestehenden
COST-Authoring-Pfad gespeichert; Vorlagen selbst sind nicht Teil
der Projektdatei. Keine Änderung am SCUMM-v6-Opcode-/Ressourcenvertrag
oder der Matrixbewertung. Core-/Chromium-CI je zweimal,
stock-ScummVM-CI grün (Merge `075f76e9`; Runs `42967973393`,
`42967981930`, `42967973479`, `42967981911`, `42967981973`).
Menschliche UI-Abnahme offen. Nächste Editor-Funktion: persistente
Projektvorlagen mit kompatibler JSON-Versionierung.

**D03 – aktuelle Editor-Ergänzung (PR #165, CI-Abnahme bestanden):**
Die NPC-Dialog-Sprite-Sheet-Historie bietet jetzt beschriftete
Bearbeitungsstände und direkte Auswahl jedes verfügbaren Schritts.
Stale Sheet-/Raster-/Zellkontexte und ungültige Auswahlpositionen
werden abgelehnt. Dies ändert keine native COST-/SCUMM-v6-Fähigkeit
oder Matrixbewertung. Core-/Chromium-CI je zweimal und stock-
ScummVM-CI grün (Merge `039f22ad`; Runs `42966089591`,
`42966116983`, `42966089618`, `42966117054`, `42966117068`).
Menschliche UI-Abnahme offen. Nächste Editor-Funktion:
benannte Bildfolgenvorlagen zwischen NPC-Dialogzeilen wiederverwenden.

**D03 – aktuelle Editor-Ergänzung (PR #164, CI-Abnahme bestanden):**
Im visuellen Dialog-Sprite-Sheet-Editor sind jetzt bis zu 20
aufeinanderfolgende Änderungen der Abspielfolge rückgängig machbar
und wiederherstellbar. Die sichtbare Verlaufsposition und der
Sheet-/Raster-/Zell-Kontextschutz betreffen ausschließlich den Editor;
die native COST-/SCUMM-v6-Abdeckung und ihr Status bleiben unverändert.
Core-CI zweimal, Chromium-CI zweimal, stock-ScummVM-CI grün
(Merge `39fa8d07`; Runs `42965034647`, `42965029471`,
`42965034831`, `42965029443`, `42965034645`). Menschliche
UI-Abnahme offen. Nächste Editor-Ergänzung: Historieneinträge
benennen und gezielt anspringen.

**D03 – aktuelle Editor-Ergänzung (PR #163, CI-Abnahme bestanden):**
Die letzte rückgängig gemachte Sprite-Sheet-Folgenänderung kann
per Redo wiederhergestellt werden. Eine neue Bearbeitung löscht den
Redo-Eintrag, Undo nach Redo bleibt möglich; Sheet-, Raster- und
Auswahlwechsel sind durch den kontextgebundenen Editor-State
abgesichert. Keine Änderung am Projektmodell oder nativen
COST-Export. Core-/Chromium-CI je zweimal grün (Browser-Run
`42963555662` mit Undo/Redo/Undo, erneuter Bearbeitung,
Import und JSON-Export); stock-ScummVM-Regression grün
(Run `42963555655`, Merge `0744476c`). D03 bleibt
Teilfähigkeit; menschliche UI-Abnahme und vollständiger
Lippensync bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #162, CI-Abnahme bestanden):**
Die letzte Bearbeitung der freien Dialog-Sprite-Sheet-Abspielfolge
lässt sich im Editor per Undo zurücknehmen. Die Rücknahme verwendet
kontextgebundenen Editor-State und verändert keine schon importierten
nativen COST-Frames. Ein zweites Undo ohne neue Änderung und ein
veralteter Raster-/Auswahlkontext werden abgewiesen. Core-/Chromium-CI
zweimal grün (Browser-Run `42962623007` mit Undo, erneuter
Bearbeitung, neun nativen Importframes und JSON-Export); stock-
ScummVM-Regression grün (Run `42962623016`, Merge `f9c78dd5`).
D03 bleibt eine Teilfähigkeit; menschliche UI-Abnahme und
vollständiger Lippensync bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #161, CI-Abnahme bestanden):**
Ein markierter Sprite-Sheet-Bildblock kann mit beliebiger positiver
Anzahl zusätzlicher Kopien an der gewünschten Position in die
Abspielfolge übernommen werden. Die bestehende validierte Folge
liefert die Bildleiste und den nativen COST-Frame-Stapel; die
Batch-Funktion schützt das temporäre PNG-Editor-Staging mit einem
expliziten Limit von 2048 Abspielbildern (keine SCUMM-v6-Grenze).
Core-/Chromium-CI je zweimal grün, Chromium-Pixel-/Neun-Frame-
Import-/Export-Nachweis (Run `42961680499`) und stock-ScummVM-
Regression (Run `42961680844`, Merge `0ff8a565`) bestanden.
D03 bleibt eine Teilfähigkeit; menschliche UI-Abnahme und
vollständiger Lippensync bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #160, CI-Abnahme bestanden):**
Ein visuell gewählter Sprite-Sheet-Bildblock kann unter Erhalt seiner
internen Reihenfolge an eine beliebige Grenze der ursprünglichen
Abspielfolge versetzt werden. Ungültige Ziele werden abgelehnt, Ziele
innerhalb des Blocks verändern nichts; der bestehende native
COST-Import verwendet die neue Abspielreihenfolge. Core- und Chromium-
CI je zweimal grün (Browser-Run `42960294415`); stock-ScummVM-
Regression im zweiten Versuch grün (Run `42960294253`, Attempt 2,
Merge `6c5d979e`). Im ersten nativen Versuch war eine unveränderte
Richtungs-Sprechprobe durch nicht reproduzierbare Frame-Abtastung
fehlgeschlagen; dies bleibt als Teststabilitätsrisiko beobachtbar.
D03 bleibt eine Teilfähigkeit; menschliche UI-Abnahme und
vollständiger Lippensync bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #159, CI-Abnahme bestanden):**
Zusammenhängende Sprite-Sheet-Abspielbilder können im Dialogeditor
gemeinsam entfernt werden, sofern keine Quellzelle ihre letzte Kopie
verliert. Die Operation ist atomar und nutzt die bestehende validierte
Sequenz für den nativen COST-Import. Core- und Chromium-CI zweimal
grün; Chromium belegt Button, Restpixel, fünf native Importframes und
JSON-Export (Run `42959011637`), stock-ScummVM-Regression grün
(Run `42959011475`, Merge `d1e810fa`). D03 bleibt eine
Teilfähigkeit; menschliche UI-Abnahme und vollständiger Lippensync
bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #158, CI-Abnahme bestanden):**
Ein zusammenhängender Bildblock der Sprite-Sheet-Abspielfolge kann an
jeder Position einschließlich vor dem ersten Bild und mitten im
Ausgangsblock kopiert werden. Das Studio validiert Auswahl und
Zielposition, erhält die Originalsequenz und exportiert die verlängerte
Folge über den bestehenden nativen COST-Pfad. 334 lokale Tests laut
PR, Chromium-Pixel-/Import-/Export-Nachweis (Run `42958026815`) und
stock-ScummVM-Regression (Run `42958026806`, Merge `fea8d462`)
bestanden. D03 bleibt eine Teilfähigkeit; menschliche UI-Abnahme und
vollständiger Lippensync bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #156, CI-Abnahme bestanden):**
Ein zusammenhängender Abschnitt der visuellen Sprite-Sheet-Folge lässt
sich über Startbild und Blockende markieren und gemeinsam nach vorne
oder hinten verschieben. Die interne Abspielreihenfolge bleibt erhalten;
die native COST-Sequenz nutzt dieselbe validierte Zellfolge. 334 lokale
Tests, Chromium-Blockauswahl-/Pixel-/Import-/Export-Nachweis (Run
`42956671612`) und stock-ScummVM-Regression (Run `42956671615`,
Merge `18fa208`) bestanden. D03 bleibt eine Teilfähigkeit;
menschliche UI-Abnahme und vollständiger Lippensync bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #154, CI-Abnahme bestanden):**
Abspielbilder einer frei zusammengestellten Dialog-Sprite-Sheet-Folge
lassen sich direkt aus der visuellen Leiste einzeln vor- oder
zurücksetzen. Die Aktion erhält Zellanzahlen und native Frame-Zuordnung;
ungültige Positionen werden abgelehnt. 334 lokale Tests,
Chromium-Verschieben-/Pixel-/Import-/Export-Nachweis (Run `42955411892`)
und stock-ScummVM-Regression (Run `42955412129`, Merge `eb28062`)
bestanden. D03 bleibt eine Teilfähigkeit; menschliche UI-Abnahme und
vollständiger Lippensync bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #152, CI-Abnahme bestanden):**
Eine anklickbare Bildleiste bildet die exakte Sequenz der nativen
Dialog-Sprite-Sheet-Frames ab, einschließlich wiederholter Zellen.
Der Bildklick wählt die Abspielposition für die bestehenden Aktionen;
bei null ausgewählten Zellen bleibt die Leiste leer. 334 lokale Tests,
Chromium-Pixel-/Positions-/Import-/Export-Nachweis (Run `42954277816`)
und stock-ScummVM-Regression (Run `42954277828`, Merge `169e21a`)
bestanden. D03 bleibt eine Teilfähigkeit; menschliche UI-Abnahme und
vollständiger Lippensync bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #150, CI-Abnahme bestanden):**
Die frei konfigurierbare Sprite-Sheet-Sequenz lässt sich über eine
Quellzellen- und Positionsauswahl einfügen, bearbeiten und zurücksetzen.
Die letzte Kopie jeder eingeschlossenen Zelle ist geschützt; GIF und
nativer COST-Import verwenden die gleiche validierte Reihenfolge.
334 lokale Tests sowie Chromium-UI-/Import-/Export-Nachweis (Run
`42952683261`) und stock-ScummVM-Regression (Run `42952683322`,
Merge `eb82f1b`) bestanden. D03 bleibt eine Teilfähigkeit;
menschliche UI-Abnahme und vollständiger Lippensync bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #148, CI-Abnahme bestanden):**
Eine frei angegebene Sequenz aus PNG-Sprite-Sheet-Zellnummern erlaubt
wiederholte Frames an beliebigen Abspielpositionen. Die gleiche
validierte Zellfolge steuert Editor-GIF und native COST-Frame-IDs;
Editoraktionen schreiben weiterhin nicht selbst ins Projektmodell.
334 lokale Tests, realer Chromium-Korrektur-/Pixel-/Import-/JSON-Export-
Nachweis (Run `42951315398`) und vollständige stock-ScummVM-
Regression (Run `42951315529`, Merge `36cb68a`) bestanden.
D03 bleibt eine Teilfähigkeit; menschliche UI-Abnahme und
vollständiger Lippensync bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #146, CI-Abnahme bestanden):**
Ausgewählte PNG-Sprite-Sheet-Zellen können mehrfach direkt hintereinander
in die vorbereitete native Dialoganimation übernommen werden. Jede
Kopie erhält eine eigene stabile Frame-ID, und die GIF-Vorschau
entspricht der erweiterten Abspielzeit. 334 lokale Tests, echter
Chromium-Wiederholungs-/GIF-/Import-/JSON-Export-Nachweis (Run
`42949528331`) sowie vollständige stock-ScummVM-Regression (Run
`42949528349`, Merge `496814a`) bestanden. D03 bleibt eine
Teilfähigkeit; menschliche UI-Abnahme und vollständiger Lippensync
bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #144, CI-Abnahme bestanden):**
Die bereits gewählte PNG-Sprite-Sheet-Abspielreihenfolge lässt sich vor
der nativen COST-Übernahme als Editor-GIF mit einstellbarer Framezeit
und unveränderten PNG-Zellpixeln abspielen. Die Vorschau hat keine
Auswirkung auf das Projektmodell oder native ScummVM-Timing. 334 lokale
Tests, Chromium-Pixel-/Timing-/Import-/JSON-Export-Nachweis (Run
`42948204777`) und vollständige stock-ScummVM-Regression (Run
`42948204871`, Merge `648b856`) bestanden. D03 bleibt eine
Teilfähigkeit; menschliche UI-Abnahme und vollständiger Lippensync
bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #142, CI-Abnahme bestanden):**
Die Abspielreihenfolge der ausgewählten Sprite-Sheet-Zellen lässt sich
in der Schnittvorschau verändern und vor dem nativen COST-Import
kontrollieren. Ausgeschlossene Zellen bleiben wiederaufnehmbar;
der native Frame-Stapel folgt der gewählten Reihenfolge. 334 lokale
Tests, realer Chromium-Import-/JSON-Export-Nachweis (Run
`42946980608`) und vollständige stock-ScummVM-Regression (Run
`42946980481`, Merge `8409083`) bestanden. D03 bleibt eine
Teilfähigkeit; menschliche UI-Abnahme und vollständiger Lippensync
bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #140, CI-Abnahme bestanden):**
Einzelne Zellen eines PNG-Sprite-Sheets können in der Schnittvorschau
vorbereitet, ausgeschlossen und wieder aufgenommen werden; nur die
ausgewählten Rasterzellen gelangen in den nativen COST-Stapelimport.
Die bestehende atomare Importvorprüfung bleibt maßgeblich. 334 lokale
Tests, Chromium-Auswahl-/Import-/JSON-Export-Nachweis (Run
`42944948283`) und vollständige stock-ScummVM-Regression (Run
`42944948354`, Merge `61d4484`) bestanden. D03 bleibt eine
Teilfähigkeit; menschliche UI-Abnahme und vollständiger Lippensync
bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #138, CI-Abnahme bestanden):**
Die Sprite-Sheet-Raster-/Schnittvorschau zeigt vor dem Hinzufügen
die exakten Bildzellen und eingezeichneten Grenzen. Sie verwendet
dasselbe Raster wie die später nativ importierten COST-Frames;
fehlerhafte Parameter werden ohne Projektänderung angezeigt.
334 lokale Tests, Chromium-Vorschau-/Pixel-/Import-/JSON-Export-
Nachweis (Run `42943608437`) und vollständige stock-ScummVM-
Regression (Run `42943608322`, Merge `5f3fc04`) bestanden.
D03 bleibt eine Teilfähigkeit; menschliche UI-Abnahme und
vollständiger Lippensync bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #136, CI-Abnahme bestanden):**
Für den vorbereiteten Sprite-Sheet-Import können horizontale und
vertikale Außenränder und Zellabstände unabhängig festgelegt werden;
Frame-Ausschnitte sind ohne Skalierung und Randpixel im bestehenden
nativen COST-Pfad nutzbar. 334 lokale Tests, realer Chromium-Pixel-/
Import-/JSON-Export-Nachweis (Run `42942425274`) und vollständige
stock-ScummVM-Regression (Run `42942425281`, Merge `396b9e8`)
bestanden. D03 bleibt eine Teilfähigkeit; menschliche UI-Abnahme und
vollständiger Lippensync bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #134, CI-Abnahme bestanden):**
Ein PNG-Sprite-Sheet mit frei angegebenem Spalten-/Zeilenraster lässt
sich im NPC-Dialogeditor in separate native Animationsframes zerlegen,
die zeilenweise an eine bestehende Importauswahl angehängt werden.
Der etablierte PNG-zu-COST-Pfad und die atomare Vorprüfung bleiben
unverändert. 334 lokale Tests, Chromium-Pixel-/Import-/JSON-Export-
Nachweis (Run `42940798599`) und vollständige stock-ScummVM-
Regression im unveränderten zweiten Lauf (Run `42940798619`,
Merge `7972b25`) bestanden. D03 bleibt
eine Teilfähigkeit, menschliche UI-Abnahme und vollständiger Lippensync
offen.

**D03 – aktuelle Editor-Ergänzung (PR #132, CI-Abnahme bestanden):**
Alle Konflikte der nativen Frame-IDs im vorbereiteten Dialog-PNG-Stapel
lassen sich jetzt in einem Schritt auflösen; bereits freie IDs,
Auswahlreihenfolge und ausgeschlossene Uploads bleiben erhalten. Die
atomare COST-Importgrenze und der exportierte SCUMM-v6-Pfad sind
unverändert. 334 lokale Tests, echter Chromium-Bedien-/JSON-Exportpfad
(Run `42939456742`) und vollständige stock-ScummVM-Regression
(Run `42939456814`, Merge `c3ee855`) bestanden. D03 bleibt eine
Teilfähigkeit; menschliche UI-Abnahme und vollständiger Lippensync
bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #130, CI-Abnahme bestanden):**
Für vorbereitete Dialog-PNGs können freie native Frame-IDs jetzt
direkt vergeben werden. Der Vorschlag berücksichtigt bestehende
Costume-Frames und andere eingeschlossene PNGs; der Import bleibt
atomar und die native COST-Abbildung unverändert. 334 lokale Tests,
Chromium mit zweifacher Konfliktauflösung und erneutem JSON-Export
(Run `42938168138`), stock ScummVM mit vollständiger Regression
(Run `42938168094`, Merge `854ca84`) bestanden. D03 bleibt eine
Teilfähigkeit; menschliche UI-Abnahme und vollständiger Lippensync
bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #128, CI-Abnahme bestanden):**
Vorbereitete Dialog-PNGs können jetzt ohne externe Dateiumbenennung
eine selbst gewählte native Frame-ID erhalten. Diese bleibt beim
Umordnen und Ausschließen stabil und wird für Vorprüfung und nativen
COST-Import genutzt; doppelte IDs blockieren den atomaren Import.
334 lokale Tests, Chromium-Bedienung mit Pixelvorschau/JSON-Export
(Run `42936784836`, unveränderter zweiter Lauf) und vollständige
stock-ScummVM-Regression (Run `42936784961`, Merge `d96954d`)
bestanden. D03 bleibt ausdrücklich eine Teilfähigkeit; menschliche
UI-Abnahme und vollständiger Lippensync bleiben offen.

**D03 – aktuelle Editor-Ergänzung (PR #126, CI-Abnahme bestanden):**
Die vorbereitete native 1..N-Dialog-PNG-Folge unterstützt jetzt den
gezielten Austausch eines ausgewählten Bilds per Einzelupload, ohne
Sortierung, Ausschlüsse oder andere Uploads zu verlieren. Unit-Tests
prüfen den direkten Pfad bis zum nativen Stapelimport; Chromium
bestätigt Austausch, Pixelvorschau und JSON-Export (Run `42934763618`),
stock ScummVM die unveränderte Dialog-/Rezept-Regression im zweiten
Lauf (Run `42934763594`, Merge `eca2568`). Die D03-Teilstatus und
die offenen menschlichen UI-/vollständigen Lippensync-Abnahmen bleiben
unverändert.

Die folgenden Nachweise stammen aus den früheren
[Source-Audits](scumm-v6-source-audit.md),
[Ressourcen-Audits](scumm-v6-export-gap-analysis.md),
dem sichtbaren Projektmodell und der
[bestehenden Roadmap](roadmap.md). Bei Änderungen bitte Links auf
konkrete Tests/Commits ergänzen, nicht nur Statusbuchstaben setzen.

## 1. Räume, Grafiken und Bildkomposition

| ID | Fähigkeit | Analyse | Studio | Test | ScummVM | Nächstes Gate |
| --- | --- | --- | --- | --- | --- | --- |
| R01 | Indizierte Room-Bitmaps/Paletten | A | I | T | V (Teil) | Mehrere Größen/Paletten |
| R02 | SMAP-Strip-Encoding und Ressourcenblöcke | A | I via ScummC | T (Teil) | V (Teil) | Unabhängiger Binär-Roundtrip P0.1 |
| R03 | 8-Pixel-Breitenvalidierung | A | I | T | – | Zu Opcode/Masken-Gates erweitern |
| R04 | Mehrere Räume und Entry-/Exit-Scripts | A | I (Teil) | T | V (Teil) | Script-Lifetime bei Wechsel |
| R05 | Objektbilder mit mehreren States | A | I (Teil) | T | V (Teil) | N Zustände/Parent-States |
| R06 | ZPxx-Masken der Raumgrafik | A | I (Teil: Studio-PNG→RoomAsset/JSON→ScummC-BMP/ZPxx) | T (Teil: PNG-Import/Story-Komposition/Binär-/Chromium-Tests) | V (Teil: stock ScummVM Run 43073010730, 350 Actor-Pixel durch authorierte Maske verdeckt) | Mehr-Ebenen-Authoring und allgemeine Engine-Varianten/Grenzen |
| R07 | Objektbilder mit Z-Masken | A | – | – | – | Writer/Decoder-Fixture |
| R08 | Walkbox-Polygone und Maskennummern | A (Teil) | I (Teil: RoomAsset/JSON, BOXD) | T (Teil: Box-Writer) | V (Teil: native Fixture) | Frei authorierte Polygone und allgemeine Laufgrenzen |
| R09 | Walkbox-Verbindungen/Wege | A (Teil) | I (Teil: BOXM, Routendaten) | T (Teil: Binär-/Validierungstest) | V (Teil: native Fixture) | Allgemeines Boxennetz mit Spieler-Klickrouten |
| R10 | Perspektive/SCAL und Box-Skalierung | A | I (Teil: SCAL-Slots und Kurven) | T (Teil: Skalierungs-Probe) | V (Teil: native Vergleichsprobe) | Allgemeine Kurven/Actor-Skalierung und Spielvarianten |
| R11 | Actor-zu-Actor-Tiefe / Sam-&-Max-Sortierung | A | – | – | – | Sichtreihenfolge in v6 |
| R12 | Palette-Cycling/Wasser-Effekte | A | I (Teil) | T | V (Teil) | Andere Effektprofile |
| R13 | Raum-/Actor-Paletten, Shadow, Tint | A (Teil) | – | – | – | Native Operationen/Paletten |
| R14 | Raum-Wackeln, Fade und Übergangseffekte | A | – | – | – | Effekt-/Roomwechsel-Fixture |

## 2. Actors, Costumes und Animationen

| ID | Fähigkeit | Analyse | Studio | Test | ScummVM | Nächstes Gate |
| --- | --- | --- | --- | --- | --- | --- |
| A01 | Native Actor-Costume-Ressourcen | A | I (COST + Projekt-JSON/Actor-Bindung; PNG-Import und Actor-Anlage im Studio) | T | V (Fixture und sichtbare Studio-PNG-Frames in ScummVM, CI `42494840322`; Verb-Interaktion offen) | Unabhängigere Actor-Spielbindung und Interaktionsablauf |
| A02 | Actor-Platzierung/Richtung/Teleport | A (Teil) | I (Anfangsposition/Richtung; Actor im selben Raum versetzen und per `face_actor` N/E/S/W drehen) | T | V (Teil: Mehr-Actor-Fixture und erfolgreiches Verb-Klick-Script mit Versetzen/Drehen, CI `42501905023`; Zwischenbilder offen) | Actor-Position und Drehung in ScummVM einzeln visuell nachweisen, freier Spieler-Actor |
| A03 | Actor-Walk/Pathfinding/Speed | A | I (Demo sowie freie `walk_actor`- und `wait_actor`-Interaktionsschritte zu Raumkoordinaten bzw. Ankunft) | T (Teil) | V (Teil: Demo und abgeschlossener Studio-Verbablauf mit Walk/Wait, CI `42501905023`; konkreter Weg/Ankunftspunkt nicht isoliert belegt) | Laufpfad und Ankunfts-Wait des Projekt-Actors visuell nachweisen |
| A04 | Stand-/Walk-/Talk-Costume-Frames | A | I (Frames/Richtungen, Startanimation einschließlich Studio-Auswahl/Deaktivierung, deklarative Verb-Animationen; Studio-PNG-Frames, Mehrframe-COST-Folgen, visuelle Timeline und GIF-Editor-Wiedergabe; Story+Actors speicherbar) | T (Teil) | V (Teil: Erststart, Room-Reentry, sichtbarer Mehrframe-Wechsel aus Studio-PNGs `42494840322` und abgeschlossener Verb-Ablauf `42501905023`; dessen Animationsframes noch nicht isoliert belegt) | Wiederholte Verb-Animation und Zwischenframes im laufenden Spiel prüfen |
| A05 | Actor-Skalierung/Z-Clip/Verdeckung | A | – | – | – | R06/R10 + Actor |
| A06 | Costume-`COUNT` und Abfrage | A | I (COST-Cues) | T | V (Ego- und Projekt-Actor-Fixtures) | Allgemeiner Action-/Condition-Export |
| A07 | Aktion während laufender Animation | A (Teil) | I (COUNT → Objektzustand; deklarative Push/Pull/Open/Close-Eingabegrenze mit zwei Zustandsausgängen) | T (JSON/ScummC + 0/1/2-Klick-, Rückkehr- und Save/Load-Fälle) | V (Teil: Push früh/spät/wiederholt; kein COUNT-Replay beim Room-Reentry oder nach Save/Load) | Mehrfach-Window-Reaktionen, explizite Animations-Neustarts, Save/Load während aktiver Animation und allgemeine Action-/Condition-IR |
| A08 | Mehrere synchronisierte Actors | A (Teil) | – | – | – | Koordinierte Scriptslots |
| A09 | Figur/Objekt-Einstieg, Abfahrt, Reaktion | A (Konzept) | – | – | – | Filmische End-to-End-Sequenz |
| A10 | Actor-Talk-Position/Blase/Portrait | A (Teil) | – | – | – | Text-/Costume-/Talk-Fixture |

## 3. Objekte, Verbsteuerung und Inventar

| ID | Fähigkeit | Analyse | Studio | Test | ScummVM | Nächstes Gate |
| --- | --- | --- | --- | --- | --- | --- |
| O01 | Room-Hotspots und Verbs | A | I (Teil) | T | V (Teil) | Weitere Verben/Profiles |
| O02 | Objekt-Sichtbarkeit/Zustandswechsel | A | I (Teil) | T | V (Teil) | Parent-State-Hierarchie |
| O03 | `drawObjectAt` und bewegte Hitbox | A | – | – | – | Position+Klick gemeinsam |
| O04 | Objekt-Parent/Child/Untouchable | A | – | – | – | OBCD-Attribute, Klicktest |
| O05 | Aufnehmen/Inventory-Owner | A | I (Teil) | T | V (Teil) | Varianten/Grenzen |
| O06 | Use Objekt mit Objekt | A | I (Teil) | T | V (Teil) | Bedingungs-/Script-Regeln |
| O07 | Inventar-Kombinationsrezepte | A (Teil) | I (Teil) | T (Teil) | offen | Prüfen: aktuell grünes Gameplay |
| O08 | Mehrstufige Zustands-/Rätselketten | A | I (Teil) | T | V (Teil) | Generische Zustandsgraphen |
| O09 | Dynamisches Inventar-Layout/Scrollen | A (Teil) | I (Demo) | T (Teil) | offen | Allgemeines Item-Layout |
| O10 | Sam-&-Max-Klickmodell versus Verb-UI | A | – | – | – | Spielprofilspezifische Input-Scripts |

## 4. Scripts, Cutscenes und Kamera

| ID | Fähigkeit | Analyse | Studio | Test | ScummVM | Nächstes Gate |
| --- | --- | --- | --- | --- | --- | --- |
| S01 | Native Script-/Objektscript-Lifetime | A | I (Teil: Studio-Verbfolgen mit Zustandsalternativen und optionalem Escape-Skip) | T (Teil: JSON-/ScummC-Vertrag und Skip-Commit) | V (Teil: drei Klicks desselben Verbs schalten native Objektzustände 1 → 2 → 1 → 2, CI `42506834029`) | Raumwechsel-/Slot-Test und allgemeinere Abbruchfälle |
| S02 | Parallele Scripts/`breakHere`/Wait/Freeze | A | – | – | – | Scheduler-Szenarien |
| S03 | Cutscene-Stack/`begin`/`end` | A | – | – | – | Native Sequenz |
| S04 | Skip-/Override-Endzustand | A | I (Teil: Studio-Verbsequenz mit Objekt-/Actor-/Inventar-/Raum-Endzustand, letztem Musik-Cue und letztem Cue je VOC-Sound-ID) | T (Teil: ScummC-`try`/`override`, JSON-Roundtrip, terminales `startRoom`, Musik- und Sound-Commit) | V (Teil: Escape mit Actor-/Inventareffekt, `Harbor → Cellar → Harbor` und MIDI-Stop/Wiederstart mit PCM-Gate, CI `42517572328`; VOC-Soundstop per PCM-Gate, CI `42522610786`) | Allgemeinere Abbrüche |
| S05 | Kamerasprung `setCameraAt` | A | I (Raum-Cues) | T | V (Raum) | Allgemeiner Shot-/Cutscene-Export |
| S06 | Horizontaler Pan + `waitForCamera` | A | I (Raum-Cues) | T | V (Raum) | Multi-Track-/Cutscene-Synchronisation |
| S07 | Camera-Follows-Actor | A | – | – | – | Follow/Abbruch |
| S08 | Shot: Totale/Nahaufnahme/Schnitt | A (Konzept) | – | – | – | Native Raum-/Bild-Komposition |
| S09 | Parallel laufende Aktionen in Cutscene | A (Teil) | – | – | – | Multi-Track-Export |
| S10 | Interaktion im bewegten Fahrgeschäft | A (Teil) | – | – | – | COUNT/Input/Objekt-Test |

## 5. Dialog, Audio und Persistenz

| ID | Fähigkeit | Analyse | Studio | Test | ScummVM | Nächstes Gate |
| --- | --- | --- | --- | --- | --- | --- |
| D01 | Einfache Textausgabe | A (Teil) | I | T | V (Teil) | Echte NPC-Talk-UI |
| D02 | Verzweigte Gespräche/Antwortoptionen | A (Teil) | I (Teil: mehrstufige NPC-Auswahlgraphen und Rücksprung zu Einstiegsoptionen; VOC-Sprachvarianten auch in späteren Stufen) | T (Teil: JSON-/Editor-/SCUMM-Quelltest, 297 lokal) | V (Teil: native Mehrstufen-/Rückwegprobe mit sichtbar wechselnden Antwortobjekten und sauberem Dialogende, CI `42536777733`; VOC-Dialogprobe CI `42533774527`) | Echte Menü-UI, Sprecherwechsel |
| D03 | Mehrere Sprecher/Costume-Lippensync | A (Teil) | I (Teil: Sprecher pro Dialogzeile, Actor-Blickrichtung und PNG-Sprechpose aus dem Studio; Frames direkt an der nativen Dialogzeile auswählbar und mit einem Klick als Geste gebunden; Schutz vor geteilter Costume; COST-Slots `stand` 12, `talk_start` 16, `talk_stop` 20, Geste 24 und weitere zeilenspezifische Posen und eigenständige, je N/E/S/W editierbare Mehrframe-Sprechfolgen ab 28 ohne Überschreiben bestehender Talk-Frames; `actorSay`/`animateActor`/optionaler Stand-Endzustand; im Costume-Editor je Blickrichtung ein eigener importierter PNG-Frame oder eine native, wiederholte Mehrframe-Sprechfolge für `gesture`/`talk_start` setzbar) | T (Teil: JSON-Roundtrip, zwei native Sprecher, Stand-/Talk-Slot-Validierung, SCUMM-Quelltest, PNG-zu-COST-Dialogpfad sowie zwei unterschiedliche Posen derselben Figur mit stabiler Indexwiederverwendung; Richtungszuweisung und Mehrframe-Sprechfolge mit Erhalt der anderen Richtungen, JSON-Roundtrip und COST-Quellprüfung; eigenständige, wiederbearbeitbare COST-Sequenzen für zwei Zeilen derselben Figur im Modell/SCUMM-Quelltest; richtungsbezogener Erhalt der drei anderen Kanäle und der zweiten Zeile; grafische Zeilen-/Richtungs-Timeline mit Frame-Anhängen, -Verschieben, -Entfernen und GIF-Editorvorschau; pro Dialogzeile einstellbarer nativer Gesture-Vorlauf und Mindestlaufzeit als `delay`-Ticks mit Legacy-Defaults 1/60; optionale Abschluss-COST-Animation nach `waitForMessage` mit positiver Tick-Laufzeit vor der Standpose; eigene Abschluss-PNG-Timeline und direkter PNG-Dateiimport mit Palettenvalidierung für Sprech- und Abschlussfolge je Dialogzeile/Richtung; sichere Copy-on-write-Vereinzelung einer geteilten Costume für den gewählten Sprecher mit Erhalt der anderen Actors; atomarer 1..N-PNG-Stapelimport in Auswahlreihenfolge und Voranzeige nativer Frame-IDs für zeilenspezifische Sprech-/Abschlussfolgen; grafisches Umordnen der Upload-Auswahl vor dem atomaren Stapelimport mit synchroner Vorschau und Zurücksetzen bei Dateiauswahl; gezieltes Ausschließen einzelner hochgeladener PNGs aus der Importauswahl ohne erneuten Upload, mit stabiler Reihenfolge, atomarem COST-Export und Ablehnung leerer Auswahl; Wiederaufnehmen ausgeschlossener, weiterhin hochgeladener PNGs ans Folgenende ohne neuen Upload, inklusive 0-zu-1 und erneuter Bearbeitung; echte pixelbasierte PNG-Miniaturgalerie der vorbereiteten COST-Importauswahl mit synchroner Reihenfolge bei Umordnen/Ausschließen/Wiederaufnehmen) | V (Teil: **sichtbare NPC-Sprechpose und Rückkehr zur Standpose im unveränderten ScummVM nachgewiesen**: 256 rote Gestenpixel statt 0 initial, anschließend 6 aufeinanderfolgende Frames mit 0 Gestenpixeln; GitHub-Commit `1edcf0c5`, Dialog-CI erfolgreich; zusätzlich zwei farblich unterscheidbare Sprechposen derselben Figur im nativen ScummVM-Dialogschritt auf PR #81 erfolgreich; reale automatisierte Chromium-Gradio-Bedienfolge inklusive Projektimport, Pose-Zuweisung, JSON-Export und Reimport erfolgreich, zusätzlich statische PNG-Pose-Vorschau aus nativen Palette-/Frame-Pixeln im Chromium-Browser mit roter und grüner Pixelprüfung nach Zeilenwechsel und Reimport nachgewiesen; menschliche UI-Abnahme offen; zusätzliche native Richtungs-Sprechpose als separates COST-Einzelbild je N/E/S/W im Gradio-Editor mit Pixel- und Richtungsbeschriftungsprüfung umgesetzt, native Dreh-/Sprech-Gameplay mit vier unterschiedlichen Farbframes und sechs stabilen Standframes bestanden (CI `42883775730`, Job `130066624232`, Code-Commit `6902dc7`; außerdem **zwei unterschiedliche Sprechframes innerhalb derselben Dialogzeile** mit Rückkehr zu sechs Standframes in stock ScummVM, CI `42886572422`, Job `130076341678`, Merge `634afb6`; **zwei eigenständige Mehrframe-Zeilen derselben Figur** in stock ScummVM mit anschließendem Standzustand nachgewiesen, Run `42890566896`, Job `130090292878`, Merge `482375e`; Gradio-Chromium-Export/Reimport zweier Zeilensequenzen ebenfalls bestanden; **Richtungskanäle zweier NPC-Zeilen** mit W-rot/grün und E-blau/gelb im stock ScummVM, inklusive Gradio-Chromium-Authoring und JSON-Reimport, bestanden: CI `42895287701`, Job `130106686621`, Merge `270be816`; **grafische Zeilen-/Richtungs-Timeline** mit Anhängen, Verschieben, Entfernen, GIF-Editorvorschau und Export/Reimport im Chromium bestanden (CI `42898953018`, PR #95, Merge `3410035`; **zwei native Sprechphasen pro Dialogzeile** mit 12/90-Tick-W und unveränderter 1/60-Tick-E-Geste im stock ScummVM bestanden, inklusive Chromium-Export/Reimport: CI `42901243477`, Job `130127449346`, Merge `208e619`; **optionale native Abschlussgeste je Zeile** mit magentafarbenem COST-Frame nach W-Rot/Grün und vor E-Blau/Gelb samt Standrückkehr im stock ScummVM und Chromium-Authoring bestanden: Run `42904734152`, Job `130139641706`, Merge `ead868b`; **direkt im Gradio-Dialogeditor erzeugte Abschluss-PNG-Folge** mit eigenem COST-Slot, Chromium-Export/Reimport und magentafarbenem Abschlussframe nach W-Sprechen und vor E-Sprechen im stock ScummVM bestanden: PR #101, Jobs `130151091545` und `130151090189`, Merge `8557ea0`; **direkter PNG-Dateiimport im NPC-Dialogeditor** für Sprech-/Abschlussfolge mit Chromium-Upload/Export/Reimport und nativer Magenta-Abschlussgeste zwischen W-/E-Sprechen und Standrückkehr im stock ScummVM bestanden: PR #103, Jobs `130161049750` / `130161082960` / `130161083496`, Merge `1cc99f7`; **Copy-on-write-Vereinzelung einer geteilten Sprecher-Costume direkt im Dialogeditor** mit Erhalt anderer Actor-Ressourcen, Chromium-PNG-Import/Export und nativer Magenta-Abschlussgeste samt Standrückkehr im stock ScummVM bestanden: PR #105, native Jobs `130167489043` / `130167388424`, Browser `130167488068` / `130167388133`, Merge `1595e1c`; **geordneter 1..N-PNG-Stapelimport direkt im Dialogeditor** mit Dateinamen-/Frame-ID-Vorschau, Chromium-Mehrfachupload/Export und zweiframiger nativer Abschlussanimation vor Ost-Sprechen samt Standrückkehr im stock ScummVM bestanden: PR #107, native Job `130175052358`, Chromium `130175056189` / `130175014763`, Merge `a685897`; **grafische Umsortierung der vorab hochgeladenen PNG-Folge** mit Chromium-Auswahl-/Verschiebeprüfung, geordneter Vorschau und Export/Reimport in zwei UI-Läufen und bestehendem nativen zweiframigem Abschlussdialog samt Standpose im stock ScummVM bestanden: PR #109, Chromium Jobs `130181832614` / `130181718511`, native Jobs `130181832477` / `130181719158`, Merge `e974946`; **einzelne hochgeladene PNGs vor dem nativen Stapelimport gezielt ausgeschlossen** bei stabiler Sortierung: zwei erfolgreiche Chromium-Abläufe mit Drei-Dateien-Auswahl, Ausschluss des dritten Bilds und JSON-Export/Reimport, ein stock-ScummVM-Lauf mit bestehender zweiframiger Abschlussgeste und Standrückkehr bestanden: PR #111, Chromium Jobs `130188492998` / `130188465475`, native Job `130188494313`, Merge `33c28f5`; **ausgeschlossene Upload-PNGs ohne Neu-Upload wieder aufgenommen** mit Chromium-Entfernen/Wiederaufnehmen/erneutem Ausschließen und exportierter nativer Folge in zwei erfolgreichen Browser-Läufen, bestehender zweiframiger Dialogabschluss und Standrückkehr in zwei stock-ScummVM-Läufen bestanden: PR #113, Chromium Jobs `130193752594` / `130193639385`, native Jobs `130193752872` / `130196817977`, Merge `36187ac`; **pixelbasierte PNG-Miniaturgalerie vor dem nativen Stapelimport** in realem Chromium mit Farben/Reihenfolge nach Upload, Umsortieren, Entfernen und Wiederaufnehmen sowie JSON-Export/Reimport zweimal bestanden; unveränderter zweiframiger Abschlussdialog mit Standrückkehr in stock ScummVM zweimal bestanden: PR #115, Chromium Jobs `130201926707` / `130201843676`, native Jobs `130201843845` / `130203561023`, Merge `6e495d5`))) | menschliche Gradio-Abnahme, eigenständiger Sichtnachweis für angehängte dritte Zeile, vollständiger Lippensync |
| D04 | Mehrsprachige Textressourcen | A (Teil) | I (Teil: Story-Katalog und VOC-Untertitel mit gemeinsamem CHAR und `GameLanguage` im nativen Export) | T (Teil: gemeinsamer Export-/Sprachverzweigungs-Test, 293 lokal) | V (Teil: gemeinsames deutsches Objektlabel und VOC-Untertitel mit PCM-Escape in stock ScummVM, CI `42531065406`) | Vollständige Story-Übersetzung, Sprecher-Sprachaufnahmen an Dialogknoten |
| U01 | MIDI-/Soundresource | A (Teil) | I (Teil: Studio-MIDI-Import, SOUN-Export, Raumreferenz) | T (Teil: JSON-/Exporter-Test) | V (Teil: Studio-MIDI als native SOUN mit Stop/Start-PCM-Gate in stock ScummVM, CI `42517572328`) | Weitere Soundformate und allgemeines iMUSE |
| U02 | iMUSE-/Music-State-Übergänge | A (Teil) | I (Plan) | T (Plan) | – | Hook-/Beat-Nachweis |
| U03 | VOC-Sprache und Soundeffekte | A (Teil) | I (Teil: VOC-Import, Unicode-Sprachzeilen, eigene Sprach-VOC-/Untertitel-Varianten sowie VOC-Zuordnung zu NPC-Dialogzeilen und Antworten) | T (Teil: JSON-/Exporter-/Unicode-/Dialog-Audiobindungstests, 295 lokal) | V (Teil: VOC-Effekt CI `42522610786`; ASCII-Sprachzeile CI `42524819678`; Umlaut + VOC-Escape CI `42526681259`; Sprachvariante CI `42528788315`; native NPC-Dialog-Stimme und Antwortauswahl CI `42533774527`) | Actor-Lipsync und vollständige Dialoggraphen |
| P01 | Globale Variablen/Objektzustände | A | I (Teil) | T | V (Teil) | Langzeit-/Room-Scope |
| P02 | Save/Load kompletter Spielzustand | A (Teil) | I (Probe) | T (Teil) | offen | Raum+Inventar+Actors |
| P03 | Spielziel/Quest-Fortschritt | A (Projekt) | I (Teil) | T | V (Teil) | Verschiedene Enden |

## 6. Editor-/Compiler-Qualitäten (nicht VM-Opcodes)

| ID | Fähigkeit | Stand | Nächstes Gate |
| --- | --- | --- | --- |
| E01 | Versioniertes JSON-/Story-Modell | I/T (Teil) | Vollständige SCUMM-Mechaniken |
| E02 | Deterministischer SCUMM-Compiler/Linker | I/T (Teil) | Native Gesamt-Abdeckung |
| E03 | Unabhängiger Ressourcen-Binärparser | Offen | P0.1 |
| E04 | Visueller Raum-/Hotspot-Editor | I/T (Demo) | Masken/Walkbox-UI |
| E05 | Actor-/Costume-Editor | Offen | A01–A08 |
| E06 | Cinematic Shot-/Cutscene-Editor | Offen | S03–S09 |
| E07 | Interaktive ScummVM-Vorschau | Probe | Reproduzierbar im Studio |
| E08 | KI-gestützte, validierte Änderungen | I/T (Teil) | Größere Spielmechaniken |
| E09 | Eigene Spielkennung in stock ScummVM | Offen | Separates Kompatibilitäts-Gate |
| E10 | Original-Interpreter-Kompatibilität | Nicht nachgewiesen | Optionales eigenes Gate |

## Bearbeitungsregeln

1. Jede neue Fähigkeit bekommt eine **stabile ID** und ein Testziel.
2. Analyse-Link ist Pflicht, bevor native Kompatibilität behauptet wird.
3. `I` bezieht sich auf **allgemeinen Export**, nicht nur hartkodierte
   Fixture- oder Probe-Module; solche Ausnahmen als „Demo/Probe“ markieren.
4. Für `V` konkrete CI-Run-/Screenshot-/Interaktionsbelege angeben.
5. Nach jedem Arbeitspaket nur die **tatsächlich geänderten** Zeilen
   aktualisieren und den neuen Status in `PROJECT_STATUS.md` spiegeln.
6. Offene Mechaniken anhand der Quellcodebefunde priorisieren,
   nicht anhand der Anzahl früherer grüner Workflows.

Die konkrete Implementierungsreihenfolge für die nächsten Arbeitspakete
steht in [PROJECT_STATUS.md](PROJECT_STATUS.md).
