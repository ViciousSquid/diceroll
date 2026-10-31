# API reference — diceroll 3.0.0

**Distribution:** `vicioussquid-diceroll` · **Import:** `diceroll` · **Python:** 3.10+ · **Runtime dependencies:** none · **Licence:** MIT

This document describes the API actually exported by
[`diceroll/__init__.py`](../diceroll/__init__.py). It documents the
**breaking v3 interface**, not the removed legacy `dicerollAPI` facade.

## Installation and first roll

Install from the repository (or, once published, from PyPI):

```console
python -m pip install .
```

```python
from diceroll import DiceRoller, render_svg

roller = DiceRoller()
result = roller.roll(
    "2d4 + 3d6 + d8 + d10 + d12 + d20 - 5",
    target=35,
    d6_colour="random",
)
print(result.total, result.faces, result.success)

with open("dice.svg", "w", encoding="utf-8") as output:
    output.write(render_svg(result))
```

`render_svg` returns **static, self-contained SVG text**; it does not
require Pygame, Qt, a display server, or any external renderer. To display
the SVG, use a browser or the host application's own UI facilities.

## Public symbol index

These are the names exported from `diceroll`:

| Symbol | Kind | Purpose |
| --- | --- | --- |
| `DiceRoller` | class | Roll dice, manage events/history and calculate probabilities |
| `RollResult` | frozen dataclass | Immutable completed roll |
| `RollComponent` | frozen dataclass | Signed component and individual coloured faces |
| `DiceTerm` | frozen dataclass | Parsed dice or modifier expression term |
| `DiceNotationError` | exception | Invalid dice expression |
| `parse_dice_notation` | function | Strict expression parser |
| `probability_target` | function | Chance-to-die-target conversion |
| `roll_check` | function | Generic probability check |
| `render_svg` | function | Static dependency-free SVG |
| `pygame_available` | function | Detect installed Pygame without importing it |
| `visualise` | function | Auto-select Pygame animation or SVG |
| `PygameDiceAnimation` | class | Optional, caller-driven per-die tumbling animation |
| `PygameDieFrame` | frozen dataclass | Snapshot of a die's visual state |

Core calculations and SVG have **zero third-party dependencies**.
Pygame is optional, auto-detected at runtime and imported only when a
Pygame animation instance is constructed.

## Notation and parsing

### `parse_dice_notation(notation: str) -> tuple[tuple[DiceTerm, ...], str]`

Accepts terms of the form `NdS` (N dice with S sides), `dS` (one die), and
integer modifiers separated by `+` or `-`. Uppercase `D` and whitespace
are accepted. The returned second value is the trimmed original notation.

```python
from diceroll import parse_dice_notation

terms, original = parse_dice_notation("d20 + 2D6 - 3")
assert original == "d20 + 2D6 - 3"
assert [(t.sign, t.count, t.sides, t.modifier) for t in terms] == [
    (1, 1, 20, 0),
    (1, 2, 6, 0),
    (-1, 0, 0, 3),
]
```

Supported examples include `d4`, `3d6`, `d8+d10+d12+d20`,
`2d100-d7+5` and `2d4 + 3d6 + d8 + d10 + d12 + d20 - 5`.
**Any integer number of sides from 2 through 10,000 is supported.**
Only the common d4/d6/d8/d10/d12/d20 types have bundled artwork.

The parser *does not* support `*`, `/`, parentheses, `k`/`d`
keep/drop notation, exploding dice, rerolls, or arbitrary Python
expressions. Invalid or partially matched expressions raise
`DiceNotationError`, which inherits from `ValueError`.

Current parser safety limits:

| Limit | Value |
| --- | ---: |
| Expression length | 4,096 characters |
| Number of terms | 128 |
| Dice per term | 1,000 |
| Total dice across expression | 10,000 |
| Sides per die | 2–10,000 |
| Magnitude of each numeric modifier | 1,000,000,000 |

### `DiceTerm`

A frozen dataclass with integer fields `sign` (1 or -1), `count`,
`sides`, and `modifier` (default 0).

For dice terms, `count` and `sides` describe the dice, while
`modifier=0`. For a numeric term, `count=sides=0`, and the integer is
stored in `modifier`. Its `notation: str` property returns the
**unsigned** canonical term (for example `"2d6"` or `"3"`).
Always read `sign` separately.

## `DiceRoller`

### `DiceRoller(*, rng=None, history_limit: int | None = 5)`

Constructs an independent roller.

