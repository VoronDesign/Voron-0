## V0 Configuration Files:

# printer.cfg
***
 - This is the base config that will need tweaking to your specific setup.

# bedScrews.cfg
***
This is an addon to the main config that contains the code needed to enable and add the Bed Screw calibration menu to the printers screen.
This routine moves your nozzle overtop of the 3 bed screws on the V0 and allows you to manually adjust them to flatten the bed to the z-position of your endstop.
If you want to use this add-on config, place the `bedScrew.cfg` file into the same location as your `printer.cfg` and add `[include bedScrew.cfg]` to the bottom of the config.
