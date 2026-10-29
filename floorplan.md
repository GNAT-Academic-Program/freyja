# Odin floorplan and placement contract

**Intent doc for `tools/placement.py` / `tools/place.py`. The code is
authoritative; this page says why.** Rev A state, 2026-10-23.

**Current plan (2026-10-28, owner's choice: `tools/city.py` variant `best`):**
U1 turned 90 degrees, the network jacks (LINK P, LINK Q, ETH) and HDMI on the
**bottom** edge with the JTAG header and AUX IN, the two 5 V bus headers on
the **top** edge with the DC input and USB-C, slots A-D (J3) on the left and
E-H (J5) on the right. The zone sketch and the "top edge: network" section below are
the earlier contract and are kept as history; `ref/city/plan.yaml` and
`ref/city/city.svg` are the plan being compacted by hand. The lattice rules
(signal 2x32, power 1x7, post at position 1) are unchanged and still checked.

**microSD access (findings 45):** J74 sits inboard, south-west of U1, card
opening toward the bottom edge. Access is **from above**: keep the card's
travel (the socket body plus 10 mm toward its opening) and a finger-width
(12 mm) above it free of tall parts, and give any shield or enclosure a
cut-out over that rectangle. No board-edge opening is reserved. Check
insertion and ejection with J72/J2 populated before the layout is frozen.

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

## Top edge: network (historical; the current plan puts the jacks on the bottom)

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
  die. Bank 13 is the top-right quadrant of U1 as mounted; it runs at 1.8 V
  (`+1V8_IO`) and holds both 5 V buses with their DIR/OE and the four PSRAMs,
  so the PSRAM islands belong on that side of U1. The two PHY control pins
  moved to bank 35 (bottom-right corner, with HDMI and the SDRAM data bus);
  the SDRAM's address bus leaves bank 14 (columns 23-26, rows M-T), so U32
  wants the corner between banks 14 and 35. The MRAM and the microSD socket
  take bank 14 balls in columns 22-26; the socket is an edge connector.
- The BGA sits below centre to leave the network strip; the GTP corner is
  unused in rev A (powered, RX grounded).
- USB-C keeps the top-right corner: VBUS parts, PD sink and the regulator
  row anchor there, one entry point for all power.
- X4, the 50 MHz fabric oscillator, sits at U1's left, outside the
  decoupling ring at the MRCC ball it drives (`SYS_CLK`, ball M21,
  `ref/ballmap.md`), short trace, 33 Ω at the source, away from the top
  power door. The city picks that side from the SYS_CLK pin alone (not from
  the +3V3 pads the two share) and reseats X4, R147 and C246 together
  (re-audit 2026-10-29, item 58).
- U34, the +5V source mux, is the junction every ampere of regulated 5 V
  passes through (U11 -> U34 -> U15/U14/U16 and +5V_EXT): the city pulls it
  to U11 first and to the top power door second, and its IN2 bypass is at
  its own pin with U11's bulk beside it (item 57).

## FPGA decoupling placement

The UG483 Table 2-2 network (C301..C393) is placed by hand on F.Cu: the
0.47 µF 0603s in a ring as close to the package as possible, each on its own
via pair; the 4.7 µF 0805s the next ring out; 1210 and D-case bulk anywhere
near the FPGA with multiple vias to the planes. Each bank's six capacitors go
on that bank's side of the package. Nothing goes under the package on B.Cu;
the board is assembled on one side. Full rule and table: `ref/decoupling.md`.

## PSRAM termination placement

R104–R127 (and R151, the SDRAM clock resistor) damp the FPGA's drive and
belong at the FPGA escape, not beside the memory: their design.py groups name
U1 (`U1 PSRAM0 series termination`, `U1 SDRAM clock source`) and
`tools/islands.py` gives the named anchor ownership. On the board they still
sit in the islands of U2–U5 and U32 from before that rule; moving them is
`islands.py --anchor U1 --extend --with R104,...,R127,R151` after review
(findings 44). See [the PSRAM layout note](ref/psram.md) for tuning limits.
## Island placement (tools/islands.py)

Hand placement stays authoritative. `tools/islands.py` is the only script
allowed to move footprints, and only the unlocked passives (prefixes in
`tools/placement.lock.yaml`, default R, C, L, FB) of one anchor's island per
run. Membership follows short nets from each passive to the first locked
footprint; rail-to-GND caps are assigned from their `design.py` group or, failing
that, from where the hand put them. While the anchor is still in the staging
pile the island is built as a self-contained chunk around it (pile neighbours
are not obstacles, chains run straight out); the report prints the chunk box and
the refs to box-select, and the chunk is dragged onto the board by hand.
It is a dry run unless `--apply` is given,
prints the lock table, the membership table and a move report, and renders
`ref/islands/<anchor>[-<net>].svg` for inspection. With `--apply` it rewrites only
the `(at ...)` lines of the moved footprints, then runs `kicad-cli pcb drc`.
One applied island per commit, so any island can be reverted alone.

    python3 tools/islands.py --list-anchors
    python3 tools/islands.py --anchor U13 --island-net +2V5          # review
    python3 tools/islands.py --anchor U13 --island-net +2V5 --apply  # write

Placement inside an island follows the IC's datasheet layout example, encoded
as a profile in `tools/island_profiles.yaml`; the audit behind each profile is
`ref/island-layouts.md`. No profile means the generic ring, chain and signal
rules. The flow for a new IC is: read its layout example, add the audit row, add
the profile, then run the island. Profile rules match on prefix, pin role,
cap-between, between (any two-net part, for divider resistors) and value, and place on a side or flank, with a facing direction and
`outside: NAME` to stack a rule beyond an earlier one, inner to outer as in the
figure. `figure_rotation` names the footprint rotation at which it looks like the
datasheet figure, so directions can be read off the figure (the TSOT26 is upside
down at rotation 0). A rule may set `overhang: MM` to let a row pass the chip's
corners on small packages, and `at: pin` to put a flank part at its pin's corner.
Without a profile, decoupling caps sit at their pins beside any chain
block, and signal parts fold onto the flank next to their pin only while the
folded row fits level with the IC.

A finished chunk is parked in the lot right of the sheet (x 430 to 620, y 10
to 290, outside the A3 frame), stacked top-down like desktop icons. Its marker
on `Cmts.User` is a dashed box round the parts under a solid title bar that
carries the label (`island U13`) and a note (profile, part count, date); the
box, the bar, the texts and the island's footprints are one KiCad group named
after the label, so the island drags as one piece and its title cannot be read
as a neighbour's. Other islands' markers are obstacles when a chunk is parked,
so a small chunk never sits in the empty corner of a bigger island's box.
Rerunning a parked island lands it back in its own slot, so an island can be
re-applied after a rule change without reshuffling the lot. A re-park never
re-lays an island out: `--repark` keeps the reviewed layout and moves the chunk
as one body to its slot (a fresh run would follow today's rules, which may differ
from the ones the layout was reviewed under); `--revert SNAPSHOT` puts an island
back where a `check_positions.py` snapshot has it, the undo of one apply;
`--lot X0 Y0 X1 Y1` parks into another rectangle. Drag each group from the lot
onto the board, then ungroup it (right click, Ungroup) and delete the marker
once the parts are placed.

Placement rule since 2026-10-28 evening: position decides. A part inside the
board outline stays where it is; a part outside may move, unless it is parked in
another island's group. ICs, connectors, crystals, switches and posts are anchors
(`anchor_families` in `tools/placement.lock.yaml`). `--extend` adds new members
to a parked island without touching the parts already there; `--with REF,...`
pulls a part into an island (a TVS to its connector instead of the nearest chip),
`--without REF,...` leaves one out. Rows can lie along an edge (`lie: along`),
sit at a chosen gap (`gap`), and pick their side by direction (`dir: N|E|S|W`,
or `inboard`/`outboard` relative to the board centre); part rotations snap to
90 degrees.

The older connectivity report and the ISLxx net classes moved to
`tools/island_classes.py` (`place.py --stage` imports it).

## City plan (tools/city.py), 2026-10-28

The islands are neighbourhoods; `tools/city.py` lays them out as a city in a
copy of the board outline drawn at 2.2x beside the sheet (x 650 to 870), every
footprint already on the board drawn as a grey ghost at its scaled place. The
owner compacts the blocks by hand onto the board. `python3 tools/city.py` writes
`ref/city/plan.yaml` and a preview; `python3 tools/islands.py --city
ref/city/plan.yaml --apply` moves each island group as one rigid body (turn,
then translate) and rebuilds its box. Rerunning is safe: turns are absolute.

How a block's place is chosen:
- Edges for the user: connectors a cable plugs into sit on an edge, packed in a
  fixed order. Everything else is pulled by wiring: each net shared by two
  blocks pulls the pins on that net together (pins, not centres, so a
  regulator lands on the side of its load where its rail pins are), weighted
  1/(k-1) for a net shared by k blocks; GND is ignored. Blocks then go, in
  order of how strongly they are wired, to the nearest spot that overlaps
  nothing inside the frame.
- U1's rotation and the two edge strips were chosen by scoring, on signal
  balls only, which way each interface faces for every U1 rotation and every
  choice of edge for the network and the 5 V buses. The slot sides are the
  board as placed by hand: A-D (J3) left, E-H (J5) right.

| U1 | network | 5 V buses | A-D to J3 | E-H to J5 | network | buses | score |
|---|---|---|---|---|---|---|---|
| 90 | bottom | top | +0.75 | +0.97 | +0.73 | +0.48 | +115.6 |
| 0 (contract above) | top | bottom | +0.61 | -0.02 | +0.56 | -0.86 | +29.0 |

So the city (variant `best`) turns U1 by 90, puts the three jacks on the bottom
edge under the bank 16 balls (bottom-left), the bus headers J7/J8 with their slot
rows on the top edge, USB-C, the DC input and the AUX input top-right, and the
service row bottom-right. This contradicts the zones at the top of this page
and `tools/placement.py` (jacks top, buses bottom), which were written for the
slot sides the other way round. `python3 tools/city.py --variant contract`
lays out the contract instead. Owner, 2026-10-28: keep `best`; electrical quality first. Before ordering: confirm the
jack mouths in 3D (J70 turned to 180, J71/J72 at 0 for mouths out of the
bottom edge), and update `tools/placement.py` and `place.py --check` if the
bottom-edge bus lattice moves to the top.

Rules that win over wire counts (`SATELLITES` and `CRITICAL` in
`tools/city.py`, each with its reason): a satellite joins its chip's island and
sits on the side where its pins are (RP2350 crystal Y1 and flash U8 with U7, PHY
crystal X3 with U30, the 50 MHz clock X4 with U1); a critical link pulls at full
strength whatever else shares the net, and its blocks are placed first (USB-C to
the eFuse U26, the PD chip U18 and the RP2350; the FPGA to its config flash,
core regulator, PSRAMs and PHY). The bottom edge reads LINK P, LINK Q, JTAG,
ETH: the FPGA JTAG header separates the two experiment jacks from Ethernet.
The bus headers J7/J8 sit symmetric about the board centre (37.3 and 62.7 mm).
J1 (USB-C) is turned 180 in the city: its signal pins sit at the back of the
body, so at rotation 0 the opening faced into the board. `tools/placement.py`
still lists J1 at 0 and needs the same fix. Screw terminals J50 and J68: the
footprint does not show the wire-entry side; check both in the 3D view.

## Power doors, HDMI and 8 layers, 2026-10-28 (late)

Power doors (`DOORS` in `tools/city.py`). The top and bottom of the FPGA's
middle column hold only the unused transceiver balls, so no signal escapes
there and power can enter without blocking one. The right side is taken on
In3 by VCCIO_2 and the slot E-H escape, the left by VCCIO_1 and slots A-D,
the bottom-left corner by bank 16. So the regulators line up at the doors:
U16 (1.2 V), U15 (1.0 V core) and U14 (1.8 V) in a row above the FPGA, U15
centred on the 1.0 V balls (within 1.3 mm), U11 (5 V) right above them,
U13 (2.5 V) below the FPGA beside the PHY. In3 carries +3V3 as the
background, a short wide +1V0 area straight down the middle column, +2V5 up
from below and left under the bank 16 corner, VCCIO_1/VCCIO_2 under their
slot sides; +1V8 and the two transceiver rails go on In5 (their balls are
mixed into the 1.0 V ones). The city gaps look large because the FPGA box
includes its whole decoupling ring; they close when compacted by hand.

X4 and R147 (`RESEAT`) now sit on the FPGA's left, at the SYS_CLK ball,
outside the decoupling ring (16 to 19 mm in the city, was 27 mm and on the
top, where the power door is). The satellite rule missed it because the
clock reaches the ball through R147.

HDMI OUT (Video sheet): J73, Amphenol 10029449-001RLF, on the bottom edge at
83 mm under bank 35 (the FPGA's bottom-right corner), opening out of the
edge at rotation 0 (footprint "PCB Edge" marker at the front). U31,
TPD12S016PWR, joins the J73 block as a satellite (TI: as close to the
connector as possible, no vias between). The SWD connector J51, the JTAG
jumper J52 and BOOTSEL SW1 left the bottom edge and are placed by wiring.
Pairs are 100 ohm (`LVDS_100R` class, outer layers only).

8 layers: `gen_pcb.py --rules-only` inserted the 8-layer list in front of
the old 6-layer one instead of replacing it (`sexpr_block` returned at once
on a marker starting with a newline), and KiCad reads the last list. Fixed;
the board now loads with 8 copper layers. The same bug is why the commit
"Eight layers" never actually gave KiCad 8 layers.
