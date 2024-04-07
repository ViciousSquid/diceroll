To make a call through the DiceAPI asking for a blue-colored dice and a roll of 2d6, you would use the roll_dice method of the DiceAPI class. Here's an example of how you could do it:

First, you need to import the `DiceAPI` class from the diceroll.dice_api module:

```
from diceroll.dice_api import DiceAPI
```

Then, you can create an instance of the `DiceAPI` class:

```
dice_api = DiceAPI()
```

To roll a blue-coloured 2d6, you can call the roll_dice method of the DiceAPI instance and pass the "2d6" string as the dice_type argument, and the "blue" string as the dice_colour argument:

```
roll_result = dice_api.roll_dice("2d6", dice_colour="blue")
```

The `roll_dice` method returns a dictionary containing the following keys:

* "dice_type": The string representing the dice type rolled (e.g., "2d6").
* "roll_result": The total result of the dice roll.
* "roll_details": A list containing the individual results of each die roll.

You can access the individual components of the returned dictionary like this:

```
from diceroll.diceroll_anim import DiceAnimator

dice_animator = DiceAnimator()
animated_roll_result = dice_animator.run_animation("2d6", dice_colour="blue")
```

The run_animation method of the DiceAnimator class will open a window and display an animation of the dice roll, and it will return the same dictionary as the roll_dice method of the DiceAPI class.

Here's an example of how you could use both the DiceAPI and DiceAnimator classes together:

```
from diceroll.dice_api import DiceAPI
from diceroll.diceroll_anim import DiceAnimator

dice_api = DiceAPI()
dice_animator = DiceAnimator()

roll_result = dice_api.roll_dice("2d6", dice_colour="blue")
print(f"Dice Type: {roll_result['dice_type']}")
print(f"Roll Result: {roll_result['roll_result']}")
print(f"Roll Details: {roll_result['roll_details']}")

animated_roll_result = dice_animator.run_animation("2d6", dice_colour="blue")
```

This code will first roll the 2d6 dice using the DiceAPI class and print the results, and then it will display an animation of the same 2d6 dice roll using the DiceAnimator class.
