"""End-to-end tests for public API, persistence and truly headless imports.

No mocked core/parser/renderer functions. A fresh Python subprocess blocks
all optional graphics libraries while it imports, rolls and renders the
actual installed-or-source package in isolated mode.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import textwrap
import unittest

from diceroll import DiceRoller, RollResult, render_svg


class HeadlessExecutionTests(unittest.TestCase):
    def run_isolated(self, program):
        # -I ignores PYTHONPATH, so the subprocess explicitly uses the exact
        # source checkout as an import root. It does not inherit any GUI
        # plugins, test monkeypatching or an implicit working-directory import.
        root = Path(__file__).resolve().parent.parent
        wrapper = (
            "import os, sys\n"
            "sys.path.insert(0, os.environ['DICEROLL_SOURCE_PATH'])\n"
            + textwrap.dedent(program)
        )
        with tempfile.TemporaryDirectory() as folder:
            env = dict(os.environ)
            env.update({
                "DICEROLL_SOURCE_PATH": str(root),
                "DISPLAY": "",
                "SDL_VIDEODRIVER": "invalid",
                "PYTHONNOUSERSITE": "1",
            })
            completed = subprocess.run(
                [sys.executable, "-I", "-c", wrapper],
                cwd=folder, env=env, capture_output=True, text=True,
                check=False, timeout=30,
            )
            leftover = list(Path(folder).iterdir())
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(leftover, [], "headless invocation wrote files implicitly")
        self.assertEqual(completed.stderr, "", completed.stderr)
        return completed.stdout

    def test_headless_import_render_and_roll_with_gui_packages_forbidden(self):
        stdout = self.run_isolated(
            """
            import importlib.abc
            class NoGUI(importlib.abc.MetaPathFinder):
                def find_spec(self, fullname, path=None, target=None):
                    if fullname.split('.')[0] in ('pygame', 'PyQt5', 'PIL',
                                                    'tkinter', 'PySide6'):
                        raise AssertionError("Unwanted GUI dependency: " + fullname)
                    return None
            import sys
            sys.meta_path.insert(0, NoGUI())
            from diceroll import DiceRoller, render_svg
            import random
            import xml.etree.ElementTree as ET
            roll = DiceRoller(rng=random.Random(0)).roll(
                "d4+d6+d8+d10+d12+d20", d6_colour="red"
            )
            image = render_svg(roll)
            assert roll.total == 39
            assert len(ET.fromstring(image).findall(
                '{http://www.w3.org/2000/svg}image'
            )) == 6
            assert not {'pygame', 'PyQt5', 'PIL', 'tkinter', 'PySide6'} & set(sys.modules)
            print(roll.total)
            """
        )
        self.assertEqual(stdout.strip(), "39")

    def test_headless_renders_each_d6_colour_from_isolated_python(self):
        stdout = self.run_isolated(
            """
            from diceroll import DiceRoller, render_svg
            import random
            import xml.etree.ElementTree as ET
            for colour in ("red", "white", "blue", "random"):
                roll = DiceRoller(rng=random.Random(21)).roll(
                    "d20+5d6+d8", d6_colour=colour
                )
                image = ET.fromstring(render_svg(roll))
                assert len(image.findall('{http://www.w3.org/2000/svg}image')) == 7
                assert roll.total == 37
                if colour != "random":
                    assert roll.components[1].colours == (colour,) * 5
            print("four colours")
            """
        )
        self.assertEqual(stdout.strip(), "four colours")

    def test_only_public_v3_names_are_exported(self):
        import diceroll
        expected = {
            "DiceRoller", "RollResult", "RollComponent", "DiceTerm",
            "DiceNotationError", "parse_dice_notation",
            "probability_target", "roll_check", "render_svg",
        }
        self.assertTrue(expected.issubset(set(diceroll.__all__)))
        self.assertEqual(len(diceroll.__all__), len(set(diceroll.__all__)))
        for name in expected:
            self.assertTrue(hasattr(diceroll, name), name)
        for removed in ("DiceAPI", "dicerollAPI", "DiceType", "DiceAnimator"):
            self.assertFalse(hasattr(diceroll, removed))

    def test_import_is_silent_even_in_fresh_process(self):
        self.assertEqual(
            self.run_isolated("import diceroll\nimport diceroll.core\nimport diceroll.svg\n"),
            "",
        )

    def test_no_graphics_runtime_is_required_for_default_routing(self):
        stdout = self.run_isolated(
            """
            import sys
            from diceroll import DiceRoller, render_svg
            for sides in (4, 6, 8, 10, 12, 20, 37, 100):
                result = DiceRoller().roll('d' + str(sides))
                assert 'TOTAL' in render_svg(result)
            assert 'pygame' not in sys.modules
            print('headless')
            """
        )
        self.assertEqual(stdout.strip(), "headless")


class HistoryAndEventIntegrationTests(unittest.TestCase):
    def test_history_roundtrip_of_mixed_colours_and_multiple_modes(self):
        roller = DiceRoller(rng=random.Random(31), history_limit=None)
        originals = [
            roller.roll("d4+4d6+d12", d6_colour="random"),
            roller.roll("2d6-d8+3", d6_colour="red", target=5),
            roller.roll("d20+d6", d6_colour="white", mode="advantage"),
            roller.roll("d10+d6", d6_colour="blue", mode="disadvantage"),
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.json"
            roller.save_history(path)
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(len(raw), 4)
            self.assertEqual([x["d6_colour"] for x in raw],
                             ["random", "red", "white", "blue"])
            restored = DiceRoller(history_limit=None)
            restored.load_history(path)
            self.assertEqual(list(restored.history), originals)
            for expected, actual in zip(originals, restored.history):
                self.assertEqual(render_svg(expected), render_svg(actual))

    def test_history_capacity_zero_and_unlimited(self):
        unlimited = DiceRoller(history_limit=None, rng=random.Random(7))
        disabled = DiceRoller(history_limit=0, rng=random.Random(7))
        for _ in range(12):
            unlimited.roll("d6")
            disabled.roll("d6")
        self.assertEqual(len(unlimited.history), 12)
        self.assertEqual(disabled.history, ())

    def test_loading_history_obeys_latest_N_retention_rule(self):
        writer = DiceRoller(rng=random.Random(12), history_limit=None)
        for i in range(9):
            writer.roll("d20+" + str(i), d6_colour="blue")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.json"
            writer.save_history(path)
            reader = DiceRoller(history_limit=3)
            seen = []
            reader.subscribe(seen.append)
            reader.load_history(path)
            self.assertEqual(reader.history, writer.history[-3:])
            self.assertEqual(seen, [])
            empty_reader = DiceRoller(history_limit=0)
            empty_reader.load_history(path)
            self.assertEqual(empty_reader.history, ())

    def test_malformed_saved_rolls_are_rejected_without_losing_existing_history(self):
        reader = DiceRoller(rng=random.Random(5), history_limit=10)
        original = reader.roll("2d6", d6_colour="red")
        malformed = [
            {},
            {"notation": "d6"},
            {**original.to_dict(), "total": 123456},
            {**original.to_dict(), "faces": [4, 5, 6]},
            {**original.to_dict(), "d6_colour": "chartreuse"},
            {**original.to_dict(), "components": [
                {**original.to_dict()["components"][0], "colours": ["red"]}
            ]},
        ]
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "history.json"
            for item in malformed:
                with self.subTest(item=item):
                    file.write_text(json.dumps([item]), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        reader.load_history(file)
                    self.assertEqual(reader.history, (original,))

    def test_listener_exceptions_are_logged_but_other_observers_still_run(self):
        roller = DiceRoller(rng=random.Random(6))
        events = []
        def bad_listener(_):
            raise RuntimeError("subscriber crashed")
        def good_listener(result):
            events.append(result)
        roller.subscribe(bad_listener)
        roller.subscribe(good_listener)
        roller.subscribe(good_listener)
        with self.assertLogs("diceroll.core", level="ERROR") as capture:
            result = roller.roll("d20+2", source="integration")
        self.assertEqual(events, [result])
        self.assertIn("subscriber crashed", "\n".join(capture.output))
        roller.unsubscribe(bad_listener)
        roller.unsubscribe(good_listener)
        roller.unsubscribe(good_listener)
        self.assertEqual(roller.roll("d6").notation, "d6")
        self.assertEqual(len(events), 1)

    def test_repeated_svg_rendering_has_no_history_or_listener_side_effects(self):
        roller = DiceRoller(rng=random.Random(5))
        seen = []
        roller.subscribe(seen.append)
        original = roller.roll("d20+3d6", d6_colour="random")
        before_state = roller.rng.getstate()
        for _ in range(5):
            output = render_svg(original)
            self.assertIn("TOTAL", output)
        self.assertEqual(roller.rng.getstate(), before_state)
        self.assertEqual(roller.history, (original,))
        self.assertEqual(seen, [original])

    def test_result_serialisation_reflects_signed_subtotals_exactly(self):
        result = DiceRoller(rng=random.Random(11)).roll(
            "2d4 - 3d6 + d12 + 5", d6_colour="white", target=7
        )
        payload = result.to_dict()
        self.assertEqual(payload["total"], 3)
        self.assertEqual([c["total"] for c in payload["components"]],
                         [8, -14, 4, 5])
        self.assertEqual(payload["modifier"], 5)
        self.assertEqual(payload["success"], False)
        self.assertEqual(payload["components"][1]["colours"], ["white"] * 3)
        self.assertEqual(RollResult.from_dict(payload), result)

    def test_history_save_and_load_are_explicit_only(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.json"
            roller = DiceRoller()
            roller.roll("d6")
            self.assertFalse(path.exists())
            roller.save_history(path)
            self.assertTrue(path.is_file())
            loaded = DiceRoller()
            loaded.load_history(path)
            self.assertEqual(loaded.history, roller.history)


if __name__ == "__main__":
    unittest.main()
