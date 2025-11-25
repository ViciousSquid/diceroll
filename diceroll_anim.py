"""
diceroll_anim.py

A deterministic-ish pygame-based dice animator with:
- lazy pygame initialization and robust lifecycle (always quits in finally)
- deterministic RNG injection (so animations can be reproducible if seeded)
- non-blocking or blocking mode + auto_close timeout
- render-to-surface mode (headless friendly)
- graceful fallback when pygame is unavailable (numeric-only render)
"""

from __future__ import annotations
import logging
import math
import random
import time
from typing import Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

try:
    import pygame
    PYGAME_AVAILABLE = True
except Exception:
    pygame = None  # type: ignore
    PYGAME_AVAILABLE = False

# Simple lightweight sprite representation for animation (no external assets required)
DEFAULT_WINDOW_SIZE = (800, 400)


class DiceAnimator:
    """
    Animate dice rolls with pygame. If pygame is not available, falls back to simple numeric output.
    Usage:
        animator = DiceAnimator(seed=42)
        result = animator.animate("2d6+1", roll_result=13, blocking=True, auto_close_after_seconds=3)
    The animator will not write files or mutate unrelated state.
    """

    def __init__(self,
                 window_size: Tuple[int, int] = DEFAULT_WINDOW_SIZE,
                 seed: Optional[int] = None,
                 fps: int = 30):
        self.window_size = window_size
        self._seed = seed
        self.rng = random.Random(seed) if seed is not None else random.Random()
        self.fps = fps
        # animation parameters
        self.die_pixel = 96
        self.bg_color = (30, 30, 30)
        self.die_color = (220, 220, 220)
        self.pip_color = (20, 20, 20)

    def _init_pygame(self):
        if not PYGAME_AVAILABLE:
            raise RuntimeError("pygame is not available in this environment")
        pygame.init()
        # set a simple caption
        pygame.display.set_caption("Dice Animator")

    def _quit_pygame(self):
        if PYGAME_AVAILABLE:
            try:
                pygame.quit()
            except Exception as e:
                logger.debug("pygame.quit() raised: %s", e)

    def _draw_die_on_surface(self, surface, center_xy, size_px, pip_value: int):
        """
        Draw a simple rounded-square die with pips on a pygame surface.
        If pygame is not available, this function is not used.
        """
        # draw background rectangle
        rect = pygame.Rect(0, 0, size_px, size_px)
        rect.center = center_xy
        pygame.draw.rect(surface, self.die_color, rect, border_radius=max(4, size_px // 12))
        # draw pips
        offsets = {
            1: [(0, 0)],
            2: [(-0.25, -0.25), (0.25, 0.25)],
            3: [(-0.25, -0.25), (0, 0), (0.25, 0.25)],
            4: [(-0.25, -0.25), (-0.25, 0.25), (0.25, -0.25), (0.25, 0.25)],
            5: [(-0.25, -0.25), (-0.25, 0.25), (0, 0), (0.25, -0.25), (0.25, 0.25)],
            6: [(-0.25, -0.4), (-0.25, 0), (-0.25, 0.4), (0.25, -0.4), (0.25, 0), (0.25, 0.4)]
        }
        pip_positions = offsets.get(pip_value, offsets[1])
        pip_radius = max(3, size_px // 12)
        for ox, oy in pip_positions:
            cx = int(center_xy[0] + ox * size_px)
            cy = int(center_xy[1] + oy * size_px)
            pygame.draw.circle(surface, self.pip_color, (cx, cy), pip_radius)

    def render_final_frame_to_image(self, roll_details: Sequence[int]) -> Optional[bytes]:
        """
        Render a final image of the dice roll and return PNG bytes.
        Returns None if pygame is not available.
        """
        if not PYGAME_AVAILABLE:
            logger.debug("pygame not available; cannot render image surface")
            return None

        self._init_pygame()
        try:
            surface = pygame.Surface(self.window_size)
            surface.fill(self.bg_color)
            # Layout dice evenly
            n = len(roll_details)
            if n == 0:
                return None
            spacing = self.window_size[0] // (n + 1)
            y = self.window_size[1] // 2
            for i, d in enumerate(roll_details):
                x = spacing * (i + 1)
                pip_value = abs(d) if isinstance(d, int) else 1
                self._draw_die_on_surface(surface, (x, y), self.die_pixel, max(1, min(6, pip_value)))
            # Save surface to PNG bytes
            import io
            img_bytes = io.BytesIO()
            pygame.image.save(surface, img_bytes)
            img_bytes.seek(0)
            data = img_bytes.read()
            return data
        finally:
            self._quit_pygame()

    def animate(self,
                notation: str,
                roll_result: Optional[int] = None,
                roll_details: Optional[Sequence[int]] = None,
                blocking: bool = True,
                auto_close_after_seconds: Optional[float] = 3.0) -> dict:
        """
        Animate a roll. If pygame is not present, simply returns a dict describing the roll.
        Parameters:
            notation: original dice notation string (for display)
            roll_result: if provided, animator will display this final value; otherwise uses roll_details or numeric-only fallback
            roll_details: list of face values (integers). If omitted, animator will display the total only.
            blocking: if True, this call will keep window open until keypress/close or auto_close timeout.
            auto_close_after_seconds: if provided, automatically closes after that many seconds.
        Returns:
            A dict describing the final frame: {"notation": ..., "result": ..., "details": [...]}
        """
        info = {"notation": notation, "result": roll_result, "details": list(roll_details) if roll_details else []}

        if not PYGAME_AVAILABLE:
            logger.info("pygame not available: falling back to numeric-only animator")
            # simply return the info dict; caller can print or otherwise handle it
            return info

        # Begin pygame lifecycle; ensure quit in finally
        self._init_pygame()
        try:
            screen = pygame.display.set_mode(self.window_size)
            clock = pygame.time.Clock()
            start_time = time.time()
            duration = 1.6  # seconds for rolling animation
            final_shown = False

            # Simple deterministic-ish rolling animation: each die will have a seeded sequence of faces
            n = len(info["details"]) if info["details"] else (1 if info["result"] is not None else 0)
            die_sequences = []
            base_seed = self._seed if self._seed is not None else int(time.time() * 1000) & 0xFFFFFFFF
            for i in range(n):
                seq_rng = random.Random(base_seed + i)
                seq = [seq_rng.randint(1, 6) for _ in range(int(self.fps * duration))]
                die_sequences.append(seq)

            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return info
                    if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                        if blocking:
                            return info

                now = time.time()
                elapsed = now - start_time
                screen.fill(self.bg_color)

                # Render current frame of each die
                if elapsed < duration:
                    # in-animation: show sequence frame
                    frame_idx = int(min(len(die_sequences[0]) - 1, elapsed / duration * (len(die_sequences[0]) - 1)))
                    for i in range(n):
                        value = die_sequences[i][frame_idx]
                        # layout
                        spacing = self.window_size[0] // (n + 1)
                        x = spacing * (i + 1)
                        y = self.window_size[1] // 2
                        self._draw_die_on_surface(screen, (x, y), self.die_pixel, value)
                else:
                    # final frame: show provided details or derived from result
                    if info["details"]:
                        for i, d in enumerate(info["details"]):
                            spacing = self.window_size[0] // (n + 1)
                            x = spacing * (i + 1)
                            y = self.window_size[1] // 2
                            pip_value = abs(d) if isinstance(d, int) else 1
                            self._draw_die_on_surface(screen, (x, y), self.die_pixel, max(1, min(6, pip_value)))
                    else:
                        # Single big total
                        font = pygame.font.SysFont(None, 72)
                        text = font.render(str(info["result"]) if info["result"] is not None else "?", True, (255, 255, 255))
                        rect = text.get_rect(center=(self.window_size[0] // 2, self.window_size[1] // 2))
                        screen.blit(text, rect)

                    if not final_shown:
                        final_shown = True
                        final_time = now

                pygame.display.flip()
                clock.tick(self.fps)

                # handle auto-close
                if final_shown and auto_close_after_seconds is not None:
                    if time.time() - final_time > auto_close_after_seconds:
                        return info

        finally:
            self._quit_pygame()
