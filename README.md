## diceroll![image](https://github.com/ViciousSquid/diceroll/assets/161540961/86d8abe9-3153-4cbc-b3d9-0c4b1b20c166)



**diceroll** is a Python library that provides API functionality `dicerollAPI` for simulating dice rolls and performing dice-related operations. 

API documentation starts here: https://github.com/ViciousSquid/diceroll/blob/main/Docs/dicerollAPI.md

It includes classes for rolling dice, tracking & saving roll results, and animating dice rolls using Pygame.

## Features

- Roll various types of dice (e.g., 2d6, 1d20, 3d8+1d4) and get the roll results
- Save the last 5 roll results to a file
- Retrieve the last 5 roll results
- Enable or disable roll saving
- Set/Get the dice colour for dice animation (red, white, blue, black & custom)
- Perform dice rolls with animated visualizations (optional, requires Pygame)

## How this is used

Core functionality is exposed as an API allowing rolling functionality, retrieve roll results, dice types, and colours

Further Documentation: https://github.com/ViciousSquid/diceroll/tree/main/Docs

### Source files:


<code style="color : name_color">diceroll.py</code> : Contains the `DiceRoller` and `OutcomeDeterminer` classes, as well as the `roll_dice` function.

<code style="color : name_color">diceroll_anim.py</code> : Contains the `DiceAnimator` class, which handles the dice roll animation using the Pygame library.

<code style="color : name_color">diceroll_api.py</code> : Exposes `dicerollAPI` classes and defs

<code style="color : name_color">roll_dice_example.py</code> : A script that demonstrates the usage of the `roll_dice` function in the console without animation.

<code style="color : name_color">roll_dice_example_gui.py</code> : A script that demonstrates the usage of the `roll_dice` function with a GUI and animations (requires pygame)



This library and API were specifically designed for and alongside the **Adventure!** *Interactive story engine* : https://github.com/ViciousSquid/Adventure
