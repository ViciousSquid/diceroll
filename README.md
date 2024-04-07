### Introduction

This versatile library offers a comprehensive set of tools for handling dice rolling operations across various scenarios. Its core strength lies in the ability to roll any combination of dice types effortlessly, making it invaluable for applications that require random number generation based on dice mechanics, such as games, simulations, or projects requiring dice-driven randomness.

Additionally, Users can define target numbers and preset success/failure outcomes, allowing the library to intelligently analyze roll results and provide corresponding outcome details. This feature is particularly useful in scenarios where specific outcomes need to be determined based on the dice rolls.

<code style="color : name_color">**DiceRoller**</code> class: This class encapsulates the core functionality of rolling dice and maintaining the state of the last roll.

<code style="color : name_color">**OutcomeDeterminer**</code> class: This class determines the outcome of a dice roll based on a target number and predefined success/failure outcomes.

<code style="color : name_color">**roll_dice**</code> function: This is a utility function that combines the functionality of <code style="color : name_color">DiceRoller</code> and <code style="color : name_color">OutcomeDeterminer</code> to perform a dice roll and return the result and outcome (if a target is provided).

Core functionality is exposed as an API allowing rolling functionality, retrieve roll results, dice types, and colours

Full Documenation is included https://github.com/ViciousSquid/diceroll/tree/main/Docs

### Source is divided into 3 files:


<code style="color : name_color">diceroll.py</code> : Contains the DiceRoller and OutcomeDeterminer classes, as well as the roll_dice function.

<code style="color : name_color">diceroll_anim.py</code> : Contains the <code style="color : name_color">DiceAnimator</code> class, which handles the dice roll animation using the Pygame library.

<code style="color : name_color">roll_dice_example.py</code> : A script that demonstrates the usage of the roll_dice function with and without animation.
