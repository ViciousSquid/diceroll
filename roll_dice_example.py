# roll_dice_example.py

from diceroll import roll_dice

# Roll 2d6 dice with a target of 7, success outcome, and failure outcome
result = roll_dice("2d6", target=7, success_outcome={"details": "Success!"}, failure_outcome={"details": "Failure."})
print(result)

# Roll 1d20 dice with animation
result = roll_dice("1d20", use_animation=True)
print(result)