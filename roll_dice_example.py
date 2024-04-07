from dice_api import DiceAPI

# Create a DiceAPI instance
dice_api = DiceAPI()

# Enable roll saving
# This will save the last 5 roll results to a file named "last_5_rolls.txt"
dice_api.enable_roll_saving()

# Roll 2d6 dice
# This will roll two six-sided dice and return the result
result = dice_api.roll_dice("2d6")
print("2d6 Roll Result:")
print(result)

# Roll 1d20 dice
# This will roll one twenty-sided die and return the result
result = dice_api.roll_dice("1d20")
print("\n1d20 Roll Result:")
print(result)

# Roll 3d8+1d4 dice
# This will roll three eight-sided dice and one four-sided die, and return the total sum
result = dice_api.roll_dice("3d8+1d4")
print("\n3d8+1d4 Roll Result:")
print(result)

# Roll 2d10 dice with a target of 15
# This will roll two ten-sided dice and compare the result against the target value of 15
# If the roll result is greater than or equal to 15, it will be considered a success
# Otherwise, it will be considered a failure
result = dice_api.roll_dice("2d10")
print("\n2d10 Roll Result (Target: 15):")
print(result)
if result["roll_result"] >= 15:
    print("Success!")
else:
    print("Failure.")

# Get the last 5 roll results
# This will retrieve the last 5 roll results saved by the DiceRoller
last_5_rolls = dice_api.dice_roller.get_last_5_rolls()
print("\nLast 5 Roll Results:")
for i, roll_data in enumerate(last_5_rolls, 1):
    print(f"Result {i}:")
    print(f"  Dice Type: {roll_data['dice_type']}")
    print(f"  Roll Result: {roll_data['roll_result']}")
    print(f"  Roll Details: {roll_data['roll_details']}")

# Disable roll saving
# This will stop saving the roll results to the file
dice_api.disable_roll_saving()

# Roll 1d6 dice
# This roll result will not be saved to the file
result = dice_api.roll_dice("1d6")
print("\n1d6 Roll Result (Not Saved):")
print(result)

# Get the available dice colours
# This will retrieve the list of available dice colours for the dice animation
available_colours = dice_api.get_available_dice_colours()
print("\nAvailable Dice Colours:")
print(available_colours)