"""Headless, reusable dice expressions and probability utilities.

No UI framework or game rules are imported.  Consumers can supply their own RNG,
subscribe to roll notifications, or render results using any toolkit.
"""

from __future__ import annotations

import json
import logging
import random
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

__all__ = [
    "DiceNotationError", "DiceTerm", "DiceRoller", "parse_dice_notation",
    "probability_target", "roll_check",
]

MAX_EXPRESSION_LENGTH = 4096
MAX_TERMS = 128
MAX_DICE_PER_TERM = 1000
MAX_TOTAL_DICE = 10000
MAX_DIE_SIDES = 10000
MAX_MODIFIER = 1_000_000_000
MAX_PROBABILITY_OPERATIONS = 2_000_000
HISTORY_LIMIT = 5
LOGGER = logging.getLogger(__name__)


class DiceNotationError(ValueError):
    """A dice expression is invalid or exceeds safe resource limits."""


@dataclass(frozen=True)
class DiceTerm:
    """One signed dice component or flat modifier in a dice expression."""

    sign: int
    count: int
    sides: int
    modifier: int = 0

    @property
    def notation(self) -> str:
        return f"{self.count}d{self.sides}" if self.sides else str(self.modifier)


def parse_dice_notation(dice_notation: str) -> tuple[list[DiceTerm], str]:
    """Parse dice such as `d20 + 2d6 - 3` into validated signed terms.

    Only positive dice counts and sides >= 2 are accepted.  At least one die
    must occur; whitespace and uppercase D are allowed.  Extraneous input
    (including a dangling operator) is rejected instead of silently ignored.
    """
    if not isinstance(dice_notation, str):
        raise DiceNotationError("Dice notation must be a string")
    source = dice_notation.strip()
    if not source or len(source) > MAX_EXPRESSION_LENGTH:
        raise DiceNotationError("Dice notation is empty or too long")
    terms: list[DiceTerm] = []
    index = 0
    total_dice = 0
    expect_term = True
    while index < len(source):
        while index < len(source) and source[index].isspace():
            index += 1
        if index == len(source):
            break
        sign = 1
        if source[index] in "+-":
            sign = -1 if source[index] == "-" else 1
            index += 1
            while index < len(source) and source[index].isspace():
                index += 1
        elif not expect_term:
            raise DiceNotationError(f"Expected '+' or '-' at position {index}")
        if index >= len(source) or not (source[index].isdigit() or source[index] in "dD"):
            raise DiceNotationError(f"Expected die or modifier at position {index}")
        start = index
        while index < len(source) and source[index].isdigit():
            index += 1
        digits = source[start:index]
        while index < len(source) and source[index].isspace():
            index += 1
        if index < len(source) and source[index] in "dD":
            count = int(digits) if digits else 1
            index += 1
            while index < len(source) and source[index].isspace():
                index += 1
            start = index
            while index < len(source) and source[index].isdigit():
                index += 1
            if start == index:
                raise DiceNotationError("Missing die size")
            sides = int(source[start:index])
            if not 1 <= count <= MAX_DICE_PER_TERM:
                raise DiceNotationError("Dice count is out of range")
            if not 2 <= sides <= MAX_DIE_SIDES:
                raise DiceNotationError("Die size is out of range")
            total_dice += count
            if total_dice > MAX_TOTAL_DICE:
                raise DiceNotationError("Expression contains too many dice")
            terms.append(DiceTerm(sign, count, sides))
        elif digits:
            modifier = int(digits)
            if modifier > MAX_MODIFIER:
                raise DiceNotationError("Modifier is out of range")
            terms.append(DiceTerm(sign, 0, 0, modifier))
        else:
            raise DiceNotationError(f"Invalid dice term at position {index}")
        if len(terms) > MAX_TERMS:
            raise DiceNotationError("Expression has too many terms")
        expect_term = False
        while index < len(source) and source[index].isspace():
            index += 1
        if index < len(source) and source[index] not in "+-":
            raise DiceNotationError(f"Unexpected input at position {index}")
    if not terms or not any(term.sides for term in terms):
        raise DiceNotationError("Expression must contain at least one die")
    if source.rstrip()[-1] in "+-":
        raise DiceNotationError("Expression ends with an operator")
    return terms, source


def probability_target(chance: float, sides: int = 20) -> int:
    """Minimum successful face when rolling at or above a target.

    A chance is rounded to the nearest representable fraction of `sides`.
    Unlike MiniWind's game rule this function does not force a nonzero chance
    to succeed at least 1/sides of the time.  For example, 1% on a d20
    maps to an impossible check rather than an inaccurate 5% chance.
    """
    import math

    chance = float(chance)
    sides = int(sides)
    if not math.isfinite(chance) or not 0 <= chance <= 1:
        raise ValueError("chance must be finite and between 0 and 1")
    if sides < 2:
        raise ValueError("sides must be at least 2")
    winning_faces = int(math.floor(chance * sides + 0.5))
    return sides - winning_faces + 1


