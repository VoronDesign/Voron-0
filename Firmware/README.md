# Voron 0.1 Stock Printer Config Example

For detailed instructions on setting up your Voron, visit https://docs.vorondesign.com/build/startup/

As always, check Discord #voron_0_questions for help

## Quick Start

* Find and update your unique mcu `serial`
* Do a `STEPPER_BUZZ STEPPER=stepper_x` and repeat for each stepper
* Test each endstop using `QUERY_ENDSTOPS`
* Be ready to emergency stop, practice it
* Try homeing each axis, `G28 X` then `G28 X Y` then `G28`
* Adjust direction `dir_pin` as necessary
* Do a `BED_SCREWS_ADJUST` with the paper test
* Check fans are working properly
* Validate your thermistors `sensor_type`
* Tune bed `PID_CALIBRATE HEATER=heater_bed TARGET=100`
* Tune hotend with `M106 S64` then `PID_CALIBRATE HEATER=extruder TARGET=245`

## Warnings

* If using mainsail or others, you will likely need a special include or other adjustments
* You may need to swap your A/B motor physical connections and/or software stepper directions
* This firmware assumes stock BOM with Mini Stealthburner DD toolhead