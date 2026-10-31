"""Exercise the shipped binary artwork through the real SVG rendering path."""

from __future__ import annotations

import base64
import hashlib
from importlib.resources import files
import random
import struct
import unittest
from xml.etree import ElementTree as ET

from diceroll import DiceRoller, render_svg

SVG = "{http://www.w3.org/2000/svg}"
FACE_SEEDS = {1: 2, 2: 1, 3: 7, 4: 0, 5: 5, 6: 19}
STANDARDS = (4, 6, 8, 10, 12, 20)


def embedded_images(svg):
    """Read the real SVG image hrefs, decoding the exact embedded file bytes."""
    tree = ET.fromstring(svg)
    images = tree.findall(SVG + "image")
    decoded = []
    for image in images:
        link = image.get("href")
        if not link or not link.startswith("data:image/"):
            raise AssertionError(f"SVG image has external or missing href: {link!r}")
        prefix, encoded = link.split(",", 1)
        decoded.append((prefix, base64.b64decode(encoded, validate=True)))
    return tree, decoded


def image_resource(*parts):
    return files("diceroll").joinpath("images", *parts).read_bytes()


class ActualImageTests(unittest.TestCase):
    def test_all_std_miniwind_png_assets_are_valid_images_not_empty_placeholders(self):
        for sides in (4, 8, 10, 12, 20):
            with self.subTest(sides=sides):
                contents = image_resource(f"blank_d{sides}.png")
                self.assertGreater(len(contents), 4000)
                self.assertEqual(contents[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(contents[12:16], b"IHDR")
                width, height = struct.unpack(">II", contents[16:24])
                self.assertGreater(width, 16)
                self.assertGreater(height, 16)

    def test_every_d6_face_in_every_palette_is_shipped_as_real_image(self):
        for colour in ("red", "white", "blue"):
            for face in range(1, 7):
                with self.subTest(colour=colour, face=face):
                    name = f"dice{face}.jpg" if colour == "white" else f"dice{face}.png"
                    contents = image_resource(colour, name)
                    self.assertGreater(len(contents), 1000)
                    if colour == "white":
                        self.assertTrue(contents.startswith(b"\xff\xd8"))
                    else:
                        self.assertEqual(contents[:8], b"\x89PNG\r\n\x1a\n")

    def test_every_face_palette_pair_rolls_and_embeds_matching_asset_bytes(self):
        # Six real seeds select each d6 face, for each real colour, with
        # no monkeypatched RNG or mocked rendering functions.
        for colour in ("red", "white", "blue"):
            for face, seed in FACE_SEEDS.items():
                with self.subTest(colour=colour, face=face, seed=seed):
                    roll = DiceRoller(rng=random.Random(seed)).roll(
                        "1d6", d6_colour=colour
                    )
                    self.assertEqual(roll.faces, (face,))
                    self.assertEqual(roll.components[0].colours, (colour,))
                    tree, image_data = embedded_images(render_svg(roll))
                    self.assertEqual(len(image_data), 1)
                    mime, actual_bytes = image_data[0]
                    if colour == "white":
                        self.assertEqual(mime, "data:image/jpeg;base64")
                        source = image_resource("white", f"dice{face}.jpg")
                    else:
                        self.assertEqual(mime, "data:image/png;base64")
                        source = image_resource(colour, f"dice{face}.png")
                    self.assertEqual(hashlib.sha256(actual_bytes).digest(),
                                     hashlib.sha256(source).digest())
                    self.assertIn(f"d6 ({colour}) = {face}",
                                  "".join(tree.itertext()))

    def test_every_standard_die_type_renders_correct_original_image(self):
        roll = DiceRoller(rng=random.Random(0)).roll(
            "d4 + d6 + d8 + d10 + d12 + d20", d6_colour="red"
        )
        tree, images = embedded_images(render_svg(roll))
        self.assertEqual(len(images), len(STANDARDS))
        for i, sides in enumerate(STANDARDS):
            with self.subTest(sides=sides):
                expected = (
                    image_resource("red", f"dice{roll.faces[i]}.png")
                    if sides == 6 else image_resource(f"blank_d{sides}.png")
                )
                self.assertEqual(images[i][1], expected)
                self.assertIn(f"d{sides}", "".join(tree.itertext()))

    def test_random_mixed_d6s_embed_individually_selected_palette_faces(self):
        roll = DiceRoller(rng=random.Random(21)).roll(
            "d20 + 5d6 + d8", d6_colour="random"
        )
        colours = roll.components[1].colours
        self.assertEqual(colours, ("red", "white", "blue", "red", "blue"))
        _, images = embedded_images(render_svg(roll))
        self.assertEqual(len(images), 7)
        self.assertEqual(images[0][1], image_resource("blank_d20.png"))
        self.assertEqual(images[-1][1], image_resource("blank_d8.png"))
        for index, (face, colour) in enumerate(zip(roll.components[1].faces, colours)):
            with self.subTest(index=index, face=face, colour=colour):
                image = (
                    image_resource("white", f"dice{face}.jpg")
                    if colour == "white"
                    else image_resource(colour, f"dice{face}.png")
                )
                self.assertEqual(images[index + 1][1], image)

    def test_nonstandard_dice_render_with_readable_vector_fallback(self):
        for sides in (2, 3, 7, 37, 100, 9999):
            with self.subTest(sides=sides):
                roll = DiceRoller(rng=random.Random(5)).roll(f"2d{sides}")
                svg = render_svg(roll)
                tree, images = embedded_images(svg)
                self.assertEqual(images, [])
                self.assertEqual(len(tree.findall(SVG + "rect")), 3)
                self.assertIn(f"d{sides} = ", "".join(tree.itertext()))

    def test_svg_has_no_network_assets_or_external_fonts(self):
        roll = DiceRoller(rng=random.Random(7)).roll(
            "d4+3d6+d8+d10+d12+d20", d6_colour="random"
        )
        svg = render_svg(roll)
        tree, images = embedded_images(svg)
        self.assertEqual(len(images), 8)
        self.assertFalse(any("http://" in value or "https://" in value
                             for element in tree.iter()
                             for key, value in element.attrib.items()
                             if key.endswith("href")))
        self.assertNotIn("<script", svg.lower())
        self.assertNotIn("<foreignObject", svg)

    def test_svg_is_stable_for_same_result_and_does_not_consume_rng(self):
        roller = DiceRoller(rng=random.Random(14))
        roll = roller.roll("d4+6d6+d20", d6_colour="random")
        state = roller.rng.getstate()
        first = render_svg(roll, die_size=96, columns=3)
        second = render_svg(roll, die_size=96, columns=3)
        self.assertEqual(first, second)
        self.assertEqual(roller.rng.getstate(), state)
        self.assertEqual(len(roller.history), 1)
        self.assertEqual(embedded_images(first)[0].get("role"), "img")

    def test_layout_dimensions_and_title_are_real_svg(self):
        roll = DiceRoller(rng=random.Random(2)).roll(
            "4d6+d20", d6_colour="white"
        )
        one_row = ET.fromstring(render_svg(roll, columns=6, die_size=64))
        narrow = ET.fromstring(render_svg(roll, columns=2, die_size=64))
        w1, h1 = [float(x) for x in one_row.get("viewBox").split()[2:]]
        w2, h2 = [float(x) for x in narrow.get("viewBox").split()[2:]]
        self.assertGreater(h2, h1)
        self.assertGreaterEqual(w1, w2)

        custom = render_svg(roll, title='Danger < & "escaped"')
        tree = ET.fromstring(custom)
        title = tree.find(SVG + "title")
        self.assertIsNotNone(title)
        self.assertIn('Danger < & "escaped"', title.text)

    def test_success_failure_and_no_target_are_rendered_correctly(self):
        for seed, target, expected in (
            (5, 20, "SUCCESS"),
            (2, 20, "FAILED"),
        ):
            with self.subTest(seed=seed, expected=expected):
                roll = DiceRoller(rng=random.Random(seed)).roll("d20", target=target)
                svg = render_svg(roll)
                self.assertIn(expected, svg)
                self.assertIn("NEED 20+", svg)
        no_target = render_svg(DiceRoller().roll("d20"))
        self.assertNotIn("NEED", no_target)
        self.assertNotIn("SUCCESS", no_target)
        self.assertNotIn("FAILED", no_target)

    def test_invalid_svg_arguments_raise_before_rendering(self):
        roll = DiceRoller().roll("d6")
        cases = [
            {"die_size": 39}, {"die_size": 257}, {"die_size": "88"},
            {"columns": 0}, {"columns": 21}, {"columns": "6"},
        ]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    render_svg(roll, **kwargs)
        with self.assertRaises(TypeError):
            render_svg({"total": 10})

    def test_svg_output_does_not_write_files(self):
        import os
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as folder:
            previous = os.getcwd()
            try:
                os.chdir(folder)
                for colour in ("red", "white", "blue", "random"):
                    svg = render_svg(
                        DiceRoller(rng=random.Random(7)).roll(
                            "d4+d6+d8+d10+d12+d20", d6_colour=colour
                        )
                    )
                    self.assertTrue(svg.startswith("<svg "))
                self.assertEqual(list(Path(folder).iterdir()), [])
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
