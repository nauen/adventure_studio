"""Structured, non-mutating diagnostics for the bounded SCUMM-v6 adapter.

This is an adapter capability check, not a second story validator. Known
constraints are reported together; the actual compiler remains authoritative
and fails closed for cases the preflight does not yet recognize.
"""

from __future__ import annotations

from dataclasses import dataclass

from .story import Story
from .story_to_scumm import compile_story_to_scumm
from .targets import DEFAULT_TARGET


@dataclass(frozen=True)
class ExportBlocker:
    code: str
    entity_kind: str
    entity_id: str
    target_id: str
    reason: str


@dataclass(frozen=True)
class ExportCompatibility:
    target_id: str
    blockers: tuple[ExportBlocker, ...]

    @property
    def exportable(self) -> bool:
        return not self.blockers


def assess_export(story: Story) -> ExportCompatibility:
    """Return deterministic, typed known blockers and an explicit fallback.

    The fallback intentionally makes no claim about the nature of a compiler
    failure. We never classify a native limit by parsing exception messages.
    """
    target = DEFAULT_TARGET.id
    issues: list[ExportBlocker] = []

    def block(code: str, kind: str, id_: str, reason: str) -> None:
        issues.append(ExportBlocker(code, kind, id_, target, reason))

    for asset in story.assets:
        block("ASSET_REFERENCE_UNSUPPORTED", "asset", asset.id,
              "Versioned asset references are not supported by the current SCUMM adapter")

    if len(story.chapters) != 1:
        block("CHAPTER_ROUTE_UNSUPPORTED", "story", story.starting_scene_id,
              "Current exporter only handles one chapter")

    if story.recipes:
        if (len(story.scenes) != 2 or len(story.puzzles) != 1
                or story.characters):
            block("RECIPE_FIXTURE_TOPOLOGY", "story", story.starting_scene_id,
                  "Recipe adapter requires two scenes, one puzzle and no characters")
    elif not 1 <= len(story.puzzles) <= 2 or len(story.scenes) != len(story.puzzles) + 1:
        block("LINEAR_ROUTE_FIXTURE_LIMIT", "story", story.starting_scene_id,
              "Current door adapter needs one or two sequential puzzles and one extra scene")

    if not story.recipes:
        pickup_count = sum(len(p.requires) for p in story.puzzles)
        if pickup_count > 3:
            block("FIXTURE_PICKUP_PALETTE_LIMIT", "story", story.starting_scene_id,
                  f"Current fixture has three pickup colors; route requires {pickup_count}")

    for scene in story.scenes:
        decorations = [i for i in story.items if i.scene_id == scene.id and i.role == "decoration"]
        if len(decorations) > 4:
            block("AUTOMATIC_DECORATION_LAYOUT_LIMIT", "scene", scene.id,
                  f"Current automatic layout supports four decorations; found {len(decorations)}")

    # The demo adapter renders the final destination at 320px, other rooms
    # at 640px; this is a fixture decision, not an SCUMM-native limit.
    final = next((p for p in story.puzzles if p.id == story.final_puzzle_id), None)
    goal_id = final.opens_scene_id if final else None
    placements = {p.item_id: p for p in story.placements}
    for item in story.items:
        placement = placements.get(item.id)
        if placement is None:
            continue
        width = 320 if item.scene_id == goal_id else 640
        if placement.x + 16 > width or placement.y + 16 > 200:
            block("FIXTURE_ROOM_GEOMETRY", "item", item.id,
                  f"16px hotspot at ({placement.x}, {placement.y}) exceeds {width}x200 export room")

    for node in story.dialogue_nodes:
        choices = [choice for choice in story.dialogue_choices if choice.node_id == node.id]
        if len(choices) > 3:
            block("DIALOGUE_CHOICE_LAYOUT_LIMIT", "dialogue_node", node.id,
                  f"Current automatic dialogue layout supports three choices; found {len(choices)}")

    for scene in story.scenes:
        width = 320 if scene.id == goal_id else 640
        actors = [c for c in story.characters if c.scene_id == scene.id]
        if actors and 185 + (len(actors) - 1) * 35 + 16 > width:
            block("AUTOMATIC_CHARACTER_LAYOUT_LIMIT", "scene", scene.id,
                  f"Current character layout does not fit {len(actors)} actors in {width}px")

    try:
        compile_story_to_scumm(story)
    except ValueError as error:
        # A compiler-specific reason may complement the known blockers, but
        # cannot safely be assigned a specific category without inspection.
        if not issues:
            block("ADAPTER_REJECTED", "story", story.starting_scene_id, str(error))

    return ExportCompatibility(target, tuple(issues))


def format_export_warning(assessment: ExportCompatibility) -> str:
    if assessment.exportable:
        return ""
    descriptions = "; ".join(
        f"{issue.code} [{issue.entity_kind}:{issue.entity_id}]: {issue.reason}"
        for issue in assessment.blockers)
    return f"SCUMM-Export noch nicht möglich ({assessment.target_id}): {descriptions}"
