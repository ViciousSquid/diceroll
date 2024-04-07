The <code style="color : name_color">**animate_dice_roll**</code> function provides a visually engaging animation of the dice roll process. It consists of two distinct animation phases: shaking and tumbling.

**Shaking Animation Phase:**

This phase lasts for specified duration <code style="color : name_color">(shake_duration)</code>

During this phase, the following steps occur in a loop:

* The window is cleared with a white background.
* A random dice image from the loaded set is selected and displayed.
* The selected dice image is slightly rotated and offset to create a shaking effect. The rotation angle and offset values are randomly generated for each iteration.
* The rotated and offset dice image is drawn (blitted) onto the window.
* The display is updated to reflect the changes.
* The animation frame rate is limited to 30 frames per second (FPS) for a smoother appearance.

**Tumbling Animation Phase:**

This phase lasts for specified duration <code style="color : name_color">(tumble_duration)</code>
During this phase, the following steps occur in a loop:

* The window is cleared with a white background.
* A random dice image from the loaded set is selected and displayed.
* The selected dice image is continuously rotated to create a tumbling effect. The rotation angle is calculated based on the elapsed time and the total tumble duration, ensuring a smooth and continuous tumbling motion.
* The rotated dice image is drawn (blitted) onto the window at the center position.
* The display is updated to reflect the changes.
* The animation frame rate is limited to 60 FPS for a smoother appearance.

## Final Result Display:**

After the shaking and tumbling animations, the actual dice roll is performed using the <code style="color : name_color">roll_dice</code> function from the <code style="color : name_color">DiceRoller</code> class.
The final dice image corresponding to the roll result is displayed.
The roll result is rendered as text and displayed on the window.
There is a short delay (3 seconds) to allow the user to see the final result before the function returns the roll result.

## Customization Options:**

* The <code style="color : name_color">animate_dice_roll</code> function accepts two additional boolean parameters: <code style="color : name_color">shake_dice</code> and <code style="color : name_color">tumble_dice</code>.
* These flags control whether the shaking and tumbling animations are enabled or disabled, respectively. By default, both animations are enabled.
* You can customize the animation durations by adjusting the <code style="color : name_color">shake_duration</code> and <code style="color : name_color">tumble_duration</code> values according to your preference.
