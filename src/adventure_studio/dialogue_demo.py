"""Deterministic one-character/linear-dialogue SCUMM test fixture."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

from .story import Character, Dialogue, DialogueChoice, DialogueNode
from .story_document import canonical_story_json, parse_story_document, build_story_document


def dialogue_fixture(raw: str, choices: bool = False, nested: bool = False,
                     multispeaker: bool = False) -> str:
    story = parse_story_document(raw)
    if story.characters or story.dialogues or story.dialogue_nodes or story.dialogue_choices or story.assets:
        raise ValueError("Dialogue fixture requires an unmodified story")
    actor = Character("HarborKeeper", "Hafenwaechter", "Ein alter Waechter steht hier.",
                      story.starting_scene_id)
    greeting = Dialogue("HarborTalk", story.starting_scene_id, "HarborHello")
    nodes = (
        DialogueNode("HarborHello", greeting.id, actor.id, "Was suchst du hier?",
                     None if choices else "HarborHint"),
        DialogueNode("HarborHint", greeting.id, actor.id, "Der Schluessel liegt am Boden.", None),
    )
    if choices:
        nodes += (DialogueNode("HarborBye", greeting.id, actor.id, "Bis bald.", None),)
    options = ((DialogueChoice("AskKey", "HarborHello", "Ich suche einen Schluessel.", "HarborHint"),
                DialogueChoice("Goodbye", "HarborHello", "Auf Wiedersehen.", "HarborBye"))
               if choices else ())
    if nested:
        if not choices:
            raise ValueError("Nested dialogue needs choices")
        options += (DialogueChoice("AskAgain", "HarborHint", "Nochmal fragen.", "HarborHello"),
                    DialogueChoice("Finish", "HarborHint", "Das reicht.", None))
    if multispeaker:
        witness = Character("Witness", "Zeuge", "Ein Zeuge sieht zu.", story.starting_scene_id)
        nodes = tuple(replace(node, speaker_id="Witness") if node.id == "HarborHint" else node
                      for node in nodes)
    return canonical_story_json(replace(story, characters=(actor, witness) if multispeaker else (actor,),
                                        dialogues=(greeting,), dialogue_nodes=nodes,
                                        dialogue_choices=options))


def main() -> int:
    if (len(sys.argv) not in (3, 4)
            or (len(sys.argv) == 4 and sys.argv[3] not in ("--choices", "--nested", "--multispeaker", "--linear-multispeaker"))):
        print("Usage: python -m adventure_studio.dialogue_demo STORY.json OUTPUT_DIRECTORY [--choices|--nested|--multispeaker|--linear-multispeaker]")
        return 2
    raw = dialogue_fixture(Path(sys.argv[1]).read_text(encoding="utf-8"),
                           len(sys.argv) == 4 and sys.argv[3] != "--linear-multispeaker",
                           len(sys.argv) == 4 and sys.argv[3] == "--nested",
                           len(sys.argv) == 4 and sys.argv[3] in ("--multispeaker", "--linear-multispeaker"))
    output = Path(sys.argv[2])
    build_story_document(raw, output)
    (output / "story.json").write_text(raw, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
