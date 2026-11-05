# Adventure Studio – deterministic core (prototype)

Story-first adventure creation, with a strictly data-driven, testable engine.

Project milestones and acceptance criteria: [`docs/roadmap.md`](docs/roadmap.md).

## Product target

**Produce original SCUMM v6 game data that runs in ScummVM.** The author never
needs to know about compilers or game file formats. Compatibility with an
original DOS SCUMM interpreter is a *separate optional goal*, not an assumption.
AGS is **not** an export target. The first integration candidate is ScummC;
its outputs and game recognition must be tested with unmodified ScummVM before
we can claim a working exporter. See `docs/room-and-export-contract.md`.

## Run tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

The current proof of concept supports Boolean state, atomic actions, reachability,
dead-end detection, typed object/action changes, orphan consolidation with
container dependencies, structured change reports and atomic JSON persistence
with revision checks. It now also includes a story bible (`story.py`) with
chapters, scenes, characters, items and puzzles, a deterministic story compiler,
typed story changes and a strict JSON protocol for untrusted AI proposals.
It does **not** yet include an actual AI provider or a visual editor. It now
generates experimental SCUMM-v6 graphics, room scripts and linked game fixtures.
The linked fixture still uses an external GPL ScummC bootstrap and a temporary
ScummVM game identity, so it is not a standalone release-ready export.
`targets.py` defines the SCUMM v6 target policy and a fail-closed export gate.

## SCUMM toolchain research

The CLI probe `PYTHONPATH=src python -m adventure_studio.scumm_probe GAME_DIRECTORY`
checks for non-empty matching `.000`/`.001` files and asks unmodified ScummVM
to detect them. This is an **early gate only**, not a playability test.

An experimental GitHub Actions workflow, `Experimental SCUMM v6 compatibility
probe`, builds the upstream ScummC sample on Ubuntu and attempts recognition
using stock ScummVM. It runs on relevant probe changes or manually. A red run
is diagnostic and not a product-release failure. Build success, game detection,
actual launch and save/load are separate acceptance gates.

The workflow tests **three distinct detection cases**: our normally linked
`studio.000/.001` files, the untouched upstream sample, and a separate
`tentacle.000/.001` research fixture created with ScummC's documented
`-key 0x69` compatibility option. The last case deliberately identifies as
Day of the Tentacle: it is useful for isolating detection failures, but is
**not** proof of native recognition, general ScummVM compatibility, or a
shippable game. Detection probes do not hide compiler/linker failures.

The experimental `scumm_launch.py` smoke test starts the isolated `tentacle`
compatibility fixture in an Xvfb display. It waits up to twenty seconds until
the blue initial room is actually rendered, then observes six more seconds
of scripted movement. It uploads start/end
screenshots (`.png`, plus raw `.xwd`), an ImageMagick difference image, a JSON
pixel-change report and console logs as Actions artifacts. The comparison
uses a 5% pixel color tolerance and requires at least 500 changed pixels.
This detects a stationary or entirely unchanged output but does not by itself
prove interactions or save/load. For the fixed 1024x768
test display it additionally samples pixel `(700,280)` in both screenshots:
the scripted two-screen room must visibly transition from blue sky to orange
sky (RGB tolerance 25/channel). That is a reproducible camera-pan signature,
but is not proof of smooth scrolling or arbitrary-room behavior. Those remain
separate integration milestones.

The live gameplay probe clicks the original SCUMM verbs and checks rendered
pixels through the sequence: locked door rejects entry, key pickup moves its
sprite to the inventory, `Use` opens the door, then a separate click enters
the goal room. A further research gate tests return to the first room and
object persistence. Save/load remains unverified.

## Story JSON to SCUMM

The story can now be represented as a versioned, code-free JSON document.
An example is checked into [`examples/mini_story.json`](examples/mini_story.json).
Generate the corresponding project model, SCUMM room sources and pixel assets:

```bash
PYTHONPATH=src python -m adventure_studio.story_document examples/mini_story.json build/story
```

