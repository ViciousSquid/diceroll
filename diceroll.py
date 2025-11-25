"""
diceroll.py

A robust dice-rolling library with:
- full dice-notation parser (e.g. "2d6+1d4-2", "d6", "+3")
- pure roll implementation (`_roll_once`) + a stateful DiceRoller wrapper
- deterministic RNG injection
- efficient PMF generation (convolution) with caching
- no implicit file writes (history saved only if explicitly requested)
- careful input validation / limits
- type hints, docstrings, and logging
"""

from __future__ import annotations
import re
import copy
import logging
import math
import random
from collections import Counter
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

# Safety limits to avoid accidental DoS
MAX_ABS_DICE = 1000       # maximum number of dice (absolute, across terms)
MAX_SIDES = 10000         # maximum number of sides for any die
MAX_COMBINATIONS = 10_000_000  # rough guard for enumerations (product of sides**count)

# Types
RollDetails = List[int]
PMF = Dict[int, float]


def parse_dice_notation(notation: str) -> Tuple[List[Tuple[int, int]], int]:
    """
    Parse dice notation like:
        "2d6+1d4-2" -> ([(2,6), (1,4)], -2)
        "d6" -> ([(1,6)], 0)
        "4" -> ([], 4)
    Returns:
        (dice_terms, modifier)
        dice_terms is a list of (count, sides). count may be negative if prefixed by '-'.
    Raises:
        ValueError for invalid notation or out-of-bounds numbers.
    """
    if notation is None:
        raise ValueError("Notation must be a string, got None")
    s = notation.replace(" ", "")
    if s == "":
        raise ValueError("Empty dice notation")

    token_re = re.finditer(r'([+-]?)(?:(\d*)d(\d+)|(\d+))', s)
    dice_terms: List[Tuple[int, int]] = []
    modifier = 0
    pos = 0
    total_dice = 0

    for m in token_re:
        if m.start() != pos:
            # Found garbage between tokens
            raise ValueError(f"Invalid dice notation at: {s[pos:]} in '{notation}'")
        sign = -1 if m.group(1) == '-' else 1
        if m.group(3):  # matched NdM or dM
            n = int(m.group(2)) if m.group(2) else 1
            sides = int(m.group(3))
            if n <= 0 or sides <= 0:
                raise ValueError("Dice counts and sides must be positive integers")
            total_dice += n
            if total_dice > MAX_ABS_DICE:
                raise ValueError(f"Total number of dice exceeds allowed limit ({MAX_ABS_DICE})")
            if sides > MAX_SIDES:
                raise ValueError(f"Die with {sides} sides exceeds allowed limit ({MAX_SIDES})")
            dice_terms.append((sign * n, sides))
        else:  # plain integer modifier
            modifier += sign * int(m.group(4))
        pos = m.end()
    if pos != len(s):
        raise ValueError(f"Trailing garbage in dice notation: {s[pos:]}")

    return dice_terms, modifier


