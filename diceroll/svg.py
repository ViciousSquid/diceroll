"""Dependency-free SVG presentation of :mod:`diceroll` results.

SVG is plain text and can be embedded in HTML, saved as a file, shown in
browsers or rendered by a host application's chosen toolkit.  No graphical
dependency, event loop or network connection is required.
"""

from __future__ import annotations

import base64
from html import escape
from importlib.resources import files

from .core import RollResult

__all__ = ["render_svg"]

_STANDARD_IMAGES = {4, 8, 10, 12, 20}
_D6_PALETTES = {"red", "white", "blue"}


def _image_data(filename: str) -> str | None:
    """Embed shipped image bytes; SVG remains portable outside this package."""
    image = files("diceroll").joinpath("images", *filename.split("/"))
    if not image.is_file():
        return None
    media_type = "image/jpeg" if filename.endswith(".jpg") else "image/png"
    payload = base64.b64encode(image.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{payload}"


def render_svg(
    result: RollResult,
    *,
    die_size: int = 88,
    columns: int = 6,
    title: str | None = None,
) -> str:
    """Return a self-contained SVG illustration of a roll.

    Every die receives its own slot, value and type. For d6s, the specified
    colour is taken from the actual roll's per-die metadata, so a `random`
    roll can display mixed red/white/blue dice. MiniWind's d4/d8/d10/d12/d20
    die art and the original colour-specific d6 art are embedded directly.
    Arbitrary faces (e.g. d7, d100) have a legible vector fallback.
    No rendering package is imported or required.
    """
    if not isinstance(result, RollResult):
        raise TypeError("result must be a RollResult")
    if not isinstance(die_size, int) or not 40 <= die_size <= 256:
        raise ValueError("die_size must be an integer from 40 to 256")
    if not isinstance(columns, int) or not 1 <= columns <= 20:
        raise ValueError("columns must be an integer from 1 to 20")
    dice: list[tuple[int, int, str | None]] = []
    for component in result.components:
        if not component.faces:
            continue
        sides = int(component.notation.split("d", 1)[1])
        if len(component.colours) != len(component.faces):
            raise ValueError("result is missing per-die colour metadata")
        dice.extend(zip((sides,) * len(component.faces),
                        component.faces, component.colours))
    if not dice:
        raise ValueError("result has no dice")
    columns = min(columns, len(dice))
    rows = (len(dice) + columns - 1) // columns
    gap = 22
    margin = 24
    slot_h = die_size + 31
    panel_w = max(320, columns * (die_size + gap) - gap + 2 * margin)
    panel_h = margin * 2 + 60 + rows * slot_h + 43
    # Center a shorter final row rather than leaving an awkward left gutter.
    img_cache: dict[str, str | None] = {}
    heading = escape(result.notation if title is None else title)
    details = f"TOTAL {result.total}"
    if result.target is not None:
        details += f"  ·  NEED {result.target}+  ·  "
        details += "SUCCESS" if result.success else "FAILED"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {panel_w} {panel_h}" width="{panel_w}" '
        f'height="{panel_h}" role="img">',
        f'<title>{heading}: {escape(details)}</title>',
        f'<rect width="{panel_w}" height="{panel_h}" rx="14" fill="#171a26"/>',
        f'<text x="{panel_w/2:.1f}" y="34" font-family="sans-serif" '
        f'font-weight="bold" font-size="17" fill="#f3f4f9" '
        f'text-anchor="middle">{heading}</text>',
    ]
    for i, (sides, value, colour) in enumerate(dice):
        row, col = divmod(i, columns)
        count_in_row = min(columns, len(dice) - row * columns)
        row_width = count_in_row * (die_size + gap) - gap
        left = (panel_w - row_width) / 2
        x = left + col * (die_size + gap)
        y = 60 + row * slot_h
        name = f"d{sides}"
        if sides == 6 and colour in _D6_PALETTES:
            ext = "jpg" if colour == "white" else "png"
            filename = f"{colour}/dice{value}.{ext}"
            name += f" ({colour})"
        elif sides in _STANDARD_IMAGES:
            filename = f"blank_d{sides}.png"
        elif sides == 6:
            filename = f"d6_{value}.png"
        else:
            filename = ""
        if filename not in img_cache:
            img_cache[filename] = _image_data(filename) if filename else None
        uri = img_cache[filename]
        if uri is not None:
            parts.append(
                f'<image x="{x:.1f}" y="{y:.1f}" width="{die_size}" '
                f'height="{die_size}" href="{uri}"/>'
            )
        else:
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{die_size}" '
                f'height="{die_size}" rx="16" fill="#344b6d" '
                f'stroke="#9dbadb" stroke-width="2"/>'
            )
        # Non-d6 illustrations have blank faces, and arbitrary dice need a
        # value drawn on top. A d6's numbered/pipped face is already artwork.
        if sides != 6 or uri is None:
            parts.append(
                f'<text x="{x+die_size/2:.1f}" y="{y+die_size*.6:.1f}" '
                f'text-anchor="middle" font-family="sans-serif" '
                f'font-weight="bold" font-size="{max(16, die_size//3)}" '
                f'fill="#ffffff">{value}</text>'
            )
        parts.append(
            f'<text x="{x+die_size/2:.1f}" y="{y+die_size+19:.1f}" '
            f'text-anchor="middle" font-family="sans-serif" '
            f'font-size="12" fill="#bec8dc">{escape(name)} = {value}</text>'
        )
    baseline = margin + 60 + rows * slot_h + 8
    parts.append(
        f'<text x="{panel_w/2:.1f}" y="{baseline}" font-family="sans-serif" '
        f'font-weight="bold" font-size="17" fill="#f3db9e" '
        f'text-anchor="middle">{escape(details)}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)
