"""Tests for the only supported, installable diceroll package API."""

from __future__ import annotations

import json
import math
import random
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from fractions import Fraction
from importlib.resources import files
from pathlib import Path

from diceroll import (
    DiceNotationError, DiceRoller, RollResult, parse_dice_notation,
    probability_target, render_svg, roll_check,
)


class ParserTests(unittest.TestCase):
    def test_shorthand_whitespace_signed_terms(self):
        terms, notation = parse_dice_notation("d20 + 2D6 - 3")
        self.assertEqual(notation, "d20 + 2D6 - 3")
        self.assertEqual(
            [(x.sign, x.count, x.sides, x.modifier) for x in terms],
            [(1, 1, 20, 0), (1, 2, 6, 0), (-1, 0, 0, 3)],
        )

    def test_many_combined_dice_types(self):
        terms, _ = parse_dice_notation("2d4 + 3d6 + d8 + 2d10 + d12 + d20 - 4")
        self.assertEqual([x.sides for x in terms], [4, 6, 8, 10, 12, 20, 0])

    def test_arbitrary_die_sizes(self):
        terms, _ = parse_dice_notation("d7+2d100-6")
        self.assertEqual([x.sides for x in terms], [7, 100, 0])

    def test_bad_notation_is_never_silently_accepted(self):
        for notation in (
            "", "1d20oops", "1d6+", "2d", "d1", "0d6",
            "1d6++3", "1d6 -- 2", "2d6*3", "4",
            "1d6+1d0", "1d6+0d6", "1d6+1d99999",
            "1d6+" + "2" * 4000,
        ):
            with self.subTest(expression=notation[:30]):
                with self.assertRaises(DiceNotationError):
                    parse_dice_notation(notation)

    def test_resource_limits(self):
        for notation in ("1001d6", "+".join(["100d6"] * 101),
                         "1d10001", "10000000000"):
            with self.subTest(expression=notation[:30]):
                with self.assertRaises(DiceNotationError):
                    parse_dice_notation(notation)


