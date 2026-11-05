"""UI-independent story editing facade; all changes use the existing validator.

The GUI and future MCP adapter share these functions. No generated runtime
scripts, persistence side-effects or AI-generated source code live here.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .story import Item, Placement, Story, verify_story
from .story_changes import PutEntity, StoryChangeReport, edit_story
from .story_document import canonical_story_json, parse_story_document
from .story_to_scumm import compile_story_to_scumm
from .story_localization import story_translation_template_json


def export_warning(story: Story) -> str:
    """Allow new authoring concepts while never silently dropping them on export."""
    try:
        compile_story_to_scumm(story)
    except ValueError as error:
        if story.characters or story.dialogues or story.dialogue_nodes or story.dialogue_choices or story.assets:
            return f"SCUMM-Export noch nicht möglich: {error}"
        raise
    return ""


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
    changed, report = edit_story(story, (operation,))
    # Prevent accepting a locally valid story which the bounded SCUMM adapter
    # cannot yet export (e.g. more than four decorations in one room).
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


def change_dialogue_line(raw: str, node_id: str, text: str) -> StudioEdit:
    story = parse_story_document(raw)
    node = next((node for node in story.dialogue_nodes if node.id == node_id), None)
    if node is None:
        raise ValueError("Unknown dialogue node ID")
    if not text.strip() or len(text) > 4096:
        raise ValueError("Dialogue text must be 1..4096 characters")
    return _commit(story, PutEntity("dialogue_node", replace(node, text=text.strip())))


def item_position(raw: str, item_id: str) -> tuple[int, int]:
    story = parse_story_document(raw)
    item = next((i for i in story.items if i.id == item_id), None)
    if item is None or item.role == "crafted":
        raise ValueError("Position requires a physical item")
    game = compile_story_to_scumm(story)
    room = next((r for r in game.rooms if r.name == item.scene_id), None)
    hotspot = next((h for h in room.hotspots if h.id == item_id), None) if room else None
    if hotspot is None:
        raise ValueError("Item does not have a visible room hotspot")
    return hotspot.x, hotspot.y


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
    """Data-only preview; the optional UI layer chooses the image renderer."""
    story = parse_story_document(raw)
    game = compile_story_to_scumm(story)
    room = next((room for room in game.rooms if room.name == scene_id), None)
    if room is None:
        raise ValueError("Unknown or unsupported scene ID")
    hotspots = tuple((h.label, h.x, h.y, h.width, h.height) for h in room.hotspots)
    return room.geometry.room_width, room.geometry.room_height, room.pixels, room.palette, hotspots



def translation_draft(raw: str) -> str:
    """Generate an incomplete, validated-source translation draft for Studio."""
    story = parse_story_document(raw)
    game = compile_story_to_scumm(story)
    return story_translation_template_json(game)


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
