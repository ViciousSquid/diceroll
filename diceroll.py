import random
import pygame
import time
import os
import re

# Initialize Pygame
pygame.init()

# Set up the window
window_width = 600
window_height = 600
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

def perform_dice_roll(dice_roll_data, dice_roller, dice_color):
    """
    Performs a dice roll based on the provided dice roll data and determines the outcome.
    Uses the DiceRoller instance to perform the roll and retrieve the last roll total.

    Args:
        dice_roll_data (dict): The dice roll data from the story JSON.
        dice_roller (DiceRoller): An instance of the DiceRoller class.
        dice_color (str): The color of the dice set to use (e.g., "red", "white", "blue", or "black").

    Returns:
        dict: The outcome details based on the dice roll result.
    """
    dice_type = dice_roll_data['type']
    target = dice_roll_data['target']
    success_outcome = dice_roll_data['success']
    failure_outcome = dice_roll_data['failure']

    # Animate the dice roll
    roll_result = animate_dice_roll(dice_type, dice_color, dice_roller)

    outcome = determine_outcome(roll_result, target, success_outcome, failure_outcome)
    return outcome

def animate_dice_roll(dice_type, dice_color, dice_roller):
    """
    Animates the dice roll in the Pygame window.
    Uses the DiceRoller instance to perform the actual roll.

    Args:
        dice_type (str): The type of dice to roll (e.g., "2d6" or "2d6+1d4" for a combination of dice).
        dice_color (str): The color of the dice set to use (e.g., "red", "white", "blue", or "black").
        dice_roller (DiceRoller): An instance of the DiceRoller class.

    Returns:
        int: The result of the dice roll.
    """
    clock = pygame.time.Clock()
    shake_duration = 2.0  # Duration of the shaking animation in seconds
    tumble_duration = 1.0  # Duration of the tumbling animation in seconds

    # Shaking animation
    start_time = time.time()
    while time.time() - start_time < shake_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        window.fill((255, 255, 255))  # Clear the window with a white background

        # Display random dice images with a slight rotation and offset
        dice_components = re.split(r'(\d+d\d+)', dice_type)
        num_dice = sum(int(component.split('d')[0]) for component in dice_components if component.endswith('d'))
        dice_images = [random.choice(dice_sets[dice_color]) for _ in range(num_dice)]
        dice_rects = []
        for i, dice_image in enumerate(dice_images):
            dice_rect = dice_image.get_rect()
            dice_rect.center = (
                window_width // 2 + (i - (num_dice - 1) / 2) * (dice_rect.width + 10),
                window_height // 2,
            )
            rotation_angle = random.randint(-20, 20)
            offset_x = random.randint(-20, 20)
            offset_y = random.randint(-20, 20)
            rotated_dice_image = pygame.transform.rotate(dice_image, rotation_angle)
            rotated_dice_rect = rotated_dice_image.get_rect(center=dice_rect.center)
            rotated_dice_rect.move_ip(offset_x, offset_y)
            window.blit(rotated_dice_image, rotated_dice_rect)
            dice_rects.append(rotated_dice_rect)

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

        # Display random dice images with a rotation
        dice_images = [random.choice(dice_sets[dice_color]) for _ in range(num_dice)]
        dice_rects = []
        for i, dice_image in enumerate(dice_images):
            dice_rect = dice_image.get_rect()
            dice_rect.center = (
                window_width // 2 + (i - (num_dice - 1) / 2) * (dice_rect.width + 10),
                window_height // 2,
            )
            rotation_angle = (time.time() - start_time) / tumble_duration * 360 * 2  # Rotate faster
            rotated_dice_image = pygame.transform.rotate(dice_image, rotation_angle)
            rotated_dice_rect = rotated_dice_image.get_rect(center=dice_rect.center)
            window.blit(rotated_dice_image, rotated_dice_rect)
            dice_rects.append(rotated_dice_rect)

        pygame.display.flip()  # Update the display
        clock.tick(60)  # Limit the animation frame rate

    # Perform the actual dice roll
    roll_result = dice_roller.roll_dice(dice_type)
    roll_details = dice_roller.get_last_roll_details()

    # Display the final dice images based on the roll result
    window.fill((255, 255, 255))  # Clear the window with a white background
    for i, roll in enumerate(roll_details):
        final_dice_image = dice_sets[dice_color][roll - 1]
        final_dice_rect = final_dice_image.get_rect()
        final_dice_rect.center = (
            window_width // 2 + (i - (num_dice - 1) / 2) * (final_dice_rect.width + 10),
            window_height // 2,
        )
        window.blit(final_dice_image, final_dice_rect)

    pygame.display.flip()

    # Wait for a short duration to display the final result
    pygame.time.delay(2000)

    return roll_result

print("++ diceroll")
print("DEMO: Press space bar to roll 2d6+1d4 with a target of 10")
# Example dice roll data
dice_roll_data = {
    'type': '2d6+1d4',  # Roll two six-sided dice and one four-sided die
    'target': 10,
    'success': {'details': 'You succeeded!'},
    'failure': {'details': 'You failed.'}
}

def main():
    # Create a DiceRoller instance
    dice_roller = DiceRoller()

    # Set the initial dice color based on the available dice sets
    available_colors = list(dice_sets.keys())
    dice_color = available_colors[0]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Perform a dice roll when the space bar is pressed
                    outcome = perform_dice_roll(dice_roll_data, dice_roller, dice_color)
                    print(f"Roll result: {outcome['roll_result']}")
                    print(f"Outcome: {outcome['details']}")
                elif event.key == pygame.K_r and 'red' in dice_sets:
                    dice_color = 'red'
                elif event.key == pygame.K_w and 'white' in dice_sets:
                    dice_color = 'white'
                elif event.key == pygame.K_b and 'blue' in dice_sets:
                    dice_color = 'blue'
                elif event.key == pygame.K_k and 'black' in dice_sets:
                    dice_color = 'black'

    pygame.quit()

if __name__ == "__main__":
    main()