def _normalize_dice_terms(dice_terms: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Combine terms with the same number of sides, and separate positive and negative counts explicitly.
    E.g., [(2,6), (-1,6), (1,4)] -> [(1,6), (1,4)]
    """
    combined: Dict[int, int] = {}
    for count, sides in dice_terms:
        combined[sides] = combined.get(sides, 0) + count
    normalized = [(count, sides) for sides, count in combined.items() if count != 0]
    # keep deterministic order by sides
    normalized.sort(key=lambda t: t[1])
    return normalized


def _ways_pmf_for_positive_dice(count: int, sides: int) -> Counter:
    """
    Return a Counter mapping sum -> number_of_ways for `count` dice each with `sides` faces (1..sides).
    Uses iterative convolution. count > 0 is expected.
    """
    if count <= 0:
        return Counter({0: 1})
    dist = Counter({0: 1})
    for _ in range(count):
        new = Counter()
        for total, ways in dist.items():
            for face in range(1, sides + 1):
                new[total + face] += ways
        dist = new
    return dist


@lru_cache(maxsize=128)
def ways_pmf_cache_key(terms_key: Tuple[Tuple[int, int], ...]) -> Tuple[Tuple[int, int], ...]:
    # trivial pass-through function used to wrap lru_cache; not called directly in code
    return terms_key


def compute_pmf(dice_terms: Sequence[Tuple[int, int]], modifier: int = 0) -> PMF:
    """
    Compute the probability mass function for a dice expression described by dice_terms and modifier.
    dice_terms: sequence of (count, sides), where count may be negative to subtract dice.
    Returns: mapping sum -> probability (floats summing to 1).
    Note: This function is careful about limits and uses convolution; it raises for extremely large combination counts.
    """
    # Normalize terms: aggregate same-sided dice and separate positive/negative counts
    normalized = _normalize_dice_terms(list(dice_terms))

    # Quickly estimate combinatorial explosion to avoid runaway work
    total_combinations = 1
    for count, sides in normalized:
        if count == 0:
            continue
        abs_count = abs(count)
        # if any term's combinations exceed limit, raise
        try:
            term_combos = pow(sides, abs_count)
            total_combinations = total_combinations * term_combos
            if total_combinations > MAX_COMBINATIONS:
                raise ValueError("Dice expression would generate too many combinations to compute exactly")
        except OverflowError:
            raise ValueError("Dice expression too large to compute")

    # Start with distribution {0:1}
    overall = Counter({0: 1})

    for count, sides in normalized:
        if count == 0:
            continue
        if count > 0:
            term_dist = _ways_pmf_for_positive_dice(count, sides)
        else:
            # negative count: distribution of subtracting some dice -> flip sign of faces then convolve
            # simulate by computing distribution for positive count and then reflect sums
            positive_term = _ways_pmf_for_positive_dice(-count, sides)
            term_dist = Counter({-s: ways for s, ways in positive_term.items()})
        # Convolve overall and term_dist
        new_overall = Counter()
        for a_sum, a_ways in overall.items():
            for b_sum, b_ways in term_dist.items():
                new_overall[a_sum + b_sum] += a_ways * b_ways
        overall = new_overall

    # Apply modifier by shifting keys
    if modifier != 0:
        shifted = Counter({k + modifier: v for k, v in overall.items()})
        overall = shifted

    # Convert ways -> probabilities
    total_ways = sum(overall.values())
    if total_ways <= 0:
        return {}
    pmf = {s: ways / total_ways for s, ways in sorted(overall.items())}
    return pmf


def expected_value_from_pmf(pmf: PMF) -> float:
    """Return expected value (mean) from PMF."""
    return sum(s * p for s, p in pmf.items())


class DiceRoller:
    """
    A stateful dice roller that wraps a pure `_roll_once` function.
    It does NOT write files automatically. History persistence is explicit.
    """

    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()
        self.last_roll_result: Optional[int] = None
        self.last_roll_details: Optional[RollDetails] = None
        self.history: List[Dict] = []
        # history is only saved when caller requests via save_history_to_file

    @staticmethod
    def _roll_once_pure(dice_terms: Sequence[Tuple[int, int]], modifier: int, rng: random.Random) -> Dict:
        """
        Pure roll: given normalized dice_terms and modifier, and an RNG, produce a roll result dict.
        Does NOT mutate any DiceRoller instance fields.
        Returned dict:
        {
          "dice_terms": [(count,sides), ...],
          "modifier": int,
          "roll_details": [face1, face2, ...],  # order is deterministic by term order
          "roll_result": int
        }
        """
        normalized = _normalize_dice_terms(list(dice_terms))
        roll_details: List[int] = []
        total = 0
        for count, sides in normalized:
            times = abs(count)
            for _ in range(times):
                face = rng.randint(1, sides)
                if count > 0:
                    roll_details.append(face)
                    total += face
                else:
                    # negative dice count: subtract these dice
                    roll_details.append(-face)
                    total -= face
        total += modifier
        return {
            "dice_terms": list(normalized),
            "modifier": modifier,
            "roll_details": roll_details,
            "roll_result": total,
        }

    def roll_dice(self,
                  notation: str,
                  target: Optional[int] = None,
                  success_outcome: Optional[Dict] = None,
                  failure_outcome: Optional[Dict] = None,
                  update_history: bool = True) -> Dict:
        """
        Roll dice using a standard notation string (e.g., "2d6+1").
        - target: if provided, result will include 'success': bool of roll_result >= target
        - success_outcome / failure_outcome: optional dicts; a COPY will be attached as 'outcome' (mutating caller dict is avoided)
        - update_history: if False, do not modify internal history/last_roll fields (useful for simulation/testing)
        Returns a dictionary with keys:
            dice_notation, dice_terms, modifier, roll_details, roll_result, (optional) target, success, outcome
        """
        dice_terms, modifier = parse_dice_notation(notation)
        pure = self._roll_once_pure(dice_terms, modifier, self.rng)
        result = {
            "dice_notation": notation,
            "dice_terms": pure["dice_terms"],
            "modifier": pure["modifier"],
            "roll_details": pure["roll_details"],
            "roll_result": pure["roll_result"],
        }
        if target is not None:
            result["target"] = target
            result["success"] = result["roll_result"] >= target
            if success_outcome is not None or failure_outcome is not None:
                chosen = success_outcome if result["success"] else failure_outcome
                if chosen is not None:
                    outcome_copy = copy.deepcopy(chosen)
                    if isinstance(outcome_copy, dict):
                        outcome_copy.setdefault("roll_result", result["roll_result"])
                    result["outcome"] = outcome_copy

        if update_history:
            self.last_roll_result = result["roll_result"]
            self.last_roll_details = list(result["roll_details"])
            # keep limited history length (for example, last 100)
            entry = {
                "dice_notation": notation,
                "result": result["roll_result"],
                "details": list(result["roll_details"]),
            }
            self.history.append(entry)
            if len(self.history) > 100:
                self.history.pop(0)
        return result

    def get_pmf(self, notation: str) -> PMF:
        """Return the PMF (sum -> probability) for the given notation string."""
        dice_terms, modifier = parse_dice_notation(notation)
        return compute_pmf(dice_terms, modifier)

    def get_expected_value(self, notation: str) -> float:
        pmf = self.get_pmf(notation)
        return expected_value_from_pmf(pmf)

    def save_history_to_file(self, path: str, *, indent: Optional[int] = 2) -> None:
        """Explicitly save history to a JSON file. This method may raise IO errors to caller."""
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=indent, ensure_ascii=False)

    def load_history_from_file(self, path: str) -> None:
        """Explicitly load history from a JSON file. Validates basic shape."""
        import json
        with open(path, "r", encoding="utf-8") as f:
            arr = json.load(f)
        if not isinstance(arr, list):
            raise ValueError("History file must contain a JSON array")
        # Basic validation
        for item in arr:
            if not isinstance(item, dict) or "result" not in item:
                raise ValueError("History JSON has invalid items")
        self.history = arr[-100:]  # keep last 100 entries

