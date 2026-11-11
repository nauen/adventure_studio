# Adventure Studio – Projektstatus und Chat-Übergabe

Stand: 2026-11-07. **Dies ist die kurze Einstiegseite für jede neue
Arbeitssitzung.** Sie ersetzt nicht die [Roadmap](roadmap.md) oder die
[SCUMM-v6-Funktionsmatrix](SCUMM_V6_CAPABILITIES.md).

**Produktpaket in Prüfung (2026-11-11):** Die vorbereitete native
PNG-Importgalerie kennzeichnet jetzt einzelne Bilder mit `⚠️`, wenn
deren Import in der aktuellen Reihenfolge scheitert. Direkt darunter
stehen Position, Dateiname und konkreter Fehler (z. B. doppelte
Frame-ID, PNG-Defekt, Costume-Palette). Die Vorschau simuliert dafür
den tatsächlichen Frame-Import im verworfenen JSON-Zwischenstand und
unterscheidet sichere Bilder von Konfliktbildern; die verbindliche
Gesamtprüfung und der gesperrte Importknopf bleiben unverändert.
Kein neues Projektfeld oder SCUMM-Opcode. Lokale Tests grün;
Chromium-/CI-Abnahme und menschliche Bedienabnahme offen.
**Nächstes Paket:** Ein einzelnes fehlerhaftes Upload-PNG gezielt durch
eine neue Datei ersetzen, ohne die übrige geordnete Auswahl zu verlieren.

**Produktpaket (2026-11-11, CI-Abnahme bestanden):** Der NPC-Dialogeditor zeigt vor
dem PNG-Stapelimport, ob die vorbereitete Reihenfolge wirklich als native
Sprech-/Abschlussfolge speicherbar ist. Dieselbe atomare Importfunktion
wird ohne Änderung am Projekt-JSON zur Prüfung ausgeführt. Der Button
ist bei leerer Auswahl, doppelt vergebener Frame-ID, fehlerhaftem PNG,
voller Costume-Palette oder anderem Importfehler deaktiviert; beim
Fehler wird die Ursache einschließlich betroffenem Dateinamen angezeigt,
soweit der Fehler zu einer einzelnen PNG-Datei gehört. Jede Änderung an
Auswahl, Richtung, Dialogzeile oder Ziel aktualisiert die Prüfung.
334 lokale Tests, Core- und Chromium-CI grün; der Browser prüft
Importbereitschaft, native COST-Speicherung/JSON-Roundtrip und die
anschließende Sperre wegen bereits belegter Frame-IDs. Die native
ScummVM-Regression bestand im unveränderten vollständigen Job-Replay;
der erste Lauf scheiterte bei einer Richtungs-Abschlussgeste in einer
bestehenden Bildabtastung (PR #122, Merge `3d94a6d`, Runs
`42930996980` / `42930997132` / `42930997256`). Menschliche Bedien-
abnahme offen. **Nächstes Paket:** Beim Importvorgang Konflikte an
einzelnen Miniaturkarten sichtbar markieren.

**Produktpaket (2026-11-11, CI-Abnahme bestanden):** Ein Klick auf ein Miniaturbild
in der vorbereiteten PNG-Importgalerie wählt unmittelbar genau dieses
Frame. Einzelbildvorschau, Positions-/Frame-ID-Anzeige, Dropdown und
Vorwärts-/Rückwärtsnavigation verwenden dieselbe Auswahl. Der
Auswahlwert bleibt an die aktuellen Dropdown-Optionen gebunden;
Projekt-JSON und COST-Export
bleiben unverändert. 334 lokale Tests und Core-/Chromium-CI grün;
ein echter Miniaturklick zeigt den erwarteten PNG-Pixelwert und die
Frame-ID, die übrigen Sortier-/Exportpfade bleiben grün. Die bestehende
native ScummVM-Regression bestand auf dem ersten PR-Commit, spätere
Korrekturen änderten nur die Gradio-Auswahlbindung und den Browsertest
(PR #120, Merge `6e9db6d`, Runs `42929768607` / `42929768636` /
`42927794343`). Menschliche Bedienabnahme offen. **Nächstes Paket:**
Importhindernisse (insbesondere doppelte Frame-IDs und Palette) bereits
vor dem Importklick in der Vorschau benennen.

**Folgepaket (2026-11-11, CI-Abnahme bestanden):** Die vorbereitete PNG-Importfolge
hat nun eine Einzelbildansicht mit Position, nativer Frame-ID und
Vorheriges-/Nächstes-Bild-Navigation. Sie verwendet dieselbe ausgewählte
Reihenfolge wie Galerie, GIF und Import. Die Auswahl bleibt editierbar,
die Navigation ändert keine JSON-Daten und endet sichtbar am Rand statt
unerwartet zum anderen Ende zu springen. 334 lokale Tests sowie alle
drei CI-Workflows bestanden; Chromium-Navigation mit echter Pixelprobe
und bestehende native ScummVM-Dialogregression grün (PR #118,
Merge `cff209c`, Runs `42926566873` / `42926566651` / `42926566581`).
Menschliche UI-Abnahme offen. **Nächstes Paket:** direkte
Frame-Auswahl über die Miniaturgalerie zur Navigation vor dem Import.

**Produktpaket (2026-11-11, CI-Abnahme bestanden):** Im NPC-Dialogeditor lässt sich
die noch nicht gespeicherte PNG-Importauswahl in ihrer aktuellen Reihenfolge
als animiertes GIF abspielen. Die frei wählbare Bilddauer (40–2000 ms)
gilt nur für die Editor-Vorschau, nicht für native COST-Ticks; Änderung der
Auswahl verwirft die alte Vorschau. Der Import und Projekt-JSON bleiben
unverändert. 334 lokale Tests und alle drei CI-Workflows grün,
einschließlich Chromium-Bedienpfad und bestehender nativer Dialogprobe
(PR #117, Merge `630a28d`, Actions `42925614655` / `42925614671` /
`42925614660`). Menschliche Bedienabnahme bleibt offen.
**Nächstes Paket nach Abnahme:** Vorabvorschau mit erkennbarem aktuellem
Frame und direkter Navigation durch die geplante Importfolge.

**Neues Produktpaket (2026-11-11, native Abnahme bestanden):**
Der NPC-Dialogeditor zeigt die **tatsächlichen PNG-Bildpixel vor dem
Import als beschriftete Miniatur-Galerie** in genau der Reihenfolge der
zukünftigen nativen COST-Frames. Umsortieren, Ausschließen,
Wiederaufnehmen und eine neue Dateiauswahl aktualisieren die Galerie
zusammen mit dem bestehenden Textplan. Keine neuen Modellfelder,
Interpreter-Befehle oder Änderungen am atomaren Import erforderlich.
334 lokale Tests und alle sechs finalen CI-Checks grün. Zwei Chromium-
Läufe prüfen die echten Pixel-Farben und Reihenfolge der 3/2/3/2
Miniaturen nach Upload, Umordnen, Ausschließen und Wiederaufnehmen
einschließlich Export/Reimport. Zwei stock-ScummVM-Läufe bestätigen
weiterhin die bestehende zweiframige Abschlussgeste und Standrückkehr
(PR #115, Merge `6e495d5`, Chromium Jobs `130201926707` /
`130201843676`, native Jobs `130201843845` / `130203561023`).
Eine anfängliche unveränderte Startbild-Sichtprobe schlug einmal fehl
und bestand im unveränderten Job-Replay. Menschliche UI-Abnahme offen.
**Nächstes Paket:** Abspielbare Vorschau
der geplanten PNG-Importfolge vor dem Speichern.

**Neues Produktpaket (2026-11-11, native Abnahme bestanden):**
Zuvor ausgeschlossene PNG-Dateien lassen sich im NPC-Dialogeditor **ohne
Neu-Upload wieder in die vorbereitete Importauswahl aufnehmen**. Das
Wiederaufnehmen hängt das Bild an die bestehende Reihenfolge an;
Verschieben, erneutes Ausschließen, Frame-ID-Vorschau und atomarer nativer
COST-Import bleiben konsistent. Selbst wenn vorher alle Bilder entfernt
wurden, lässt sich ein beliebiges hochgeladenes PNG wieder auswählen.
334 lokale Tests und sechs finale CI-Checks grün: Zwei Chromium-Läufe
prüfen Entfernen, Wiederaufnehmen, geänderte Importauswahl und den
Export/Reimport, zwei native stock-ScummVM-Läufe das bestehende
zweiframige Dialogende samt Standrückkehr (PR #113, Merge `36187ac`,
Chromium Jobs `130193752594` / `130193639385`, native Jobs
`130193752872` / `130196817977`). Ein zunächst fehlgeschlagener
unveränderter Tür-Sichttest im nativen Job wurde ohne Gate-Änderung
wiederholt und bestand. Menschliche UI-Abnahme offen.
**Nächstes Paket:** Bild-Miniaturvorschau der vorbereiteten PNG-Importfolge
vor dem Speichern, nicht nur Dateinamen und Frame-IDs.

**Neues Produktpaket (2026-11-10, native Abnahme bestanden):**
Im NPC-Dialogeditor kann man jetzt einzelne PNGs **aus der vorgesehenen
Importauswahl entfernen**, ohne die anderen bereits hochgeladenen Dateien
erneut auszuwählen. Die verbleibenden Bilder behalten ihre manuell
festgelegte Abspielreihenfolge. Vorschau und atomarer SCUMM-v6-COST-Import
berücksichtigen ausschließlich diese Bilder; selbst ein vollständig
geleerter Import wird klar zurückgewiesen. Die ursprünglichen Uploads
bleiben für diese Sitzung als Dateikarten sichtbar; die als solche
beschriftete Importauswahl ist verbindlich. 334 lokale Tests und alle fünf
CI-Checks der finalen Commit-Spitze grün. Zwei Chromium-Läufe prüfen drei
Uploads, Umordnen, Ausschließen des dritten Bilds und Export/Reimport
der beiden verbleibenden; der unveränderte stock-ScummVM-Dialog mit
zweiframiger Abschlussgeste und Standrückkehr bestand ebenfalls
(PR #111, Merge `33c28f5`, Chromium Jobs `130188492998` /
`130188465475`, native Job `130188494313`). Menschliche UI-Abnahme offen.
**Nächstes Paket:** Vorher
ausgeschlossene PNGs wieder in die Importauswahl aufnehmen, ohne Neu-Upload.

**Neues Produktpaket (2026-11-10, native Abnahme bestanden):**
Im NPC-Dialogeditor lassen sich mehrere hochgeladene PNGs **vor dem
Stapelimport grafisch nach oben oder unten verschieben**. Ein gewähltes
Bild bleibt beim Verschieben markiert; Vorschau, automatisch erzeugte
Frame-IDs und nativer Import verwenden dieselbe neue Reihenfolge. Ein
Wechsel der Dateiauswahl setzt die Sortierung zurück; ungültige/stale
Reihenfolgen werden abgelehnt, ohne das Projekt zu verändern. Der
SCUMM-v6-COST-Exporter und die atomare Importsemantik bleiben gleich.
334 lokale Tests und sechs CI-Checks grün. Zwei Chromium-Läufe beweisen
Auswahl, Umsortierung, sichtbare Reihenfolge und JSON-Export/Reimport;
zwei stock-ScummVM-Läufe bestätigen den bestehenden nativen
Mehrframe-Abschlussdialog mit Standrückkehr (PR #109, Merge `e974946`,
Chromium Jobs `130181832614` / `130181718511`, native Jobs
`130181832477` / `130181719158`). Menschliche UI-Abnahme offen.
**Nächstes Paket:** Einzelne PNG-Dateien aus der
Upload-Auswahl entfernen, ohne die übrige Auswahl neu hochzuladen.

**Neues Produktpaket (2026-11-10, native Gameplay-Abnahme bestanden):**
Der NPC-Dialogeditor importiert jetzt **mehrere PNG-Dateien auf einmal**
als geordnete native Sprech- oder Abschlussfolge für die ausgewählte
Dialogzeile und Blickrichtung. Vor dem Klick werden die Reihenfolge und
die aus Dateinamen erzeugten Frame-IDs angezeigt. Doppelte IDs,
ungültige PNG-Dateien und native Palettenfehler verhindern den gesamten
Import ohne Teiländerungen. Bestehende Actor-/Costume-Zuweisungen und
andere Richtungen bleiben erhalten. **334 lokale Tests und alle fünf
CI-Checks der aktuellen Commit-Spitze grün.** Chromium-Multiupload,
Reihenfolge, Export/Reimport und stock-ScummVM-Abnahme einer zweiframigen
per Stapel importierten Abschlussgeste zwischen West-/Ost-Sprechen
mit Standrückkehr bestanden (PR #107, Merge `a685897`, native Job
`130175052358`, Chromium Jobs `130175056189` / `130175014763`).
Der erweiterte Importbereich ist für die stabile primäre Vorschau
zunächst zugeklappt. Menschliche Bedienabnahme offen.
**Nächstes Paket:** PNG-Reihenfolge
bereits ausgewählter Dateien vor dem Stapelimport grafisch umsortieren.

**Neues Produktpaket (2026-11-10, native Gameplay-Abnahme bestanden):**
Eine gemeinsam genutzte native Figuren-Costume lässt sich jetzt direkt
im NPC-Dialogeditor **für die gewählte Sprecherfigur vereinzeln**. Der
Editor zeigt die betroffene Figur, den neuen eindeutigen Costume-Namen
und alle weiterhin unveränderten Mitnutzer vor dem Klick. Die gesamte
Costume einschließlich PNG-Frames, Palette und COST-Animationen wird
kopiert, nur die Actor-Referenz des gewählten Sprechers wird umgestellt.
Alle seine Dialogzeilen behalten gültige Gesten; danach sind private
Sprech-/Abschluss-PNG-Imports möglich. **333 lokale Tests und alle sechs
CI-Checks grün.** Chromium-Trennen/Import/Export und die native ScummVM-
Abnahme der über die private Costume exportierten Magenta-Schlussgeste
zwischen West- und Ost-Dialog mit Standrückkehr bestanden (PR #105,
Merge `1595e1c`, native Jobs `130167489043` / `130167388424`,
Chromium Jobs `130167488068` / `130167388133`). Menschliche Bedien-
abnahme offen.
**Nächstes Paket:** Mehrere neue PNG-Bilder in einem Schritt als
geordnete Sprech- oder Abschlussfolge im Dialogeditor importieren.

