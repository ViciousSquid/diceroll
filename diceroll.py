import random

def roll_dice(dice_type):
    """
    Rolls a dice of the specified type and returns the result.

    Args:
        dice_type (str): The type of dice to roll (e.g., "d6" for a six-sided die).

    Returns:
        int: The result of the dice roll.
    """
    # Extract the number of sides from the dice type
    # For example, if dice_type is "d6", dice_size will be 6
    dice_size = int(dice_type[1:])

    # Generate a random number between 1 and the number of sides (inclusive)
    # This simulates rolling the dice
    roll_result = random.randint(1, dice_size)

    return roll_result

def determine_outcome(roll_result, target, success_outcome, failure_outcome):
    """
    Determines the outcome based on the dice roll result and the target number.

    Args:
        roll_result (int): The result of the dice roll.
        target (int): The target number to beat.
        success_outcome (dict): The outcome details if the roll is successful.
        failure_outcome (dict): The outcome details if the roll is a failure.

    Returns:
        dict: The outcome details based on the dice roll result.
    """
    if roll_result >= target:
        # If the roll result is greater than or equal to the target number,
        # the outcome is considered a success
        outcome = success_outcome
    else:
        # If the roll result is less than the target number,
        # the outcome is considered a failure
        outcome = failure_outcome

    return outcome

def perform_dice_roll(dice_roll_data):
    """
    Performs a dice roll based on the provided dice roll data and determines the outcome.

    Args:
        dice_roll_data (dict): The dice roll data from the story JSON.

    Returns:
        dict: The outcome details based on the dice roll result.
    """
    # Extract the necessary information from the dice_roll_data dictionary
    dice_type = dice_roll_data['type']
    target = dice_roll_data['target']
    success_outcome = dice_roll_data['success']
    failure_outcome = dice_roll_data['failure']

    # Roll the dice to get the result
    roll_result = roll_dice(dice_type)

    # Determine the outcome based on the roll result and the target number
    outcome = determine_outcome(roll_result, target, success_outcome, failure_outcome)

    # Add the roll result to the outcome dictionary for display purposes
    outcome['roll_result'] = roll_result

    return outcome