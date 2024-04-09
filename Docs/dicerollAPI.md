

## dicerollAPI
The `dicerollAPI` class provides a high-level interface for rolling dice, performing animations, and managing roll history. 

It utilizes the `DiceRoller` and `DiceAnimator` classes internally.

### Initialization:

To create an instance of the `dicerollAPI`, you can optionally specify the `save_rolls` parameter to enable or disable saving roll history.

```python
api = dicerollAPI(save_rolls=False)
```

______

## Methods

### set_animation_window_size(width=300, height=300)
Sets the size of the animation window.

* `width` (int): The width of the window (default: 300).
* `height` (int): The height of the window (default: 300).
______
### set_dice_image_path(path="diceroll/images")
Sets the path to the directory containing the dice images.

* `path` (str): The path to the dice image directory (default: "diceroll/images")
______
### roll_dice(dice_notation, dice_color=DiceColor.BLUE, target_value=None, animate=True)
Rolls the specified dice and returns the roll result.

* `dice_notation` (str): The dice notation (e.g., "2d6+4").
* `dice_color` (str): The color of the dice (default: DiceColor.BLUE).
* `target_value` (int): The target value for the roll (default: None).
* `animate` (bool): Whether to animate the roll (default: True).

  
Returns a dictionary containing the roll result, or `None` if the dice notation is invalid.
______
### roll_single_dice(dice_type, dice_color=DiceColor.BLUE, animate=True)
Rolls a single dice of the specified type.

* `dice_type` (str): The type of the dice (e.g., DiceType.D20).
* `dice_color` (str): The color of the dice (default: DiceColor.BLUE).
* `animate` (bool): Whether to animate the roll (default: True).

  
Returns a dictionary containing the roll result.
______
### roll_multiple_dice_of_same_type(dice_type, num_dice, dice_color=DiceColor.BLUE, animate=True)
Rolls multiple dice of the same type.

* `dice_type` (str): The type of the dice (e.g., DiceType.D20).
* `num_dice` (int): The number of dice to roll.
* `dice_color` (str): The color of the dice (default: DiceColor.BLUE).
* `animate` (bool): Whether to animate the roll (default: True).

  
Returns a dictionary containing the roll result.
______


### roll_multiple_dice(dice_notations, dice_colors=None, target_values=None, animate=True)
Rolls multiple dice with different notations.

* `dice_notations` (list): A list of dice notations.
* `dice_colors` (list): A list of dice colors (default: None).
* `target_values` (list): A list of target values (default: None).
* `animate` (bool): Whether to animate the rolls (default: True).

  
Returns a list of dictionaries containing the roll results.
______



### get_roll_sum(roll_result)
Calculates the sum of the roll details.

* `roll_result` (dict): The roll result dictionary.

  
Returns the sum of the roll details.
______



### get_roll_average(roll_result)
Calculates the average of the roll details.

* `roll_result` (dict): The roll result dictionary.

  
Returns the average of the roll details.
______



### get_roll_max(roll_result)
Returns the maximum value from the roll details.

* `roll_result` (dict): The roll result dictionary.

  
Returns the maximum value from the roll details.
______




### get_roll_min(roll_result)
Returns the minimum value from the roll details.

* `roll_result` (dict): The roll result dictionary.

  
Returns the minimum value from the roll details.
______




### get_roll_statistics(dice_notation, num_rolls)
Retrieves the statistics for a given dice notation and number of rolls.

* `dice_notation` (str): The dice notation.
* `num_rolls` (int): The number of rolls to perform.

  
Returns a dictionary containing the roll statistics.
______




### save_roll_history_to_file(file_path)
Saves the roll history to a file.

* `file_path` (str): The path to the file.

______



### load_roll_history_from_file(file_path)
Loads the roll history from a file.

* `file_path` (str): The path to the file.

  
Returns the loaded roll history.
______





### get_last_roll_total()
Retrieves the total of the last roll.


Returns the total of the last roll.
______




### get_last_roll_details()
Retrieves the details of the last roll.


Returns the details of the last roll.
______






### get_last_5_rolls()
Retrieves the last 5 rolls.


Returns a list of the last 5 roll results.

______





### get_available_dice_colors()
Retrieves the available dice colors.


Returns a list of available dice colors.

______



### enable_roll_saving()
Enables saving roll history.


______


### disable_roll_saving()
Disables saving roll history.


______


### set_animation_style(style=AnimationStyle.SHAKE)
Sets the animation style.

* `style` (str): The animation style (default: AnimationStyle.SHAKE).

______




### roll_saving_throw(dice_type=DiceType.D20, dice_color=DiceColor.BLUE, target_value=None, success_threshold=None, animate=True)
Rolls a saving throw.

* `dice_type` (str): The type of the dice (default: DiceType.D20).
* `dice_color` (str): The color of the dice (default: DiceColor.BLUE).
* `target_value` (int): The target value for the roll (default: None).
* `success_threshold` (int): The success threshold for the roll (default: None).
* `animate` (bool): Whether to animate the roll (default: True).
  

 Returns a dictionary containing the saving throw result.
______






### roll_multiple_saving_throws(num_throws, dice_type=DiceType.D20, dice_color=DiceColor.BLUE, target_values=None, success_thresholds=None, animate=True)
Rolls multiple saving throws.

* `num_throws` (int): The number of saving throws to roll.
* `dice_type` (str): The type of the dice (default: DiceType.D20).
* `dice_color` (str): The color of the dice (default: DiceColor.BLUE).
* `target_values` (list): A list of target values (default: None).
* `success_thresholds` (list): A list of success thresholds (default: None).
* `animate` (bool): Whether to animate the rolls (default: True).
  

Returns a list of dictionaries containing the saving throw results.
______




## Enums
`dicerollAPI` uses the following enums:


### DiceType
`D4`: Represents a 4-sided dice.
`D6`: Represents a 6-sided dice.
`D8`: Represents an 8-sided dice.
`D10`: Represents a 10-sided dice.
`D12`: Represents a 12-sided dice.
`D20`: Represents a 20-sided dice.

### DiceColor
`RED`: Represents the red dice color.
`BLUE`: Represents the blue dice color.
`BLACK`: Represents the black dice color.
`WHITE`: Represents the white dice color.

### AnimationStyle
`SHAKE`: Represents the shake animation style.
`TUMBLE`: Represents the tumble animation style.
`SPIN`: Represents the spin animation style.

______

This documentation provides an overview of the methods and enums available in the dicerollAPI class. It allows you to roll dice, perform animations, manage roll history, and customize the animation settings.
