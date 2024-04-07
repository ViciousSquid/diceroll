from diceroll import DiceRoller
import random
import pygame
import time
import os

class DiceAnimator:
    """
    A class to handle the dice roll animation using Pygame.
    """

    def __init__(self, window_width=300, window_height=300, dice_image_path="images"):
        """
        Initialize the DiceAnimator instance.

        Args:
            window_width (int, optional): The width of the Pygame window. Default is 300.
            window_height (int, optional): The height of the Pygame window. Default is 300.
            dice_image_path (str, optional): The path to the directory containing the dice images. Default is "images".

        Raises:
            ValueError: If no dice image sets are found in the specified directory.
        """
        pygame.init()
        self.window_width = window_width
        self.window_height = window_height
        self.window = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption("Dice Roll")
        self.dice_image_path = dice_image_path
        self.dice_sets = self.load_dice_sets()
        if not self.dice_sets:
            raise ValueError(f"No dice image sets found in the '{dice_image_path}' directory.")
        self.font = pygame.font.Font(None, 36)

    def load_dice_sets(self):
        """
        Load dice images from the specified directory.

        Returns:
            dict: A dictionary containing the loaded dice sets, with colors as keys and lists of dice images as values.
        """
        dice_sets = {}

        for color in ['red', 'white', 'blue', 'black']:
            dice_set = []
            for i in range(1, 7):
                image_path = os.path.join(self.dice_image_path, color, f"dice{i}.png")
                if os.path.exists(image_path):
                    dice_set.append(pygame.image.load(image_path))
            if dice_set:
                dice_sets[color] = dice_set

        return dice_sets

    def animate_dice_roll(self, dice_type, dice_color, dice_roller, target=None):
        """
        Animates the dice roll in the Pygame window.
        Uses the DiceRoller instance to perform the actual roll.
        Always displays the animation for a single die, regardless of the number of dice specified.

        Args:
            dice_type (str): The type of dice to roll (e.g., "2d6" or "3d8+1d4" for a combination of dice).
            dice_color (str): The color of the dice set to use (e.g., "red", "white", "blue", or "black").
            dice_roller (DiceRoller): An instance of the DiceRoller class.
            target (int, optional): The target number to beat. If provided, the function will display the dice type and target.

        Returns:
            int: The result of the dice roll.

        Raises:
            ValueError: If an invalid dice color is provided.
        """
        if dice_color not in self.dice_sets:
            raise ValueError(f"Invalid dice color: {dice_color}. Available colors are: {', '.join(self.dice_sets.keys())}")

        clock = pygame.time.Clock()
        shake_duration = 0.75  # Duration of the shaking animation in seconds
        tumble_duration = 0.25  # Duration of the tumbling animation in seconds

        # Render the dice type and target text
        dice_and_target_text = f"{dice_type}"
        if target:
            dice_and_target_text += f"-{target}"
        dice_and_target_render = self.font.render(dice_and_target_text, True, (0, 0, 0))
        dice_and_target_rect = dice_and_target_render.get_rect(midtop=(self.window_width // 2, 10))

        # Shaking animation
        start_time = time.time()
        while time.time() - start_time < shake_duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            self.window.fill((255, 255, 255))  # Clear the window with a white background

            # Display the dice type and target text
            self.window.blit(dice_and_target_render, dice_and_target_rect)

            # Display a random dice image with a slight rotation and offset
            dice_image = random.choice(self.dice_sets[dice_color])
            dice_rect = dice_image.get_rect(center=(self.window_width // 2, self.window_height // 2))
            rotation_angle = random.randint(-5, 5)
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            rotated_dice_image = pygame.transform.rotate(dice_image, rotation_angle)
            rotated_dice_rect = rotated_dice_image.get_rect(center=(self.window_width // 2 + offset_x, self.window_height // 2 + offset_y))
            self.window.blit(rotated_dice_image, rotated_dice_rect)

            pygame.display.flip()  # Update the display
            clock.tick(30)  # Limit the animation frame rate

        # Tumbling animation
        start_time = time.time()
        while time.time() - start_time < tumble_duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            self.window.fill((255, 255, 255))  # Clear the window with a white background

            # Display the dice type and target text
            self.window.blit(dice_and_target_render, dice_and_target_rect)

            # Display a random dice image with a rotation
            dice_image = random.choice(self.dice_sets[dice_color])
            dice_rect = dice_image.get_rect(center=(self.window_width // 2, self.window_height // 2))
            rotation_angle = (time.time() - start_time) / tumble_duration * 360
            rotated_dice_image = pygame.transform.rotate(dice_image, rotation_angle)
            rotated_dice_rect = rotated_dice_image.get_rect(center=(self.window_width // 2, self.window_height // 2))
            self.window.blit(rotated_dice_image, rotated_dice_rect)

            pygame.display.flip()  # Update the display
            clock.tick(60)  # Limit the animation frame rate

        # Perform the actual dice roll
        roll_result = dice_roller.roll_dice(dice_type)

        # Get the first individual roll result (for displaying a single die)
        roll_details = dice_roller.get_last_roll_details()
        single_roll_result = roll_details[0]

        # Display the final dice image and result
        self.window.fill((255, 255, 255))  # Clear the window with a white background

        # Display the dice type and target text
        self.window.blit(dice_and_target_render, dice_and_target_rect)

        # Display the final dice image
        try:
            final_dice_image = self.dice_sets[dice_color][single_roll_result - 1]
        except IndexError:
            # Handle the case where the single_roll_result is out of range
            final_dice_image = self.dice_sets[dice_color][0]  # Use the first image in the set as a fallback
        final_dice_rect = final_dice_image.get_rect(center=(self.window_width // 2, self.window_height // 2))
        self.window.blit(final_dice_image, final_dice_rect)

        # Render and display the roll result text
        result_text = self.font.render(f"Result {roll_result}", True, (0, 0, 0))
        result_rect = result_text.get_rect(midbottom=(self.window_width // 2, self.window_height - 10))
        self.window.blit(result_text, result_rect)

        pygame.display.flip()

        # Wait for a longer duration to display the final result
        pygame.time.delay(3000)

        return roll_result

    def run_animation(self, dice_type, dice_color='blue', target=None):
        """
        Runs the dice roll animation and returns the roll result.

        Args:
            dice_type (str): The type of dice to roll (e.g., "2d6" or "3d8+1d4" for a combination of dice).
            dice_color (str, optional): The color of the dice set to use (e.g., "red", "white", "blue", or "black"). Default is 'blue'.
            target (int, optional): The target number to beat. If provided, the function will display the dice type and target.

        Returns:
            int: The result of the dice roll.
        """
        dice_roller = DiceRoller()
        roll_result = self.animate_dice_roll(dice_type, dice_color, dice_roller, target)
        return roll_result