import random
import pygame
import time
import os
import re
from datetime import datetime
from diceroll import DiceRoller

# Define DiceColor
class DiceColor:
    RED = 'red'
    BLUE = 'blue'
    BLACK = 'black'
    WHITE = 'white'

# Reverted AnimationStyle (Removed ROLL_AND_TUMBLE)
class AnimationStyle:
    SHAKE = 'shake'
    TUMBLE = 'tumble'
    SPIN = 'spin'

# --- Die Class (Physics Removed) ---
class DieSprite:
    def __init__(self, x, y, die_size, images_to_use, font, target_size=(60, 60)):
        self.x = x # Original center X
        self.y = y # Original center Y
        self.rot = random.randint(0, 359)
        self.offset_x = 0 # Offset for shaking
        self.offset_y = 0 # Offset for shaking
        self.die_size = die_size
        self.images = images_to_use
        self.font = font
        self.final_value = 0
        self.is_d6 = (self.die_size == 6 and isinstance(self.images, list) and len(self.images) == 6)
        self.target_size = target_size

        self.current_image_base = random.choice(self.images) if self.is_d6 else self.images[0]
        self.final_image = None

    def update_animation(self, style, duration_ratio):
        """Updates position/rotation - Reverted to simpler styles."""
        if not self.images: return

        base_img = random.choice(self.images) if self.is_d6 else self.images[0]
        self.current_image_base = base_img

        if style == AnimationStyle.SHAKE:
            self.rot = random.randint(-15, 15)
            self.offset_x = random.randint(-10, 10)
            self.offset_y = random.randint(-10, 10)
        elif style == AnimationStyle.TUMBLE:
            self.rot = duration_ratio * 360 * random.uniform(0.8, 1.2) # Desync spin
            self.offset_x = 0
            self.offset_y = 0
        elif style == AnimationStyle.SPIN:
            self.rot = duration_ratio * 720 * random.uniform(0.8, 1.2) # Desync spin
            self.offset_x = 0
            self.offset_y = 0
        else: # Default to SHAKE
            self.rot = random.randint(-15, 15)
            self.offset_x = random.randint(-10, 10)
            self.offset_y = random.randint(-10, 10)

    def draw_animated(self, window):
        """Draws the die during animation using offsets."""
        if not self.current_image_base: return
        rotated_image = pygame.transform.rotate(self.current_image_base, self.rot)
        # Draw using base x/y + current offsets
        rect = rotated_image.get_rect(center=(int(self.x + self.offset_x), int(self.y + self.offset_y)))
        window.blit(rotated_image, rect)

    def set_final_value(self, value):
        """Sets the final value and prepares final image."""
        self.final_value = value
        if self.is_d6 and 1 <= value <= 6:
            self.final_image = self.images[value - 1]
        elif not self.is_d6 and self.images:
            self.final_image = self.images[0]
        else:
            self.final_image = None

    def draw_final(self, window, pos_x, pos_y):
        """Draws the die in its final state at a specific position."""
        if not self.final_image: return
        rect = self.final_image.get_rect(center=(pos_x, pos_y))
        window.blit(self.final_image, rect)
        if not self.is_d6:
            text_surface = self.font.render(str(self.final_value), True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=rect.center)
            shadow_surface = self.font.render(str(self.final_value), True, (0, 0, 0))
            window.blit(shadow_surface, (text_rect.x + 1, text_rect.y + 1))
            window.blit(text_surface, text_rect)

# ------------------------------------

