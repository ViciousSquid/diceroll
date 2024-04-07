import random
import re
print("+++ diceroll") 

class DiceRoller:
    def __init__(self, save_rolls=False):
        self.last_roll_total = None
        self.last_roll_details = None
        self.last_5_rolls = []
        self.save_rolls = save_rolls

    def roll_dice(self, dice_type, target=None, success_outcome=None, failure_outcome=None):
        roll_results = []
        roll_sum = 0

        components = re.split(r'(\d+d\d+)', dice_type)
        for component in components:
            if component.startswith('+'):
                component = component[1:]
            match = re.match(r"(\d+)d(\d+)", component)
            if match:
                number_of_dice, dice_size = int(match.group(1)), int(match.group(2))
                component_results = [random.randint(1, dice_size) for _ in range(number_of_dice)]
                roll_results.extend(component_results)
                roll_sum += sum(component_results)
            elif component.strip():
                raise ValueError(f"Invalid dice type: {component}")

        roll_data = {
            "dice_type": dice_type,
            "roll_result": roll_sum,
            "roll_details": roll_results
        }

        if target is not None:
            if success_outcome is None or failure_outcome is None:
                raise ValueError("Success and failure outcome details must be provided when target is specified.")
            if roll_sum >= target:
                outcome = success_outcome
            else:
                outcome = failure_outcome
            outcome["roll_result"] = roll_sum
            roll_data["outcome"] = outcome

        self.last_5_rolls.append(roll_data)
        self.last_5_rolls = self.last_5_rolls[-5:]

        if self.save_rolls:
            self.save_last_5_rolls()

        self.last_roll_total = roll_sum
        self.last_roll_details = roll_results
        return roll_data

    def get_last_roll_total(self):
        return self.last_roll_total

    def get_last_roll_details(self):
        return self.last_roll_details

    def get_last_5_rolls(self):
        return self.last_5_rolls

    def save_last_5_rolls(self):
        with open("last_5_rolls.txt", "w") as file:
            for i, roll_data in enumerate(self.last_5_rolls, 1):
                file.write(f"Result {i}:\n")
                file.write(f"  Dice Type: {roll_data['dice_type']}\n")
                file.write(f"  Roll Result: {roll_data['roll_result']}\n")
                file.write(f"  Roll Details: {roll_data['roll_details']}\n")
                file.write("\n")