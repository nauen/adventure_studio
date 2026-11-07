"""Pure dependency ordering for story-generated inventory gameplay."""

import unittest

from adventure_studio.scumm_recipe_plan import plan_recipes


def recipe(first: str, second: str, result: str) -> dict:
    def item(name: str) -> dict:
        return {"item_id": name, "rgb": [255, 220, 75]}
    return {"room_id": "Kitchen", "ingredients": [item(first), item(second)],
            "result": item(result)}


class RecipePlanTests(unittest.TestCase):
    def test_converging_four_recipes_in_arbitrary_manifest_order(self):
        final = recipe("Essence", "Crystal", "Elixir")
        catalyst = recipe("Herb", "Powder", "Catalyst")
        essence = recipe("Juice", "Catalyst", "Essence")
        juice = recipe("Pineapple", "Bottle", "Juice")
        self.assertEqual(plan_recipes([final, catalyst, essence, juice], "Elixir"),
                         (juice, catalyst, essence, final))

    def test_rejects_cycles_and_unrelated_recipes(self):
        with self.assertRaisesRegex(ValueError, "Cyclic"):
            plan_recipes([recipe("A", "B", "C"), recipe("C", "D", "A")], "C")
        with self.assertRaisesRegex(ValueError, "Unreachable"):
            plan_recipes([recipe("A", "B", "C"), recipe("D", "E", "F")], "C")
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            plan_recipes([recipe("A", "B", "C"), recipe("A", "D", "E")], "C")
        with self.assertRaisesRegex(ValueError, "not produced"):
            plan_recipes([recipe("A", "B", "C")], "Unknown")


if __name__ == "__main__":
    unittest.main()
