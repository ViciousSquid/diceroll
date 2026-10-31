"""Black-box tests that roll real dice with real Python RNG instances.

The golden outcomes below are deliberately literal: they detect a regression
where a roll changes while tests still pass by reimplementing the same bug.
"""

from __future__ import annotations

import random
import unittest
from dataclasses import FrozenInstanceError
from fractions import Fraction

from diceroll import DiceNotationError, DiceRoller, RollResult, probability_target, roll_check


class ActualRollOutputTests(unittest.TestCase):
    def test_seeded_standard_dice_have_exact_individual_faces_and_total(self):
        result = DiceRoller(rng=random.Random(0)).roll(
            "d4 + d6 + d8 + d10 + d12 + d20",
            target=39,
            d6_colour="blue",
        )
        self.assertEqual(result.faces, (4, 4, 1, 5, 9, 16))
        self.assertEqual(result.total, 39)
        self.assertEqual([c.total for c in result.components], [4, 4, 1, 5, 9, 16])
        self.assertEqual([c.notation for c in result.components],
                         ["1d4", "1d6", "1d8", "1d10", "1d12", "1d20"])
        self.assertTrue(result.success)
        self.assertEqual(result.components[1].colours, ("blue",))
        self.assertEqual(result.alternative_totals, ())

    def test_seeded_red_dice_and_modifier_exact_output(self):
        roll = DiceRoller(rng=random.Random(7)).roll("2d6+2", d6_colour="red", target=8)
        self.assertEqual(roll.faces, (3, 2))
        self.assertEqual(roll.total, 7)
        self.assertEqual(roll.modifier, 2)
        self.assertEqual(roll.components[0].total, 5)
        self.assertEqual(roll.components[0].colours, ("red", "red"))
        self.assertEqual(roll.components[1].faces, ())
        self.assertEqual(roll.components[1].total, 2)
        self.assertFalse(roll.success)

    def test_seeded_signed_rolls_have_correct_subtotals(self):
        result = DiceRoller(rng=random.Random(11)).roll(
            "2d4 - 3d6 + d12 + 5", d6_colour="white",
        )
        self.assertEqual(result.faces, (4, 4, 4, 5, 5, 4))
        self.assertEqual(result.total, 3)
        self.assertEqual(tuple(part.total for part in result.components),
                         (8, -14, 4, 5))
        self.assertEqual(result.modifier, 5)
        self.assertEqual(result.components[1].sign, -1)
        self.assertEqual(result.components[1].colours, ("white",) * 3)
        self.assertIsNone(result.success)

    def test_seeded_random_mixed_palette_and_exact_output(self):
        result = DiceRoller(rng=random.Random(21)).roll(
            "d20 + 5d6 + d8", d6_colour="random", target=37,
        )
        self.assertEqual(result.faces, (6, 4, 6, 4, 6, 3, 8))
        self.assertEqual(result.total, 37)
        self.assertEqual(result.components[1].colours,
                         ("red", "white", "blue", "red", "blue"))
        self.assertEqual(result.components[0].colours, (None,))
        self.assertEqual(result.components[2].colours, (None,))
        self.assertTrue(result.success)

    def test_seeded_advantage_is_one_published_roll_with_exact_winner(self):
        roller = DiceRoller(rng=random.Random(6))
        published = []
        roller.subscribe(published.append)
        result = roller.roll("2d6 + d20 + 3", mode="advantage", d6_colour="random")
        self.assertEqual(result.faces, (5, 1, 16))
        self.assertEqual(result.total, 25)
        self.assertEqual(result.alternative_totals, (8,))
        self.assertEqual(result.components[0].colours, ("red", "blue"))
        self.assertEqual(result.mode, "advantage")
        self.assertEqual(roller.history, (result,))
        self.assertEqual(published, [result])

    def test_seeded_disadvantage_is_one_published_roll_with_exact_loser(self):
        result = DiceRoller(rng=random.Random(1)).roll(
            "2d6 + d20 + 3", mode="disadvantage", d6_colour="random",
        )
        self.assertEqual(result.faces, (2, 5, 3))
        self.assertEqual(result.total, 13)
        self.assertEqual(result.alternative_totals, (23,))
        self.assertEqual(result.components[0].colours, ("white", "white"))
        self.assertEqual(result.mode, "disadvantage")

    def test_nonstandard_dice_have_exact_seeded_faces(self):
        result = DiceRoller(rng=random.Random(42)).roll("d100 + d7 + 2")
        self.assertEqual(result.faces, (82, 1))
        self.assertEqual(result.total, 85)
        self.assertEqual(result.components[0].colours, (None,))
        self.assertEqual(result.components[1].colours, (None,))

    def test_same_seed_replays_entire_sequence_on_multiple_independent_rollers(self):
        expression = "2d4+4d6-d8+d10+d12+d20+3"
        for seed in (-91, 0, 1, 2, 7, 19, 21, 42, 123456789):
            for colour in ("red", "white", "blue", "random"):
                with self.subTest(seed=seed, colour=colour):
                    a = DiceRoller(rng=random.Random(seed))
                    b = DiceRoller(rng=random.Random(seed))
                    one = [a.roll(expression, d6_colour=colour, mode=mode).to_dict()
                           for mode in ("normal", "advantage", "disadvantage")]
                    two = [b.roll(expression, d6_colour=colour, mode=mode).to_dict()
                           for mode in ("normal", "advantage", "disadvantage")]
                    self.assertEqual(one, two)

    def test_all_sided_dice_stay_within_bounds_across_real_seeds(self):
        for sides in (2, 3, 4, 6, 8, 10, 12, 20, 37, 100, 1000, 10000):
            for seed in (0, 1, 7, 42, 2026):
                with self.subTest(sides=sides, seed=seed):
                    result = DiceRoller(rng=random.Random(seed)).roll(f"7d{sides}")
                    self.assertEqual(len(result.faces), 7)
                    self.assertTrue(all(1 <= face <= sides for face in result.faces))
                    self.assertEqual(result.total, sum(result.faces))

    def test_mixed_roll_with_every_standard_die_and_both_signs(self):
        expr = "2d4+3d6+d8-d10+d12+d20-4"
        for seed in (0, 1, 2, 7, 42, 333):
            with self.subTest(seed=seed):
                result = DiceRoller(rng=random.Random(seed)).roll(
                    expr, d6_colour="random"
                )
                self.assertEqual(len(result.faces), 9)
                self.assertEqual(result.total, sum(c.total for c in result.components))
                self.assertEqual(result.modifier, -4)
                self.assertEqual([len(c.faces) for c in result.components],
                                 [2, 3, 1, 1, 1, 1, 0])
                self.assertEqual([c.sign for c in result.components],
                                 [1, 1, 1, -1, 1, 1, -1])
                self.assertEqual(len(result.components[1].colours), 3)
                self.assertTrue(all(color in ("red", "blue", "white")
                                    for color in result.components[1].colours))

    def test_every_fixed_colour_keeps_identical_faces_with_same_seed(self):
        expression = "3d6+d12-2d6+d20+10"
        for seed in (0, 1, 17, 42):
            results = {
                colour: DiceRoller(rng=random.Random(seed)).roll(
                    expression, d6_colour=colour
                )
                for colour in ("red", "white", "blue", "random")
            }
            faces = results["blue"].faces
            for colour, result in results.items():
                with self.subTest(seed=seed, colour=colour):
                    self.assertEqual(result.faces, faces)
                    self.assertEqual(result.total, results["blue"].total)
                    if colour != "random":
                        expected = (colour,) * 3
                        self.assertEqual(result.components[0].colours, expected)
                        self.assertEqual(result.components[2].colours, (colour,) * 2)

    def test_random_colour_consumes_rng_only_after_numeric_faces(self):
        baseline = DiceRoller(rng=random.Random(2026))
        random_palette = DiceRoller(rng=random.Random(2026))
        one = baseline.roll("5d6+d12", d6_colour="blue")
        two = random_palette.roll("5d6+d12", d6_colour="random")
        self.assertEqual(one.faces, two.faces)
        self.assertEqual(one.total, two.total)
        self.assertNotEqual(baseline.rng.getstate(), random_palette.rng.getstate())

    def test_success_failure_and_boundary_are_actual_d20_rolls(self):
        # random.Random(5) produces 20 and random.Random(2) produces 2.
        success = DiceRoller(rng=random.Random(5)).roll("1d20", target=20)
        failure = DiceRoller(rng=random.Random(2)).roll("1d20", target=20)
        self.assertEqual(success.faces, (20,))
        self.assertTrue(success.success)
        self.assertEqual(failure.faces, (2,))
        self.assertFalse(failure.success)
        self.assertTrue(DiceRoller(rng=random.Random(2)).roll("1d20", target=2).success)

    def test_zero_and_certain_checks_are_not_fudged(self):
        for sides in (6, 20, 100):
            with self.subTest(sides=sides):
                dice = DiceRoller(rng=random.Random(7))
                impossible = roll_check(dice, 0.0, sides=sides, label="Impossible")
                certain = roll_check(dice, 1.0, sides=sides, label="Certain")
                self.assertEqual(impossible.target, sides + 1)
                self.assertFalse(impossible.success)
                self.assertEqual(certain.target, 1)
                self.assertTrue(certain.success)
                self.assertEqual(impossible.context["label"], "Impossible")
                self.assertEqual(certain.context["chance"], 1.0)

    def test_result_is_frozen_and_callbacks_receive_real_object(self):
        roller = DiceRoller(rng=random.Random(0))
        received = []
        roller.subscribe(received.append)
        original_context = {"origin": "outside"}
        result = roller.roll("d20", source="integration", context=original_context)
        original_context["origin"] = "changed"
        self.assertEqual(result.context["origin"], "outside")
        self.assertIs(received[0], result)
        self.assertIsInstance(result, RollResult)
        with self.assertRaises(FrozenInstanceError):
            result.total = 999
        with self.assertRaises(TypeError):
            result.context["origin"] = "mutated"

    def test_history_has_accurate_order_and_does_not_count_discarded_attempt(self):
        roller = DiceRoller(rng=random.Random(4), history_limit=2)
        first = roller.roll("d6", d6_colour="red")
        second = roller.roll("d20+2", mode="advantage")
        third = roller.roll("2d4", mode="disadvantage")
        self.assertEqual(roller.history, (second, third))
        self.assertNotIn(first, roller.history)
        self.assertEqual(len(roller.history), 2)

    def test_rolls_never_implicitly_save_files(self):
        import os
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            previous = os.getcwd()
            try:
                os.chdir(tmp)
                dice = DiceRoller(rng=random.Random(2))
                for colour in ("blue", "red", "white", "random"):
                    dice.roll("3d6+d12", d6_colour=colour)
                self.assertEqual(list(Path(tmp).iterdir()), [])
                dice.save_history("history.json")
                self.assertTrue(Path("history.json").exists())
            finally:
                os.chdir(previous)

    def test_out_of_range_colours_and_modes_raise_before_consuming_rng(self):
        roller = DiceRoller(rng=random.Random(77))
        state = roller.rng.getstate()
        for kwargs in ({"d6_colour": "green"},
                       {"d6_colour": "Random"},
                       {"mode": "triple"},
                       {"target": True},
                       {"target": 8.5}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((ValueError, TypeError)):
                    roller.roll("2d6", **kwargs)
                self.assertEqual(roller.rng.getstate(), state)

    def test_parser_invalid_input_cannot_be_published(self):
        roller = DiceRoller()
        events = []
        roller.subscribe(events.append)
        with self.assertRaises(DiceNotationError):
            roller.roll("d6 + invalid")
        self.assertEqual(events, [])
        self.assertEqual(roller.history, ())


if __name__ == "__main__":
    unittest.main()
