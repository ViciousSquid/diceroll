"""Optional, non-blocking Pygame animation of real :class:\`RollResult\` dice.

Importing this module never imports pygame. The renderer only imports it
when instantiated and uses a caller-owned Surface/window/event loop.
There is no required third-party dependency in diceroll.
"""

from __future__ import annotations

import io
import math
import random
from dataclasses import dataclass
from importlib.resources import files

from .core import RollResult

__all__ = ["PygameDiceAnimation", "PygameDieFrame"]

_PIP_HELP = "Pygame visualisation requires pygame: pip install pygame-ce"
_PALETTES = {"red", "white", "blue"}
_ART_SIDES = {4, 8, 10, 12, 20}


@dataclass(frozen=True)
class PygameDieFrame:
    """Visual state for one die at the given elapsed time; never rerolls."""

    sides: int
    face: int
    colour: str | None
    angle: float
    offset_x: float
    offset_y: float
    scale: float
    settled: bool


@dataclass(frozen=True)
class _Motion:
    sides: int
    face: int
    colour: str | None
    delay: float
    stop: float
    speed: float
    phase: float
    spins: float
    bounce: float


class PygameDiceAnimation:
    """Animate a finished roll on any caller-owned :class:\`pygame.Surface\`.

    Construct one animation per :class:\`RollResult\`, then call
    :meth:\`draw\` each frame with elapsed seconds from the start of the
    animation. The application owns its window, input, frame clock and
    event loop. No randomness used for animation alters the dice RNG.

    Each die has an independently seeded delay, face-cycle rate, tumble,
    bounce and stopping time. \`frames(elapsed)\` exposes the frame states
    without touching a display. The definitive face and colour always
    come from the original RollResult.
    """

    def __init__(
        self,
        result: RollResult,
        *,
        seed: int = 0,
        duration: float = 1.25,
        die_size: int = 84,
        columns: int = 6,
        title: str | None = None,
    ):
        if not isinstance(result, RollResult):
            raise TypeError("result must be a RollResult")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)):
            raise ValueError("duration must be a finite positive number")
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("duration must be a finite positive number")
        if isinstance(die_size, bool) or not isinstance(die_size, int) or not 40 <= die_size <= 256:
            raise ValueError("die_size must be an integer from 40 to 256")
        if isinstance(columns, bool) or not isinstance(columns, int) or not 1 <= columns <= 20:
            raise ValueError("columns must be an integer from 1 to 20")
        if title is not None and not isinstance(title, str):
            raise TypeError("title must be a string or None")

        # Only this constructor imports pygame. Merely importing diceroll,
        # calling render_svg, or checking availability remains headless.
        try:
            import pygame
        except ImportError as exc:
            raise ImportError(_PIP_HELP) from exc

        source_dice: list[tuple[int, int, str | None]] = []
        for component in result.components:
            if not component.faces:
                continue
            try:
                sides = int(component.notation.split("d", 1)[1])
            except (ValueError, IndexError) as exc:
                raise ValueError("invalid die notation in RollResult") from exc
            if len(component.colours) != len(component.faces):
                raise ValueError("RollResult has invalid per-die colours")
            for face, colour in zip(component.faces, component.colours):
                if not isinstance(face, int) or not 1 <= face <= sides:
                    raise ValueError("RollResult has an invalid face")
                if sides == 6:
                    if colour not in _PALETTES:
                        raise ValueError("d6 needs a stored red, white or blue colour")
                elif colour is not None:
                    raise ValueError("only d6 may have a stored colour")
                source_dice.append((sides, face, colour))
        if not source_dice:
            raise ValueError("RollResult contains no dice")

        self.result = result
        self.die_size = die_size
        self.columns = columns
        self.title = result.notation if title is None else title
        self._pygame = pygame
        self._asset_cache: dict[tuple[int, int, str | None], object] = {}
        self._font_cache: dict[tuple[int, bool], object] = {}
        independent_rng = random.Random(seed)
        self._motions = tuple(
            _Motion(
                sides=sides, face=face, colour=colour,
                delay=independent_rng.uniform(0.0, 0.22 * duration),
                stop=0.0,
                speed=independent_rng.uniform(11.0, 23.0),
                phase=independent_rng.random(),
                spins=independent_rng.choice((-1.0, 1.0)) *
                      independent_rng.uniform(540.0, 1260.0),
                bounce=independent_rng.uniform(0.55, 1.0),
            )
            for sides, face, colour in source_dice
        )
        # Compute staggered end times without using the dice's RNG.
        self._motions = tuple(
            _Motion(
                sides=m.sides, face=m.face, colour=m.colour, delay=m.delay,
                stop=m.delay + independent_rng.uniform(0.62, 1.10) * duration,
                speed=m.speed, phase=m.phase, spins=m.spins, bounce=m.bounce,
            )
            for m in self._motions
        )
        self.total_duration = max(m.stop for m in self._motions)

    @staticmethod
    def _time(elapsed: float) -> float:
        if isinstance(elapsed, bool) or not isinstance(elapsed, (int, float)):
            raise ValueError("elapsed must be a finite nonnegative number")
        if not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError("elapsed must be a finite nonnegative number")
        return float(elapsed)

    @property
    def timings(self) -> tuple[tuple[float, float], ...]:
        """Per-die (start, settle) seconds; useful for orchestration/tests."""
        return tuple((m.delay, m.stop) for m in self._motions)

    def is_finished(self, elapsed: float) -> bool:
        return self._time(elapsed) >= self.total_duration

    def frames(self, elapsed: float) -> tuple[PygameDieFrame, ...]:
        """Deterministically sample every die without advancing any RNG."""
        t = self._time(elapsed)
        states = []
        for m in self._motions:
            if t >= m.stop:
                states.append(PygameDieFrame(
                    m.sides, m.face, m.colour, 0.0, 0.0, 0.0, 1.0, True
                ))
                continue
            active = max(0.0, t - m.delay)
            span = m.stop - m.delay
            progress = min(1.0, active / span)
            if t < m.delay:
                face = (int(m.phase * m.sides) % m.sides) + 1
            else:
                face = (int(m.phase * m.sides + active * m.speed) % m.sides) + 1
            # Die-specific phase, speed, bounce and stopping times. Ease all
            # motion continuously to the exact final authored dice face.
            fade = (1.0 - progress) ** 1.5
            angle = m.spins * progress * fade
            offset_x = math.sin((active * m.speed + m.phase * 7) * 1.2) * (
                self.die_size * 0.14 * fade
            )
            offset_y = -abs(math.sin((active * m.speed + m.phase * 5) * 0.9)) * (
                self.die_size * 0.38 * m.bounce * fade
            )
            scale = 1.0 + 0.12 * fade * math.sin(active * m.speed * 1.7 + m.phase)
            states.append(PygameDieFrame(
                m.sides, face, m.colour, angle, offset_x, offset_y,
                max(0.65, scale), False,
            ))
        return tuple(states)

    def _font(self, size: int, *, bold: bool = False):
        pg = self._pygame
        if not pg.font.get_init():
            pg.font.init()
        key = (size, bold)
        if key not in self._font_cache:
            font = pg.font.Font(None, size)
            font.set_bold(bold)
            self._font_cache[key] = font
        return self._font_cache[key]

    def _texture(self, sides: int, face: int, colour: str | None):
        """Load package artwork without requiring an SDL display/window."""
        key = (sides, face, colour)
        if key in self._asset_cache:
            return self._asset_cache[key]
        pg = self._pygame
        name = None
        if sides == 6 and colour in _PALETTES:
            ext = "jpg" if colour == "white" else "png"
            name = f"{colour}/dice{face}.{ext}"
        elif sides in _ART_SIDES:
            name = f"blank_d{sides}.png"
        resource = files("diceroll").joinpath("images", *(name or "").split("/")) if name else None
        if resource is not None and resource.is_file():
            image = pg.image.load(io.BytesIO(resource.read_bytes()), resource.name)
            image = pg.transform.smoothscale(image, (self.die_size, self.die_size))
        else:
            image = pg.Surface((self.die_size, self.die_size), pg.SRCALPHA)
            pg.draw.circle(image, (44, 69, 108),
                           (self.die_size // 2, self.die_size // 2),
                           self.die_size // 2 - 3)
            pg.draw.circle(image, (190, 204, 235),
                           (self.die_size // 2, self.die_size // 2),
                           self.die_size // 2 - 3, 2)
        if sides != 6 or name is None:
            font = self._font(max(22, self.die_size // 2), bold=True)
            label = font.render(str(face), True, (245, 248, 255))
            image.blit(label, label.get_rect(center=(self.die_size // 2,
                                                      self.die_size // 2)))
        self._asset_cache[key] = image
        return image

    @property
    def panel_size(self) -> tuple[int, int]:
        cols = min(self.columns, len(self._motions))
        rows = (len(self._motions) + cols - 1) // cols
        stride = self.die_size + max(18, self.die_size // 4)
        return (
            max(320, 48 + cols * stride),
            112 + rows * (stride + 21),
        )

    def draw(
        self,
        surface,
        elapsed: float,
        *,
        center: tuple[int, int] | None = None,
    ):
        """Draw one animation frame on a host-owned Pygame Surface.

        Returns the occupied pygame.Rect. Does not call display.flip,
        pygame.init/quit, pygame.event.get, or pygame.time.Clock.
        Repeated calls with the same elapsed time produce the same pixels.
        """
        pg = self._pygame
        if not isinstance(surface, pg.Surface):
            raise TypeError("surface must be a pygame.Surface")
        states = self.frames(elapsed)
        panel_w, panel_h = self.panel_size
        if center is None:
            center = surface.get_rect().center
        panel = pg.Rect(0, 0, panel_w, panel_h)
        panel.center = center
        pg.draw.rect(surface, (24, 28, 41), panel, border_radius=14)
        pg.draw.rect(surface, (76, 84, 108), panel, width=1, border_radius=14)

        heading = self._font(25, bold=True).render(
            self.title, True, (242, 244, 252)
        )
        surface.blit(heading, heading.get_rect(center=(panel.centerx,
                                                       panel.top + 28)))
        cols = min(self.columns, len(states))
        stride = self.die_size + max(18, self.die_size // 4)
        for index, frame in enumerate(states):
            row, col = divmod(index, cols)
            count_in_row = min(cols, len(states) - row * cols)
            base_x = panel.centerx - count_in_row * stride / 2 + (
                col + 0.5
            ) * stride
            base_y = panel.top + 66 + row * (stride + 21) + self.die_size / 2
            texture = self._texture(frame.sides, frame.face, frame.colour)
            transformed = pg.transform.rotozoom(
                texture, frame.angle, frame.scale
            )
            position = (
                round(base_x + frame.offset_x),
                round(base_y + frame.offset_y),
            )
            surface.blit(transformed, transformed.get_rect(center=position))
            name = f"d{frame.sides}"
            if frame.colour is not None:
                name += f" ({frame.colour})"
            label = self._font(17).render(name, True, (186, 202, 228))
            surface.blit(
                label, label.get_rect(
                    center=(round(base_x), round(base_y + self.die_size / 2 + 16))
                ),
            )
        footer = f"TOTAL {self.result.total}"
        if self.result.target is not None:
            footer += "  /  " + ("SUCCESS" if self.result.success else "FAILED")
        footer_label = self._font(23, bold=True).render(
            footer, True, (242, 223, 161)
        )
        surface.blit(
            footer_label,
            footer_label.get_rect(center=(panel.centerx, panel.bottom - 26)),
        )
        return panel
