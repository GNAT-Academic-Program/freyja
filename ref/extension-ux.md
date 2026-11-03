# Odin extension connector

## Sections and connector bodies

A 16 shield bridges A/E (or another matching section pair) for 24 I/O;
a 32 spans two section pairs for 48 I/O; a 64 spans all four for 96 I/O.
A-D use J3A/J3B and E-H use J5A/J5B. The intended contract has the J5 pair
on the left and the J3 pair on the right, each pair centred at board-local
y=50.00 mm. Each edge is one continuous 2x32 lattice carried by two
HC-PM254-8.5H-2x16PZ 2x16 through-hole female bodies, C22373921, H8.5, end to
end: a 2.54 mm body is exactly 16 x 2.54 = 40.64 mm long, so the pitch runs
through the joint and a shield's 2x32 male strip mates as before. J3A carries
sections A and B (its pins 1-32 are positions 1-32 of the former single body),
J3B sections C and D (pin n = former position n+32); J5A carries E and F, J5B
G and H (on the left edge the former J5 numbering ran from the H end: J5B pin n
= former position n, J5A pin n = former position n+32). Smaller shields occupy
contiguous sub-ranges starting and ending on eight-column section boundaries.

**Placement is not certified.** The authoritative hand-placed PCB was not
moved to this contract. In the current PCB, J3/J5 remain on their previous,
opposite edges with unequal longitudinal centres. The posts also retain
their previous positions. The human must reconcile these positions before
a shield can mate. Do not build a shield from the contract alone.

## Per-section contacts

Columns are in increasing board-coordinate direction along the row;
the pattern is identical on both edges, never mirrored.

| Row / column | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Signal row 1 | IO0 | IO2 | GND | IO4 | IO6 | GND | IO8 | IO10 |
| Signal row 2 | IO1 | IO3 | GND | IO5 | IO7 | GND | IO9 | IO11 |
| Power row | GND POST | PIN V | GND | 3V3 | GND | 5V | GND | AUX |

There are four signal-row GND contacts, three female power-row GND contacts,
and one grounded mechanical post/probe point. The post is **not a mated
electrical contact**. Every power rail has a neighboring ground contact.
Six signal pairs occupy one column each; use the ball map for differential
capability and bank-voltage requirements.

J7/J8 serve L/M, the two complete eight-bit 5 V buses, using a 2x8
2.54 mm female socket, 8.5 mm body, C30734. Their columns 3 and 6 are also GND in both rows;
columns 7 and 8 are NC in both rows because only eight bus bits exist.
Each bus has one shared direction control and an active-low enable with
a default-disable pull-up. A-H are raw FPGA pins, not 5 V tolerant.

## Keyed power row and shield obligations

Each zone uses C41426870 (Boom B254N02-0B7P51-H85C32, 3 A), a 1x7 female on columns
1..7. A-H retain MK65..MK72; L/M retain MK76/MK77 for the GND post on column 8, one
pitch off the socket's line toward the board edge.
Female references are A:J53, B:J62, C:J54, D:J63, E:J55, F:J64,
G:J56, H:J65, L:J57, M:J58.

The shield must provide:

- A male 1x7 strip on columns 1..7; cut a breakaway strip such as C2337.
- A **bare NPTH >=1.6 mm at the post** (column 8, one pitch toward the edge), with **no plated contact** there.
  A pin rubbing a plated hole is not a contact.
- Mating pin projection below the shield PCB **<=9 mm**.
- Seating height of approximately **11 mm** with plain male strips, or
  **8.5 mm** with a compatible stack-through female option. Verify the
  actual contact engagement and insulator stack before choosing parts.
- One male 2x32 signal strip per edge for a 64 shield, or a suitable
  2x40 breakaway cut to 2x32. Smaller shields populate only their sub-ranges.
  The L/M male 2x8 counterpart is C779499. Stack-through female options must
  preserve this pin map and provide the required downward male pins.

The post tip must stand **>=18.5 mm above the base board**, so wrong insertion
is rejected **before any signal or power pin touches any socket**. C51353
(21 mm donor, cut to 1P, hand/wave soldered) is provisional: total pin length
is not installed projection. **TODO:** qualify a ~25 mm donor if necessary.

With the post off the socket's line, a 180-degree reversal about the zone
centre puts it on column 1, one pitch on the other side of the line: not the
key hole, so it meets solid shield material. A shift along the row keeps it off
the line, so it cannot enter a contact hole there either. This argument depends
on every post having the same offset, the shield keeping that area free of
holes, adequate shield coverage at its boundary, and sufficient post
projection. It has not been tried on a real shield. Signal bodies do not key
the shield. It does not certify arbitrary out-of-row offsets or abusive tilt.

