# Voron Zero

![Image of Voron Zero](http://vorondesign.com/images/voron0.1_bg.jpg)

The official release of the Voron Zero 3d printer.  You can find the BOM in the configurator located at the [Voron Design]( http://vorondesign.com/voron0) website.

The current revision is V0.1.

## Highlights
- Compact and portable
- 120x120x120 build volume
- CoreXY
- Low mass direct drive extruder
- Enclosed chamber
- 24v DC bed simplifies electronics
- Klipper firmware

## Release History
### V0.1 (2021 April)

A majority of the printed parts have changed. The configurator will give you an idea of parts needed if you are upgrading from V0.0.

**Toolhead**
- New design: Mini Afterburner
- Direct Drive Extruder with BMG gears and pancake motor with 10 tooth spur gear
- Improved part cooling ducts (fans are same as V0.0)
- Supports Mosquitto, Dragon, Dragonfly mounts
- V6 mount too large for DDE (bowden still an option)

**Z motor**
- Simplified to use Nema17 integrated T8x8 200mm leadscrew and printed mount (highly recommended upgrade)

**Drive units**
- A/B steppers changed to larger 40Ncm motors for increased torque (optional upgrade)
- Parts are now embossed with “A” or “B” respectively to avoid improper assembly
- Motor screws are countersunk to add more thread engagement 
- Panel mount point added

**Frame**
- No changes

**Electronics**
- Move from AC to 24v 60 watt DC bed (no more SSR)
- 150 watt PSU (larger to support DC bed)
- Fused AC power inlet (now with switch)
- SKR moves to rear compartment and Mini E3 V2.0 now spec
- PSU terminal cover

**Tophat**
- All panels have changed
- Front and rear are now straight vertical to accommodate new toolhead
- Sides went from 15° to 10°
- 10mm taller all around
- Lower panel clips are built into frame mounts

**Panels/clips**
- Front deck panel is unchanged
- Mid and back panel has various holes removed (can use your V0.0 panels)
- Rear deck panel is gone
- Motor panel is added (can be printed later)
- Side windows and door are unchanged
- Rear upper panel clips have an added mount point

**X/Y Joints**
- Hex nuts replaced with threaded inserts
- Idlers replaced by F623 bearing stack (hole adjusted to align perfectly in CAD)
- Endstop block changed to be compatible with DD toolhead
- Inaccessible bottom gantry screw holes removed

**Bed Assembly**
- Rear mounts extended 3mm to account for DD toolhead position changes
- Z chain mount adjusted to accommodate off-the-shelf chain or printed beltchain
- Zip tie mounts added for cable routing
- Removed horizontal bolt hole to prevent over-constraining assembly 
- Front mount reduced in size for less plastic use
- Printed thumb screws for bed adjustments

**Feet/Skirts**
- Extended to accommodate 34mm Z motor

**Front Idlers**
- No changes


### V0.0 Updates and fixes (2020 Sept)
See https://github.com/VoronDesign/Voron-0/releases/tag/V0.0r1

### V0.0 Initial release (2020 April)
See https://github.com/VoronDesign/Voron-0/releases/tag/V0.0

![Voron Logo](http://vorondesign.com/images/voron_design_logo.png)
