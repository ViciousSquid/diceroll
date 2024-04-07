Work in progress

A library for rolling and animating dice using Pygame

Explanation:

The roll_dice function takes a dice_type parameter, which represents the type of dice to roll (e.g., "d6" for a six-sided die).
It extracts the number of sides from the dice_type string and generates a random number between 1 and the number of sides (inclusive) using random.randint(). This simulates rolling the dice and returns the result.

The determine_outcome function takes the roll_result, target, success_outcome, and failure_outcome as parameters.
It compares the roll_result with the target number. If the roll_result is greater than or equal to the target, it considers the outcome a success and returns the success_outcome. 
Otherwise, it considers the outcome a failure and returns the failure_outcome.

The perform_dice_roll function is the main entry point for performing a dice roll.
It takes the dice_roll_data dictionary from the story JSON as a parameter. 
This dictionary contains the necessary information for the dice roll, such as the dice type, target number, success outcome, and failure outcome.
The function extracts the required information from the dice_roll_data dictionary and calls the roll_dice function to obtain the roll result.
It then calls the determine_outcome function to determine the outcome based on the roll result and the target number.
Finally, it adds the roll_result to the outcome dictionary for display purposes and returns the outcome.

To use diceroll.py module in your application, you can import the perform_dice_roll function and call it with the appropriate dice_roll_data whenever a dice roll is required.
The function will return the outcome details based on the dice roll result, which you can then use to update the room description, exits, or any other relevant information in your game.