## Power and voltage domains

J19 sets PIN V for A-D (FPGA bank 15); J20 sets E-H (bank 34).
Selections are 3.3/2.5/1.8 V. Every section in a domain shares the selected
voltage. L/M PIN V remains 3.3 V; their signal translation is separately 5 V.

AUX: **9-28V raw via AUX IN, 1A per zone, see power corner.** There is no
on-board AUX converter; all ten AUX branches share the J68 terminal.
The per-zone fitted PTC is C70150, actually **1.1 A hold / 33 V at 25 C**,
not an exact 1.0 A-hold device; its temperature derating must be respected.
This remains a deviation from the exact 1 A-hold request, not a silent rating
change. PIN V/3V3/5V branch PTCs are 500 mA / 500 mA / 1.1 A hold (2026-11-03,
were 500/300/500): one slot can carry a display, a radio module or a small
servo on 5 V. The buses above are the ceiling the ten slots share: U21 2 A on
5 V, U22 1 A on 3.3 V, so two slots at their PTC rating already exceed the
bus, and a dead short is cleared by the bus switch (every slot on that bus
drops, EXT_FAULT) rather than isolated by the slot PTC; a sustained overload
below the switch limit opens the slot PTC alone.

Four low-voltage protection channels remain (U21-U24) under EXT_EN. U21/U22
(TPS22950C) limit current and report on EXT_FAULT; U23/U24 are TPS22975
switches biased from +3V3 so the 1.8 V PIN V setting is inside their rating:
they ramp in about 1.2 ms (CT 1 nF, 3.3 V) and the 500 mA PINV fuse in each
slot is the overload limit. They report nothing (no PG pin; EXT_FAULT comes
from U21/U22/U26 only), they do not block reverse current (while off the
output is discharged through 230 ohm, but a voltage forced onto PIN V
reaches the domain through the switch's body diode), four slots share each
domain so four 500 mA fuses are not a 500 mA ceiling, and the switch has
thermal shutdown only: a shorted PIN V branch against the shared upstream
rail is a bench test, not a proven isolation. The controller measures both
PIN V domains (MON_VCCIO_1/2), so firmware knows the jumper setting.
AUX no longer has U25's active reverse-blocking/current-limit protection.
PTCs isolate sustained branch faults; overload can droop the shared source.
Never backfeed a power contact. A PTC is not instantaneous short protection.
See [the power manual](power.md) for actual shared allocations and release holds.

## Tall-part shield keep-outs

Generated from the **current saved PCB**, read-only, by
`/usr/bin/python3 tools/placement.py --keepouts`. Coordinates are board-local.
These are XY envelopes to clear, not a claim that an 8.5 or 11 mm seat clears
the jacks/terminals. Provide cutouts or independently verified height clearance
and screwdriver access. New AUX IN placement must be chosen by the human and
this table regenerated afterward. The key posts require their NPTHs instead
of plated sockets.

| Ref | Board-local X interval (mm) | Y interval (mm) | Shield obligation |
|---|---:|---:|---|
| J70 | 103.95 to 120.04 | 241.17 to 262.52 | jack cutout and cable access; currently outside board, human placement pending |
| J71 | 124.29 to 140.34 | 245.10 to 263.64 | jack cutout and cable access; currently outside board, human placement pending |
| J72 | 144.29 to 160.34 | 245.10 to 263.64 | jack cutout and cable access; currently outside board, human placement pending |
| J50 | 169.09 to 179.14 | -155.08 to -147.43 | terminal cutout and screwdriver access; currently outside board, human placement pending |
| J68 | 88.75 to 98.80 | 91.48 to 99.13 | terminal cutout and screwdriver access |
| MK65 | centre 11.90 | centre 22.00 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK66 | centre 88.00 | centre 23.00 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK67 | centre 11.90 | centre 42.30 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK68 | centre 11.90 | centre 62.60 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK69 | centre 11.90 | centre 82.90 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK70 | centre 87.70 | centre 83.40 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK71 | centre -123.67 | centre 100.44 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK72 | centre -123.67 | centre 120.84 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK76 | centre 88.00 | centre 63.60 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK77 | centre 88.00 | centre 43.20 | >=1.6 mm bare NPTH; post tip >=18.5 mm |

The EDGE_SIG inset remains 4.70 mm. No perfboard-lattice change, placement
application, island staging, decap movement or BGA fanout was performed.
