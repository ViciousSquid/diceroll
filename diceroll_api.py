"""Convenient public API for the headless diceroll library.

Pygame animation remains an optional module (`diceroll_anim`), not a
dependency of this API.
"""

from __future__ import annotations

import re
from pathlib import Path

from diceroll import (
    DiceNotationError, DiceRoller, DiceTerm, parse_dice_notation,
    probability_target, roll_check,
)


class DiceType:
    D4 = "1d4"
    D6 = "1d6"
    D8 = "1d8"
    D10 = "1d10"
    D12 = "1d12"
    D20 = "1d20"


class DiceColor:
    RED = "red"
    BLUE = "blue"
    BLACK = "black"
    WHITE = "white"
    GREEN = "green"


class AnimationStyle:
    SHAKE = "shake"
    TUMBLE = "tumble"
    SPIN = "spin"


class DiceAPI:
    """Thin convenience wrapper around DiceRoller.

    Invalid dice expressions raise DiceNotationError, rather than printing and
    returning None.  This is intentional for library callers.
    """

    def __init__(self, save_rolls: bool = False, *, rng=None,
                 save_format: str = "txt"):
        self.dice_roller = DiceRoller(
            save_rolls=save_rolls, rng=rng, save_format=save_format,
        )

    def roll_dice(self, dice_notation: str, target_value=None, *,
                  source: str = "library", context=None):
        return self.dice_roller.roll_dice(
            dice_notation, target=target_value, source=source, context=context,
        )

    def request_roll(self, dice_notation: str, target=None, *,
                     source: str = "library", context=None):
        return self.dice_roller.request_roll(
            dice_notation, target=target, source=source, context=context,
        )

    def add_roll_listener(self, listener):
        self.dice_roller.add_roll_listener(listener)

    def remove_roll_listener(self, listener):
        self.dice_roller.remove_roll_listener(listener)

    def roll_single_dice(self, dice_type: str):
        sides = self._single_die_size(dice_type)
        return self.roll_dice(f"1d{sides}")

    def roll_multiple_dice_of_same_type(self, dice_type: str, num_dice: int):
        sides = self._single_die_size(dice_type)
        return self.roll_dice(f"{int(num_dice)}d{sides}")

    @staticmethod
    def _single_die_size(dice_type: str) -> int:
        match = re.fullmatch(r"(?:1)?[dD]([0-9]+)", str(dice_type).strip())
        if match is None:
            raise DiceNotationError("Expected single die such as 'd6' or '1d20'")
        return int(match.group(1))

    def roll_multiple_dice(self, dice_notations, target_values=None):
        return self.dice_roller.roll_multiple_dice(dice_notations, target_values)

    def roll_with_advantage(self, dice_notation: str):
        return self.dice_roller.roll_with_advantage(dice_notation)

    def roll_with_disadvantage(self, dice_notation: str):
        return self.dice_roller.roll_with_disadvantage(dice_notation)

    def roll_saving_throw(self, dice_type: str = DiceType.D20,
                          target_value=None, success_threshold=None):
        return self.dice_roller.roll_saving_throw(
            dice_type, target_value=target_value,
            success_threshold=success_threshold,
        )

    def roll_multiple_saving_throws(self, num_throws: int,
                                    dice_type: str = DiceType.D20,
                                    target_values=None,
                                    success_thresholds=None):
        if num_throws < 0:
            raise ValueError("num_throws must be non-negative")
        targets = ([None] * num_throws if target_values is None
                   else list(target_values))
        thresholds = (targets if success_thresholds is None
                      else list(success_thresholds))
        if len(targets) != num_throws or len(thresholds) != num_throws:
            raise ValueError("targets and thresholds must match num_throws")
        return [self.roll_saving_throw(dice_type, t, s)
                for t, s in zip(targets, thresholds)]

    def get_roll_sum(self, roll_result) -> int:
        """Includes arithmetic modifiers; not merely the sum of dice faces."""
        return roll_result["roll_result"] if roll_result else 0

    def get_roll_average(self, roll_result) -> float:
        details = roll_result.get("roll_details", ()) if roll_result else ()
        return sum(details) / len(details) if details else 0.0

    def get_roll_max(self, roll_result) -> int:
        details = roll_result.get("roll_details", ()) if roll_result else ()
        return max(details) if details else 0

    def get_roll_min(self, roll_result) -> int:
        details = roll_result.get("roll_details", ()) if roll_result else ()
        return min(details) if details else 0

    def get_roll_statistics(self, dice_notation: str, num_rolls: int):
        return self.dice_roller.get_roll_statistics(dice_notation, num_rolls)

    def get_dice_probabilities(self, dice_notation: str):
        return self.dice_roller.get_dice_probabilities(dice_notation)

    def get_last_roll_total(self):
        return self.dice_roller.get_last_roll_total()

    def get_last_roll_details(self):
        return self.dice_roller.get_last_roll_details()

    def get_last_5_rolls(self):
        return self.dice_roller.get_last_5_rolls()

    def get_roll_history(self):
        return self.dice_roller.get_roll_history()

    def set_roll_history(self, history):
        self.dice_roller.set_roll_history(history)

    def save_last_5_rolls(self, file_path="last_5_rolls.txt"):
        self.dice_roller.save_last_5_rolls(file_path)

    def save_roll_history_to_file(self, file_path: str | Path):
        self.dice_roller.save_roll_history_to_file(file_path)

    def load_roll_history_from_file(self, file_path: str | Path):
        """Retain legacy behaviour for a missing or invalid history file."""
        import json

        try:
            return self.dice_roller.load_roll_history_from_file(file_path)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def enable_roll_saving(self):
        self.dice_roller.save_rolls = True

    def disable_roll_saving(self):
        self.dice_roller.save_rolls = False


class dicerollAPI(DiceAPI):
    """Backwards-compatible name for DiceAPI."""


__all__ = [
    "DiceAPI", "dicerollAPI", "DiceType", "DiceColor", "AnimationStyle",
    "DiceNotationError", "DiceTerm", "DiceRoller", "parse_dice_notation",
    "probability_target", "roll_check",
]