The bounded adapter supports two scenes, up to three required inventory items,
an unlock puzzle and decorations. Unsupported narrative mechanics fail closed.
The GitHub research workflow also compiles this independent story fixture with
ScummC, runs a full single-key puzzle interaction in ScummVM and uploads a
`story-playable-preview` artifact for manual testing. The story-derived
key pickup, door unlock and goal-room transition passed in workflow
[#42021639269](https://github.com/nauen/adventure_studio/actions/runs/42021639269).
Multi-item gameplay and save/load have not yet been verified in ScummVM.
See [`docs/project-format.md`](docs/project-format.md) for the precise contract.

`scumm_assets.py` now emits an original 640×200 indexed BMP and a SCUMM-v6
`room` source with data-driven object hotspots, LookAt and PickUp handlers.
The experimental workflow attempts to compile the room and link it with the
upstream example's global startup scripts. This is **not yet** a standalone
game whose bootstrap was independently written by Adventure Studio. The
research adapter `scumm_bootstrap.py` retargets the original GPL demo's
bootstrap to our generated room, with exact-match safety checks. This requires
compatible upstream assets and carries the upstream code's license obligations.
The pipeline also replaces the upstream road
demo background with our generated image, rebuilds the *complete upstream demo*
and attempts stock ScummVM detection. That verifies parts of the exporter
chain without misrepresenting upstream game logic as our own. Linking our own
global scripts, actors and interactions is still unfinished.

## Boundaries

The AI should eventually propose typed project operations, not executable scripts.
Deterministic validation and state exploration decide whether a proposal may commit.
An incomplete state exploration must fail closed.

Use `adventure_studio.changes.apply_changes` to build a validated candidate
and inspect a complete diff before calling `adventure_studio.storage.save`.
The storage layer uses an atomic file replacement and a SHA-256 revision guard.
Concurrent writers must be serialized by a higher-level repository service;
the guard alone is not a multiprocess lock.

## Story-first workflow

1. Describe the plot using the immutable dataclasses in `story.py`.
2. `validate_story` checks references; `compile_story` translates a restricted
   puzzle vocabulary into generic actions; `verify_story` rejects softlocks.
3. An AI client can submit bounded JSON operations through
   `story_protocol.parse_operations`; no submitted code is evaluated.
4. `story_changes.edit_story` applies all operations on a candidate, validates
   the complete result and returns an explicit before/after report.

The current story compiler supports item pickup, scene-unlock puzzles and a
final puzzle goal. Dialogue trees, multi-step crafting, item consumption,
positioning and dynamic story generation are deliberately **not** implemented.

Dead-end analysis uses reverse reachability from winning states, so loops that
cannot reach a goal are classified as dead ends too. The current model remains
deliberately small: Boolean flags and predefined actions only.
# Gradio Studio (erste lokale Vorschau)

**Direkt im Browser über GitHub Codespaces:**

1. Repository auf GitHub öffnen, `Code` → `Codespaces` →
   `Create codespace on main` auswählen.
2. Beim ersten Start installiert die `.devcontainer/devcontainer.json`
   die optionalen Gradio-Abhängigkeiten. Danach startet das Studio auf
   **Port 7860** automatisch.
3. GitHub öffnet den weitergeleiteten Port im Browser. Falls das nicht
   automatisch passiert: in Codespaces den Reiter **Ports** öffnen und bei
   **Adventure Studio (7860)** auf die Webadresse klicken.

Der weitergeleitete Port bleibt standardmäßig **privat** und erfordert
GitHub-Anmeldung. Bitte den Port nicht öffentlich freigeben, solange das
Studio keine eigene Anmeldung implementiert hat. Codespaces hat ein separates
monatliches Nutzungskontingent; aktiven Codespace bei Nichtgebrauch stoppen.
In neuen Codespaces wird die ScummC-Toolchain beim ersten Einrichten aus
einem **festgelegten Upstream-Commit** kompiliert. Das kann einige Minuten
dauern; danach ist der Compilerpfad bereits im Studio gesetzt. Bei einer
lokalen Installation ohne Codespaces kannst du einen vorhandenen ScummC-Pfad
weiterhin selbst angeben.

Der erste Editor verwendet dasselbe validierte Storymodell wie der
deterministische SCUMM-Exporter. In einem Python-3.11+-Environment:

```bash
python -m pip install -e '.[studio]'
python -m adventure_studio.studio_gradio
```

Die **Projektübersicht** zeigt die Story als Katalog und Beziehungsgraph:
Kapitel, Szenen, Charaktere, Gegenstände samt Positionen, Rätsel,
Inventarbedingungen und Rezeptkombinationen. Eine Galerie zeigt die
momentan deterministisch erzeugten Raumhintergründe. Nach der Bestätigung
eines Edits wird die gesamte Übersicht aus dem neuen Storymodell
aktualisiert. Das ist eine reine Lesesicht; sie fügt keine zweite Datenhaltung
hinzu. Das Storyformat v4 enthält jetzt Dialogknoten, Antwortverzweigungen
und referenzierte Bilder und Sprachclips. Die Übersicht zeigt diese Daten,
aber die Binärbilder werden noch nicht geladen. Der eigentliche SCUMM-Export
unterstützt **erste lineare Gespräche und experimentelle Antwortauswahl**: Die Figur erscheint
als anklickbarer Platzhalter-Hotspot und über „Talk to“ wird zeilenweise
Text angezeigt (noch als Ego-Text, keine echte NPC-Sprechblase). Bei einer
Auswahl werden bis zu drei Antwortobjekte im Raum ein-/ausgeblendet.
Die tatsächliche ScummVM-Bedienbarkeit dieser neuen Antworten muss noch
getestet werden. Verschachtelte Dialoge und externe Bild-/Sprach-Assets melden eine explizite
Exportwarnung. Alte
Story-Dateien v1/v2/v3 bleiben vollständig lesbar.
Im Reiter **Dialogzeilen** lassen sich vorhandene Sprechtexte bearbeiten;
neue Gespräche und Antwortverzweigungen entstehen als geprüfte
KI-Operationsvorschläge.

Gradio öffnet eine lokale Oberfläche im Browser. Die Offline-Bearbeitung
braucht weiterhin weder ComfyUI noch einen API-Key.
Du kannst eine vorhandene Story-JSON laden, Kapitel und Szenen prüfen,
Szenentitel und -texte bearbeiten, Gegenstände umbenennen, Dekorationen
hinzufügen, Rätseltitel und benötigte Inventargegenstände bearbeiten und
eine Raumvorschau mit Hotspots anzeigen. Du kannst physische Gegenstände
per Klick in die Raumvorschau oder durch X/Y-Eingabe positionieren. Die
Koordinaten werden mit stabilen IDs im **versionierten Story-JSON v3**
gespeichert; vorhandene Storys v1/v2 bleiben kompatibel. Jede Änderung läuft
durch den Story-Solver und den SCUMM-Adapter. Ungültige Änderungen werden
abgewiesen. Erst **Änderung prüfen** zeigt den deterministischen Bericht,
danach übernimmt **Geprüfte Änderung jetzt übernehmen** die geprüfte Version.
Über **Geprüfte Story
exportieren** lädst du die aktuelle JSON-Datei herunter. Änderungen bleiben
bis dahin nur in der laufenden Sitzung und überschreiben keine Projektdateien.

Im Reiter **KI-Story-Regie** lassen sich Änderungswünsche frei formulieren.
Optional kann das Studio daraus über die OpenAI Responses API strukturierte
Story-Operationen erzeugen. Die KI schreibt **keinen** SCUMM-/Python-Code und
verändert die Story nicht direkt: Ein typisierter JSON-Parser, der Story-Solver,
die Konsolidierung und der SCUMM-Adapter prüfen den *gesamten* Vorschlag.
Der Änderungsbericht zeigt alle hinzugefügten, entfernten und geänderten
Elemente. Erst die ausdrückliche Bestätigung übernimmt ihn. Gegen einen
inzwischen geänderten Story-Stand lässt sich eine alte Vorschau nicht anwenden.

KI-Zugriff ist opt-in und kann API-Kosten verursachen. Für diese Funktion:

```bash
python -m pip install -e '.[studio,ai]'
export OPENAI_API_KEY='DEIN_EIGENER_SCHLUESSEL'
python -m adventure_studio.studio_gradio
```

Den Schlüssel als Umgebungsvariable bzw. Secret einrichten, **niemals ins
Repository committen**. Über `ADVENTURE_STUDIO_AI_MODEL` lässt sich das
Modell konfigurieren (Standard `gpt-4.1-mini`). Der Story-Text wird nur bei
Betätigung des KI-Buttons an den Anbieter übertragen; die API-Anfrage setzt
`store=false`. Andere Generatoren können ihre deklarativen JSON-Operationen
über den Importbereich derselben UI zur Prüfung einreichen. Ohne API-Schlüssel
bleiben alle bisherigen lokalen Editierfunktionen nutzbar. Die Anbindung an
ComfyUI bleibt weiterhin ausdrücklich aus.

Unter **Spielbares SCUMM-ZIP erzeugen** kann der Editor außerdem die Story
mit der **in Codespaces automatisch eingerichteten** oder einer lokal
vorhandenen ScummC-Toolchain in ein ZIP exportieren. In Codespaces ist der
Compilerpfad vorbelegt; lokal kannst du das Verzeichnis eingeben. Beim
eigentlichen Export erfolgen **keine** Downloads.
Die Tools und ihr GPL-Beispielprojekt werden in ein temporäres Arbeitsverzeichnis
kopiert, bevor Ressourcen erzeugt werden; die Originalinstallation wird
nicht geändert. Das ZIP enthält `tentacle.000`, `tentacle.001`, `story.json`
und eine Startanleitung. Die verwendete DOTT-Identität ist weiterhin nur
ein Forschungs-Kompatibilitätstrick, keine eigene ScummVM-Spielerkennung.

Noch nicht enthalten: mehrstufiger KI-Chat, Echtzeit-ScummVM-Spielvorschau, frei ziehbare
Objektsprites und automatisches ComfyUI. Die Vorschau verwendet
bewusst die bisherigen technischen Platzhaltergrafiken.

