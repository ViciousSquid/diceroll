import random
import pygame
import time
import os

# Initialize Pygame
pygame.init()

# Set up the window
window_width = 400
window_height = 300
window = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Dice Roll")

# Set the path for the dice images
dice_image_path = "/diceroll/images"

# Load dice images
dice_images = []
for i in range(1, 7):
    image_path = os.path.join(dice_image_path, f"dice{i}.png")
    dice_images.append(pygame.image.load(image_path))

def roll_dice(dice_type):
    """
    Rolls a dice of the specified type and returns the result.

    Args:
        dice_type (str): The type of dice to roll (e.g., "d6" for a six-sided die).

    Returns:
        int: The result of the dice roll.
    """
    dice_size = int(dice_type[1:])
    roll_result = random.randint(1, dice_size)
    return roll_result

def determine_outcome(roll_result, target, success_outcome, failure_outcome):
    """
    Determines the outcome based on the dice roll result and the target number.

    Args:
        roll_result (int): The result of the dice roll.
        target (int): The target number to beat.
        success_outcome (dict): The outcome details if the roll is successful.
        failure_outcome (dict): The outcome details if the roll is a failure.

    Returns:
        dict: The outcome details based on the dice roll result.
    """
    if roll_result >= target:
        outcome = success_outcome
    else:
        outcome = failure_outcome
    return outcome

def perform_dice_roll(dice_roll_data):
    """
    Performs a dice roll based on the provided dice roll data and determines the outcome.

    Args:
        dice_roll_data (dict): The dice roll data from the story JSON.

    Returns:
        dict: The outcome details based on the dice roll result.
    """
    dice_type = dice_roll_data['type']
    target = dice_roll_data['target']
    success_outcome = dice_roll_data['success']
    failure_outcome = dice_roll_data['failure']

    # Animate the dice roll
    roll_result = animate_dice_roll(dice_type)

    outcome = determine_outcome(roll_result, target, success_outcome, failure_outcome)
    outcome['roll_result'] = roll_result
    return outcome

def animate_dice_roll(dice_type):
    """
    Animates the dice roll in the Pygame window.

    Args:
        dice_type (str): The type of dice to roll (e.g., "d6" for a six-sided die).

    Returns:
        int: The result of the dice roll.
    """
    clock = pygame.time.Clock()
    shake_duration = 1.5  # Duration of the shaking animation in seconds
    tumble_duration = 0.5  # Duration of the tumbling animation in seconds

    # Shaking animation
    start_time = time.time()
    while time.time() - start_time < shake_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        window.fill((255, 255, 255))  # Clear the window with a white background

        # Display a random dice image with a slight rotation and offset
        dice_image = random.choice(dice_images)
        dice_rect = dice_image.get_rect(center=(window_width // 2, window_height // 2))
        rotation_angle = random.randint(-10, 10)
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-10, 10)
        rotated_dice_image = pygame.transform.rotate(dice_image, rotation_angle)
        rotated_dice_rect = rotated_dice_image.get_rect(center=(window_width // 2 + offset_x, window_height // 2 + offset_y))
        window.blit(rotated_dice_image, rotated_dice_rect)

        pygame.display.flip()  # Update the display
        clock.tick(20)  # Limit the animation frame rate

    # Tumbling animation
    start_time = time.time()
    while time.time() - start_time < tumble_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        window.fill((255, 255, 255))  # Clear the window with a white background

        # Display a random dice image with a rotation
        dice_image = random.choice(dice_images)
        dice_rect = dice_image.get_rect(center=(window_width // 2, window_height // 2))
        rotation_angle = (time.time() - start_time) / tumble_duration * 360
        rotated_dice_image = pygame.transform.rotate(dice_image, rotation_angle)
        rotated_dice_rect = rotated_dice_image.get_rect(center=(window_width // 2, window_height // 2))
        window.blit(rotated_dice_image, rotated_dice_rect)

        pygame.display.flip()  # Update the display
        clock.tick(60)  # Limit the animation frame rate

    # Perform the actual dice roll
    roll_result = roll_dice(dice_type)

    # Display the final dice image based on the roll result
    final_dice_image = dice_images[roll_result - 1]
    final_dice_rect = final_dice_image.get_rect(center=(window_width // 2, window_height // 2))
    window.blit(final_dice_image, final_dice_rect)
    pygame.display.flip()

    # Wait for a short duration to display the final result
    pygame.time.delay(1000)

    return roll_result