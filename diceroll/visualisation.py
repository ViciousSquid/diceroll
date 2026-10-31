"""Framework choice with no mandatory graphics dependencies.

\`visualise(result)\` uses Pygame when its importable module is installed,
otherwise returns the existing dependency-free SVG markup. Pass
\`backend="svg"\` or \`backend="pygame"\` to choose explicitly.
"""

from __future__ import annotations

from importlib.util import find_spec

from .core import RollResult
from .pygame_renderer import PygameDiceAnimation
from .svg import render_svg

__all__ = ["pygame_available", "visualise"]


def pygame_available() -> bool:
    """Whether an importable \`pygame\` module is installed (without importing it).

    Either pygame-ce or classic Pygame provides the \`pygame\` import.
    This checks availability, not SDL display or audio initialisation.
    """
    try:
        return find_spec("pygame") is not None
    except (ImportError, ValueError):
        return False


def visualise(
    result: RollResult, *, backend: str = "auto", **options
) -> PygameDiceAnimation | str:
    """Select an installed visualiser.

    \`auto\`: if Pygame is installed, return a \`PygameDiceAnimation\` for
    drawing on the host's Surface, otherwise return self-contained SVG
    markup. Use \`backend="pygame"\` or \`backend="svg"\` to request
    a specific format. Pygame is imported only upon creating an animation.

    Pygame-specific options: \`seed\`, \`duration\`, \`die_size\`, \`columns\`,
    \`title\`. SVG-specific options: \`die_size\`, \`columns\`, \`title\`.
    """
    if backend == "auto":
        backend = "pygame" if pygame_available() else "svg"
    if backend == "pygame":
        return PygameDiceAnimation(result, **options)
    if backend == "svg":
        return render_svg(result, **options)
    raise ValueError("backend must be 'auto', 'pygame' or 'svg'")
