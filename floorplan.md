# Odin floorplan and placement contract

**Generated intent doc for `tools/placement.py` / `tools/place.py`. The code
is authoritative; this page says why.**

## Zones

```text
        SFP0  SFP1        J50   USB-C          top:    cages nose out,
  E  +--------------------------------+  A            input corner right
  F  |  cages intrude to y=41.98       |  B     left:   slots E-H (bank 34,
     |        [ XC7A100T ]            |               package columns 1-8)
  G  |        centre (50,62)          |  C     right:  slots A-D (bank 15,
  H  |  supervisor row      5V buses  |  D            columns 14-26)
     +--------------------------------+        bottom: service row, U7,
       JTAG SWD BOOT   J7/L    J8/M                   5V buses L and M
```

## The lattice (the actual contract)

Signal rows, power row and key post of every extension edge sit on ONE
2.54 mm grid, because a shield PCB bridges all three:

- signal 2x16 centreline 4.70 mm from its edge, rows at 3.43 / 5.97
- power 1x16 centreline 13.59 mm (inner signal row + 3 pitches)
- key post 18.67 mm (inner signal row + 5 pitches)
- body centres at 26.50 and 73.50 along each edge; zone centres +/-10.16
  within each body

`tools/place.py --check` verifies from real pad coordinates that the left
and right sockets expose identical y-lattices (bottom pair: x-lattices) and
that the three rows stay on the grid. It refuses to write a board that
breaks this. It also prints the column-facing convention; copy that line
into `ref/extension-ux.md` once and it is a fact, closing findings item 14
for the electrical part. Stack height remains a mechanical purchase choice.

## SFP mechanical datums

SH1/SH2 use the solder-tail Amphenol U77A11133001 with TE 1888247-1
connectors. The cage footprint origin is the PCB-edge datum at y=0;
its mouth is at y=-7.00 and shell rear at y=41.98. J60/J61 locating-peg
centrelines are at **y=35.40**, derived from cage datum F at 34.50 plus
TE's 0.90 connector offset. Cage rotation is 270°, connector rotation 180°.
See [the drawing comparison](ref/sfp-cage.md).

The shell extends above the SVG's original view; the renderer includes the
full mouth overhang. Anchor positions remain starting values for eye-tuning.
The cage's front region excludes top-side components and signal traces;
several existing group anchors under the cages still need relocation before
applying the full floorplan. This change updates the four SFP placements only.

## Reasoning already burned in

- Bank 34 balls (E-H) are on package columns 1-8, banks 15/13/14 on 14-26,
  so E-H own the left edge and A-D the right; the 5V buses (banks 14/13) and
  the supervisor sideband exit the bottom. No slot escape crosses the die.
- GTP balls are on rows A-F (top of the die); the cages face them across a
  approximately 6.2 mm channel. Refclk oscillator sits at the channel's right end.
- The BGA sits below centre because the cages intrude 41.98 mm from the top.
- USB-C and J50 keep the top-right corner: VBUS parts, PD sink and the
  regulator row anchor there, one entry point for all power.

## PSRAM termination placement

`tools/place.py` places R104–R127 in a column just outside the FPGA's right
edge (15.4 mm from U1 centre, 1 mm pitch), ordered by their associated ball
row/column. Their pad 1 faces the FPGA. This rule keeps them out of the
PSRAM-chip group packing; refine their positions as escape routing develops.
See [the PSRAM layout note](ref/psram.md) for net names and tuning limits.
