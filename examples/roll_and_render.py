"""Pure-stdlib example: generate a mixed-dice SVG in the working directory."""
from pathlib import Path
import random

from diceroll import DiceRoller, render_svg

dice = DiceRoller(rng=random.Random(7))
roll = dice.roll(
    "2d4 + d8 + 3d6 + d10 + d12 + d20 - 5",
    target=42,
    d6_colour="random",
)
print(f"Rolled {roll.total}: {roll.faces} (success: {roll.success})")
for component in roll.components:
    if component.colours and any(c is not None for c in component.colours):
        print("D6 colours:", component.colours)
output = Path("dice_roll.svg")
output.write_text(render_svg(roll), encoding="utf-8")
print(f"Saved: {output.resolve()}")
