# Fixed import statement: Use 'diceroll_api' and 'dicerollAPI'
from diceroll_api import dicerollAPI, DiceColor # Import DiceColor too

print("--- Dice Roller GUI Example (Console Part) ---")

# Create a dicerollAPI instance
dice_api = dicerollAPI()

# Enable roll saving
dice_api.enable_roll_saving()
print("Roll saving enabled.")

# --- Perform Console Rolls ---
result = dice_api.roll_dice("2d6")
print("\n2d6 Roll Result:", result["roll_result"])

result = dice_api.roll_dice("1d20")
print("1d20 Roll Result:", result["roll_result"])

result = dice_api.roll_dice("3d8+1d4")
print("3d8+1d4 Roll Result:", result["roll_result"])

result = dice_api.roll_dice("2d10", target_value=15)
print("2d10 Roll Result (Target: 15):", result["roll_result"])
if result and result.get('success', False):
    print("Success!")
else:
    print("Failure.")

# Get the last 5 roll results
last_5_rolls = dice_api.get_last_5_rolls()
print("\nLast 5 Roll Results:")
if last_5_rolls:
    for i, roll_data in enumerate(last_5_rolls, 1):
        print(f"Result {i}:")
        # Fixed key error: Use 'dice_notation'
        print(f"  Dice Notation: {roll_data['dice_notation']}")
        print(f"  Roll Result: {roll_data['roll_result']}")
        print(f"  Roll Details: {roll_data['roll_details']}")
else:
    print("No rolls yet.")

# Disable roll saving
dice_api.disable_roll_saving()
print("\nRoll saving disabled.")

result = dice_api.roll_dice("1d6")
print("1d6 Roll Result (Not Saved):", result["roll_result"])

print("\n--- Now attempting Animation ---")

# --- Perform Animated Roll (Explicitly Import and Use Animator) ---
try:
    from diceroll_anim import DiceAnimator # Import Animator here

    print("Creating DiceAnimator...")
    dice_animator = DiceAnimator() # Create it only when needed
    print("Running animation...")
    # Use DiceColor.RED
    roll_result = dice_animator.run_animation("1d20+1d6", dice_color=DiceColor.RED, target=18)
    print("\nAnimated Roll Result:")
    print(roll_result)

except ImportError:
    print("\nPygame is not installed or diceroll_anim not found. Skipping dice roll animation.")
except Exception as e:
    print(f"\nAn error occurred during animation: {e}")

print("\n--- GUI Example Finished ---")