**Neues Produktpaket (2026-11-10, native Gameplay-Abnahme bestanden):**
Der NPC-Dialogeditor kann jetzt **neue PNG-Bilddateien direkt importieren**
und sie mit einem Klick an die native Sprech- oder Abschluss-PNG-Folge
der gewählten Zeile und Blickrichtung anhängen. Der existierende
Costume-Palettenimport wird wiederverwendet; eine bereits geteilte Costume,
volle Palette, doppelte Frame-ID oder unzulässiger Dialog-Cue verhindern
den Vorgang vollständig und sichtbar. Andere Zeilen, Richtungen, Stand- und
Talk-Frames bleiben erhalten. **332 lokale Tests und alle fünf Checks der
aktuellen CI-Commit-Spitze grün.** Chromium-Datei-Upload, Export/Reimport
und die aus der PNG-Datei generierte Magenta-Schlussgeste zwischen W- und
E-Sprechen samt Standrückkehr im stock ScummVM bestanden (PR #103,
Merge `1cc99f7`, native Jobs `130161049750` / `130161082960`, Chromium
Job `130161083496`). Ein vorheriger bildabtastungsbedingter Fehlversuch
führte zur vollständigen Wiederholungsoption der ScummVM-Probe; beide
erneut ausgeführten nativen Gameplay-Jobs bestanden. Menschliche Abnahme
offen. **Nächstes Paket:** Die sichere Trennung einer gemeinsam genutzten
Figuren-Costume direkt im Dialogeditor, um auch dort PNGs zu importieren.

**Neues Produktpaket (2026-11-10, native Gameplay-Abnahme bestanden):**
Die eigene **Abschluss-PNG-Folge pro NPC-Zeile und Blickrichtung** lässt
sich nun direkt im Dialogeditor aufbauen, anhängen, verschieben,
Frames entfernen und als GIF ansehen, ohne den Costume-Editor zu öffnen.
Die erste Änderung reserviert einen stabilen eigenen COST-Slot und bindet
ihn nach dem Dialog-Wait mit positiver nativer Tick-Dauer ein. Andere
Dialogzeilen und Richtungskanäle bleiben erhalten. Bestehende Projekte
behalten ihre bisherigen Cues. **331 lokale Tests und alle sechs CI-Checks
grün.** Chromium-Authoring, Export/Reimport und der native Gameplay-
Nachweis der magentafarbenen Abschlussgeste zwischen West- und Ost-
Sprechzeile mit anschließender Standpose bestanden (PR #101, Merge
`8557ea0`, Jobs `130151091545` und `130151090189`). Menschliche
UI-Abnahme offen. **Nächstes Paket:** Eigene neue PNG-Bilder direkt
in der Dialogansicht importieren und als Sprech-/Abschlussframes zuweisen.

