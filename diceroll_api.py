from diceroll_enums import DiceColor, AnimationStyle

try:
    from diceroll_anim import DiceAnimator
except ImportError:
    DiceAnimator = None

from diceroll import DiceRoller
from datetime import datetime
import json

class DiceType:
    D4 = "d4"
    D6 = "d6"
    D8 = "d8"
    D10 = "d10"
    D12 = "d12"
    D20 = "d20"

class dicerollAPI:
    def __init__(self, save_rolls=False):
        self.dice_roller = DiceRoller(save_rolls=save_rolls)
        if DiceAnimator is not None:
            self.dice_animator = DiceAnimator()
        else:
            self.dice_animator = None

    def set_animation_window_size(self, width=300, height=300):
        if self.dice_animator is not None:
            self.dice_animator.set_window_size(width, height)

    def set_dice_image_path(self, path="diceroll/images"):
        if self.dice_animator is not None:
            self.dice_animator.set_dice_image_path(path)

    def roll_dice(self, dice_notation, dice_color=DiceColor.WHITE, target_value=None, animate=True):
        try:
            roll_result = self.dice_roller.roll_dice(dice_notation)
            if animate and self.dice_animator is not None:
                self.dice_animator.run_animation(dice_notation, dice_color, target_value)

            # Set console text color based on dice_color
            if dice_color == DiceColor.RED:
                console_color = '\033[91m'  # Red
            elif dice_color == DiceColor.BLUE:
                console_color = '\033[94m'  # Light blue
            elif dice_color == DiceColor.GREEN:
                console_color = '\033[92m'  # Green
            elif dice_color == DiceColor.BLACK:
                console_color = '\033[97m'  # White (for visibility)
            elif dice_color == 'bread':
                console_color = '\033[97m'  # White (default) for 'bread' color
            else:
                console_color = '\033[97m'  # White (default)

            print(f"{console_color}Dice Notation: {dice_notation}")
            print(f"Roll Result: {roll_result['roll_result']}")
            print(f"Roll Details: {roll_result['roll_details']}\033[0m")  # Reset color

            return roll_result
        except ValueError as e:
            print(f"\033[91mInvalid dice notation: {dice_notation}. Error: {str(e)}\033[0m")
            return None

    def roll_single_dice(self, dice_type, dice_color=DiceColor.WHITE, animate=True):
        return self.roll_dice(dice_type, dice_color=dice_color, animate=animate)

    def roll_multiple_dice_of_same_type(self, dice_type, num_dice, dice_color=DiceColor.WHITE, animate=True):
        dice_notation = f"{num_dice}{dice_type}"
        return self.roll_dice(dice_notation, dice_color=dice_color, animate=animate)

    def roll_multiple_dice(self, dice_notations, dice_colors=None, target_values=None, animate=True):
        if dice_colors is None:
            dice_colors = [DiceColor.WHITE] * len(dice_notations)
        if target_values is None:
            target_values = [None] * len(dice_notations)

        roll_results = []
        for i, dice_notation in enumerate(dice_notations):
            roll_result = self.roll_dice(dice_notation, dice_color=dice_colors[i], target_value=target_values[i], animate=animate)
            roll_results.append(roll_result)
        return roll_results

    def get_roll_sum(self, roll_result):
        return sum(roll_result['roll_details'])

    def get_roll_average(self, roll_result):
        roll_details = roll_result['roll_details']
        return sum(roll_details) / len(roll_details)

    def get_roll_max(self, roll_result):
        return max(roll_result['roll_details'])

    def get_roll_min(self, roll_result):
        return min(roll_result['roll_details'])

    def get_roll_statistics(self, dice_notation, num_rolls):
        return self.dice_roller.get_roll_statistics(dice_notation, num_rolls)

    def save_roll_history_to_file(self, file_path):
        roll_history = self.dice_roller.get_roll_history()
        with open(file_path, 'w') as file:
            json.dump(roll_history, file)

    def load_roll_history_from_file(self, file_path):
        with open(file_path, 'r') as file:
            roll_history = json.load(file)
        self.dice_roller.set_roll_history(roll_history)
        return roll_history

    def get_last_roll_total(self):
        return self.dice_roller.get_last_roll_total()

    def get_last_roll_details(self):
        return self.dice_roller.get_last_roll_details()

    def get_last_5_rolls(self):
        return self.dice_roller.get_last_5_rolls()

    def get_available_dice_colors(self):
        return [color_value for color_name, color_value in DiceColor.__dict__.items() if not color_name.startswith("__")]

    def enable_roll_saving(self):
        self.dice_roller.save_rolls = True

    def disable_roll_saving(self):
        self.dice_roller.save_rolls = False

    def set_animation_style(self, style=AnimationStyle.SHAKE):
        self.dice_animator.set_animation_style(style)

    def roll_saving_throw(self, dice_type=DiceType.D20, dice_color=DiceColor.WHITE, target_value=None, success_threshold=None, animate=True):
        if success_threshold is None:
            success_threshold = target_value

        roll_result = self.roll_dice(dice_type, dice_color=dice_color, target_value=target_value, animate=animate)

        if roll_result is not None:
            success = roll_result['roll_result'] >= success_threshold
            roll_result['success'] = success

        return roll_result

    def roll_multiple_saving_throws(self, num_throws, dice_type=DiceType.D20, dice_color=DiceColor.WHITE, target_values=None, success_thresholds=None, animate=True):
        if target_values is None:
            target_values = [None] * num_throws
        if success_thresholds is None:
            success_thresholds = target_values

        saving_throw_results = []
        for i in range(num_throws):
            saving_throw_result = self.roll_saving_throw(dice_type, dice_color=dice_color, target_value=target_values[i], success_threshold=success_thresholds[i], animate=animate)
            saving_throw_results.append(saving_throw_result)

        return saving_throw_results