| Parameter | Default | Meaning |
| --- | --- | --- |
| `rng` | `None` | Optional random generator with a `randint(a, b)` method; otherwise a fresh `random.Random()` is used |
| `history_limit` | `5` | Results retained in memory; `0` disables history and `None` retains unlimited results |

`rng` is accessible as `roller.rng`. Use a seeded random generator for
deterministic tests:

```python
import random
from diceroll import DiceRoller

roller = DiceRoller(rng=random.Random(7), history_limit=100)
assert roller.roll("2d6+2").total == 7
```

**Warning:** `random.Random` is not cryptographically secure. This
library is appropriate for games, simulation and tabletop utilities, not
cryptographic or regulated gambling use cases.

### `roll(notation: str, *, target: int | None = None, mode: str = "normal", source: str = "library", context=None, d6_colour: str = "blue") -> RollResult`

Rolls one complete dice expression and returns an immutable typed result.

| Parameter | Meaning |
| --- | --- |
| `notation` | Valid expression such as `"2d4+d6-3"` |
| `target` | Optional **inclusive** success threshold; `total >= target` |
| `mode` | `"normal"`, `"advantage"`, or `"disadvantage"` |
| `source` | Free-form label for the caller, recorded on the result |
| `context` | Optional metadata mapping, copied into the result |
| `d6_colour` | `"blue"` (default), `"red"`, `"white"`, or `"random"` |

`normal` rolls once. `advantage` rolls the entire expression **twice**
and retains the higher total; `disadvantage` retains the lower total.
Ties retain the first attempt. `alternative_totals` contains the other
attempt's **total only**, not its faces. One `RollResult` is published
and added to history for each call, regardless of mode.

```python
hit = roller.roll(
    "d20+3",
    target=15,
    mode="advantage",
    source="myapp.attack",
    context={"target_name": "Bandit"},
)
if hit.success:
    print("Attack succeeds")
```

Invalid expressions raise `DiceNotationError`; invalid `mode` or
`d6_colour` raises `ValueError`; an invalid `target` raises
`TypeError` (the implementation requires an integer or `None` and
rejects booleans).

#### D6 colour selection

The original red, white, and blue **d6 face images** are shipped with
the package. Set the desired colour at roll time:

```python
red = roller.roll("3d6+d8", d6_colour="red")
white = roller.roll("3d6+d8", d6_colour="white")
blue = roller.roll("3d6+d8", d6_colour="blue")
mixed = roller.roll("12d6+d20", d6_colour="random")

for part in mixed.components:
    if any(colour is not None for colour in part.colours):
        print(part.faces, part.colours)
```

`random` independently chooses red, white or blue **for each d6**;
repeated colours in a single roll are expected. The exact selection for
every die is preserved in `RollComponent.colours` and history JSON.
Non-d6 dice have `None` as their colour.

All numeric die faces are rolled first. Therefore changing from a fixed
colour to `random` does **not** change the current result's numeric faces
for an identically seeded RNG; however, random colour selection consumes
extra values from that RNG, so **subsequent rolls can differ**.

### `history -> tuple[RollResult, ...]`

A snapshot of retained results, oldest to newest. A `roll` call
appends one result unless `history_limit=0`. Neither probability
calculation nor statistics updates history.

### `subscribe(listener: Callable[[RollResult], None]) -> None`

Registers a callback. A registered callback receives **one**
`RollResult` after each completed roll. Duplicate registrations are
ignored; a non-callable listener raises `TypeError`. Notifications
are synchronous, not background work.

### `unsubscribe(listener) -> None`

Unregisters the callback. Removing an unregistered callback has no effect.

```python
def show_result(result):
    print(result.source, result.total, result.context)

roller.subscribe(show_result)
roller.roll("d20", source="example", context={"reason": "Skill check"})
roller.unsubscribe(show_result)
```

An exception in one listener is logged but does not cancel the roll or
prevent other listeners from being invoked. This is not a thread-safety
guarantee; the host application owns its event-loop/thread coordination.

### `distribution(notation: str) -> dict[int, fractions.Fraction]`

Returns the **exact** probability of each possible **signed total**,
including mixed die sizes and numeric modifiers. Values are
`fractions.Fraction`, not floats.

```python
from fractions import Fraction

odds = roller.distribution("2d6")
assert odds[7] == Fraction(1, 6)
assert sum(odds.values()) == Fraction(1, 1)

other = roller.distribution("d20 - d4 + 2")
```

