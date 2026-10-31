"""Real Pygame renderer integration: no mocks or fake dice surfaces.

Only runs if pygame/pygame-ce is installed. Ordinary library installs skip
these tests and still exercise SVG and the numerical engine.
"""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys
import unittest

from diceroll import (
    DiceRoller, PygameDiceAnimation, PygameDieFrame,
    pygame_available, render_svg, visualise,
)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


class NoDependencyTests(unittest.TestCase):
    def test_explicit_svg_renders_without_needing_pygame(self):
        result = DiceRoller(rng=random.Random(21)).roll(
            "d4+3d6+d8+d12+d20", d6_colour="random"
        )
        output = visualise(result, backend="svg")
        self.assertEqual(output, render_svg(result))
        self.assertIn("data:image/", output)

    def test_invalid_backend_does_not_roll_again(self):
        roller = DiceRoller(rng=random.Random(17))
        result = roller.roll("2d6", d6_colour="random")
        before = roller.rng.getstate()
        with self.assertRaises(ValueError):
            visualise(result, backend="unknown")
        self.assertEqual(roller.history, (result,))
        self.assertEqual(roller.rng.getstate(), before)

    def test_forced_pygame_is_optional(self):
        if not pygame_available():
            result = DiceRoller().roll("d4+d6")
            with self.assertRaisesRegex(ImportError, "pip install pygame-ce"):
                visualise(result, backend="pygame")


