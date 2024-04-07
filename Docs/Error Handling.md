### Error Handling

Error handling is implemented in various places to gracefully handle and report exceptions:
* When loading dice images, a try-except block catches any <code style="color : name_color">pygame.error</code> exceptions and prints an appropriate error message before exiting the program.
* In the <code style="color : name_color">roll_dice</code> function, a try-except block catches <code style="color : name_color">ValueError</code> and <code style="color : name_color">IndexError</code> exceptions that may occur when parsing the <code style="color : name_color">dice_type</code> string. If an invalid dice type is provided, an error message is printed, and <code style="color : name_color">None</code> is returned.
* In the <code style="color : name_color">perform_dice_roll</code> function, a try-except block catches <code style="color : name_color">KeyError</code> exceptions that may occur when accessing required keys in the <code style="color : name_color">dice_roll_data</code> dictionary. If a required key is missing, an error message is printed, and <code style="color : name_color">None</code> is returned.
* The <code style="color : name_color">determine_outcome</code> function checks if the <code style="color : name_color">roll_result</code> is None before determining the outcome. If roll_result is <code style="color : name_color">None</code>, the function returns <code style="color : name_color">None</code>.