"""Interactive optional Pygame animation, independent of the dice engine.

Install Pygame yourself: pip install pygame-ce
Run from the checkout: python examples/pygame_animation.py

The caller owns the window, events and frame clock. An existing Pygame app
can copy just the construction and \`animation.draw(surface, elapsed)\` lines.
"""
from __future__ import annotations

import random

from diceroll import DiceRoller, PygameDiceAnimation, pygame_available


def main() -> None:
    if not pygame_available():
        raise SystemExit("Pygame is optional: install it with pip install pygame-ce")

    import pygame

    pygame.init()
    try:
        surface = pygame.display.set_mode((1100, 660))
        pygame.display.set_caption("diceroll — independent tumbling dice")
        clock = pygame.time.Clock()

        # Numerical faces and colours are resolved once, before animation.
        result = DiceRoller(rng=random.Random(21)).roll(
            "2d4 + 5d6 + d8 + d10 + d12 + d20 + 3",
            target=45,
            d6_colour="random",
        )
        animation = PygameDiceAnimation(
            result, seed=12, duration=1.8, die_size=88, columns=6,
            title="Mixed dice — red / white / blue",
        )
        started = pygame.time.get_ticks() / 1000.0
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
            elapsed = pygame.time.get_ticks() / 1000.0 - started
            surface.fill((12, 15, 22))
            animation.draw(surface, elapsed)
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
