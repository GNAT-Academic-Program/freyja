# Odin extension connector

## Sections and connector bodies

A 16 shield bridges A/E (or another matching section pair) for 24 I/O;
a 32 spans two section pairs for 48 I/O; a 64 spans all four for 96 I/O.
A-D use J3 and E-H use J5. The intended contract has J5 on the left and
J3 on the right, each centred at board-local y=50.00 mm. Each edge is one
WingTAT 2044-2X32G00SA 2x32 through-hole female body, C49569844, H8.5.
There is no two-body seam. Smaller shields occupy contiguous sub-ranges
starting and ending on eight-column section boundaries.

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

J7/J8 serve L/M, the two complete eight-bit 5 V buses, using HCTL
PM254-2-08-Z-8.5, C2897409. Their columns 3 and 6 are also GND in both rows;
columns 7 and 8 are NC in both rows because only eight bus bits exist.
Each bus has one shared direction control and an active-low enable with
a default-disable pull-up. A-H are raw FPGA pins, not 5 V tolerant.

## Keyed power row and shield obligations

Each zone uses C2832270 (XFCN PM254V-11-07-H85), a 1x7 female at positions
2..8. A-H retain MK65..MK72; L/M retain MK76/MK77 for the GND post at position 1.
Female references are A:J53, B:J62, C:J54, D:J63, E:J55, F:J64,
G:J56, H:J65, L:J57, M:J58.

The shield must provide:

- A male 1x7 strip at positions 2..8; cut a breakaway strip such as C2337.
- A **bare NPTH >=1.6 mm at position 1**, with **no plated contact** there.
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

With the uniform position-1 post, a 180-degree reversal maps position
p to 9-p: a fixed key would require p=9-p, with no integer solution.
An in-row shift of 1..7 pitches puts a post under a populated contact or
solid shield material rather than the sole bare key hole. This argument
depends on every post occupying exactly position 1, adequate shield coverage
at its boundary, and sufficient post projection. Signal bodies do not key
the shield. It does not certify arbitrary out-of-row offsets or abusive tilt.

## Power and voltage domains

J19 sets PIN V for A-D (FPGA bank 15); J20 sets E-H (bank 34).
Selections are 3.3/2.5/1.8 V. Every section in a domain shares the selected
voltage. L/M PIN V remains 3.3 V; their signal translation is separately 5 V.

AUX: **9/12/15/24 regulated, or 9-28V raw via AUX IN,
1A per zone, see power corner.** All ten AUX branches share J66's source.
The per-zone fitted PTC is C70150, actually **1.1 A hold / 33 V at 25 C**,
not an exact 1.0 A-hold device; its temperature derating must be respected.
This remains a deviation from the exact 1 A-hold request, not a silent rating
change. PIN V/3V3/5V branch PTCs remain 500/300/500 mA.

Four low-voltage protection channels remain (U21-U24), with EXT_EN/EXT_FAULT.
AUX no longer has U25's active reverse-blocking/current-limit protection.
PTCs isolate sustained branch faults; overload can droop the shared source.
Never backfeed a power contact. A PTC is not instantaneous short protection.
See [the power manual](power.md) for actual shared allocations and release holds.

## Tall-part shield keep-outs

Generated from the **current saved PCB**, read-only, by
`/usr/bin/python3 tools/placement.py --keepouts`. Coordinates are board-local.
These are XY envelopes to clear, not a claim that an 8.5 or 11 mm seat clears
the cages/terminals. Provide cutouts or independently verified height clearance
and screwdriver access. New AUX IN placement must be chosen by the human and
this table regenerated afterward. The key posts require their NPTHs instead
of plated sockets.

| Ref | Board-local X interval (mm) | Y interval (mm) | Shield obligation |
|---|---:|---:|---|
| SH1 | 16.60 to 33.40 | -7.27 to 42.67 | cage cutout/clearance |
| SH2 | 66.60 to 83.40 | -7.27 to 42.67 | cage cutout/clearance |
| J50 | 169.09 to 179.14 | -155.08 to -147.43 | terminal cutout and screwdriver access; currently outside board, human placement pending |
| J68 | 161.43 to 171.48 | 122.48 to 130.13 | terminal cutout and screwdriver access; currently outside board, human placement pending |
| MK65 | centre 11.90 | centre 22.00 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK66 | centre 143.20 | centre 17.40 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK67 | centre 11.90 | centre 42.30 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK68 | centre 11.90 | centre 62.60 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK69 | centre 11.90 | centre 82.90 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK70 | centre 143.40 | centre 81.80 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK71 | centre -123.67 | centre 100.44 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK72 | centre -123.67 | centre 120.84 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK76 | centre 143.20 | centre 60.20 | >=1.6 mm bare NPTH; post tip >=18.5 mm |
| MK77 | centre 143.20 | centre 38.80 | >=1.6 mm bare NPTH; post tip >=18.5 mm |

The EDGE_SIG inset remains 4.70 mm. No perfboard-lattice change, placement
application, island staging, decap movement or BGA fanout was performed.
