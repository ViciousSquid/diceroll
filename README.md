# diceroll

**[Full API reference](https://github.com/ViciousSquid/diceroll/blob/1.0.0.0/docs/API.md)** ·

A **dependency-free, installable Python dice module**, extracted from the
reusable parts of MiniWind's dice engine. No Pygame, Qt, game engine or graphical
library is installed or imported. Dice values, colours and exact probability
calculations are available to any project.

The public interface is deliberately small: `DiceRoller.roll()`, immutable
`RollResult` objects, `DiceRoller.distribution()` and the standard-library
`render_svg()` presentation function. No legacy `dicerollAPI`, duplicate
facades, GUI window ownership or implicit disk I/O.



Import it with `import diceroll`. 

## Roll any combination of dice

```python
from diceroll import DiceRoller

dice = DiceRoller()
result = dice.roll("2d4 + 3d6 + d8 + d10 + d12 + d20 - 5", target=42)

print(result.total)       # complete signed total
print(result.faces)       # all individual physical die results
print(result.components)  # per-term signed subtotals and colours
print(result.success)     # True, False or None (when no target)
```

The parser supports `d4`, `2d6`, `d8`, `d10`, `d12`, `d20`,
`2d6-1d4+5` and arbitrary sizes such as `d7` or `2d100`. Mixed types,
numeric modifiers and signed dice terms all work. It strictly rejects invalid
syntax with `DiceNotationError` and imposes resource limits.

### Select D6 colours when rolling

```python
from diceroll import DiceRoller, render_svg
from pathlib import Path

dice = DiceRoller()
red = dice.roll("4d6 + d20", d6_colour="red")
white = dice.roll("4d6 + d20", d6_colour="white")
blue = dice.roll("4d6 + d20", d6_colour="blue")
mixed = dice.roll("12d6 + d4 + d12", d6_colour="random")

# Each random d6 chooses independently from red / white / blue.
for component in mixed.components:
    if component.colours and any(c is not None for c in component.colours):
        print(component.faces, component.colours)

Path("mixed_dice.svg").write_text(render_svg(mixed), encoding="utf-8")
```

The default is `blue`. The `random` choice is **per individual d6**,
not per entire roll. Different d6s can legitimately choose the same colour.
Colours are stored alongside the exact dice faces in the result and JSON
history. Every other die records no colour, because the available coloured
artwork applies to the d6 only. Fixed colours never influence numerical dice
results; random colours are selected only after all numeric dice have rolled.

The original d6 red/white/blue face artwork is included in the wheel. MiniWind
contributes its actual **d4, d8, d10, d12 and d20** illustrations. Together
these cover all six standard tabletop dice. Other die types render as labelled
vector shapes, so unusual expressions do not require additional image assets.

## Visualise without Pygame

```python
from pathlib import Path
from diceroll import DiceRoller, render_svg

result = DiceRoller().roll("2d4 + 3d6 + d8 + d10 + d12 + d20",
                           d6_colour="random")
Path("roll.svg").write_text(render_svg(result), encoding="utf-8")
```

Open the SVG in any browser or embed it in a host application. The renderer
returns **plain SVG text** and embeds image bytes using `data:` URIs, making
the result self-contained. It neither creates windows nor depends on any
graphics framework. It is deliberately static: application-specific animation
and event loops belong to the host program.

## Reproducible rolls and observable results

```python
import random
from diceroll import DiceRoller

dice = DiceRoller(rng=random.Random(7), history_limit=100)

def on_roll(result):
    print(result.source, result.context, result.total)

dice.subscribe(on_roll)
result = dice.roll(
    "d20+2", mode="advantage", source="demo.skill",
    context={"label": "Climbing", "why": "Rough rock"}
)
dice.unsubscribe(on_roll)
```

`mode` is `normal`, `advantage` or `disadvantage`. The latter two roll
twice and keep the higher or lower total. The discarded attempt's total is
retained in `result.alternative_totals`. A custom RNG needs only `randint`.
Callbacks receive a single immutable `RollResult`; subscriber exceptions
are logged and do not undo a completed roll.

## Exact distributions, checks, and simulation

```python
from diceroll import DiceRoller, roll_check, probability_target

dice = DiceRoller()
odds = dice.distribution("2d6-1d4+3")  # exact fractions for all totals
check = roll_check(dice, 0.5, sides=20, label="Skill check")
stats = dice.statistics("2d6", trials=1000)
```

`distribution` supports signed mixed dice and modifiers, uses exact rational
probabilities and never advances the RNG. Large calculations have bounded
cost. `statistics` is Monte Carlo: it advances the RNG but does not emit
events or add roll history. `probability_target` rounds to the chosen die's
resolution, **not** MiniWind's game-specific minimum success chance. For
a 1% chance on d20 the resulting check is impossible, rather than falsely
offering 5%; use a larger-sided die when finer odds matter.

## Explicit history storage

```python
dice = DiceRoller(history_limit=100)  # default 5, 0 disables, None is unlimited
dice.roll("d6", d6_colour="red")
dice.save_history("rolls.json")       # the only operation that writes a file

copy = DiceRoller()
copy.load_history("rolls.json")
result = copy.history[0]
payload = result.to_dict()            # JSON-compatible dictionary
```

No automatic files are generated. Stored dice colours remain associated
with their individual faces after JSON round-trips.

## Tests

Run the suite locally with no third-party test runner:

```bash
python -m unittest discover -s tests -v
```

GitHub Actions validates Python **3.10, 3.12 and 3.14**, wheel building,
wheel installation outside the checkout, all standard dice artwork, mixed
expressions, deterministic random colours, exact probabilities, history,
error handling and dependency-free SVG rendering.

## Version 3 API

This is a deliberate **breaking, clean API release**. The former top-level
`diceroll.py`, `diceroll_api.py`, `diceroll_anim.py`, `DiceAPI`,
`dicerollAPI`, `DiceType`, animation aliases and old duplicate roll
methods are removed. Code should use `from diceroll import DiceRoller`,
`roller.roll(...)` and `render_svg(result)`. Results are typed objects
rather than loosely structured dictionaries; `to_dict()` exists for
serialisation.

No MiniWind or Fio game logic is packaged. MIT licensed.
