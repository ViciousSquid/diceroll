import random
import re
from collections import defaultdict

# Fixed syntax error (was print|)
print("++ diceroll init")

class DiceRoller:
    def __init__(self, save_rolls=False):
        self.last_roll_total = None
        self.last_roll_details = None
        self.last_5_rolls = []
        self.save_rolls = save_rolls
        self.roll_history = []

    def roll_dice(self, dice_notation, target=None, success_outcome=None, failure_outcome=None):
        roll_results = []
        roll_sum = 0

        # Fixed parsing logic (Bug 1)
        matches = re.findall(r"(\d+)d(\d+)", dice_notation)

        if not matches and dice_notation.strip():
            raise ValueError(f"Invalid dice notation: {dice_notation}. Expected format like '1d6' or '2d8+1d4'.")

        for match in matches:
            number_of_dice, dice_size = int(match[0]), int(match[1])
            component_results = [random.randint(1, dice_size) for _ in range(number_of_dice)]
            roll_results.extend(component_results)
            roll_sum += sum(component_results)

        if not roll_results and not matches:
             raise ValueError(f"No dice found to roll in: {dice_notation}")

        roll_data = {
            "dice_notation": dice_notation,
            "roll_result": roll_sum,
            "roll_details": roll_results
        }

        # Fixed target handling to be more flexible
        if target is not None:
            is_success = roll_sum >= target
            roll_data["target"] = target
            roll_data["success"] = is_success
            # Only add outcome dicts if they are provided
            if success_outcome and failure_outcome:
                if is_success:
                    outcome = success_outcome
                else:
                    outcome = failure_outcome
                outcome["roll_result"] = roll_sum
                roll_data["outcome"] = outcome
            # Add simple text outcome if full dicts aren't provided
            elif is_success:
                 roll_data["outcome_text"] = "Success"
            else:
                 roll_data["outcome_text"] = "Failure"


        self.last_5_rolls.append(roll_data)
        self.last_5_rolls = self.last_5_rolls[-5:]

        if self.save_rolls:
            self.roll_history.append(roll_data)
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

    def get_roll_history(self):
        return self.roll_history

    def set_roll_history(self, roll_history):
        self.roll_history = roll_history

    def save_last_5_rolls(self):
        with open("last_5_rolls.txt", "w") as file:
            for i, roll_data in enumerate(self.last_5_rolls, 1):
                file.write(f"Result {i}:\n")
                file.write(f"  Dice Notation: {roll_data['dice_notation']}\n")
                file.write(f"  Roll Result: {roll_data['roll_result']}\n")
                file.write(f"  Roll Details: {roll_data['roll_details']}\n")
                file.write("\n")

    def get_roll_statistics(self, dice_notation, num_rolls):
        roll_results = []
        for _ in range(num_rolls):
            roll_data = self.roll_dice(dice_notation)
            roll_results.append(roll_data["roll_result"])

        statistics = {
            "dice_notation": dice_notation,
            "num_rolls": num_rolls,
            "average": sum(roll_results) / num_rolls if num_rolls > 0 else 0, # Avoid division by zero
            "min": min(roll_results) if roll_results else 0,
            "max": max(roll_results) if roll_results else 0,
            "frequency": self.calculate_frequency(roll_results)
        }
        return statistics

    def calculate_frequency(self, roll_results):
        frequency = defaultdict(int)
        for result in roll_results:
            frequency[result] += 1
        return dict(frequency)

    # Fixed: Removed unused parameters (Bug 2)
    def roll_with_advantage(self, dice_notation):
        roll_data_1 = self.roll_dice(dice_notation)
        roll_data_2 = self.roll_dice(dice_notation)
        if roll_data_1["roll_result"] >= roll_data_2["roll_result"]:
            return roll_data_1
        else:
            return roll_data_2

    # Fixed: Removed unused parameters (Bug 2)
    def roll_with_disadvantage(self, dice_notation):
        roll_data_1 = self.roll_dice(dice_notation)
        roll_data_2 = self.roll_dice(dice_notation)
        if roll_data_1["roll_result"] <= roll_data_2["roll_result"]:
            return roll_data_1
        else:
            return roll_data_2

    def get_dice_probabilities(self, dice_notation):
        match = re.match(r"(\d+)d(\d+)", dice_notation)
        if not match:
            # Handle mixed notation better or clarify limitation
            raise ValueError(f"Probability calculation currently only supports simple 'XdY' notation: {dice_notation}")

        number_of_dice, dice_size = int(match.group(1)), int(match.group(2))

        probabilities = {}
        for i in range(number_of_dice, number_of_dice * dice_size + 1):
            probability = self.calculate_probability(i, number_of_dice, dice_size)
            probabilities[i] = probability

        return probabilities

    def calculate_probability(self, target_sum, number_of_dice, dice_size):
        if target_sum < number_of_dice or target_sum > number_of_dice * dice_size:
            return 0

        # Using dynamic programming to calculate probabilities
        dp = [[0] * (target_sum + 1) for _ in range(number_of_dice + 1)]
        dp[0][0] = 1

        for i in range(1, number_of_dice + 1):
            for j in range(1, target_sum + 1):
                for k in range(1, dice_size + 1):
                    if j - k >= 0:
                        dp[i][j] += dp[i - 1][j - k]

        total_combinations = dice_size ** number_of_dice
        favorable_combinations = dp[number_of_dice][target_sum]
        probability = favorable_combinations / total_combinations

        return probability