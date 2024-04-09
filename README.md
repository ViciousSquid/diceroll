## diceroll![image](https://github.com/ViciousSquid/diceroll/assets/161540961/86d8abe9-3153-4cbc-b3d9-0c4b1b20c166)



**diceroll** is a Python library that provides API functionality `dicerollAPI` for simulating dice rolls and performing dice-related operations. 

API documentation starts here: https://github.com/ViciousSquid/diceroll/blob/main/Docs/dicerollAPI.md

It includes classes for rolling dice, tracking & saving roll results, and animating dice rolls using Pygame.

## Features

- Roll various types of dice (e.g., 2d6, 1d20, 3d8+1d4) and get the roll results
- Save the last 5 roll results to a file (.txt or .json)
- Retrieve the last 5 roll results
- Set/Get the dice colour for dice animation (red, white, blue, black & custom)
- Perform dice rolls with animated visualizations (optional, requires Pygame)
____

## Further Documentation

https://github.com/ViciousSquid/diceroll/tree/main/Docs
____
### Source files:


`diceroll.py` : Contains the `DiceRoller` and `OutcomeDeterminer` classes, as well as the `roll_dice` function.

`diceroll_anim.py` : Contains the `DiceAnimator` class, which handles the dice roll animation using the Pygame library.

`diceroll_api.py` : Exposes `dicerollAPI` classes and defs

`roll_dice_example.py` : A script that demonstrates the usage of the `roll_dice` function in the console without animation.

`roll_dice_example_gui.py` : A script that demonstrates the usage of the `roll_dice` function with a GUI and animations (requires pygame)

____

This library and API were specifically designed for and alongside the **Adventure!** *Interactive story engine* : https://github.com/ViciousSquid/Adventure
