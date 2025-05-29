# Fixed import statement: Use 'diceroll_api' and 'dicerollAPI'
from diceroll_api import dicerollAPI

print("--- Dice Roller Console Example ---")

# Create a dicerollAPI instance (fixed class name)
dice_api = dicerollAPI()

# Enable roll saving
dice_api.enable_roll_saving()
print("Roll saving enabled (last_5_rolls.txt)")

# --- Perform Rolls ---

# Roll 2d6 dice
result_2d6 = dice_api.roll_dice("2d6")
print("\n--- 2d6 Roll Result ---")
print(result_2d6)

# Roll 1d20 dice
result_1d20 = dice_api.roll_dice("1d20")
print("\n--- 1d20 Roll Result ---")
print(result_1d20)

# Roll 3d8+1d4 dice
result_mixed = dice_api.roll_dice("3d8+1d4")
print("\n--- 3d8+1d4 Roll Result ---")
print(result_mixed)

# Roll 2d10 dice with a target of 15
result_target = dice_api.roll_dice("2d10", target_value=15)
print("\n--- 2d10 Roll Result (Target: 15) ---")
print(result_target)
if result_target and result_target.get('success', False):
    print("Success!")
else:
    print("Failure.")

# --- Get History ---
last_5_rolls = dice_api.get_last_5_rolls() # Direct access via API getter
print("\n--- Last 5 Roll Results ---")
if last_5_rolls:
    for i, roll_data in enumerate(last_5_rolls, 1):
        print(f"Result {i}:")
        # Fixed key error: Use 'dice_notation' instead of 'dice_type'
        print(f"  Dice Notation: {roll_data['dice_notation']}")
        print(f"  Roll Result: {roll_data['roll_result']}")
        print(f"  Roll Details: {roll_data['roll_details']}")
else:
    print("No rolls in history yet.")


# Disable roll saving
dice_api.disable_roll_saving()
print("\nRoll saving disabled.")

# Roll 1d6 dice
result_nosave = dice_api.roll_dice("1d6")
print("\n--- 1d6 Roll Result (Not Saved) ---")
print(result_nosave)

print("\n--- Console Example Finished ---")