class DiceAnimator:
    def __init__(self, window_width=600, window_height=400, dice_image_path="diceroll/images"):
        pygame.init()
        self.window_width = window_width
        self.window_height = window_height
        self.window = None
        self.dice_image_path = dice_image_path
        self.raw_dice_sets = {}
        self.raw_base_images = {}
        self.processed_dice_sets = {}
        self.processed_base_images = {}
        self.images_loaded = False
        self.images_processed = False

        try:
            self.font = pygame.font.Font(None, 36)
            self.large_font = pygame.font.Font(None, 72)
            self.outcome_font = pygame.font.Font(None, 48)
            self.die_number_font = pygame.font.Font(None, 40)
        except pygame.error as e:
            print(f"Pygame font error: {e}. Using fallback SysFont.")
            self.font = pygame.font.SysFont('Arial', 36)
            self.large_font = pygame.font.SysFont('Arial', 72)
            self.outcome_font = pygame.font.SysFont('Arial', 48)
            self.die_number_font = pygame.font.SysFont('Arial', 30, bold=True)

        self.animation_speed = 1.0
        self.animation_style = AnimationStyle.SHAKE # Reverted Default!

    def _load_raw_images(self):
        """Loads images WITHOUT converting or scaling."""
        if self.images_loaded: return True
        print(f"--- Loading Raw Images from: {self.dice_image_path} ---")
        today = datetime.today()
        is_special_day = (today.month == 10 and today.day == 31) or (today.month == 4 and today.day == 1)
        d6_colors = ['bread'] if is_special_day else [DiceColor.RED, DiceColor.WHITE, DiceColor.BLUE, DiceColor.BLACK]
        base_sizes = [4, 8, 10, 12, 20]
        for color in d6_colors:
            dice_set = []
            image_dir = os.path.join(self.dice_image_path, color)
            if not os.path.isdir(image_dir): continue
            for i in range(1, 7):
                image_path = os.path.join(image_dir, f"dice{i}.jpg")
                if os.path.exists(image_path):
                    try: img = pygame.image.load(image_path); dice_set.append(img)
                    except pygame.error as e: print(f" -> Error loading {image_path}: {e}")
            if dice_set: self.raw_dice_sets[color] = dice_set
        for size in base_sizes:
            image_path = os.path.join(self.dice_image_path, f"blank_d{size}.png")
            if os.path.exists(image_path):
                try: img = pygame.image.load(image_path); self.raw_base_images[size] = img
                except pygame.error as e: print(f" -> Error loading {image_path}: {e}")
        self.images_loaded = (bool(self.raw_dice_sets) or bool(self.raw_base_images))
        if not self.images_loaded: print(f"ERROR: No raw images found in {self.dice_image_path}")
        return self.images_loaded

    def _process_images(self):
        """Scales and converts images AFTER display is set."""
        if self.images_processed or not self.images_loaded: return
        print("--- Processing Images ---")
        for color, img_list in self.raw_dice_sets.items():
            self.processed_dice_sets[color] = [
                pygame.transform.scale(img.convert_alpha(), (60, 60))
                for img in img_list ]
        for size, img in self.raw_base_images.items():
            self.processed_base_images[size] = pygame.transform.scale(img.convert_alpha(), (70, 70))
        self.images_processed = True
        print("--- Image Processing Finished ---")

    def _display_text_only(self, roll_result, dice_and_target_text):
        """Displays only the total result as text."""
        self.window.fill((255, 255, 255))
        dice_and_target_render = self.font.render(dice_and_target_text, True, (0, 0, 0))
        dice_and_target_rect = dice_and_target_render.get_rect(midtop=(self.window_width // 2, 10))
        self.window.blit(dice_and_target_render, dice_and_target_rect)
        result_text = self.large_font.render(f"{roll_result['roll_result']}", True, (0, 0, 0))
        result_rect = result_text.get_rect(center=(self.window_width // 2, self.window_height // 2))
        self.window.blit(result_text, result_rect)
        if 'outcome_text' in roll_result:
            outcome_text_render = self.outcome_font.render(roll_result['outcome_text'], True, (0, 128, 0) if roll_result.get('success', False) else (255, 0, 0))
            outcome_rect = outcome_text_render.get_rect(midbottom=(self.window_width // 2, self.window_height - 10))
            self.window.blit(outcome_text_render, outcome_rect)
        pygame.display.flip()

    def _display_multiple_dice(self, roll_result, dice_color, dice_and_target_text, all_dice_defs):
        """Handles animation and display for multiple dice (reverted style)."""
        dice_list = []
        d6_set_to_use = self.processed_dice_sets.get(dice_color)
        base_images_to_use = self.processed_base_images

        num_dice = len(all_dice_defs)
        for i, die_size in enumerate(all_dice_defs):
            # Place dice near their final positions for shake/tumble
            die_width = 70
            spacing = 20
            total_width = (num_dice * die_width) + ((num_dice - 1) * spacing)
            start_x_layout = (self.window_width - total_width) / 2 + (die_width / 2)
            x = start_x_layout + i * (die_width + spacing)
            y = self.window_height / 2 - 40 # Use final Y

            images_for_this_die = d6_set_to_use if die_size == 6 else [base_images_to_use.get(die_size)]
            if not images_for_this_die or not images_for_this_die[0]: continue
            target_size = (60, 60) if die_size == 6 else (70, 70)
            die = DieSprite(x, y, die_size, images_for_this_die, self.die_number_font, target_size)
            die.set_final_value(roll_result['roll_details'][i])
            dice_list.append(die)

        clock = pygame.time.Clock()
        animation_duration = 1.0 / self.animation_speed # Shorter duration

        dice_and_target_render = self.font.render(dice_and_target_text, True, (0, 0, 0))
        dice_and_target_rect = dice_and_target_render.get_rect(midtop=(self.window_width // 2, 10))

        start_time = time.time()
        while time.time() - start_time < animation_duration:
            duration_ratio = (time.time() - start_time) / animation_duration
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); return None

            self.window.fill((255, 255, 255))
            self.window.blit(dice_and_target_render, dice_and_target_rect)

            for die in dice_list:
                # Pass duration ratio for Tumble/Spin, but not window size
                die.update_animation(self.animation_style, duration_ratio)
                die.draw_animated(self.window)

            pygame.display.flip()
            clock.tick(30) # Back to 30fps is fine for this style

        # --- Final Display ---
        self.window.fill((255, 255, 255))
        self.window.blit(dice_and_target_render, dice_and_target_rect)

        die_width = 70
        spacing = 20
        total_width = (num_dice * die_width) + ((num_dice - 1) * spacing)
        start_x = (self.window_width - total_width) / 2 + (die_width / 2)

        for i, die in enumerate(dice_list):
            pos_x = start_x + i * (die_width + spacing)
            # Use the die's original Y, which is the final Y now
            die.draw_final(self.window, int(pos_x), int(die.y))

        total_text = self.large_font.render(f"Total: {roll_result['roll_result']}", True, (0, 0, 0))
        total_rect = total_text.get_rect(center=(self.window_width // 2, self.window_height / 2 + 60))
        self.window.blit(total_text, total_rect)

        if 'outcome_text' in roll_result:
             outcome_text_render = self.outcome_font.render(roll_result['outcome_text'], True, (0, 128, 0) if roll_result.get('success', False) else (255, 0, 0))
             outcome_rect = outcome_text_render.get_rect(midbottom=(self.window_width // 2, self.window_height - 10))
             self.window.blit(outcome_text_render, outcome_rect)

        pygame.display.flip()

    def animate_dice_roll(self, dice_notation, dice_color, dice_roller, target=None):
        """Main function to orchestrate the animation."""
        if not self._load_raw_images():
            print("Cannot animate due to missing images.")
            return dice_roller.roll_dice(dice_notation, target=target)

        self.window = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Dice Roll")
        self._process_images()

        today = datetime.today()
        is_special_day = (today.month == 10 and today.day == 31) or (today.month == 4 and today.day == 1)
        if is_special_day: dice_color = 'bread'
        if dice_color not in self.processed_dice_sets:
            print(f"Warning: D6 set for '{dice_color}' not found, using blue.")
            dice_color = DiceColor.BLUE
            if dice_color not in self.processed_dice_sets:
                if self.processed_dice_sets:
                    dice_color = list(self.processed_dice_sets.keys())[0]
                    print(f"Warning: Blue D6 set not found, using '{dice_color}'.")
                else:
                    print("Warning: No D6 sets processed at all.")
                    dice_color = None

        roll_result = dice_roller.roll_dice(dice_notation, target=target)
        if not roll_result: return None

        dice_and_target_text = f"{dice_notation}" + (f" (Target: {target})" if target else "")

        matches = re.findall(r"(\d+)d(\d+)", dice_notation, re.IGNORECASE)
        all_dice_defs = []
        can_display_all = True
        if not matches: can_display_all = False
        else:
            for num_str, size_str in matches:
                num, size = int(num_str), int(size_str)
                for _ in range(num):
                    all_dice_defs.append(size)
                    can_show_d6 = (size == 6 and dice_color and self.processed_dice_sets.get(dice_color))
                    can_show_base = (size != 6 and size in self.processed_base_images)
                    if not (can_show_d6 or can_show_base):
                        can_display_all = False; break
                if not can_display_all: break
        if can_display_all and len(all_dice_defs) != len(roll_result['roll_details']):
            can_display_all = False

        if can_display_all:
            self._display_multiple_dice(roll_result, dice_color, dice_and_target_text, all_dice_defs)
        else:
            self._display_text_only(roll_result, dice_and_target_text)

        waiting = True
        while waiting:
             for event in pygame.event.get():
                 if event.type == pygame.QUIT: waiting = False
                 if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN: waiting = False
        return roll_result

    def run_animation(self, dice_notation, dice_color=DiceColor.BLUE, target=None, save_rolls=False):
        dice_roller = DiceRoller(save_rolls=save_rolls)
        result = self.animate_dice_roll(dice_notation, dice_color, dice_roller, target)
        return result

    def set_window_size(self, width, height):
        self.window_width = width
        self.window_height = height

    def set_dice_image_path(self, path):
        self.dice_image_path = path
        self.images_loaded = False
        self.images_processed = False

    def set_animation_style(self, style):
        # Updated list of styles
        if style in [AnimationStyle.SHAKE, AnimationStyle.TUMBLE, AnimationStyle.SPIN]:
            self.animation_style = style
        else:
            print(f"Warning: Unknown animation style '{style}'. Using default.")

    def set_animation_speed(self, speed):
        self.animation_speed = max(0.1, speed)

    def set_custom_dice_faces(self, dice_notation, face_images):
        print("Warning: Custom faces not currently supported.")

    def set_target_success_failure_animations(self, success_animation, failure_animation):
         print("Warning: Success/Failure animations not currently supported.")