The method is deterministic, does not advance the injected RNG, does not
add history, and does not call listeners. A computational budget of
approximately 2 million operations guards against expensive distributions;
excessive requests raise `ValueError`.

### `statistics(notation: str, trials: int) -> dict[str, object]`

Simulates the expression `trials` times. Returns a dictionary with keys
`"trials"`, `"mean"`, `"min"`, `"max"`, and `"frequency"`;
`frequency` maps each observed integer total to its count.

```python
stats = roller.statistics("2d6 + 1", trials=1000)
assert sum(stats["frequency"].values()) == 1000
```

**Unlike `distribution`, statistics advances the RNG.** It does not
generate roll history entries or listener notifications. `trials` must
be an integer between 1 and 100,000; invalid counts raise `ValueError`.
Choose `distribution` for exact probabilities and `statistics`
for sampling.

### `save_history(path: str | pathlib.Path) -> None`

Writes the currently retained history to UTF-8 JSON, overwriting the
specified file. The parent directory must already exist. No other
method writes a history file implicitly.

### `load_history(path: str | pathlib.Path) -> None`

Reads a JSON array of serialised `RollResult` objects and **replaces**
the current history, applying `history_limit` (keeping the newest
entries when necessary). It emits no roll events. File errors, JSON
errors and record validation errors propagate.

```python
roller.save_history("history.json")
restored = DiceRoller(history_limit=100)
restored.load_history("history.json")
print(restored.history)
```

## Result dataclasses

### `RollResult`

A `dataclass(frozen=True)`. Do not modify fields; `context` is copied
into a shallow, read-only mapping, although **nested objects inside it
are not recursively frozen**.

| Attribute | Type | Description |
| --- | --- | --- |
| `notation` | `str` | Trimmed original expression |
| `total` | `int` | Final sum, including signed dice and flat modifiers |
| `faces` | `tuple[int, ...]` | Unsigned individual face values |
| `components` | `tuple[RollComponent, ...]` | Each signed component in the expression |
| `modifier` | `int` | Sum of numeric-only modifiers |
| `target` | `int | None` | Inclusive target, when supplied |
| `success` | `bool | None` | Computed property, `None` when no target |
| `source` | `str` | Source passed to `roll` |
| `context` | `Mapping` | Shallow read-only metadata |
| `mode` | `str` | Roll mode |
| `alternative_totals` | `tuple[int, ...]` | Discarded total for advantage/disadvantage; otherwise empty |
| `d6_colour` | `str` | Original colour selection mode |

`result.to_dict() -> dict` converts the record into a
JSON-serialisable structure **provided the caller's context values
are JSON-serialisable**.

`RollResult.from_dict(data: Mapping) -> RollResult` reconstructs
a stored record, checking component totals, face lists and
colour metadata. Use it for records produced by `to_dict()`; it is
not designed as a strict untrusted-input security parser.

### `RollComponent`

A frozen dataclass for one dice term or integer modifier:

| Attribute | Type | Description |
| --- | --- | --- |
| `notation` | `str` | Unsigned canonical term, e.g. `"3d6"` |
| `sign` | `int` | 1 or -1 |
| `faces` | `tuple[int, ...]` | Unsigned faces for dice terms; empty for modifiers |
| `total` | `int` | Signed component subtotal |
| `colours` | `tuple[str | None, ...]` | One red/white/blue colour per d6; `None` for all other dice |

`component.to_dict() -> dict` converts the component into a serialisable
dictionary. Note that `component.total`, **not** `sum(component.faces)`,
accounts for a negative sign. Numeric modifiers have no faces.

## Generic chance utilities

### `probability_target(chance: float, sides: int = 20) -> int`

Returns the minimum winning face on a die with `sides` faces. A check
succeeds when the die rolls **at least** this value. The probability
is rounded to the nearest representable number of successful faces.

```python
from diceroll import probability_target

assert probability_target(0.5, 20) == 11  # 10 winning faces
assert probability_target(1.0, 20) == 1   # all 20 faces win
assert probability_target(0.0, 20) == 21  # impossible
assert probability_target(0.01, 20) == 21 # 1% rounds to 0% on d20
```

A `chance` outside [0, 1] or a nonfinite chance raises
`ValueError`. `sides` must be an integer of at least 2 (booleans
are rejected). The helper is **generic**: it does not apply MiniWind's
rule guaranteeing at least one winning face for tiny nonzero chances.
Use more sides (e.g. d100) if finer probability resolution is required.

