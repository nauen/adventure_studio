"""UI-independent story editing facade; all changes use the existing validator.

The GUI and future MCP adapter share these functions. No generated runtime
scripts, persistence side-effects or AI-generated source code live here.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .story import DialogueNode, DialogueChoice, Item, Placement, Story, verify_story
from .story_changes import PutEntity, StoryChangeReport, edit_story
from .story_document import canonical_story_json, parse_story_document
from .story_to_scumm import compile_story_to_scumm
from .export_compatibility import ExportCompatibility, assess_export, format_export_warning
from .studio_preview import authoring_scene_preview, preview_positions
from .story_localization import story_authoring_template_json, validate_story_catalog
from .localization import canonical_catalog_json, charset_plan, parse_catalog


def export_warning(story: Story) -> str:
    """Report adapter limitations without rejecting valid authoring edits.

    The exporter itself still rejects unsupported stories; no content is
    silently omitted from a generated SCUMM game.
    """
    return format_export_warning(assess_export(story))


def assess_story_export(raw: str) -> ExportCompatibility:
    """Machine-readable target-specific blockers for Studio or future clients."""
    return assess_export(parse_story_document(raw))


@dataclass(frozen=True)
class StudioView:
    chapters: tuple[tuple[str, str], ...]
    scenes: tuple[tuple[str, str], ...]
    items: tuple[tuple[str, str, str], ...]
    puzzles: tuple[tuple[str, str], ...]
    playable_path: tuple[str, ...]


@dataclass(frozen=True)
class StudioEdit:
    story_json: str
    report: StoryChangeReport


@dataclass(frozen=True)
class StudioProposal:
    base_json: str
    edit: StudioEdit


def describe_story(raw: str) -> StudioView:
    story = parse_story_document(raw)
    return StudioView(
        chapters=tuple((chapter.id, chapter.title) for chapter in story.chapters),
        scenes=tuple((scene.id, scene.title) for scene in story.scenes),
        items=tuple((item.id, item.name, item.scene_id) for item in story.items),
        puzzles=tuple((puzzle.id, puzzle.title) for puzzle in story.puzzles),
        playable_path=verify_story(story),
    )


def _commit(story: Story, operation: PutEntity) -> StudioEdit:
    return _commit_many(story, (operation,))


def _commit_many(story: Story, operations: tuple[PutEntity, ...]) -> StudioEdit:
    changed, report = edit_story(story, operations)
    # Export support is a separate capability; authoring validity is checked
    # by edit_story and the strict JSON roundtrip below.
    warning = export_warning(changed)
    # UI output is again parsed by the same strict format boundary.
    canonical = canonical_story_json(changed)
    parse_story_document(canonical)
    return StudioEdit(canonical, replace(report, export_warning=warning))


def change_scene(raw: str, scene_id: str, title: str, description: str) -> StudioEdit:
    story = parse_story_document(raw)
    scene = next((scene for scene in story.scenes if scene.id == scene_id), None)
    if scene is None:
        raise ValueError("Unknown scene ID")
    if not title.strip() or not description.strip():
        raise ValueError("Scene title and description cannot be empty")
    return _commit(story, PutEntity("scene", replace(scene, title=title.strip(),
                                                     description=description.strip())))


def change_item(raw: str, item_id: str, name: str, description: str) -> StudioEdit:
    story = parse_story_document(raw)
    item = next((item for item in story.items if item.id == item_id), None)
    if item is None:
        raise ValueError("Unknown item ID")
    if not name.strip() or not description.strip():
        raise ValueError("Item name and description cannot be empty")
    return _commit(story, PutEntity("item", replace(item, name=name.strip(),
                                                   description=description.strip())))


def add_decoration(raw: str, scene_id: str, item_id: str,
                   name: str, description: str) -> StudioEdit:
    story = parse_story_document(raw)
    if scene_id not in {scene.id for scene in story.scenes}:
        raise ValueError("Unknown scene ID")
    if not item_id.isascii() or not item_id.isidentifier() or not item_id[0].isalpha():
        raise ValueError("Object ID must start with a letter and contain only ASCII letters, digits or _")
    if any(item.id == item_id for item in story.items):
        raise ValueError("Object ID already exists")
    if not name.strip() or not description.strip():
        raise ValueError("Object name and description cannot be empty")
    item = Item(item_id, name.strip(), description.strip(), scene_id, "decoration")
    return _commit(story, PutEntity("item", item))


def change_puzzle(raw: str, puzzle_id: str, title: str,
                  required_item_ids: tuple[str, ...]) -> StudioEdit:
    story = parse_story_document(raw)
    puzzle = next((puzzle for puzzle in story.puzzles if puzzle.id == puzzle_id), None)
    if puzzle is None:
        raise ValueError("Unknown puzzle ID")
    if not title.strip() or not required_item_ids or any(not item_id.strip() for item_id in required_item_ids):
        raise ValueError("Puzzle needs a title and at least one required item")
    return _commit(story, PutEntity("puzzle", replace(puzzle, title=title.strip(),
                                                      requires=required_item_ids)))


def change_dialogue_line(raw: str, node_id: str, text: str,
                         speaker_id: str | None = None) -> StudioEdit:
    story = parse_story_document(raw)
    node = next((node for node in story.dialogue_nodes if node.id == node_id), None)
    if node is None:
        raise ValueError("Unknown dialogue node ID")
    if not text.strip() or len(text) > 4096:
        raise ValueError("Dialogue text must be 1..4096 characters")
    speaker = speaker_id if speaker_id is not None else node.speaker_id
    dialogue = next(d for d in story.dialogues if d.id == node.dialogue_id)
    if speaker not in {character.id for character in story.characters
                       if character.scene_id == dialogue.scene_id}:
        raise ValueError("Dialogue speaker must be a character in the same scene")
    return _commit(story, PutEntity("dialogue_node", replace(
        node, text=text.strip(), speaker_id=speaker)))


def change_dialogue_facing(raw: str, node_id: str, direction: str | None) -> StudioEdit:
    story = parse_story_document(raw)
    node = next((node for node in story.dialogue_nodes if node.id == node_id), None)
    if node is None:
        raise ValueError("Unknown dialogue node ID")
    if direction not in (None, "N", "E", "S", "W"):
        raise ValueError("Dialogue facing must be north, east, south, west or disabled")
    return _commit(story, PutEntity("dialogue_node", replace(node, face_direction=direction)))


def extend_dialogue_line(raw: str, node_id: str, new_node_id: str,
                         text: str, speaker_id: str | None = None) -> StudioEdit:
    """Append a spoken line to a terminal dialogue node (no answer required)."""
    story = parse_story_document(raw)
    parent = next((node for node in story.dialogue_nodes if node.id == node_id), None)
    if parent is None:
        raise ValueError("Unknown dialogue node ID")
    if parent.next_node_id is not None or any(choice.node_id == node_id
                                               for choice in story.dialogue_choices):
        raise ValueError("Only a terminal dialogue line can be extended")
    if (not isinstance(new_node_id, str) or not new_node_id.isascii()
            or not new_node_id.isidentifier() or not new_node_id[0].isalpha()
            or new_node_id in {node.id for node in story.dialogue_nodes}
            or not isinstance(text, str) or not text.strip() or len(text) > 4096):
        raise ValueError("New dialogue line requires a unique ASCII ID and text of 1..4096 characters")
    dialogue = next(d for d in story.dialogues if d.id == parent.dialogue_id)
    speaker = speaker_id if speaker_id is not None else parent.speaker_id
    if speaker not in {character.id for character in story.characters
                       if character.scene_id == dialogue.scene_id}:
        raise ValueError("Dialogue speaker must be a character in the same scene")
    node = DialogueNode(new_node_id, parent.dialogue_id, speaker, text.strip())
    return _commit_many(story, (PutEntity("dialogue_node", node),
                                PutEntity("dialogue_node", replace(parent, next_node_id=new_node_id))))


def add_dialogue_choice(raw: str, node_id: str, choice_id: str, text: str,
                        target_node_id: str | None = None) -> StudioEdit:
    """Offer a new answer, optionally returning to an existing dialogue stage."""
    story = parse_story_document(raw)
    node = next((item for item in story.dialogue_nodes if item.id == node_id), None)
    if node is None or node.next_node_id is not None:
        raise ValueError("Select a dialogue node without an automatic successor")
    if (not isinstance(choice_id, str) or not choice_id.isascii() or not choice_id.isidentifier()
            or not choice_id[0].isalpha() or choice_id in {choice.id for choice in story.dialogue_choices}
            or not isinstance(text, str) or not text.strip()):
        raise ValueError("Answer requires a new ASCII ID and non-empty text")
    if target_node_id == "":
        target_node_id = None
    if target_node_id is not None and (target_node_id not in {n.id for n in story.dialogue_nodes
                                                                if n.dialogue_id == node.dialogue_id}):
        raise ValueError("Answer target must be in the same dialogue")
    return _commit(story, PutEntity("dialogue_choice", DialogueChoice(
        choice_id, node_id, text.strip(), target_node_id)))


def change_dialogue_choice(raw: str, choice_id: str, text: str,
                           target_node_id: str | None) -> StudioEdit:
    """Edit an existing answer without changing its stable identity or parent."""
    story = parse_story_document(raw)
    choice = next((item for item in story.dialogue_choices if item.id == choice_id), None)
    if choice is None:
        raise ValueError("Unknown dialogue answer ID")
    if not isinstance(text, str) or not text.strip() or len(text) > 4096:
        raise ValueError("Answer text must be 1..4096 characters")
    if target_node_id == "":
        target_node_id = None
    parent = next(node for node in story.dialogue_nodes if node.id == choice.node_id)
    if target_node_id is not None and target_node_id not in {
            node.id for node in story.dialogue_nodes if node.dialogue_id == parent.dialogue_id}:
        raise ValueError("Answer target must be in the same dialogue")
    return _commit(story, PutEntity("dialogue_choice", replace(
        choice, text=text.strip(), next_node_id=target_node_id)))


def extend_dialogue_choice(raw: str, choice_id: str, new_node_id: str,
                           text: str, speaker_id: str | None = None) -> StudioEdit:
    """Atomically attach a new response node to a previously terminal answer."""
    story = parse_story_document(raw)
    choice = next((item for item in story.dialogue_choices if item.id == choice_id), None)
    if choice is None or choice.next_node_id is not None:
        raise ValueError("Select an answer without an existing target")
    if (not isinstance(new_node_id, str) or not new_node_id.isascii()
            or not new_node_id.isidentifier() or not new_node_id[0].isalpha()
            or new_node_id in {node.id for node in story.dialogue_nodes}
            or not isinstance(text, str) or not text.strip()):
        raise ValueError("New dialogue node requires a new ASCII ID and non-empty text")
    parent = next(node for node in story.dialogue_nodes if node.id == choice.node_id)
    dialogue = next(d for d in story.dialogues if d.id == parent.dialogue_id)
    speaker = speaker_id if speaker_id is not None else parent.speaker_id
    if speaker not in {character.id for character in story.characters
                       if character.scene_id == dialogue.scene_id}:
        raise ValueError("Dialogue speaker must be a character in the same scene")
    node = DialogueNode(new_node_id, parent.dialogue_id, speaker, text.strip())
    return _commit_many(story, (PutEntity("dialogue_node", node),
                                PutEntity("dialogue_choice", replace(choice, next_node_id=new_node_id))))


def item_position(raw: str, item_id: str) -> tuple[int, int]:
    story = parse_story_document(raw)
    item = next((i for i in story.items if i.id == item_id), None)
    if item is None or item.role == "crafted":
        raise ValueError("Position requires a physical item")
    # Explicit placements stay inspectable/editable even when the remaining
    # story exceeds the current export adapter's layout capabilities.
    placement = next((p for p in story.placements if p.item_id == item_id), None)
    if placement is not None:
        return placement.x, placement.y
    position = preview_positions(story, item.scene_id).get(item_id)
    if position is None:
        raise ValueError("Item does not have a visible room hotspot")
    return position


def change_position(raw: str, item_id: str, x: int, y: int) -> StudioEdit:
    story = parse_story_document(raw)
    if type(x) is not int or type(y) is not int:
        raise ValueError("Position requires integer coordinates")
    if not any(item.id == item_id and item.role != "crafted" for item in story.items):
        raise ValueError("Unknown physical item")
    return _commit(story, PutEntity("placement", Placement(item_id, x, y)))


def prepare_proposal(raw: str, edit: StudioEdit) -> StudioProposal:
    """Pin the exact version against which an author reviewed the diff."""
    return StudioProposal(canonical_story_json(parse_story_document(raw)), edit)


def accept_proposal(raw: str, proposal: StudioProposal) -> str:
    """Reject stale previews; only the explicitly reviewed bytes are committed."""
    if canonical_story_json(parse_story_document(raw)) != proposal.base_json:
        raise ValueError("Story changed since preview; please review the edit again")
    parse_story_document(proposal.edit.story_json)
    return proposal.edit.story_json


def scene_preview(raw: str, scene_id: str) -> tuple[int, int, bytes, tuple[tuple[int, int, int], ...], tuple[tuple[str, int, int, int, int], ...]]:
    """Data-only authoring preview, independent from SCUMM exportability."""
    story = parse_story_document(raw)
    return authoring_scene_preview(story, scene_id)



def translation_draft(raw: str, source_language: str = "en") -> str:
    """Generate an incomplete, validated-source translation draft for Studio."""
    story = parse_story_document(raw)
    return story_authoring_template_json(story, source_language)



def validate_translation_draft(raw: str, translated_json: str) -> str:
    """Validate complete translations against the current story and charset."""
    story = parse_story_document(raw)
    game = compile_story_to_scumm(story)
    catalog = parse_catalog(translated_json)
    validate_story_catalog(game, catalog)
    charset_plan(catalog)
    return canonical_catalog_json(catalog)


def report_text(report: StoryChangeReport) -> str:
    """Human-readable and deterministic consolidation result."""
    labels = []
    for change in report.changes:
        action = "hinzugefügt" if change.before is None else "entfernt" if change.after is None else "geändert"
        labels.append(f"{action}: {change.kind} {change.id}")
    for removed in report.consolidated:
        labels.append(f"konsolidiert: {removed}")
    labels.append("Spielbarer Pfad: " + " → ".join(report.playable_path))
    if report.export_warning:
        labels.append("Hinweis: " + report.export_warning)
    return "\n".join(labels)
