"""Portable, headless dice engine.

The public API is exported by :mod:`diceroll`.  No game or rendering
dependencies are imported by this module.
"""
from __future__ import annotations

import json
import logging
import math
import random
from collections import defaultdict
from dataclasses import dataclass, field, replace
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping

__all__ = [
    "DiceNotationError", "DiceTerm", "RollComponent", "RollResult",
    "DiceRoller", "parse_dice_notation", "probability_target", "roll_check",
]

_LOG = logging.getLogger(__name__)
_MAX_LENGTH = 4096
_MAX_TERMS = 128
_MAX_DICE_PER_TERM = 1000
_MAX_TOTAL_DICE = 10000
_MAX_SIDES = 10000
_MAX_MODIFIER = 1_000_000_000
_MAX_DISTRIBUTION_OPERATIONS = 2_000_000
_MAX_SIMULATIONS = 100_000


class DiceNotationError(ValueError):
    """An invalid or excessively large dice expression."""


@dataclass(frozen=True)
class DiceTerm:
    """A signed dice term or a signed integer modifier."""

    sign: int
    count: int
    sides: int
    modifier: int = 0

    @property
    def notation(self) -> str:
        return f"{self.count}d{self.sides}" if self.sides else str(self.modifier)


def parse_dice_notation(notation: str) -> tuple[tuple[DiceTerm, ...], str]:
    """Parse dice expressions such as `d20 + 2d6 - 3`.

    No arbitrary Python expressions, implicit multiplication or partial matches
    are allowed. At least one die is required. Limits protect callers from
    accidentally large expressions.
    """
    if not isinstance(notation, str):
        raise DiceNotationError("notation must be a string")
    source = notation.strip()
    if not source or len(source) > _MAX_LENGTH:
        raise DiceNotationError("notation is empty or too long")
    terms: list[DiceTerm] = []
    total_dice = 0
    index = 0
    while index < len(source):
        while index < len(source) and source[index].isspace():
            index += 1
        if index >= len(source):
            break
        sign = 1
        if source[index] in "+-":
            sign = -1 if source[index] == "-" else 1
            index += 1
            while index < len(source) and source[index].isspace():
                index += 1
        elif terms:
            raise DiceNotationError(f"expected '+' or '-' near position {index}")
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
            if index == start:
                raise DiceNotationError("die has no sides")
            sides = int(source[start:index])
            if not 1 <= count <= _MAX_DICE_PER_TERM:
                raise DiceNotationError("die count out of range")
            if not 2 <= sides <= _MAX_SIDES:
                raise DiceNotationError("die sides out of range")
            total_dice += count
            if total_dice > _MAX_TOTAL_DICE:
                raise DiceNotationError("too many dice")
            terms.append(DiceTerm(sign, count, sides))
        elif digits:
            modifier = int(digits)
            if modifier > _MAX_MODIFIER:
                raise DiceNotationError("modifier out of range")
            terms.append(DiceTerm(sign, 0, 0, modifier))
        else:
            raise DiceNotationError(f"expected die or modifier near position {index}")
        if len(terms) > _MAX_TERMS:
            raise DiceNotationError("too many terms")
        while index < len(source) and source[index].isspace():
            index += 1
        if index < len(source) and source[index] not in "+-":
            raise DiceNotationError(f"unexpected character near position {index}")
    if source[-1] in "+-":
        raise DiceNotationError("expression ends with an operator")
    if not any(term.sides for term in terms):
        raise DiceNotationError("expression must include at least one die")
    return tuple(terms), source


@dataclass(frozen=True)
class RollComponent:
    """The individual faces and signed subtotal for one expression term."""

    notation: str
    sign: int
    faces: tuple[int, ...]
    total: int
    colours: tuple[str | None, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "notation": self.notation, "sign": self.sign,
            "faces": list(self.faces), "total": self.total,
            "colours": list(self.colours),
        }