### `roll_check(roller: DiceRoller, chance: float, *, sides: int = 20, label: str = "", source: str = "check", context=None) -> RollResult`

Computes `probability_target(chance, sides)` and rolls `1d<sides>`
through the supplied roller with that target. Adds `"chance"` to the
result context and adds `"label"` when a nonempty label is supplied.
All other metadata is passed through. It has the same history and
subscriber behaviour as `DiceRoller.roll`.

```python
from diceroll import DiceRoller, roll_check

check = roll_check(
    DiceRoller(), 0.75, sides=20,
    label="Cross the bridge", source="myapp.skill",
    context={"character": "Scout"},
)
print(check.total, check.target, check.success)
```

## SVG output

### `render_svg(result: RollResult, *, die_size: int = 88, columns: int = 6, title: str | None = None) -> str`

Returns self-contained UTF-8-compatible **SVG markup as a Python string**.
It draws every rolled die and its value, plus the total and optional
target/verdict. Artwork is embedded using base64 `data:` URIs, so
the SVG does not rely on files elsewhere.

| Argument | Default | Description |
| --- | --- | --- |
| `result` | required | An actual `RollResult` |
| `die_size` | `88` | Integer size, 40–256 pixels |
| `columns` | `6` | Integer maximum number of dice per row, 1–20 |
| `title` | `None` | Optional caption; default uses `result.notation` |

The package ships **actual d4, d8, d10, d12 and d20 images** taken from
MiniWind, plus the original **red, white and blue d6 face images**. For
a d6, the renderer uses the stored colour for *that individual die*.
Other dice sizes, such as d7 or d100, display vector fallback artwork
with the correct number. Output is **static**; animations and any host
window lifecycle are outside the library.

```python
from pathlib import Path
from diceroll import DiceRoller, render_svg

roller = DiceRoller()
result = roller.roll("2d4+5d6+d8+d10+d12+d20",
                     d6_colour="random")
svg = render_svg(result, die_size=96, columns=4, title="Treasure roll")
Path("treasure.svg").write_text(svg, encoding="utf-8")
```

`render_svg` raises `TypeError` if `result` is not a
`RollResult`, and `ValueError` for invalid dimensions or incomplete
per-die colour metadata. The result may be large because image data is
embedded; consider caching SVGs in applications that repeatedly show
the same roll.

## Optional Pygame animation (no required dependency)

Install Pygame separately **only if the host application wants it**:

```console
python -m pip install pygame-ce
```

The package dependency list remains empty. Both `pygame-ce` and classic
`pygame` provide the importable `pygame` module. Merely importing
`diceroll` **never imports Pygame** or starts a display.

### `pygame_available() -> bool`

Uses `importlib.util.find_spec("pygame")` to check whether the module
is importable, **without importing Pygame or initialising SDL**. It
does not test a display, audio device or image-decoder availability.

### `visualise(result: RollResult, *, backend: str = "auto", **options) -> PygameDiceAnimation | str`

Selects and instantiates the available representation:

| `backend` | Returned value |
|---|---|
| `"auto"` (default) | `PygameDiceAnimation` when Pygame is installed; otherwise SVG markup `str` |
| `"pygame"` | `PygameDiceAnimation`; raises `ImportError` with an installation hint when unavailable |
| `"svg"` | Always returns self-contained SVG `str` |

`options` accepts `die_size`, `columns`, `title` for both backends;
Pygame additionally accepts `seed` and `duration`.

```python
from diceroll import DiceRoller, visualise, pygame_available

result = DiceRoller().roll("2d4 + 4d6 + d12", d6_colour="random")
presentation = visualise(result)   # automatically chooses an installed backend

if pygame_available():
    # presentation is a PygameDiceAnimation, ready to draw in a host loop
    ...
else:
    # presentation is standalone SVG text
    ...
```

When the application requires a **consistent return type**, request
`backend="svg"` or `backend="pygame"` explicitly rather than `auto`.

### `PygameDiceAnimation(result: RollResult, *, seed: int = 0, duration: float = 1.25, die_size: int = 84, columns: int = 6, title: str | None = None)`

Creates an animation from an **already completed** dice roll.
Every die has its own staggered start time, rolling face cadence,
rotation, bounce and settling time. The animation RNG is separate
from the roller's RNG, so previews cannot change the rolled result.

