"""Deterministic read-only story inventory and relationship graph for any UI."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape

from .story_document import parse_story_document


@dataclass(frozen=True)
class StudioCatalog:
    chapters: tuple[tuple[str, str, str], ...]
    scenes: tuple[tuple[str, str, str, str], ...]
    characters: tuple[tuple[str, str, str, str], ...]
    items: tuple[tuple[str, str, str, str, str], ...]
    puzzles: tuple[tuple[str, str, str, str, str], ...]
    recipes: tuple[tuple[str, str, str, str], ...]
    dialogues: tuple[tuple[str, str, str], ...]
    dialogue_nodes: tuple[tuple[str, str, str, str, str], ...]
    dialogue_choices: tuple[tuple[str, str, str, str], ...]
    assets: tuple[tuple[str, str, str, str, str], ...]
    edges: tuple[tuple[str, str, str, str, str], ...]


def story_catalog(raw: str) -> StudioCatalog:
    story = parse_story_document(raw)
    positions = {p.item_id: (p.x, p.y) for p in story.placements}
    chapters = tuple((c.id, c.title, c.synopsis) for c in story.chapters)
    scenes = tuple((s.id, s.title, s.chapter_id, s.description) for s in story.scenes)
    portrait_ids = {a.target_id for a in story.assets if a.target_kind == "character" and a.asset_kind == "portrait"}
    characters = tuple((c.id, c.name, c.scene_id, "Asset-Referenz vorhanden" if c.id in portrait_ids else "Kein Charakterbild zugeordnet")
                       for c in story.characters)
    items = tuple((i.id, i.name, i.scene_id, i.role,
                   f"{positions[i.id][0]}, {positions[i.id][1]}" if i.id in positions else "automatisch")
                  for i in story.items)
    puzzles = tuple((p.id, p.title, p.scene_id, ", ".join(p.requires),
                     p.opens_scene_id or "–") for p in story.puzzles)
    recipes = tuple((r.id, r.title, " + ".join(r.ingredients), r.result_item_id)
                    for r in story.recipes)
    dialogues = tuple((d.id, d.scene_id, d.entry_node_id) for d in story.dialogues)
    nodes = tuple((n.id, n.dialogue_id, n.speaker_id, n.text, n.next_node_id or "–")
                  for n in story.dialogue_nodes)
    choices = tuple((c.id, c.node_id, c.text, c.next_node_id or "Ende")
                    for c in story.dialogue_choices)
    assets = tuple((a.id, a.target_kind, a.target_id, a.asset_kind, a.source_id)
                   for a in story.assets)
    edges: list[tuple[str, str, str, str, str]] = []
    for s in story.scenes:
        edges.append(("chapter", s.chapter_id, "scene", s.id, "enthält"))
    for c in story.characters:
        edges.append(("scene", c.scene_id, "character", c.id, "Figur"))
    for i in story.items:
        edges.append(("scene", i.scene_id, "item", i.id, "liegt in"))
    for p in story.puzzles:
        edges.append(("scene", p.scene_id, "puzzle", p.id, "Rätsel"))
        for item_id in p.requires:
            edges.append(("item", item_id, "puzzle", p.id, "benötigt"))
        if p.opens_scene_id:
            edges.append(("puzzle", p.id, "scene", p.opens_scene_id, "öffnet"))
    for r in story.recipes:
        for item_id in r.ingredients:
            edges.append(("item", item_id, "recipe", r.id, "Zutat"))
        edges.append(("recipe", r.id, "item", r.result_item_id, "erzeugt"))
    for dialogue in story.dialogues:
        edges.append(("scene", dialogue.scene_id, "dialogue", dialogue.id, "Gespräch"))
        edges.append(("dialogue", dialogue.id, "dialogue_node", dialogue.entry_node_id, "beginnt"))
    for node in story.dialogue_nodes:
        edges.append(("character", node.speaker_id, "dialogue_node", node.id, "spricht"))
        if node.next_node_id:
            edges.append(("dialogue_node", node.id, "dialogue_node", node.next_node_id, "weiter"))
    for choice in story.dialogue_choices:
        edges.append(("dialogue_node", choice.node_id, "dialogue_choice", choice.id, "Antwort"))
        if choice.next_node_id:
            edges.append(("dialogue_choice", choice.id, "dialogue_node", choice.next_node_id, "führt zu"))
    for asset in story.assets:
        edges.append(("asset", asset.id, asset.target_kind, asset.target_id, "zugeordnet"))
    return StudioCatalog(chapters, scenes, characters, items, puzzles, recipes,
                         dialogues, nodes, choices, assets, tuple(edges))


def relationship_svg(raw: str) -> str:
    """Static, escaped SVG without third-party graph engines or script execution."""
    story = parse_story_document(raw)
    catalog = story_catalog(raw)
    types = (
        ("chapter", [(c.id, c.title) for c in story.chapters], 15, "#e0edff"),
        ("scene", [(s.id, s.title) for s in story.scenes], 235, "#def8e7"),
        ("character", [(c.id, c.name) for c in story.characters], 455, "#f1e5ff"),
        ("item", [(i.id, i.name) for i in story.items], 675, "#fff0cf"),
        ("puzzle", [(p.id, p.title) for p in story.puzzles], 895, "#ffe2df"),
        ("recipe", [(r.id, r.title) for r in story.recipes], 1115, "#e5f7fb"),
        ("dialogue", [(d.id, d.id) for d in story.dialogues], 1335, "#fae8ff"),
        ("dialogue_node", [(n.id, n.text) for n in story.dialogue_nodes], 1555, "#ecefff"),
        ("dialogue_choice", [(c.id, c.text) for c in story.dialogue_choices], 1775, "#fff2db"),
        ("asset", [(a.id, a.asset_kind) for a in story.assets], 1995, "#e2f6ed"),
    )
    width = 2210
    max_rows = max((len(rows) for _, rows, _, _ in types), default=0)
    height = max(145, 90 + 62 * max_rows)
    nodes: dict[tuple[str, str], tuple[int, int]] = {}
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Story-Beziehungsgraph" viewBox="0 0 {width} {height}" width="100%">',
           f'<rect width="{width}" height="{height}" fill="#fafafa"/>',
           '<defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6" fill="#64748b"/></marker></defs>']
    node_svg = []
    for kind, rows, x, color in types:
        node_svg.append(f'<text x="{x+8}" y="28" font-size="17" font-weight="bold" fill="#26374c">{escape(kind)}</text>')
        for index, (id_, title) in enumerate(rows):
            y = 48 + index * 62
            nodes[(kind, id_)] = (x, y)
            node_svg.append(f'<rect x="{x}" y="{y}" width="200" height="48" rx="7" fill="{color}" stroke="#8492a6"/>')
            node_svg.append(f'<title>{escape(kind)}: {escape(id_)} – {escape(title)}</title>')
            node_svg.append(f'<text x="{x+8}" y="{y+20}" font-size="13" fill="#172338">{escape(title[:26])}</text>')
            node_svg.append(f'<text x="{x+8}" y="{y+37}" font-size="10" fill="#475569">{escape(id_[:30])}</text>')
    for from_kind, from_id, to_kind, to_id, relation in catalog.edges:
        start = nodes.get((from_kind, from_id))
        end = nodes.get((to_kind, to_id))
        if not start or not end:
            continue
        sx, sy = start[0] + 100, start[1] + 24
        tx, ty = end[0] + 100, end[1] + 24
        svg.append(f'<path d="M{sx},{sy} L{tx},{ty}" fill="none" stroke="#64748b" stroke-width="1.4" opacity="0.65" marker-end="url(#arrow)"><title>{escape(from_id)} → {escape(to_id)} ({escape(relation)})</title></path>')
    # Render links behind the nodes so overlapping edges cannot hide labels.
    return "".join(svg + node_svg) + "</svg>"
