# Adventure Studio – Produkt- und Entwicklungsroadmap

> **Aktive Steuerung, Stand 2026-11-07:**
> [Produktvision](PRODUCT_VISION.md) · [Projektstatus und nächstes Arbeitspaket](PROJECT_STATUS.md) ·
> [SCUMM-v6-Funktionsmatrix](SCUMM_V6_CAPABILITIES.md) · [Arbeitsvertrag](../AGENTS.md).
> Die nachstehenden älteren Checkboxen dokumentieren historische Teilnachweise.
> Sie bedeuten **nicht**, dass die entsprechende vollständige SCUMM-v6-Funktion
> fertig ist. Für die aktuelle Abdeckung gilt die Funktionsmatrix.

## Aktuelle Produktphasen und Abnahme

**Sprite-Sheet-Bildblock frei positionieren (CI-Abnahme bestanden):**
Ein markierter Block kann ohne Kopieren direkt an jede Zielgrenze
der ursprünglichen Abspielsequenz verschoben werden (0 vor dem ersten
Bild, N nach Bild N). Selbstziele sind wirkungslos; Bildanzahl,
Reihenfolge im Block und native COST-Sequenz bleiben konsistent.
Core-/Chromium-CI zweimal grün und stock-ScummVM-CI im zweiten
Versuch grün (PR #160, Merge `6c5d979e`, Runs `42960294165` /
`42960294415` / `42960294253`, Attempt 2). Der erste native
Versuch hatte eine nicht reproduzierte Frame-Abtastungsabweichung
in einer unveränderten Sprechprobe. Menschliche UI-Abnahme offen.
Danach: einen gewählten Bildblock mit frei wählbarer positiver
Wiederholungsanzahl gesammelt einfügen; die Anzahl vor Übernahme
sichtbar machen und native Ressourcenfolgen sicher validieren.

**Zusammenhängende Sprite-Sheet-Abspielbilder entfernen
(CI-Abnahme bestanden):** Der Nutzer wählt in der visuellen Bildleiste
Start- und einschließlich Endbild und entfernt den Block in einer
Aktion. Die verbleibende Sequenz muss weiterhin jede übernommene
Quellzelle enthalten; ansonsten erfolgt keine Änderung. Der
Chromium-Nutzerpfad prüfte die Restpixel und den nativen COST-Import
sowie JSON-Export, Core-/Chromium-CI je zweimal, stock-ScummVM-CI
einmal grün (PR #159, Merge `d1e810fa`, Runs `42959011539` /
`42959011637` / `42959011475`). Menschliche UI-Abnahme offen.
Danach: ausgewählte Bildblöcke ohne Kopie direkt an eine beliebige
Position versetzen, einschließlich Beginn und Ende der freien Folge.

**Bildblöcke frei in der Sprite-Sheet-Abspielfolge kopieren
(CI-Abnahme bestanden):** Der Editor übernimmt einen aus Start- und
Endbild gewählten zusammenhängenden Bereich als zusätzliche Kopie an
einer frei wählbaren Position. Die Originalfolge bleibt unverändert;
auch Zielpositionen innerhalb des Quellblocks sind erlaubt. Die
gemeinsame validierte Reihenfolge steuert GIF, nativen COST-Import und
JSON-Export. 334 lokale Tests laut PR, Core-/Chromium-/stock-ScummVM-CI
zweimal grün (PR #158, Merge `fea8d462`, Runs `42958027740` /
`42958026815` / `42958026806`). Menschliche UI-Abnahme offen.
Danach: zusammenhängende Bildblöcke mit Schutz der letzten Zellkopie
in einem Schritt entfernen.

**Zusammenhängende Abspielbild-Blöcke verschieben (CI-Abnahme bestanden):**
Das erste Bild wird per Bildleistenklick und das letzte per Dropdown
gewählt. Beide Blockknöpfe verschieben alle enthaltenen Abspielbilder
gemeinsam um genau einen Platz, ohne ihre Reihenfolge oder Anzahl zu
verändern. Leere bzw. ungültige Bereiche werden abgelehnt, Grenzen
bleiben stabil. 334 lokale Tests, Core-/Chromium-/stock-ScummVM-CI
grün; der Browser prüft die Blockverschiebung bis zum nativen Import
und JSON-Export (PR #156, Merge `18fa208`, Runs `42956671714` /
`42956671612` / `42956671615`). Menschliche UI-Abnahme offen.
Danach: einen ganzen Bildblock an beliebiger Stelle wiederholen.

**Einzelne Sprite-Sheet-Abspielbilder verschieben (CI-Abnahme bestanden):**
Über die anklickbare Bildleiste gewählte Positionen lassen sich ohne
Kopieren oder Löschen um einen Platz nach vorne oder hinten setzen.
Auch einzelne Wiederholungen bleiben unterscheidbar; Grenzen und
identische Nachbarn verändern die bisherige Konfiguration nicht.
334 lokale Tests, Core-/Chromium-/stock-ScummVM-CI grün; der Browser
prüfte beide Richtungen bis zum nativen Import und JSON-Export
(PR #154, Merge `eb28062`, Runs `42955411899` / `42955411892` /
`42955412129`). Menschliche UI-Abnahme offen. Danach: mehrere
aufeinanderfolgende Bilder gemeinsam als Block verschieben.

**Anklickbare Sprite-Sheet-Abspielfolge (CI-Abnahme bestanden):**
Jede tatsächliche Abspielposition erscheint mit dem Quellzellen-Bild
als eigene Miniatur; wiederholte Zellen sind dadurch sichtbar.
Ein Klick wählt die Position für das bestehende Einfügen und Entfernen.
Die Leiste folgt allen Raster- und Sequenzänderungen; ein leeres
Auswahlergebnis bleibt als leere Leiste zulässig. 334 lokale Tests,
Core-/Chromium-/stock-ScummVM-CI grün (PR #152, Merge `169e21a`,
Runs `42954277899` / `42954277816` / `42954277828`). Menschliche
UI-Abnahme offen. Danach: ein Abspielbild ohne Kopieren/Entfernen um
eine Position nach vorn oder hinten verschieben.

**Sprite-Sheet-Folge über die Oberfläche zusammenstellen (CI-Abnahme bestanden):**
Quellzelle und Position werden per Dropdown gewählt; Einfügen,
Entfernen zusätzlicher Kopien und Zurücksetzen bearbeiten die freie
Abspielsequenz. Die letzte Kopie jeder eingeschlossenen Zelle ist
geschützt. Dieselbe Folge steuert GIF, nativen COST-Import und Export.
334 lokale Tests sowie Core-/Chromium-/stock-ScummVM-CI grün;
Chromium prüfte den vollständigen Editor- und Importablauf (PR #150,
Merge `eb82f1b`, Runs `42952683287` / `42952683261` /
`42952683322`). Menschliche UI-Abnahme offen. Danach: eine
übersichtliche visuelle Bildfolge für jede Abspielposition anzeigen.

**Freie Sprite-Sheet-Abspielsequenz (CI-Abnahme bestanden):**
Ein optionales Sequenzfeld nimmt die gewünschte Folge von Rasterzellen
als Zellnummern entgegen, einschließlich nicht benachbarter Wiederholungen
wie `2,1,2`. Vorschau, GIF und nativer COST-Import nutzen denselben
validierten Ablauf und erhalten eindeutige IDs für zusätzliche Kopien.
Jede eingeschlossene Zelle muss vorkommen; ausgeschlossene, falsche
oder fehlende Zellnummern erzeugen klare Fehler. 334 lokale Tests,
Core-/Chromium-/stock-ScummVM-CI grün. Chromium überprüft Korrektur,
Frame-Pixel und native Exportreihenfolge (PR #148, Merge `36cb68a`,
Runs `42951315432` / `42951315398` / `42951315529`). Menschliche
UI-Abnahme offen. Danach: freie Folge über direkte UI-Interaktion
mit den Sheet-Zellen zusammenstellen.

**Sprite-Sheet-Zellen vor dem Import wiederholen (CI-Abnahme bestanden):**
Für jede eingeschlossene Rasterzelle lässt sich ihre direkte Abspiel-
wiederholung erhöhen oder entfernen. Editor-GIF, Zellenanzeige und
nativer COST-Stapel verwenden dieselbe expandierte Sequenz; separate
Frame-IDs verhindern Kollisionen. Bereits vorbereitete PNG-Frames
und ausgeschlossene Rasterzellen bleiben unverändert. 334 lokale
Tests und Core-/Chromium-/stock-ScummVM-CI grün; der Browser prüft
den Wiederholungsfaktor, zusammengefasste GIF-Haltezeit und native
Frame-Reihenfolge im JSON-Export (PR #146, Merge `496814a`, Runs
`42949528348` / `42949528331` / `42949528349`). Menschliche
UI-Abnahme offen. Danach: Wiederholungen an beliebigen Stellen
der geplanten Sequenz platzieren.

**Animierte Sprite-Sheet-Schnittvorschau (CI-Abnahme bestanden):**
Das Studio zeigt vor dem Hinzufügen ein wiederholbares Editor-GIF aus
genau den gewählten Rasterzellen in ihrer konfigurierten Abspielreihenfolge.
Es verwendet dieselben Pixelkoordinaten, Ränder, Abstände und Ausschlüsse
wie der native COST-Stapelimport. Die Vorschaugeschwindigkeit ist unabhängig
vom nativen Timing; eine veraltete Animation wird bei Änderungen entfernt.
334 lokale Tests, Core-/Chromium-/stock-ScummVM-CI grün. Chromium prüft
GIF-Frame-Pixel, Dauer und anschließenden Import/Export (PR #144,
Merge `648b856`, Runs `42948204879` / `42948204777` /
`42948204871`). Menschliche UI-Abnahme offen. Danach: dieselbe
Sprite-Sheet-Zelle mehrfach in einer geplanten Sequenz verwenden.

**Sprite-Sheet-Zellen vor dem Import umordnen (CI-Abnahme bestanden):**
Über eine Zellenauswahl und Vor-/Zurück-Knöpfe lässt sich die native
Abspielreihenfolge der gewählten Rasterbilder ändern. Ausgeschlossene
Zellen bleiben für die Wiederaufnahme in der Permutation erhalten;
Miniaturen zeigen die tatsächliche Abspielposition. COST-Import und
JSON-Export folgen der benutzerdefinierten Sequenz, während bereits
vorbereitete Frames unverändert bleiben. 334 lokale Tests sowie Core-,
Chromium- und stock-ScummVM-CI grün; Browser-Nachweis inklusive
vertauschter Pixel-/Frame-/Exportfolge (PR #142, Merge `8409083`,
Runs `42946980659` / `42946980608` / `42946980481`). Menschliche
UI-Abnahme offen. Danach: Abspielvorschau der gewählten Zellsequenz
vor der Übernahme.

**Auswahl einzelner Sprite-Sheet-Zellen (CI-Abnahme bestanden):**
In der PNG-Schnittvorschau lassen sich Einzelzellen durch einen Klick
ein- oder ausschließen. Grafik-Overlay, Miniaturtexte und Zählung
zeigen den aktuellen Übernahmestatus. Der COST-Stapel erhält nur die
ausgewählten Zellen in Zeilenreihenfolge, ohne die vorhandenen
vorbereiteten Uploads zu ändern. Leere Auswahl und ungültige
Zellindizes werden abgefangen. 334 lokale Tests, Core-/Chromium-/
stock-ScummVM-CI grün; Chromium prüft das Umschalten und den
exportierten Import (PR #140, Merge `61d4484`, Runs
`42944948323` / `42944948283` / `42944948354`). Menschliche
UI-Abnahme offen. Danach: Zellreihenfolge vor der Übernahme
direkt in der Vorschau festlegen.

