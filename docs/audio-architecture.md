# Musik, Effekte und Sprache: SCUMM-v6-Audiokonzept

## Entscheidung

Wir beginnen mit einer **iMUSE-orientierten Musikregie** statt einer
einfachen festen Musikdatei pro Raum. Das Storymodell beschreibt Musikzustände
und semantische Übergänge (z. B. `MonsterSeen`); die spätere SCUMM-Ausgabe
entscheidet reproduzierbar über die dazugehörigen MIDI- und iMUSE-Befehle.
Wir bauen aber **keine neue Sound-Engine** und behaupten keine komplette
iMUSE-Kompatibilität, bevor echte ScummVM-Tests vorliegen.

Der Compiler ScummC dokumentiert `startMusic`, `stopMusic`, `startSound`,
`stopSound`, `isSoundRunning` sowie `soundKludge([cmds])` als Zugang zu iMUSE.
`soundKludge` ist eine Low-Level-Schnittstelle, keine fertige, sicher
abstrakte iMUSE-Bibliothek. Besonders musikalisch korrekte Übergänge über
Beats/Takte, Hooks und SysEx benötigen eigene, einzeln geprüfte Experimente.

Quellen:

- https://github.com/AlbanBedel/scummc/wiki/Scumm-6-functions
- https://github.com/AlbanBedel/scummc/wiki/ScummC-Grammar
- https://github.com/scummvm/scummvm/blob/master/engines/scumm/script_v6.cpp
- https://docs.scummvm.org/en/latest/advanced_topics/understand_audio.html

## Neu: deklarative Musikregie

`music_director.py` liefert eine bewusst begrenzte, deterministische Domäne:

- `MusicTrack(id, asset_id)`: stabile Identität und zugehörige Audioressource.
- `MusicTransition(event_id, target_track_id, mode)`: `immediate`, `beat`, `bar`.
- `MusicPlan`: Tracks, Übergänge, initialer Musikzustand.
- `resolve_music_event`: reine Zustandsauswertung ohne Seiteneffekte.
- `orphan_music_tracks`: Meldung unreferenzierter Musik ohne stilles Löschen.

`beat` und `bar` sind **Anforderungen**, noch keine tatsächlich unterstützten
SCUMM-Kommandos. Der Backend-Compiler muss unbekannte oder nicht nachweisbar
unterstützte Übergänge ablehnen, statt sie unbemerkt in harte Schnitte
umzuwandeln. Versionierung, Asset-Caching und atomare Änderungen folgen
denselben Regeln wie in der Grafikpipeline.

## Nächste Kompatibilitäts-Gates

1. Das originale MIDI-Teststück aus `music_demo.py` wird ohne Fremdassets als
   SMF Typ 0 erzeugt. Im experimentellen CI-Workflow verpackt ScummCs
   `soun -gmd` die Datei in `HarborTheme.soun`; der SCUMM-Exporter deklariert
   `sound HarborTheme = "HarborTheme.soun";` und startet es in der
   Raumeintrittsroutine mit `startMusic(HarborTheme)`. Die Datei muss vor dem
   Spielbuild vorhanden sein. **Compiler/Linker-Erfolg ist noch kein Beweis
   hörbarer Musik.**
2. Ein separater Audio-Forschungsprobe versucht mit dem SDL-Disk-Audiotreiber
   PCM-Samples aus stock ScummVM aufzunehmen und prüft auf Aktivität.
   Der erste reale Test produzierte 1,4 MB **Stille**, obwohl ScummC die
   GMD-Ressource erfolgreich eingebunden hatte (CI #42047861523). Das
   Testsetup erzwingt deshalb für den nächsten Lauf einen ausdrücklich
   gewählten FluidSynth-General-MIDI-Treiber mit lokalem SoundFont, statt
   ScummVM automatisch einen möglicherweise inkompatiblen AdLib-Treiber
   auswählen zu lassen.
   Der Test bleibt optional, bis das Audioformat und die mögliche
   Verwechslung mit Systemsounds beziehungsweise Startgeräuschen ausgeschlossen
   sind. Erst danach ist die Musikerzeugung in ScummVM hörbar nachgewiesen.
3. `stopSound()` und mindestens zwei Musikzustände durch ein Spielereignis
   steuern. Tonaufzeichnung und MIDI-Event/Log-Inspektion als CI-Nachweis
   entwickeln; ein grüner Compile-Lauf alleine reicht nicht.
4. iMUSE-Beat- oder Taktwechsel und Hook/SysEx-Strategien einzeln
   implementieren und mit exakt definierten MIDI-Teststücken prüfen.
5. Soundeffekte mit stabilen IDs und Wiederverwendung ergänzen.
6. Digitalisierte Sprache: ScummC `voice`-Ressourcen aus klassischen VOC-Dateien
   und optionalen Synchronisationspunkten; Untertitel bleiben separat und
   immer spielbar. Späterer TTS-Provider erzeugt Audio **außerhalb** des
   reproduzierbaren SCUMM-Builds.

## Noch nicht unterstützt

Die normale Story-JSON-Ausgabe enthält weiterhin keine Musik. Die neue
MIDI-Ressource ist eine **opt-in Forschungsvariante**, kein genereller
MIDI-Erzeugungsprovider. Kein echtes iMUSE-Timing und kein TTS-Aufruf.
DOS-/ScummVM-Unterstützung wird separat je Format und Ausgabeprofil geprüft.
