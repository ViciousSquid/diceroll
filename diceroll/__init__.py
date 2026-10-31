"""Installable, dependency-free Python dice module.

One public roller (`DiceRoller.roll`) and a standalone SVG visualisation
function (`render_svg`). This package does not import Pygame or Qt.
"""
from .core import (
    DiceNotationError, DiceTerm, RollComponent, RollResult,
    DiceRoller, parse_dice_notation, probability_target, roll_check,
)
from .svg import render_svg

__all__ = [
    "DiceNotationError", "DiceTerm", "RollComponent", "RollResult",
    "DiceRoller", "parse_dice_notation", "probability_target",
    "roll_check", "render_svg",
]
