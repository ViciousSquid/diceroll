## diceroll![image](https://github.com/ViciousSquid/diceroll/assets/161540961/86d8abe9-3153-4cbc-b3d9-0c4b1b20c166)



**diceroll** is a Python library that provides API functionality (`dicerollAPI`) for simulating dice rolls and performing dice-related operations. 

It includes classes for rolling dice, tracking & saving roll results, and animating dice rolls using Pygame (pygame is completely optional)

API documentation starts here: https://github.com/ViciousSquid/diceroll/blob/main/Docs/dicerollAPI.md

## Features

- Roll various types of dice (e.g., 2d6, 1d20, 3d8+1d4) and get the roll results
- Console printing and logging
- Save the last 5 roll results to a file (.txt or .json)
- Retrieve the last 5 roll results
- Saving throws and skillchecks
- Set/Get the dice/font color (red, white, blue, black, green, custom)
- Animations (optional, requires Pygame)
____

## Further Documentation

https://github.com/ViciousSquid/diceroll/tree/main/Docs
____
### Source files:


`diceroll.py` : Contains the `DiceRoller` and `OutcomeDeterminer` classes, as well as the `roll_dice` function.

`diceroll_anim.py` : **(optional)** Contains the `DiceAnimator` class, which handles animation using the Pygame.

`diceroll_api.py` : Exposes `dicerollAPI` classes and defs

`diceroll_enums.py` 

`Example.py` and `Example2.py` : Commented demos of the `roll_dice` function in the console. 

`Example3_gui.py` : A simple demo of an animation that rolls and returns a result (requires pygame)

____

This API was custom-designed for use in the **Adventure!** *Interactive story engine* : https://github.com/ViciousSquid/Adventure