class RollTests(unittest.TestCase):
    def test_seeded_d6_and_modifier(self):
        result = DiceRoller(rng=random.Random(7)).roll("2d6+2")
        self.assertEqual(result.faces, (3, 2))
        self.assertEqual(result.total, 7)
        self.assertEqual(result.modifier, 2)
        self.assertEqual(result.components[-1].total, 2)
        self.assertEqual(result.components[0].colours, ("blue", "blue"))

    def test_mixed_signed_dice_and_components(self):
        result = DiceRoller(rng=random.Random(12)).roll(
            "2d4 + d12 - 3d6 + 5", d6_colour="red", target=10
        )
        self.assertEqual(result.total, sum(c.total for c in result.components))
        self.assertEqual(result.faces, tuple(
            value for c in result.components for value in c.faces
        ))
        self.assertEqual(len(result.faces), 6)
        self.assertEqual(result.components[0].colours, (None, None))
        self.assertEqual(result.components[2].colours, ("red",) * 3)
        self.assertEqual(result.success, result.total >= 10)

    def test_supported_dice_all_valid(self):
        for sides in (4, 6, 8, 10, 12, 20, 37, 100):
            with self.subTest(sides=sides):
                result = DiceRoller(rng=random.Random(5)).roll(f"3d{sides}")
                self.assertEqual(len(result.faces), 3)
                self.assertTrue(all(1 <= x <= sides for x in result.faces))

    def test_d6_palette_choices(self):
        for colour in ("red", "white", "blue"):
            with self.subTest(colour=colour):
                result = DiceRoller(rng=random.Random(9)).roll(
                    "d4 + 5d6 + d20", d6_colour=colour
                )
                self.assertEqual(result.d6_colour, colour)
                self.assertEqual(result.components[1].colours, (colour,) * 5)
                self.assertEqual(result.components[0].colours, (None,))
                self.assertEqual(result.components[2].colours, (None,))

    def test_random_colour_individually_per_d6(self):
        expr = "12d6 + d8 + 5d6"
        first = DiceRoller(rng=random.Random(8)).roll(
            expr, d6_colour="random"
        )
        second = DiceRoller(rng=random.Random(8)).roll(
            expr, d6_colour="random"
        )
        self.assertEqual(first, second)
        colours = first.components[0].colours + first.components[2].colours
        self.assertEqual(len(colours), 17)
        self.assertGreater(len(set(colours)), 1)
        self.assertTrue(set(colours) <= {"red", "white", "blue"})

    def test_random_colour_does_not_change_face_values(self):
        normal = DiceRoller(rng=random.Random(21)).roll(
            "2d6 + d20 + 4d6", d6_colour="blue"
        )
        mixed = DiceRoller(rng=random.Random(21)).roll(
            "2d6 + d20 + 4d6", d6_colour="random"
        )
        self.assertEqual(normal.faces, mixed.faces)
        self.assertEqual(normal.total, mixed.total)

    def test_bad_colour_rejected(self):
        with self.assertRaises(ValueError):
            DiceRoller().roll("1d6", d6_colour="green")

    def test_modes_keep_selected_total(self):
        for mode, comparator in (("advantage", max), ("disadvantage", min)):
            with self.subTest(mode=mode):
                result = DiceRoller(rng=random.Random(10)).roll(
                    "d20 + d4", mode=mode
                )
                self.assertEqual(len(result.alternative_totals), 1)
                self.assertEqual(
                    result.total,
                    comparator(result.total, *result.alternative_totals),
                )
                self.assertEqual(result.total, sum(c.total for c in result.components))

    def test_invalid_mode_does_not_roll(self):
        with self.assertRaises(ValueError):
            DiceRoller().roll("d6", mode="reroll-all")

    def test_listeners_receive_one_result_and_bad_listeners_cannot_break_roll(self):
        dice = DiceRoller()
        seen = []
        dice.subscribe(lambda result: seen.append(result))
        result = dice.roll("d20", context={"label": "Test"}, source="test")
        self.assertIs(seen[0], result)
        self.assertEqual(result.context["label"], "Test")
        with self.assertRaises(TypeError):
            result.context["label"] = "Changed"
        def bad(_result):
            raise RuntimeError("bad listener")
        dice.subscribe(bad)
        with self.assertLogs("diceroll.core", level="ERROR"):
            dice.roll("d6")
        self.assertEqual(len(seen), 2)
        dice.unsubscribe(bad)

    def test_history_is_bounded_and_no_implicit_disk_write(self):
        dice = DiceRoller(history_limit=3)
        with tempfile.TemporaryDirectory() as folder:
            for _ in range(6):
                dice.roll("1d6")
            self.assertEqual(len(dice.history), 3)
            self.assertEqual(list(Path(folder).iterdir()), [])
        self.assertEqual(len(DiceRoller(history_limit=0).history), 0)

    def test_history_serialization_keeps_d6_colours(self):
        dice = DiceRoller(rng=random.Random(4), history_limit=10)
        original = dice.roll("4d6+d12", d6_colour="random")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "rolls.json"
            dice.save_history(path)
            data = json.loads(path.read_text())
            self.assertEqual(data[0]["d6_colour"], "random")
            restored = DiceRoller()
            restored.load_history(path)
            self.assertEqual(restored.history[0], original)
            self.assertEqual(
                restored.history[0].components[0].colours,
                original.components[0].colours,
            )

    def test_history_file_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "invalid.json"
            path.write_text('{"not": "a list"}')
            with self.assertRaises(ValueError):
                DiceRoller().load_history(path)

    def test_success_is_none_without_target(self):
        self.assertIsNone(DiceRoller().roll("1d6").success)