| Parameter | Description |
|---|---|
| `result` | Immutable `RollResult` (does not reroll) |
| `seed` | Seed used exclusively to derive repeatable animation timings |
| `duration` | Base animation length in seconds; individual dice have staggered durations (must be positive/finite) |
| `die_size` | Die size in pixels, integer from 40 through 256 |
| `columns` | Number of dice per row, integer from 1 through 20 |
| `title` | Optional title, defaulting to the original expression |

Properties and methods:

| API | Description |
|---|---|
| `animation.timings` | Tuple of per-die `(start_seconds, settle_seconds)` |
| `animation.total_duration` | Time (seconds) at which the **last die** settles |
| `animation.panel_size` | `(width, height)` for the rendered panel |
| `animation.frames(elapsed: float)` | Return a deterministic tuple of `PygameDieFrame` states |
| `animation.is_finished(elapsed: float)` | Whether all dice have settled |
| `animation.draw(surface: pygame.Surface, elapsed: float, *, center: tuple[int,int] | None = None) -> pygame.Rect` | Draw one frame onto the caller's Surface and return occupied area |

The public `PygameDieFrame` frozen dataclass exposes
`sides`, `face`, `colour`, `angle`, `offset_x`,
`offset_y`, `scale`, and `settled`. These are
**presentation values**, not alternative game outcomes.

At or after `total_duration`, every die has the **exact**
face and colour stored in the original `RollResult`, with no
remaining movement. During animation, each die cycles preview
faces independently. D6s use the actual red, white and blue
bundled artwork; d4/d8/d10/d12/d20 use MiniWind artwork;
nonstandard dice use vector fallback shapes.

The renderer has **no window lifecycle** and does not poll events,
call `pygame.display.flip()`, or tick a frame clock. The
host application owns the Surface and calls `draw` each frame.

#### Embedded Pygame integration

```python
import time
import pygame
from diceroll import DiceRoller, PygameDiceAnimation

# Existing application owns the Pygame window and frame loop.
result = DiceRoller().roll("d4 + 4d6 + d20", d6_colour="random")
animation = PygameDiceAnimation(result, seed=7, duration=1.4)

started = time.perf_counter()
# During each frame of your existing pygame loop:
elapsed = time.perf_counter() - started
animation.draw(your_existing_surface, elapsed)
# Your application then flips the screen / handles events as usual.
```

For a complete runnable window example, see
[`examples/pygame_animation.py`](../examples/pygame_animation.py).
It demonstrates independent tumbles on the caller-owned Pygame
window, without introducing a required dependency for other users.

Invalid configuration or elapsed time raises `ValueError`; missing
Pygame raises `ImportError`. Pygame's usual image/font errors
may propagate if its installation is broken.

## Working with exceptions

```python
from diceroll import DiceRoller, DiceNotationError

try:
    roll = DiceRoller().roll("2d6 + broken")
except DiceNotationError as exc:
    print(f"Invalid expression: {exc}")
```

`DiceNotationError` is a `ValueError` subclass. Other relevant errors
include `ValueError` for invalid modes, colours, probability inputs or
large distributions, `TypeError` for an invalid target, and ordinary
`OSError` / `json.JSONDecodeError` for file operations.

## Integration considerations

- **No required third-party dependencies:** importing the dice engine and
  rendering SVG use only the standard library. Pygame is imported only when
  a caller constructs an optional animation.
- **Rendering and rules are separate:** use `result` directly in a game,
  backend or test; call `render_svg` only when a picture is needed.
- **No implicit file writes:** callers explicitly request
  `save_history`, or write their own SVGs.
- **RNG ownership:** one seeded RNG can make rolls reproducible, but
  `d6_colour="random"` consumes extra random numbers after the current
  roll. Do not assume identical future rolls if colour settings differ.
- **Game-specific logic stays outside:** combat critical hits, RPG skill
  rules, quest logic and MiniWind's special d20 minimum-win rule are not
  features of this module.
- **Breaking API:** migrating callers must replace the old
  `dicerollAPI().roll_dice(...)` dictionary interface with
  `DiceRoller().roll(...)` and typed `RollResult` fields.

## Running tests

```console
python -m unittest discover -s tests -v
```

The repository's CI builds and installs a wheel and runs the suite on
Python 3.10, 3.12 and 3.14. Separate headless Pygame-enabled jobs exercise
animation surfaces on Linux, macOS and Windows. The tests verify dice
notation, seeded randomness, colour metadata, probabilities, history, the
bundled artwork, dependency-free SVG and independently timed tumbling dice.
