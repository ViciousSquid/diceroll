"""Verify real exact probabilities against independent exhaustive enumeration."""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
from itertools import product
import random
import unittest

from diceroll import DiceNotationError, DiceRoller, probability_target, roll_check


def independent_brute_force(specification):
    """Enumerate independent Cartesian products, not the library's DP.

    Each specification entry is (sign, count, sides, constant). The expected
    answer deliberately does *not* call the production parser or distribution.
    """
    dice = [(sign, sides) for sign, count, sides, _ in specification
            if sides for _ in range(count)]
    modifier = sum(sign * constant for sign, _, sides, constant
                   in specification if sides == 0)
    outcomes = Counter(
        modifier + sum(sign * face for (sign, _), face in zip(dice, sample))
        for sample in product(*(range(1, sides + 1) for _, sides in dice))
    )
    denominator = sum(outcomes.values())
    return {total: Fraction(ways, denominator)
            for total, ways in sorted(outcomes.items())}


class ProbabilityEngineTests(unittest.TestCase):
    def test_all_small_mixed_expressions_match_exhaustive_probability_oracle(self):
        cases = [
            ("d2", [(1, 1, 2, 0)]),
            ("2d4", [(1, 2, 4, 0)]),
            ("d20-d4+2", [(1, 1, 20, 0), (-1, 1, 4, 0), (1, 0, 0, 2)]),
            ("2d6-1d8+3", [(1, 2, 6, 0), (-1, 1, 8, 0), (1, 0, 0, 3)]),
            ("d2+d3-d4+2", [
                (1, 1, 2, 0), (1, 1, 3, 0), (-1, 1, 4, 0), (1, 0, 0, 2),
            ]),
            ("d6+d6-2d4+5", [
                (1, 1, 6, 0), (1, 1, 6, 0), (-1, 2, 4, 0), (1, 0, 0, 5),
            ]),
        ]
        roller = DiceRoller(rng=random.Random(123))
        before = roller.rng.getstate()
        for expression, specification in cases:
            with self.subTest(expression=expression):
                expected = independent_brute_force(specification)
                actual = roller.distribution(expression)
                self.assertEqual(actual, expected)
                self.assertEqual(sum(actual.values()), Fraction(1, 1))
                self.assertTrue(all(isinstance(value, Fraction)
                                    for value in actual.values()))
        self.assertEqual(roller.rng.getstate(), before)
        self.assertEqual(roller.history, ())

    def test_all_six_standard_die_types_are_uniform(self):
        roller = DiceRoller()
        for sides in (4, 6, 8, 10, 12, 20):
            with self.subTest(sides=sides):
                distribution = roller.distribution(f"1d{sides}")
                self.assertEqual(
                    distribution,
                    {face: Fraction(1, sides) for face in range(1, sides + 1)},
                )

    def test_nonstandard_die_is_uniform_without_any_artwork(self):
        result = DiceRoller().distribution("d7")
        self.assertEqual(result, {face: Fraction(1, 7) for face in range(1, 8)})

    def test_negative_sign_reflects_outcomes_without_changing_probability(self):
        roller = DiceRoller()
        positive = roller.distribution("2d6")
        negative = roller.distribution("-2d6")
        self.assertEqual(negative, {-total: probability
                                    for total, probability in positive.items()})

    def test_modifier_shifts_the_distribution(self):
        roller = DiceRoller()
        ordinary = roller.distribution("d20+d4")
        shifted = roller.distribution("d20+d4+5-2")
        self.assertEqual(shifted, {total+3: probability
                                   for total, probability in ordinary.items()})

    def test_distribution_is_observationally_pure_for_arbitrary_sequences(self):
        a = DiceRoller(rng=random.Random(999))
        b = DiceRoller(rng=random.Random(999))
        received = []
        a.subscribe(received.append)
        a.distribution("2d4+d6-d8+2")
        self.assertEqual(a.history, ())
        self.assertEqual(received, [])
        self.assertEqual(a.roll("2d6+d20"), b.roll("2d6+d20"))

    def test_computation_budget_rejects_expensive_distribution(self):
        roller = DiceRoller(rng=random.Random(4))
        before = roller.rng.getstate()
        with self.assertRaises(ValueError):
            roller.distribution("1000d1000")
        self.assertEqual(roller.history, ())
        self.assertEqual(roller.rng.getstate(), before)

    def test_invalid_distribution_notation_raises(self):
        for expression in ("", "d1", "1d8 + bad", "2d6*4"):
            with self.subTest(expression=expression):
                with self.assertRaises(DiceNotationError):
                    DiceRoller().distribution(expression)

    def test_simulated_statistics_match_independent_seeded_roll_stream(self):
        expression = "2d4+d20-3"
        for trials in (1, 10, 100, 1000):
            with self.subTest(trials=trials):
                seed = 314159
                expected_rng = random.Random(seed)
                totals = [
                    expected_rng.randint(1, 4) + expected_rng.randint(1, 4)
                    + expected_rng.randint(1, 20) - 3
                    for _ in range(trials)
                ]
                roller = DiceRoller(rng=random.Random(seed))
                received = []
                roller.subscribe(received.append)
                stats = roller.statistics(expression, trials)
                self.assertEqual(stats["trials"], trials)
                self.assertEqual(stats["mean"], sum(totals) / trials)
                self.assertEqual(stats["min"], min(totals))
                self.assertEqual(stats["max"], max(totals))
                self.assertEqual(stats["frequency"], dict(sorted(Counter(totals).items())))
                self.assertEqual(roller.rng.getstate(), expected_rng.getstate())
                self.assertEqual(roller.history, ())
                self.assertEqual(received, [])

    def test_exact_distributions_and_sampling_have_distinct_rng_effects(self):
        roller = DiceRoller(rng=random.Random(101))
        before = roller.rng.getstate()
        roller.distribution("d20")
        self.assertEqual(roller.rng.getstate(), before)
        roller.statistics("d20", 20)
        self.assertNotEqual(roller.rng.getstate(), before)

    def test_sampling_trials_must_be_valid(self):
        for invalid in (0, -1, 100001, 1.5, "2"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    DiceRoller().statistics("d6", invalid)

    def test_target_quantisation_across_various_sides(self):
        for sides in (4, 6, 8, 10, 12, 20, 100):
            for success_faces in range(sides + 1):
                with self.subTest(sides=sides, wins=success_faces):
                    chance = success_faces / sides
                    target = probability_target(chance, sides)
                    self.assertEqual(target, sides - success_faces + 1)

    def test_probability_target_rejects_nonfinite_outside_unit_interval(self):
        for invalid in (float("inf"), float("-inf"), float("nan"),
                        -0.1, 1.01):
            with self.subTest(chance=invalid):
                with self.assertRaises(ValueError):
                    probability_target(invalid)
        for invalid_sides in (1, 0, -1, True, "20", 8.4):
            with self.subTest(sides=invalid_sides):
                with self.assertRaises(ValueError):
                    probability_target(0.5, invalid_sides)

    def test_real_rounded_skill_checks_include_actual_dice_rolls(self):
        for seed in (0, 1, 2, 5, 7, 42):
            for sides in (4, 6, 8, 10, 12, 20, 100):
                with self.subTest(seed=seed, sides=sides):
                    checker = DiceRoller(rng=random.Random(seed))
                    result = roll_check(
                        checker, 0.35, sides=sides, label="Bridge",
                        source="integrations.check",
                        context={"terrain": "wet"},
                    )
                    actual_face = random.Random(seed).randint(1, sides)
                    self.assertEqual(result.faces, (actual_face,))
                    self.assertEqual(result.target, probability_target(0.35, sides))
                    self.assertEqual(result.success, actual_face >= result.target)
                    self.assertEqual(result.context["terrain"], "wet")
                    self.assertEqual(result.context["chance"], 0.35)
                    self.assertEqual(result.context["label"], "Bridge")
                    self.assertEqual(result.source, "integrations.check")
                    self.assertEqual(checker.history, (result,))


if __name__ == "__main__":
    unittest.main()