**Visuelle Sprite-Sheet-Raster-/Schnittvorschau (CI-Abnahme bestanden):**
Vor der Übernahme zeigt der NPC-Dialogeditor das originale PNG mit
Schnittgrenzen und die daraus entstehenden Einzelbilder samt Anzahl,
Zellgröße und Reihenfolge. Die Bildvorschau wird bei jeder Änderung
der Rasterparameter aktualisiert; ungültige Raster werden konkret
angezeigt, ohne die Importauswahl zu ändern. Die exakt selben
Schnittkoordinaten gelten für den nativen COST-Import. 334 lokale
Tests, Core-/Chromium-/stock-ScummVM-CI grün; Chromium prüft die
Miniaturpixel, ungültiges und korrigiertes Raster sowie native
Import-/JSON-Exportfolge (PR #138, Merge `5f3fc04`, Runs
`42943608415` / `42943608437` / `42943608322`). Menschliche
UI-Abnahme offen. Danach: einzelne Sheet-Zellen schon vor dem
Hinzufügen ein- oder ausschließen.

**Sprite-Sheets mit Außenrändern und Zellabständen (CI-Abnahme bestanden):**
Der Studio-Import akzeptiert separate X/Y-Außenränder und X/Y-
Zellabstände als Pixelparameter. Ein exaktes Raster ohne Skalierung
und ohne Bildverlust in den ausgewählten Zellen ist Voraussetzung;
ungültige Größen werden abgelehnt, `0` erhält die bisherige Variante.
334 lokale Tests und Core-/Chromium-/stock-ScummVM-CI grün; der
Browser bestätigt 2 px Rand, 4 px Lücke, korrekte Pixel und nativen
COST-Import samt JSON-Export (PR #136, Merge `396b9e8`, Runs
`42942425436` / `42942425274` / `42942425281`). Menschliche
UI-Abnahme offen. Danach: sichtbare Raster- und Schnittvorschau
vor dem Aufteilen des Sheets.

**PNG-Sprite-Sheet als native Animationsfolge (CI-Abnahme bestanden):**
Der NPC-Dialogeditor teilt ein Raster-PNG ohne Änderung der Pixelgröße
und Transparenz zeilenweise in mehrere separate Importbilder auf und
hängt diese an die bestehende Auswahl an. Manuelle Reihenfolge,
ausgeschlossene Bilder und eigene native Frame-IDs bleiben erhalten;
Rasterfehler werden konkret abgelehnt. 334 lokale Tests, Core-CI,
Chromium-Sprite-Sheet-Pixelprobe und vierfacher COST-Import mit
JSON-Export grün. Die stock-ScummVM-Regression bestand im unveränderten
zweiten Lauf nach einer zeitabhängigen Richtungs-Sichtprobe im ersten
(PR #134, Merge `7972b25`, Runs `42940798608` / `42940798599` /
`42940798619`). Menschliche UI-Abnahme offen. Danach:
Zellabstände/Außenränder für Sprite-Sheets unterstützen.

**Alle nativen Frame-ID-Konflikte eines PNG-Stapels beheben (CI-Abnahme bestanden):**
Ein Knopf löst alle Kollisionen mit bestehenden Costume-Frames und
innerhalb der aktuellen Auswahl. Vorhandene freie IDs einschließlich
manueller Namen werden geschützt; nur Konfliktbilder bekommen
deterministische freie Suffixe. Ausgeschlossene Uploads und native
Projektressourcen bleiben unverändert, bis ein eigener atomarer Import
erfolgt. 334 lokale Tests und Core-/Chromium-/stock-ScummVM-CI grün;
Browser-Nachweis mit einem Reparaturklick, zweitem Import und JSON-Export
(PR #132, Merge `c3ee855`, Runs `42939456745` / `42939456742` /
`42939456814`). Menschliche UI-Abnahme offen. Danach: Animationsframes
aus einem PNG-Sprite-Sheet als geordnete native COST-Folge importieren.

**Freie Frame-ID für ein vorbereitetes PNG vergeben (CI-Abnahme bestanden):**
Ein Klick weist dem gewählten Uploadbild eine native ID zu, die weder
in der betroffenen Sprecher-Costume noch bei den anderen eingeschlossenen
Importbildern belegt ist. Der Algorithmus erweitert bei Bedarf den
bisherigen Namen deterministisch um `_2`, `_3` usw.; die verbindliche
atomare Importprüfung bleibt unverändert. 334 lokale Tests,
Core-/Chromium-CI und vollständige stock-ScummVM-Regression grün.
Der Browser prüft zwei aufeinanderfolgende Konfliktlösungen, erneuten
Import und exportierte native Frame-IDs (PR #130, Merge `854ca84`,
Runs `42938168129` / `42938168138` / `42938168094`). Menschliche
UI-Abnahme offen. Danach: alle Konflikte eines Stapels mit einem
Klick beheben.

**Native Frame-ID eines vorbereiteten PNGs bearbeiten (CI-Abnahme bestanden):**
Im Dialogeditor kann ein ausgewähltes Upload-PNG eine individuelle
native ID erhalten. Die Zuordnung überlebt Umsortieren, Ausschließen
und Wiederaufnehmen, ohne Bilddaten oder Projekt-JSON vor dem Import
zu ändern. Vorschau, Konfliktprüfung, GIF und nativer COST-Stapelimport
verwenden die bearbeitete ID. Ungültige IDs werden abgelehnt; Duplikate
verhindern bis zur vollständigen Auflösung den Import. 334 lokale Tests,
Core-/Chromium- und stock-ScummVM-CI grün; Browser nach einmaligem
unverändertem Replay und ScummVM im ersten Lauf bestanden (PR #128,
Merge `d96954d`, Runs `42936785066` / `42936784836` /
`42936784961`). Menschliche UI-Abnahme offen. Danach: einen freien
nativen ID-Vorschlag für Konfliktbilder direkt übernehmen können.

**Ein vorbereitetes PNG gezielt ersetzen (CI-Abnahme bestanden):**
Eine separate Einzeldatei-Auswahl ersetzt das gewählte Importbild,
ohne weitere Uploads, die editierte Reihenfolge oder Ausschlüsse
zurückzusetzen. Die native Frame-ID wird aus dem neuen Dateinamen
abgeleitet; Galerie, GIF, Vorprüfung und atomarer COST-Import lesen
denselben geänderten Stapel. 334 lokale Tests sowie Core-/Chromium-CI
grün, einschließlich Browser-Pixel-, Import- und JSON-Export-Nachweis;
stock-ScummVM-Regression im unveränderten zweiten Joblauf bestanden
(PR #126, Merge `eca2568`, Runs `42934763597` / `42934763618` /
`42934763594`). Menschliche UI-Abnahme offen. Danach: native Frame-ID einzelner vorbereiteter PNGs direkt
im Studio ändern können.

**PNG-Konflikte an einzelnen Importminiaturen anzeigen (CI-Abnahme bestanden):**
Bei der vorbereiteten 1..N-PNG-Folge werden native Frameimporte
sequenziell auf einer nur temporären Projektkopie geprüft. Die Galerie
kennzeichnet konfliktbehaftete Positionen und zeigt den Fehler je
Datei darunter; valide Frames und bestehende Reihenfolge bleiben
sichtbar. Die vollständige Importfreigabe nutzt weiter die atomare
Gesamtprüfung. 334 lokale Tests und alle drei CI-Workflows bestanden;
Chromium-Warnkarten, Fehlerliste, Import/Export und native stock-ScummVM-
Regression belegt (PR #124, Merge `a3e1281`, Runs `42933208866` /
`42933208843` / `42933208842`). Menschliche UI-Abnahme offen.
Danach: einzelne PNG-Datei in der Upload-Reihenfolge ersetzen.

**Vorabprüfung der nativen PNG-Importfähigkeit (CI-Abnahme bestanden):**
Die Studio-Oberfläche simuliert den atomaren Stapelimport mit aktueller
Dialogzeile, Richtung, Ziel und PNG-Reihenfolge ohne Projektänderung.
Konkrete Fehler werden vor dem Klick angezeigt und der Importknopf
bleibt in diesem Zustand deaktiviert. Gleiche Prüfung für 0/1/N-Bilder,
Dateiformat, Frame-ID- und Palettenkonflikte. 334 lokale Tests und
Core-/Chromium-CI grün; realer Import/Export und anschließende
Blockierung belegter IDs im Chromium bestätigt. Native ScummVM-
Regression im unveränderten vollständigen Job-Replay grün (erster
Lauf mit Richtungs-Frame-Abtastungsfehler; PR #122, Merge `3d94a6d`,
Runs `42930996980` / `42930997132` / `42930997256`). Menschliche
UI-Abnahme offen. Anschließend: Fehler an konkreten
Miniaturkarten markieren.

**Miniaturklick als direkte Frame-Navigation (CI-Abnahme bestanden):**
Ein beliebiges Bild der vorbereiteten Importfolge lässt sich durch
Klick auf seine Galerie-Karte direkt auswählen. Die bestehende
Einzelbildansicht zeigt die echten PNG-Pixel, Position und geplante
native ID. Keine Änderung am Importformat; die Auswahl bleibt an
die aktuellen Galerie-/Dropdown-Einträge gebunden. 334 lokale Tests
und Core-/Chromium-CI grün, einschließlich echtem Pixel- und
Export/Reimport-Nachweis. Die bestehende native Regression war auf dem
ersten PR-Commit grün, danach nur UI-Ereignisbindung und Browsertest
angepasst (PR #120, Merge `6e9db6d`, Runs `42929768607` /
`42929768636` / `42927794343`). Menschliche UI-Abnahme offen.
Anschließend: präventive Importfehleranzeige für die
vorbereitete Sequenz.

**Einzelbild-Navigation in der noch nicht importierten PNG-Folge (CI-Abnahme bestanden):**
Autorinnen und Autoren können jedes gewählte Frame mit Dateipixeln,
Position und nativer Frame-ID ansehen und schrittweise vor/zurück wechseln.
Die Auswahl bleibt dieselbe wie für den atomaren Import; bei leerer
Auswahl erscheint kein Bild. 334 lokale Tests und alle drei CI-Workflows
grün; der Chromium-Test prüft echte Einzelbildpixel, die native
ScummVM-Regression blieb grün (PR #118, Merge `cff209c`, Runs
`42926566873` / `42926566651` / `42926566581`). Menschliche
UI-Abnahme offen. Danach: Klick auf eine Miniatur als direkte Navigation.

**Abspielbare Vorabvorschau für PNG-Stapelimport (CI-Abnahme bestanden):**
Die sichtbare, noch ungespeicherte Auswahl wird als Editor-GIF mit
einstellbarer Bilddauer abgespielt. Die Reihenfolge stammt aus derselben
validierten Auswahl wie der atomare native Import. Ändert sich die Auswahl,
verschwindet die bisherige Animation. 334 lokale Tests und drei
CI-Workflows bestanden: Chromium-Bedienpfad sowie bestehende native
ScummVM-Dialogregression (PR #117, Merge `630a28d`, Runs
`42925614655` / `42925614671` / `42925614660`). Menschliche UI-Abnahme
offen. Die GIF-Zeit ist keine native COST-Zeit.
Danach: Frame-Navigation in der vorbereiteten Vorschau.

