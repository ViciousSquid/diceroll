import random
import pygame
import time
import os
import re
from datetime import datetime
from diceroll import DiceRoller

# Define DiceColor and AnimationStyle locally or import if preferred
class DiceColor:
    RED = 'red'
    BLUE = 'blue'
    BLACK = 'black'
    WHITE = 'white'

class AnimationStyle:
    SHAKE = 'shake'
    TUMBLE = 'tumble'
    SPIN = 'spin'

# --- Enhanced Die Class for State ---
class DieSprite:
    def __init__(self, x, y, die_size, d6_set, base_images, font):
        self.x = x
        self.y = y
        self.rot = 0
        self.offset_x = 0
        self.offset_y = 0
        self.die_size = die_size
        self.d6_set = d6_set # Specific color d6 images (list of 6)
        self.base_images = base_images # Dict of base images {size: img}
        self.font = font # Font for drawing numbers
        self.final_value = 0
        self.is_d6 = (self.die_size == 6 and self.d6_set)

        if self.is_d6:
            self.images = self.d6_set
            self.base_image = None
        elif self.die_size in self.base_images:
            self.images = [self.base_images[self.die_size]] # List with one image
            self.base_image = self.base_images[self.die_size]
        else:
            self.images = None # Cannot display this die visually
            self.base_image = None

        self.current_image = random.choice(self.images) if self.images else None

    def update_animation(self, style, duration_ratio):
        """Updates position/rotation for one animation frame."""
        if not self.images: return

        # Flicker during animation (use base image for non-d6)
        self.current_image = random.choice(self.d6_set) if self.is_d6 else self.base_image

        if style == AnimationStyle.SHAKE:
            self.rot = random.randint(-15, 15)
            self.offset_x = random.randint(-10, 10)
            self.offset_y = random.randint(-10, 10)
        elif style == AnimationStyle.TUMBLE:
            self.rot = duration_ratio * 360 * random.uniform(0.8, 1.2)
            self.offset_x = 0
            self.offset_y = 0
        elif style == AnimationStyle.SPIN:
            self.rot = duration_ratio * 720 * random.uniform(0.8, 1.2)
            self.offset_x = 0
            self.offset_y = 0

    def draw_animated(self, window):
        """Draws the die during animation."""
        if not self.current_image: return

        rotated_image = pygame.transform.rotate(self.current_image, self.rot)
        rect = rotated_image.get_rect(center=(self.x + self.offset_x, self.y + self.offset_y))
        window.blit(rotated_image, rect)

    def set_final_value(self, value):
        """Sets the final value and image."""
        self.final_value = value
        if self.is_d6 and 1 <= value <= 6:
            self.current_image = self.images[value - 1]
        elif self.base_image:
            self.current_image = self.base_image
        else:
            self.current_image = None # Should not happen if check is done before

    def draw_final(self, window, pos_x, pos_y):
        """Draws the die in its final state at a specific position."""
        if not self.current_image: return

        rect = self.current_image.get_rect(center=(pos_x, pos_y))
        window.blit(self.current_image, rect)

        # If not a d6, draw the number on top
        if not self.is_d6:
            text_surface = self.font.render(str(self.final_value), True, (255, 255, 255)) # White text
            text_rect = text_surface.get_rect(center=rect.center)
            window.blit(text_surface, text_rect)


# ------------------------------------

