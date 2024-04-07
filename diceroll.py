# diceroll.py

import random
import re

class DiceRoller:
    """
    A class to encapsulate the dice rolling functionality and maintain the state.
    """

    def __init__(self):
        """
        Initialize the DiceRoller instance with the last roll total and details set to None.
        """
        self.last_roll_total = None
        self.last_roll_details = None

    def roll_dice(self, dice_type):
        """
        Rolls one or more dice of the specified type and returns the sum of the results.
        Updates the last roll total and details.

        Args:
            dice_type (str): The type of dice to roll (e.g., "2d6" or "3d8+1d4" for a combination of dice).

        Returns:
            int: The sum of the dice roll results.

        Raises:
            ValueError: If an invalid dice type is provided.

        Examples:
            >>> roller = DiceRoller()
            >>> result = roller.roll_dice("2d6")
            >>> print(result)
            7
            >>> result = roller.roll_dice("3d8+1d4")
            >>> print(result)
            18
        """
        roll_results = []
        roll_sum = 0

        # Split the dice type string into individual components
        components = re.split(r'(\d+d\d+)', dice_type)
        for component in components:
            match = re.match(r"(\d+)d(\d+)", component)
            if match:
                num_dice, dice_size = int(match.group(1)), int(match.group(2))
                component_results = [random.randint(1, dice_size) for _ in range(num_dice)]
                roll_results.extend(component_results)
                roll_sum += sum(component_results)
            elif component.strip():
                raise ValueError(f"Invalid dice type: {component}")

        self.last_roll_total = roll_sum
        self.last_roll_details = roll_results
        return roll_sum

    def get_last_roll_total(self):
        """
        Returns the total of the last dice roll.

        Returns:
            int: The total of the last dice roll, or None if no roll has been performed yet.
        """
        return self.last_roll_total

    def get_last_roll_details(self):
        """
        Returns the individual results of the last dice roll.

        Returns:
            list: A list containing the individual results of the last dice roll, or None if no roll has been performed yet.
        """
        return self.last_roll_details

class OutcomeDeterminer:
    """
    A class to determine the outcome of a dice roll based on the target number and outcome details.
    """

    @staticmethod
    def determine_outcome(roll_result, target, success_outcome, failure_outcome):
        """
        Determines the outcome based on the dice roll result and the target number.
        Checks for critical success or failure based on the maximum or minimum dice roll value.

        Args:
            roll_result (int): The result of the dice roll.
            target (int): The target number to beat.
            success_outcome (dict): The outcome details if the roll is successful.
            failure_outcome (dict): The outcome details if the roll is a failure.

        Returns:
            dict: The outcome details based on the dice roll result.

        Raises:
            ValueError: If the target, success_outcome, or failure_outcome is not provided.

        Examples:
            >>> outcome_determiner = OutcomeDeterminer()
            >>> result = outcome_determiner.determine_outcome(15, 10, {"details": "Success!"}, {"details": "Failure."})
            >>> print(result)
            {'details': 'Success!', 'roll_result': 15}
            >>> result = outcome_determiner.determine_outcome(5, 10, {"details": "Success!"}, {"details": "Failure."})
            >>> print(result)
            {'details': 'Failure.', 'roll_result': 5}
        """
        if target is None:
            raise ValueError("Target number must be provided.")
        if success_outcome is None or failure_outcome is None:
            raise ValueError("Success and failure outcome details must be provided.")

        max_roll_value = sum(range(1, target + 1))  # Assuming the maximum roll value is the sum of all dice faces
        min_roll_value = len(range(1, target + 1))  # Assuming the minimum roll value is the number of dice

        if roll_result == max_roll_value:
            outcome = {'critical_success': True, 'details': success_outcome['details']}
        elif roll_result == min_roll_value:
            outcome = {'critical_failure': True, 'details': failure_outcome['details']}
        elif roll_result >= target:
            outcome = success_outcome
        else:
            outcome = failure_outcome

        outcome['roll_result'] = roll_result
        return outcome

def roll_dice(dice_type, target=None, success_outcome=None, failure_outcome=None, use_animation=False):
    """
    Performs a dice roll with the specified parameters and returns the roll result and outcome details.

    Args:
        dice_type (str): The type of dice to roll (e.g., "2d6" or "3d8+1d4" for a combination of dice).
        target (int, optional): The target number to beat. If provided, the function will return the outcome details.
        success_outcome (dict, optional): The outcome details if the roll is successful. Required if `target` is provided.
        failure_outcome (dict, optional): The outcome details if the roll is a failure. Required if `target` is provided.
        use_animation (bool, optional): Whether to use the dice roll animation. Default is False.
                                         Note: The `diceroll_anim` module is required for the animation feature.
                                         If `use_animation` is True, make sure the `diceroll_anim` module is available.

    Returns:
        dict: A dictionary containing the roll result and, if `target` is provided, the outcome details.

    Raises:
        ValueError: If `target` is provided but `success_outcome` or `failure_outcome` is missing.
        ImportError: If `use_animation` is True but the `diceroll_anim` module is not available.

    Examples:
        >>> result = roll_dice("2d6", target=7, success_outcome={"details": "Success!"}, failure_outcome={"details": "Failure."})
        >>> print(result)
        {'roll_result': 8, 'outcome': {'details': 'Success!', 'roll_result': 8}}
        >>> result = roll_dice("1d20", use_animation=True)
        >>> print(result)
        {'roll_result': 15}
    """
    dice_roller = DiceRoller()

    if use_animation:
        try:
            from diceroll_anim import DiceAnimator
            dice_animator = DiceAnimator()
            roll_result = dice_animator.run_animation(dice_type, target=target)
        except ImportError:
            raise ImportError("The 'diceroll_anim' module is required for the animation feature. Make sure it is available.")
    else:
        roll_result = dice_roller.roll_dice(dice_type)

    if target is not None:
        if success_outcome is None or failure_outcome is None:
            raise ValueError("Success and failure outcome details must be provided when target is specified.")
        outcome_determiner = OutcomeDeterminer()
        outcome = outcome_determiner.determine_outcome(roll_result, target, success_outcome, failure_outcome)
        return {'roll_result': roll_result, 'outcome': outcome}

    return {'roll_result': roll_result}