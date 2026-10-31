# diceroll

A small, reusable **Python dice library**. The core has **no third-party
dependencies, no GUI, no automatic file writes, and no game-specific rules**.
It grew out of the original diceroll project; the new parsing, seeded rolls,
event listeners and structured results were developed further in MiniWind.

The existing Pygame renderer remains available as an optional feature. This
library has no dependency on MiniWind, Fio, Qt, a game loop, or a specific RPG.

## Install

From a checkout:

```sh
python -m pip install .
# Optional Pygame animations:
python -m pip install ".[animation]"
```

Import `DiceRoller` from `diceroll`, or the higher-level `DiceAPI` (also
available under its historic name `dicerollAPI`) from `diceroll_api`.

## Quick start

```python
from diceroll import DiceRoller

dice = DiceRoller()
result = dice.roll_dice("d20 + 2d6 - 3", target=15)
print(result["roll_result"], result["success"])
print(result["roll_details"])  # actual dice faces, excluding modifiers
print(result["components"])    # each signed term and its subtotal
```

Notation supports `d20`, `2d6`, `3d8+1d4`, `d20+3`,
`2d6-1d4+5` and whitespace. Malformed expressions raise
`DiceNotationError` (a subclass of `ValueError`). Bounds protect against
unreasonably large counts, die sizes, and probability requests. Arbitrary dice
sides are supported; there is no imposed set of tabletop dice.

### Reproducible rolls

```python
import random
from diceroll_api import DiceAPI

api = DiceAPI(rng=random.Random(7))
assert api.roll_dice("2d6+2")["roll_result"] == 7
```

Any instance providing `randint(a, b)` can be injected.

### Events are UI-independent

```python
def on_roll(result, source, context):
    print(source, result["roll_result"], context.get("label"))

dice.add_roll_listener(on_roll)
dice.request_roll("1d20", target=12, source="my-app.skill",
                  context={"label": "Climbing check", "why": "Wet rock"})
dice.remove_roll_listener(on_roll)
```

Subscribers receive `(result, source, context)`. An exception in a subscriber
is logged but does not invalidate a completed dice roll. Build any visualisation
as a subscriber, without coupling the dice service to that renderer.

### Generic probability utilities

```python
from diceroll import DiceRoller, probability_target, roll_check

dice = DiceRoller()
distribution = dice.get_dice_probabilities("2d6")
assert distribution[7] == 6 / 36

target = probability_target(0.5, sides=20)  # 11: need 11 or higher
result = roll_check(dice, 0.5, sides=20, label="Example")
```

`probability_target` rounds probabilities to the nearest number of winning
faces. Values too small to represent on the chosen die can become impossible
(`target > sides`). This is deliberate: **the library does not impose
MiniWind's game-specific rule that every nonzero chance must have a winning
face**. If your application needs more granularity, select a die with more sides
or perform its probability check using its own RNG.

Exact probability distributions currently support one positive homogeneous
`NdM` term. Mixed terms and modifiers can still be rolled normally.

### Optional history and explicit persistence

```python
dice = DiceRoller(save_rolls=True)
dice.roll_dice("1d6")
dice.save_last_5_rolls("recent.txt")
dice.save_roll_history_to_file("history.json")
history = DiceRoller().load_roll_history_from_file("history.json")
```

`save_rolls=True` accumulates full history in memory. **It does not create
files on every roll.** Writing requires an explicit file path. The five most
recent rolls are always held in memory. `save_format="json"` changes the
format used by `save_last_5_rolls`.

`get_roll_statistics(expression, trials)` is a simulation helper; it does not
emit events or alter the roll history.

### Legacy API and optional animation

```python
from diceroll_api import dicerollAPI, DiceType

api = dicerollAPI()
api.roll_dice("1d20", target_value=10)
api.roll_saving_throw(DiceType.D20, target_value=12)
api.roll_with_advantage("2d6")
```

The separate `diceroll_anim.DiceAnimator` is a Pygame frontend, imported
only if explicitly requested. Its existing `run_animation(...)` interface
remains available. Pygame is not imported by `diceroll` or `diceroll_api`.

## API migration (v2)

- `dicerollAPI` remains available; `DiceAPI` is the preferred class name.
- Invalid expressions now **raise** `DiceNotationError` instead of printing an
  error and returning `None` from `dicerollAPI.roll_dice`.
- `get_roll_sum` returns the full result, **including numeric modifiers**.
- `roll_saving_throw` treats `success_threshold` as the threshold to compare.
- `save_rolls=True` records in memory; writing is always **explicit**.
- `roll_dice` additionally includes `components` and `modifier` keys;
  existing `dice_notation`, `roll_result`, and `roll_details` remain.
- No GUI or backend is imported by core modules.
- Application-specific combat/loot/quest mechanics are intentionally **not**
  part of the library.

## Tests

```sh
python -m unittest discover -s tests -v
```

## Licence

MIT. Originally designed for the [Adventure!](https://github.com/ViciousSquid/Adventure)
interactive story engine; the standalone library can be used by any project.
