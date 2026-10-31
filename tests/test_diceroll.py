"""Regression and compatibility tests for the standalone library."""

import importlib
import io
import json
import math
import os
import random
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from diceroll import (
    DiceNotationError, DiceRoller, parse_dice_notation,
    probability_target, roll_check,
)
from diceroll_api import DiceAPI, DiceType, dicerollAPI


class DiceParserTests(unittest.TestCase):
    def test_signed_terms_and_shorthand(self):
        terms, original = parse_dice_notation("d20 + 2D6 - 3")
        self.assertEqual(original, "d20 + 2D6 - 3")
        self.assertEqual(
            [(t.sign, t.count, t.sides, t.modifier) for t in terms],
            [(1, 1, 20, 0), (1, 2, 6, 0), (-1, 0, 0, 3)],
        )

    def test_invalid_expressions_rejected(self):
        for notation in (
            "", "1d20oops", "1d6+", "2d", "d1", "0d6",
            "1d6++3", "1d6 -- 2", "2d6*3", "4",
            "1d6+1d0", "1d6+0d6", "1d6+1d99999",
            "1d6+" + "2" * 4000,
        ):
            with self.subTest(notation=notation[:40]):
                with self.assertRaises(DiceNotationError):
                    parse_dice_notation(notation)

    def test_safety_limits(self):
        with self.assertRaises(DiceNotationError):
            parse_dice_notation("1001d6")
        with self.assertRaises(DiceNotationError):
            parse_dice_notation("+".join(["100d6"] * 101))


