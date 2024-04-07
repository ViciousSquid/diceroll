import random
import pygame
import time
import os
import re

# Initialize Pygame
pygame.init()

# Set up the window
window_width = 300
window_height = 300
window = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Dice Roll")

# Set the path for the dice images
dice_image_path = "images"

# Load dice images
dice_sets = {}

for color in ['red', 'white', 'blue', 'black']:
    dice_set = []
    for i in range(1, 7):
        image_path = os.path.join(dice_image_path, color, f"dice{i}.png")
        if os.path.exists(image_path):
            dice_set.append(pygame.image.load(image_path))
    if dice_set:
        dice_sets[color] = dice_set

# If no dice sets are found, raise an error
if not dice_sets:
    raise ValueError("No dice image sets found in the 'images' directory.")

# Define font for text rendering
font = pygame.font.Font(None, 36)

class DiceRoller:
    """
    A class to encapsulate the dice rolling functionality and maintain the state.
    """

    def __init__(self):
        """
        Initialize the DiceRoller instance with the last roll total and details set to None.
        """
        self.last_roll_total = None
        self.last_roll_details = None

    def roll_dice(self, dice_type):
        """
        Rolls one or more dice of the specified type and returns the sum of the results.
        Updates the last roll total and details.

        Args:
            dice_type (str): The type of dice to roll (e.g., "2d6" or "3d8+1d4" for a combination of dice).

        Returns:
            int: The sum of the dice roll results.
        """
        roll_results = []
        roll_sum = 0

        # Split the dice type string into individual components
        components = re.split(r'(\d+d\d+)', dice_type)
        for component in components:
            match = re.match(r"(\d+)d(\d+)", component)
            if match:
                num_dice, dice_size = int(match.group(1)), int(match.group(2))
                component_results = [random.randint(1, dice_size) for _ in range(num_dice)]
                roll_results.extend(component_results)
                roll_sum += sum(component_results)

        self.last_roll_total = roll_sum
        self.last_roll_details = roll_results
        return roll_sum

    def get_last_roll_total(self):
        """
        Returns the total of the last dice roll.

        Returns:
            int: The total of the last dice roll, or None if no roll has been performed yet.
        """
        return self.last_roll_total

    def get_last_roll_details(self):
        """
        Returns the individual results of the last dice roll.

        Returns:
            list: A list containing the individual results of the last dice roll, or None if no roll has been performed yet.
        """
        return self.last_roll_details

def determine_outcome(roll_result, target, success_outcome, failure_outcome):
    """
    Determines the outcome based on the dice roll result and the target number.
    Checks for critical success or failure based on the maximum or minimum dice roll value.

    Args:
        roll_result (int): The result of the dice roll.
        target (int): The target number to beat.
        success_outcome (dict): The outcome details if the roll is successful.
        failure_outcome (dict): The outcome details if the roll is a failure.

    Returns:
        dict: The outcome details based on the dice roll result.
    """
    max_roll_value = sum(range(1, target + 1))  # Assuming the maximum roll value is the sum of all dice faces
    min_roll_value = len(range(1, target + 1))  # Assuming the minimum roll value is the number of dice

    if roll_result == max_roll_value:
        outcome = {'critical_success': True, 'details': success_outcome['details']}
    elif roll_result == min_roll_value:
        outcome = {'critical_failure': True, 'details': failure_outcome['details']}
    elif roll_result >= target:
        outcome = success_outcome
    else:
        outcome = failure_outcome

    outcome['roll_result'] = roll_result
    return outcome