class MathsTests(unittest.TestCase):
    def test_two_d6_distribution(self):
        probabilities = DiceRoller().distribution("2d6")
        self.assertEqual(sum(probabilities.values()), Fraction(1))
        self.assertEqual(probabilities[2], Fraction(1, 36))
        self.assertEqual(probabilities[7], Fraction(6, 36))
        self.assertEqual(probabilities[12], Fraction(1, 36))

    def test_mixed_signed_distribution_exact(self):
        probabilities = DiceRoller().distribution("2d4 + d6 - d8 + 3")
        self.assertEqual(sum(probabilities.values()), Fraction(1))
        self.assertEqual(min(probabilities), 2 + 1 - 8 + 3)
        self.assertEqual(max(probabilities), 8 + 6 - 1 + 3)
        self.assertEqual(
            probabilities[min(probabilities)], Fraction(1, 4*4*6*8)
        )

    def test_distribution_no_rng_or_events(self):
        roller = DiceRoller(rng=random.Random(4))
        events = []
        roller.subscribe(events.append)
        before = roller.rng.getstate()
        roller.distribution("3d4-1d8+2")
        self.assertEqual(roller.rng.getstate(), before)
        self.assertEqual(roller.history, ())
        self.assertEqual(events, [])

    def test_probability_guard(self):
        with self.assertRaises(ValueError):
            DiceRoller().distribution("1000d1000")

    def test_roll_check_is_generic_and_quantisation_is_explicit(self):
        self.assertEqual(probability_target(0, 20), 21)
        self.assertEqual(probability_target(0.01, 20), 21)
        self.assertEqual(probability_target(0.5, 20), 11)
        self.assertEqual(probability_target(1.0, 20), 1)
        check = roll_check(
            DiceRoller(rng=random.Random(7)), 0.5,
            sides=10, label="Climb",
        )
        self.assertEqual(check.target, 6)
        self.assertEqual(check.context["label"], "Climb")
        with self.assertRaises(ValueError):
            probability_target(float("nan"))

    def test_statistics_does_not_mutate_rolls(self):
        roller = DiceRoller(rng=random.Random(5))
        stats = roller.statistics("2d4 + 3", 100)
        self.assertEqual(sum(stats["frequency"].values()), 100)
        self.assertEqual(roller.history, ())


class SVGTests(unittest.TestCase):
    def test_all_six_standard_dice_have_real_artwork(self):
        assets = files("diceroll").joinpath("images")
        for sides in (4, 8, 10, 12, 20):
            self.assertTrue(
                assets.joinpath(f"blank_d{sides}.png").is_file(), sides
            )
        for colour in ("blue", "red", "white"):
            for face in range(1, 7):
                ext = "jpg" if colour == "white" else "png"
                self.assertTrue(
                    assets.joinpath(colour, f"dice{face}.{ext}").is_file(),
                    (colour, face),
                )

    def test_every_standard_type_renders_with_embedded_asset(self):
        result = DiceRoller(rng=random.Random(6)).roll(
            "d4+d6+d8+d10+d12+d20", d6_colour="red"
        )
        svg = render_svg(result)
        tree = ET.fromstring(svg)
        images = tree.findall("{http://www.w3.org/2000/svg}image")
        self.assertEqual(len(images), 6)
        self.assertEqual(svg.count("data:image/png;base64,"), 6)
        self.assertIn("d4 = ", svg)
        self.assertIn("d20 = ", svg)

    def test_three_d6_colours_and_random_mix_render(self):
        result = DiceRoller(rng=random.Random(7)).roll(
            "18d6", d6_colour="random"
        )
        svg = render_svg(result)
        self.assertIn("(red)", svg)
        self.assertIn("(white)", svg)
        self.assertIn("(blue)", svg)
        self.assertIn("data:image/jpeg;base64,", svg)
        self.assertIn("data:image/png;base64,", svg)
        self.assertEqual(svg.count("<image "), 18)

    def test_unsupported_die_size_has_vector_fallback(self):
        result = DiceRoller().roll("2d7 + d100", d6_colour="white")
        svg = render_svg(result)
        ET.fromstring(svg)
        self.assertIn("d7 =", svg)
        self.assertIn("d100 =", svg)
        self.assertEqual(svg.count("<image "), 0)

    def test_svg_is_well_formed_and_escapes_title(self):
        result = DiceRoller().roll("1d6+2")
        svg = render_svg(result, title='Roll < & ">')
        ET.fromstring(svg)
        self.assertIn("Roll &lt; &amp;", svg)

    def test_svg_requires_no_pygame(self):
        script = (
            "import sys; from diceroll import DiceRoller, render_svg; "
            "result = DiceRoller().roll('2d4+2d6', d6_colour='blue'); "
            "assert '<svg' in render_svg(result); "
            "assert 'pygame' not in sys.modules"
        )
        subprocess.run([sys.executable, "-c", script],
                       capture_output=True, text=True, check=True)


if __name__ == "__main__":
    unittest.main()