@dataclass(frozen=True)
class RollResult:
    """Immutable result of a single roll (or the kept roll of two attempts)."""

    notation: str
    total: int
    faces: tuple[int, ...]
    components: tuple[RollComponent, ...]
    modifier: int = 0
    target: int | None = None
    source: str = "library"
    context: Mapping[str, Any] = field(default_factory=dict)
    mode: str = "normal"
    alternative_totals: tuple[int, ...] = ()
    d6_colour: str = "blue"

    def __post_init__(self) -> None:
        object.__setattr__(self, "context", MappingProxyType(dict(self.context)))

    @property
    def success(self) -> bool | None:
        return None if self.target is None else self.total >= self.target

    def to_dict(self) -> dict[str, Any]:
        """Convert to a JSON-compatible structure (if context is JSON-safe)."""
        return {
            "notation": self.notation,
            "total": self.total,
            "faces": list(self.faces),
            "components": [component.to_dict() for component in self.components],
            "modifier": self.modifier,
            "target": self.target,
            "success": self.success,
            "source": self.source,
            "context": dict(self.context),
            "mode": self.mode,
            "alternative_totals": list(self.alternative_totals),
            "d6_colour": self.d6_colour,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RollResult:
        """Read a record previously produced by :meth:`to_dict`."""
        if not isinstance(data, dict):
            raise ValueError("roll record must be an object")
        try:
            components = tuple(
                RollComponent(
                    str(c["notation"]), int(c["sign"]),
                    tuple(int(x) for x in c["faces"]), int(c["total"]),
                    tuple(c["colours"]),
                )
                for c in data["components"]
            )
            result = cls(
                notation=str(data["notation"]),
                total=int(data["total"]),
                faces=tuple(int(x) for x in data["faces"]),
                components=components,
                modifier=int(data.get("modifier", 0)),
                target=(None if data.get("target") is None
                        else int(data["target"])),
                source=str(data.get("source", "library")),
                context=dict(data.get("context", {})),
                mode=str(data.get("mode", "normal")),
                alternative_totals=tuple(
                    int(x) for x in data.get("alternative_totals", ())
                ),
                d6_colour=str(data["d6_colour"]),
            )
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError("invalid roll record") from exc
        if result.total != sum(c.total for c in result.components):
            raise ValueError("roll total does not match components")
        if result.faces != tuple(x for c in result.components for x in c.faces):
            raise ValueError("roll faces do not match components")
        if result.d6_colour not in ("blue", "red", "white", "random"):
            raise ValueError("invalid d6 colour")
        for component in result.components:
            if len(component.colours) != len(component.faces):
                raise ValueError("colour count does not match dice faces")
            if any(c is not None and c not in ("blue", "red", "white")
                   for c in component.colours):
                raise ValueError("invalid die colour")
        return result


def probability_target(chance: float, sides: int = 20) -> int:
    """Minimum winning face on a `sides`-sided die, using nearest odds.

    Impossible checks return `sides + 1`. No RPG-specific minimum success
    chance is imposed; for example 1% on d20 rounds to 0%, not 5%.
    """
    chance = float(chance)
    if not math.isfinite(chance) or not 0 <= chance <= 1:
        raise ValueError("chance must be finite and in [0, 1]")
    if isinstance(sides, bool) or not isinstance(sides, int) or sides < 2:
        raise ValueError("sides must be an integer of at least 2")
    wins = int(math.floor(chance * sides + 0.5))
    return sides - wins + 1


def roll_check(roller: DiceRoller, chance: float, *, sides: int = 20,
               label: str = "", source: str = "check",
               context: Mapping[str, Any] | None = None) -> RollResult:
    """General probability check expressed as a single configurable die."""
    target = probability_target(chance, sides)
    metadata = dict(context or {})
    if label:
        metadata["label"] = label
    metadata["chance"] = float(chance)
    return roller.roll(f"1d{sides}", target=target, source=source, context=metadata)


class DiceRoller:
    """Headless roller with injectable randomness, events, and bounded history.

    The `rng` must supply `randint(a, b)`. None of the operations writes to
    disk except the explicit `save_history(path)` method.
    """

    def __init__(self, *, rng: random.Random | None = None,
                 history_limit: int | None = 5):
        if history_limit is not None and (not isinstance(history_limit, int)
                                          or history_limit < 0):
            raise ValueError("history_limit must be None or nonnegative")
        self.rng = rng if rng is not None else random.Random()
        self.history_limit = history_limit
        self._history: list[RollResult] = []
        self._listeners: list[Callable[[RollResult], None]] = []

    @property
    def history(self) -> tuple[RollResult, ...]:
        return tuple(self._history)

    def subscribe(self, listener: Callable[[RollResult], None]) -> None:
        """Subscribe to completed rolls; called with one RollResult."""
        if not callable(listener):
            raise TypeError("listener must be callable")
        if listener not in self._listeners:
            self._listeners.append(listener)

    def unsubscribe(self, listener: Callable[[RollResult], None]) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _attempt(self, terms: tuple[DiceTerm, ...]) -> tuple[int, tuple[int, ...], tuple[RollComponent, ...], int]:
        total = 0
        all_faces: list[int] = []
        components: list[RollComponent] = []
        modifier = 0
        for term in terms:
            if term.sides:
                faces = tuple(self.rng.randint(1, term.sides)
                              for _ in range(term.count))
                subtotal = term.sign * sum(faces)
                all_faces.extend(faces)
            else:
                faces = ()
                subtotal = term.sign * term.modifier
                modifier += subtotal
            components.append(RollComponent(term.notation, term.sign, faces, subtotal))
            total += subtotal
        return total, tuple(all_faces), tuple(components), modifier

    def roll(self, notation: str, *, target: int | None = None,
             mode: str = "normal", source: str = "library",
             context: Mapping[str, Any] | None = None,
             d6_colour: str = "blue") -> RollResult:
        """Roll a full expression, optionally choosing the better/worse of two.

        `mode` is `normal`, `advantage` (higher of two totals), or
        `disadvantage` (lower of two totals). The result describes the kept
        attempt and records the other total when rolling twice.
        """
        terms, source_notation = parse_dice_notation(notation)
        if mode not in ("normal", "advantage", "disadvantage"):
            raise ValueError("mode must be normal, advantage or disadvantage")
        if d6_colour not in ("blue", "red", "white", "random"):
            raise ValueError("d6_colour must be red, white, blue or random")
        if target is not None and (isinstance(target, bool)
                                   or not isinstance(target, int)):
            raise TypeError("target must be an integer or None")
        first = self._attempt(terms)
        alternative_totals: tuple[int, ...] = ()
        selected = first
        if mode != "normal":
            second = self._attempt(terms)
            take_second = (
                second[0] > first[0] if mode == "advantage"
                else second[0] < first[0]
            )
            selected = second if take_second else first
            alternative_totals = ((first if take_second else second)[0],)
        # Apply visual colours after rolling *all* faces, so selecting a fixed
        # colour never changes the numerical dice results for the same seed.
        coloured_components = []
        for component in selected[2]:
            if component.faces and component.notation.split("d")[-1] == "6":
                colours = tuple(
                    ("red", "white", "blue")[self.rng.randint(0, 2)]
                    if d6_colour == "random" else d6_colour
                    for _ in component.faces
                )
            else:
                colours = (None,) * len(component.faces)
            coloured_components.append(replace(component, colours=colours))
        result = RollResult(
            notation=source_notation, total=selected[0], faces=selected[1],
            components=tuple(coloured_components), modifier=selected[3], target=target,
            source=str(source), context=dict(context or {}),
            mode=mode, alternative_totals=alternative_totals,
            d6_colour=d6_colour,
        )
        if self.history_limit != 0:
            self._history.append(result)
            if self.history_limit is not None:
                del self._history[:-self.history_limit]
        for listener in tuple(self._listeners):
            try:
                listener(result)
            except Exception:
                _LOG.exception("dice roll subscriber failed")
        return result

    def distribution(self, notation: str) -> dict[int, Fraction]:
        """Exact total probabilities for signed and mixed dice expressions.

        Uses integer-count dynamic programming, returning rational fractions.
        An operation cap prevents accidental exponential/time-heavy workloads.
        This method does not touch the RNG, history or event listeners.
        """
        terms, _ = parse_dice_notation(notation)
        counts: dict[int, int] = {0: 1}
        work = 0
        for term in terms:
            if not term.sides:
                counts = {k + term.sign * term.modifier: ways
                          for k, ways in counts.items()}
                continue
            for _ in range(term.count):
                work += len(counts) * term.sides
                if work > _MAX_DISTRIBUTION_OPERATIONS:
                    raise ValueError("distribution exceeds computation budget")
                next_counts: dict[int, int] = defaultdict(int)
                for subtotal, ways in counts.items():
                    for face in range(1, term.sides + 1):
                        next_counts[subtotal + term.sign * face] += ways
                counts = dict(next_counts)
        combinations = sum(counts.values())
        return {k: Fraction(ways, combinations)
                for k, ways in sorted(counts.items())}

    def statistics(self, notation: str, trials: int) -> dict[str, Any]:
        """Simulate independent rolls without changing history or publishing.

        This advances the injected RNG. It is distinct from exact
        `distribution`, which never uses randomness.
        """
        if not isinstance(trials, int) or not 1 <= trials <= _MAX_SIMULATIONS:
            raise ValueError("trials out of range")
        terms, _ = parse_dice_notation(notation)
        counts: dict[int, int] = defaultdict(int)
        total = 0
        for _ in range(trials):
            score = self._attempt(terms)[0]
            counts[score] += 1
            total += score
        return {
            "trials": trials,
            "mean": total / trials,
            "min": min(counts),
            "max": max(counts),
            "frequency": dict(sorted(counts.items())),
        }

    def save_history(self, path: str | Path) -> None:
        """Write recorded results to JSON only when explicitly requested."""
        with open(path, "w", encoding="utf-8") as stream:
            json.dump([item.to_dict() for item in self._history],
                      stream, ensure_ascii=False, indent=2)

    def load_history(self, path: str | Path) -> None:
        """Replace recorded history from JSON without emitting roll events."""
        with open(path, encoding="utf-8") as stream:
            data = json.load(stream)
        if not isinstance(data, list):
            raise ValueError("history must be a JSON array")
        results = [RollResult.from_dict(entry) for entry in data]
        if self.history_limit == 0:
            self._history = []
        elif self.history_limit is None:
            self._history = results
        else:
            self._history = results[-self.history_limit:]
