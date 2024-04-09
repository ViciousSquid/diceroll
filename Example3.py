import pygame
import random
import time
import os

# Initialize Pygame
pygame.init()

# Set the window size
window_width = 300
window_height = 300
window = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("diceroll")

# Load dice images
dice_images = []
for i in range(1, 7):
    image_path = os.path.join("diceroll", "images", "blue", f"dice{i}.jpg")
    dice_images.append(pygame.image.load(image_path))

# Set up the clock
clock = pygame.time.Clock()

# Set up the font for displaying the result
font = pygame.font.Font(None, 36)

# Animation loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear the window
    window.fill((255, 255, 255))

    # Display the dice roll animation
    for _ in range(10):
        dice_image = random.choice(dice_images)
        dice_rect = dice_image.get_rect(center=(window_width // 2, window_height // 2))
        window.blit(dice_image, dice_rect)
        pygame.display.flip()
        clock.tick(10)

    # Determine the final dice roll result
    roll_result = random.randint(1, 6)

    # Display the final dice image
    final_dice_image = dice_images[roll_result - 1]
    final_dice_rect = final_dice_image.get_rect(center=(window_width // 2, window_height // 2))
    window.blit(final_dice_image, final_dice_rect)

    # Display the roll result text
    result_text = font.render(f"Roll Result: {roll_result}", True, (0, 0, 0))
    result_rect = result_text.get_rect(center=(window_width // 2, window_height - 50))
    window.blit(result_text, result_rect)

    # Update the display
    pygame.display.flip()

    # Print the roll result in the console
    print(f"Roll Result: {roll_result}")

    # Wait for 2 seconds before closing the window
    time.sleep(2)
    running = False

# Quit Pygame
pygame.quit()