**Neues Produktpaket (2026-11-10, native Gameplay-Abnahme bestanden):**
Eine einzelne NPC-Dialogzeile kann jetzt nach `waitForMessage()` eine
**eigene optionale Abschlussgeste** aus einer vorhandenen indizierten
Costume-Animation der Sprecherfigur abspielen. Ihre positive Mindestdauer
ist in nativen Skript-Ticks definiert; danach erfolgt die bisherige
optionale Rückkehr zur Standpose. Ohne Abschlussgeste bleiben Skript und
alte JSON-Projekte unverändert. Andere Zeilen, Richtungskanäle und
Sprechphasen werden nicht verändert. **330 lokale Tests und alle 13
CI-Checks grün.** Der echte Gradio-Chromium-Pfad mit Export/Reimport
ist bestanden; der native magentafarbene Abschlussframe erschien nach
West-rot/grün und vor Ost-blau/gelb mit anschließender Standpose im
unveränderten ScummVM (Run `42904734152`, Job `130139641706`,
PR #99, Merge `ead868b`). Menschliche Bedienabnahme offen.
Kein wortgenauer Lippensync. **Nächstes Paket:** Eine direkt im Dialog-
Editor anlegbare eigene Abschluss-PNG-Folge pro Zeile und Blickrichtung,
ohne zuerst manuell eine Costume-Animation erstellen zu müssen.

**Neues Produktpaket (2026-11-10, native Gameplay-Abnahme bestanden):**
Der Autor kann für **jede NPC-Dialogzeile** die zwei nativen Sprechphasen
einstellen: den Vorlauf bis zum Start ihrer COST-Sprechgeste und ihre
Mindestlaufzeit vor dem `waitForMessage`. Der Editor verwendet ganzzahlige
SCUMM-Skript-Ticks, keine Millisekunden. Werte 0/1/N, getrennte Zeilen
und unveränderte ältere JSON-Projekte sind modellseitig unterstützt;
die bestehenden Defaults `delay(1)` und `delay(60)` bleiben erhalten.
Die neue Kombination mit unterschiedlichen Richtungskanälen ist in einem
regulär exportierten ScummVM-Dialog geprüft. **329 lokale Tests und alle
13 CI-Checks grün**, inklusive echtem Chromium-Editorpfad mit Export/Reimport,
stock-ScummVM-West-Geste mit 12/90 Ticks und unveränderter Ost-Geste mit
1/60 Ticks (Run `42901243477`, Job `130127449346`, PR #97,
Merge `208e619`). Menschliche Bedienabnahme bleibt offen. Kein automatischer
Silben-/Wort-Lippensync. **Nächstes Produktpaket:** Ein optionaler,
zeilenspezifischer Abschlussgesten-Kanal am nativen Dialogende.

**Neues Produktpaket (2026-11-10, Abnahme bestanden):**
Die eigene Sprechfolge einer NPC-Dialogzeile und Blickrichtung lässt sich
im Studio jetzt **grafisch als Frame-Timeline** bearbeiten: aus importierten
PNG-Frames anhängen, selektieren, nach links/rechts verschieben, entfernen
und als animiertes GIF abspielen. Jede Editieraktion speichert denselben
stabilen COST-Slot; die anderen Richtungen und Dialogzeilen bleiben erhalten.
Die GIF-Bilddauer ist nur eine Editor-Vorschau, keine behauptete native
ScummVM-Abspielgeschwindigkeit. **328 lokale Tests und fünf CI-Checks grün.**
Die echte Chromium-Bedienfolge (Anhängen/Verschieben/Entfernen, GIF,
Export/Reimport) ist bestanden; native ScummVM-Regression ebenfalls
grün (Run `42898953018`, Job `130119459630`, PR #95,
Merge `3410035`). Menschliche UI-Abnahme bleibt offen. **Nächstes Paket:**
Visuelles Authoring von zeilenspezifischen Sprechphasen mit steuerbarer
nativer Anbindung an den Dialogablauf, ohne erfundene Millisekunden-Opcodes.

**Neues Produktpaket (2026-11-10, native Gameplay-Abnahme bestanden):**
Für eine einzelne native NPC-Dialogzeile kann der Autor nun eine eigene
Mehrframe-Sprechfolge **nur für Nord, Ost, Süd oder West** speichern.
Erneutes Auswählen der Richtung zeigt deren tatsächliche Framefolge;
die drei anderen Kanäle derselben Zeile, weitere Dialogzeilen und die
globalen `gesture`-/`talk_start`-Frames bleiben unverändert. Wird die
Zeile erstmals richtungsbezogen bearbeitet, werden ihre bisherigen
Richtungskanäle übernommen, nicht durch einen Default ersetzt.
Der vorhandene zeilenspezifische native Animationsslot wird wiederverwendet;
keine JSON-Schemamigration. **327 lokale Tests und alle vier CI-Checks grün.**
Der reale Gradio-Chromium-Pfad inklusive Export/Reimport und der
Stock-ScummVM-W/E-Sprechfolgen-Test mit rot/grün und blau/gelb sind
bestanden (Run `42895287701`, Job `130106686621`, PR #93,
Merge `270be816`). Menschliche Bedienabnahme bleibt offen.
**Nächstes Paket:** Autorentaugliche grafische Mehrframe-Timeline und
Abspielvorschau direkt je NPC-Zeile und Blickrichtung, ohne native
Abspielgeschwindigkeit vorzutäuschen.

**Aktuelles Produktpaket (2026-11-10, native Gameplay-Abnahme bestanden):**
Im nativen Dialogeditor kann der Autor **je Dialogzeile** eine eigene Folge
aus 1..N importierten PNG-Frames speichern. Jede Zeile derselben Figur
bekommt einen stabilen eigenen indizierten COST-Animationsslot ab 28;
erneutes Bearbeiten verwendet diesen Slot wieder, ohne `gesture`/
`talk_start` oder die Sequenzen anderer Zeilen zu überschreiben. Die
gespeicherte Folge wird bei Zeilenwechsel und nach JSON-Reimport angezeigt.
Bestehende Sprechposen und abweichende Costume-Richtungen bleiben nutzbar;
die neuen Folgen werden zunächst einheitlich für alle vier Richtungen
dieser **einen** Dialogzeile angelegt. **327 lokale Tests und alle fünf
PR-Checks grün.** Der Gradio-Chromium-Klickweg speichert zwei verschiedene
Sprechfolgen und importiert sie korrekt wieder. Stock ScummVM zeigt für
dieselbe Figur erst rote/grüne, danach blaue/gelbe Sprechframes und kehrt
zur Standpose zurück (Run `42890566896`, Job `130090292878`, Artefakt
`native-v6-studio-independent-speaking-lines`, Merge `482375e`).
**Offen:** menschliche Bedienabnahme; vollständiger Lippensync weiterhin
nicht erreicht.
**Nächstes Produktpaket:** individuell gerichtete Mehrframe-Folgen je
Dialogzeile, ohne Verlust der anderen Richtungskanäle.

**Neues Produktpaket (2026-11-10, native Abnahme bestanden):**
Im Costume-Editor kann ein Autor für eine gewählte Blickrichtung eine
kommagetrennte Folge importierter PNG-Frame-IDs als wiederholte native
Sprechsequenz speichern. Die Folge wird gemeinsam auf `gesture` und
`talk_start` gesetzt und bleibt beim Richtungswechsel sowie JSON-Roundtrip
erhalten. Die übrigen Blickrichtungen und `stand`/`talk_stop` bleiben
unverändert. Die native COST-Quelle enthält mehrere Frames pro Richtung;
die zeitliche Abspielrate bestimmt der native Interpreter, nicht eine
frei erfundene Millisekundenangabe im Studio. **326 lokale Tests grün;
stock-ScummVM-Gate für zwei unterscheidbare Frames während derselben
Dialogzeile mit anschließenden sechs Standframes bestanden** (Run
`42886572422`, Job `130076341678`, Artefakt
`native-v6-studio-speaking-sequence`; alle PR-#89-Checks grün,
Merge-Commit `634afb6`). Menschliche Gradio-Bedienabnahme offen.
**Nächstes Produktpaket nach dem nativen Gate:** individuelle Sprechfolgen
je Dialogzeile (auch mehrere Zeilen derselben Figur), ohne die Costume-
Richtungsfolgen global zu überschreiben.

**Aktuelles Produktpaket (2026-11-10, native Gameplay-Abnahme bestanden):**
Ein durch den produktiven Story-/Studio-Pfad erstelltes Vier-Zeilen-Gespräch
setzt den selben NPC vor jeder Zeile auf N/E/S/W. Dessen Costume enthält
vier unterschiedlich gefärbte PNG-äquivalente Sprechframes, mit den
vorhandenen Richtungs-Authoring-Operationen als `gesture` und `talk_start`
gebunden. Der neue stock-ScummVM-Klicktest hat die sichtbare Farbfolge
**N/E/S/W mit jeweils 256 Farbpixeln** und danach **sechs stabile
Standframes mit null Sprechfarben** nachgewiesen (GitHub-Dialog-Job
`130066624232`, Run `42883775730`, Artefakt
`native-v6-studio-dialogue-four-facing`, Code-Commit `6902dc7`).
Die erste native Probe zeigte ausschließlich den Nord-Frame, obwohl alle
vier Dialogtexte ausgegeben wurden. **Ursache identifiziert:** ScummC-
Richtungskonstanten `NORTH/EAST/SOUTH/WEST` sind alte IDs 3/1/2/0,
ScummVM-v6-`setActorDirection` erwartet dagegen Winkel 0/90/180/270.
Die zentrale Exportabbildung für Actor-Initialisierung, Interaktionen und
Dialoge wurde berichtigt. 325 lokale Tests grün. Die native Richtungs-
Sprechpose ist damit für diesen vierteiligen Actor-Dialog auf Stufe V
nachgewiesen; vollständiger Lippensync ist **nicht** erreicht.
**Offen:** übrige Gesamt-CI-Gates, menschliche Gradio-Bedienabnahme.
**Nächstes Produktpaket:** zeitabhängige Sprechframe-Wechsel je Zeile
authoren und sichtbar in ScummVM prüfen (D03).

**Neues Produktpaket (2026-11-10, Implementierung):** Im Costume-Editor kann
der Autor ein importiertes PNG-Frame gezielt für Nord, Ost, Süd oder West
als Sprechpose setzen. Der bestehende native `gesture`-Slot 24 und
`talk_start` 16 werden nur in dieser Richtung geändert; die anderen
Richtungen sowie `stand` 12 und `talk_stop` 20 bleiben erhalten. Beim
Richtungswechsel erscheint der gespeicherte Frame wieder im Auswahlfeld.
Ein Modell-/COST-Quelltest und 322 lokale Regressionstests sind grün.
Ein echter Gradio-Chromium-Test für N/O-Wechsel, Speichern und Reimport
ist auf Commit `bf35cc2` grün (beide Gradio-Smoke-Jobs, beide Core-Testjobs).
Die bewusst leere Einzel-PNG-Vorauswahl bei richtungsabhängigen Frames
wird im Browservertrag berücksichtigt; die Costume-Auswahl bleibt nach
dem Speichern erhalten.
**Offen:** native ScummVM-Dreh-/Sprechprobe
mit vier unterschiedlichen PNG-Frames sowie menschliche UI-Abnahme.
**Nächstes Produktpaket:** Vier-Richtungs-Sprechposen im generierten Spiel
durch Drehen und Sprechen sichtbar nachweisen; erst danach D03 weiterführen.

**Aktuelles Browser-Abnahmepaket (2026-11-10, PR in Prüfung):**
Der native Dialogeditor hat einen realen Chromium-Klicktest erhalten, nicht
nur einen Gradio-HTTP-Startcheck. Der Browser lädt eine native Projektdatei
mit zwei unterschiedlichen Sprechposen derselben NPC-Figur, wählt die
betreffenden Dialogzeilen, sieht die gespeicherten PNG-Frames, ändert die
Pose über den tatsächlichen Button, exportiert JSON, leert das File-Feld
und importiert das gespeicherte Projekt erneut. Dabei bleiben die
zugeordneten Dialog-Cues konsistent. **Nachweis:** GitHub-Gradio-Smoke
`Click through native NPC dialogue pose editing in real Chrome` grün;
Screenshots und exportierte JSON als Artefakte. Core-Tests ebenfalls grün.
**Offen:** menschliche Bedienabnahme und etwaige unabhängige
Responsive-Layout-Probleme; der Chromium-Workflow ersetzt diese nicht.
**Nächstes Produktpaket:** direkte visuelle PNG-Pose-Vorschau im
Dialogeditor, damit Autoren das gewählte Bild ohne Wechsel zum
Costume-Bereich prüfen können.

**Produktpaket (2026-11-10, PR in Prüfung):** Nach Auswahl einer nativen
Sprecher-Dialogzeile zeigt der Gradio-Editor die bereits zugewiesene
PNG-Sprechpose wieder an. Er liest dazu die persistierte Dialog-Cue-Animation
und löst einen einzelnen, für alle vorhandenen Blickrichtungen eindeutigen
COST-Frame auf. Mehrteilige/uneindeutige Costume-Animationen werden nicht
als einzelnes PNG ausgegeben; der Animationsselektor bleibt verfügbar.
Die ausgewählte Dialogzeile bleibt beim Speichern erhalten und die Editorfelder
werden aus dem aktualisierten Projekt neu gelesen; veraltete Zeilen werden
zurückgesetzt. Ein gezielter Roundtrip-/Reassignment-/Mehrframe-Test ist grün.
**Offen:** vollständige Gradio-CI und interaktive manuelle Bedienabnahme.
**Nächster Schritt:** Manuelle Bedienabnahme des Gradio-Pfads mit importierten
PNG-Frames, Zeilenwechsel, Speichern und erneutem Laden.

**Produktpaket (2026-11-10, PR in Prüfung):** Der native NPC-Dialogeditor
zeigt nun eine direkte 256×256-Bildvorschau der gewählten Sprecher-PNG-Pose.
Die Vorschau rendert den tatsächlich gespeicherten indizierten Costume-Frame
mit dessen SCUMM-Palette; sie ist ausdrücklich eine statische Editor-Vorschau,
keine Simulation des ScummVM-Animations-Timings. Nach Dialogzeilenwechsel,
Frameauswahl (auch vor dem Zuweisen), Speichern und Projekt-Reimport wird
die Anzeige aktualisiert oder ohne gültige Auswahl geleert. Ein Pillow-Test
prüft beide unterschiedlichen Costume-Palettenfarben und die unveränderte
Dialogzuordnung bei vorläufiger Auswahl. Der reale Chromium-Klicktest
prüft rote und grüne Bildpixel in der Oberfläche und den gespeicherten
Roundtrip; Core- und Gradio-CI auf Code-Commit `f940d93` grün.
**Offen:** PR-Gesamt-CI und menschliche Bedienabnahme.
**Nächstes Paket:** Die Sprechpose im Dialogeditor bei der Auswahl visuell
neben dem Actor bzw. der jeweiligen Dialogzeile darstellen, mit
gezielter Ausrichtung für unterschiedliche Blickrichtungen; weiterhin
ohne vollständigen Lippensync zu behaupten.

**Aktuelles Produktpaket (2026-11-10, PR in Prüfung):**
Der NPC-Dialogeditor bietet eine zusätzliche Richtungsvorschau für die
tatsächlich ausgewählte indizierte Costume-Sprechanimation mit den
Richtungen **Nord, Ost, Süd, West**. Anders als die vereinfachte
Ein-PNG-Zuweisung zeigt sie pro Richtung deren eigenen nativen Frame –
auch wenn die vier Richtungen verschiedene Frames haben. Ein
unbekannter Richtungszweig, eine native Kommando-Folge oder mehrere
Frames wird ausdrücklich ohne erfundenes Einzelbild gemeldet.
Die echte Palettenauflösung bleibt erhalten; die unabhängige
Vorschaukarte enthält ihre Richtung als Überschrift.
**Tests:** Eine PNG-Fixture belegt pro Richtung die korrekte Farbe und
schützt Mehrframe-Fälle vor falscher Anzeige. Ein Gradio-Chromium-Test
klickt Nord, West und Ost und prüft Status und echte Pixel; Core und
Browser-Gate auf Code-Commit `981ab80` grün.
**Offen:** native ScummVM-Spielansicht für *unterschiedliche Richtungsframes*
(nicht durch den Editor-Screenshot ersetzt), menschliche UI-Abnahme,
vollständiger Lippensync.
**Nächstes Produktpaket:** Richtungsabhängige Frames direkt im
Costume-Editor anlegen und über einen native ScummVM-Dreh-/Sprechtest
mit allen vier Blickrichtungen verifizieren.

## Nordstern

Ein vollständiger, originaler SCUMM-v6-Generator für klassische
Point-and-Click-Adventures. Technischer Output: native Ressourcen und
Bytecode, lauffähig in ScummVM ohne eigene Adventure-Studio-Engine.
Die kreative Oberfläche soll später auch komplexe, cineastische
Sequenzen authoren können.

**Aktuelles Produktpaket (2026-11-10, PR #81):** Im Studio lassen sich
zwei oder mehr Dialogzeilen derselben Figur mit unterschiedlichen importierten
PNG-Sprechframes versehen. Die erste Pose nutzt die bewährte native
`gesture`-/`talk_start`-Zuordnung, weitere Posen bekommen stabile
COST-Animationsslots ab 28. Ein anderer Dialog-Cue bleibt dabei unverändert;
gleiche Frames werden wiederverwendet und gemeinsam genutzte Costumes geschützt.
Der Editor-zu-COST-/SCUMM-Quellpfad ist regressionsgetestet. **Native E2E-Abnahme:
zwei unterscheidbare Posen derselben Figur sichtbar in stock ScummVM**, der
native Schritt ist auf Commit `eb5ba420` zweimal erfolgreich (GitHub-Actions-Dialogschritt `Play two different PNG speaking poses`). Die früher belegte
Standpose bleibt als Abschlussprüfung erhalten.
**Noch offen:** Abschluss der Gesamt-CI und manuelle Gradio-Bedienabnahme.
**Nächstes Paket:** Sichtbare Auswahl/Rückmeldung der bereits einer Dialogzeile
zugeordneten PNG-Sprechpose im Gradio-Editor und interaktive Bedienabnahme.

## Aktuelles Produktpaket (2026-11-09)

**Neues Paket – PNG-Sprechpose direkt an der Dialogzeile (PR in Arbeit):**
Der native Dialogeditor bietet nun die importierten Frames genau der
gewählten Sprecherfigur an. Eine Aktion erzeugt daraus die nativen
Talk-Start-/Stop-/Gestenanimationen und bindet die Geste an die Zeile.
Eine zwischen mehreren Actors geteilte Costume wird dabei nicht still
überschrieben, sondern mit konkreter Fehlermeldung abgewiesen; der Autor
muss zuerst eine eigene Costume zuordnen. 319 lokale Tests grün,
einschließlich des Dialog-zu-PNG-zu-COST-Quellpfads. Die bereits belegte
stock-ScummVM-Sprechgesten-/Standpose-Semantik bleibt unverändert.
**Offen:** CI des neuen Pakets und manuelle Gradio-Bedienabnahme.
**Nächstes Produktpaket:** Mehrere verschiedene Sprechframes je Figur
und Dialogzeile, ohne die globale native Talk-Start-Costume zu überschreiben.

**Vorheriges Paket – auf `main` integriert:** PR #78 wurde als Commit
`9fde9e97` mit vollständig grüner CI und nachgewiesener stock-ScummVM-
Sprechgeste samt Standpose gemergt. Ältere Debugging-Absätze unten
sind historische Befunde, keine aktuellen Blocker.

**Aktuellster nativer Nachweis (vor Merge):** Der stock-ScummVM-Dialogtest
hat die rote Sprechgeste mit 256 Pixeln sichtbar gemacht und später
deren Rückkehr zu 0 Pixeln bestätigt. Nach Anpassung der Bildprobe auf
sechs *aufeinanderfolgende* Standframes ist der native Gesten-/Standpose-
Schritt auf Commit `2dc5271` **grün**. Ausschlaggebend waren die
reservierten COST-Talk-Start-/Stop-Slots 16/20 und ein begrenztes
Endzustands-Wartefenster; die Geste 24 bleibt als editierbarer Cue
erhalten. Der Studio-Ein-Klick-Pfad erzeugt jetzt selbst `talk_start`
(Index 16) aus dem gewählten PNG-Frame und `talk_stop` (Index 20) aus
der Standpose; der Validator prüft die Übereinstimmung bei aktiviertem
Reset. 318 lokale Tests grün. **Noch offen:** vollständiger aktueller
CI-Lauf und interaktive Gradio-Bedienabnahme. Die folgenden älteren
Absätze dokumentieren die Fehlersuche, nicht mehr den letzten Status.


**Sprechpose aus importiertem PNG-Frame (Implementierung):** Im
Costume-Editor kann der Autor ein zuvor importiertes Frame auswählen und
mit einem Klick als `gesture`-Sprechpose für alle vier Blickrichtungen
zuweisen. Die Geste verwendet Index 24 und bleibt bis zum eigens
autorisierten Standpose-Reset sichtbar; die vorhandene `stand`-Animation
bleibt unberührt. Der Produktpfad nutzt das gleiche validierte
Projekt-JSON wie der native Export. 318 lokale Tests grün, inklusive
PNG-Import, vier Richtungen, ungültigem Frame, nativer COST-Quelldatei
und Dialog-Cue-Bindung im ScummC-Quellgenerator.
**Offen:** Durchgeklickter Gradio-Pfad und der strenge stock-ScummVM-
Sichtnachweis; PR #78 bleibt bis zu einem grünen nativen Gate offen.

**Native Fehleranalyse (2026-11-09):** Der zuerst fehlende CI-Start war
ein unvollständiger Git-Baum auf dem Feature-Branch; Commit `a091769`
hat den vollständigen Repository-Baum samt Workflows wiederhergestellt.
Die danach regulär laufenden nativen Dialogjobs zeigen Sprechertexte,
aber keine nachweisbare zweite NPC-Costume-Grafik. Auch der explizite
`stand`-Start in der Test-Fixture brachte keine zusätzlichen
Actor-Farbpixel im Bildbereich. Reservierte COST-Slots sind jetzt
Stand 12, Sprechbeginn 16 und Sprechende 20; die Geste 24 wird über
`setActorTalkFrame` an den Sprecher gebunden. **Offenes Gate vor der
Gesten-Abnahme:** Die native Sprecherfigur muss selbst sichtbar sein,
anschließend Geste und Rückkehr zur Standpose.

**Präziser ScummVM-Nachweis:** Nach Trennung der Sprecherfigur von Ego
und dem Talk-Hotspot ist die Witness-Stand-Costume tatsächlich sichtbar
(`speaker_costume_pixels=256`, CI auf `f765992`). Wird dieselbe
Costume-Animation 24 bereits beim Raumeintritt gestartet, zeigt
ScummVM die roten Sprechframe-Pixel (`gesture_initial_pixels=256`,
CI auf `7f096dc`). Bei der normalen Sprechzeile bleibt die Geste trotz
`setActorTalkFrame(6,3)`, `actorSay`, einem `delay(1)`-Tick und
`animateActor(...,24)` unsichtbar (`gesture_frame_pixels=0`, CI auf
`64a110b`). Ursache ist damit die Interaktion der Actor-Sprechphase
mit dem Animationsstart; eine native Talk-Start-/Talk-Script-Lösung
ist erforderlich, bevor Geste und Rücksetzung als Produktfunktion
freigegeben werden können.


**Sprechgesten mit definierter Standpose (Implementierung):** Zu einer
nativen Dialoganimation kann der Autor nun im Studio „Nach der Sprechzeile
zur Standpose zurückkehren“ auswählen. Nach `waitForMessage` und optionalem
VOC-Stopp setzt der SCUMM-v6-Exporter den betroffenen Actor ausdrücklich
mit `setCurrentActor`/`setActorStanding` zurück, stellt danach Ego als
aktiven Actor wieder her und startet die explizit indizierte `stand`-
Costume-Animation. Beim Wechsel mehrerer Sprecher gilt das jeweils für
die tatsächliche Actor-Bindung; fehlende `stand`-Richtungen oder ein
fehlender nativer `stand`-Index werden abgewiesen. Neue PNG-Costumes
erhalten dafür den nativen `stand`-Index 12. Der Dialogexport konfiguriert
zusätzlich die Actor-Talk-Frames auf den Gesten- und Stand-Index. Das versionierte Projekt-JSON speichert `reset_to_stand` nur
bei aktivierter Einstellung; ältere Cues ohne Feld behalten das bisherige
Verhalten. 316 lokale Tests grün (einschließlich zweier Sprecher und
Alt-JSON). Die erste native Endzustandsprobe wertete zwölf rote Pixel
in der unveränderten Standpose fälschlich als verbliebene Sprechgeste.
Die Bildartefakte aus CI `42552675686` machten die statische Farbe
sichtbar. Der Export startet zusätzlich die konkrete native `stand`-
Animation. Die korrigierte Klickprobe zeichnet den stärksten Gesten-
Frame auf und fordert danach einen über mehrere Ticks stabilen
Standzustand mit weniger Gestenpixeln als am Maximum. Die verschärfte
native Probe in CI `42552675686` (vorher) und der anschließenden
CI-Runde (12 rote Pixel vor und nach der Zeile, kein nachgewiesener
Gestenüberschuss) zeigt, dass auch der bisherige visuelle Gestennachweis
nicht hinreichend abgesichert war. Das ist ein offener Laufzeitfehler,
kein bestätigter End-to-End-Erfolg; PR #78 bleibt deshalb ungemergt.
**Offenes Pflichtgate:** Eine tatsächlich sichtbare native Sprechgeste,
anschließende Standpose und eine
durchgeklickte Gradio-UI-Bedienung stehen zum jetzigen Zeitpunkt aus.
**Nächstes Produktpaket:** Nach bestandenem Standpose-Gate die Gesten beim
Sprecherwechsel mit real importierten PNG-Frames im Editor-End-to-End-Fluss
prüfen; danach zeitgebundene Audio-/Lippen-Cues authoren.

## Vorheriges Produktpaket: Dialoganimation

**Costume-Animation je nativer Sprecherzeile (Implementierung):** Im nativen
Studio-Bereich kann eine Dialogzeile mit gebundenem `Speaker`-Actor eine
indizierte Costume-Animation erhalten oder die Zuordnung wieder entfernen.
Die neue, optionale `dialogue_animation_cues`-Sammlung bleibt im gemeinsamen
Projekt-JSON erhalten. Beim Export löst `animateActor` die gewählte Animation
unmittelbar nach dem zugehörigen `actorSay` und vor `waitForMessage` aus,
auch in mehrstufigen Dialogen;
bereits vorhandene VOC-Aufnahmen bleiben kombinierbar. Stale-Text, fehlende
Sprecher, Animationsindices und unpassende Blickrichtungen werden abgewiesen.
314 lokale Tests grün, darunter lineare/Antwort-Dialoge, Roundtrip und
SCUMM-Quellnachweis. Der erste native Klicklauf zeigte beide Sprecherzeilen,
aber noch keinen sichtbaren Gesten-Frame. Nach Anpassung der Befehlsfolge
(`actorSay` vor `animateActor`) und des kamerafolgenden Bildbereichs hat
die damalige stock-ScummVM-Klickprobe beide Sprecherzeilen und 14
rote Pixel im Actor-Bereich gezählt: `gesture_frame_pixels=14`,
`first_speaker_pixels=152`, `second_speaker_pixels=1056`, `passed=true`,
CI `42550554974` (Artefakt `native-v6-studio-dialogue-gesture`).
Neuere Frame-Vergleiche zeigen zwölf gleichfarbige Pixel in der Standpose;
die zwei zusätzlichen Pixel sind kein ausreichender Beleg für einen
sichtbaren zweiten Costume-Frame. Die Geste ist nativ erneut zu beweisen.
**Offen:** Ein interaktiver Gradio-UI-Klickpfad und ein echter zeitlich
präziser Lippen-/Sprach-Sync sind nicht nachgewiesen. D03 bleibt Teilfähigkeit.
**Nächstes Produktpaket:** Die Actor-Geste aus importierten PNG-Frames im
sichtbaren Gradio-Workflow auswählen, ihr Start-/Ende-Verhalten bei
aufeinanderfolgenden Sprecherwechseln prüfen und den Zustand nach einer
Sprechzeile sauber behandeln.

## Vorheriges Produktpaket: Sprecher-Costumes

**PNG-Costume einem Story-Sprecher zuweisen (Implementierung):** Nach dem
Synchronisieren der Story mit dem nativen Studio-Projekt kann ein bereits
vorhandener `Speaker<Figuren-ID>`-Actor eine aus PNG importierte Costume
erhalten. Die Gradio-Aktion „Ausgewähltem Actor diese Costume zuweisen“
übernimmt die gewählte Costume ohne die Sprecher-ID, Position oder die
Dialogbindung zu verändern. Ein vorhandener Startanimationsname muss in der
neuen Costume existieren. Der gemeinsame Projekt-Roundtrip bewahrt die
Zuordnung, und der reguläre Export erzeugt die native `.scost`-Ressource.
312 lokale Tests grün (der PNG-Integrationstest benötigt das optionale Pillow);
eine echte visuelle ScummVM-Probe mit der neuen
Actor-Grafik und ein durchgeklickter Gradio-UI-Pfad sind noch offen.
**Nächstes Produktpaket:** Pro Dialogzeile eine vorhandene Costume-Animation
des zugeordneten Actors authoren, im nativen Skript auslösen und die sichtbare
Framefolge in stock ScummVM prüfen.

## Vorheriges Produktpaket (2026-11-09)

**Bestehende Dialogantworten bearbeiten (Implementierung):** Im Gradio-Reiter
„Dialogzeilen“ kann eine vorhandene Antwort ausgewählt, ihr Text geändert
und ihr Zielknoten innerhalb desselben Gesprächs neu gesetzt oder das Gespräch
beendet werden. Die stabile Antwort-ID und ihr Ursprungsknoten bleiben erhalten.
Die Änderung folgt dem bestehenden Prüfen-/Übernehmen-Ablauf; die
Story-Validierung weist unerreichbare Gesprächszeilen und unzulässige
Verbindungen ab. Der reguläre Story-zu-SCUMM-Pfad übernimmt neue Texte und
Antwortverläufe. 309 lokale Tests grün, einschließlich produktivem Service-
und Quellgenerierungsnachweis. Eine eigene interaktive Gradio- und native
ScummVM-Klickabnahme dieser neuen Editoroperation steht aus; die bereits
nachgewiesene native Antwortmechanik wird nicht erneut als neues Feature
behauptet.

**Nächstes Produktpaket:** Eine sichtbare, vom Autor gewählte Costume-
Animation pro Sprechzeile an die tatsächlichen nativen Sprecher-Actors
binden und im Studio samt stock-ScummVM-Gameplay prüfen. Der derzeitige
automatisch erzeugte Dialog-Costume besitzt nur eine Standpose; die
Bild-/Frame-Bindung muss daher real in den gemeinsamen Authoring-Pfad.

## Gesichert vorhandene Grundlagen

- Versionierte Story-/Projektmodelle, deterministische Validierung
  und ScummC-Quelltextausgabe.
- Indizierte Raumhintergründe, einfache Hotspots und Bildzustände,
  Inventar-/Use-/Combine-Regeln, begrenzte Dialogvarianten,
  Palettenzyklen und Musikexperimente.
- Separate ScummC-/ScummVM-Workflows mit Bild-/Interaktionsprüfungen
  für definierte Demo-Szenarien. Einzelne erfolgreiche Proben
  **beweisen nicht** automatisch vollständige Generatorabdeckung.
- Eine erste Gradio-Oberfläche und JSON-/ZIP-Exportpfade.

Codebelege im Repository: `src/adventure_studio/scumm_assets.py`,
`scumm_project.py`, `story_to_scumm.py`, `scumm_launch.py` und deren Tests.

## Größte bekannte Lücken

1. Vollständige Z-Masken, Walkbox-/BOXM-/SCAL-Daten und
   nativer Ressourcen-Roundtrip fehlen im allgemeinen Raumdatenmodell.
2. Vollständige Actor-Costumes samt Animation, `COUNT`-Timing,
   mehreren Figuren und bewegten, interaktiven Objekten fehlen
   als durchgängige authorbare Features.
3. Native Schnitt-/Kamera-/Cutscene-Choreografie und sichere
   Skip-Endzustände fehlen im Studio-Editor.
4. Viele weitere SCUMM-v6-Bereiche sind nur teilweise untersucht;
   Details in der Funktionsmatrix. Die Gesamtkompatibilität ist offen.

## Letzte grundlegende Entscheidungen

- SCUMM v6 ist **Zielbinary und Laufzeitvertrag**, keine selbstgebaute
  Nachbildung der Mechanik.
- ScummVM-/ScummC-Quellcode ist die Primärreferenz; der konkrete
  Compiler-/Interpreterpfad wird dokumentiert, bevor Funktionen
  als kompatibel eingestuft werden.
- Editor-Shots sind Authoring-Metadaten, die nur native Räume,
  Bildzustände, Scripts und Kamera-Operationen erzeugen.
- Ein großes, generisches „Konformitätsspiel“ ist aktuell nicht
  Voraussetzung. Kleine native Export-Fixtures belegen konkrete Gates.
- Pull Requests sind interne GitHub-Technik. Bei grünen Checks und
  unkritischen, abgeschlossenen Änderungen kann der Agent wie gewünscht
  selbstständig mergen.

## Architektur-Audit und künftige Qualitätsregeln (2026-11-07)

Der [Architekturaudit](architecture-audit.md) hat konkrete
Demo-/Adapter-Grenzen und Verantwortungskonflikte dokumentiert.
Wesentliche Befunde: begrenzte lineare Story-Routen,
fixe Pickup-Farben/Platzierungen, harte Dialog-/Regelquoten,
absolute Koordinaten im Story-Fachmodell und die Kopplung
zwischen Authoring- und Exportvalidierung.

**Wichtig:** Das zweistellige Rezept `Use A with B` ist als
binäre Interaktion fachlich plausibel. Allgemeine Rätsel dürfen
aber mehr als zwei Bedingungen besitzen. Native SCUMM-Limits
sind von künstlichen Demo-/Layout-Limits getrennt zu führen.

Gültige Architekturleitlinien:
[Architekturverträge](architecture-contracts.md),
[ADR-0001](adr/0001-domain-and-export-boundaries.md),
[ADR-0002](adr/0002-limits-evidence-and-compatibility.md).
Eine [PR-Checkliste](../.github/pull_request_template.md) sichert
Regression, Versionsverträglichkeit und native Nachweise ab.

**Stabilisierung umgesetzt (2026-11-07):** Platzierungen werden im fachlichen
Story-Modell und im JSON-Parser nicht mehr auf die 640×200-Demogeometrie
begrenzt. Der aktuelle Exportadapter prüft seine konkrete Raumgeometrie
weiterhin und verweigert nicht darstellbare Exporte ausdrücklich. Die
Studio-Editierfassade lässt fachlich gültige Änderungen (auch mehr als vier
Dekoobjekte) mit Exportwarnung speichern; explizite Platzierungen bleiben
selbst bei nicht exportierbaren Stories lesbar. Regressionen: 203 Unit-Tests
lokal grün, darunter neue Grenztests und unveränderte Exportfixtures.

**Architekturstabilisierung abgeschlossen (weiteres Paket):** Das Studio
liefert nun typisierte Export-Blocker (`code`, `entity_kind`, `entity_id`,
`target_id`, `reason`), einschließlich mehrerer gleichzeitig bekannter
Hindernisse. Nicht klassifizierte Adapterfehler bleiben als
`ADAPTER_REJECTED` sichtbar, statt als native Limits ausgegeben zu werden.
Die Raumvorschau benutzt einen unabhängigen Authoring-Layoutpfad und
zeigt auch nicht exportierbare Projekte; sie ist ausdrücklich **keine**
Spielsimulation. Die Demo-Bildquelle wird von Exporter und Vorschau geteilt,
ohne dass die Vorschau den Compiler benötigt. Die zuvor künstlichen
JSON-Grenzen von 128 Entitäten bzw. 32 Bedingungen sind entfernt; das
1-MB-Eingabelimit bleibt als Ressourcenschutz bestehen. Grenzklassifikation:
[Audit-Nachtrag](architecture-audit.md). Regressionen: 208 Unit-Tests
lokal grün. **Keine** neue native SCUMM-v6-Funktion ist damit belegt.

**Unverändert als Produktentwicklung offen:** Allgemeine Action-/Condition-
IR, dynamische Raumgeometrie und vollständige native SCUMM-v6-Fähigkeiten.
Der Diagnosebericht beschreibt alle aktuell statisch erkannten Blocker;
für noch nicht typisierte Compilerfälle wird die allgemeine Ablehnung
zurückgegeben. Diese Fähigkeiten gehören zu den nächsten vertikalen
SCUMM-Paketen, nicht zum abgeschlossenen A0-Stabilisierungsgate.

## Verbindlicher SCUMM-v6-Referenzvertrag (2026-11-07)

Die [Referenzbibliothek](scumm-v6-reference/README.md) verbindet den
**einen** [64-ID-Funktionskatalog](SCUMM_V6_CAPABILITIES.md) mit
[technischen ScummC-/ScummVM-Primitiven](scumm-v6-reference/NATIVE_PRIMITIVES.md),
[konkreten Abnahmeszenarien](scumm-v6-reference/SCENARIOS.md) und einem
[maschinenlesbaren Quellenindex](scumm-v6-reference/capability_sources.json).
Das Produktziel ist damit für die Implementierung festgelegt. Vorhandene
Source-Audits werden wiederverwendet; neue Quellcodeanalyse ist nur bei
fehlendem v6-Encoder-/Decoder-/Sonderfallbeleg oder Versionswechsel nötig.
Die Referenz beschreibt den Zielumfang, **nicht** 64 bereits fertige
Funktionen. Ein kleines natives Test-Fixture pro Grundbaustein genügt;
ein großes neues Konformitätsspiel ist kein Gate.

**Nächster Implementierungsschritt bleibt P0.1** (nativer Binär-Roundtrip),
dann P0.2/0.3. Neue Features werden anhand des Katalogs und der
Szenarien abgenommen, nicht anhand zusätzlicher spontaner Demo-Limits.

## Nächste drei priorisierte Pakete

**Fortschritt 2026-11-07 nach den ursprünglichen P0.x-Planungen:**
Der SCUMM-v6-Raumparser (P0.1), native Z-Masken (P0.2) sowie Walkboxen,
BOXM und vertikale SCAL-Slots (P0.3) wurden in nachfolgenden vertikalen
Paketen umgesetzt und im unveränderten ScummVM geprüft; für konkrete
Nachweise siehe `scumm-v6-perspective-scal-contract.md` und die GitHub-
Actions-Läufe von PR #26/#27. Ein weiterer Teilbaustein der cineastischen
Funktionen ist das typisierte `camera_cues`-Raummodell mit nativem
`setCameraAt`, `panCameraTo`, `waitForCamera` und `cameraFollowActor`.
Die unabhängigen ScummVM-Bildkompositionen sind im Actions-Lauf
`42405122040` verifiziert ([Kamera-Vertrag](scumm-v6-camera-cue-contract.md)).
**Das nächste noch offene Schwerpunktpaket ist P0.4/P0.5:** native
bewegte Objekte und Actor-/Costume-Animationen mit zeitlichen Phasen;
vollständige Cutscene-Skip-Zustände bleiben P1.1 offen.

**Nächster P0.5-Teilnachweis (2026-11-07):** Ein allgemeiner
[`CostumeAsset`-Ressourcenvertrag](scumm-v6-native-costume-count-contract.md)
liefert eigene Bildframes, vier Blickrichtungen, Stand-/Walk-/Init- und
Aktionsanimationen sowie explizite `COUNT`-Kommandos in ScummCs v6-`COST`.
Die erzeugte Figur wurde in stock ScummVM gerendert; eine Counter-Scriptprobe
schaltet den Objektzustand nach zwei markierten Ereignissen, während eine
Gegenprobe mit drei erwarteten Ereignissen den Ausgangszustand bewahrt.
Die native CI-Evidenz liegt in Actions `42408510454` und deren Artefakten.
**Offen und priorisiert:** freie Actor-Instanzen samt Costume-Bindung im
Projektmodell, generischer Action-/Condition-/Ereignisablauf sowie echte
Spielereingabe während laufender Animation. P0.5 insgesamt ist nicht fertig.

**Weiterer P0.5-Modellschritt (2026-11-07):** `GameDocument` speichert nun
beliebig viele validierte `CostumeAsset`-Ressourcen als versioniertes JSON
(inklusive Frame-Pixeln, Blickrichtungen, nativen Animations-IDs und `COUNT`).
`export_document` schreibt zu den Räumen auch die zugehörigen `.scost`-
und Frame-BMP-Compiler-Eingaben. Bestehende JSON-v1-Projekte ohne Costumes
bleiben bitgenau unverändert. Dieses Gate belegt **noch keine freie
Actor-Instanz und keine Verknüpfung des COST im Spiel**; das nächste Paket
ist die native Actor-Symbol-/Costume-Bindung über den ScummC-Bootstrap.

**P0.5 Mehr-Actor-Integrationsschritt (2026-11-07):** Das Projektmodell hat
nun referenzgeprüfte Actor-Instanzen mit Costume-ID, Anfangsraum, Position,
Blickrichtung und optionalem Namen. JSON-v1-Roundtrip bleibt kompatibel,
und der ScummC-Forschungsadapter erzeugt globale `actor`-Symbole,
native Costume-Deklarationen, `initActor`/`setActorCostume` und Platzierung
für mehrere Actors. Ein gemeinsames Costume wird nur einmal kompiliert.
CI prüft einen SCUMM-v6-Spielstart mit zwei NPCs und gemeinsamem COST;
der native Ergebnisstatus ist erst nach grünem Actions-Lauf zu setzen.
**Noch offen:** freier Spieler-Actor jenseits des Road-Fixture-Symbols `hero`,
echte Spielgrafik-Evidenz für jede Figur, Animations-Cues, Action/Condition-IR
und Interaktion während laufender Animation. Der externe Bootstrap wird
nicht zur Produktarchitektur erklärt.

**P0.5-Teilbaustein (COUNT-Laufzeitgate erfolgreich, kein vollständiges Animations-Gate):**
`ActorAsset.initial_animation` referenziert optional eine benannte,
explizit numerierte native COST-Animation mit passender Startrichtung.
GameDocument-v1-JSON bleibt rückwärtskompatibel; der Forschungsadapter
erzeugt `animateActor(actor,index)` im Einstiegsscript des Startraums
nach der Actor-Initialisierung (nicht vor `startRoom`).
Der Mehr-Actor-CI-Probe startet eine solche Animation. Der eigenständige
COUNT-Laufzeitnachweis ist inzwischen erfolgreich; vollständige
Frame-Phasen, Spielerinteraktion und allgemeine Animations-Choreografie
sind damit noch nicht belegt.

**COUNT-Folgegate in ScummVM abgenommen (`42421713939`):** Eine isolierte
positive und negative ScummVM-Probe beobachtet nun
`getActorAnimCounter1(Companion)` des projektdefinierten Actors. Bei zwei
COUNT-Ereignissen muss der native Schlüsselzustand wechseln; die
Drei-Ereignis-Kontrolle darf ihn nicht wechseln. Die CI-Artefakte enthalten
beide Raumskripte, Screenshots und den Pixelbericht. Die positive und
negative Kontrolle sind im unveränderten ScummVM grün. Sichtbare
Animationsphasen, Eingaben während der Animation und eine allgemeine
Ereignis-IR bleiben gesonderte offene Gates.

**Behobener Fixture-Fehler (zuvor rot `42420046842`):** Der Raumscript-Pfad funktionierte
(bei COUNT-Schwelle 0 verschwindet der Schlüssel, 0 Pixel). Bei Schwellen
1, 2 und 3 bleiben dagegen jeweils 112 Schlüsselpixel sichtbar. Damit
ist noch **kein einziges COUNT-Ereignis** für den projektdefinierten
Actor belegt, obwohl die separate Ego-COST-Probe weiterhin grün war.
Raumzuordnung, Costume und aktiver Frame 24 wurden daraufhin separat
nachgewiesen. Die Ursache lag in der nur für `S` vorhandenen COUNT-Geste
des Mehr-Actor-Test-Costumes. Die vollständige N/E/S/W-Sequenz liefert
nun die erwarteten nativen Ereignisse. Die fixierte Testfixture ist
kein Beleg für beliebige Richtungswechsel während einer Animation.

**P0.5-Vertikalschnitt (native CI-Abnahme erfolgreich `42461862069`):**
`GameDocument.animation_rules` modelliert eine `ActorCountCondition`
(Actor und COUNT-Schwelle) mit einem `ObjectStateEffect` (Raum-Hotspot und
Zustand) als versioniertes, deklaratives JSON. Der ScummC-Adapter gibt
lokale native COUNT-Wächter-Scripts nach dem Anfangsanimationsaufruf aus.
Die Referenzen und die Erreichbarkeit des COUNT-Schwellwerts in einer
nicht-loopenden Anfangsanimation werden geprüft. Bestehendes v1-JSON
bleibt unverändert. Die neue CI-Probe kompiliert auch eine solche aus
Projekt-JSON geladene Regel und prüft den resultierenden Objektzustand
in stock ScummVM. Die positive JSON-Regel und die bisherige negative
Fixture-Kontrolle sind grün. Allgemeine Action-/Condition-IR, parallele Interaktion und
mehrstufige Animationsabläufe sind nicht abgeschlossen.

**P0.5-Eingabefolge (stock ScummVM, CI `42467237997`):** Ein
versioniertes `AnimationInputRule` erzeugt native `Push`-/`Pull`-/`Open`-/
`Close`-Verbfälle, die vor beziehungsweise nach einer COUNT-Grenze
unterschiedliche Objektzustände setzen. Der reproduzierbare native
Gameplay-Test prüft 0, 1 und 2 Eingaben: Ohne Klick bleiben Schlüssel
sichtbar und Tür nach COUNT 1 offen; ein früher Klick entfernt die Tür,
ein später Klick den Schlüssel,
und bei einem frühen und einem späteren Klick **im selben Spielprozess**
werden beide zeitabhängigen Aktionen nacheinander ausgeführt. Das
ist kein Nachweis für beliebige Wiederholung, mehrfach gestartete
Animationen, Raumwechsel oder Save/Load. Der seither ergänzte
Raumwechsel-Nachweis folgt unmittelbar darunter.

**P0.5-Raumwechsel-Teilnachweis (native CI `42468551627`):** Nach einer
verspäteten `Push`-Aktion verschwindet der Schlüssel; die offene Tür
ermöglicht den regulären `WalkTo`-Wechsel `Harbor → Cellar`. Über den
Treppe-Hotspot kehrt der Spieler nach `Harbor` zurück. Die native
ScummVM-Probe bestätigt, dass der Schlüssel weiterhin unsichtbar
und die Tür offen ist. Die bisherigen 0/1/2-Klick-Tests bleiben grün.
Der seither verifizierte Initialanimations-Lifecycle folgt direkt
darunter. Save/Load und das vollständige Fahrgeschäft bleiben offen.

**P0.5-Initialanimations-Lifecycle (stock ScummVM `42471602488`):**
`ActorAsset.initial_animation` startet nun durch ein pro Actor deklariertes
globales SCUMM-Bit genau beim ersten Eintritt in seinen Anfangsraum.
Beim Wiedereintritt wird weder die Anfangsanimation noch der daran
gebundene COUNT-Wächter erneut ausgelöst. Ein zusätzlicher nativer
Negativ-Wächter würde den zuvor entfernten Schlüssel nach einem
Doppelstart wieder sichtbar machen; der unveränderte ScummVM-Lauf
bestätigt, dass er verborgen bleibt. Der Guard umfasst alle an die
Animation gebundenen COUNT-Wächter. Die alten JSON-v1-Projekte bleiben
unverändert. Das nachfolgende Gate prüft nun auch Save/Load eines
**abgeschlossenen** COUNT-/Objektzustands. Weiter offen bleiben explizite
wiederholbare Animationen sowie Save/Load mitten in einer aktiven Animation.

**P0.5-Save/Load-Gate in stock ScummVM bestanden (`42477804196`):** Die
isolierte Actor-Fixture führt einen nativen Save/Load-Ablauf aus: späte
`Push`-Aktion, Prüfung der Key-/Door-Bilder, Speichern über den ScummVM-
Dialog, Neustart mit `--save-slot=1`, erneute Bildprüfung und regulärer
`Harbor → Cellar → Harbor`-Rückweg. Der COUNT-Replay-Negativwächter deckt
einen verlorenen Initialanimations-Guard auf. Der native CI-Schritt und
die zugehörige Artefaktaufbewahrung sind erfolgreich. Save/Load **während**
einer noch laufenden Animation ist davon nicht abgedeckt.
Die vormals auf einzelne Testfälle hartcodierten Screenshot-Frame-Namen in
den gemeinsamen Door-/Key-Pixelhelfern wurden durch eine gemeinsame sichere
Frame-Namensvalidierung ersetzt. Neue native Szenarien erfordern damit keine
Änderung an den allgemeinen Bildprüfhelfern mehr.

**P0.5-Produktfunktion (nativer ScummC-/Spielstart belegt, CI `42481225873`):** `animation_triggers`
ermöglichen wiederholbare Actor-Animationen über einen frei gewählten
Hotspot-Verbfall im versionierten `GameDocument`. Der native Export startet
die benannte, indizierte Costume-Animation bei jeder Aktion erneut, unabhängig
vom einmaligen Erststart-Guard. Das Actor-Projekt enthält eine authored
`Pull`-Aktion, die mit dem zweiten Actor ohne `initial_animation` kompiliert
und gelinkt wurde. Die wiederholte Interaktion bleibt bis zum Gameplay-Nachweis
als offen gekennzeichnet. **Nächstes Produktpaket:** kombinierbare
Animations-Cues und Reaktionen über mehrere Actors und Objekte.

**P0.5 – geordnete Interaktionsfolgen (Implementierung, native CI ausstehend):**
`interaction_sequences` verbindet ein Hotspot-Verb mit einer expliziten
Reihenfolge aus Actor-Animationen, `delaySeconds` und `setObjectState`.
Mehrere Actors und Objekte können in einer Sequenz referenziert werden;
Projekt-JSON, Referenzvalidierung und ScummC-Exporter sind angeschlossen.
Das bestehende native Actor-Projekt enthält eine authored `Close`-Aktion
mit zwei Cues und einer Objektreaktion. Noch kein visueller Gameplay-Nachweis
für die gesamte Sequenz. **Nächster Produktfokus:** Authoring und Bearbeitung
dieser Abläufe im Studio statt ausschließlich über Projekt-JSON.

**P0.5 – native Interaktionen im Studio bearbeiten (Implementierung, UI-/Gameplay-Gate offen):**
Der Gradio-Editor enthält einen separaten Bereich für validierte native
`GameDocument`-Dateien. Hier lassen sich Hotspot-Verb-Abläufe anlegen, Actor-
Animationen, Pausen und Objektzustände als Schritte anhängen, verschieben
oder entfernen und das Ergebnis als Projekt-JSON oder über den echten
ScummC-Pfad als Spiel-ZIP ausgeben. Bereits vorhandene Story-v4-Dateien
werden nicht stillschweigend als native Projekte behandelt. Service-
Roundtrip und Regressionstests sind lokal grün; Gradio-UI-Interaktion
und ein interaktiver ScummVM-Klickpfad wurden noch nicht geprüft.
**Nächstes Produktpaket:** Story-Authoring und native Actor-/Interaktions-
Authoringdaten in einem durchgängigen Projektmodell verbinden.

**P0.5 – Story/native Projekt-Integration (Implementierung, Gameplay offen):**
Im Studio lässt sich die aktuelle Story ausdrücklich in das native
`GameDocument` übersetzen. Vorhandene native Actor-/Costume-Daten und
Interaktionsregeln werden auf die frisch aus der Story generierten Räume
übertragen und dabei referenzvalidiert. Nach Storyänderungen wird beim
Projekt-Download und Spiel-Build erneut komponiert; gelöschte oder
umbenannte Objekte führen zu einem sichtbaren Fehler statt Datenverlust.
Das SCUMM-ZIP enthält sowohl die aktuelle `story.json` als auch die
kompilierte `project.json`. Die Gradio-UI startet im CI-Smoke (`42486144774`);
der neue Kompositionspfad wird per Integrationstest bis zur ScummC-Quelle
geprüft. Die aktuelle Umsetzung ist **noch kein gemeinsames persistentes
Story-/Native-Schema**: zusätzliche manuelle native Raumänderungen werden
beim bewussten Story-Abgleich nicht übernommen. Der echte ScummVM-Klickablauf
und das vollständige UI-Interaktionsgate fehlen weiterhin.
**Nächstes Produktpaket:** ein versioniertes gemeinsames Authoring-Dokument,
das Story- und Actor-/Costume-/Interaktionsdaten dauerhaft und verlustfrei
zusammen speichert und wieder lädt.

**P0.5 – gemeinsames Studio-Authoring-Dokument (Implementierung, CI ausstehend):**
Das Studio speichert und lädt nun `adventure.studio.json` mit einem
versionierten Story-Dokument und einer nativen Actor-/Costume-/Action-Ebene.
Die referenzgeprüfte Story-Übersetzung bleibt die einzige Quelle für Räume,
Bitmaps und Hotspots; die native Ebene wird ohne redundante generierte
Room-Ressourcen gespeichert. Der Studio-Editor stellt beide Ebenen nach
Laden wieder her, erlaubt weitere Schritte und kann daraus das native
SCUMM-Projekt bzw. Spiel-ZIP erzeugen. Bestehende Story-/native-JSON-Dateien
werden nicht migriert oder ersetzt. Lokaler Roundtrip mit Bearbeitung und
alle Regressionstests grün; vollständiger UI-Klicktest und nativer Gameplay-
Nachweis bleiben offen.
**Nächstes Produktpaket:** Actors und Costumes direkt im gemeinsamen Studio-
Projekt anlegen und bearbeiten, ohne eine externe native JSON-Datei als
Ausgangspunkt zu benötigen.

**P0.5 – Actor-/Costume-Authoring im Studio (Implementierung, CI ausstehend):**
Aus einem vom Autor geladenen PNG lässt sich jetzt im Studio eine echte
palettierte native Costume erzeugen. Das Studio legt damit Actors in
gewählten Story-Räumen an und erlaubt deren Position/Richtung zu ändern.
Jedes neue Costume enthält zunächst eine Standpose und eine per
Interaktionsfolge nutzbare `gesture`-Animation auf Index 24. Projekt-JSON,
gemeinsames `adventure.studio.json` und ScummC-COST-Export bleiben derselbe
Produktpfad. Ein Integrationstest belegt PNG → Costume/Actor → validiertes
Modell → ScummC-Quellen (Fake-Compiler); noch **kein** echter nativer Build
oder ScummVM-Nachweis der neu importierten Grafik.
**Nächstes Produktpaket:** mehrteilige Costume-Animationen und individuelle
Blickrichtungen aus mehreren importierten Frames im Editor definieren.

**P0.5 – mehrteilige Costume-Animationen im Studio (Implementierung, CI ausstehend):**
Bestehenden Costumes können jetzt mehrere echte PNG-Frames zugeordnet
werden. Ein gemeinsamer 31-Farben-Palettenvertrag erhält bereits importierte
Framefarben; zusätzliche unpassende Farben werden sichtbar abgewiesen.
Im Studio werden benannte Animationen mit eigenen nativen Indizes und
richtungsbezogenen Frame-/COUNT-Folgen definiert oder aktualisiert. Der
bestehende Interaktionseditor kann diese Animationen über ihren Namen
auslösen. Modell, versionierte Projektdatei und ScummC-COST-/Verbquellen
sind verbunden. Ein gezielter Studio-Integrationstest mit zwei PNGs und
einer `wave`-Animation ist grün; echter ScummC-Build und stock-ScummVM-
Gameplay dieser neuen Mehrframe-Costume sind noch offen.
**Nächstes Produktpaket:** visuelle Costume-Frame-/Animationsvorschau und
direkte Frame-Reihenfolge im Editor statt kommaseparierter Kommandoliste.

**P0.5 – visuelle Costume-Timeline (Implementierung, CI ausstehend):**
Der Studio-Editor zeigt die echten Costume-Frame-Pixel und COST-Kommandos
einer ausgewählten Richtung als geordnete Karten. Schritte können direkt
angeklickt, umsortiert, angehängt und entfernt werden. Die Speicherung
verändert ausschließlich die typisierten `CostumeDirection.commands`; das
SCUMM-Projekt und der Compilerpfad bleiben unverändert. Der bestehende
Studio-Integrationstest prüft Vorschaureihenfolge, Bearbeitung und die
resultierende `.scost`-Quellfolge; keine zusätzliche Engine-Testmatrix.
Eine animierte Echtzeitvorschau oder ein ScummVM-Nachweis der neuen
Mehrframe-Sequenzen liegt noch nicht vor.
**Nächstes Produktpaket:** eine abspielbare Editor-Vorschau über die
vorhandenen Frames und Richtungsauswahl, mit einstellbaren Framezeiten,
ohne eine zusätzliche Spiel-Runtime zu simulieren.

**P0.5 – abspielbare Costume-Vorschau (Implementierung, CI ausstehend):**
Die gewählte Richtung einer Costume-Animation lässt sich jetzt direkt
im Studio als GIF abspielen. Die Frames stammen unverändert aus den
importierten COST-Bilddaten; die relative native Frame-Position bleibt
erhalten. Eine frei wählbare Millisekunden-Dauer steuert ausschließlich
die Editor-Wiedergabe, **nicht** native SCUMM-Framezeiten oder Costume-
COUNT-Kommandos. Der bestehende Studio-Integrationstest prüft Ausgabe,
Frameanzahl und Wiedergabedauer. Keine eigene Spiel-Runtime.
Stock-ScummVM-Bild- und Gameplay-Nachweise bleiben offen.
**Nächstes Produktpaket:** native ScummC-Kompilierung und tatsächliche
Wiedergabe einer aus Studio-PNGs erzeugten Mehrframe-Costume in stock
ScummVM belegen, bevor weitere Komfortfunktionen priorisiert werden.

**Studio-PNG-Nativpfad (2026-11-08, Nachweis ausstehend):** Der bestehende
experimentelle ScummC-/ScummVM-Workflow baut nun zusätzlich aus zwei
wirklichen PNGs über die produktiven Studio-Funktionen eine mehrteilige
`wave`-COST-Animation mit vier Richtungen und Actor-Startanimation. Er
exportiert das versionierte Projekt, kompiliert es und startet das Spiel in
stock ScummVM; Compilerquellen, Projekt-JSON und Bilder werden als Artefakte
aufbewahrt. Lokal ist die ScummC-Quellgenerierung geprüft; **CI-Ausführung,
Kompilierung, Spielstart und sichtbarer Framewechsel sind noch nicht
nachgewiesen**. Das nächste Gate bleibt die Auswertung dieses nativen
Laufs und ein tatsächlicher Framewechsel-Nachweis, bevor die Fähigkeit als
in ScummVM verifiziert eingestuft wird.

**Actor-Startanimation im Studio (2026-11-08):** Die Gradio-Oberfläche kann
für einen bestehenden Actor jetzt eine seiner nativen COST-Animationen als
einmalige Startanimation auswählen oder die Startanimation deaktivieren.
Auswahl und Änderung bleiben im gemeinsamen Projekt-JSON erhalten; der
bestehende SCUMM-v6-Exporter gibt `animateActor` mit dem bereits validierten
Animationsindex aus. Es ist keine neue Runtime-Funktion. Native Wiedergabe
von importierten PNG-Mehrframe-Costumes bleibt bis zum echten
ScummVM-Bildnachweis offen.

**Actor zur Laufzeit versetzen (2026-11-08):** In einer geordneten
Studio-Objektinteraktion lässt sich jetzt ein Actor an eine neue X-/Y-Position
im selben Raum setzen. Der typisierte `move_actor`-Schritt wird im
versionierten Projekt-JSON gespeichert und als natives
`putActorAt(actor, x, y, room)` zusammen mit den bisherigen Animations-,
Warte- und Objektzustandsschritten ausgegeben. Der Studio-Editor bietet
die Aktion direkt an. Geprüft sind Modell-/Exportpfad und die bestehende
Regression; **die interaktive Auslösung im stock ScummVM ist noch offen**.
Nächstes Produktpaket: tatsächliches Mehrframe- und Actor-Bewegungs-
Gameplay im nativen Compiler-/Interpreterpfad nachweisen.

**Laufbewegung als Story-Interaktion (2026-11-08):** Zusätzlich zum
sofortigen `move_actor`-Versetzen kann das Studio jetzt einen Actor per
`walk_actor` im selben Raum zu einer Zielposition schicken. Das
versionierte JSON und der SCUMM-v6-Exporter verwenden das bereits für
den Demo-Spieler belegte native `walkActorTo`; nachfolgende Aktionen
laufen bewusst ohne implizite Ankunftssperre weiter. Die visuelle
Spielprobe und eine später explizite `waitForActor`-Choreografie bleiben
offen. Das nächste Produktgate bleibt echter ScummVM-Nachweis für
Actor-Laufbewegung und die importierten Mehrframe-Costumes.

**Warten auf Actor-Ankunft (2026-11-08):** Der Studio-Interaktionseditor
hat nun einen expliziten `wait_actor`-Schritt. Auf einen
`walk_actor`-Laufauftrag kann so ein natives `waitForActor(actor)` folgen,
bevor weitere Animations- oder Objektaktionen ausgeführt werden.
Das Projekt-JSON bewahrt die Reihenfolge; nur im selben Raum vorhandene
Actors sind gültig. Die ScummC-Signatur ist im unveränderten upstream
`examples/road/road.scc` und `examples/openquest/officeroom.scc` belegt.
Ein interaktiver ScummVM-Nachweis der neu authorbaren Actor-Choreografie
bleibt offen. Nächstes Gate: diese Abfolge und importierte Mehrframe-
Costumes im echten Spiel beobachten.

**Actor-Blickrichtung zur Laufzeit (2026-11-08):** Der Studio-Ablauf
enthält nun `face_actor` als eigenständige Aktion mit N/E/S/W-Auswahl.
Projekt-JSON und Validator halten Actor- und Raumreferenz fest; ScummC
verwendet das in upstream `examples/road/road.scc` belegte Paar
`setCurrentActor`/`setActorDirection` und stellt danach `VAR_EGO` als
aktiven Actor wieder her. Der Schritt ist mit Bewegung, Ankunfts-Wait,
Animation und Objektzustand kombinierbar. Die interaktive ScummVM-
Choreografie ist weiterhin nicht als V belegt.

**Native Mehrframe-Animation – ausführbarer Bildnachweis (2026-11-08):**
Die bestehende Studio-PNG-Actor-Probe sammelt jetzt während eines einzigen
stock-ScummVM-Spielstarts mehrere Szenenbilder und verlangt sichtbare
Pixel beider unterschiedlich gefärbten COST-Frames. Ein bloßer Spielstart
oder identisches Standbild reicht nicht mehr aus. Der experimentelle
ScummC-Workflow läuft für diese Probe nun auch bei passenden Pull Requests;
die Einzelbilder werden als CI-Artefakte bereitgestellt. **Bis zu einem
erfolgreichen nativen Lauf bleibt die V-Einstufung offen.** Das folgende
Paket ist die Auswertung und bei Bedarf Korrektur der konkreten nativen
Spielgrafik, danach der Actor-Lauf-/Wait-/Dreh-Choreografie.

**Erster tatsächlicher CI-Lauf und konkreter Fix (2026-11-08):** Der native
Lauf `42493144908` kompiliert die Studio-COST, startet ScummVM und liefert
24 Bilder; die erwarteten PNG-Farben erscheinen darin jedoch nicht. Die
Original-ScummC-COST-Palette enthält **absolute Raum-Palettenindizes**,
deren RGB-Werte im bisherigen Export nicht in die Room-BMP übernommen
wurden. Der Export gleicht deshalb nun die belegten COST-Farben aller
gebundenen Actors über einen gemeinsamen, deterministischen Indexplan ab
und ergänzt die Räume, ohne das Authoring-JSON zu verändern. Belegte
Room-Artwork-Indizes bleiben reserviert; bei erschöpften Plätzen wird der
Exporter-Blocker ausdrücklich gemeldet. Ein gezielter BMP-Palettenvergleich
ist grün. Im erneuten nativen Lauf `42493988461` sind beide Costume-Farben
in 26 ScummVM-Aufnahmen sichtbar und wechseln ihre Dominanz. Die
Abnahme fordert nun ausdrücklich diesen zeitlichen Wechsel statt nur
zweier irgendwann vorhandener Farben. Der finale native Lauf
`42494840322` ist grün: Die aus Studio-PNGs exportierten Costume-Frames
wechseln sichtbar im unveränderten ScummVM. PR #54 wurde nach den
vollständigen CI-Prüfungen gemergt (`bbba784`). Die gesamte Actor-
Choreografie durch Spielereingaben bleibt weiter als V offen.

**Studio-Interaktionseditor (2026-11-08):** Ein bestehender Schritt lässt
sich nun auswählen, in die vorhandenen Aktionsfelder zurückladen und am
selben Platz ersetzen. Actor, Animation, Bewegung, Blickrichtung, Pause
und Objektzustand nutzen weiterhin das validierte Projektmodell und den
existierenden nativen Exportpfad. Das Bearbeiten erfordert kein Löschen
und erneutes Anhängen und verändert nicht das auslösende Hotspot-Verb.
**Nächstes Produktgate:** Eine vollständige, vom Studio authorbare
Actor-Lauf-/Wait-/Dreh-/Animationsfolge durch einen tatsächlichen
ScummVM-Verb-Klick nachweisen.

**Native Klick-Choreografie (ScummVM-Teilnachweis, 2026-11-08):** Ein
End-to-End-Spiel wird aus dem gleichen `append_sequence_step`-Pfad wie der
Studio-Editor erzeugt. Der reale `Close`-Klick auf den Schlüssel soll
`Guide` versetzen, laufen lassen, auf die Ankunft warten, drehen,
animieren und anschließend die Tür öffnen. Die Actions-Probe archiviert
Projekt-JSON, generierten SCUMM-Quelltext, Bilder vor/nach dem Klick und
den Zustandsbericht. Im unveränderten ScummVM öffnet der reale Klick die
vorher geschlossene Tür nach der generierten sechsstufigen Folge (CI
`42501905023`, `response_seconds=3.44`). **Das ist ein Teilnachweis des
geketteten Verbablaufs**, kein Einzelbeweis für jeden Animationframe oder
jede Walkbox-Position. Als nächstes sind solche visuellen Actor-
Zwischenzustände und Wiederholung/Abbruch im Spiel gezielt zu prüfen.

**Zustandsgebundene Interaktionsfolgen (2026-11-08, Teilnachweis):**
Eine vorhandene Hotspot-/Verbfolge kann im Studio optional nur bei einem
konkreten Raumobjektzustand (0–2 im derzeitigen Exportvertrag) ausgeführt
werden. Modell, JSON-v1-Roundtrip und Gradio-Editor verwenden dieselbe
Bedingung; der ScummC-Export setzt ein natives `getObjectState`-Gate vor
die geordneten Aktionen. Ohne Bedingung bleibt die bisherige JSON-Ausgabe
unverändert. Der bestehende reale Klick-Actor-Ablauf mit Türzustand 1 als
Voraussetzung lief im unveränderten ScummVM erfolgreich (CI `42505166878`,
PR #57 gemergt). Der negative Zustand und die Wiederholung waren noch offen.

**Mehrere Zustandsvarianten je Verb (2026-11-08, ScummVM nachgewiesen):** Im Studio
können bestehende Folgen für einen weiteren Zustand desselben Raumobjekts
dupliziert und unabhängig bearbeitet werden. Der Export führt sie unter
einem einzigen nativen `case` mit disjunkten Zustandsvergleichen aus und
akzeptiert optional eine bedingungslose Fallback-Folge. Mehrdeutige
Varianten werden schon im Projektmodell abgewiesen. Der native
Spielablauf führte dieselbe `Close`-Aktion dreimal aus: Türzustand
1 → 2 → 1 → 2, einschließlich Rückkehr zur ersten Actor-Choreografie.
CI `42506834029`, Artefakt `native-v6-studio-actor-sequence`. Beim ersten
Lauf zeigte sich ein wandernder Kameraausschnitt; die Klickprobe bestimmt
deshalb vor jeder Eingabe die aktuelle Hotspot-Position neu, ohne die
Studio-Produktlogik zu ändern.
**Neues Teilpaket:** Studio-Verbfolgen können optional mit Escape übersprungen
werden. ScummC emittiert native `try`/`override`-Blöcke; der Override setzt
die letzten dokumentierten Raumobjekt-Zustände, Actor-Zielpositionen und
Blickrichtungen. Das veränderte native Klickszenario sendet Escape während
eines Actor-Ablaufs und prüft den Türzustand (CI `42508973832`, PR #59).

**Aktuelles Produktpaket:** Studio-Interaktionsfolgen können nun einen
aufnehmbaren Gegenstand als nativen `pickupObject`-Schritt enthalten – auch
innerhalb einer bedingten Variante. Beim Escape-Skip wird dieser Effekt
ebenfalls angewendet, sodass die Inventaraufnahme nicht an einer übersprungenen
Wartezeit verloren geht. Die native Probe ergänzt deshalb die zweite
Zustandsvariante um einen eigenen Token und kontrolliert dessen Inventar-Icon
nach Escape. Vollständige Ton-/Raumwechsel-Skip-Zustände bleiben offen.

**Nächstes Produktpaket:** Eine `Inventar kombinieren`-Aktion kann im
Studio an ein bestehendes Raumrezept gebunden werden. Die normale Sequenz
prüft den Besitz beider Eingangsobjekte, verbraucht sie und erzeugt das
Rezeptresultat mit nativen SCUMM-Befehlen. Der Escape-Pfad übernimmt die
vorherigen Aufnahmen und die Kombination in derselben Reihenfolge. Das
Stock-ScummVM-Szenario überprüft dafür ein aus Token und Shard erzeugtes
Badge nach Escape; der CI-Nachweis steht bei Erstellung noch aus. Audio-
und Raumwechsel-Endzustände bleiben außerhalb dieses Pakets.

**Folgepaket Raumwechsel am Sequenzende (2026-11-08, Implementierung):**
Im Studio kann `Raum wechseln` als letzter Schritt einer Hotspot-/Verbfolge
auf einen existierenden Projekt-Raum zeigen. Der JSON-v1-Vertrag nimmt
optional `change_room` auf; frühere Projekte bleiben unverändert. Der
ScummC-Exporter gibt `startRoom` erst **nach** den bisherigen Schritten und
bei überspringbaren Folgen erst **nach** `try`/`override` aus, damit Actor-,
Objekt- und Inventar-Endzustände vor dem Wechsel angewendet werden. 287 lokale
Tests grün, darunter Editor-/JSON-/ScummC- und Ungültigzielprüfungen.
**Native Abnahme ergänzt:** Die bestehende echte `Close`-Spielprobe führt
nach der Inventarkombination eine separate Studio-`Door`-Sequenz aus,
überspringt ihre sechssekündige Wartezeit, betritt `Cellar`, kehrt über
`Stairs` nach `Harbor` zurück und prüft offene Tür sowie Badge im Inventar.
Die neue Zusammensetzung bestand im unveränderten ScummVM (Actions
`42514653114`, Actor-Choreografie-Schritt). Der erste Gesamtlauf hatte
einen nachgelagerten zeitabhängigen PNG-Costume-Fehler; dessen Wiederholung
hat den PNG-Schritt bestanden. Gesamtworkflow und weitere CI-Gates sind
gesondert abzuschließen. **Keine vollständige S04-Abnahme**, da native
Audio-Endzustände offen sind.
**Nächstes Produktpaket:** Sequenz-Audio-Cues und ihr definierter Escape-
Endzustand über Studio/JSON/ScummC/stock ScummVM nutzbar machen.

**Sequenz-Audio-Produktpaket (2026-11-08, Implementierung):** Das Gradio-Studio
nimmt echte MIDI-Dateien entgegen und bindet sie als versionierte, eingebettete
`music_assets` an einen Raum. Der normale native ZIP-Export erzeugt mit
ScummCs `soun -gmd` die benötigte SOUN-Ressource ohne eine externe Studio-
Runtime; fehlende/ungültige Ressourcen werden nicht still übergangen.
Interaktionssequenzen besitzen nun `Musik starten` und `Musik stoppen`, mit
nativen `startMusic`/`stopMusic`-Schritten. Der Escape-Override übernimmt
den **letzten** Musikeffekt vor einem möglichen terminalen Raumwechsel.
JSON-v1-Projekte ohne Audio bleiben unverändert. 288 lokale Tests grün.
Die native Actor-Klickprobe kompilierte das Studio-MIDI zu `SOUN`, lief im
unveränderten ScummVM und erfasste drei zeitlich abgegrenzte PCM-Fenster
(Actions `42517210707`, Actor-Schritt erfolgreich): Aktivität vor dem
Escape-Stopp `0,9482`, danach `0,2686`, nach erneutem Start `0,9830`.
Der relative Stop-/Wiederstart-Unterschied ist ein **verbindliches
CI-Gate** und wurde im finalen PR-Lauf `42517572328` (Wiederholung nach
einem nicht reproduzierten älteren Tür-Smoke-Fehlschlag) erneut bestanden.
Alle Pflichtworkflows des Pakets sind grün.
Die allgemeine iMUSE-/Beat-/Taktabdeckung bleibt offen.
**Nächstes Produktpaket nach der CI-Abnahme:** frei authorbare Soundeffekte
mit eigenen Ressourcen und synchronisierten Spielereignissen.

**Studio-VOC-Soundeffekte (2026-11-08, Implementierung und lokale Tests):**
Pro Raum lassen sich originale Creative-Voice-(`.voc`)-Dateien mit eindeutiger
Sound-ID importieren. Die Studio-Sequenzaktionen `Sound starten` und
`Sound stoppen` erzeugen native `startSound`-/`stopSound`-Aufrufe; der
Escape-Override übernimmt für **jede** beteiligte Sound-ID die letzte
Aktion. JSON-v1-Roundtrip und Projekt-ZIP enthalten die binären VOC-Daten,
der reguläre ScummC-Export kompiliert sie über `soun -voc` zu SOUN.
289 lokale Tests grün, einschließlich zweier unabhängiger Sound-Endzustände
in derselben Sequenz und Fake-Toolchain-Export. Die native Hotspot-Klickprobe
im unveränderten ScummVM (`42522610786`, Wiederholung nach älterem
Screenshot-Smoke-Timeout) kompiliert das originale VOC zu SOUN und bestätigt
den Escape-Stop anhand des PCM-Gates: vor dem Klick `0,0000`, während des
Sounds `0,8558`, nach Escape `0,0000` bei 2.211.840 PCM-Bytes.
Der vollständige Pflichtworkflow ist zum Zeitpunkt dieser Dokumentation
noch nicht abgeschlossen.
VOC-Sprachvarianten, Untertitel und Synchronisierung mit Actor-Lippensprache
bleiben offen.

**Sprachzeilen mit VOC und Untertitel (2026-11-08, Implementierung):**
Die Studio-Sequenzaktion `Gesprochene Zeile` verbindet einen importierten
Raum-VOC-Effekt mit editierbarem Untertitel und optionalem Actor (ohne
Auswahl spricht Ego). Der native SCUMM-v6-Export startet die SOUN-Ressource,
zeigt den Text mit `egoSay`/`actorSay`, wartet auf die Nachricht und beendet
den Sound; der Escape-Endzustand stoppt die Sprachausgabe ebenfalls.
Die erste Version validiert Untertitel bewusst als native, sichere ASCII-
Zeichenkette mit maximal 160 Zeichen; mehrsprachige Glyphen erfordern
eine separate Charset-Integration. JSON-v1 ist rückwärtskompatibel.
290 lokale Tests sind grün. Die echte ScummVM-Probe aus CI
`42524819678` zeigt den Untertitel `I can hear the bell.` sichtbar
über der Spielfigur, während die importierte VOC-Datei hörbar ist:
PCM-Aktivität vor dem Klick `0,0000`, während der Zeile `0,8557`,
nach Escape `0,0000` (2.109.440 PCM-Bytes). Die vollständigen
Pflichtworkflows der PR-Schlussrevision wurden für PR #65 vollständig grün
abgeschlossen (Merge `031053e1`).

**Unicode-Untertitel mit nativer CHAR-Erzeugung (2026-11-08, Implementierung):**
Die bisherige ASCII-Grenze für `Gesprochene Zeile` entfällt. Das Studio
akzeptiert nun auch Umlaute und weitere Unicode-Glyphen; der Export sammelt
die tatsächlich benötigten Zeichen aus beliebig vielen Sprachzeilen,
berechnet einen stabilen SCUMM-Byteplan und erzeugt mit dem vorhandenen
Font-Paketpfad ein verifiziertes natives `multilingual-font.char`.
Die ScummC-Quelle verwendet dazu explizite `\\xNN`-Bytes statt ungesicherter
UTF-8-Literale. Ein nicht vorhandener DejaVu-Font bzw. fehlende `char`-
Toolchain führt zu einer verständlichen Exportfehlermeldung. Bestehende
ASCII-Projekte benötigen keinen zusätzlichen Font-Build. 291 lokale Tests
grün. Der echte ScummVM-Klicklauf `42526681259` zeigt den korrekt gerenderten
Umlaut in `Ich höre die Glocke.`; das VOC-Audio misst vor dem Klick `0,0000`,
während der Zeile `0,8558` und nach Escape `0,0000` (2.105.344 Bytes).
Die vollständigen Pflichtworkflows der Schlussrevision stehen noch aus.
Sprachabhängige VOC-Varianten und dynamischer Sprachwechsel bleiben offen.

**Sprachvarianten pro VOC-Zeile (2026-11-08, Implementierung):**
Studio-Projekte besitzen eine einstellbare Standardsprache (zwei Buchstaben,
für alte JSON-v1-Daten weiterhin `en`). Jede `Gesprochene Zeile` kann
beliebig viele weitere Sprachvarianten mit eigener Raum-VOC-Sound-ID und
eigenem Unicode-Untertitel enthalten. Die Studio-Aktionsbearbeitung fügt
Sprachen hinzu, ersetzt oder entfernt sie. Beim regulären Export wird der
native `GameLanguage`-Zustand über sichtbare Sprachverben umgeschaltet;
die Sequenz verzweigt Text **und** Soundressource und fällt für fehlende
Übersetzungen ausdrücklich auf die Standardsprache zurück. Escape stoppt
alle potenziellen Sprachaufnahmen. Die aktuelle native Sprachleisten-UI
unterstützt bis zu fünf Sprachcodes; das Fachmodell kann mehr tragen,
ein solcher Export wird dann klar abgelehnt. 292 lokale Tests grün,
neue stock-ScummVM-Klick-/Sprachwechsel-/PCM-Probe erfolgreich in CI
`42528788315` (Artefakt `native-v6-studio-voc-localized`): Nach Auswahl
von `de` zeigt der native Screenshot `Ich höre die Glocke.` einschließlich
Umlaut. Die Audiomessung ergibt vor dem Klick `0,0000`, während der
deutschen Zeile `0,8115` und nach Escape `0,0000`; die gewählte
Sprachvariante ist damit im Spiel hör- und sichtbar. Die vollständige
Pflicht-CI der Schlussrevision bleibt gesondert zu prüfen.

**Gemeinsame Story- und VOC-Lokalisierung (2026-11-08, Implementierung):**
Der native SCUMM-v6-Exporter kann jetzt ein geprüftes Story-Sprachpaket mit
den in Studio erfassten Sprachvarianten gesprochener Zeilen kombinieren.
Ein gemeinsamer CHAR-Font enthält die Zeichen beider Textbestände;
Dialog-/Objekttexte und VOC-/Untertitel-Verzweigungen teilen sich
`GameLanguage` und dieselbe sichtbare Sprachauswahl. Die Eingabeprüfung
weist abweichende Quellsprachen sowie VOC-Sprachcodes außerhalb des
Story-Katalogs sichtbar zurück. Die vorhandenen getrennten Exporte bleiben
erhalten; historische Projekt-JSONs benötigen keine Migration. Im nativen
Studio-ZIP-Export kann eine vollständige `language-catalog.json` direkt
geladen werden. 293 lokale Tests sind grün. Die kombinierte native
stock-ScummVM-Probe CI `42531065406` zeigt **gleichzeitig** den deutschen
Objektnamen `Schlüssel` und `Ich höre die Glocke.` als Voice-Untertitel;
der PCM-Gate misst vor dem Klick `0,0000`, während der Wiedergabe `0,8012`
und nach Escape `0,0000` (Artefakt `native-v6-studio-story-voc-localized`).
Die übrigen Pflicht-Gates der Schlussrevision sind gesondert abzuschließen.
Offen bleiben insbesondere
automatische Sprachaufnahmen an Gesprächsknoten und Actor-Lippensync;
das kombinierte Paket erfordert einen vollständig übersetzten Story-Katalog.

**Sprachaufnahmen an NPC-Gesprächszeilen (2026-11-08, Implementierung):**
Der Studio-Editor kann jetzt für die Öffnungszeilen und Antworttexte der
vorhandenen verzweigten NPC-Gespräche eine importierte Raum-VOC-Aufnahme
der Standardsprache und weitere Sprachaufnahmen binden. Die native SCUMM-
Ausgabe startet die pro `GameLanguage` ausgewählte Aufnahme zum passenden
übersetzten `egoSay`-Text und stoppt anschließend alle möglichen Aufnahmen.
Die Bindungen stehen verlustfrei im versionierten Projekt-JSON und bleiben
beim Zusammensetzen mit einer geänderten Story nur erhalten, wenn die
Dialogzeile noch dieselbe ist; sonst wird der Export klar abgewiesen.
295 lokale Tests sind grün. Die native Dialog-/VOC-Probe in stock ScummVM,
CI `42533774527` (Artefakt `native-v6-studio-dialogue-voice`), zeigt die
gesprochene Öffnungszeile `Was suchst du hier?`, hörbares VOC-Audio
(`pcm_active_fraction = 0,3279`), zwei eingeblendete Antwortobjekte und
deren erfolgreiches Entfernen nach einer echten Antwortauswahl.
Die vollständigen Pflichtworkflows der Schlussrevision bleiben getrennt
abzuschließen.
Scope-Limit: Der aktuelle SCUMM-Dialog-Compiler unterstützt weiterhin
nur flache, begrenzte Antwortzweige ohne Actor-Lippensynchronisation;
vollständige beliebige Dialoggraphen bleiben offen.

**Mehrstufige NPC-Gespräche mit Rückweg (2026-11-09, Implementierung):**
Story-Dialogknoten mit Auswahlantworten können jetzt weitere Auswahlstufen
öffnen oder zur Einstiegsstufe zurückführen; die native SCUMM-v6-Ausgabe
blendet nur die gerade gültigen Antwortobjekte ein und setzt deren Zustand
bei jeder Auswahl explizit. Der Studio-Dialogeditor kann neue Antworten
mit optionalem Zielknoten hinzufügen und abschließende Antworten atomar
mit einer neuen Sprechzeile fortsetzen. Die vorhandene JSON-v1-
Raumstruktur bleibt ohne Stage-Felder identisch, zusätzliche Stufen werden
als optionale `stages` und `next_stage_id` serialisiert. Dialog-Audiobindungen
und der Sprachkatalog berücksichtigen auch Zeilen nach der ersten Stufe.
297 lokale Tests sind grün. Die native Mehrstufen-/Rückweg-Klickprobe in
stock ScummVM ist erfolgreich (CI `42536777733`, Artefakt
`native-v6-studio-nested-dialogue`): Einstiegsantworten eingeblendet,
zweite Stufe sichtbar, Rückkehr zur ersten Stufe und sauberes Schließen
(`passed = true`, `answer_pixels_dismissed = 0`). Während des Übergangs
werden die bisherigen Antwortobjekte nach gesprochenen Zeilen erneut
ausgeblendet; beide Reihen bleiben im 144-Pixel-Viewport. Die native
UI verwendet weiterhin klickbare Antwortobjekte statt eines echten
SCUMM-Gesprächsmenüs; Sprecherwechsel und völlig freie Layouts bleiben offen.

**Sprecherzuordnung im Dialogeditor (2026-11-09, Teilimplementierung):**
Bestehende Sprechzeilen und neu an abschließende Antworten angehängte
Dialogknoten können im Studio jetzt ausdrücklich einer Figur derselben Szene
zugeordnet werden. Die fachliche Validierung verhindert fremde Szenen;
der bestehende Story-JSON-Vertrag bleibt unverändert. 299 lokale Tests
grün. Der Story-zu-SCUMM-Adapter ordnet Sprecher in Gesprächen mit
Antwortauswahl eigenen nativen Actors mit Costume zu und gibt ihre Zeilen
mit `actorSay` aus; die Zeilenbindung bleibt im Projekt-JSON erhalten.
Die neue native Actor-Sprechprobe ist in stock ScummVM erfolgreich
(CI `42540762070`, Artefakt `native-v6-studio-multispeaker-dialogue`):
Die Antwort wird angeklickt, danach erscheint die separate schwarze
`actorSay`-Zeile des Zeugen mit `speaker_text_pixels = 1700`;
`answer_pixels_dismissed = 0`, `passed = true`. Die Actor-Costume nutzt
eine von den Antwortobjekten getrennte Farbe. Mehrsprecher-Gespräche ohne
Auswahlstufe und Costume-Lippensynchronisierung bleiben offen.

**Lineare Mehrsprecher-Gespräche (2026-11-09, nativ bestätigt):**
Auch Sprechketten ohne Antwortmenü exportieren jetzt die vom Story-Editor
zugeordneten Figuren als native `actorSay`-Zeilen. Der SCUMM-Raum hält dafür
optionale `talk_actor_lines` pro Hotspot; einstufige Altprojekte behalten
ihre unveränderte JSON-Struktur und `egoSay`-Ausgabe. Die neuen Actor-Bindungen
werden auf Vollständigkeit und Szenenzugehörigkeit geprüft. 301 lokale Tests
sind grün. Die eigenständige native Zwei-Sprecher-Probe hat im unveränderten
ScummVM-Interpreter zwei aufeinanderfolgende, unterschiedliche Sprechtexte
ohne Antwortmenü sichtbar bestätigt (CI `42542244245`, 112 und 1056
Textpixel, `passed: true`). Costume-Lippensync bleibt offen.

**Lineare Sprechketten direkt im Studio authoren (2026-11-09, Implementierung):**
Die Registerkarte „Dialogzeilen“ kann eine abschließende Gesprächszeile nun
mit einer neuen Zeile fortsetzen und dabei einen anderen Sprecher derselben
Szene wählen. Die Änderung läuft über den bestehenden Vorschau-/Übernahmeweg,
speichert die neue Knotenverbindung im Story-JSON und wird vom nativen
Dialog-Exporter ohne zusätzliche Laufzeit übernommen. Dialogknoten mit
bereits vorhandener Antwortauswahl oder Folgekante können nicht überschrieben
werden. 304 lokale Tests grün; der native Fixture-Aufbau benutzt dieselbe
Studio-Operation. Der native Dialog-Gameplay-Lauf `42543308699` bestätigt
zwei unterschiedliche gesprochene Actor-Zeilen in ScummVM; die dritte, im
Studio angehängte Zeile ist im kompilierten `Harbor.scc` als `actorSay`
enthalten. Für die dritte Zeile existiert noch kein eigener visueller
Laufzeitnachweis. Der übergreifende Kompatibilitätslauf `42543308664`
war nach einem nicht reproduzierten PNG-Frame-Fehler im zweiten Versuch grün.

**Actor-Blickrichtung je Dialogzeile (2026-11-09, Implementierung):**
In „Dialogzeilen“ lässt sich pro gesprochenem Knoten eine optionale Richtung
N/O/S/W auswählen oder entfernen. Der persistierte Story-v4-Vertrag lässt
Altdateien unverändert; die zugeordneten nativen Actors werden sowohl in
linearen als auch verzweigten Gesprächen vor ihrer `actorSay`-Zeile mit
`setCurrentActor`/`setActorDirection` gedreht. Die Gameplay-Fixture
setzt unterschiedliche Richtungen für zwei Sprecher über dieselbe
Studio-Service-Operation. 307 lokale Tests grün; der native ScummVM-Dialoglauf
`42545583240` mit WEST/EAST-Cues ist erfolgreich. Die Befehle stehen im
kompilierten `Harbor.scc`; ein isolierter Bildnachweis der Blickrichtung
bleibt ausstehend. Individuelle
Sprech-/Gesten-Costumes und Lippenanimation bleiben offen.

Die ältere Liste unten bleibt als historischer Arbeitsvorrat erhalten;
ihre ungekreuzten Kästchen sind nicht der aktuelle Capability-Nachweis.

1. **P0.1 – Binär-Roundtrip-Prüfer für ScummC-Räume; bestehende Modellgrenzen sind initial durch Regressionstests charakterisiert.**
   Chunk-Baum, Tag-/Größenprüfung, SMAP-/ZPxx-Offsets,
   OBIM/OBCD-IDs; erst wenn das bestehende Fixture valide parsebar
   ist, als erledigt markieren.
2. **P0.2 – Z-Masken im RoomAsset/JSON und ScummC-Export.**
   Masken-Indizes/Größen validieren, Bitmapquellen schreiben und
   sichtbare Verdeckung in ScummVM belegen.
3. **P0.3 – Walkbox-/BOXM-/SCAL-Modell.**
   Native Walkability, Tiefenzuordnung und Perspektivskalierung
   in einem exportierten Raum prüfen.

Abhängigkeiten und weitere Pakete:
[Lückenanalyse](scumm-v6-export-gap-analysis.md).

## Definition of Done pro Arbeitspaket

- Das betroffene SCUMM-v6-Verhalten ist benannt und quellenbasiert
  abgeglichen.
- Projektmodell, Export und Datenvalidierung sind konsistent.
- Unit-/Strukturtests laufen; bei spielrelevanten Funktionen zusätzlich
  eine **stock-ScummVM-Laufzeitprüfung** (oder ausdrücklich offener Gate).
- Keine nicht verwandten Features als abgeschlossen markieren.
- Funktionsmatrix, Status und Roadmap sind bei tatsächlicher
  Statusänderung synchronisiert.
- Änderungen sind nach Prüfung in `main` enthalten und der GitHub-Link
  ist in der Übergabe genannt.

## Einstieg für den nächsten Chat/Agenten

1. `AGENTS.md` lesen; dann Vision, **diesen Status**, Capabilities
   und Roadmap lesen.
2. `main`, laufende Branches/PRs und CI-Status prüfen.
3. Vorhandene Implementierungen und die letzten Commit-Diffs
   ansehen; weder abgeschlossene Arbeit wiederholen noch neue
   Lücken aus unvollständiger Erinnerung erfinden.
4. Das oberste unverblockierte Paket bearbeiten und Tests ausführen.
5. Nach Merge **diese Datei aktualisieren**: Ist-Stand, Nachweise,
   noch offene Risiken und nächstes Paket.

## Quellenindex

- Mechanikziel: [Adventure-Mechaniken](scumm-adventure-mechanics.md).
- Native Laufzeit: [Source-Audit](scumm-v6-source-audit.md),
  [Execution/Lifecycle](scumm-v6-execution-lifecycle.md).
- Filmische Inszenierung: [Cinematic-Audit](scumm-v6-cinematic-source-audit.md).
- Grafiken und Compiler: [Compositing-Audit](scumm-v6-compositing-compiler-audit.md),
  [Binär-Ressourcen](scumm-v6-room-resource-binary-audit.md),
  [Export-Lücken](scumm-v6-export-gap-analysis.md).