**PNG-Miniaturvorschau der vorbereiteten nativen Dialog-Importfolge (2026-11-11, native Abnahme bestanden):**
Die noch nicht importierten hochgeladenen Bilder erscheinen unter dem
Textplan als echte farbige Miniaturkarten mit nativen Frame-IDs.
Dateiauswahl, Umordnen, Entfernen und Wiederaufnehmen zeigen stets
dieselbe Auswahl/Reihenfolge, die beim Klick als native COST-Folge
gespeichert wird. Auch 0 Bilder ergibt eine leere Galerie. 334 lokale
Tests und sechs finale CI-Checks grün. Echte Chromium-Pixelprüfungen
der Farben und Reihenfolge nach Umordnen/Ausschließen/Wiederaufnehmen
und JSON-Export/Reimport zweimal bestanden; bestehende zweiframige
native Abschlussanimation mit Standzustand in zwei stock-ScummVM-Läufen
bestanden (PR #115, Merge `6e495d5`, Chromium Jobs `130201926707` /
`130201843676`, native Jobs `130201843845` / `130203561023`).
Ein früher fehlgeschlagener unveränderter Startbild-Sichttest bestand im
unveränderten Replay. Menschliche UI-Abnahme offen.
Anschließend: abspielbare Vorabvorschau der ausgewählten PNG-Sequenz.

**Ausgeschlossene Upload-PNGs ohne Neu-Upload reaktivieren (2026-11-11, native Abnahme bestanden):**
Das Dropdown listet die noch hochgeladenen, aber ausgeschlossenen Bilder.
Ein Klick hängt das gewählte Bild ans Ende der aktuellen Importauswahl.
Es kann anschließend sortiert oder wieder entfernt werden; auch 0 → 1
funktioniert. Validierte Reihenfolge und native COST-Ausgabe behalten
ihre bestehenden Grenzen. 334 lokale Tests und sechs finale CI-Checks
grün. Chromium-Entfernen/Wiederaufnehmen mit anschließender Auswahländerung
und Export/Reimport zweimal nachgewiesen; bestehende native zweiframige
Abschlussanimation mit Standzustand im stock ScummVM zweimal bestanden
(PR #113, Merge `36187ac`, Chromium `130193752594` / `130193639385`,
native Jobs `130193752872` / `130196817977`). Ein vorher fehlgeschlagener
unveränderter Tür-Frame-Sichttest wurde ohne Prüfungsänderung erfolgreich
wiederholt. Menschliche UI-Abnahme offen.
Anschließend: Miniaturvorschau für die vorbereitete PNG-Folge.

**Einzelne Upload-PNGs vor dem nativen Dialog-Stapelimport ausschließen (2026-11-10, native Abnahme bestanden):**
Ein PNG wird in der Importauswahl gewählt und mit einem Klick ausgeschlossen.
Die übrigen hochgeladenen Bilder bleiben in der bisherigen Sortierung
erhalten und lassen sich ohne neue Dateiauswahl atomar als native Sprech-
oder Abschlussfolge importieren. Bei 0 verbleibenden Bildern wird nichts
geschrieben; doppelte oder ungültige Referenzen werden abgelehnt.
334 lokale Tests und fünf finale CI-Checks grün. Zwei Chromium-Läufe
bestätigen das Ausschließen des dritten Uploads nach dem Umordnen und
den JSON-Export/Reimport der zwei gewünschten Frames. Der bestehende
native Zweiframe-Abschlussdialog mit Standpose bestand im stock ScummVM
(PR #111, Merge `33c28f5`, Chromium Jobs `130188492998` /
`130188465475`, native Job `130188494313`). Menschliche Bedienabnahme offen.
Anschließend: ausgeschlossene Uploads ohne erneute Dateiauswahl reaktivieren.

**Ausgewählte PNG-Dateien vor dem nativen Dialog-Stapelimport umsortieren (2026-11-10, native Abnahme bestanden):**
Die Autorin oder der Autor wählt ein Upload-Frame und verschiebt es per
Schaltfläche nach oben/unten. Das Auswahlfeld und die Vorschau zeigen die
Reihenfolge, die anschließend atomar als native Sprech- oder Abschlussfolge
importiert wird. Frische Dateiauswahl setzt die alte Sortierung zurück;
ein nicht zur Dateiauswahl passender Sortierzustand wird abgelehnt.
334 lokale Python-Tests und sechs CI-Checks grün. Chromium-Umsortierung,
Vorschau und Export/Reimport in zwei UI-Läufen nachgewiesen; bestehende
native Zweiframe-Abschlussfolge samt Standzustand in stock ScummVM in
zwei Läufen bestanden (PR #109, Merge `e974946`, Chromium Jobs
`130181832614` / `130181718511`, native Jobs `130181832477` /
`130181719158`). Menschliche Bedienabnahme offen.
Anschließend: einzelne Upload-Dateien vor dem Import entfernen.

**Mehrere PNG-Dateien als eine native Dialogfolge importieren (2026-11-10, native Abnahme bestanden):**
Der Dialogeditor nimmt 1..N neue PNG-Dateien in Auswahlreihenfolge an,
zeigt die native Frame-ID je Datei vor dem Speichern und importiert sie
in einer einzigen validierten Modelloperation an eine Sprech- oder
Abschlussfolge derselben Zeile/Richtung. Ungültiger Dateityp, doppelte
oder bereits belegte ID, Palette und Native-Exporter-Grenzen führen
zu einem vollständigen Abbruch ohne neue gespeicherte Frames. 334
lokale Tests und fünf aktuelle CI-Checks grün. Chromium-Mehrfachupload
samt geordneter Frame-ID-Vorschau und Export/Reimport sowie nativer
stock-ScummVM-Nachweis einer zweiframigen Abschlussfolge mit Standpose
bestanden (PR #107, Merge `a685897`, native Job `130175052358`,
Browser `130175056189` / `130175014763`). Menschliche UI-Abnahme offen.
Danach: grafisches Umordnen der Upload-Auswahl.

**Geteilte Sprecher-Costume im NPC-Dialogeditor vereinzeln (2026-11-10, native Abnahme bestanden):**
Ist eine Costume an mehrere Actors gebunden, legt der Autor im
Dialogeditor eine private vollständige Kopie für die gewählte
Sprecherfigur an. Der UI-Dialog benennt vorher Quelle, neues Ziel und
andere betroffene Figuren. Original-COST-Palette/Frames/Animationen
bleiben erhalten, andere Actors unverändert, sämtliche Dialogzeilen
des gewählten Actors verwenden seine neue Costume-Referenz. Danach
können PNG-Sprech-/Abschlussframes ohne globale Nebeneffekte importiert
werden. 333 lokale Tests und sechs CI-Checks grün; Chromium-Folgeklickweg
samt Export/Reimport und nativer ScummVM-Dialogbeleg auf der kopierten
Costume bestanden (PR #105, Merge `1595e1c`, native Jobs
`130167489043` / `130167388424`, Browser `130167488068` /
`130167388133`). Menschliche UI-Abnahme offen.
Anschließend: Mehrere PNGs als geordnete Folge auf einmal importieren.

**PNG-Bilddatei direkt für Dialog-PNG-Folgen importieren (2026-11-10, native Abnahme bestanden):**
Ein Autor wählt im Dialogeditor eine neue PNG-Datei, eine native Frame-ID
und den Zielkanal Sprech- oder Abschlussfolge. Die Datei wird auf die
bereits zugewiesene Costume importiert und in einem gültigen Schritt
an die gewählte Zeile/Richtung angehängt. Bestehende Farbpalette und
andere Animationen bleiben geschützt; geteilte Costumes und native
Frame-/Palettefehler werden sichtbar abgelehnt, ohne den Projektstand
zu verändern. 332 lokale Tests und fünf aktuelle CI-Checks grün.
Echte Chromium-Dateiupload-Abnahme und stock-ScummVM-Farbframe auf dem
neuen Pfad bestanden (PR #103, Merge `1cc99f7`, native Jobs
`130161049750` / `130161082960`, Chromium `130161083496`).
Eine initial schwankende Echtzeit-Bildabtastung wurde als solcher
Testflüchtigkeitsfall behandelt; die finale Probe spielt bei Bedarf
das gesamte native Szenario einmal erneut ab, ohne das Gate zu senken.
Anschließend: Geteilte Actor-Costumes im Dialogeditor sicher vereinzeln.

**Direkte Abschluss-PNG-Folge im NPC-Dialogeditor (2026-11-10, native Abnahme bestanden):**
Ein Autor kann aus bereits importierten PNG-Costume-Frames eine eigene
zeilenspezifische native Abschlussanimation für eine Blickrichtung
gestalten: anhängen, umordnen, entfernen, GIF-Vorschau. Eigener stabiler
COST-Slot, native Tick-Anbindung nach `waitForMessage`, Erhalt aller
anderen Richtungen/Zeilen und älterer JSON-Projekte. 331 lokale Tests
und sechs CI-Checks grün. Chromium-Export/Reimport und stock-ScummVM-
Frameprobe des neuen PNG-Authoring-Pfads bestanden (PR #101,
Merge `8557ea0`, Jobs `130151091545` und `130151090189`).
Menschliche Bedienabnahme offen.
Anschließend: PNG-Bilddateien direkt im Dialogeditor importieren.