def animate_dice_roll(dice_type, dice_color, dice_roller, target=None):
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
    """
    clock = pygame.time.Clock()
    shake_duration = 0.75  # Duration of the shaking animation in seconds
    tumble_duration = 0.25  # Duration of the tumbling animation in seconds

    # Render the dice type and target text
    dice_and_target_text = f"{dice_type}"
    if target:
        dice_and_target_text += f"-{target}"
    dice_and_target_render = font.render(dice_and_target_text, True, (0, 0, 0))
    dice_and_target_rect = dice_and_target_render.get_rect(midtop=(window_width // 2, 10))

    # Shaking animation
    start_time = time.time()
    while time.time() - start_time < shake_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        window.fill((255, 255, 255))  # Clear the window with a white background

        # Display the dice type and target text
        window.blit(dice_and_target_render, dice_and_target_rect)

        # Display a random dice image with a slight rotation and offset
        dice_image = random.choice(dice_sets[dice_color])
        dice_rect = dice_image.get_rect(center=(window_width // 2, window_height // 2))
        rotation_angle = random.randint(-5, 5)
        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-5, 5)
        rotated_dice_image = pygame.transform.rotate(dice_image, rotation_angle)
        rotated_dice_rect = rotated_dice_image.get_rect(center=(window_width // 2 + offset_x, window_height // 2 + offset_y))
        window.blit(rotated_dice_image, rotated_dice_rect)

        pygame.display.flip()  # Update the display
        clock.tick(30)  # Limit the animation frame rate

    # Tumbling animation
    start_time = time.time()
    while time.time() - start_time < tumble_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        window.fill((255, 255, 255))  # Clear the window with a white background

        # Display the dice type and target text
        window.blit(dice_and_target_render, dice_and_target_rect)

        # Display a random dice image with a rotation
        dice_image = random.choice(dice_sets[dice_color])
        dice_rect = dice_image.get_rect(center=(window_width // 2, window_height // 2))
        rotation_angle = (time.time() - start_time) / tumble_duration * 360
        rotated_dice_image = pygame.transform.rotate(dice_image, rotation_angle)
        rotated_dice_rect = rotated_dice_image.get_rect(center=(window_width // 2, window_height // 2))
        window.blit(rotated_dice_image, rotated_dice_rect)

        pygame.display.flip()  # Update the display
        clock.tick(60)  # Limit the animation frame rate

    # Perform the actual dice roll
    roll_result = dice_roller.roll_dice(dice_type)

    # Get the first individual roll result (for displaying a single die)
    roll_details = dice_roller.get_last_roll_details()
    single_roll_result = roll_details[0]

    # Display the final dice image and result
    window.fill((255, 255, 255))  # Clear the window with a white background

    # Display the dice type and target text
    window.blit(dice_and_target_render, dice_and_target_rect)

    # Display the final dice image
    final_dice_image = dice_sets[dice_color][single_roll_result - 1]
    final_dice_rect = final_dice_image.get_rect(center=(window_width // 2, window_height // 2))
    window.blit(final_dice_image, final_dice_rect)

    # Render and display the roll result text
    result_text = font.render(str(roll_result), True, (0, 0, 0))
    result_rect = result_text.get_rect(midbottom=(window_width // 2, window_height - 10))
    window.blit(result_text, result_rect)

    pygame.display.flip()

    # Wait for a longer duration to display the final result
    pygame.time.delay(3000)

    return roll_result

def roll_with_animation(dice_type, dice_color='blue', target=None, success_outcome=None, failure_outcome=None):
    """
    Performs a dice roll with the specified parameters and displays the dice animation.
    Returns the roll result and outcome details.

    Args:
        dice_type (str): The type of dice to roll (e.g., "2d6" or "3d8+1d4" for a combination of dice).
        dice_color (str, optional): The color of the dice set to use (e.g., "red", "white", "blue", or "black"). Default is 'blue'.
        target (int, optional): The target number to beat. If provided, the function will return the outcome details.
        success_outcome (dict, optional): The outcome details if the roll is successful. Required if `target` is provided.
        failure_outcome (dict, optional): The outcome details if the roll is a failure. Required if `target` is provided.

    Returns:
        dict: A dictionary containing the roll result and, if `target` is provided, the outcome details.
    """
    # Create a DiceRoller instance
    dice_roller = DiceRoller()

    # Animate the dice roll
    roll_result = animate_dice_roll(dice_type, dice_color, dice_roller, target)

    # Determine the outcome if target and outcome details are provided
    if target is not None and success_outcome is not None and failure_outcome is not None:
        outcome = determine_outcome(roll_result, target, success_outcome, failure_outcome)
        return {'roll_result': roll_result, 'outcome': outcome}

    # If no target or outcome details are provided, return only the roll result
    return {'roll_result': roll_result}

# Example usage:
# If no args are passed the default action will be:
# Roll 2d6+1d4 with a target of 10, success outcome, and failure outcome
result = roll_with_animation('2d6+1d4', target=10, success_outcome={'details': 'You succeeded!'}, failure_outcome={'details': 'You failed.'})
print(f"Roll result: {result['roll_result']}")
print(f"Outcome: {result['outcome']['details']}")

# Note: Only the blue dice image files need to be included for this library to work,
# as a space-saving measure for other projects that may use this library.