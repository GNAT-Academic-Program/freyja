# Odin floorplan and placement contract

**Intent doc for `tools/placement.py` / `tools/place.py`. The code is
authoritative; this page says why.** Rev A state, 2026-10-23.

## Zones

```text
   J50  LINK P  LINK Q   ETH        USB-C      top:    three RJ45 mouths out,
  E  +--------------------------------+  A            PHY under ETH, screw
  F  |  network strip   [PHY]  [X4]   |  B            terminal top-left
     |        [ XC7A100T ]            |        left:   slots E-H (bank 34,
  G  |        centre (50,62)          |  C            package columns 1-8)
  H  |  supervisor row      5V buses  |  D     right:  slots A-D (bank 15,
     +--------------------------------+               columns 14-26)
       JTAG SWD BOOT   J7/L    J8/M           bottom: service row, U7,
                                                      5V buses L and M
```

## The lattice (the actual contract)

Signal rows, power row and key post of every extension edge sit on ONE
2.54 mm grid, because a shield PCB bridges all three:

- signal 2x32 centreline 4.70 mm from its edge, rows at 3.43 / 5.97
- power 1x7 centreline 13.59 mm (inner signal row + 3 pitches)
- one continuous signal body per left/right edge, centred at y = 50; zone
  centres 20.32 mm apart within it; position 1 of every power row is the
  grounded key post

`tools/place.py --check` verifies from real pad coordinates that the left
and right sockets expose identical y-lattices (bottom pair: x-lattices) and
that the rows stay on the grid. It refuses to write a board that breaks
this. Stack height remains a mechanical purchase choice.

## Top edge: network

Three tab-down RJ45 jacks at 17.8 mm pitch, mouths about 3 mm past the edge:
LINK P (J71, x = 25.0), LINK Q (J72, x = 42.8), ETH (J70, x = 60.6). J50
moves to the top-left corner (9.5, 4.2), USB-C keeps (79.0, 2.6). The
imported footprints put the HanRun magjack's mouth at −y (LED pins at the
front) and the Kinghelm plain jack's at +y (shell tabs at the front), hence
rotations 0 and 180; **confirm both in the 3D view** (STEP models imported)
before ordering. The PHY (U30) sits between ETH and the FPGA with its crystal
beside it; the link jacks' ESD arrays go right behind their jacks. Bank 16
is the top-left quadrant of U1 and faces this strip, so the eight LVDS pairs
and the RGMII bus run straight up. Positions are a proposal for phase B hand
placement, not a measured contract.

## Reasoning already burned in

- Bank 34 balls (E-H) are on package columns 1-8, banks 15/13/14 on 14-26,
  so E-H own the left edge and A-D the right; the 5V buses (bank 13) and the
  supervisor sideband (bank 14) exit the bottom. No slot escape crosses the
  die. Bank 13 is the top-right quadrant of U1 as mounted; both 5 V buses,
  their DIR/OE and the two 3.3 V PHY pins live there.
- The BGA sits below centre to leave the network strip; the GTP corner is
  unused in rev A (powered, RX grounded).
- USB-C keeps the top-right corner: VBUS parts, PD sink and the regulator
  row anchor there, one entry point for all power.
- X4, the 50 MHz fabric oscillator, sits just above U1 near bank 14's MRCC
  ball it drives (`SYS_CLK`, `ref/ballmap.md`), short trace, 33 Ω at the
  source.

## FPGA decoupling placement

The UG483 Table 2-2 network (C301..C393) is placed by hand on F.Cu: the
0.47 µF 0603s in a ring as close to the package as possible, each on its own
via pair; the 4.7 µF 0805s the next ring out; 1210 and D-case bulk anywhere
near the FPGA with multiple vias to the planes. Each bank's six capacitors go
on that bank's side of the package. Nothing goes under the package on B.Cu;
the board is assembled on one side. Full rule and table: `ref/decoupling.md`.

## PSRAM termination placement

`tools/place.py` places R104–R127 in a column just outside the FPGA's right
edge (15.4 mm from U1 centre, 1 mm pitch), ordered by their associated ball
row/column. Their pad 1 faces the FPGA. This rule keeps them out of the
PSRAM-chip group packing; refine their positions as escape routing develops.
See [the PSRAM layout note](ref/psram.md) for net names and tuning limits.
