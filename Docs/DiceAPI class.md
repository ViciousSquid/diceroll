The `DiceAPI` class provides an API interface for accessing the core dice rolling functionality and retrieving roll results and dice information.

Methods:

- `roll_dice(dice_type)`:
    - Args:
        - `dice_type` (str): The type of dice to roll (e.g., "2d6" or "3d8+1d4" for a combination of dice).
    - Returns:
        - int: The result of the dice roll.
    - Description: Rolls the specified dice type and returns the roll result.

- `get_last_roll_total()`:
    - Returns:
        - int: The total of the last dice roll, or None if no roll has been performed yet.
    - Description: Returns the total of the last dice roll.

- `get_last_roll_details()`:
    - Returns:
        - list: A list containing the individual results of the last dice roll, or None if no roll has been performed yet.
    - Description: Returns the individual results of the last dice roll.

- `get_available_dice_colors()`:
    - Returns:
        - list: A list of available dice colors for the animation feature.
    - Description: Returns a list of available dice colors that can be used with the animation feature.

Usage:

To use the `DiceAPI`, create an instance of the class and call the desired methods:

```python
from dice_api import DiceAPI

# Create a DiceAPI instance
dice_api = DiceAPI()

# Roll 2d6 dice
result = dice_api.roll_dice("2d6")
print(f"Roll result: {result}")

# Get the total of the last roll
last_roll_total = dice_api.get_last_roll_total()
print(f"Last roll total: {last_roll_total}")

# Get the individual results of the last roll
last_roll_details = dice_api.get_last_roll_details()
print(f"Last roll details: {last_roll_details}")

# Get the available dice colors for animation
available_colors = dice_api.get_available_dice_colors()
print(f"Available dice colors: {', '.join(available_colors)}")
