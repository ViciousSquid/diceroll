import json
import re # Added for DiceType handling
from diceroll import DiceRoller
# REMOVED all imports related to DiceAnimator and datetime

# --- Constants (Keep them here for API users) ---
class DiceType:
    D4 = "1d4"
    D6 = "1d6"
    D8 = "1d8"
    D10 = "1d10"
    D12 = "1d12"
    D20 = "1d20"

class DiceColor:
    RED = 'red'
    BLUE = 'blue'
    BLACK = 'black'
    WHITE = 'white'

class AnimationStyle: # Keep for reference if GUI needs it
    SHAKE = 'shake'
    TUMBLE = 'tumble'
    SPIN = 'spin'

# --- API Class (No Animator) ---
class dicerollAPI:
    def __init__(self, save_rolls=False):
        self.dice_roller = DiceRoller(save_rolls=save_rolls)
        # REMOVED self.dice_animator = DiceAnimator()

    # REMOVED set_animation_window_size
    # REMOVED set_dice_image_path
    # REMOVED set_animation_style

    def roll_dice(self, dice_notation, target_value=None):
        """Rolls dice based on notation, no animation."""
        try:
            roll_result = self.dice_roller.roll_dice(dice_notation, target=target_value)
            return roll_result
        except ValueError as e:
            print(f"Invalid dice notation: {dice_notation}. Error: {str(e)}")
            return None

    def roll_single_dice(self, dice_type):
        return self.roll_dice(dice_type)

    def roll_multiple_dice_of_same_type(self, dice_type, num_dice):
        d_match = re.search(r"d(\d+)", dice_type)
        if not d_match:
            raise ValueError(f"Invalid dice_type format: {dice_type}")
        d_size = d_match.group(0)
        dice_notation = f"{num_dice}{d_size}"
        return self.roll_dice(dice_notation)

    def roll_multiple_dice(self, dice_notations, target_values=None):
        if target_values is None:
            target_values = [None] * len(dice_notations)

        roll_results = []
        for i, dice_notation in enumerate(dice_notations):
            roll_result = self.roll_dice(dice_notation, target_value=target_values[i])
            roll_results.append(roll_result)
        return roll_results

    def get_roll_sum(self, roll_result):
        return sum(roll_result['roll_details']) if roll_result else 0

    def get_roll_average(self, roll_result):
        roll_details = roll_result['roll_details'] if roll_result else []
        return sum(roll_details) / len(roll_details) if roll_details else 0

    def get_roll_max(self, roll_result):
        return max(roll_result['roll_details']) if roll_result and roll_result['roll_details'] else 0

    def get_roll_min(self, roll_result):
        return min(roll_result['roll_details']) if roll_result and roll_result['roll_details'] else 0

    def get_roll_statistics(self, dice_notation, num_rolls):
        return self.dice_roller.get_roll_statistics(dice_notation, num_rolls)

    def save_roll_history_to_file(self, file_path):
        roll_history = self.dice_roller.get_roll_history()
        with open(file_path, 'w') as file:
            json.dump(roll_history, file)

    def load_roll_history_from_file(self, file_path):
        try:
            with open(file_path, 'r') as file:
                roll_history = json.load(file)
            self.dice_roller.set_roll_history(roll_history)
            return roll_history
        except FileNotFoundError:
            print(f"Roll history file not found: {file_path}")
            return []
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file: {file_path}")
            return []

    def get_last_roll_total(self):
        return self.dice_roller.get_last_roll_total()

    def get_last_roll_details(self):
        return self.dice_roller.get_last_roll_details()

    def get_last_5_rolls(self):
        return self.dice_roller.get_last_5_rolls()

    # REMOVED get_available_dice_colors (as it's animation-related)

    def enable_roll_saving(self):
        self.dice_roller.save_rolls = True

    def disable_roll_saving(self):
        self.dice_roller.save_rolls = False

    def roll_saving_throw(self, dice_type=DiceType.D20, target_value=None, success_threshold=None):
        if success_threshold is None:
            success_threshold = target_value

        roll_result = self.roll_dice(dice_type, target_value=target_value)

        if roll_result is not None:
            if 'success' not in roll_result and success_threshold is not None:
                 roll_result['success'] = roll_result['roll_result'] >= success_threshold
            elif 'success' not in roll_result:
                 roll_result['success'] = None

        return roll_result

    def roll_multiple_saving_throws(self, num_throws, dice_type=DiceType.D20, target_values=None, success_thresholds=None):
        if target_values is None:
            target_values = [None] * num_throws
        if success_thresholds is None:
            success_thresholds = target_values

        saving_throw_results = []
        for i in range(num_throws):
            saving_throw_result = self.roll_saving_throw(dice_type, target_value=target_values[i], success_threshold=success_thresholds[i])
            saving_throw_results.append(saving_throw_result)

        return saving_throw_results