def roll_check(roller: "DiceRoller", chance: float, *, sides: int = 20,
               label: str = "", source: str = "check",
               context: Mapping[str, Any] | None = None) -> dict:
    """Resolve a labelled probability check using a configurable die."""
    ctx = dict(context or {})
    if label:
        ctx["label"] = str(label)
    ctx["chance"] = float(chance)
    return roller.request_roll(
        f"1d{sides}", target=probability_target(chance, sides),
        source=source, context=ctx,
    )


class DiceRoller:
    """General-purpose dice roller with optional history and notifications.

    `save_rolls=True` collects history in memory; explicit save methods write
    it to disk.  Importing or rolling never writes files without a path.
    """

    def __init__(self, save_rolls: bool = False, *,
                 rng: random.Random | None = None, save_format: str = "txt"):
        if save_format not in ("txt", "json"):
            raise ValueError("save_format must be 'txt' or 'json'")
        self.rng = rng if rng is not None else random.Random()
        self.save_rolls = bool(save_rolls)
        self.save_format = save_format
        self.last_roll_total: int | None = None
        self.last_roll_details: list[int] | None = None
        self.last_5_rolls: list[dict] = []
        self.roll_history: list[dict] = []
        self._roll_listeners: list[Callable[[dict, str, dict], None]] = []

    def add_roll_listener(self, listener: Callable[[dict, str, dict], None]) -> None:
        """Subscribe to (result, source, context) events."""
        if not callable(listener):
            raise TypeError("listener must be callable")
        if listener not in self._roll_listeners:
            self._roll_listeners.append(listener)

    def remove_roll_listener(self, listener: Callable[[dict, str, dict], None]) -> None:
        if listener in self._roll_listeners:
            self._roll_listeners.remove(listener)

    def request_roll(self, dice_notation: str, target: int | None = None,
                     *, source: str = "library",
                     context: Mapping[str, Any] | None = None) -> dict:
        return self.roll_dice(dice_notation, target=target, source=source,
                              context=context)

    def roll_dice(self, dice_notation: str, target: int | None = None,
                  success_outcome: Any = None, failure_outcome: Any = None,
                  *, source: str = "library",
                  context: Mapping[str, Any] | None = None) -> dict:
        """Roll, track and publish one expression; optionally test a target."""
        terms, original = parse_dice_notation(dice_notation)
        components: list[dict] = []
        details: list[int] = []
        total = 0
        modifier = 0
        for term in terms:
            if term.sides:
                values = [self.rng.randint(1, term.sides)
                          for _ in range(term.count)]
                part = term.sign * sum(values)
                details.extend(values)
                components.append({
                    "notation": f"{term.count}d{term.sides}",
                    "sign": term.sign,
                    "roll_details": values,
                    "roll_result": part,
                })
            else:
                part = term.sign * term.modifier
                modifier += part
                components.append({
                    "notation": ("-" if term.sign < 0 else "+") + str(term.modifier),
                    "sign": term.sign,
                    "roll_details": [],
                    "roll_result": part,
                })
            total += part
        result: dict = {
            "dice_notation": original,
            "roll_result": total,
            "roll_details": details,
            "components": components,
            "modifier": modifier,
        }
        safe_context = dict(context or {})
        for key in ("label", "why", "chance"):
            if key in safe_context:
                result[key] = safe_context[key]
        if target is not None:
            result["target"] = target
            result["success"] = total >= target
            if success_outcome is not None and failure_outcome is not None:
                import copy
                outcome = success_outcome if result["success"] else failure_outcome
                result["outcome"] = copy.deepcopy(outcome)
                if isinstance(result["outcome"], dict):
                    result["outcome"]["roll_result"] = total
            else:
                result["outcome_text"] = ("Success" if result["success"]
                                           else "Failure")
        self.last_roll_total = total
        self.last_roll_details = list(details)
        self.last_5_rolls = (self.last_5_rolls + [result])[-HISTORY_LIMIT:]
        if self.save_rolls:
            self.roll_history.append(result)
        for listener in tuple(self._roll_listeners):
            try:
                listener(result, str(source), dict(safe_context))
            except Exception:
                LOGGER.exception("Dice roll listener failed")
        return result

    def roll_with_advantage(self, dice_notation: str) -> dict:
        """Roll twice and choose the larger total."""
        first = self.roll_dice(dice_notation)
        second = self.roll_dice(dice_notation)
        return first if first["roll_result"] >= second["roll_result"] else second

    def roll_with_disadvantage(self, dice_notation: str) -> dict:
        """Roll twice and choose the smaller total."""
        first = self.roll_dice(dice_notation)
        second = self.roll_dice(dice_notation)
        return first if first["roll_result"] <= second["roll_result"] else second

    def roll_saving_throw(self, dice_type: str = "1d20", target_value: int | None = None,
                          success_threshold: int | None = None) -> dict:
        threshold = success_threshold if success_threshold is not None else target_value
        return self.roll_dice(dice_type, target=threshold)

    def roll_multiple_dice(self, dice_notations, target_values=None) -> list[dict]:
        notations = list(dice_notations)
        targets = ([None] * len(notations) if target_values is None
                   else list(target_values))
        if len(targets) != len(notations):
            raise ValueError("target_values must match dice_notations")
        return [self.roll_dice(notation, target=target)
                for notation, target in zip(notations, targets)]

    def get_roll_statistics(self, dice_notation: str, num_rolls: int) -> dict:
        """Simulate rolls without mutating recent rolls, history or listeners."""
        count = int(num_rolls)
        if count < 1:
            raise ValueError("num_rolls must be at least 1")
        terms, _ = parse_dice_notation(dice_notation)
        results = []
        for _ in range(count):
            total = 0
            for term in terms:
                if term.sides:
                    total += term.sign * sum(
                        self.rng.randint(1, term.sides) for _ in range(term.count)
                    )
                else:
                    total += term.sign * term.modifier
            results.append(total)
        return {
            "dice_notation": dice_notation,
            "num_rolls": count,
            "average": sum(results) / count,
            "min": min(results),
            "max": max(results),
            "frequency": self.calculate_frequency(results),
        }

    @staticmethod
    def calculate_frequency(roll_results) -> dict[int, int]:
        counts: dict[int, int] = defaultdict(int)
        for value in roll_results:
            counts[int(value)] += 1
        return dict(counts)

    def get_dice_probabilities(self, dice_notation: str) -> dict[int, float]:
        """Exact distribution for one homogeneous positive `NdM` expression.

        Complexity is bounded to avoid unexpectedly expensive requests.
        """
        terms, _ = parse_dice_notation(dice_notation)
        if len(terms) != 1 or terms[0].sides == 0 or terms[0].sign != 1:
            raise DiceNotationError("Probabilities require one positive NdM term")
        term = terms[0]
        operations = term.count * (term.count * (term.sides - 1) + 1) * term.sides
        if operations > MAX_PROBABILITY_OPERATIONS:
            raise DiceNotationError("Probability calculation exceeds safe limit")
        counts: dict[int, int] = {0: 1}
        for _ in range(term.count):
            next_counts: dict[int, int] = defaultdict(int)
            for subtotal, ways in counts.items():
                for face in range(1, term.sides + 1):
                    next_counts[subtotal + face] += ways
            counts = dict(next_counts)
        total_ways = term.sides ** term.count
        return {value: ways / total_ways
                for value, ways in sorted(counts.items())}

    def get_last_roll_total(self) -> int | None:
        return self.last_roll_total

    def get_last_roll_details(self) -> list[int] | None:
        return (list(self.last_roll_details)
                if self.last_roll_details is not None else None)

    def get_last_5_rolls(self) -> list[dict]:
        return list(self.last_5_rolls)

    def get_roll_history(self) -> list[dict]:
        return list(self.roll_history)

    def set_roll_history(self, history) -> None:
        self.roll_history = list(history)

    def save_last_5_rolls(self, file_path: str | Path = "last_5_rolls.txt") -> None:
        """Explicitly write five most recent results to JSON or text."""
        self._write_results(file_path, self.last_5_rolls)

    def save_roll_history_to_file(self, file_path: str | Path) -> None:
        """Explicitly write all saved results as JSON."""
        with open(file_path, "w", encoding="utf-8") as handle:
            json.dump(self.roll_history, handle, indent=2)

    def load_roll_history_from_file(self, file_path: str | Path) -> list[dict]:
        with open(file_path, encoding="utf-8") as handle:
            results = json.load(handle)
        if not isinstance(results, list):
            raise ValueError("Roll history must be a JSON list")
        self.set_roll_history(results)
        return self.get_roll_history()

    def _write_results(self, file_path: str | Path, results: list[dict]) -> None:
        with open(file_path, "w", encoding="utf-8") as handle:
            if self.save_format == "json":
                json.dump(results, handle, indent=2)
            else:
                for index, result in enumerate(results, 1):
                    handle.write(f"Result {index}:\n")
                    handle.write(f"  Dice Notation: {result['dice_notation']}\n")
                    handle.write(f"  Roll Result: {result['roll_result']}\n")
                    handle.write(f"  Roll Details: {result['roll_details']}\n\n")
