

### DiceAPI
The `DiceAPI` class provides an API interface for accessing the core dice rolling functionality and retrieving roll results and dice information.
* roll_dice()
* get_last_roll_total()
* get_last_roll_details()
* get_available_dice_colours()
* enable_roll_saving()
* disable_roll_saving()


### DiceRoller
The `DiceRoller` class handles the actual dice rolling and result tracking. It includes the following functions:

* roll_dice()
* get_last_roll_total()
* get_last_roll_details()
* get_last_5_rolls()
* save_last_5_rolls()

### DiceAnimator
The `DiceAnimator` class provides functionality for animating dice rolls using Pygame. It includes the following functions:

* animate_dice_roll()
* run_animation()

 ## Example:

```
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
```
