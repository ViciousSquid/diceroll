from diceroll import DiceRoller
from dice_api import DiceAPI
import random
import pygame
import time
import os
from datetime import datetime

class DiceAnimator:
    def __init__(self, window_width=300, window_height=300, dice_image_path="images"):
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
        dice_sets = {}

        today = datetime.today()
        if (today.month == 10 and today.day == 31) or (today.month == 4 and today.day == 1):
            colours = ['bread']
        else:
            colours = ['red', 'white', 'blue', 'black']

        for colour in colours:
            dice_set = []
            for i in range(1, 7):
                image_path = os.path.join(self.dice_image_path, colour, f"dice{i}.jpg")
                if os.path.exists(image_path):
                    dice_set.append(pygame.image.load(image_path))
            if dice_set:
                dice_sets[colour] = dice_set

        return dice_sets

    def animate_dice_roll(self, dice_type, dice_colour, dice_roller, target=None):
        today = datetime.today()
        if (today.month == 10 and today.day == 31) or (today.month == 4 and today.day == 1):
            dice_colour = 'bread'

        if dice_colour not in self.dice_sets:
            raise ValueError(f"Invalid dice colour: {dice_colour}. Available colours are: {', '.join(self.dice_sets.keys())}")

        clock = pygame.time.Clock()
        shake_duration = 0.75
        tumble_duration = 0.25

        dice_and_target_text = f"{dice_type}"
        if target:
            dice_and_target_text += f"-{target}"
        dice_and_target_render = self.font.render(dice_and_target_text, True, (0, 0, 0))
        dice_and_target_rect = dice_and_target_render.get_rect(midtop=(self.window_width // 2, 10))

        start_time = time.time()
        while time.time() - start_time < shake_duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            self.window.fill((255, 255, 255))

            self.window.blit(dice_and_target_render, dice_and_target_rect)

            dice_image = random.choice(self.dice_sets[dice_colour])
            dice_rect = dice_image.get_rect(center=(self.window_width // 2, self.window_height // 2))
            rotation_angle = random.randint(-5, 5)
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            rotated_dice_image = pygame.transform.rotate(dice_image, rotation_angle)
            rotated_dice_rect = rotated_dice_image.get_rect(center=(self.window_width // 2 + offset_x, self.window_height // 2 + offset_y))
            self.window.blit(rotated_dice_image, rotated_dice_rect)

            pygame.display.flip()
            clock.tick(30)

        start_time = time.time()
        while time.time() - start_time < tumble_duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            self.window.fill((255, 255, 255))

            self.window.blit(dice_and_target_render, dice_and_target_rect)

            dice_image = random.choice(self.dice_sets[dice_colour])
            dice_rect = dice_image.get_rect(center=(self.window_width // 2, self.window_height // 2))
            rotation_angle = (time.time() - start_time) / tumble_duration * 360
            rotated_dice_image = pygame.transform.rotate(dice_image, rotation_angle)
            rotated_dice_rect = rotated_dice_image.get_rect(center=(self.window_width // 2, self.window_height // 2))
            self.window.blit(rotated_dice_image, rotated_dice_rect)

            pygame.display.flip()
            clock.tick(60)

        dice_api = DiceAPI()
        roll_result = dice_api.roll_dice(dice_type)

        roll_details = dice_api.get_last_roll_details()
        single_roll_result = roll_details[0]

        self.window.fill((255, 255, 255))

        self.window.blit(dice_and_target_render, dice_and_target_rect)

        try:
            final_dice_image = self.dice_sets[dice_colour][single_roll_result - 1]
        except IndexError:
            final_dice_image = self.dice_sets[dice_colour][0]
        final_dice_rect = final_dice_image.get_rect(center=(self.window_width // 2, self.window_height // 2))
        self.window.blit(final_dice_image, final_dice_rect)

        result_text = self.font.render(f"Result: {roll_result['roll_result']}", True, (0, 0, 0))
        result_rect = result_text.get_rect(midbottom=(self.window_width // 2, self.window_height - 10))
        self.window.blit(result_text, result_rect)

        pygame.display.flip()

        pygame.time.delay(3000)

        return roll_result

    def run_animation(self, dice_type, dice_colour='blue', target=None, save_rolls=False):
        today = datetime.today()
        if (today.month == 10 and today.day == 31) or (today.month == 4 and today.day == 1):
            dice_colour = 'bread'

        available_colours = DiceAPI().get_available_dice_colours()
        if dice_colour not in available_colours:
            raise ValueError(f"Invalid dice colour: {dice_colour}. Available colours are: {', '.join(available_colours)}")

        dice_roller = DiceRoller(save_rolls=save_rolls)
        roll_result = self.animate_dice_roll(dice_type, dice_colour, dice_roller, target)
        return roll_result