class DiceRollerTests(unittest.TestCase):
    def test_seed_and_modifiers(self):
        roller = DiceRoller(rng=random.Random(7))
        result = roller.roll_dice("2d6+2")
        self.assertEqual(result["roll_details"], [3, 2])
        self.assertEqual(result["roll_result"], 7)
        self.assertEqual(result["modifier"], 2)
        self.assertEqual(len(result["components"]), 2)
        self.assertEqual(result["components"][1]["roll_result"], 2)

    def test_negative_dice_and_outcomes(self):
        roller = DiceRoller(rng=random.Random(2))
        result = roller.roll_dice("1d20-1d4+10", target=25)
        self.assertEqual(result["roll_result"], sum(
            c["roll_result"] for c in result["components"]
        ))
        self.assertEqual(result["success"], result["roll_result"] >= 25)

    def test_outcome_dict_is_not_mutated(self):
        failure = {"message": "try again"}
        success = {"message": "yes"}
        roller = DiceRoller(rng=random.Random(10))
        result = roller.roll_dice("1d6", target=99,
                                  success_outcome=success, failure_outcome=failure)
        self.assertNotIn("roll_result", failure)
        self.assertEqual(result["outcome"]["message"], "try again")

    def test_listener_events_and_isolation(self):
        roller = DiceRoller()
        events = []

        def faulty(*_args):
            raise RuntimeError("subscriber failed")

        def record(result, source, context):
            events.append((result, source, context))

        roller.add_roll_listener(faulty)
        roller.add_roll_listener(record)
        with self.assertLogs("diceroll", level="ERROR"):
            result = roller.request_roll(
                "1d4", source="library.test",
                context={"label": "test roll", "why": "demo"},
            )
        self.assertEqual(len(events), 1)
        self.assertIs(events[0][0], result)
        self.assertEqual(events[0][1], "library.test")
        self.assertEqual(events[0][2]["label"], "test roll")
        self.assertEqual(result["why"], "demo")
        roller.remove_roll_listener(record)
        with self.assertLogs("diceroll", level="ERROR"):
            roller.roll_dice("1d6")
        self.assertEqual(len(events), 1)

    def test_history_has_no_implicit_files(self):
        roller = DiceRoller(save_rolls=True, rng=random.Random(3))
        with tempfile.TemporaryDirectory() as folder:
            old = os.getcwd()
            try:
                os.chdir(folder)
                for _ in range(8):
                    roller.roll_dice("1d6")
                self.assertEqual(os.listdir(folder), [])
                self.assertEqual(len(roller.get_last_5_rolls()), 5)
                self.assertEqual(len(roller.get_roll_history()), 8)
                roller.save_last_5_rolls("results.txt")
                self.assertIn("Roll Result:", Path("results.txt").read_text())
                roller.save_roll_history_to_file("history.json")
                history = json.loads(Path("history.json").read_text())
                self.assertEqual(len(history), 8)
                fresh = DiceRoller()
                fresh.load_roll_history_from_file("history.json")
                self.assertEqual(len(fresh.get_roll_history()), 8)
            finally:
                os.chdir(old)

    def test_advanced_statistics_do_not_emit_events(self):
        roller = DiceRoller(rng=random.Random(1), save_rolls=True)
        events = []
        roller.add_roll_listener(lambda *args: events.append(args))
        stats = roller.get_roll_statistics("2d6-1", 200)
        self.assertEqual(sum(stats["frequency"].values()), 200)
        self.assertEqual(roller.get_last_5_rolls(), [])
        self.assertEqual(events, [])
        self.assertEqual(roller.get_roll_history(), [])

    def test_exact_probability_distribution(self):
        probs = DiceRoller().get_dice_probabilities("2d6")
        self.assertTrue(math.isclose(sum(probs.values()), 1.0))
        self.assertEqual(probs[2], 1 / 36)
        self.assertEqual(probs[7], 6 / 36)
        self.assertEqual(probs[12], 1 / 36)
        for invalid in ("2d6+2", "1d6+1d4", "2d6-1d4"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(DiceNotationError):
                    DiceRoller().get_dice_probabilities(invalid)

    def test_probability_guard(self):
        with self.assertRaises(DiceNotationError):
            DiceRoller().get_dice_probabilities("1000d1000")

    def test_generic_check_does_not_force_false_odds(self):
        self.assertEqual(probability_target(0, 20), 21)
        self.assertEqual(probability_target(0.01, 20), 21)
        self.assertEqual(probability_target(0.5, 20), 11)
        self.assertEqual(probability_target(1, 20), 1)
        with self.assertRaises(ValueError):
            probability_target(1.1, 20)
        with self.assertRaises(ValueError):
            probability_target(float("nan"))
        roller = DiceRoller(rng=random.Random(1))
        result = roll_check(roller, 0.5, sides=6, label="test")
        self.assertEqual(result["target"], 4)
        self.assertEqual(result["label"], "test")
        self.assertEqual(result["chance"], 0.5)


class APITests(unittest.TestCase):
    def test_import_is_headless_and_quiet(self):
        import subprocess
        import sys
        completed = subprocess.run(
            [sys.executable, "-c", "import diceroll; import diceroll_api"],
            capture_output=True, text=True, check=True,
        )
        self.assertEqual(completed.stdout, "")

    def test_legacy_api_and_fixed_sum(self):
        api = dicerollAPI(rng=random.Random(7))
        self.assertIsInstance(api, DiceAPI)
        self.assertEqual(api.roll_dice("2d6+2")["roll_result"], 7)
        self.assertEqual(api.get_roll_sum(api.dice_roller.get_last_5_rolls()[-1]), 7)
        self.assertEqual(api.roll_single_dice(DiceType.D4)["dice_notation"], "1d4")
        self.assertEqual(
            api.roll_multiple_dice_of_same_type("d6", 3)["dice_notation"], "3d6",
        )

    def test_invalid_api_notation_raises(self):
        with self.assertRaises(DiceNotationError):
            DiceAPI().roll_dice("broken notation")

    def test_saving_throw_thresholds_are_independent(self):
        api = DiceAPI(rng=random.Random(7))
        result = api.roll_saving_throw("1d6", target_value=1, success_threshold=7)
        self.assertFalse(result["success"])
        self.assertEqual(result["target"], 7)
        self.assertEqual(
            len(api.roll_multiple_saving_throws(3, target_values=[1, 2, 3])), 3,
        )
        with self.assertRaises(ValueError):
            api.roll_multiple_saving_throws(2, target_values=[1])

    def test_advantage_and_disadvantage(self):
        api = DiceAPI(rng=random.Random(5))
        greater = api.roll_with_advantage("1d20")
        smaller = api.roll_with_disadvantage("1d20")
        self.assertGreaterEqual(greater["roll_result"], 1)
        self.assertLessEqual(smaller["roll_result"], 20)


if __name__ == "__main__":
    unittest.main()