@unittest.skipUnless(pygame_available(), "pygame is not installed (optional)")
class RealPygameAnimationTests(unittest.TestCase):
    def setUp(self):
        import pygame

        self.pg = pygame
        self.roller = DiceRoller(rng=random.Random(21))
        self.roll = self.roller.roll(
            "2d4 + 5d6 + d8 + d10 + d12 + d20",
            d6_colour="random", target=43,
        )
        self.seen = []
        self.roller.subscribe(self.seen.append)

    def animation(self, **opts):
        return PygameDiceAnimation(self.roll, seed=37, duration=1.5,
                                   die_size=75, columns=4, **opts)

    def test_availability_auto_selects_real_pygame_without_re_rolling(self):
        self.assertTrue(pygame_available())
        before = self.roller.rng.getstate()
        auto = visualise(self.roll, backend="auto", seed=99)
        explicit = visualise(self.roll, backend="pygame", seed=99)
        self.assertIsInstance(auto, PygameDiceAnimation)
        self.assertEqual(auto.timings, explicit.timings)
        self.assertEqual(auto.frames(0.4), explicit.frames(0.4))
        self.assertEqual(self.roller.rng.getstate(), before)
        self.assertEqual(self.roller.history, (self.roll,))
        self.assertEqual(self.seen, [])

    def test_every_die_has_independent_starts_rates_and_settling_times(self):
        animation = self.animation()
        timings = animation.timings
        self.assertEqual(len(timings), len(self.roll.faces))
        self.assertEqual(len(set(timings)), len(timings))
        self.assertGreater(len({start for start, _ in timings}), 1)
        self.assertGreater(len({stop for _, stop in timings}), 1)
        self.assertGreater(animation.total_duration, 1.0)
        self.assertFalse(animation.is_finished(0.0))
        middle = sorted(stop for _, stop in timings)[len(timings) // 2]
        states = animation.frames(middle)
        self.assertTrue(any(frame.settled for frame in states))
        self.assertTrue(any(not frame.settled for frame in states))
        self.assertGreater(len({round(f.angle, 1) for f in states
                                if not f.settled}), 1)

    def test_tumbling_faces_are_visual_only_and_final_faces_match_result(self):
        animation = self.animation()
        before_history = self.roller.history
        before_rng = self.roller.rng.getstate()
        before_svg = render_svg(self.roll)
        preview = animation.frames(0.4)
        self.assertTrue(all(isinstance(frame, PygameDieFrame)
                            for frame in preview))
        self.assertTrue(any(not frame.settled for frame in preview))
        self.assertTrue(any(f.offset_y != 0 or f.angle != 0
                            for f in preview if not f.settled))
        finished = animation.frames(animation.total_duration + 1)
        self.assertTrue(all(f.settled for f in finished))
        self.assertEqual(tuple(f.face for f in finished), self.roll.faces)
        self.assertEqual(
            tuple(f.colour for f in finished),
            tuple(c for component in self.roll.components
                  for c in component.colours),
        )
        self.assertTrue(all(f.angle == 0 and f.offset_x == 0 and
                            f.offset_y == 0 and f.scale == 1.0
                            for f in finished))
        self.assertEqual(self.roller.history, before_history)
        self.assertEqual(self.roller.rng.getstate(), before_rng)
        self.assertEqual(render_svg(self.roll), before_svg)

    def test_same_animation_seed_has_repeatable_frames_and_drawings(self):
        first = self.animation()
        second = self.animation()
        for t in (0.0, 0.2, 0.7, 1.1, first.total_duration + 0.01):
            with self.subTest(elapsed=t):
                self.assertEqual(first.frames(t), second.frames(t))
                one = self.pg.Surface((1000, 800))
                two = self.pg.Surface((1000, 800))
                one.fill((9, 9, 9))
                two.fill((9, 9, 9))
                box1 = first.draw(one, t, center=(500, 400))
                box2 = second.draw(two, t, center=(500, 400))
                self.assertEqual(box1, box2)
                self.assertEqual(
                    self.pg.image.tostring(one, "RGB"),
                    self.pg.image.tostring(two, "RGB"),
                )

    def test_surface_changes_during_tumbling_and_settles_correctly(self):
        animation = self.animation()
        before_display = self.pg.display.get_init()
        stages = (0.05, 0.35, 0.75, animation.total_duration + 0.01)
        pixels = []
        for t in stages:
            surface = self.pg.Surface((1000, 800))
            surface.fill((7, 9, 12))
            rectangle = animation.draw(surface, t)
            self.assertEqual(rectangle.center, surface.get_rect().center)
            self.assertEqual(surface.get_at((rectangle.left+16,
                                             rectangle.top+16))[:3],
                             (24, 28, 41))
            pixels.append(self.pg.image.tostring(surface, "RGB"))
        self.assertEqual(len(set(pixels)), len(stages))
        self.assertEqual(self.pg.display.get_init(), before_display)

    def test_original_coloured_d6_sprites_load_for_all_18_face_palette_pairs(self):
        for colour in ("red", "white", "blue"):
            for face_seed in range(100):
                result = DiceRoller(rng=random.Random(face_seed)).roll(
                    "d6", d6_colour=colour
                )
                face = result.faces[0]
                with self.subTest(colour=colour, face=face):
                    anim = PygameDiceAnimation(result, seed=face_seed)
                    surface = self.pg.Surface((480, 310))
                    anim.draw(surface, anim.total_duration + 0.1)
                if face_seed >= 40 and face == 6:
                    break

    def test_many_standard_and_unusual_dice_animate_without_a_window(self):
        result = DiceRoller(rng=random.Random(7)).roll(
            "d4+d6+d8+d10+d12+d20+d7+d100", d6_colour="white"
        )
        animation = PygameDiceAnimation(result, seed=5)
        surface = self.pg.Surface((1200, 800))
        for t in (0, 0.2, 1.0, animation.total_duration):
            rectangle = animation.draw(surface, t)
            self.assertGreater(rectangle.width, 0)
            self.assertEqual(len(animation.frames(t)), 8)

    def test_invalid_animation_config_and_time_are_rejected(self):
        bad_configs = (
            {"duration": 0}, {"duration": math.nan},
            {"duration": math.inf}, {"duration": -1},
            {"die_size": 20}, {"die_size": 400},
            {"columns": 0}, {"columns": 21},
        )
        for options in bad_configs:
            with self.subTest(options=options):
                with self.assertRaises(ValueError):
                    PygameDiceAnimation(self.roll, **options)
        animation = self.animation()
        for invalid in (-0.01, float("nan"), float("inf"), "0"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    animation.frames(invalid)
        with self.assertRaises(TypeError):
            animation.draw("not a Pygame surface", 0.5)

    def test_rendering_does_not_consume_events_or_manage_window_lifecycle(self):
        animation = self.animation()
        started = self.pg.get_init()
        before_display = self.pg.display.get_init()
        surface = self.pg.Surface((900, 650))
        animation.draw(surface, 0.5)
        self.assertEqual(self.pg.get_init(), started)
        self.assertEqual(self.pg.display.get_init(), before_display)
        self.assertEqual(self.roller.history, (self.roll,))


if __name__ == "__main__":
    unittest.main()
