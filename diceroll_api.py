"""
diceroll_api.py

A thin, typed API wrapper around diceroll.py that:
- exposes a clear RollResult TypedDict
- provides convenience functions for common tasks
- keeps a single DiceRoller instance by default but allows callers to create their own
"""

from __future__ import annotations
from typing import Dict, List, Optional, TypedDict
from dataclasses import dataclass
import logging

from diceroll import DiceRoller, parse_dice_notation

logger = logging.getLogger(__name__)


class RollResult(TypedDict):
    dice_notation: str
    dice_terms: List[tuple]
    modifier: int
    roll_details: List[int]
    roll_result: int
    target: Optional[int]
    success: Optional[bool]
    outcome: Optional[Dict]


_default_roller = DiceRoller()


def roll(dice_notation: str,
         target: Optional[int] = None,
         success_outcome: Optional[Dict] = None,
         failure_outcome: Optional[Dict] = None,
         roller: Optional[DiceRoller] = None,
         update_history: bool = True) -> RollResult:
    """
    Roll dice and return a structured RollResult.
    Parameters:
        dice_notation: e.g., "2d6+1"
        target: optional integer target to compare against
        success_outcome/failure_outcome: optional dicts that will be attached (copied) as 'outcome'
        roller: optional DiceRoller instance; uses module-level default if omitted
        update_history: if False, the dice roller will not update its history (useful for simulations)
    """
    roller = roller or _default_roller
    raw = roller.roll_dice(dice_notation, target=target,
                           success_outcome=success_outcome,
                           failure_outcome=failure_outcome,
                           update_history=update_history)
    # Normalize return to RollResult shape
    res: RollResult = {
        "dice_notation": raw.get("dice_notation"),
        "dice_terms": raw.get("dice_terms", []),
        "modifier": raw.get("modifier", 0),
        "roll_details": raw.get("roll_details", []),
        "roll_result": raw.get("roll_result", 0),
        "target": raw.get("target"),
        "success": raw.get("success"),
        "outcome": raw.get("outcome"),
    }
    return res


def pmf(dice_notation: str, roller: Optional[DiceRoller] = None) -> Dict[int, float]:
    """Return PMF mapping for the notation."""
    roller = roller or _default_roller
    return roller.get_pmf(dice_notation)


def expected(dice_notation: str, roller: Optional[DiceRoller] = None) -> float:
    """Return expected value for the notation."""
    roller = roller or _default_roller
    return roller.get_expected_value(dice_notation)


def roll_multiple_same(sides: int, count: int, roller: Optional[DiceRoller] = None) -> RollResult:
    """Convenience wrapper for rolling 'count' dice of 'sides' sides (notation like '3d6')."""
    if count <= 0:
        raise ValueError("count must be positive")
    if sides <= 0:
        raise ValueError("sides must be positive")
    notation = f"{count}d{sides}"
    return roll(notation, roller=roller)


# Small helper to validate notation quickly
def validate_notation(notation: str) -> bool:
    try:
        parse_dice_notation(notation)
        return True
    except Exception:
        return False