**Optionale native Abschlussgeste pro NPC-Zeile (2026-11-10, native Abnahme bestanden):**
Nach `waitForMessage()` kann ein eigener vorhandener indizierter
Costume-Kanal für positive native Ticks abgespielt werden. Erst danach
kehrt der Actor gegebenenfalls zur Standpose zurück. Der Dialogeditor
speichert, entfernt und lädt die Abschlusszuweisung; ältere Dokumente
bleiben ohne Abschlussgeste unverändert. Modell-/JSON-/Skript-Test,
Chromium-Authoring samt Export/Reimport und der stock-ScummVM-Nachweis
des magentafarbenen Abschlussframes zwischen West- und Ost-Sprechzeile
mit Standpose sind bestanden (Run `42904734152`, Job `130139641706`,
PR #99, Merge `ead868b`). Menschliche UI-Abnahme offen.
Danach folgt die direkte PNG-Authoring-Funktion für eine eigene
Abschlussfolge pro Dialogzeile und Richtung.

**Native Sprechphasen pro NPC-Zeile (2026-11-10, native Abnahme bestanden):**
Vorlauf bis zur Sprechanimation und Mindestlaufzeit bis zum
`waitForMessage` sind jetzt als native ganze Skript-Ticks pro Zeile
authorbar. Das bestehende `actorSay`/`animateActor`-/Stand-Verhalten
bleibt erhalten, und alte Projekte verwenden weiterhin 1/60 Ticks.
Modell-/Exporter-/Kompatibilitätstest, echter Gradio-Chromium-Ablauf
(zwei Zeilen, Export/Reimport) und der Stock-ScummVM-Dialog mit 12/90-
Tick-West-Geste sowie unveränderter 1/60-Tick-Ost-Geste sind bestanden
(CI `42901243477`, Job `130127449346`, PR #97, Merge `208e619`).
Kein Anspruch auf exakten Wort-Lippensync; menschliche UI-Abnahme offen.
Danach: eigene native Abschlussgeste pro Dialogzeile.

**Grafische NPC-Sprech-Timeline pro Zeile/Richtung (2026-11-10, Abnahme bestanden):**
Der Dialogeditor zeigt die tatsächlich zugeordnete native PNG-Framefolge
als klickbare Karten. Ein Frame lässt sich anhängen, verschieben und
entfernen, ohne den stabilen COST-Slot, andere Richtungen, andere Zeilen
oder globale Costume-Animationen zu verändern. Eine GIF-Vorschau nutzt
einen frei gewählten Editor-Takt; diese Zeit ist keine SCUMM-v6-Semantik.
Modell-/GIF-Test, Chromium-Authoring samt Export/Reimport und die
unveränderten nativen ScummVM-Regressionen sind bestanden (CI
`42898953018`, PR #95, Merge `3410035`). Menschliche UI-Abnahme offen.
Danach: fachlich steuerbare Sprechphasen im nativen Dialogablauf.

**Richtungsspezifische animierte NPC-Zeilen (2026-11-10, native Abnahme bestanden):**
Ein einzelner Dialog-Cue hält weiterhin seinen eigenen nativen COST-Slot,
kann darin aber je Nord/Ost/Süd/West eine unterschiedliche 1..N-
Framefolge verwenden. Der Studio-Dialogeditor speichert nur den gewählten
Richtungskanal; andere Richtungen und Zeilen bleiben erhalten. Der
vorhandene zeilenspezifische Cue wird nicht neu nummeriert. Lokale
JSON-/COST-/Skript-Verträge, der echte Chromium-Authoring-Pfad und
ein stock-ScummVM-Dialog mit westlicher rot/grüner und östlicher
blau/gelber Animation sind bestanden (CI `42895287701`, PR #93,
Merge `270be816`). Menschliche Bedienabnahme ist offen. Danach folgt die
grafische Mehrframe-Timeline je Dialogzeile und Richtung.

**Unabhängige Mehrframe-Folgen pro NPC-Zeile (2026-11-10, native Abnahme bestanden):**
Der Dialogeditor speichert 1..N importierte Frame-IDs als eigene native
COST-Animation pro Zeile, mit einem stabilen Animationsnamen/-slot und
vorhandenen `animateActor`-/`actorSay`-Bindungen. Mehrere Zeilen eines
Actors können unterschiedliche Folgen haben, ohne die globale
`gesture`-/`talk_start`-Animation oder andere Zeilen zu verändern.
Re-Edit/JSON-Roundtrip und Exportquellen sind geprüft; echter Gradio-
Chromium-Klickweg und stock-ScummVM-Klicktest sind bestanden. Zwei
unterschiedliche Framepaare derselben Figur erscheinen in zwei
aufeinanderfolgenden Zeilen mit Rückkehr zur Standpose (CI
`42890566896`, Job `130090292878`, Artefakt
`native-v6-studio-independent-speaking-lines`; Merge `482375e`).
Danach: Richtungsspezifische Sequenzen pro Zeile.

**Native animierte Sprechsequenz (2026-11-10, native Abnahme bestanden):** Der Autor
legt im Costume-Editor je N/E/S/W eine Folge vorhandener PNG-Frames fest.
Der bestehende Dialog-Cue verwendet die native COST-`gesture`-Animation;
die Frames folgen während der NPC-Zeile der Interpreter-Abspielrate.
Gespeichert werden die Frames als wiederholte `gesture`- und `talk_start`-
Folge ohne Änderung an `stand`, `talk_stop` oder den anderen Richtungen.
Lokale Modell-, Exportquellen- und JSON-Regression grün. Eigener
stock-ScummVM-Test mit zwei sichtbaren, aufeinanderfolgenden Farbframes
**innerhalb einer Dialogzeile** und anschließend sechs Standframes
bestanden (CI `42886572422`, Job `130076341678`, Artefakt
`native-v6-studio-speaking-sequence`; Merge `634afb6`). Danach:
zeilenspezifische Sequenzen mehrerer Dialogzeilen.

**Vier native Richtungs-Sprechposen (2026-11-10, native Abnahme bestanden):**
Eine regulär exportierte vierteilige Actor-Sprechkette dreht den Actor vor
jeder Zeile auf N/E/S/W und verwendet pro Costume-Richtung einen anderen
Frame. Die native ScummVM-Bildprobe verlangt die Farbfolge in Reihenfolge
und sechs aufeinanderfolgende Standframes. Lokaler Source-/Modellnachweis
und lokale Regressionstests grün. Die erste native Sichtprobe deckte eine
falsche alte ScummC-Richtungs-ID bei `setActorDirection` auf; der Export
verwendet jetzt die von ScummVM erwarteten Winkel. Die native Wiederholung
zeigt **N/E/S/W in Reihenfolge mit je 256 Pose-Pixeln**, anschließend sechs
stabile Standframes ohne Pose-Pixel (CI-Job `130066624232`, Artefakt
`native-v6-studio-dialogue-four-facing`). **Noch offen:** Gesamt-CI,
menschliche UI-Abnahme und zeitgesteuerter Lippensync.

**Richtungsspezifische PNG-Sprechposen authoren (2026-11-10, Implementierung):**
Der Costume-Editor wählt je N/E/S/W einen importierten Frame für die native
Sprechanimation. Änderungen betreffen nur die gewählte Richtung von `gesture`
und `talk_start`; Standpose und andere Richtungen bleiben bestehen. Der
persistierte Frame wird bei erneuter Auswahl der Richtung angezeigt.
Modell-/COST-Regression und 322 lokale Tests grün; der Chromium-Browser-
Klicktest für die persistierte Richtungswahl und den Reimport ist auf
Commit `bf35cc2` grün. **Offen:** native Gameplay-Sichtprobe
und native Sichtprobe für alle vier Blickrichtungen. **Nächstes:** diese
vier Posen im unveränderten ScummVM durch Actor-Drehung und Dialog prüfen.

**Sprechposen nach vier Blickrichtungen im Dialogeditor (2026-11-10):**
Nord/Ost/Süd/West lassen sich für die gewählte native Actor-Animation
einzeln ansehen. Das Bild stammt aus dem tatsächlichen Richtungskanal
der Costume (nicht aus einer automatisch gespiegelten Kopie).
Native Mehrframe- und Kommandoanimationen werden im Einzelbildmodus
klar als nicht darstellbar gekennzeichnet. Getestet: Unterschiedliche
Frames pro Richtung im PNG-/COST-Modell sowie
Gradio-Chromium-Richtungswahl mit Pixel- und Beschriftungsprüfung.
Die Stand-/Sprech-Bytecodes bleiben unverändert.
**Offen:** native Spielprüfung mit vier bewusst unterschiedlichen
Richtungs-Frames, menschliche UI-Abnahme und vollständiger Lippensync.
**Nächstes:** Editor-Zuweisung einer eigenen PNG-Pose je Actor-Richtung
mit realem Interpreter-Nachweis nach Blickrichtungswechsel.

**Native NPC-Sprechpose direkt im Dialogeditor anzeigen (2026-11-10):**
Das ausgewählte PNG wird jetzt aus den originalen Costume-Frame-Indizes
und der nativen Palette als statisches Bild gerendert. Die Bildvorschau
reagiert auf gespeicherte Dialog-Cues, Zeilenwechsel, frei gewählte Frames
vor dem Speichern und nach dem Reimport. Ein Echtbrowser-Test verlangt
rot/grün unterscheidbare Costume-Pixel und kontrolliert die bestehende
JSON-Export-/Reimport-Folge. **Abgenommen:** automatisierter Gradio-
Chromium-Klicktest und Pillow-Modelltest auf Code-Commit `f940d93`;
menschliche UI-Abnahme weiterhin offen. **Nächstes:** präzisere
richtungsabhängige Auswahl/Ansicht, ohne native Engine-Semantik zu erfinden.

**Echter Gradio-Browser-Klickweg für NPC-PNG-Sprechposen (2026-11-10):**
Der automatisierte Chromium-Test lädt eine bestehende Zwei-Posen-Projektdatei,
wählt zwei Dialogzeilen, ändert die PNG-Zuweisung, exportiert die validierte
Projektdatei und importiert sie erneut. Screenshots, Ergebnisbericht und
Projekt-JSON sind CI-Artefakte; der reale Browserlauf ist grün. Zusätzlich
zu den bisherigen Gradio-HTTP- und Unit-Gates. Das ist eine automatisierte
Browserabnahme, keine protokollierte menschliche Abnahme.
**Als nächstes:** direkte Bildvorschau der ausgewählten Sprecher-PNG-Pose
neben der Dialogzeile mit konsistenter Aktualisierung beim Zeilenwechsel.

**Gespeicherte PNG-Sprechpose im Dialogeditor vorauswählen (2026-11-10):**
Die Zeilenauswahl bleibt bei Projektänderungen erhalten. Nach einem
Speichern bzw. erneutem Öffnen werden Animations-Cue, Rücksetzoption
und eindeutig zugeordneter PNG-Frame aus dem Modell angezeigt.
Mehrframe- oder blickrichtungsabhängige Animationen bleiben im PNG-Feld
bewusst ohne Vorauswahl; der native Animationseditor zeigt den Cue weiter.
Roundtrip- und Editiertests implementiert, Gradio-HTTP-Smoke ausstehend.
**Nächster UI-Abnahmeschritt:** Im echten Browser zwei PNG-Posen zwischen
Dialogzeilen wechseln, speichern, neu laden und die vorausgewählten
Frames kontrollieren.

**Mehrere Sprechposen derselben Figur (2026-11-10, PR #81):**
Importierte PNG-Frames lassen sich jetzt unabhängig an Dialogzeilen einer
Figur binden. Weitere native Costume-Slots ab 28 bewahren vorhandene
`talk_start`-/`gesture`-Posen. Die neue Zwei-Posen-Abnahme in stock
ScummVM hat den sichtbaren rot/grün-Wechsel und die Rückkehr zur Standpose
bestanden. **Offen:** Gesamt-CI-Abschluss und interaktiver Gradio-Klickweg.
Danach: beim erneuten Öffnen einer Dialogzeile deren zugeordnete PNG-Pose
sichtbar vorauswählen und diesen Bedienablauf manuell abnehmen.

**PNG-Sprechpose direkt aus der Dialogzeile (2026-11-09):** Die native
Sprecherzeile bietet die Frames ihrer eigenen Costume an; ein Klick
übernimmt Frame, COST-Talk-Slots und Dialog-Geste. Geteilte Costumes
werden vor unbeabsichtigtem Überschreiben geschützt. 319 lokale Tests
grün; CI und interaktive Gradio-Abnahme offen. Darauf folgt
zeilenspezifische Mehrfach-Sprechpose ohne globale Talk-Start-Kollision.

**Neuer nativer Gesten-/Standpose-Nachweis (2026-11-09):** Eine
Studio-authored Costume zeigt in stock ScummVM die rote Sprechpose
(`256` Pixel) und danach eine stabile Standpose (`0` Pixel über sechs
aufeinanderfolgende Frames); der native Schritt ist auf `2dc5271`
grün. Der reguläre PNG-Ein-Klick-Pfad schreibt dafür die reservierten
`talk_start`-/`talk_stop`-Slots 16/20 und den Gesten-Cue 24. Noch offen:
aktuelle Gesamt-CI und durchgeklickte Gradio-Abnahme (PR #78).


**Sprechpose mit einem Klick aus PNG-Frame (2026-11-09, Implementierung):**
Im nativen Costume-Editor wird ein vorhandenes PNG-Frame als dauerhaft
sichtbare `gesture`-Pose für alle vier Actor-Richtungen gesetzt. Die
Standpose bleibt erhalten, der bestehende Dialog-Cue verwendet die
indizierte Animation. 318 lokale Tests grün (PNG-zu-COST und
Dialog-Quellgenerierung), native ScummVM-Bildprobe und interaktive
Gradio-Abnahme noch ausstehend (PR #78).

**Blocker im nativen Sprecher-Rendering:** Der vollständige Feature-Branch
und die GitHub-Actions-Workflows wurden wiederhergestellt. Die SCUMM-
Compiler- und Dialogtextprüfungen laufen, aber die Sprecher-Costume
selbst ist in den Screenshots nicht nachweisbar. COST-Standindex 12 und
native Talk-Frame-Bindung sind implementiert; vor der Gestenprüfung muss
die tatsächliche Sichtbarkeit der Sprecher-Actors nachgewiesen werden.

**Native Actor-Sichtbarkeit nachgewiesen, Gestenstart offen:** In der
kamerafolgenden Testszene steht der Witness sichtbar separat von Ego
(`256` cyanfarbene Costume-Pixel). Die rote Animation 24 ist ebenfalls
nativ darstellbar, wenn sie beim Raumeintritt startet (`256` rote Pixel).
Während `actorSay` lässt sich dieselbe Geste bislang weder unmittelbar
noch nach einem nativen Tick sichtbar starten. Nächstes vertikales Gate:
Sprecher-Animation über den nativen Talk-Start-/Talk-Script-Mechanismus
statt durch einen wirkungslosen direkten Animationsimpuls auslösen.


**Sprechanimationen kontrolliert beenden (2026-11-09, Implementierung):**
Optionale Standpose-Rücksetzung je Dialog-Cue im nativen Studio, nach
`waitForMessage` und ggf. VOC-Stopp mit nativer `stand`-Animation 12
und Actor-Talk-Frame-Bindung. Sprecherwechsel verwenden den
jeweiligen Actor, ältere Cue-JSONs bleiben unverändert. 316 lokale Tests
grün; die erste native Probe belegte, dass `setActorStanding` allein das
Bild nicht zurücksetzt. Die korrigierte ScummVM-Klickprobe muss den
animierten Frame und dessen bleibendes Ende über mehrere Ticks bestätigen.
Danach: Gradio-End-to-End und echte PNG-Costume-Sprecherwechsel.

**Sprechgesten je Dialogzeile (2026-11-09, Implementierung):** Native
Dialogzeilen mit Actor-Bindung können im Studio eine bereits authorierte
indizierte Costume-Animation auswählen. Gemeinsame JSON-Persistenz,
Validierung der Sprecher-/Animations-/Blickrichtungsbindung und
`animateActor` direkt nach `actorSay` im regulären ScummC-Pfad; 314 lokale Tests
grün. Reale stock-ScummVM-Klick-/Sichtabnahme der authored Zwei-Frame-Geste
bestanden (CI `42550554974`, 14 rote Gestenpixel und zwei verschiedene
Sprechertexte). D03 bleibt Teilfähigkeit; als nächstes interaktiver
Gradio-Pfad und definierter Animations-Endzustand/Sprecherwechsel.

**Native Sprecher-Costumes aus PNG (2026-11-09, Implementierung):** Bereits
erzeugte Story-Sprecher-Actors können im gemeinsamen Studio eine vom Autor
importierte native Costume erhalten. Die Bindung bleibt in der versionierten
Projektdatei und im COST-Export erhalten. 312 lokale Tests grün;
interaktive Gradio-/stock-ScummVM-Sichtabnahme offen. Nächster Schritt:
eine konkrete Costume-Animation je gesprochener Dialogzeile authoren.

**Dialogantworten editieren (2026-11-09, Implementierung):** Der Studio-
Dialogeditor kann vorhandene Antworttexte und Folgeziele bei stabilen IDs
ändern. Der Story-Solver schützt vor verwaisten Knoten; der native
SCUMM-Quellpfad nutzt den geänderten Graphen. 309 lokale Tests grün;
interaktive UI-/ScummVM-Abnahme dieser Operation bleibt offen. Nächstes
vertikales Paket: autorierte sichtbare Costume-Animation pro Sprecherzeile.

1. **P1 – Vollständiger nativer SCUMM-v6-Generator (jetzt):**
   Raumgrafiken, Masken, Walkboxen, Objekte, Actors/Costumes, Animation,
   zeitabhängige Aktionen, Rätsel, Kamera, Cutscenes, Dialog, Audio und
   Persistenz werden als native Ressourcen/Skripte exportiert.
   Abnahme: pro erforderlicher Mechanik ein Compiler-/Format-Gate und
   ein konkreter ScummVM-Gameplay-Nachweis.
2. **P2 – Durchgängiger visueller Adventure-Editor:**
   Alle unterstützten P1-Daten aus dem Projektmodell authorbar.
3. **P3 – Cineastischer Shot-/Cutscene-Editor:**
   Filmbegriffe auf native Kamera-/Raum-/Costume-/Script-Bausteine abgebildet.
4. **P4 – KI-gestützte Spieleentwicklung:**
   Validierte, nachvollziehbare Änderungen statt unkontrolliertem Code.
5. **P5 – Produktreife:** Distribution, Bedienbarkeit, Stabilität, Qualität.

### Verbindlicher SCUMM-v6-Funktionsvertrag

**Aktuelles vertikales Paket (2026-11-08):** Gemeinsamer nativer
Sprachzustand für lokalisierten Story-Text und VOC-Zeilen; ein geprüftes
Story-Sprachpaket wird beim Export um die Unicode-Untertitel ergänzt.
Nachweis: integrierter Exporttest und deutschsprachiger Story-Text mit VOC-
Untertitel im selben stock-ScummVM-Bild plus PCM-Escape (CI `42531065406`).
Weitere Sprechrollen- und Dialogknoten-
Synchronisierung bleibt offen (D03/D04/U03).

**Aktuelles NPC-Dialog-VOC-Paket (2026-11-08):** Studio-Import von VOCs
auf Gesprächs-Öffnungs- und Antwortzeilen mit Sprachvariante,
versioniertem Quelltext-Schutz und nativer `GameLanguage`-Ausgabe.
Gezielte Modell-/SCUMM-Tests und echte NPC-Klick-/Antwort-/Audioprobe in
stock ScummVM grün (CI `42533774527`). Vollständige zyklische
Gesprächsgraphen, mehrere Sprecher und Actor-Lippensync bleiben offen.

**Mehrstufige Dialoggraphen (2026-11-09):** Der Studio-Editor kann
aus vorhandenen Gesprächsknoten neue Antwortzweige und Rückverbindungen
authoren. Der native Compiler projiziert Wahlstufen auf getrennte,
zustandsabhängige SCUMM-Objekte; alte einstufige Projekte bleiben gültig.
Die native stock-ScummVM-Abnahme bestätigt zwei Auswahlebenen, den Rückweg
und den endgültigen Gesprächsabschluss durch echte Klicks (CI
`42536777733`, `native-v6-studio-nested-dialogue`). Eine echte klassische
SCUMM-Gesprächsmenü-UI und Sprecherwechsel bleiben weitere Produktpakete.

**Sprecher-Authoring (2026-11-09, Teilstand):** Der Story-Editor ordnet
Sprechzeilen und neue Antwortknoten jetzt einer Figur derselben Szene zu.
Der Compiler erzeugt jetzt SCUMM-Actors mit eigenem Costume und `actorSay`
für die zugeordneten Sprechzeilen. In stock ScummVM ist die zweite,
vom Antworttext verschiedene Sprecherzeile nachgewiesen (CI `42540762070`).
Lineare Sprechketten ohne Antwortauswahl sind inzwischen ebenfalls im nativen
`actorSay`-Compiler unterstützt; ihre ScummVM-Abnahme läuft noch. Die
Kopplung von Costume-/Lippenanimation an Sprachaufnahmen bleibt der nächste
D03-Teilschritt.

**Lineares Dialog-Authoring (2026-11-09):** Aufeinanderfolgende Sprechzeilen
lassen sich nun direkt im Studio an eine abschließende Gesprächszeile anhängen,
einschließlich optionalem Sprecherwechsel. Das bestehende native
Zwei-Sprecher-Fixture wird dafür um einen über die produktive Editoroperation
hinzugefügten Folgesatz erweitert. 304 lokale Tests grün; native
ScummVM-Abnahme der ersten beiden Sprecherzeilen mit angehängtem Folgesatz
erfolgreich (CI `42543308699`). Sichtnachweis der dritten Zeile separat offen.

**Actor-Blickrichtung während Dialogen (2026-11-09):** Der Studio-Editor
speichert optionale N/E/S/W-Blickrichtungs-Cues pro Sprechzeile. Lineare und
verzweigte Dialoge setzen den sprechenden Actor vor der Ausgabe nativ über
`setActorDirection`, während ältere Story-v4-Dokumente unverändert bleiben.
307 lokale Tests grün; nativer Dialoglauf mit WEST/EAST-Cues in stock
ScummVM erfolgreich (CI `42545583240`). Isolierte Sichtprüfung offen.

Die [Referenzbibliothek](scumm-v6-reference/README.md) ist der dauerhafte
technische Zugang zu ScummC-/ScummVM-Primitiven und
[Abnahmeszenarien](scumm-v6-reference/SCENARIOS.md). Die
[Funktionsmatrix](SCUMM_V6_CAPABILITIES.md) bleibt **einziger**
64-ID-Katalog für Scope und I/T/V-Status. Der
[Quellenindex](scumm-v6-reference/capability_sources.json) wird gegen
die Matrix getestet; bereits analysierte Primitive werden wiederverwendet.
Die nächsten vertikalen Pakete bleiben P0.1–P0.3; wir ersetzen sie nicht
durch ein großes vorgeschaltetes Konformitätsspiel.

### Architektur- und Regression-Gates

[Architekturaudit](architecture-audit.md) ·
[Architekturverträge](architecture-contracts.md) ·
[ADR-0001](adr/0001-domain-and-export-boundaries.md) ·
[ADR-0002](adr/0002-limits-evidence-and-compatibility.md).

- [x] Bestand auf künstliche Demo-/Adapter-Limits geprüft; A0-Befunde
      dokumentiert; feste Story-/JSON-Koordinatenbegrenzungen entfernt.
- [x] Grenzfall-Regressionen für 0/1/2/N Dekorationen, Platzierungen,
      JSON-Sammlungen >128, Anforderungen >32 und Fail-Closed-Export;
      vorhandene JSON-/Export-Fälle unverändert grün.
- [x] Fachlich gültige Änderungen bei aktuellem Export-Limit editierbar;
      maschinenlesbare Blocker nach Zielprofil, Feature-Code und Objekt
      verfügbar. Unbekannte Compilergründe sind ausdrücklich generisch.
- [x] Studio-Raumvorschau benötigt keinen erfolgreichen SCUMM-Export mehr;
      sichtbare Authoring-Platzhalter werden nicht als Gameplay beworben.
- [x] Vorhandene Mengen-/Geometrie-/Layoutgrenzen nach ADR-0002
      [klassifiziert](architecture-audit.md); ohne nativen Quellbeleg gelten
      übrige Compilerquoten als vorläufige `EXPORTER_LIMIT`.
- [ ] Native Grenzen bei den jeweiligen P0.x-Arbeitspaketen mit
      ScummC/ScummVM-Quellen beweisen bzw. vorläufige Exporterquoten ersetzen.

### Aktueller Arbeitsvorrat (P1)

- [ ] **P0.1 (mit A0-Regression-Gates):** Binär-Roundtrip-Parser für ScummC-Raumdaten
      (RMIM/SMAP/ZPxx/OBIM/OBCD), mit Test-Fixture und Größen-/Offset-/ID-Prüfungen.
- [ ] **P0.2:** Z-Plane-/Maskenbilder in RoomAsset, JSON, Validierung und
      ScummC-Export; sichtbare Verdeckung in stock ScummVM.
- [ ] **P0.3:** Native Walkboxen, BOXM, SCAL und Perspektive;
      Actor-Weg und Maskenzuordnung in ScummVM geprüft.
- [ ] **P0.4:** Bewegte, zustandsabhängige, klickbare Objekte einschließlich
      Parent-State und aktualisierter Hitbox.
- [ ] **P0.5:** Native Actor-/Costume-Ressourcen, Animation, COUNT-Marker
      und zeitabhängige Skriptreaktionen.
  - [x] Teil-Gate: unabhängig erzeugte, original-v6-COST-Ressourcen mit
        Richtungs-/Framefolgen und expliziten `COUNT`-Kommandos via ScummC.
        Native Darstellung in ScummVM und positive/negative
        `getActorAnimCounter1`-Gameplay-Probe belegt
        ([COST-Vertrag](scumm-v6-native-costume-count-contract.md)).
  - [x] Teil-Gate: COST-Frames und Animationen in `GameDocument`-JSON v1
        authorbar, verlustfrei roundtrip-fähig und als ScummC-Inputs exportiert;
        native Actor-Symbol-/Spielbindung ist weiterhin offen.
  - [x] Teil-Gate: Mehrere Actor-Instanzen mit referenzierter COST, initialer
        Position und Blickrichtung; Modell/ScummC-Bootstrap-Bindung und
        nativer ScummVM-Start nachgewiesen. Eine benannte Startanimation
        löst COUNT-Ereignisse am projektdefinierten Actor aus (positive
        Zwei-COUNT- und negative Drei-COUNT-Kontrolle, Actions `42421713939`).
  - [x] Teil-Gate: Versionierte `ActorCountCondition` und `ObjectStateEffect`
        mit nativer Script-Ausgabe und einer aus Projekt-JSON geladenen,
        in stock ScummVM getesteten COUNT-Objektreaktion. Native CI
        `42461862069` mit JSON-Projektregel und manueller Negativkontrolle.
  - [x] Teil-Gate: deklaratives `AnimationInputRule`-Zeitfenster mit
        früh/spät getrennten nativen Objektzuständen. Stock-ScummVM-Probe
        bestätigt 0/1/2 Spieleraktionen einschließlich erneuter Eingabe
        **im selben Prozess**; CI `42467237997`.
  - [x] Teil-Gate: Dieselbe späte, deklarative Eingabe bleibt nach
        `Harbor → Cellar → Harbor` über normale `WalkTo`-Hotspots erhalten:
        Schlüssel weiterhin unsichtbar, Tür offen. Native CI `42468551627`.
  - [x] Teil-Gate: Initialanimation pro Actor nur einmal über ein globales
        natives SCUMM-Bit starten. Ein adversarialer COUNT-Wächter würde
        nach Wiedereintritt den Schlüssel wiederbeleben; die stock-ScummVM-
        Probe `42471602488` bestätigt, dass dies ausbleibt.
  - [x] Teil-Gate: Ein abgeschlossener COUNT-/Push-Objektzustand
        übersteht natives ScummVM-Speichern, Interpreter-Neustart und Laden;
        danach bleibt die Initialanimation über einen echten
        `Harbor → Cellar → Harbor`-Rückweg gesperrt. Stock-ScummVM-
        CI `42477804196` grün; laufende Animationen separat.
  - [x] Produkt-Teilgate: `animation_triggers` startet benannte
        Costume-Animationen bei jedem zugeordneten Hotspot-Verb erneut.
        Modell, JSON und ScummC-Ausgabe implementiert; native Fixture mit
        zweitem Actor erfolgreich kompiliert und gestartet (CI `42481225873`).
        Wiederholte Spielerinteraktion noch nicht gesondert visuell belegt.
  - [x] Produkt-Implementierung: `interaction_sequences` kombiniert native
        Actor-Cues, Pausen und Objektzustände in einem geordneten Verbablauf;
        JSON und Exporter angebunden. Native CI und Gameplay-Nachweis offen.
  - [x] Produkt-Implementierung: Interaktionsfolgen aus einem geladenen nativen
        `GameDocument` im Gradio-Studio anlegen, Schritte anhängen, umordnen,
        entfernen, bestehende Schritte samt Parametern bearbeiten und JSON
        bzw. natives SCUMM-ZIP exportieren. Service-Test
        grün; Gradio-Start-Smoke CI `42486144774` grün, vollständige
        UI-Interaktion und Interaktionsnachweis in ScummVM noch offen.
  - [x] Native End-to-End-Abnahme: Eine mit denselben Studio-Aktionsoperationen
        erstellte Actor-Folge (Versetzen, Laufen, Warten, Drehen, Animation,
        Türzustand) über einen realen Hotspot-Verb-Klick in stock ScummVM
        ausführen. Stock-ScummVM-Lauf `42501905023` öffnet die zuvor
        geschlossene Tür nach realem Klick und der sechsstufigen Folge;
        Bilder/JSON im CI-Artefakt. Einzelne Actor-Zwischenpositionen und
        wiederholte/abgebrochene Sequenzen bleiben gesondert offen.
  - [x] Produkt- und Native-Teilabnahme: Eine Interaktionsfolge im Studio an
        einen vorhandenen Objektzustand binden. `getObjectState` prüft im
        nativen Verbscript die Voraussetzung, bevor Actor-/Objektaktionen
        starten. Ein bestehendes ScummVM-Klickszenario verwendet das neue
        Gate erfolgreich (CI `42505166878`). Wiederholte Zustandswechsel
        werden im folgenden Paket geprüft.
  - [x] Zustandsvarianten desselben Hotspot-Verbs: Studio kann eine Variante
        duplizieren und mit anderen Aktionen für einen anderen Zustand des
        selben Objekts belegen. Native `case`-Ausgabe vermeidet konkurrierende
        Verbbindungen; echte Klickfolge Tür 1 → 2 → 1 → 2 in stock ScummVM
        bestätigt (CI `42506834029`). Unterbrechung laufender Sequenzen
        bleibt ein eigenständiges offenes Gameplay-Paket.
  - [x] Produkt-Implementierung: Interaktionsvarianten können im Studio
        separat als **mit Escape überspringbar** markiert werden. Der native
        ScummC-`try`/`override`-Pfad setzt bei Skip die letzten geschriebenen
        Objektzustände, Actor-Zielpositionen und Blickrichtungen, statt
        Wartezeiten/Bewegungen zu Ende laufen zu lassen. In einer realen
        Stock-ScummVM-Klickprobe wird Escape während der Actor-Folge ausgelöst.
        Weitergehende Cutscene-Zustände (Inventarkombinationen, Ton,
        Raumwechsel) bleiben offen.
  - [x] Produkt-Implementierung: Ein Studio-Sequenzschritt kann ein als
        `pickup` markiertes Raumobjekt nativ ins Inventar übernehmen. Die
        UI kann zusätzliche Schritte gezielt an eine vorhandene bedingte
        Variante anhängen; der Escape-Override erhält ebenfalls die
        Inventaraufnahme. Das ScummVM-Klickszenario kontrolliert den Token
        nach der übersprungenen zweiten Sequenz. Ton und Raumwechsel offen.
  - [x] Produkt-Implementierung: Autorierte Actor-Interaktionen können ein
        vorhandenes Inventar-Kombinationsrezept als Sequenzschritt ausführen.
        Die beiden Voraussetzungen werden über native Besitzerzustände
        geprüft; der resultierende Gegenstand wird mit `pickupObject` erzeugt.
        Ein Escape-Skip führt auch vorausgehende Pickups und die Kombination
        in Schrittfolge aus. Native Probe kontrolliert das Badge-Icon nach
        dem zweiten Escape. Audio-/Raumwechsel-Skip weiterhin offen.
  - [x] Produkt-Implementierung/Native Abnahme: `Raum wechseln` ist als
        terminale Studio-Sequenzaktion mit existierendem Zielraum, JSON-v1-
        Roundtrip und `startRoom` nach normalem Ablauf beziehungsweise nach
        `try`/`override` implementiert und lokal getestet. Die echte native
        Door-/Close-Probe überspringt die Wartezeit, erreicht `Cellar`, kehrt
        über `Stairs` zurück und kontrolliert Türzustand und Badge im Inventar
        (Actions `42514653114`, Actor-Schritt grün). Allgemeine Cutscene-
        Audio-Endzustände bleiben ein separates Produktpaket.
  - [x] Produkt-/Native-Abnahme: MIDI kann als versionierte Ressource im
        Studio einem Raum zugewiesen werden; `Musik starten`/`Musik stoppen`
        erzeugen die nativen ScummC-Befehle und beim Escape den letzten
        Musik-Endzustand. Native SOUN-Kompilierung ist in den regulären ZIP-
        Export integriert. Modell, UI, JSON und Quell-/Fake-Exporter lokal
        getestet. Die ScummVM-Klickprobe (`42517210707`) bestätigt die native
        SOUN-Kompilierung und gemessene PCM-Aktivität vor Stopp, nach Stopp und
        nach Neustart; dieses Ergebnis ist ein Pflichtgate. Der vollständige
        native CI-Lauf `42517572328` hat es erneut erfolgreich ausgeführt.
  - [x] Produkt-Implementierung/lokale Tests: Raumspezifische VOC-Dateien
        lassen sich im Studio importieren, als `Sound starten`/`Sound stoppen`
        in Sequenzen verwenden und im regulären Export durch ScummC `soun -voc`
        in native SOUN-Ressourcen übersetzen. Escape übernimmt pro Sound-ID
        den letzten Zustand. JSON-Roundtrip, UI-Services und Fake-Exporter
        getestet (289 lokale Tests). Das native Hotspot-Klick-/Escape-Gate
        bestätigt echtes VOC-Audio und dessen Stopp in stock ScummVM
        (PCM `0,0000` vor / `0,8558` während / `0,0000` nach Escape,
        CI `42522610786`).
  - [x] Produkt-Implementierung/lokale Tests: VOC-Sprachzeile als echte
        Studio-Sequenzaktion mit editierbarem Untertitel und optionalem
        Sprecher, JSON-v1-Roundtrip und nativen Start-/Text-/Wait-/Stop-
        Befehlen. Escape beendet die Sprachressource. Aktuell sichere
        ASCII-Untertitel. In stock ScummVM sind Text und VOC-Ton gleichzeitig
        sichtbar/hörbar und nach Escape stumm (CI `42524819678`,
        PCM `0,0000`/`0,8557`/`0,0000`).
  - [x] Produkt-Implementierung/lokaler Test: Unicode-Untertitel einschließlich
        deutscher Umlaute in der regulären VOC-Sprachzeile, mit automatisch
        geplanter und durch ScummC erzeugter CHAR-Ressource. Fehlende Fonts
        und Byte-/Glyph-Grenzen werden sichtbar abgelehnt; die bestehende
        ASCII-Ausgabe bleibt ohne Zusatzabhängigkeit. 291 Tests grün;
        natives Untertitel-/PCM-Gate für `Ich höre die Glocke.` bestanden,
        inklusive korrektem Umlaut-Screenshot und VOC-Stopp nach Escape
        (CI `42526681259`).
  - [x] Produkt-Implementierung/lokale Tests: Eine gesprochene VOC-Zeile
        besitzt weitere Sprachvarianten mit eigenem Sound und Untertitel;
        Sprachkürzel können in der Studio-UI bearbeitet und die Standardsprache
        festgelegt werden. Die native v6-Sprachleiste steuert Text und Ton
        gemeinsam; nicht vorhandene Übersetzungen verwenden die Standardsprache,
        Escape stoppt alle möglichen Aufnahmen. 292 Tests grün;
        native Sprachwechsel-/PCM-Probe noch in CI zu bestätigen.
  - [x] Produkt-Implementierung: Story-Räume im Gradio-Studio mit vorhandenen
        nativen Actors/Costumes und Interaktionsregeln kombinieren; bei
        Storyänderungen neu validieren, Story und Projekt gemeinsam in das
        Spiel-ZIP legen. Kein dauerhafter gemeinsamer Authoring-Datentyp;
        Gameplay-Nachweis offen.
  - [x] Produkt-Implementierung: gemeinsames `adventure.studio.json` für
        Story und native Actor-/Costume-/Interaktionsdaten speichern, laden,
        erneut bearbeiten und ohne doppelte Room-Bitmaps exportieren.
        Validierter Service-Roundtrip; UI- und Gameplay-Gates offen.
  - [x] Produkt-Implementierung: neue Costumes aus echten PNGs im Gradio-Studio
        anlegen, Actors in Story-Räumen erstellen und ihre Position/Richtung
        bearbeiten. Eine Standpose und native `gesture`-Aktion pro Costume;
        mehrteilige Animationen, echte PNG-COST-Kompilierung und Gameplay-
        Nachweis noch offen.
  - [x] Produkt-Implementierung: weitere PNG-Frames in Costume aufnehmen und
        native Animationsfolgen pro Blickrichtung mit Frame-IDs und `COUNT`
        als Daten authoren; ScummC-Quellgenerierung und Verb-Aufruf im
        Studio-Integrationstest, native Kompilierung/Gameplay noch offen.
  - [x] Produkt-Implementierung: visuelle Timeline aus importierten Costume-
        Frames und nativen Kommandos, mit Auswahl, Umordnung, Hinzufügen und
        Entfernen. Derselbe native COST-Exporter bleibt zuständig; animierte
        Vorschau und ScummVM-Gate offen.
  - [x] Produkt-Implementierung: animierte GIF-Editor-Vorschau aus wirklichen
        Costume-Frames und ihren Ursprungspositionen, mit frei gewählter
        Vorschaugeschwindigkeit. Keine behauptete SCUMM-Tick-Semantik;
        nativer Gameplay-Nachweis weiter offen.
  - [ ] Native Verifikation: Der experimentelle Actor-Workflow erzeugt jetzt
        zusätzlich über die echten Studio-PNG-Aktionen eine zweiframeige
        `wave`-COST samt Actor-Startanimation und archiviert Compiler-/
        ScummVM-Artefakte. Ein grüner Workflowlauf und ein beobachteter
        Framewechsel fehlen noch; reiner Spielstart genügt nicht für V.
        Der Workflow ist nun bei passendem PR ausführbar und prüft mehrere
        tatsächlich aufgenommene Bilder auf beide native Frame-Farben.
        Erster nativer Lauf `42493144908` zeigte fehlende COST-Farben;
        die Raum-/Costume-Palettenzuordnung ist im Export korrigiert, die
        erneute ScummVM-Bildprüfung `42493988461` zeigt beide Farbphasen;
        die verschärfte Prüfung verlangt wechselnde dominante Farben und
        bleibt bis zum erneuten vollständigen CI-Lauf offen.
  - [x] Produkt-Implementierung: Im Gradio-Studio kann eine native
        Animation eines Actors als Startanimation ausgewählt oder deaktiviert
        werden. JSON und SCUMM-Export verwenden die bereits bestehende
        Actor-/Costume-Bindung; visuelle ScummVM-Verifikation unverändert offen.
  - [x] Produkt-Implementierung: geordnete Hotspot-Interaktionen können
        Actors mit einer nativen `putActorAt`-Aktion an eine neue Position
        im selben Raum setzen. Studio-UI, Projekt-JSON und Export sind
        verbunden; die interaktive ScummVM-Spielprobe ist noch offen.
  - [x] Produkt-Implementierung: der neue `walk_actor`-Schritt startet
        in einem nativen Interaktionsablauf `walkActorTo` zum angegebenen
        Raumziel; anders als `move_actor` löst er eine Laufbewegung aus.
        Ein implizites Ankunfts-Wait wird nicht erfunden. ScummVM-Nachweis
        des projektdefinierten Actors bleibt offen.
  - [x] Produkt-Implementierung: `wait_actor` als expliziter nächster
        Interaktionsschritt mit nativer ScummC-Signatur `waitForActor(actor)`;
        weitere Aktionen beginnen erst, wenn der Actor nicht mehr läuft.
        Signatur in den unveränderten ScummC-Beispielen belegt; die neue
        Studio-Choreografie ist noch nicht in stock ScummVM vorgeführt.
  - [x] Produkt-Implementierung: `face_actor` dreht einen Projekt-Actor
        als native Interaktionsaktion über `setCurrentActor` und
        `setActorDirection` in N/E/S/W; die vorherige Actor-Auswahl wird
        auf `VAR_EGO` zurückgesetzt. Studio/JSON/Exporter sind verbunden,
        die visuelle ScummVM-Probe dieser Zusammensetzung bleibt offen.
  - [ ] Allgemeine Actor-Zuordnung, Animations-Cue-/Condition-IR und
        projektgetriebene Aktionsfenster sind **nicht** durch das Fixture gelöst.
- [ ] **P1.1:** Native Kameraführung, Shot-Komposition und Cutscene-
      Kontrollfluss mit Skip-Endzustand.
  - [x] Teil-Gate: unbeschränkte native v6-Raum-Kamera-Cues
        (`setCameraAt`, `panCameraTo`, `waitForCamera`, `cameraFollowActor`),
        dokumentierter Binärpfad und zwei in stock ScummVM verglichene
        Bildkompositionen ([Kamera-Vertrag](scumm-v6-camera-cue-contract.md)).
        **Nicht** als Abschluss von P1.1 werten: Override/Skip, Shots und
        Actor-Choreografie sind weiterhin offen.

Detaillierte Abhängigkeiten: [Export-Lückenanalyse](scumm-v6-export-gap-analysis.md).
Diese Liste ist **kein Abschluss** des v6-Funktionsumfangs; weitere
Funktionen werden anhand der Capability-Matrix priorisiert.

## Historische, detaillierte Entwicklungsmeilensteine

Stand: 2026-11-04. Dieses Dokument ist die Arbeitsgrundlage für die Umsetzung.

**Mechanik-Erweiterung (2026-11-07):** Der vollständige Anforderungskatalog
für typische, auch zeitabhängige klassische Adventure-Spielabläufe steht in
[`scumm-adventure-mechanics.md`](scumm-adventure-mechanics.md). Die erste
quellenbasierte Zuordnung zu originalen v6-Operationen und offenen
Kompatibilitätsfragen steht in
[`scumm-v6-runtime-contract.md`](scumm-v6-runtime-contract.md).
Diese Dokumente sind Forschungs-/Entwurfsstände, keine als implementiert
markierten Produktfeatures.
Die vertiefte Prüfung konkreter ScummVM- und ScummC-Quellcodepfade ist in
[`scumm-v6-source-audit.md`](scumm-v6-source-audit.md) dokumentiert.

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

## Mehrsprachigkeit (SCUMM-v6-Kompatibilitätsblock)

Ein verlinktes Spiel soll die Sprachen Deutsch, Englisch, Französisch,
Polnisch und Japanisch zur Laufzeit anbieten. Text-IDs bleiben unabhängig
von der Sprache und referenzieren dieselbe Spielmechanik. Die technische
Analyse und die offenen Nachweispunkte stehen in
[`docs/localization-compatibility.md`](localization-compatibility.md).

- [x] Strikter, versionierter Unicode-Übersetzungskatalog mit vollständigen
      Sprachvarianten und deterministischer Zeichensatzbedarfsanalyse.
- [x] Stabile Sprach-IDs und ScummC-Quelltextfragment mit fünf bedingten
      Textzweigen; Polnisch und Japanisch mit eigenen Testfällen.
- [x] Deterministische CHAR-Bitmap-Vorbereitung mit überprüfter Font-Cmap,
      ScummC-Konverter-Aufruf und Ressourcenslot-Prüfung; unabhängiger
      `font-smoke.yml`-Workflow für alle fünf Sprachen vorbereitet.
- [ ] Font-Glyphen für die benötigten Bytecodes als SCUMM-CHAR-Ressource
      erzeugen und **im Interpreter** nachweisen; erfolgreiches Konvertieren
      allein genügt nicht.
- [ ] Laufzeit-Sprachwahl, Raumwechsel und Save/Load in stock ScummVM prüfen.
- [ ] Sprachausgabe (VOC) je Sprachvariante unabhängig verifizieren.
- [ ] Erst nach grünen Interpretertests ins normale Story-/SCUMM-Exportmodell
      integrieren; bis dahin keine scheinbar spielbare Unicode-Ausgabe.

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
      (`scumm_toolchain.py`, lokale Boundary-Tests und erfolgreicher ScummVM-
      Gameplay-Lauf #42022413382).
- [x] Zwei erforderliche Gegenstände als vollständigen Story-JSON-zu-ScummVM-
      Gameplay-Test nachgewiesen: Schlüssel allein öffnet die Tür nicht,
      zusätzlicher Gegenstand wird in das Inventar übernommen, danach öffnet
      die Tür und der Zielraum wird betreten (CI-Lauf #42023767043).
- [x] Drei erforderliche Gegenstände in stock ScummVM nachgewiesen: sowohl
      Schlüssel allein als auch Schlüssel und Abzeichen ohne Münze lassen die
      Tür verschlossen; erst das vollständige Inventar öffnet den Zielraum
      (CI-Lauf #42024978434).
- [x] Lineare Rätselkette mit zwei Türen und drei Szenen: Story-JSON-Export,
      verknüpfte Ressourcen und ScummVM-Start erfolgreich (CI #42026108989).
- [x] Vollständigen Spielweg durch beide Türen der Rätselkette in ScummVM
      nachgewiesen: Hafenhaus-Schlüssel, erster Raumwechsel, Keller-Abzeichen,
      zweite Tür und finaler Archivraum (CI-Lauf #42028572233).
- [x] Persistente Zustände und Rückwege über mehrere verknüpfte Räume hinweg
      in stock ScummVM geprüft: Archiv → Keller → Hafenhaus; beide Türen
      bleiben geöffnet, beide Gegenstände bleiben im Inventar und erscheinen
      nicht erneut in den Räumen (CI-Lauf #42029750897).
- [x] Deklaratives Story-Rezeptmodell v2: exakt zwei Zutaten, ein hergestelltes
      Ergebnis, einmalige Entnahme vom Boden, atomare KI-Änderungen,
      deterministische Spielbarkeitsprüfung auch bei Verbrauchs-Softlocks und
      Bereinigung nicht mehr referenzierter Pickups mit Änderungsbericht
      (ohne SCUMM-Laufzeitexport).
- [ ] Inventar-zu-Inventar-Kombinationen in SCUMM v6 kompilieren und den
      kompletten Spielablauf bis zum Ziel in ScummVM nachweisen.
- [ ] Adapter auf weitere Rätseltypen, mehrere Kapitel, Figuren und Dialoge
      erweitern; die aktuelle Platzhaltergrafik durch einen Asset-Generator
      ersetzen und End-to-End-Spielbarkeit eines adaptierten Projekts testen.

### M4 – Grafik- und Animationspipeline

- [ ] Einheitliche Stile, Figuren- und Raumvarianten, Paletten und Animationen.
- [ ] KI-Bilder vor Verwendung deterministisch auf Format und Grenzen prüfen.
- [x] Erste Objektpositionen sind editierbar; `Story`-Format v3 enthält
      optionale `placements` mit stabilen Item-IDs, strikter Referenz-/
      Geometrieprüfung, atomarem Änderungsbericht und abwärtskompatiblem
      JSON. Der SCUMM-Exporter setzt die Objekt-Hotspots entsprechend.
- [x] Provider-unabhängiger Vertrag für fertige 8-Bit-Indexbilder, inklusive
      Palette, Abmessungen, Herkunft und reproduzierbarem Content-Hash;
      Offline-Fixture-Provider mit Validierung und Tests (`image_pipeline.py`).
- [x] Story-zu-SCUMM-Compiler liest Raumhintergründe über die Provider-Grenze;
      Standard bleibt der bisherige byteidentische Offline-Generator. Externe
      Fixture-Provider werden ohne Änderung der SCUMM-Exportkette unterstützt.
- [ ] Einen späteren ComfyUI-/RunComfy-Adapter für **vorhandene, vom Nutzer
      bereitgestellte Workflows** ergänzen; aktuell keine Verbindung, keine
      Modellwahl und keine Netzwerkaufrufe im Build.
- [ ] Generierte Assets unveränderlich zwischenspeichern (Workflow-Version,
      Modell, Seed, Quell-ID), damit Story- und SCUMM-Builds dieselben Bilder
      wiederverwenden und keine stillschweigende Neugenerierung auslösen.
- [ ] Palette-Cycling für geeignete Szeneneffekte als gesonderten,
      deterministischen SCUMM-v6-Compilerbaustein entwickeln und in ScummVM
      mit visuellen Prüfungen validieren.
- [x] Erste deterministische, providerunabhängige Palettenzyklus-Vorschau
      (`palette_animation.py`): Bereichs-/Timingprüfung, geschützte Indizes,
      disjunkte Zyklen, Vorwärts-/Rückwärtsrotation und Tests.
- [x] Deklarative Palettenzyklen werden als SCUMM-v6-`CYCL`-Ressourcen
      aus `RoomAsset` erzeugt und in das kanonische Projekt-JSON übernommen;
      reservierte Transparenz- und Sprite-Indizes dürfen nicht rotieren.
- [x] Separates opt-in-Wasserfixture und ScummVM-Screenshot-Probe in CI
      integriert, inklusive JSON-Auswertung von animiertem Wasser und
      unveränderter Himmelsfarbe (`palette_demo.py`, `scumm_palette_probe.py`).
- [x] **CI-Gate:** Stock ScummVM bestätigt vier wechselnde Wasserfarben bei
      statischem Himmel (CI #42047861523, erneut #42048814497).

Die KI-Bildworkflows sind **selbst für Pixel-Art-Stil, Zielauflösung und
Farbpalette zuständig**. Adventure Studio quantisiert oder skaliert ein
gültiges Provider-Ergebnis nicht erneut. Die Engine prüft lediglich, ob
die tatsächlich gelieferten Pixel die SCUMM-Grenzen erfüllen. Farbindizes
für Palette-Cycling sind eine zusätzliche, explizit definierte Bearbeitung:
ein hübsches Pixel-Art-Bild ist nicht automatisch farbzyklusfähig.

### M4b – Musik, Soundeffekte und Sprachausgabe

- [x] Architekturentscheidung: ereignisgesteuerte, iMUSE-orientierte Musikregie
      statt bloß einer starren Hintergrundmusik je Raum
      (`docs/audio-architecture.md`).
- [x] Typisierter, deterministischer Musikplan mit Tracks, Ereignissen,
      Übergangsanforderungen (`immediate`/`beat`/`bar`) und Bericht über
      unreferenzierte Tracks (`music_director.py` samt Tests).
- [ ] Erstes originales MIDI-/ScummC-Soundresource-Fixture in stock ScummVM
      hörbar überprüfen; Ton- oder MIDI-Nachweis in CI, kein reiner Buildcheck.
- [x] Originales MIDI-SMF-Teststück und optionales SCUMM-v6-Einstiegsmusik-
      Fixture generieren (`music_demo.py`); `soun -gmd`- und
      ScummVM-Audioerfassungsgates in CI vorbereitet.
- [x] Originale MIDI-Ressource und reale nicht-stumme PCM-Ausgabe in ScummVM
      gemessen (CI #42048814497). Kontrollspiel ohne Musik als nächstes
      Nachweis-Gate ergänzt; Ergebnis noch offen.
- [ ] Spielereignisse steuern Start, Stop und musikalischen Zustandswechsel.
- [ ] iMUSE-Beat-/Takt- und Hook-Übergänge als **eigene** Kompatibilitäts-Gates
      nachweisen; keine unbemerkte Herabstufung auf harte Schnitte.
- [ ] Wiederverwendbare Soundeffekte und klassische VOC-Sprache mit
      Untertiteln, später optionalen Generator-Providern und Provenienz.

### M5 – KI-Story-Regie

- [x] Erste **providerunabhängige Story-Regie**: natürlichsprachlicher
      Änderungswunsch plus kanonischer Projektstand als Eingabe, untrusted
      JSON-Operationen als Ausgabe. Die deterministische Pipeline prüft
      sämtliche Änderungen atomar, konsolidiert, verifiziert die Spielbarkeit,
      testet die SCUMM-Exportgrenze und zeigt den Diff vor Bestätigung.
      Keine KI-Ausführung oder generierten Skripte.
- [x] Optionaler OpenAI-Responses-Adapter mit explizitem Opt-in über
      `OPENAI_API_KEY`, ohne Server-Speicherung (`store=false`) und ohne
      Abhängigkeit des Kerns vom Anbieter. Offline-Import fremder
      Operations-JSON bleibt möglich; echte API-Integration ist noch nicht
      mit Zugangsdaten end-to-end geprüft.
- [ ] Plot-, Kapitel- und Szenenentwürfe als validierte Operationen.
- [ ] Änderungswünsche zu Gegenständen, Rezepten, Dialogen und Rätseln.
- [ ] Ergebnisbericht: hinzugefügt, geändert, entfernt, Konflikte und Tests.
- [ ] Konflikte werden gezielt geklärt; Rollback und Revisionen sind möglich.

### M6 – Gradio Studio und MCP

- [x] Erste **Projektübersicht** als deterministisches, UI-unabhängiges
      Inventar (`studio_catalog.py`): Kapitel, Szenen, Charaktere samt
      Bildstatus, Gegenstände/Positionen, Rätsel, Rezeptkombinationen,
      Hintergrundvorschau-Galerie und ein direkt aus dem Storymodell
      abgeleiteter Beziehungsgraph mit Referenzen und Raumübergängen.
      Die Ansicht aktualisiert sich nach jedem bestätigten Edit.
- [ ] Visuelle Story-Bibel: Charakterporträts, Sprite-Sheets,
      Animationen und Raumhintergründe über **stabile Asset-Referenzen**
      im versionierten Datenmodell verknüpfen; den Bildstatus inklusive
      Erzeugungs-/Versionsinformation je Figur und Szene anzeigen.
- [x] **Storyformat v4:** Überprüfbare Referenzen für Hintergründe,
      Porträts, Lauf- und Objektsprites sowie Sprache mit Asset-ID,
      Zielobjekt, Quell-ID und SHA-256. Die Dateien selbst werden noch
      nicht geladen oder neu generiert.
- [x] **Dialog-Datenmodell v4:** Gespräche, Sprechende, Dialogknoten und
      Antwortverzweigungen mit deterministischer Erreichbarkeits- und
      Sackgassenprüfung. Die Übersicht zeigt Texte, Referenzen und Graph;
      bestehende Dialogzeilen sind im Gradio-Editor änderbar.
- [x] **Export-Grenze:** Dialoge/Assets können gespeichert werden;
      unimplementierte Inhalte werden beim SCUMM-Build ausdrücklich
      abgewiesen und im Änderungsbericht als Exportwarnung angezeigt.
- [x] **Erster SCUMM-Dialog-Compiler:** Figuren als Platzhalter-Hotspots,
      je Figur ein einfacher linearer Dialog (bis zu 16 Zeilen), `TalkTo`,
      `egoSay` und `waitForMessage`; Quellen und Projekt-JSON sind getestet.
      ScummC-Kompilierung bestätigt (#42101258027), vollständiger manueller
      ScummVM-Dialogklick steht noch aus.
- [x] Erster begrenzter **Antwortauswahl-Compiler** als typisierter,
      datenbasierter `TalkRule`-/`TalkChoice`-Baustein. Bis zu drei temporär
      eingeblendete, anklickbare Antwortobjekte; Auswahl löst lineare
      Folgezeilen aus. Quelltext-/JSON-Roundtrip-Tests grün; ScummC hat die
      Auswahl-Ressourcen kompiliert (#42103638725). Ein separater visueller
      ScummVM-Klicktest prüft nun den Zustandswechsel von verborgenen zu
      sichtbaren und wieder verborgenen Antworten; Ergebnis noch offen.
- [x] **Isolierter Dialog-CI-Workflow:** `.github/workflows/dialogue-smoke.yml`
      kompiliert ausschließlich das versionierte Dialogfixture und prüft
      die ScummVM-Eingabe mit Screenshots und JSON-Report. Unabhängig von
      den längeren Musik-/Palette-/Raumwechseltests; Laufzeitergebnis offen.
- [ ] Echte NPC-Sprechblasen, klassisches SCUMM-Gesprächsmenü, Sprecherwechsel,
      Kostüm-/Animationsresourcen und Voice-Cues mit Stock ScummVM prüfen.
- [ ] Dialogmodell als eigene versionierte Struktur: Sprechende,
      Dialogknoten, Antwortoptionen, Bedingungen, Effekte, Untertitel
      und optionale Sprach-Assets. Dialoggraph und Verzweigungen
      deterministisch auf fehlende Referenzen, unerreichbare Knoten
      und Sackgassen prüfen. Erst danach SCUMM-v6-Ausgabe erweitern.
- [ ] Interaktiver Graph mit Filtern (Kapitel, Szenen, Charaktere,
      Gegenstände, Aktionen/Dialoge), Detailauswahl und Navigation
      zum jeweiligen Editorfeld; zum Start ist der SVG-Graph lesbar.
- [x] Erste **optionale lokale Gradio-Oberfläche** mit Story-JSON-Import,
      Kapitel-/Szenenübersicht, Raumvorschau samt Hotspot-Markierungen,
      Szenen- und Gegenstandseditor, neuen Dekorationsobjekten,
      deterministischem Änderungs-/Prüfbericht und JSON-Export.
      Die UI importiert die Gradio-Abhängigkeit erst beim Start und benutzt
      `studio_service.py` als testbare, UI-unabhängige Grenze.
- [x] Manuelle Textkorrekturen ohne Änderungen am generierten SCUMM-Quelltext;
      atomare Modelländerung mit `edit_story` und zusätzlichem SCUMM-Adaptercheck.
- [x] Erste Rätselbearbeitung: Titel und notwendige Inventar-IDs ändern;
      Änderungen werden vor dem Übernehmen mit Diff, Story-Solver und
      SCUMM-Adapter geprüft. Stale Vorschläge dürfen nicht stillschweigend
      gegen einen neueren Storyzustand übernommen werden.
- [ ] Vollständiger Rätsel-, Kapitel- und Dialogeditor, Drag-and-drop-Positionierung und
      eine tatsächlich live gestartete ScummVM-Spielvorschau.
- [ ] Browser-UI nach dem ersten Gradio-CI-Smoke interaktiv evaluieren;
      separate `.github/workflows/studio.yml` installiert das optionale
      Studio-Profil und baut die echten Gradio-Blocks samt Callback-Graph auf.
- [x] Experimenteller SCUMM-ZIP-Export aus Gradio mit einer **vorhandenen
      lokalen ScummC-Toolchain**. Validierte Story und spielbare Dateien
      werden in einem ZIP ausgeliefert; der Compiler arbeitet auf einer
      temporären Kopie der Toolchain, um Nutzerdateien nicht zu verändern.
      Deterministischer ZIP-Inhalt und Fehlerfall sind lokal getestet.
- [ ] Compiler-Setup und Plattformfähigkeit für Endnutzer vereinfachen:
      Build-Service oder gekapselte Toolchain, ohne implizite Downloads im
      lokalen Editor und mit getrennten Lizenz-/Versionsgrenzen.
- [x] Erste **gekapselte Codespaces-Toolchain**: gepinntes ScummC wird beim
      erstmaligen Codespaces-Setup separat gebaut. Der Gradio-Editor erhält
      den Pfad automatisch, während sein Export weiterhin ohne neue Downloads