class DiceAnimator:
    def __init__(self, window_width=600, window_height=400, dice_image_path="diceroll/images"):
        pygame.init()
        self.window_width = window_width
        self.window_height = window_height
        self.window = None
        self.dice_image_path = dice_image_path
        self.dice_sets = {} # Will hold d6 images {color: [img1, ...]}
        self.base_dice_images = {} # Will hold base images {size: img}
        self.load_images() # Renamed from load_dice_sets

        if not self.dice_sets and not self.base_dice_images:
             raise ValueError(f"No dice images (d6 sets or base images) found in '{dice_image_path}'. Cannot animate.")

        try:
            self.font = pygame.font.Font(None, 36)
            self.large_font = pygame.font.Font(None, 72)
            self.outcome_font = pygame.font.Font(None, 48)
            self.die_number_font = pygame.font.Font(None, 40) # Font for numbers on dice
        except pygame.error as e:
            print(f"Pygame font error: {e}. Using fallback SysFont.")
            self.font = pygame.font.SysFont('Arial', 36)
            self.large_font = pygame.font.SysFont('Arial', 72)
            self.outcome_font = pygame.font.SysFont('Arial', 48)
            self.die_number_font = pygame.font.SysFont('Arial', 30, bold=True)

        self.animation_speed = 1.0
        self.animation_style = AnimationStyle.SHAKE

    def load_images(self):
        """Loads both d6 sets and base dice images with enhanced path handling."""
        print(f"--- Loading Images from: {self.dice_image_path} ---")
        base_path = os.path.abspath(self.dice_image_path)
        print(f"Absolute base path: {base_path}")

        today = datetime.today()
        # Check current date (May 29th, 2025) - Not a special day
        is_special_day = (today.month == 10 and today.day == 31) or (today.month == 4 and today.day == 1)
        d6_colors = ['bread'] if is_special_day else [DiceColor.RED, DiceColor.WHITE, DiceColor.BLUE, DiceColor.BLACK]
        base_sizes = [4, 8, 10, 12, 20]

        # Load d6 sets
        print("--- Loading D6 Sets ---")
        for color in d6_colors:
            dice_set = []
            image_dir = os.path.join(self.dice_image_path, color)
            print(f"Checking D6 dir: {os.path.abspath(image_dir)}")
            if not os.path.isdir(image_dir):
                print(f" -> Not found or not a directory.")
                continue

            for i in range(1, 7):
                image_path = os.path.join(image_dir, f"dice{i}.jpg")
                if os.path.exists(image_path):
                    try:
                       # --- CRITICAL: Ensure .convert_alpha() is NOT here ---
                       img = pygame.image.load(image_path)
                       dice_set.append(pygame.transform.scale(img, (60, 60))) # Scale d6
                    except pygame.error as e: print(f" -> Error loading {image_path}: {e}")
            if dice_set:
                self.dice_sets[color] = dice_set
                print(f" -> Loaded {len(dice_set)} images for '{color}'.")
            else:
                 print(f" -> No images loaded for '{color}'.")


        # Load base images
        print("--- Loading Base Images ---")
        for size in base_sizes:
            image_path = os.path.join(self.dice_image_path, f"blank_d{size}.png")
            print(f"Checking base image: {os.path.abspath(image_path)}")
            if os.path.exists(image_path):
                try:
                    # --- CRITICAL: Ensure .convert_alpha() is NOT here ---
                    img = pygame.image.load(image_path)
                    self.base_dice_images[size] = pygame.transform.scale(img, (70, 70)) # Scale base dice
                    print(f" -> Loaded blank_d{size}.png")
                except pygame.error as e: print(f" -> Error loading {image_path}: {e}")
            else:
                print(f" -> Not found: blank_d{size}.png")

        print("--- Image Loading Finished ---")

        # Check if *any* images were loaded
        if not self.dice_sets and not self.base_dice_images:
             raise ValueError(f"No dice images (d6 sets or base images) found in '{self.dice_image_path}'. Cannot animate.")
        elif not self.base_dice_images:
             print("Warning: No base dice images (d4, d8, etc.) were loaded.")
        elif not self.dice_sets:
             print("Warning: No d6 image sets (red, blue, etc.) were loaded.")

    def _display_text_only(self, roll_result, dice_and_target_text):
        """Displays only the total result as text."""
        # (Implementation is the same as before, ensure it uses self.window etc.)
        self.window.fill((255, 255, 255))
        dice_and_target_render = self.font.render(dice_and_target_text, True, (0, 0, 0))
        dice_and_target_rect = dice_and_target_render.get_rect(midtop=(self.window_width // 2, 10))
        self.window.blit(dice_and_target_render, dice_and_target_rect)

        result_text = self.large_font.render(f"{roll_result['roll_result']}", True, (0, 0, 0))
        result_rect = result_text.get_rect(center=(self.window_width // 2, self.window_height // 2))
        self.window.blit(result_text, result_rect)

        if 'outcome_text' in roll_result:
            outcome_text_render = self.outcome_font.render(roll_result['outcome_text'], True, (0, 128, 0) if roll_result['success'] else (255, 0, 0))
            outcome_rect = outcome_text_render.get_rect(midbottom=(self.window_width // 2, self.window_height - 10))
            self.window.blit(outcome_text_render, outcome_rect)

        pygame.display.flip()


    def _display_multiple_dice(self, roll_result, dice_color, dice_and_target_text, all_dice_defs):
        """Handles animation and display for multiple dice."""
        dice_list = []
        d6_set_to_use = self.dice_sets.get(dice_color) # Get the specific color d6 set

        # --- Create DieSprite objects ---
        num_dice = len(all_dice_defs)
        for i, die_size in enumerate(all_dice_defs):
            x = self.window_width / (num_dice + 1) * (i + 1)
            y = self.window_height / 2 + random.randint(-20, 20)
            die = DieSprite(x, y, die_size, d6_set_to_use, self.base_dice_images, self.die_number_font)
            die.set_final_value(roll_result['roll_details'][i])
            dice_list.append(die)

        clock = pygame.time.Clock()
        shake_duration = 1.0 / self.animation_speed

        dice_and_target_render = self.font.render(dice_and_target_text, True, (0, 0, 0))
        dice_and_target_rect = dice_and_target_render.get_rect(midtop=(self.window_width // 2, 10))

        # --- Animation Loop ---
        start_time = time.time()
        while time.time() - start_time < shake_duration:
            duration_ratio = (time.time() - start_time) / shake_duration
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return None

            self.window.fill((255, 255, 255))
            self.window.blit(dice_and_target_render, dice_and_target_rect)

            for die in dice_list:
                die.update_animation(self.animation_style, duration_ratio)
                die.draw_animated(self.window)

            pygame.display.flip()
            clock.tick(30)

        # --- Final Display Loop ---
        self.window.fill((255, 255, 255))
        self.window.blit(dice_and_target_render, dice_and_target_rect)

        die_width = 70 # Use average/max size
        spacing = 20
        total_width = (num_dice * die_width) + ((num_dice - 1) * spacing)
        start_x = (self.window_width - total_width) / 2 + (die_width / 2)

        for i, die in enumerate(dice_list):
            pos_x = start_x + i * (die_width + spacing)
            die.draw_final(self.window, pos_x, self.window_height / 2 - 40)

        total_text = self.large_font.render(f"Total: {roll_result['roll_result']}", True, (0, 0, 0))
        total_rect = total_text.get_rect(center=(self.window_width // 2, self.window_height / 2 + 60))
        self.window.blit(total_text, total_rect)

        if 'outcome_text' in roll_result:
             outcome_text_render = self.outcome_font.render(roll_result['outcome_text'], True, (0, 128, 0) if roll_result['success'] else (255, 0, 0))
             outcome_rect = outcome_text_render.get_rect(midbottom=(self.window_width // 2, self.window_height - 10))
             self.window.blit(outcome_text_render, outcome_rect)

        pygame.display.flip()

    def animate_dice_roll(self, dice_notation, dice_color, dice_roller, target=None):
        today = datetime.today()
        is_special_day = (today.month == 10 and today.day == 31) or (today.month == 4 and today.day == 1)
        if is_special_day:
            dice_color = 'bread'

        # Ensure selected color (or bread) d6 set exists if needed, or default
        if dice_color not in self.dice_sets:
            print(f"Warning: D6 set for '{dice_color}' not found, using blue.")
            dice_color = DiceColor.BLUE
            if dice_color not in self.dice_sets:
                 print("Warning: Default 'blue' D6 set also not found. Only non-d6 rolls can show d6 images.")


        self.window = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Dice Roll")

        roll_result = dice_roller.roll_dice(dice_notation, target=target)
        if not roll_result: return None

        dice_and_target_text = f"{dice_notation}"
        if target: dice_and_target_text += f" (Target: {target})"

        # --- New Parsing Logic ---
        matches = re.findall(r"(\d+)d(\d+)", dice_notation, re.IGNORECASE)
        all_dice_defs = []
        can_display_all = True

        if not matches: # If parsing fails, use text only
            can_display_all = False
        else:
            for num_str, size_str in matches:
                num = int(num_str)
                size = int(size_str)
                for _ in range(num):
                    all_dice_defs.append(size)
                    # Check if we can display this die type
                    if not (size == 6 and self.dice_sets.get(dice_color)) and size not in self.base_dice_images:
                        can_display_all = False
                        break
                if not can_display_all: break

        # Check if number of dice matches results
        if can_display_all and len(all_dice_defs) != len(roll_result['roll_details']):
            print("Warning: Mismatch between parsed dice and roll results. Using text display.")
            can_display_all = False

        # --- Decide which display method to use ---
        if can_display_all:
            self._display_multiple_dice(roll_result, dice_color, dice_and_target_text, all_dice_defs)
        else:
            print("Info: Cannot visually represent all dice, showing text result only.")
            self._display_text_only(roll_result, dice_and_target_text)

        # --- Wait for close ---
        waiting = True
        while waiting:
             for event in pygame.event.get():
                 if event.type == pygame.QUIT:
                     waiting = False
                 if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                     waiting = False

        return roll_result

    def run_animation(self, dice_notation, dice_color=DiceColor.BLUE, target=None, save_rolls=False):
        today = datetime.today()
        is_special_day = (today.month == 10 and today.day == 31) or (today.month == 4 and today.day == 1)
        if is_special_day:
            dice_color = 'bread'

        dice_roller = DiceRoller(save_rolls=save_rolls)
        roll_result = self.animate_dice_roll(dice_notation, dice_color, dice_roller, target)
        return roll_result

    # --- Other Setters ---
    def set_window_size(self, width, height):
        self.window_width = width
        self.window_height = height

    def set_dice_image_path(self, path):
        self.dice_image_path = path
        self.load_images() # Reload images

    def set_animation_style(self, style):
        self.animation_style = style

    def set_animation_speed(self, speed):
        self.animation_speed = speed

    def set_custom_dice_faces(self, dice_notation, face_images):
        print("Warning: Custom faces not currently supported in multi-die display.")

    def set_target_success_failure_animations(self, success_animation, failure_animation):
         print("Warning: Success/Failure animations not currently supported in multi-die display.")