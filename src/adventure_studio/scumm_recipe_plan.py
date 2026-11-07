"""Deterministic recipe dependency planning for ScummVM gameplay probes."""

from __future__ import annotations


def plan_recipes(combinations: list[dict], required_item_id: str) -> tuple[dict, ...]:
    """Topologically order all required recipes, rejecting ambiguous graphs.

    Inputs follow the exported fixture manifest: two ingredient dictionaries
    and one result dictionary, each with an ``item_id`` and palette RGB.
    This function only chooses an order; live inventory state is checked by
    the emulator runner before each operation.
    """
    if not combinations or not isinstance(required_item_id, str) or not required_item_id:
        raise ValueError("Recipe plan needs combinations and a required result")
    producers: dict[str, dict] = {}
    consumed: set[str] = set()
    for combination in combinations:
        if (not isinstance(combination, dict)
                or set(combination) != {"room_id", "ingredients", "result"}
                or not isinstance(combination["ingredients"], list)
                or len(combination["ingredients"]) != 2):
            raise ValueError("Invalid recipe plan manifest")
        inputs = [item.get("item_id") if isinstance(item, dict) else None
                  for item in combination["ingredients"]]
        result = combination["result"].get("item_id") if isinstance(combination["result"], dict) else None
        if (not isinstance(result, str) or not result
                or any(not isinstance(item, str) or not item for item in inputs)
                or len(set((*inputs, result))) != 3
                or result in producers
                or any(item in consumed for item in inputs)):
            raise ValueError("Ambiguous recipe inputs or result")
        producers[result] = combination
        consumed.update(inputs)

    ordered: list[dict] = []
    active: set[str] = set()
    completed: set[str] = set()

    def visit(item_id: str) -> None:
        if item_id in active:
            raise ValueError("Cyclic recipe dependency")
        if item_id in completed or item_id not in producers:
            return
        active.add(item_id)
        recipe = producers[item_id]
        for ingredient in recipe["ingredients"]:
            visit(ingredient["item_id"])
        active.remove(item_id)
        completed.add(item_id)
        ordered.append(recipe)

    if required_item_id not in producers:
        raise ValueError("Final puzzle item is not produced by a recipe")
    visit(required_item_id)
    if len(ordered) != len(combinations):
        raise ValueError("Unreachable recipe is not part of the final solution")
    return tuple(ordered)
