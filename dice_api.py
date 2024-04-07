from .diceroll import DiceRoller
from datetime import datetime

class DiceAPI:
    def __init__(self, save_rolls=False):
        self.dice_roller = DiceRoller(save_rolls=save_rolls)

    def roll_dice(self, dice_type):
        return self.dice_roller.roll_dice(dice_type)

    def get_last_roll_total(self):
        return self.dice_roller.get_last_roll_total()

    def get_last_roll_details(self):
        return self.dice_roller.get_last_roll_details()

    def get_available_dice_colours(self):
        today = datetime.today()
        if (today.month == 10 and today.day == 31) or (today.month == 4 and today.day == 1):
            return ['bread']
        else:
            return ['red', 'white', 'blue', 'black']

    def enable_roll_saving(self):
        self.dice_roller.save_rolls = True

    def disable_roll_saving(self):
        self.dice_roller.save_rolls = False