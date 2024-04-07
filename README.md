# Dice Roll API

The Dice Roll API is a Python library that provides functionality for simulating dice rolls and performing dice-related operations. It includes classes for rolling dice, saving roll results, and animating dice rolls using Pygame.

## Features

- Roll various types of dice (e.g., 2d6, 1d20, 3d8+1d4) and get the roll results
- Save the last 5 roll results to a file
- Retrieve the last 5 roll results
- Enable or disable roll saving
- Get the available dice colours for dice animation
- Perform dice rolls with animated visualizations (optional, requires Pygame)

## How this is used

Core functionality is exposed as an API allowing rolling functionality, retrieve roll results, dice types, and colours

Documentation: https://github.com/ViciousSquid/diceroll/tree/main/Docs

### Source files:


<code style="color : name_color">diceroll.py</code> : Contains the DiceRoller and OutcomeDeterminer classes, as well as the roll_dice function.

<code style="color : name_color">diceroll_anim.py</code> : Contains the <code style="color : name_color">DiceAnimator</code> class, which handles the dice roll animation using the Pygame library.

<code style="color : name_color">roll_dice_example.py</code> : A script that demonstrates the usage of the roll_dice function in the console without animation.

<code style="color : name_color">roll_dice_example_gui.py</code> : A script that demonstrates the usage of the roll_dice function with a GUI and animations (requires pygame)

<code style="color : name_color">dice_api.py</code> : Exposes API feaures
