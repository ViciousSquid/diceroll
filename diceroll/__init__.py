"""Dependency-free dice core with optional auto-detected visualisation.

`render_svg` always works; `PygameDiceAnimation` and `visualise`
use Pygame only when it is already installed and an animation is requested.
Importing diceroll itself never imports Pygame.
"""
from .core import (
    DiceNotationError, DiceTerm, RollComponent, RollResult,
    DiceRoller, parse_dice_notation, probability_target, roll_check,
)
from .svg import render_svg
from .pygame_renderer import PygameDiceAnimation, PygameDieFrame
from .visualisation import pygame_available, visualise

__all__ = [
    "DiceNotationError", "DiceTerm", "RollComponent", "RollResult",
    "DiceRoller", "parse_dice_notation", "probability_target",
    "roll_check", "render_svg", "PygameDiceAnimation", "PygameDieFrame",
    "pygame_available", "visualise",
]
