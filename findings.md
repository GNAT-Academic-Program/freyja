# Freyja — current status and dated findings

## Current status — 2026-11-04 routing checkpoint

**PSRAM0/1 routing transferred** to `kicad/odin.kicad_pcb`: all six signals of
both ports, through R104–R115 to U2/U3, with pull branches. All 60 pads on the
24 nets connect. R104–R115, C337, C341 and C394 moved; no other footprint did.
C337/C341 reach the +3V3 and GND planes; C394 ties to FB1 output and C261 by
copper and to GND. Nothing else was connected: stress-test copper, dogbones,
placeholder vias and the provisional T16 chain were left out.

**PSRAM2/3 routing transferred**: all six signals of both ports, through
R116–R127 to U4/U5, with pull branches. All 60 pads on the 24 nets connect; with
PSRAM0/1 that is **120 of 120 pads on 48 nets**. R116–R127 moved along their
existing column (x 189.898) so each resistor faces its own memory; no other
footprint moved. Ball-to-resistor is 14.2–37.8 mm with 2 vias each;
resistor-to-memory is 6.2–15.3 mm with 0 or 2 vias. CE_B on U4 has a third via,
because accepted `PSRAM1_IO0_MEM` separates its pin from its pull. Per port,
ball to pin: PSRAM2 26.2–44.3 mm (SCK 34.1), PSRAM3 22.4–36.5 mm (SCK 36.5, the
longest), against PSRAM0 31.9–38.2 and PSRAM1 28.2–37.4.

PSRAM2 is the tight port. T19, T20, U19 and U20 sit between accepted In2/In5 lanes
and the `PSRAM1_IO2` B.Cu lane. SCK (In2) and CE_B (In5) leave on row y 142.84
between three +1V8_IO vias, since moved by the repair below (0.19 mm or more
clear now; it was 0.154 mm when routed). IO2 goes
round on B.Cu and is the longest of the 12 ball legs (37.8 mm); one pocket ball
has to take that way round while the accepted lanes stay.

**PSRAM grounds and return stitching transferred.** U2–U5 pin 4 and all 20 pull GND
pads reach the main piece of In1, In4 and In6 through their own vias (stubs 0.62–
1.31 mm, pad centre to via). The memories' C111–C114 and the rest of the 17 `+1V8_IO`
capacitors' GND pads were already connected. Of the 73 PSRAM vias, 23 go F.Cu↔In2
and keep In1 as reference, so they get no stitching. The other 50 go to In5 or B.Cu
and change reference from In1 to In6; 48 now have a GND via within 2.0 mm, a target
chosen here (worst 2.56 mm). This took 44 new vias: the 24 above, 6 U1 GND-ball
dogbones with their stubs (U18, W22, V15, Y19, T21, T13), and 14 stitching vias.
Of those 14, 4 use reserved GND sites of C336, C338, C340 and C246 without connecting
the capacitors; 10 are new sites outside the BGA lattice and part courtyards.

Plane continuity was read from the refilled In1 and In6. Of 125 track crossings
of a void, 112 are a track leaving its own via and 11 are that same case with a
neighbouring clearance merged in (9 end in the void; the 2 measured add 0.59 and
0.12 mm to the return). The other 2 are location 1 below. Stitching vias change no void, since GND vias have
no hole in a GND plane. With the 591 still-reserved vias added on a scratch copy,
no PSRAM track gained a no-copper sample. Those tracks then run on webs of about
0.25 mm between holes; that is continuous copper, not a modelled return path.

**U1 ground fanout and local repairs transferred.** All **141 of 141 U1 GND balls**
reach the main piece of In1, In4 and In6, 127 of them added here with a 0.2 mm F.Cu
stub (0.707 mm) to a through via on the half-ball lattice. Every one used its tested
reserved site, so no ball is unresolved and the ball-row lanes stay open. 126 of
the 127 got a new via; B15's reserved site at (210.7, 158.34) already held a GND via,
so its stub lands on that one.

- **U2:** tented GND via at (179.9, 156.84), under the body, on all three planes.
  `PSRAM0_IO3_MEM` at (179.60, 157.39) now has a GND via 0.63 mm away. Copper gap to
  pin 6, and so to that pad's mask and paste openings, is at least 0.20 mm. The exported F.Mask
  and F.Paste draw nothing at the via; with front tenting switched off on a scratch
  copy, the same check does find a mask opening there. The board's tenting setting is
  unchanged.
- **+1V8_IO repair at (198.86, 143.27):** the three vias are now (198.81, 142.71),
  (199.7, 143.34) and (198.79, 143.74), each to its old supply lane. They sit 0.99–
  1.09 mm apart and 0.96 mm from the nearest reserved neighbour, `BUS5V0_IO5` at
  (199.7, 142.34). `PSRAM2_SCK` and `PSRAM2_CE_B` are untouched and now run over copper:
  no-copper samples in that window went from 67 to 0 of 1980 on each. Merged foreign
  crossings went from 2 to 0. Power copper: 3 vias and 4 attached tracks changed, one
  0.3 mm stub removed, and a 0.22 mm B.Cu end and a 0.4 mm F.Cu tie added. Three vias and
  all lane widths are kept. A DC solve moves one ball, U1.V20, from 9.3 to
  9.4 mV at 0.308 A; the worst drops stay 9.5 mV at 0.308 A and 43.1 mV at 1.508 A.
- **Reserved sites:** the 465 vias and 469 stubs still reserved were added to a scratch
  copy, before and after this work. DRC gave the same 54 items both times, so this
  chunk adds no conflict. Those items need attention when that routing is done: 51
  SDRAM and PHY reserved stubs drawn at 0.1 mm against a 0.125 mm minimum; a `+2V5` stub
  at (203.3, 172.32) 0.133 mm from the GND site at (202.95, 171.19); and two near-
  duplicate site pairs, `+3V3` (197.7, 143.24)/(197.75, 143.19) and GND (196.15, 147.19)/
  (196.2, 147.14). No PSRAM track gained a no-copper sample on that scratch copy.

**Unresolved location:** (184.95, 143.84), `PSRAM2_IO1_MEM`, left unchanged as agreed.
Nearest GND via 2.15 mm (U4 pin 4). With the reservations kept, the raster finds no
clear site closer, even inside courtyards. It is now the only one of the 50 reference-changing vias beyond 2.0 mm.

Each GND plane is one piece; `+3V3` and `+1V0` keep one piece each, losing 23.6 and
31.7 mm2 of fill. A fresh refill of this board reproduces it byte for byte. Evidence:
`~/freyja-review/u1-gnd-2026-11-03/`.

**SDRAM block routed and transferred; timing assessed below at 100 MHz.** The netlist matched the expected scope: 39 balls
to U32 plus R151, R152 and R153. All 82 pads on 40 nets connect, including both pull
branches and R151 between `SDRAM_CLK` and `SDRAM_CLK_MEM`. U32's 7 `+3V3` pins and 7 GND
pins reach their planes, and both pads of C250–C257 do too. All tracks are 0.125 mm; no
reservation stub was imported, and each reserved site was checked against actual copper.
No serpentine, no tuning.

R151 moved from (235.62, 147.40) to (232.0, 153.19), east of L9, so the clock takes one
direct path: 14.1 mm from ball to R151 (In2, 2 vias), then 29.4 mm on F.Cu to pin 38 with
no via. That is the only footprint moved. Accepted copper is byte-identical; added are
619 tracks and 108 vias, including 5 stitching vias. Board: 1449 tracks, 446 vias, ratsnest
1352 to 1278, DRC 0 errors, 0 parity issues, the same 334 warnings. Each GND plane is one
piece; `+3V3` and `+1V0` keep one piece each. U1 GND 141 of 141, PSRAM 120 of 120,
`+1V8_IO` 40 of 40, differential corridors identical. A fresh refill reproduces the board
byte for byte.

Layout choices that decide later work:

- **Bank 14 is at U1's far west, so address lanes are long (47.6–89.5 mm).** Accepted PSRAM
  lanes close In2 above y 147.84, In5 above y 144.89 and B.Cu at rows 145.89 and 146.79, and
  accepted LINK vias close columns 202.2 and 203.2 at the south edge. Fanouts were reworked
  around these. A7 is the one net with no direct exit: it has a third via at (199.7, 145.34).
- **A5, A6 and A7 pass south of U32 and reach their pins from the east (74.5–89.5 mm).** They
  leave the ball field in the reverse of their pin order on one layer. This is the avoidable
  part of the spread only if those balls or the accepted PSRAM lanes change.
- **F.Cu under U32's body:** two pull branches, pin 19 to R152 and pin 37 to R153, with no
  via. No via was placed under U32.
- **Pin vias are staggered,** 0.95 mm or more from any other net's via, so their clearance
  holes do not merge. No SDRAM track crosses a merged hole; 127 of 127 void crossings are a
  track leaving its own via. PSRAM continuity is unchanged.

Return paths: of 79 SDRAM vias, 31 keep their reference (F.Cu↔In2) and 48 change In1↔In6.
41 of the 48 have a GND via within 2.0 mm, a figure chosen here. The other 7 have no free site
outside courtyards and the ball field within 2.0 mm: `A7` (199.7, 145.34), 3.11 mm; `A2`
(199.7, 146.34), 3.0; `A5` (200.7, 146.34), 2.83; `CS_N` (223.25, 178.09), 2.83; `A6` (200.7,
145.34), `A11` (201.7, 146.34) and `BA0` (203.7, 146.34), 2.24.

Room kept: the 416 vias and 430 stubs still reserved give the same 15 DRC items on a scratch
copy before and after: 12 RGMII stubs at 0.1 mm against 0.125 mm, the `+2V5` stub and the two
near-duplicate pairs listed above. All four HDMI pairs and the LINK corridor still have a
B.Cu path with 0.31 mm clearance on that scratch copy; this is an access estimate, not a route.

**SDRAM timing assessed for 100 MHz, CL3: keep the routing, change the clock scheme and bus drive.**
The target is the owner's. No board measurement exists; this is worst-case analysis on the
committed copper (`8cbbd79`), with Vivado 2026.1 STA on `xc7a100tfgg676-2`. No exceptions except one
justified multicycle below. The contract, fixture, constraints, calculation scripts and model
provenance are in [`gateware/sdram100/`](gateware/sdram100/README.md), separate from the allocation gate.

The scheme: all registers in the IOBs on one 100 MHz clock `c0`. `SDRAM_CLK` comes from an ODDR on
a second MMCM output at 270 degrees. Read data is captured in the IOB on `c0`, and the controller
accepts c0 edge 4 after the edge launching READ (CL + 1). Bus at 8 mA slow; clock stays 12 mA
fast through R151. Worst margins, ns, slow and fast corners:

| Group | Setup | Hold | Limit, ns | Now | Offenders |
|---|---:|---:|---|---|---|
| A, BA, command, CKE, DQM to U32 | +2.70 (A7) | +1.44 (LDQM) | settle − clock ≤ +4.22; leave − clock ≥ −1.77 | +1.58; −0.36 | none |
| Same, note 8 applied in full | +1.57 (A7) | +0.79 (A7) | | | none |
| Write DQ to U32 | +3.08 (DQ8) | +1.41 (DQ2) | settle − clock ≤ +4.26; leave − clock ≥ −1.77 | +1.20; −0.39 | none |
| Same, note 8 applied in full | +2.42 (DQ8) | +0.92 (DQ8) | | | none |
| Read DQ at FPGA | +1.30 (DQ8) | +1.78 (DQ2) | clock + DQ board delay ≤ 2.17 | 0.60–0.89 | none |

"Settle" and "leave" are per-net flight times from the IBIS simulation: the last crossing into, and
the first departure from, a valid input level (VIH 2.0 V, VIL 0.8 V). Both are stricter than the
datasheet's 1.4 V reference. Note 8 adds `(tr + tf)/2 − 1` ns to setup and hold because 8 mA edges
reach 2.35 ns in the slow corner; it is counted on top of those stricter figures, so the rows are
deliberately pessimistic.

These limits replace "a few mm at 166 MHz". **Equal lengths are not required at 100 MHz.** A7, at
89.5 mm and 46 mm longer than the clock, has 2.70 ns of setup margin left, equal to about 387 mm of
In5. Do not add copper to match A7. Above 100 MHz the limits do not apply and the fixture must be
rerun.

What fails, and why it matters:

- **Capture on the default STA edge fails:** read setup −1.20 ns (DQ8) at 180 degrees and −8.70 ns
  at 270, because the default edge is never more than one period after launch. The window is
  3.08 ns wide, so this is a capture-edge choice, not a board fault. The fix is one more period
  and a 90 degree offset, constrained by `set_multicycle_path -setup 2` from `sdram_clk` to
  `dq_i_reg[*]`. The justification is physical: the flop samples every edge and the read-latency
  counter accepts only that one.
- **The exception was checked against a four-word read before saving it; no problem found.** READ
  launched at c0 edge 0, sampled at U32 T0 (7.5 ns). Words launched by T2–T5 (27.5–57.5 ns) are
  accepted at c0 edges 4–7 (40–70 ns), so every capture gets the intended word. On the routed design
  setup is launch 7.5 to capture 20, requirement 12.5 ns: that word against its accept edge. Hold is
  launch 7.5 to capture 10, requirement 2.5 ns: the next word against that same edge. Scope: 16 paths,
  DQ ports to `dq_i_reg[*]` only, no pad-loopback path; narrowing it from the clock-to-clock form
  changed no slack. Exactly one edge works: `-setup 3` gives hold −8.22 ns. `-hold` is deliberately
  absent: `-hold 1` moves the hold launch to 17.5 ns, slack +11.78, checking nothing real. The full
  edge table is in the profile.
- **Forwarded clock at 180 degrees is too early at 12 mA:** A7 setup −1.97 ns.
- **12 mA on the bus passes timing thinly and overshoots.** With the same scheme: A7 setup +0.53,
  hold +0.75. Simulated at U32 with no input clamps modelled, 31 nets re-cross a threshold after
  first crossing it, 8 exceed 4.6 V and 18 go below −1.5 V, against datasheet limits of VDD + 0.5 V
  absolute (4.6 V maximum) and −1.5 V for pulses up to 5 ns. A7 settles only at 4.65 ns. At 8 mA:
  no threshold re-crossing, 3.66 V peak, bus −0.98 V, settled by 2.01 ns. The clock, unchanged at
  12 mA fast through R151, has no re-crossing either but reaches 4.09 V and −1.04 V in the fast corner.

**DQ turnaround** (section 10.2 of the datasheet: tLZ from edge CL−1, tHZ from the edge after the
last launching edge). Let `e` be the c0 edge before the U32 edge launching the last read word; that
word is accepted at c0 `e+2`. FPGA drivers on at `e+2` overlap U32 by up to 3.22 ns. At `e+3` the
margin is +6.78 ns (now taken across all 16 DQ, not DQ0 alone); for BL4, that is c0 edge 8. On write to read, releasing with the READ or one cycle after leaves at least
17.31 ns before U32 can drive, satisfying section 7.10's one clear cycle; two cycles after does not.
Release no earlier than one c0 edge after the last write word: STA hold there is +0.059 ns on the
disable arc (DQ0), counting a line that changes at release, though it actually floats. Section 7.8
still applies: mask with DQM when a READ would drive during the first two write clocks.

**Layer delays and impedance at 0.125 mm**, from a 2D field solve of the published stackup. The
solver gives 100.3 ohm for the saved JLC pair (JLC 100.0).

| Layer | Z0, ohm | Delay, ps/mm | Spread |
|---|---:|---:|---|
| F.Cu, B.Cu | 48.4 | 5.88 | width ±0.0125 mm 46.1–51.0 ohm; no mask 51.8 ohm, 5.50 ps/mm; adjacent lane at 0.3 mm 5.74–6.00 ps/mm |
| In2, In5 | 49.1 | 6.97 | width ±0.0125 mm 46.6–51.9 ohm; core ±0.01 mm 46.7–51.2; Dk ±5 % 6.79–7.14 ps/mm; In3 absent 50.3 ohm |

0.125 mm is therefore also about 50 ohm on the inner layers. The worry that it was only an
outer-layer estimate is settled by calculation, not by a fabricator's result. Adjacent inner lanes
at 0.3 mm pitch are 43.8 ohm odd and 54.1 ohm even; their crosstalk is not assessed.

**Verified by tool on the committed copper:** routed lengths and sections, STA paths and clock
uncertainty (0.208 ns: 0.071 system, 0.162 discrete jitter, 0.120 MMCM phase error), per-ball package
delay from Vivado (58–160 ps across the 39 SDRAM balls), AMD IBIS drivers, all 70 fixture registers in the
IOBs, `check_timing` clean.

**Assumptions, not verified:** X4's jitter, 200 ps peak to peak, as no datasheet for C717684 is in the
repository. U32 output behaviour into the real line, covered by a 0.3 ns allowance, because no U32
IBIS is available; this allowance also covers the 1.65 V against 1.4 V threshold difference. U32
input clamps, so the overshoot figures are upper estimates. Not assessed: crosstalk,
simultaneous-switching noise, read-direction ringing, and the -6 grade's 0–70 °C ambient against the
FPGA's industrial grade. Nothing has been measured on hardware.

Not changed: `ref/freya.xdc`, `tools/alloc.py`, the allocation gate, SDRAM copper. The 8 mA drive and
clock scheme apply through the separate profile, with RTL that makes the phase; an XDC waveform alone
is not enough. Reproduced from the repository: every command and read slack, and all 108 delay lines,
match the review fixture; `flight.py` matches its stored data exactly.

**`check_connector_rework.py`:** the failure predates this routing. At `3f76447`, `bde689c` and
`8cbbd79` the only reference difference is H1–H4 on the PCB and not in the netlist (board-only
mounting holes); nothing is missing from the PCB. The SDRAM chunk did not introduce it. Past that
assertion, in a scratch copy only, the checker next stops on its own stale rule forbidding `FB1`:
the live FB1 is the current 120 ohm bead, present at both commits. Neither was changed here. Evidence:
`~/freyja-review/sdram-timing-2026-11-03/`.

<details><summary>Per-signal length (mm), layers and vias, ball to pin; CLK is ball to R151 and CLK_MEM is R151 to pin 38</summary>

| Signal | Length | By layer | Vias |
|---|---:|---|---:|
| DQ0 | 13.5 | F.Cu 2.7 + In2 10.8 | 2 |
| DQ1 | 13.5 | F.Cu 2.7 + In2 10.8 | 2 |
| DQ2 | 21.1 | F.Cu 3.3 + In2 17.8 | 2 |
| DQ3 | 21.9 | F.Cu 2.7 + In5 19.2 | 2 |
| DQ4 | 22.1 | F.Cu 3.3 + In2 18.9 | 2 |
| DQ5 | 21.7 | F.Cu 2.7 + In5 19.0 | 2 |
| DQ6 | 22.7 | F.Cu 3.3 + In2 19.4 | 2 |
| DQ7 | 23.8 | F.Cu 2.7 + In5 21.1 | 2 |
| DQ8 | 41.3 | B.Cu 38.8 + F.Cu 2.6 | 2 |
| DQ9 | 34.0 | F.Cu 2.6 + In2 31.4 | 2 |
| DQ10 | 38.7 | B.Cu 36.7 + F.Cu 2.0 | 2 |
| DQ11 | 34.5 | B.Cu 32.5 + F.Cu 2.0 | 2 |
| DQ12 | 31.6 | F.Cu 2.6 + In2 29.0 | 2 |
| DQ13 | 30.0 | F.Cu 2.6 + In5 27.4 | 2 |
| DQ14 | 33.0 | F.Cu 2.0 + In2 31.0 | 2 |
| DQ15 | 30.1 | F.Cu 2.0 + In5 28.1 | 2 |
| LDQM | 28.4 | F.Cu 2.7 + In5 25.7 | 2 |
| UDQM | 34.7 | F.Cu 2.0 + In5 32.7 | 2 |
| A0 | 47.6 | F.Cu 3.3 + In2 44.4 | 2 |
| A1 | 56.3 | F.Cu 11.4 + In5 44.9 | 2 |
| A2 | 59.2 | F.Cu 11.6 + In5 47.6 | 2 |
| A3 | 59.3 | F.Cu 10.8 + In5 48.4 | 2 |
| A4 | 63.2 | F.Cu 2.0 + In2 61.2 | 2 |
| A5 | 74.5 | F.Cu 2.6 + In5 71.9 | 2 |
| A6 | 83.6 | F.Cu 2.0 + In5 81.6 | 2 |
| A7 | 89.5 | F.Cu 2.6 + In2 1.4 + In5 85.5 | 3 |
| A8 | 59.5 | F.Cu 2.0 + In2 57.5 | 2 |
| A9 | 63.6 | F.Cu 2.6 + In5 61.0 | 2 |
| A10 | 51.2 | F.Cu 13.1 + In5 38.2 | 2 |
| A11 | 64.5 | F.Cu 4.0 + In5 60.5 | 2 |
| A12 | 61.0 | F.Cu 2.6 + In5 58.4 | 2 |
| BA0 | 49.4 | F.Cu 10.9 + In5 38.4 | 2 |
| BA1 | 51.2 | F.Cu 13.1 + In5 38.0 | 2 |
| CKE | 52.6 | F.Cu 13.0 + In2 39.6 | 2 |
| CS_N | 37.4 | F.Cu 12.6 + In5 24.7 | 2 |
| RAS_N | 25.6 | F.Cu 3.3 + In5 22.3 | 2 |
| CAS_N | 27.8 | F.Cu 2.7 + In2 25.1 | 2 |
| WE_N | 25.9 | F.Cu 3.3 + In2 22.7 | 2 |
| CLK | 14.1 | F.Cu 1.7 + In2 12.4 | 2 |
| CLK_MEM | 29.4 | F.Cu 29.4 | 0 |

</details>

**Four HDMI high-speed pairs routed and transferred.** `HDMI_CLK_P/N` and `HDMI_D0`–`D2_P/N`: all
24 pads on 8 nets connect, U1 ball to U31 pin to J73 pad; KiCad's own connectivity, with only these
nets loaded, reports 0 unconnected. References checked against the netlist: J73, U31. Rules,
allocation, footprints and all accepted copper are unchanged. The eight corridor ends are closed.

| Pair | Length, mm (P, N) | Skew, mm | Vias per net | Uncoupled, mm (new part) |
|---|---|---:|---|---|
| CLK | 72.69, 72.69 | 0.001 | 2 | 15.2 (13.9) |
| D0 | 67.33, 67.33 | 0.001 | 2 | 12.7 (10.4) |
| D1 | 68.75, 68.75 | 0.000 | 2 | 13.7 (10.0) |
| D2 | 81.54, 81.54 | 0.000 | 2 | 12.4 (10.0) |

Lengths are track length from the U1 ball centre to the J73 pad centre, the same anchors on all 16 ends, and
exclude U1's package. Each includes 0.945 mm of track inside the J73 pad, counted in the uncoupled figures. Pair-to-pair spread is 14.2 mm; no
rule covers it and timing is not assessed. Geometry: 0.099 mm, 0.200 mm coupled gap, F.Cu and B.Cu
only, 0.31 mm to foreign copper from tracks, except the J73 entries below. Each net has its one new through via
beside U31, on the body side of the pin: J73 to U31 is F.Cu with no via, and the line runs through the
pin, per SLLSE96F 10.1. New uncoupled length is about 4 mm of F.Cu fan-out per net (U31 pitch 0.65 mm
to J73's 1.0 mm P-to-N with a shield pad between), via tapers, the corridors' staggered ends, and the
bumps below.

Topology, forced by order rather than chosen: on B.Cu, D2 is west of the other pairs and CLK has P west
of N, while U31 has CLK at the west end, D2 at the east end and N west of P in every pair. All four
stay planar with no extra via. D0 and D1 land on their vias from the north, CLK loops under the via row
and lands from the south, and D2 runs under CLK and all the vias and comes back from the east. CLK, D0
and D1 pass J8's east end; D2 passes its west end. The corridors end staggered and these turns add more,
so length bumps of about 0.3 mm height sit on one lane of each pair: 1.7 mm total height on D0_N and on
D1_N near the corridors, 2.5 mm on CLK_N and 0.9 mm on D2_P just before the loop.

**J73 pad entries: ordinary pad-centre tracks under explicit local rules.** Every entry is now a straight
0.099 mm track from y 214.25 to its pad's centre at y 215.305, exactly vertical and on the pad's x. The 0.4 µm
leans and `HDMI_D2_P`'s 0.11 mm in-pad extension are gone, and its off-centre entry at x 240.71 is back on the pad
at 240.65. Two rules in `tools/gen_pcb.py` allow what J73's pitch forces, for a track on an `HDMI_CLK_*` or
`HDMI_D0`–`D2_*` net, on F.Cu, wholly inside the rule area `J73_TMDS_ENTRY` (x 234.95–240.85, y 214.19–215.40):

- **Foreign pads, `HDMI TMDS entry to J73 pads`, 0.300 mm**, against J73 pads only. On 0.5 mm pitch, a pad 0.3 mm wide
  and a track on the pad centre: 0.5 − 0.15 − 0.0495 = 0.3005 mm measured. The 0.31 mm rule cannot be met.
- **Pair gap, `HDMI TMDS entry pair gap at J73`, 0.200–0.901 mm.** P and N pads are 2 × 0.5 = 1.0 mm apart with a GND
  pad between, so tracks on the pad centres have 1.0 − 0.099 = 0.901 mm, the upper limit. The lower limit is the
  normal coupled gap. All eight entries sit at 0.901 mm. The normal rule, exactly 0.200 mm, still governs everything
  outside the area, including the rest of these tracks.

Lengths are now measured between pad centres, so nothing inside a pad can move skew. `HDMI_D2_P` lost 0.147 mm to the
cleanup and made it up outside the pad: its F.Cu fan-out keeps its old direction past U31 pin 24 to (239.75, 213.369),
then runs through (240.424, 213.58) to (240.65, 214.25), 0.154 mm longer than the straight line. No other pair
needed any change. Skew stays
at most 0.001 mm on all four pairs.

Tested on scratch copies, DRC with the generated rules:

| Case | Result |
|---|---|
| Entries as built, exactly parallel | no errors, no warning changed |
| Pair in the area at 0.200 and 0.901 mm | passes |
| Pair in the area at 0.190 and 0.902 mm; a real entry moved 1 µm | fails, gap |
| Pair outside the area at 0.200 mm | passes |
| Pair outside the area at 0.250 and 0.901 mm | fails, gap max 0.200 |
| LINK pair in the area at 0.901 mm | fails, gap max 0.200 |
| Entry at 0.2994 mm to the next pad | fails, `HDMI TMDS entry`, min 0.300 |
| HDMI stub at 0.3005 mm running out of the area | fails, 0.31 mm rule |
| LINK track at 0.305 mm to a J73 pad, area enlarged for the test | fails, 0.31 mm rule; the same spot on an HDMI net has no clearance error |
| GND track in the area, 0.305 mm from an entry; HDMI track 0.305 mm from a U31 pad | fails, 0.31 mm rule |
| Rule area deleted | fails: 8 clearance, 4 gap |
| `gen_pcb.py --rules-only` over the routed copy | no errors, same `.kicad_dru` |

KiCad names `100R outer geometry` in the gap message even when it applies the local 0.901 mm limit; the value is the
local rule's. It also compares a pair's segments only among tracks governed by the same rule, so a track inside the
area is not checked for gap against one outside it. The generator also reformats the stackup block and reorders net
classes in `.kicad_pro`, with the same class contents; neither is part of this change, so the generated `.kicad_dru`
was copied to the live tree. Changed copper: seven entry tracks lengthened, and four `HDMI_D2_P` segments replaced by
four. Every other track, via, footprint and plane fill is byte-identical, 0 DRC errors, 0 parity issues.

Left as is, outside the J73 scope: at U31 the F.Cu stubs from the 0.65 mm via row reach each pin at about 1.9 degrees,
through a 0.02 mm via offset, so they do not fire the pair-gap rule at 0.551 mm. This is ordinary copper, not a
sub-micron lean, but it does exist because of that rule. A second local rule at U31 could replace it if wanted.

**Returns.** New GND vias: U31 pins 14 and 19 at the via row, pin 6 tented under the body, one stitching
via at (239.0, 208.95), and one for each of J73's five SMD GND pads at y 216.75, under the connector
body, tented. All reach In1, In4 and In6; U31 3 of 3, J73 5 of 5 plus 4 of 4 shell pads. Each of the 8
new HDMI vias has a GND via within 0.67–1.85 mm (within 2.05 mm at the existing U1 end). On the refilled
planes all 32 void crossings are a track leaving its own via. Via pitch at U31's 0.65 mm pads merges the
clearance holes into two slots on In1 and In6, x 233.48–236.12 and x 236.72–239.38 at y 210.32–211.08,
1.68 mm2 each. No plane splits: each GND plane is one piece, 3.4 mm2 smaller. The return current is
not modelled.

**Checks on the live board:** refilled DRC 0 errors, 0 parity; warnings unchanged except `track_dangling`
24 to 16, all LINK. Tracks 1449 to 1676, vias 446 to 463, ratsnest 1278 to 1254. The pad-entry change
has since been corrected as described above; a fresh refill reproduces the file byte for byte. SDRAM 82 of 82, PSRAM 120 of 120, `+1V8_IO` 40 of 40, U1 GND
141 of 141 still connect. On the stress copy the error count is unchanged and none involves HDMI; each
LINK pair still has a B.Cu access path to its connector, an estimate rather than a route. `gate.py
--strict` passes; `check_connector_rework.py` stops at the same pre-existing H1–H4 assertion.

**Not established: HDMI electrical compliance remains unverified.** Routing and rule checks do not
establish it. Impedance through the vias, pad entries, bumps and U31's pad capacitance is not modelled; no eye, return-loss or inter-pair timing
result exists. Not routed: HDMI management signals, `HDMI_5V`, `+5V` and `+3V3` at U31, U31's supply
capacitors, R150. F.Cu around U31's west end and In2/In5 look open for those, but that was not route
tested. KiCad's project manager was running at transfer, with no lock on the PCB: reopen the board from
disk. Evidence: `~/freyja-review/hdmi-2026-11-03/`, `~/freyja-review/j73-entry-2026-11-03/`.

**LINK P and LINK Q routed and transferred.** *Route superseded by the second pass below; this records how the first pass stood.* All sixteen `LINK_*` nets run from the corridors through their
ESD arrays to their jacks: **48 of 48 pads on 16 nets**, ball, D20–D23, J71 or J72. References and contact pairing
checked against the netlist and `ref/link-ports.md`, P/N polarity on every contact and ESD pin. KiCad's own
connectivity, with only these nets loaded, reports 0 unconnected. All sixteen corridor ends are closed and no
`track_dangling` warning is left on the board. No external termination: receivers use `DIFF_TERM`.

| Pair | Length, mm (P, N) | Track skew, mm | Vias per net (P, N) | Uncoupled, mm (P, N) |
|---|---|---:|---|---|
| P_TXC | 116.61, 116.61 | +0.00 | 2, 2 | 25.9, 25.9 |
| P_TXD | 106.76, 105.76 | +1.00 | 2, 3 | 25.6, 24.6 |
| P_RXC | 106.66, 107.66 | −1.00 | 3, 2 | 22.1, 23.0 |
| P_RXD | 101.44, 101.44 | −0.00 | 2, 2 | 16.5, 16.5 |
| Q_TXC | 70.92, 69.92 | +1.00 | 3, 4 | 28.6, 27.5 |
| Q_TXD | 76.85, 76.85 | +0.00 | 3, 3 | 26.3, 26.2 |
| Q_RXC | 78.08, 76.09 | +2.00 | 2, 4 | 22.8, 20.8 |
| Q_RXD | 77.14, 76.14 | +1.00 | 2, 3 | 26.3, 25.3 |

Lengths are track length from the U1 ball centre to the jack contact centre, including existing corridor copper;
vias include the existing escape via. **Superseded by the stackup correction below:** KiCad counted each via as 1.0 mm only
because the PCB had lost 0.589 mm of dielectric, so the 1.0 and 2.0 mm track differences above matched a wrong figure and "KiCad
skew at most 0.003 mm on every pair" no longer holds. Five of these pairs now fail the 0.1 mm limit.
There are no ESD branch stubs: every line runs through its ESD pad, and each net's track total equals its path.
Uncoupled counts every part of a lane without its partner on the same layer at 0.299 mm, including length made up.

**Why the uncoupled figures are this high.** Three fixed things force it, and no rule was relaxed for any of them:

- **Contact pads, the exact conflict.** Neighbouring J71/J72 contact pads in a row are 2.04 mm apart and 1.524 mm across,
  0.516 mm of gap. A 0.099 mm track in that gap has 0.2085 mm a side against the 0.31 mm rule, on every layer, so a
  south-row contact cannot be reached between two north-row contacts. Contacts 3 and 5 of both jacks are reached from
  the south, round the jack end. So are contacts 1 and 2 of J71 and 7 and 8 of J72; contact 7 of J71 comes round
  its west end. This splits every 3-6 and 4-5 pair by layer for the length of the jack.
- **ESD order against contact order.** D20–D23 run TXC, TXD, RXC, RXD west to east on J71's side and RXC, RXD, TXC, TXD on
  J72's, nearly the reverse of the contact order, and D20 sits about 10 mm west of J71's TXC contacts.
- **P and N pads on opposite sides of each array,** 2.7 mm apart in one column, so one lane of a pair must change layer
  beside the part.

Length is made up on the short net in real copper outside pads: triangles on the coupled B.Cu run of `P_TXC` and
`Q_TXD`, and serpentines on the uncoupled legs of the other six. Owner decisions that could reduce this: a local rule at
J71/J72 contact pads, 0.2085 mm, would allow direct entry to contacts 3 and 5; or swapping or moving D20–D23. Neither
was done. The HDMI exception was not broadened: a LINK pair in the J73 area still fails, tested above.

**Topology.** Outer layers only. LINK P runs on B.Cu, its four pairs in one row bundle north of the ESD row at 0.31 mm
between pairs, south of MK76 and between J19 and H4. LINK Q crosses that bundle on F.Cu: Q_RXC and Q_RXD change layer near
(205, 187), Q_TXC and Q_TXD near (198, 200). Two reserved sites shaped the corridors: `Q_RXD` jogs east round GND at
(206.85, 176.19), and `Q_TXC` passes west of the existing vias at (200.75, 177.19) and (200.75, 179.39).

**Grounds and stitching.** D20–D23 pin 2 reach In1, In4 and In6 through 4 vias, 4 of 4; J71 and J72 shells 4 of 4. 26 new LINK
vias, 11 new stitching vias: 25 of the 26 have a GND via or through GND pad within 2.0 mm, a figure chosen here;
`LINK_Q_TXD_N` at (199.65, 200.6) has 2.23 mm; the search found no free site within 2.0 mm of it. On the refilled planes,
68 void crossings are a track leaving its own via and 32 are that same case where a P/N via pair's clearance holes merge, at 8
locations, 5 of them new, 0.83–0.89 mm2 each. Every crossing ends at its own via; none is under a foreign via. The detour probe does not
apply to those 32, since the track ends inside the hole; the return current through these transitions is not modelled.
Each GND plane stays one piece, 11.5 mm2 smaller; `+3V3` and `+1V0` keep one piece each.

**Checks on the live board:** refilled DRC 0 errors, 0 parity; warnings as before except `track_dangling` 16 to 0. Tracks 1676 to
2136, vias 463 to 504, ratsnest 1254 to 1218. No footprint moved; every accepted track and via is byte-identical,
LINK corridors kept item for item, and a fresh refill reproduces the file byte for byte. HDMI 24 of 24, SDRAM 82 of 82,
PSRAM 120 of 120, `+1V8_IO` 40 of 40, U1 GND 141 of 141 still connect. `gate.py --strict` passes;
`check_connector_rework.py` stops at the same pre-existing H1–H4 assertion.

KiCad fires the gap rule on any exactly parallel P/N overlap on one layer, so uncoupled lanes beside their partner are ordinary
slanted legs. Within 1.5 mm of the partner, and overlapping by more than 0.05 mm, the smallest angle is 3.5 degrees. Anything
closer in angle is exactly parallel at the 0.200 mm gap, or at least 2 mm from the partner. No sub-degree tilt is used.

**Open points.**

- **Reserved site blocked.** Closed: C301's reserved `+1V0` via moves to (211.5, 174.5); see the second pass below.
- **Via length model.** Closed; see the stackup correction below.
- **Clock to data within a lane is not matched** and no rule covers it: track totals TXC against TXD 116.6/106.8 on P and 70.9/76.9 on
  Q; RXC against RXD 106.7/101.4 on P and 78.1/77.1 on Q. Calculated by direction below. A real link adds the cable.

**Not established: cable performance and electrical compliance.** These checks show copper connects and meets the rules. Impedance
through the split sections, vias, ESD capacitance and serpentines is not modelled; no eye, return-loss or link test exists. Evidence:
`~/freyja-review/link-2026-11-03/`.

**Stackup representation corrected (2026-11-04).** No track, via, footprint, zone outline or fill changed. Sixteen lines were
added to the PCB's stackup block; five LINK pairs now fail the existing skew rule, which is a measurement correction and not a
geometry regression.

*Root cause: missing data in the board, not a counting or parser error in the sum.* `tools/gen_pcb.py` wrote the extra sublayers of
dielectrics 3 and 5 as `(addsublayer)` since `3e44271`. KiCad's word is the bare `addsublayer`. The parenthesised form loads without any
message and folds all three sublayers into one holding the last values: on a scratch copy with 0.1111/0.0222/0.3333 mm, pcbnew kept one
sublayer of 0.3333 mm, while the bare form kept all three. The last sublayer here is 0.2104 mm, like the first, so the result looked
plausible. Every pcbnew save then wrote the reduced block. `gen_pcb.py` and `ref/jlc08161h-1080a-stackup.json` always agreed on intent.

| mm | Intended (JLC template) | Loaded and saved before | Loaded and saved now |
|---|---:|---:|---:|
| Copper | 0.1612 | 0.1612 | 0.1612 |
| Dielectric | 1.4624 | 0.8736 | 1.4624 |
| **Copper plus dielectric** | **1.6236** | **1.0348** | **1.6236** |
| Solder mask, two faces, not in the template | 0.0508 | 0.0508 | 0.0508 |
| F.Cu to B.Cu mid-plane, KiCad's via length | 1.5886 | 0.9998 | 1.5886 |

Mid-plane depths from F.Cu: In1 0.1015, In2 0.2167, In3 0.7367, In4 0.8519, In5 1.3719, In6 1.4871, B.Cu 1.5886 mm. The general
thickness field stays 1.6 mm, the nominal order thickness. It was not changed, and it does not set via length: DRC measured 1.5886 mm with it at 1.6.
The mask's Dk 3.8 in the generator does not survive a pcbnew save, before or after this fix. It stays in the impedance record.

*Durable fix.* The generator now writes the bare word. New `tools/check_stackup.py`, run by `gate.py` in the electrical verdict, loads
the board in pcbnew, saves a temporary copy and compares each sublayer's thickness, material, Dk and loss tangent with the template, plus the
generator's own text. It fails on the old board and on the old generator text. Python cannot read pcbnew's stackup directly, so the check
reads the saved copy. Round trip: two pcbnew load and save cycles are byte-identical; the Gerber job file, a separate reader, lists all 3/3 sublayers
and 1.6236 mm; `gen_pcb.py --rules-only` on a scratch tree, then a save, reproduces the board byte for byte, with the same `.kicad_dru`.

*Intra-pair skew, P minus N, mm unless marked.* Barrels are counted between the layers really entered and left; every signal via here is F.Cu
to B.Cu, and all tracks are on the main path with no stubs. "Plus jack barrel" adds 1.5886 mm where a line enters a through-hole contact on B.Cu,
because the jack body is on F.Cu; KiCad cannot see this. Delay is calculated, not measured. The KiCad figures match DRC with the limit forced to 0 on a scratch copy.

| Pair | Vias P, N | Exit P, N | Track only | KiCad before | KiCad now | Plus jack barrel | Delay, ps (vias; plus jack) | U1 package, ps | DRC 0.1 mm |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| HDMI_CLK | 2, 2 | F, F | −0.001 | −0.001 | −0.001 | −0.001 | −0.01; −0.01 | +4.40 | pass |
| HDMI_D0 | 2, 2 | F, F | −0.001 | −0.001 | −0.001 | −0.001 | 0.00; 0.00 | −9.84 | pass |
| HDMI_D1 | 2, 2 | F, F | −0.001 | −0.001 | −0.001 | −0.001 | 0.00; 0.00 | −3.79 | pass |
| HDMI_D2 | 2, 2 | F, F | +0.001 | +0.001 | +0.001 | +0.001 | 0.00; 0.00 | −29.09 | pass |
| P_TXC | 2, 2 | F, F | +0.002 | +0.002 | +0.002 | +0.002 | +0.01; +0.01 | −2.32 | pass |
| P_TXD | 2, 3 | F, B | +1.000 | 0.000 | **−0.588** | −2.177 | −5.21; −16.28 | −5.91 | **fail** |
| P_RXC | 3, 2 | B, F | −0.999 | +0.001 | **+0.589** | +2.178 | +5.21; +16.29 | −0.93 | **fail** |
| P_RXD | 2, 2 | F, F | 0.000 | 0.000 | 0.000 | 0.000 | 0.00; 0.00 | −2.28 | pass |
| Q_TXC | 3, 4 | B, F | +1.000 | 0.000 | **−0.589** | +1.000 | −5.21; +5.87 | −4.65 | **fail** |
| Q_TXD | 3, 3 | B, B | +0.002 | +0.002 | +0.002 | +0.002 | +0.02; +0.02 | +0.77 | pass |
| Q_RXC | 2, 4 | F, F | +1.997 | −0.002 | **−1.180** | −1.180 | −10.43; −10.43 | −0.05 | **fail** |
| Q_RXD | 2, 3 | F, B | +1.000 | +0.001 | **−0.588** | −2.177 | −5.21; −16.28 | −10.19 | **fail** |

*Clock to data on LINK, clock minus data, mean of P and N.* A positive value means the clock arrives later. KiCad's figure is a length with barrels counted
as track; the delay is length converted per section. Cable, drivers and receivers are excluded, and a real P-to-Q link adds the cable's pair difference.

| Leg | KiCad before, mm | KiCad now, mm | Delay, ps (vias) | Plus jack barrel, ps | U1 package, ps | Sum, ps |
|---|---:|---:|---:|---:|---:|---:|
| P TX | +9.847 | +9.553 | +53.93 | +48.39 | +3.18 | +51.57 |
| Q RX | +0.939 | +1.233 | +7.54 | +2.00 | −21.13 | −19.13 |
| **P out, Q in** | +10.786 | +10.786 | +61.47 | +50.39 | −17.95 | **+32.44** |
| Q TX | −5.937 | −5.642 | −31.16 | −36.70 | +17.74 | −18.96 |
| P RX | +6.215 | +6.509 | +39.10 | +44.63 | +2.72 | +47.35 |
| **Q out, P in** | +0.278 | +0.867 | +7.93 | +7.93 | +20.46 | **+28.39** |

Delay model: `fieldsolve.py`, the same solver as the SDRAM profile, gives at 0.099 mm odd mode 5.737 ps/mm (99.8 ohm differential) with a coupled 0.200 mm gap
and 5.865 ps/mm for a lone line (53.6 ohm); the barrel is 6.97 ps/mm, the figure `flight.py` already uses, an assumption rather than a via solve. So one barrel is 11.07 ps,
about 1.89 mm of lone track, not the 1.59 mm KiCad counts: matching KiCad's length is not matching delay. U1 package figures are the midpoints of Vivado's `write_csv`
trace delays for the exact part. Dk spread (about ±2.5 % on delay), via excess capacitance, ESD capacitance and return paths are not included. HDMI
pair delay on the board is 410.1–491.6 ps; this correction moves all four by the same 8.2 ps.

*SDRAM profile: not affected, nothing rerun in Vivado, all results stand.* It never read KiCad's stackup. `fieldsolve.py` carries the full 0.2104 + 0.084 + 0.2104 mm
prepreg stack, and only the route's sections come from the board. Unchanged `flight.py` on the corrected board reproduces `data/flight_8.json` exactly.
Its hard-coded via depths (F–In2 0.23, F–In5 1.33, F–B 1.57 mm) are rounded, not derived from the defective block. Using the exact depths on a scratch copy moves
any settle or leave time by at most 4.3 ps and any DQ line delay by at most 0.55 ps, against read margins of +1.30/+1.78 ns. The depths and `VIA_PS` are kept as committed.

*Superseded:* commit `9c37332`'s "KiCad skew at most 0.003 mm" and "0 DRC errors"; the 1.0 mm per via in `tune.py`, and thus the length made up on P_TXD, P_RXC, Q_TXC, Q_RXC and Q_RXD;
the "1.086 mm" reading in the LINK notes. *Still valid:* HDMI skew and every HDMI, SDRAM, PSRAM and rail result; LINK connectivity, polarity and coupled geometry.

*Checks.* HEAD plus this block against HEAD: only `setup` differs, item for item, and a fresh refill reproduces the file byte for byte. DRC: 0 parity; errors 0 to 5, all `skew_out_of_range`, no other
violation added or removed, warnings identical. 2136 tracks, 504 vias, 555 footprints, 6 zones, ratsnest 1218 unchanged. HDMI 24 of 24, LINK 48 of 48, SDRAM 82 of 82, PSRAM 120 of 120,
`+1V8_IO` 40 of 40, U1 GND 141 of 141 still connect, and KiCad reports 0 unconnected on the HDMI and LINK nets alone. `gate.py --strict` passes; `check_connector_rework.py` stops at the same H1–H4 assertion.

*Working tree, not committed.* `kicad/odin.kicad_pcb` also carries the owner's uncommitted move of H4 to (174, 205), and `.kicad_prl` its own changes; both are preserved and left out of this commit.
Saved without a refill, H4 adds 4 `hole_clearance` errors against the stale GND and `+3V3` fill, so `gate.py` on the working tree counts 9 errors. On a scratch refill those 4 go away, only those four fills change, and nothing else
appears. Refill in KiCad when that move is accepted.

**Next corrections.** Done by the second pass below, which equalises via counts and entry layers instead of matching lengths to one metric. With equal barrels KiCad's length and the calculated delay now agree within each pair. Still open: U1's package P−N, not compensated in copper, and the clock-to-data budget. Evidence for this section: `~/freyja-review/stackup-2026-11-04/`.

**LINK second pass on the corrected stackup (2026-11-04).** All eight pairs now have equal via counts, the same layer sequence on P and N and the same
entry layer at the contacts, **KiCad skew 0.0000 mm on all eight with the limit forced to 0, 0 DRC errors, 0 parity**. No dummy via, and no track compensates a contact entry. Only D20–D23 moved.
The five skew errors from the stackup correction are gone, because the cause is gone. Not established: cable performance, timing, electrical compliance.

*Why these sequences.* The contacts force one layer split: 3-6 straddles 4-5 in both jacks, so those two pairs cannot enter on one layer. D20–D23 at rotation 0 have N west and P east on both channels, with
pins 3/4 upper and pins 1/6 lower, and going round the part the pads run N(3/4), P(3/4), P(1/6), N(1/6). So a 1/6 pair with no vias lies either side of the 3/4 pair: 3/4 runs under the body between the pads, and 1/6 comes in from outside. The 3/4 pairs
(TXD, RXD) leave on B to contacts 3-6 and 7-8 of their jack, and the 1/6 pairs (TXC, RXC) stay on F. So the F-entry pairs have 2 vias and the B-entry pairs 3; fewer would need P and N on different layers.

| Pair | Layers, ball to jack | Vias P, N | Entry | KiCad skew, mm | Board delay P−N, ps | U1 package P−N, ps, separate | Uncoupled before P, N, mm | After P, N, mm | Length, mm | Made up, mm |
|---|---|---|---|---:|---:|---:|---|---|---:|---:|
| P_TXC | F B F | 2, 2 | F | 0.000 | 0.00 | −2.32 | 25.9, 25.9 | 19.1, 19.1 | 93.33 | 3.05 |
| P_TXD | F B F B | 3, 3 | B | 0.000 | 0.00 | −5.91 | 25.6, 24.6 | 12.8, 12.8 | 91.85 | 0.38 |
| P_RXC | F B F | 2, 2 | F | 0.000 | 0.00 | −0.93 | 22.0, 23.0 | 14.2, 14.2 | 110.61 | 3.53 |
| P_RXD | F B F B | 3, 3 | B | 0.000 | 0.00 | −2.28 | 16.5, 16.5 | 13.5, 13.5 | 106.04 | 1.90 |
| Q_TXC | F B F | 2, 2 | F | 0.000 | 0.00 | −4.65 | 28.6, 27.5 | 23.3, 23.3 | 73.58 | 6.18 |
| Q_TXD | F B F B | 3, 3 | B | 0.000 | 0.00 | +0.77 | 26.3, 26.2 | 14.6, 14.6 | 74.43 | 1.92 |
| Q_RXC | F B F | 2, 2 | F | 0.000 | 0.00 | −0.05 | 22.8, 20.8 | 19.5, 19.5 | 73.80 | 2.08 |
| Q_RXD | F B F B | 3, 3 | B | 0.000 | 0.00 | −10.19 | 26.3, 25.3 | 16.2, 16.2 | 71.97 | 1.28 |

Uncoupled uses the first pass's metric: every part of a lane without its partner at 0.299 mm, including the U1 escape, the length made up, and the fan to the contacts. Length made up is the difference left by the ESD geometry,
as zigzags on uncoupled legs; no via or contact entry is being offset. Delay assumptions: odd mode 5.737 ps/mm, lone line 5.865 ps/mm, barrel 6.97 ps/mm (assumed, not a via solve), with no via excess capacitance, ESD capacitance or return path. Delay mismatch is therefore
calculated from section lengths; rounded to 0.01 ps it is 0.00, which is not a claim of 0 ps on a real board. **Package delays are kept apart and not compensated in copper.**

*Clock to data on LINK, clock minus data, cable excluded; not timing closure.* Jack barrels now count once per data lane, since data enters on B and clock on F.

| Direction | KiCad length, mm | Board delay, no jack barrel, ps | With jack barrel, ps | U1 package, separate, ps | Before, board with jack barrel, ps |
|---|---:|---:|---:|---:|---:|
| P out, Q in (P TX −0.111 mm, Q RX +0.238 mm) | +0.127 | −1.97 | **−24.12** | −17.95 | +50.39 |
| Q out, P in (Q TX −2.445 mm, P RX +2.972 mm) | +0.527 | +0.30 | **−21.84** | +20.46 | +7.93 |

*Placement.* All four parts at rotation 0: D20 (168.5, 204.48), D21 (163.2, 204.48), D22 (192.6, 207.02), D23 (187.5, 207.02). D22 and D23 swapped sides to follow J72's contact order, and they now sit about 8 mm from the contact row, against about 9 mm before. Pin mapping, polarity
and channel assignment are unchanged, and the schematic and netlist are untouched. D20 and D21 sit about 11 mm from J71's contact row, against about 9 mm before, but D20 moved 7.9 mm east to its contacts; moving them south would lengthen the uncoupled lanes straddling them. D20's east edge is limited by H4's courtyard at the committed position, so the route passes DRC with H4 at either position.

*Route.* Corridors from U1 and rows of the first pass kept where possible: 52 first-pass LINK segments are byte-identical. `P_TXC` and `P_TXD` keep their rows to x 170, `P_RXC` and `P_RXD` now run south of the Q rows at y 204.55 and 205.26, x 184–201, then rise to their old rows before H4. `Q_TXD` and `Q_RXD` stay on B in two new rows, `Q_RXD` in place of its F run
at y 188, and come up after the RX rows. `Q_RXC` keeps its via pair and F run, moved east of `Q_TXC`'s vias. Teeth from the first pass are gone. Tracks 2136 to 2000; vias stay at 504.

*Contact entry exception, generated by `tools/gen_pcb.py`.* New rule `LINK entry to J71 J72 pads`: **0.200 mm**, for a `LINK_*` track wholly inside the board's rule areas `J71_LINK_ENTRY` (x 163.55–170.85) or `J72_LINK_ENTRY` (x 186.15–193.45), y 214.38–217.0, F.Cu and B.Cu, against J71/J72 pads only. Geometry: pads 1.524 mm on 2.04 mm pitch in a row, so 2.04/2 − 0.762 − 0.0495 =
0.2085 mm a side between two north-row pads; entries measure that. **No local pair-gap rule was needed.** On the pad axes the gap is 1.02 − 0.099 = 0.921 mm, or 2.961 mm for 3-6, but the partner track beside it lies wholly inside its north-row pad, which KiCad's gap check skips; the board is clean with no gap rule, so none was added. No zone workaround. P and N segments are either exactly parallel or at least 5.7 degrees apart; a check for sub-degree tilts found three by accident, now corrected.

Scope tests, DRC on scratch copies with the generated rules:

| Case | Result |
|---|---|
| Entry at 0.2000 mm to a foreign contact | passes |
| Entry at 0.1994 mm | fails, `LINK entry`, 0.200 |
| Same track started outside the area, y 214.2 | fails, 0.31 mm rule |
| J71 area deleted | fails, 0.31 mm, 3 errors |
| Floating LINK track at the 0.2085 mm spot | passes clearance |
| Floating HDMI track at the same spot | fails, 0.31 mm rule |
| LINK tracks 0.25 mm apart inside an area | fails, 0.31 mm rule |
| LINK track 0.25 mm from MK76's pad inside an area | fails, 0.31 mm rule |
| Pair in an area at 0.921 and 2.961 mm | fails, gap max 0.200 |
| `gen_pcb.py --rules-only` over the routed copy, then a pcbnew save | byte-identical board, same `.kicad_dru` |

*C301.* Reserved `+1V0` via moved from (208.7, 173.89) to **(211.5, 174.5)** in the review reservation list, with its 0.2 mm stub from pad 1; no placeholder on the live board. Via to pad edge 0.162 mm, on the `+1V0` plane at In3. With all 1252 reservations stamped on a scratch copy: errors 53 to 46, none with LINK or `+1V0`, plane pieces unchanged; the old site on this copper gave 3 errors at C301. The 46 are SDRAM, PHY, `+2V5` and GND reservation items from earlier work. Not tested with the rest of the `+1V0` routing.

*Returns.* 13 stitching vias and 4 ESD ground vias replace the first pass's 15. All 24 signal vias outside the U1 corridors have a GND via or through GND pad within 2.0 mm, a figure chosen here, except `P_TXD_P` at (169.5, 201.23), 2.01 mm. D20–D23 pin 2 reach In1, In4 and In6 through a via under the body, 0.8 mm from the pad centre; J71 and J72 shells 4 of 4. On the refilled planes: 56 crossings at a track's own via and 36 where a P/N via pair's clearance holes merge, 92 against 100 before; none under a foreign via. Largest void crossed 0.89 mm2, unchanged. A first via site for `P_TXC_P` merged with J19's clearance into a 3.9 mm2 void that DRC did not see; it moved 0.55 mm west. GND planes stay one piece each.

*Checks.* HEAD against this commit: only D20–D23, LINK copper, their GND vias and stubs, four refilled zones and two new rule areas differ; no zone outline changed. Fresh refills byte-identical. 0 DRC errors and 0 parity with H4 at either position. Warning counts unchanged at this commit; with H4 moved `silk_over_copper` goes 103 to 104. The `silk_overlap` list is capped at 199 and now names D20's outline. No dangling copper, ratsnest 1218. HDMI 24 of 24, LINK 48 of 48, SDRAM 82 of 82, PSRAM 120 of 120, `+1V8_IO` 40 of 40, U1 GND 141 of 141, ESD GND 4 of 4; KiCad 0 unconnected on HDMI and on LINK nets alone. `gate.py --strict` passes; `check_connector_rework.py` stops at the same H1–H4 assertion.

*Working tree, not committed.* The owner's H4 move and its fill changes on four planes, and `.kicad_prl`, stay uncommitted. Copper is the same in both; the working board has 0 errors after its refill, so H4's earlier stale-fill errors are gone. Evidence: `~/freyja-review/link2-2026-11-04/`, image `images/link2_closeup.png`.

**Ethernet MDI, three of four pairs routed (2026-11-04); MDI2 blocked by two fitted parts.** LINK checkpoint accepted, with its cable and timing limits as recorded above. `ETH_MDI0`, `MDI1`, `MDI3` and `ETH_CT` are routed
and connected: **12 of 16 MDI pads on 6 of 8 nets; `ETH_MDI2_P/N` are not routed**, because with footprints fixed there is no room to take them out of U30 while keeping the supply exits. Routing checks do not establish Ethernet compliance.

*Pin mapping.* The Realtek rev 1.7 and HanRun rev A PDFs are not in `ref/datasheets` and could not be retrieved here (the EasyEDA API answers, but its data for these parts holds no drawing link). Checked instead, and all agree: `ref/network.md`, the netlist, the imported vendor symbols, the footprint pads, and the check recorded in `tools/qualified.py` against those drawings. U30 pins 1/2, 4/5, 6/7, 9/10 are MDI0–3 P/N; J70 P2/P3, P4/P7, P5/P6, P8/P9. P4/P7 straddle P5/P6, like contacts 3-6 and 4-5, so MDI1 and MDI2 need different layers at the jack. The footprint has no keepout layers and its outline puts the body's rear edge at y 203.5; the drawing's keepouts were not read. All MDI copper under the body is on B.Cu; `ETH_CT` runs 2.3 mm under the edge on F.Cu.

| Pair | J70 pads | Layers | Vias P, N | Entry | Length P, N, mm | With 1.5886 mm barrel, mm | KiCad skew, mm | F, B length (P), mm | Coupled, uncoupled, mm | Mean delay, ps |
|---|---|---|---|---|---|---|---:|---|---|---:|
| MDI0 | P2, P3 | F B | 1, 1 | B | 11.60, 11.60 | 13.19 | 0.000 | 0.58, 11.02 | 4.72, 6.88 | 78.5 |
| MDI1 | P4, P7 | F B | 1, 1 | B | 11.03, 11.03 | 12.61 | 0.000 | 0.80, 10.23 | 4.99, 6.03 | 75.1 |
| MDI3 | P8, P9 | F B | 1, 1 | B | 12.42, 12.42 | 14.01 | 0.000 | 1.36, 11.05 | 5.87, 6.54 | 83.2 |
| MDI2 | P5, P6 | not routed | | | | | | | | |

Lengths run pad centre to pad centre, tracks only unless stated. No branch stubs. Uncoupled sections, per lane: F launch and the taper into the via pair, 1–2.5 mm; the fan and split at the jack's staggered rows, including length made up on the N lane, because the S row is 2.54 mm further: 0.35 mm on MDI1, 2.18 on MDI3, 2.46 on MDI0. Delay uses the assumptions of the LINK section. Layer changes are needed because of the parts row below; P and N of each pair change once, in the same direction, and enter on the same layer.

*The obstruction.* `R131`, `R132`, `C240`, `R146`, `C239` and `R134` sit in a row at y 198.735, leaving **0.74 mm** under U30's toes at y 197.995. F.Cu cannot pass the row: gaps are 0.36–0.51 mm, and 100 ohm tracks keep 0.31 mm. So every pair changes to B in that strip. MDI0 and MDI3 use the package corners. But pins 3 and 8, `PHY_1V0`, also need F exits, to `C240.1` and `C239.1`, and lie either side of pins 4–7. Between those two exits only **two** 0.45 mm vias fit at 0.6 mm pitch; MDI1 and MDI2 need four. Placing four closes pin 3 or pin 8 for good, so that was not done. MDI1 was routed first because 10/100 needs MDI0 and MDI1.

**Decision for the owner: move `C240` and `R146` about 0.65 mm south.** Tested on a scratch copy only: `C240` to y 200.145, `R146` to y 200.165 opens a second via row and all four pairs pass, 0 DRC errors, 0 parity, skew 0.000 mm. MDI1 changes its N via to (209.0, 199.0), and MDI2 runs F B F with 2 vias per net to an F entry over MDI1's B lanes, 11.04 mm. It needs the launch rule to cover MDI track against other MDI copper at 0.15 mm, in an area to y 199.1. Without that decision, the board has MDI0, MDI1 and MDI3 only, which is not 1000Base-T.

*Launch exception, generated by `tools/gen_pcb.py`.* New rule `MDI launch to U30 pads`: **0.17 mm**, for an `ETH_MDI*` track wholly inside the board's F.Cu rule area `U30_MDI_LAUNCH` (x 207.35–210.75, y 197.25–198.46), against U30's pads only. Geometry: 0.2 mm pads on 0.4 mm pitch give 0.4 − 0.1 − 0.0495 = 0.2505 mm from a track on a pad centre to the next pad, under the 0.31 mm rule; `ETH_MDI1_N` also passes 0.17 mm from pad 6's corner, between it and P's via, measured 0.1717. Above the 0.15 mm board minimum. **No J70 exception:** S-row entries clear N-row pads by 0.3585 mm. No pair-gap exception: the partner tracks at the 0.301 mm toe gap lie inside their pads, which the gap check skips. No HDMI or LINK rule changed. Discontinuity: the pair is uncoupled across the toes and into its via pair; its impedance through there is not modelled.

| Case, scratch copies | Result |
|---|---|
| Lane at 0.1683 mm to pad 6 | fails, `MDI launch`, 0.17 |
| Floating MDI track 0.2455 mm from pin 8 in the area | passes |
| Same spot, LINK net; HDMI net | fail, 0.31 mm rule |
| Rule area deleted | fails, 0.31 mm, 9 errors |
| Launch track run out of the area, toward `C240` | fails, 0.31 mm rule |
| MDI track 0.25 mm from `C245`'s pad in an area | fails, 0.31 mm rule: U30 pads only |
| MDI tracks 0.25 mm apart in an area | fails, 0.31 mm rule |
| `gen_pcb.py --rules-only` over the routed copy, then a save | byte-identical board |

*Centre tap and grounds.* `ETH_CT` runs F.Cu from `C243.1` to P1, 0.25 mm wide. `C243.2` has a GND via at (202.975, 207.15). No termination or bias was added. P10 and both shield pads reach In1, In4 and In6 through the plane fill; J70's internal network is untouched. U30's exposed pad gets four GND vias at y 196.5, x 207.7, 208.6, 209.5, 210.4, for the returns. All six signal vias have one within 2.0 mm, 1.38–1.97 mm; the remaining field stays for the supply chunk. On the refilled In1 and In6, 16 crossings of a void: 3 at a track's own via, 12 at a P/N pair's merged clearance holes, ending at the own via, and 1, `ETH_MDI1_N` running 0.14 mm into J70 P7's own clearance as it enters that pad. Largest void crossed 0.90 mm2. Each GND plane stays one piece. Return current is not modelled.

*Supply access kept.* A scratch copy with `PHY_1V0` stubs from pin 3 to `C240.1` (0.0889 mm) and pin 8 to `C239.1` (0.1 mm) has no via or pad conflict and at least 0.153 mm to MDI copper. It does fail 0.31 mm against the MDI launch tracks, so routing those pins must extend this exception to them; the 0.0889 mm width is the tightest fit beside MDI1_P's via and needs a current check then. All of this is rework if the decision above is taken.

*Checks.* HEAD against this commit: 70 tracks, 11 vias and the rule area added, nothing removed, no footprint moved, every existing track and via byte-identical, four zones refilled with no outline change. Fresh refills byte-identical. **0 DRC errors, 0 parity with H4 at either position**, warnings unchanged, no dangling copper, stackup guard passes, ratsnest 1218 to 1209. LINK 48 of 48, HDMI 24 of 24, SDRAM 82 of 82, PSRAM 120 of 120, `+1V8_IO` 40 of 40, U1 GND 141 of 141; KiCad 0 unconnected on LINK and HDMI nets alone. Stress copy 46 to 45 errors, none with an ETH net. `gate.py --strict` passes; `check_connector_rework.py` stops at the same H1–H4 assertion. The owner's H4 move, its fills and `.prl` remain uncommitted. Evidence: `~/freyja-review/eth-2026-11-04/`, image `images/eth_closeup.png`, scratch test `reports/scratch_all_four.txt`.

**Ethernet MDI complete; `PHY_1V0` and the crystal routed (2026-11-04).** All 16 MDI pads on all 8 nets, all ten `PHY_1V0` pads and the crystal nets connect. This supersedes the MDI2 block and the MDI1 row in the entry above. Routing checks do not establish Ethernet compliance, crystal frequency or drive level. **One pin stays open: U30 pin 40 (`+3V3`) has no via site while RSET keeps its lane; see "Access" below.**

*Documents.* Both retrieved and read; evidence copies in `~/freyja-review/mdi2-2026-11-04/dl/`.

| Document | Revision | Source | SHA-256 starts |
|---|---|---|---|
| HanRun HR911130A drawing | **rev B**, 4 pages | https://hrdzcn.oss-cn-beijing.aliyuncs.com/202601/ab534667d942f65.pdf | d3a5d721 |
| Realtek RTL8211F(I)/RTL8211FD(I)-CG datasheet | rev 1.7, 2016/12/28, distributor-hosted | https://static.chipdip.ru/lib/595/DOC042595102.pdf | 16573d85 |

- **Pin mapping agrees.** Realtek Figure 4 and Tables 1, 2, 8, 9 against the netlist: MDI pins 1/2, 4/5, 6/7, 9/10; AVDD10 3, 8, 38; DVDD10 21; LDO_OUT 30; XTAL_IN 36; XTAL_OUT 37; RSET 39. HanRun page 1 against J70's nets: P2/P3 MDI0, P4/P7 MDI1, P5/P6 MDI2, P8/P9 MDI3, P1 centre taps, P10 network, 11 to 12 green, 14 to 13 yellow.
- **QFN land agrees with Realtek section 11.1:** pitch 0.40, b 0.15-0.25 against a 0.20 mm pad, EP 3.45-3.75 against 3.7 mm.
- **J70 even-row pads are 0.10 mm off the drawing.** Page 3 gives a 1.27 mm stagger, tolerance 0.08 mm. The imported footprint has 1.17 and 1.37 mm: P2, P4, P6, P8, P10 sit 0.10 mm west of nominal. Odd row, row spacing 2.54, posts 11.43, shield holes 15.48 against 15.49, and LED pins agree. Footprint not changed, J70 not moved. Holes are larger than recommended: 0.91 against 0.89, 1.70 against 1.63, 1.10 against 1.02. The drawing gives no pin diameter, so whether the even row seats cannot be settled from it. Check it against a real part before fabrication; correcting the footprint moves five entries by 0.10 mm.
- **Stated restrictions:** no keepout is drawn; page 3 gives only a recommended layout and page 4 only materials, mechanical limits and 0-70 C operating temperature, against the PHY's -40 to 85 C. No drawn keepout does not establish that copper under the magnetics is electrically suitable.
- `tools/qualified.py` still cites HanRun rev A and 1500 Vrms; rev B states 2250 VDC. Reported, not changed here. This is the LDO variant, so section 9.2 applies and the switching-regulator section 9.1 and its inductor do not: LDO_OUT only to AVDD10 and DVDD10, X5R/X7R low-ESR, at least 0.1 uF, close to the pins. The "RTL8211F Series Layout Guide" it names was not available.

*Placement.* Owner decisions, the second and third taken during this chunk after scratch tests showed the brief's fixed parts could not meet it. Rotations unchanged.

| Part | From | To | Why |
|---|---|---|---|
| `C240` | (208.7575, 199.495) | (208.7575, 200.145) | As approved: second via row |
| `R146` | (209.7475, 199.515) | (204.08, 198.9) | Replaces the approved y 200.165. There, XO crossed the MDI strip, estimated 17 mm with 2 vias, and took pin 8's via site |
| `X3` | (204.2575, 195.98) | (204.0775, 195.98) | Pins 34, 36, 37, 38, 39 need five F.Cu exits past X3 and four fit: forced on a scratch copy, 0.0811 mm and shorts. 0.18 mm is the limit, 0.15 mm from `C232` |

*MDI.* P and N are symmetric and each pair enters on one layer. No net exceeds width or gap rules; no zone and no microscopic angle. Lengths as in the entry above.

| Pair | J70 pads | Layers | Vias P, N | Entry | Length P, N, mm | With barrels, mm | KiCad skew, mm | Coupled, uncoupled, mm | Mean delay, ps |
|---|---|---|---|---|---|---|---:|---|---:|
| MDI0 | P2, P3 | F B | 1, 1 | B | 11.60, 11.60 | 13.19 | 0.000 | 4.72, 6.88 | 78.5 |
| MDI1 | P4, P7 | F B | 1, 1 | B | 11.07, 11.07 | 12.66 | 0.000 | 4.27, 6.80 | 75.4 |
| MDI2 | P5, P6 | F | 0, 0 | F | 11.08, 11.08 | 11.08 | 0.000 | 4.71, 6.37 | 64.4 |
| MDI3 | P8, P9 | F B | 1, 1 | B | 12.42, 12.42 | 14.01 | 0.000 | 5.87, 6.54 | 83.2 |

MDI0 and MDI3 copper is byte-identical. MDI1: N via (209.25, 198.4) to (209.0, 199.0), both B lanes re-laid; P's F launch and via kept. MDI2 needs no via now R146 has left the strip: F through the 1.38 mm gap between `C240` and `C239`, then over MDI1's B lanes. Because the S row is 2.54 mm further, P carries 2.45 mm of triangles about 0.5 mm high at y 202.75-204.30, just before P5. MDI2 is on F.Cu under the jack body for 1.5 mm (P) and 4.05 mm (N), the only pair there. The earlier "all MDI copper under the body is on B.Cu" no longer holds.

*Launch exceptions, generated by `tools/gen_pcb.py`, F.Cu, inside `U30_MDI_LAUNCH`, now x 207.35-210.75, y 197.25-199.40.* Each is set just under its measured need.

| Rule | Value | Measured | Scope |
|---|---|---:|---|
| `MDI launch to U30 pads` | 0.17 mm | unchanged | MDI track in the area, U30 pads only |
| `MDI launch to other MDI pairs` | 0.16 mm | 0.168 mm | MDI track in the area against a track or via of another MDI pair. Not coupled partners. Owner authorized down to 0.150 mm |
| `MDI launch to PHY_1V0 exits` | 0.27 mm | 0.2786 mm | MDI track and `PHY_1V0` track both wholly in the area. **Owner authorized this during the chunk**: the original 0.150 mm covered MDI to MDI only, and a track on pin 3 or 8's centre is at best 0.3066 mm from its neighbours |

| Test, scratch copies | Result |
|---|---|
| Other pair, track at 0.155 / 0.165 mm | fails at 0.16 / passes |
| Other pair, via at 0.155 / 0.165 mm | fires at 0.16 / does not |
| Other pair at 0.25 mm, outside the area | fails, 0.31 mm rule |
| Same pair, parallel at 0.25 / 0.20 mm | fails coupled gap / passes |
| `PHY_1V0` at 0.265 / 0.275 mm | fails at 0.27 / passes |
| `+3V3` net or LINK net instead, 0.275 mm | fail, 0.31 mm rule |
| Both outside the area; `PHY_1V0` half outside, 0.275 mm | fail, 0.31 mm rule |
| `PHY_1V0` via at 0.28 mm in the area | fails, 0.31 mm rule |
| Rule area deleted | 21 errors, 0.31 mm rule |
| `gen_pcb.py --rules-only` over the routed copy, then a save | byte-identical board |

*`PHY_1V0`.* Local rail on its own net, tracks and vias only, with no zone and no tie to the FPGA's `+1V0`. F.Cu to each pin and capacitor, 7 vias, then a 0.4 mm In2 trunk (31.89 mm in all) from pin 30's via under U30's west and north edges, and on to the pin 38, bulk, pin 3 and pin 8 vias. Under the package it keeps to the edges, so exposed-pad vias stay free from x 207.7 and y 193.8.

| Pin or part | Local copper | From pin 30, mohm |
|---|---|---:|
| 30, `C241` | 0.2 then 0.3 mm to `C241.1`, 0.3 mm to via (207.5, 189.55) | 1.6 |
| 21, `C238` | 0.2 mm to via (211.6, 192.62); via (211.45, 188.87) at `C238.1`, In2 between | 29.2, 38.8 |
| 38 | **0.09 mm x 2.67 mm** past X3, then 0.2 mm to via (205.35, 198.2) | 39.3 |
| `C242` bulk | 0.3 mm to via (201.9, 194.75) | 41.3 |
| 3, `C240` | **0.0889 x 0.61 mm** between MDI0_N and MDI1_P, **0.11 x 2.33 mm** through the 0.41 mm gap beside `C240`, 0.2 mm to via (208.7345, 201.28) | 48.4, 45.4 |
| 8, `C239` | **0.0889 x 0.67 mm** between MDI2_N and MDI3_P, 0.15 x 0.74 mm to `C239.1`, 0.2 mm round `C239` to via (211.68, 200.62) | 57.9, 54.5 |

Sizing basis: the datasheet read gives no core current, so this uses `tools/budget.py`'s 0.20 A estimate for the whole PHY, as an upper bound for 1.0 V. DC solve, tracks and barrels only, 1.6 mil outer and 0.0152 mm inner assumed: 0.05 A per pin gives 6.72 mV at worst (pin 8) and 3.21 mV at best (pin 21); all 0.20 A into one pin gives at most 11.58 mV. Table 55 allows 0.95-1.05 V; the LDO's own tolerance is not stated. Narrow lengths are fixed by neighbours: pads 0.4 mm apart, a 0.41 mm part gap, two lanes in the 0.63 mm beside X3. AC impedance and LDO stability are not modelled. `C238` is 3.7 mm from pin 21 behind two vias because of where it stands, against section 9.2's "as close as possible"; pin 38 has no capacitor of its own.

*Crystal.* F.Cu, no vias, values unchanged. Pin 36 runs under X3 between its pads to `X3.1`, then `C244.1`, 4.25 mm in all at 0.1 and 0.15 mm. Pin 37 runs under X3 and down its centre to `R146.1`, 4.88 mm at 0.1 mm. `X3.3` to `C245.1` to `R146.2`, 2.69 mm at 0.15 mm. Grounds: `X3.2` via (203.2, 198.2), `C244.2` via (202.05, 194.0), `C245.2` via (205.36, 200.65). `X3.4` has no site for a via of its own, between the LINK B lanes under it and the lanes around it: it goes through `R137.1` and `R136.1` to via (204.1, 191.25), 3.72 mm in a line from its centre. XI and XO run side by side for 1.6 mm at 0.29 mm between X3's pads; coupling is not modelled. **The 18 pF load calculation's 3 pF stray, the frequency and the drive level remain unverified.**

*Other grounds.* `C238.2` (210.86, 187.25), `C239.2` (210.8, 200.63), `C240.2` (209.4, 201.35), `C241.2` (206.87, 189.45), `C242.2` (200.75, 194.85); stubs 0.66-0.97 mm, pad centre to via. `ETH_CT`, `C243` and J70's grounds are unchanged.

*Access to U30's other pins.* Raster search on real copper, then hand-drawn lanes under DRC on a scratch copy.

- **Pin 40, `+3V3`, is closed: an open item.** It lies east of RSET's lane, between that lane, `R131`, and MDI0's vias and B lane. All four candidate sites tested fail. Best: a via partly on the toe at (206.3, 197.0) comes 0.0675 mm from RSET's lane, 0.0825 mm short. **Pin 38's lane is what closes it:** with that lane beside X3, RSET cannot pass further west, and pin 38 has no other way out. The In2 trunk was moved off that site to keep it usable. This needs its own decision, and U30 cannot run without it. Untested candidates: move `C232` and X3 about 0.1 mm further west, or move `R131`.
- **RSET** has a clean lane to `R131.1`, west of pin 40 and east of pin 38's lane.
- **Pins 31-34** reach via sites north of `R136`, but not yet cleanly: the hand-drawn lanes leave three items at 0.134-0.142 mm against 0.15. Three 0.0889 mm lanes between `R136.2` and `C241.1` need 0.8667 mm and there is about 0.85 mm. Neither part moved here. Expect a small nudge when those pins are routed.
- **North and east pins:** each reaches a via or its pad alone. Laid greedily in sequence, the same 9 pins block before and after this chunk, so it closes none; that search is pessimistic and is not a routing result.
- Stress copy with reservations: no error with an ETH or local net, none within U30's area. Its count moves from 44 to 46 only through SDRAM reservation shorts near (201, 144.5), which DRC reports in a different order.

*Checks.* HEAD against the commit board: 125 tracks and 17 vias added, 22 tracks and 1 via removed, all on MDI1. Three footprints moved. Every kept track and via byte-identical, four copper zones refilled, one rule-area outline changed. Tracks 2070 to 2173, vias 515 to 531, ratsnest 1209 to 1182. KiCad 0 unconnected on the 8 MDI nets with `ETH_CT`, on `PHY_1V0`, and on the 3 crystal nets, each alone. **0 DRC errors, 0 parity with H4 at either position**, no dangling copper; `silk_over_copper` 104 to 105, from X3's silk, other warnings unchanged. Fresh refills byte-identical, stackup guard passes. LINK 48 of 48, HDMI 24 of 24, SDRAM 82 of 82, PSRAM 120 of 120, `+1V8_IO` 40 of 40, U1 GND 141 of 141, all 268 GND vias on the main plane pieces. Each GND plane one piece; `+3V3` and `+1V0` one piece each. On refilled In1 and In6, 18 crossings of a void: 12 at P/N pairs' merged via holes ending at the own via, 5 at the own via, 1 `ETH_MDI1_N` entering J70 P7's clearance. `gate.py --strict` passes; `check_connector_rework.py` stops at the same H1-H4 assertion. The owner's H4 move, its fills and `.prl` remain uncommitted. Evidence: `~/freyja-review/mdi2-2026-11-04/`, image `images/closeup.png`.

**U30 island finished; J70 footprint corrected (2026-11-04).** Pin 40, RSET, every strap and pull, the jack LEDs, all local supplies and capacitor grounds connect; the four MDI pairs stay complete. This closes the pin 40 and J70 items of the entry above. U30, the connectors and all other footprints stayed fixed. RGMII is not routed. Routing checks do not establish transient power integrity or Ethernet compliance.

*J70.* Checked against HanRun HR911130A **rev B**, 4 pages (URL and hash in the entry above), the only revision retrieved. The earlier "rev A" citation had no drawing behind it, and no evidence of an incompatible revision was found. Rev B page 3 dimensions the pattern in the component-side view: centre line midway between the 15.49 mm shield holes and the 11.43 mm posts, rows 8.89 and 6.35 mm from the post line, 1.27 mm stagger, ±0.08 mm. The PDF's vector holes agree: even row +4.444, +1.902, −0.630, −3.173, −5.705 mm from that centre line.

| Pad | Drawing, mm | Import, mm | Now, mm | Error was, mm |
|---|---|---|---|---|
| P2 | 4.445 | 4.55 | 4.45 | +0.105 |
| P4 | 1.905 | 2.01 | 1.91 | +0.105 |
| P6 | −0.635 | −0.53 | −0.63 | +0.105 |
| P8 | −3.175 | −3.07 | −3.17 | +0.105 |
| P10 | −5.715 | −5.61 | −5.71 | +0.105 |

Genuine footprint error, outside tolerance, already in the EasyEDA source for C54408 (stagger 1.171/1.369 mm), not from conversion. The page 2 bottom view independently puts pins 2, 4, 6, 8 at +4.44, +1.93, −0.63, −3.18 mm. Corrected in `easyeda/EasyEDA.pretty/RJ45-TH_HR911130A.kicad_mod` and five `at` lines of the board instance only; the file's 0.005 mm frame offset is kept, so the stagger is exactly 1.27 mm. Position, orientation, pad names, nets, odd row, posts and LEDs unchanged. S-row entries now clear N-row pads by 0.4585 mm both sides, against 0.3585 before.

Isolation is now recorded as written: 2250 VDC, 0.5 mA, 60 s, UTP to chip side, not equated with 1500 Vrms, in `tools/qualified.py`, generated `ref/qualified-parts.md` and `ref/network.md`.

Open on J70: the undimensioned page 2 view draws pin 10 at about −5.32 mm against page 3's −5.715, and also draws LED pins off their dimensions, so it is not to scale there and page 3 governs. Library holes stay larger than recommended (0.91/1.70/1.10 against 0.89/1.63/1.02); the drawing gives no pin diameter. **Check P10 and the even row against a real part before fabrication.**

*Placement.* 24 passives and X3 moved within the island, as authorized. C235, C239, C240 and R144, R145 did not.

| Side | Parts and new centres | Why |
|---|---|---|
| West | X3 (203.17, 196.5), R146 (205.1, 196.72), C245 (203.7, 199.11), C244 (201.6, 193.6) | R146 now between pin 37 and X3.3; opens pins 38-40 |
| South-west | R131 (205.74, 199.0), C232 (206.77, 199.4), C241 (204.72, 199.25) | Pin 40's via and capacitor; C241 becomes pin 38's capacitor |
| North-west | R133 (205.09, 188.1), R141 (204.62, 192.2), R142 (204.34, 193.3), R143 (202.85, 193.4) | Pulls beside pins 31-34, not across the package |
| North | C242 (206.28, 190.175), C234 (208.01, 191.12), C236 (208.49, 190.1), C238 (211.85, 191.3) | 4.7 µF on pin 30; pin 28's lane passes under C234 between its pads |
| North, RX | R136 (207.99, 187.2), R137 (208.49, 188.3), R140 (210.42, 187.25), R139 (210.93, 188.75), R135 (212.47, 188.4), R138 (211.93, 186.0) | Straps moved from around the package onto the six RX lanes, which pass through or under them |
| East | C233 (213.5, 197.2), R134 (215.81, 195.6), R132 (215.81, 196.85), C237 (214.52, 187.35) | Pin 11 capacitor; pulls on their own lanes; C237 on the `+2V5` bus |

*Pin completion.* KiCad's own connectivity, each net alone, agrees with a flood over saved copper (`reports/pins.txt`, `netconn.txt`).

| Pins | Net | State |
|---|---|---|
| 1, 2, 4-7, 9, 10 | `ETH_MDI0-3` | Complete to J70 |
| 3, 8, 21, 30, 38 | `PHY_1V0` | Complete with C238-C242 |
| 11, 29, 40 | `+3V3` | On the plane through their own vias, with C233, C234, C232 |
| 28 | `+2V5` | Complete with C236, C237, R134, R135, R139, R140; feeder open |
| 36, 37 | `PHY_XI`, `PHY_XO` | Complete with X3, C244, R146, C245 |
| 39 | `PHY_RSET` | Complete to R131, 2.7 mm |
| 32, 33, 34 | `PHY_LED0-2` | Complete: R141 and J70.12, R142, R143 and J70.14 |
| 41 | `GND` | Exposed pad, four vias |
| 22-27 | `PHY_RX*` | Pin and strap connected; U1 ball open |
| 12, 14, 31 | `PHY_RESET_N`, `PHY_MDIO`, `PHY_INT_N` | Pin and pull connected; U1 ball open |
| 13, 15-20 | `PHY_MDC`, `PHY_TX*` | Open; escape shown on the scratch copy |
| 35 | `CLKOUT` | Unconnected by design |

**Remaining connections to the rest of the board:** `PHY_TXC` C24, `PHY_TX_CTL` B21, `PHY_TXD0` B24, `PHY_TXD1` C22, `PHY_TXD2` C23, `PHY_TXD3` C21, `PHY_RXC` D19, `PHY_RX_CTL` A19, `PHY_RXD0` C19, `PHY_RXD1` H17, `PHY_RXD2` E22, `PHY_RXD3` B19, `PHY_MDC` C17, `PHY_MDIO` B17, `PHY_RESET_N` G1, `PHY_INT_N` G2, all on U1; and the **`+2V5` feeder** to the In5 bus, whose ends include via (207.95, 189.5). The rest of that rail, including L4.1, U1's bank 16 balls and C368, is not connected to it. `+3V3` and `GND` connect through their planes; what feeds those planes is outside this island and was not checked here.

*Escapes.* One scratch copy, `~/freyja-review/u30-island-2026-11-04/rt/esc/`, carries all 16 remaining nets at once: **0 DRC errors, 0 parity, every plane one piece**. RX: `RXC`, `RX_CTL`, `RXD0`, `RXD1` on F.Cu past U32 to y 176.5; `RXD2`, `RXD3` by via to B.Cu, to y 178. TX: six vias at 0.95 mm or more, B.Cu at 0.3 mm pitch to y 188.2. `MDIO`, `MDC`, `RESET_N`, `INT_N` by via to In2, to y 184-187. RGMII at 0.125 mm throughout. None of this copper is on the live board. These prove access only: no length matching or route to a ball was attempted.

*Crystal.* F.Cu, no vias, values unchanged. `PHY_XI` 6.40 mm with its C244 branch, 5.46 mm pin to X3.1; `PHY_XO` 1.70; `PHY_XO_X` 2.22: 10.32 mm against 11.82 before. XI is longer, XO and XO_X shorter, and XI no longer runs beside XO under the crystal. X3.4 and X3.2 tie under the crystal to one GND via. Frequency, drive and stray remain unverified.

*Supply sizing.* DC only; connectivity and DRC do not establish transient behaviour. No Realtek core current exists in rev 1.7, so `PHY_1V0` keeps `tools/budget.py`'s 0.20 A estimate: at most 6.02 mV at 0.05 A per pin, 10.92 mV with all of it into pin 8. `+2V5` at the budget's 0.02 A estimate for `DVDD_RG`: 0.67 mV from C237 to pin 28.

| Path, pin to capacitor | Length, mm | Narrowest |
|---|---|---|
| Pin 3, C240 | 2.21 | 0.0889 x 0.61 exit, then 0.11 x 2.33 |
| Pin 8, C239 | 1.01 | 0.0889 x 0.67 exit |
| Pin 21, C238 | 1.64 | 0.2 |
| Pin 38, C241 | 3.86 | 0.18 x 3.07, replacing 0.09 x 2.67 |
| Pin 30, C242 | 1.35 | 0.2 |
| Pin 11, C233 | 1.50 | 0.2 |
| Pin 29, C234 | 1.47 | 0.2; then 0.15 to its via, 2.98 from the pin |
| Pin 40, C232 | 2.11 | 0.2; via 0.59 from the pin |
| Pin 28, C236 | 2.10 | 0.098 x 0.95 between C234's pads; via 2.7 from the pin; C237 10.5 by the In5 bus |

Through vias are barred within 0.5845 mm of the LINK lanes on B.Cu, a band across the north-west of U30, which is why pins 28 and 29 reach vias about 3 mm out and pin 38's capacitor sits behind 2.9 mm of track. `+2V5`'s In5 bus is 0.3 mm over 18 mm. Trunk changes: the In2 diagonal to the old C242 is gone, pin 30 joins In2 at a new via beside C242.

*MDI.* MDI0's vias moved to (207.25, 198.3) and (207.78, 198.8) to free the pin 40 corner, B.Cu re-laid to the jack. Each even-row entry moved 0.10 mm; partners retuned with their existing bumps, moves of 0.002-0.044 mm. Tracks only: MDI0 10.25, MDI1 11.03, MDI2 11.14, MDI3 12.38 mm. **KiCad skew 0.0000 mm on all four** with the rule set to zero on a scratch copy. MDI2 stays F.Cu only; the others keep one via per net and B entry. **`tools/gen_pcb.py`, `kicad/odin.kicad_dru` and the `U30_MDI_LAUNCH` outline are unchanged.** A wider area was tested and removed: P's lane beside pad 2 is its coupled partner, so no extension was needed.

*Checks.* HEAD against the commit board: 25 footprints moved, J70's five pad lines changed and nothing else in it, U30 unchanged, every kept track and via byte-identical, four copper zones refilled, no zone outline, rule, stackup or net changed. Tracks 2173 to 2278, vias 531 to 551, ratsnest 1182 to 1137. **0 DRC errors, 0 parity with H4 at either position**, no dangling copper, fresh refills byte-identical. `silk_over_copper` 105 to 107: five new, all X3's silk, three gone; `lib_footprint_mismatch` stays X4 and J1. `silk_overlap` is capped at 199, so a moved part's label overlap cannot be counted from that list. KiCad 0 unconnected on the MDI nets with `ETH_CT`, on `PHY_1V0`, the crystal nets, `PHY_RSET`, and the LED nets. LINK 48 of 48, HDMI 24 of 24, SDRAM 82 of 82, PSRAM 120 of 120, `+1V8_IO` 40 of 40, U1 GND 141 of 141. Each GND plane one piece; `+3V3` and `+1V0` one piece each. On refilled In1 and In6, 18 MDI crossings of a void, the same classes as before: 12 at P/N merged via holes ending at the own via, 5 at the own via, 1 `ETH_MDI1_N` entering J70 P7's clearance. Reservation stress copy: 46 errors, none in the island. `gate.py --strict` passes; `check_connector_rework.py` stops at the same H1-H4 assertion and `audit_easyeda.py` at its listed failures. The owner's H4 move, its fills and `.prl` remain uncommitted. Evidence: `~/freyja-review/u30-island-2026-11-04/`, image `images/closeup.png`.

*Still unverified:* the Realtek layout guide was not available; C241's 3.86 mm path and pin 29's via distance rest on the LINK lanes staying; LED wiring is about 40 mm each on In5, under the jack; decoupling effectiveness, crystal behaviour, LED polarity on a real part and PHY operation need the bench.

**RGMII and management routed, U1 to U30 (2026-11-04).** All 16 nets connect: 41 pads, including every strap and pull branch, KiCad 0 unconnected on the 12 RGMII nets and on the 4 management nets, each group alone, from 12 and 4. **TX timing is provisional: Realtek publishes neither the tolerance of the internal TXC delay nor an input window for `TXDLY = 1`.** RX is calculated positive with named allowances. Nothing has been measured. The contract, fixture, constraints and results are in [`gateware/rgmii1000/`](gateware/rgmii1000/README.md). The global `+2V5` feeder is still open, as planned.

*Timing basis, rev 1.7 Table 60.* `TXDLY` and `RXDLY` read 1 from the straps. TX: the FPGA launches clock and data together and sends no shifted clock; TskewT, ±0.5 ns "without delay integrated", is held at U30's pins, board included. RX: TsetupT and TholdT, 1.2 ns, at U30's pins. The nominal 2 ns appears nowhere in the constraints and no clock serpentine was added. Vivado 2026.1 on `xc7a100tfgg676-2`, both DDR edges, min and max, slow and fast corners, all registers checked in the IOBs; RX modelled on its own received clock.

| Check, ns | TX | RX |
|---|---:|---:|
| Worst setup slack | +0.169 (TXD1) | +0.149 (RXD3) |
| Worst hold slack | +0.100 (TX_CTL) | +0.211 (RXD1) |
| Room for board and package, data minus clock, tightest net | −0.206 to +0.156 | −0.389 to +0.292, less a ±0.1 allowance |
| Routed, data minus clock, across the group | −0.110 to −0.013 | −0.078 to +0.046 |

*Two results that change the implementation.* RX needs a fixed IDELAY of 11 taps on each data ball, with a 200 MHz IDELAYCTRL: direct BUFIO capture fails hold by 1.02 ns. `ref/network.md` said the fabric needs no delay of its own and is corrected. TX is LVCMOS25, 8 mA, fast slew, chosen on the routed TXC against Table 60's 0.75 ns edge: 4 mA fast reaches 2.38 ns and 8 mA slow 1.06 ns; 12 mA rings harder; 8 mA slow on data alone fails the limit by 0.536 ns. The SDRAM settings were not reused.

| Net | Ball, pin | Length, mm | By layer, mm | Vias | Line, ps | Package, ps |
|---|---|---:|---|---:|---:|---:|
| TXC | C24, 20 | 60.46 | F 4.66, In2 20.57, B 35.24 | 3 | 400.1 | 141 |
| TXD0 | B24, 18 | 50.52 | F 1.62, In2 19.52, B 29.38 | 3 | 340.5 | 144 |
| TXD1 | C22, 17 | 55.26 | F 3.45, In2 17.61, B 34.20 | 3 | 366.2 | 151 |
| TXD2 | C23, 16 | 51.91 | F 1.70, In2 19.53, B 30.68 | 3 | 348.7 | 115 |
| TXD3 | C21, 15 | 57.36 | F 2.64, In2 17.33, B 37.39 | 3 | 378.3 | 125 |
| TX_CTL | B21, 19 | 51.74 | F 3.21, In2 19.48, B 29.06 | 3 | 347.6 | 110 |
| RXC | D19, 27 | 47.12 | F 8.28, In2 3.54, B 35.30 | 3 | 303.1 | 98 |
| RXD0 | C19, 25 | 46.25 | F 9.90, In5 5.41, B 30.93 | 3 | 300.0 | 103 |
| RXD1 | H17, 24 | 45.61 | F 7.69, In5 5.41, B 32.50 | 3 | 296.2 | 28 |
| RXD2 | E22, 23 | 52.48 | F 9.84, B 42.63 | 2 | 330.7 | 114 |
| RXD3 | B19, 22 | 47.41 | F 9.14, In5 13.62, B 24.66 | 3 | 315.8 | 124 |
| RX_CTL | A19, 26 | 36.08 | F 36.08 | 0 | 212.1 | 122 |
| MDC | C17, 13 | 57.44 | F 6.41, In2 7.41, B 43.62 | 3 | | |
| MDIO | B17, 14 | 54.14 | F 5.21, In2 8.41, B 40.52 | 3 | | |
| RESET_N | G1, 12 | 63.95 | F 63.95 | 0 | | |
| INT_N | G2, 31 | 67.14 | F 54.40, In2 12.74 | 2 | | |

Ball and pin agree with the netlist and `ref/freya.xdc`. TX and RX are each matched to their own clock within the derived limits, not to each other, and no length was added for matching. TXC is the longest of its group because the natural lane order puts it at the outside; RX_CTL is 91 ps short of RXC because it has no vias and no detour, and sits inside the limit. Line delay uses the field solve: 0.125 mm is 48.4 ohm on F and B, 49.1 ohm on In2 and In5, a calculation and not a fabricator's result. Barrels are 6.97 ps/mm, assumed.

*Layout.* TX balls lie west of RX balls while TX pins lie east of RX pins, so the groups swap between U1 and U30. In2 and In5 are closed by the SDRAM lanes between them, and F.Cu by decoupling, so the crossing is on B.Cu, spread across x 210.4 to 219 between the rows of reserved capacitor vias and x 210.4 to 217 further south. TX leaves its balls on In2 and hops to B.Cu at y 160 to 166; RX uses In5 or B.Cu in the ball field and B.Cu south, with the vias at U30 fanned so each B lane stays in order. RX_CTL has a clear path on F.Cu and takes it, through R137's pad, zero vias, F.Cu over In1 throughout. RESET_N takes the east side of U1 and under U32's body on F.Cu, zero vias. INT_N does the same as far as y 187, then In2 under both RGMII groups. Reserved via sites of other nets were kept: two of my first sites, (204.7, 158.34) and (216.7, 158.34), sat on `+2V5` and `+1V2_MGT` reservations, which plain DRC cannot see and the stress copy did; `PHY_TXC`, `PHY_TX_CTL`, `PHY_TXD1` and `PHY_MDIO` moved. No reservation stub was imported; all 12 RGMII nets are 0.125 mm throughout; MDC and MDIO are 0.125 mm except 0.1 mm on their F.Cu lanes to the pins; RESET_N and INT_N are 0.1 mm on F.Cu, and INT_N 0.125 mm on In2.

*Return paths.* Of the 40 vias on these nets, 14 keep their reference and 26 change In1 to In6. 25 of the 26 have a GND via within 2.0 mm, the figure chosen earlier; `PHY_TX_CTL` at (217.45, 165.9) has 2.08 mm. Five GND vias were added: two on reserved sites, (216.4, 167.69) and (217.95, 163.44), without connecting their capacitors, and new ones at (215.3, 194.1), (213.9, 194.97) and (212.02, 185.0). On the refilled In1 and In6, every void crossing of these nets is at its own via; one own via, `PHY_MDC` at (217.2, 196.3), merges with the `+2V5` via at (216.95, 195.6), crossed only as the track leaves it. Each GND plane stays one piece, `+3V3` and `+1V0` one piece each.

*Checks.* HEAD against the commit board: 307 tracks and 45 vias added, nothing removed, no footprint moved, every kept track and via byte-identical, five zones refilled with no outline change, no rule, stackup or net changed. Tracks 2278 to 2585, vias 551 to 596, ratsnest 1137 to 1121. **0 DRC errors, 0 parity with H4 at either position**, warnings unchanged, no dangling copper, fresh refills byte-identical. Earlier connectivity preserved, by KiCad on each group: LINK 0, SDRAM 0, PSRAM 0, MDI 0, the other PHY nets 0, `+1V8_IO` 0, HDMI 15 unchanged, and GND, `+3V3`, `+2V5` and `+1V0` unchanged at 280, 120, 20 and 40. Reservation stress copy: 34 errors before and 33 after, none with these nets. The owner's H4 move, its fills and `.prl` remain uncommitted. Evidence: `~/freyja-review/rgmii-2026-11-04/`, image `images/closeup.png`.

*Unresolved.* (1) U30's receiver in `TXDLY = 1`, as above; this is the missing term for TX. (2) TX rings in the fast corner at U30: up to 4.13 V and −1.48 V in unclamped simulation, and up to 0.31 V inside VIL and VIH. It does not re-cross 1.25 V. Damping check below. (3) U30's output is unmodelled, covered by a ±0.1 ns allowance. (4) IDELAY pattern jitter is not in the report, and DS181 is not in the repository. (5) X4 jitter, crosstalk, simultaneous switching, 10/100 modes and via stubs are unassessed. (6) `tools/gen_pcb.py` still generates the comment "length-match by hand" in `odin.kicad_dru`; it is superseded by the profile and was left for the next rules change. (7) The `+2V5` feeder from the rest of the rail to U30's In5 bus is the next chunk.

**TX series damping checked: no resistors added, board unchanged (2026-11-05).** With footprints fixed, no site exists for six resistors near the FPGA, so the live board, schematic, netlist and rules are as committed in `46791f3`. Full table in [`gateware/rgmii1000/`](gateware/rgmii1000/README.md).

*Correction.* Table 54's −0.2 to 2.8 V row is labelled "Supply Voltage 2.5V", so the earlier comparison of simulated pin voltages against it was wrong. Rev 1.7 has no RGMII input-voltage, overshoot, undershoot or clamp-current limit; its only "Input Voltage" rows are 3.3 V and 1.0 V DC. Table 58 gives VIH 1.7 V, VIL 0.7 V. So no transient pass or fail can be stated for these pins, and the simulated voltages are unclamped results, not predicted hardware voltages.

*What limits placement.* No through via is legal west of x 210.4, because the LINK pairs on B.Cu bar it. South of U1, an 0402 with its courtyard fits in one spot before y 169, between the capacitor rows; C301's body and U10 fill y 171 to 185. A pocket near (219, 171) has via sites for one or two nets. An 0201 does not change this. Length before the resistor matters: on TXC, 10 ohm clears the ringback from about 26 mm or nearer and leaves 0.08 V at 38 mm.

| Worst over corners, 2 and 5 pF, both edges, unclamped | Today | At U30, 4 mm before the pin: TXC 33, data 47 | B.Cu at the hop vias, 18-22 mm from the ball: TXC 10, data 22 |
|---|---:|---:|---:|
| Allowed now? | | Yes, no via added | **No: second-side assembly** |
| TXC edge, limit 0.75 ns | 0.63 | 0.74 | 0.71 |
| TXC peak, V | 4.13, −1.48 | 3.93, −1.29 | 3.85, −1.23 |
| TXC ringback, V | 0.31 | **0.05** | 0 |
| Data peak, V | 4.11, −1.48 | 3.82, −1.18 | 3.56, −0.94 |
| Data ringback, V | 0.30 | 0 | 0 |
| TX setup, hold, ns | +0.169, +0.100 | +0.108, +0.130 | +0.094, +0.142 |

TXC's 0.75 ns edge is the limit in both: 47 ohm at U30 reaches 0.79 ns and 22 ohm at the hop 0.80 ns. Neither site was laid out. The site at U30 filters what reaches the pin, without damping the line, so it is not the source damping asked for. Evidence: `~/freyja-review/txdamp-2026-11-05/`, image `images/placement.png`. Remaining assumptions are unchanged: unpublished TX-delay tolerance and input window, no RXC jitter figure, unmodelled U30 driver, IDELAY pattern jitter. The `+2V5` feeder is still next.

**U30-end TX resistors transferred (2026-11-05).** Six 0402 resistors in series with the TX lines at U30's end: R208 33 ohm on TXC; R209 TX_CTL, R210-R213 TXD0-3, 47 ohm; FPGA drive stays 8 mA fast. These filter what reaches U30's pins and are not source termination. **TX stays provisional.** Nothing has been measured. Full tables in [`gateware/rgmii1000/`](gateware/rgmii1000/README.md).

*Sources.* `tools/design.py` appends the six parts at the end of the build, so no designator moved and the group `U30 TX input resistors` sits on the Network sheet. U30's pins are now `PHY_TXC_U30`, `PHY_TX_CTL_U30`, `PHY_TXD0_U30` to `PHY_TXD3_U30`; U1's balls keep `PHY_TXC` and friends, so `tools/alloc.py`, `ref/freya.xdc` and `gateware/gate/` are unchanged. `tools/gen_pcb.py` adds the three patterns to the RGMII class, and all 12 net names were confirmed to resolve to it; the stale "length-match by hand" comment in `kicad/odin.kicad_dru` is replaced. Regenerated: `network.kicad_sch`, `odin.net`, `ref/parts-guide.md`, `ref/bom-jlcpcb.csv`. 47 ohm has no fixed LCSC part and is left to JLCPCB's matcher. Footprints 555 to 561, parts 551 to 557. `load_pcb.py` was tried on a clean copy with `update_silkscreen.py` held back so manual labels stay: 0 of 555 parts moved, six added, six U30 pad nets changed and nothing else; the new references went to F.Fab like every other part. The rules were edited directly for the same result as `gen_pcb.py --rules-only`, which would also have rewritten the stackup block; a semantic compare of the two project files shows only those three patterns differ.

*Layout.* All on F.Cu, one-sided, no footprint moved. Most of the old "4 mm before the pin" fell on B.Cu: F.Cu reached only 0.9 to 4.0 mm from the pins before each net's via. So each net's via moved up its lane and the end of the route was re-laid, keeping three vias per net and the B.Cu lane order at y 188. Centre from the pin: TXC 5.65, TX_CTL 4.93, TXD1 4.37, TXD0 3.13, TXD2 2.38, TXD3 2.05 mm, against about 4 mm asked; the fan-out and lane order set the spread, and no wider search was made. TXC moves further out because it must clear R209 and C238's ground via. Removed 31 tracks and 8 vias, added 54 and 9, all on TX except three GND vias replacing two: the old (215.3, 194.1) and (213.9, 194.97) now sit under the new copper, so GND vias are at (216.35, 193.9), (216.35, 192.0) and (216.4, 190.4). All six new F-to-B vias are within 2.0 mm of a GND via, worst 1.90 mm.

*Results, worst over Slow and Fast corners, 2 and 5 pF, both edges, unclamped.*

| Check | Result | Against |
|---|---:|---|
| TXC edge, 0.2 to 0.8 of the corner's VCC | 0.742 ns | 0.75 ns, Table 60 |
| TXC return inside VIL after first crossing | 0.043 V one edge, 0.090 V at 125 MHz | VIL 0.7 V, Table 58; rising edges and all data 0 |
| TXC settled at the valid level, after its 1.25 V crossing | 2.41 ns | Next edge leaves 4 ns after this one starts |
| TX setup, hold, both DDR edges, Vivado | +0.104 (TXD1), +0.138 ns (TXD2) | RX unchanged, +0.149, +0.211 |
| Peaks, unclamped | 3.92, −1.28 V | No limit published |

This entry first also recorded 0.793 ns between fixed 0.5 and 2.0 V and called 0.742 ns 20-80 % of "the swing"; see "TXC edge measured against DVDD_RG" below, which withdraws the first and corrects the second.

*The earlier 0.05 V.* One case only: TXC, 33 ohm at 4 mm, Fast corner, 2 pF, a single falling edge from a settled line. The lumped pin goes below VIL 0.7 V, undershoots to −1.29 V, and 2.17 ns after that first crossing rings back to 0.752 V, so 0.05 V is how far it returns above VIL. It is not a noise margin or a receiver result: the model has no U30 clamps, an assumed C and lossless lines. On this copper it is 0.043 V, 0.29 ns long, and 0.090 V with a square wave. No re-crossing of 1.25 V is reported, and that does not establish clock integrity: 1.25 V is a model reference, and U30's threshold, hysteresis and sensitivity to a short excursion are unpublished.

*Not in the setup and hold.* Pattern shift of the 1.25 V crossing in the square wave, up to about 0.055 ns clock against data in one corner and load; a worst-case data pattern; U30's clamps and capacitance. Still missing from Realtek: the TX delay's tolerance, an input window for `TXDLY = 1`, and any RGMII input-voltage, overshoot or clamp-current limit. Unchanged assumptions: no RXC jitter figure, unmodelled U30 driver, IDELAY pattern jitter, crosstalk, via stubs.

*Checks.* HEAD against the commit board: six footprints and six nets added, U30's six pad nets changed, every kept track and via byte-identical, four copper zones refilled with no outline change, no stackup change, no existing footprint moved. Tracks 2585 to 2608, vias 596 to 597, ratsnest 1121 unchanged. **0 DRC errors, 0 parity with H4 at either position**, warnings unchanged, no dangling copper, fresh refills byte-identical. RGMII TX 24 pads and 0 unconnected, from 12. On refilled In1 and In6, every void crossing of these nets is at the net's own via; the first layout had `PHY_TXD2` crossing a void merged from three new vias, 2.08 mm detour, and the vias were spread to clear it. `gate.py --strict` passes; `check_connector_rework.py` stops at the same H1-H4 assertion and `audit_easyeda.py` at its listed failures. The owner's H4 move, its fills and `.prl` remain uncommitted. Evidence: `~/freyja-review/r2v5-2026-11-05/`.

**`+2V5` distribution routed (2026-11-05).** All 27 pads on the net reach L4.1 by copper: U1 balls A21, B18, C25, D22, E19, F16, as expected, and the netlist has no others; U30 pin 28 with its local bus, C236, C237, R134, R135, R139, R140; C198, C199, C348-C353, C368; the J19.3 and J20.3 selector pins; R59 and R86. KiCad reports 0 unconnected on the net alone, from 20. No footprint, rule, zone outline or signal copper changed. **This completes distribution from the output node only: the rail is not yet powered in layout terms.**

*Topology.* From L4.1, C198 and C199 on F.Cu, four vias to B.Cu. Two rows pass the connector field through the gaps at y 124.94 and 127.51, 0.5 and 0.55 mm, the widest that fit between J53, MK65, J62 and J3A, and join at a 1.0 mm column x 172.95 that runs to J19. A 1.5 mm north row at y 123.2, north of the `+1V8_IO` trunk, feeds three hops under that trunk on In5, each with two vias per side: x 178.25 to a 0.5 mm feeder for the west balls, the caps, C368 and U30; x 209.65 to a 0.2 mm feeder for the east balls; x 240.2 through J5A's gap to a 1.5 mm column x 247.5 behind the J5 connectors, so x 241 stays open for slot signals on B.Cu. U1: F.Cu bus at y 160.45 through C350, C353, C349, C352; ball lanes on the half-ball lattice with the reserved dogbones. `PHY_RX_CTL` on F.Cu and the TX lanes on In2 fence B18, E19, F16 and C348 from the west balls, which is why those have their own feeder. U30: B.Cu to x 197 y 186, then In2 at 0.2 mm to the existing via on the In5 bus at (207.95, 189.5). R86 by a thin tap from the north row.

*Regulator.* R59.1 takes its own 0.2 mm In5 branch from a via beside C198.1, between In4 and In6, so the sense point is the output capacitor and no load current flows in it. The divider itself and U13's FB pin were not touched. No added copper is nearer than 0.355 mm edge to edge to the switching node, the sense line on In5 beside L4.2; the F.Cu source bar stays south of L4.1 and U13.

*Sizing.* Copper 1 oz outer, 0.5 oz inner, 18 um via barrels, assumed; DC at 25 C from C198.1. Load: `tools/budget.py` for bank 16, 0.12 A, split evenly over six balls, and DVDD_RG, 0.02 A, **both estimates to replace with an XPE result and a measurement**; J19 and J20 each 0.6 A with their selector at 2.5 V, a 0.5 A PIN V allowance plus the 0.1 A bank estimate, as for `+1V8_IO`. Pulls and the divider, about 3 mA, left out. 1.34 A at the source against U13's 2 A.

| Case | U1 balls, mV | U30 pin 28, mV | J19.3, mV | J20.3, mV |
|---|---:|---:|---:|---:|
| Board load, 0.14 A | 6.7-8.5 | 7.7 | 1.3 | 2.3 |
| J19 at 2.5 V, 0.74 A | 12.2-14.0 | 13.2 | 31.5 | 7.8 |
| J20 at 2.5 V, 0.74 A | 14.0-21.9 | 15.0 | 6.8 | 43.1 |
| Both, 1.34 A | 19.5-27.4 | 20.5 | 37.0 | **48.6** |

Most loaded against IPC-2221 at 10 C rise: the F.Cu source bar, 1.34 A in 1.0 mm, 56 %; the selector entries, 0.6 A in 0.4 mm, 49 %; worst via 0.45 A. **DC sizing and connectivity do not establish transient power integrity:** decoupling, the 103.4 uF on the output against TI's 47 uF in `ref/power-budget.md`, and the J19/J20 capacitors behind a selector, still need bench qualification.

*Grounds.* C198, C199, C348-C353 and C368 each have their own via into In1, In4 and In6, reserved sites where they exist, and KiCad's GND count falls by exactly these nine, 280 to 271.

*Still open, separately.* U13.3 `+5V` with C200 and C268, with the whole `+5V` net still unrouted; `SW+2V5`, U13.4 to L4.2; `FB+2V5`, U13.1, R59.2, R60.1; `EN_2V5`, U7.22, U13.5, R91.1; and grounds U13.2, R60.2, R91.2, C200.2, C268.2. B.Cu is now also walled by the north row and the x 172.95 and x 178 columns, so slot signals crossing them need In2 or In5.

*Checks.* The resistor commit against this one: 126 tracks and 41 vias added, nothing removed, no footprint changed, every kept track and via byte-identical, five zones refilled with no outline change, no rule or stackup change. Tracks 2608 to 2734, vias 597 to 638, ratsnest 1121 to 1092. **0 DRC errors, 0 parity with H4 at either position**, warnings unchanged, no dangling copper, fresh refills byte-identical. By KiCad on each group, unchanged: RGMII TX and RX, management, LINK, SDRAM, PSRAM, MDI, other PHY nets and `+1V8_IO` 0, HDMI 15, `+3V3` 120, `+1V0` 40. Each GND plane one piece, `+3V3` and `+1V0` one piece each; on refilled In1 and In6, every void crossing by RGMII or management is at the net's own via. Reservation stress copy: 32 errors before and after, none new on these nets; it found my first east feeder over two reserved sites, (212.25, 130.29) and (212.25, 132.49), and that lane now passes them at x 212.85. TX route and timing are identical on this board. `gate.py --strict` passes; `check_connector_rework.py` stops at the same H1-H4 assertion and `audit_easyeda.py` at its listed failures. The owner's H4 move, its fills and `.prl` remain uncommitted. Evidence: `~/freyja-review/r2v5-2026-11-05/`, image `images/result.png`.

**TXC edge measured against DVDD_RG (2026-11-05).** R208 stays 33 ohm: the edge passes with 0.2 and 0.8 of U30's DVDD_RG as thresholds, none taken from the waveform, but by single picoseconds at an assumed load, so **this is not robust electrical closure**. No schematic, BOM, footprint, copper, rule or constraint changed; `txcedge.py` and `gateware/rgmii1000/README.md` carry the numbers.

Bank 16's VCCO balls and U30 pin 28 are one net, `+2V5`, in `kicad/odin.net`. From the table in the `+2V5` entry, DVDD_RG minus VCCO is −1.0 to +6.9 mV DC. VCCO in the sweep is the IBIS range, 2.375, 2.5 and 2.625 V; U13's setpoint is 2.4987 V, bounded at 2.412 to 2.588 V by VFB 0.588 to 0.612 V (SLVSDG1C) and 1 % R59 and R60; Realtek's RGMII supply range is 2.25 to 2.75 V (rev 1.7 Table 55, 58).

| TXC, Slow corner, 5 pF | DVDD_RG, V | Rise, ns | Fall, ns | Margin to 0.75 ns, ps |
|---|---:|---:|---:|---:|
| Equal supplies, one edge | 2.3750 | 0.7416 | 0.7243 | **+8.4** |
| DC offset +6.9 mV, one edge | 2.3819 | 0.7443 | 0.7264 | +5.7 |
| R208 +1 %, DC offset +6.9 mV, one edge | 2.3819 | 0.7455 | 0.7277 | **+4.5** |
| Equal supplies, 125 MHz | 2.3750 | 0.7149 | 0.7223 | +27.7 |
| R208 +1 %, DC offset +6.9 mV, 125 MHz | 2.3819 | 0.7191 | 0.7261 | +23.9 |

Settled levels are 2.371 and 0.002 V Slow, 2.493 and 0.000 V Typ, 2.619 and 0.000 V Fast, from the last 5 ns of a 60 ns window with no ripple left. The limit is reached at 5.16 pF, or 5.08 pF with R208 at +1 % and the offset. This entry first carried a −0.4 ps stack with R208 at +5 %; see "R208 tolerance corrected" below, the part is 1 %. 18 and 22 ohm were not compared, since 33 ohm passes. Typ and Fast have over 200 ps.

*Withdrawn and corrected.* The 0.793 ns set a 2.375 V signal against 2.5 V thresholds, which needs 125 mV between two pins of one net; so the "owner's decision" asked with it, and 22 ohm's 0.749 ns, no longer apply. The 0.742 ns was reported as 20-80 % of "the swing"; it was always 0.2 and 0.8 of the corner's VCC. And `txsi.py` cut its 125 MHz windows at the driver, though an edge reaches the pin about 1.8 ns later, so each lost the end of its half period. Cut at the pin, with a settled cycle shown unchanged from the one before: TXC's return inside VIL stays 0.090 V, now also known to be 1.92 ns after the first crossing and 0.42 ns long; its settling is 2.44 ns, not 2.26 ns, 1.56 ns before the next edge crosses 1.25 V; on data, one flight figure moves by 0.1 ps and returns stay 0. No 1.25 V re-crossing, which still does not establish clock integrity.

*Unchanged, still open.* Setup +0.104 and hold +0.138 ns from Vivado, as R208 did not change; with the whole 0.055 ns pattern shift taken off both, whichever corner they occur in, +0.049 and +0.083 ns. A worst-case data pattern is not simulated. Ethernet TX stays provisional: Realtek publishes no tolerance for the TX delay, no input window for `TXDLY = 1`, no input capacitance, threshold, hysteresis or clamp, and no RGMII input-voltage, overshoot or clamp-current limit. Peaks of 3.92 and −1.28 V are unclamped model results. Lines are lossless, R208's parasitics and transient supply differences are left out, and the IBIS tables have no slow process at the rail's actual 2.5 V. Nothing has been measured on hardware.

*Checks.* `txcedge.py` on the committed board reproduces `txsi.py`'s 0.742 ns, and each edge is cross-checked by a plain first-crossing routine. `txsi.py`'s single-edge rows are unchanged. The first draft of the offset had the wrong sign and its "settled" level was an 8 ns sample of ringing; both were found and fixed before these figures. Board and `.prl` hashes unchanged, `gate.py --strict` passes.

**R208 tolerance corrected, no part changed (2026-11-05).** R208 was already a 1 % part. It is C25105, Uniroyal 0402WGF330JTCE, like every other 33 ohm 0402 on the board. Uniroyal's part-number key (chip series data sheet, section 2) makes the 7th code the tolerance, `F` = ±1 %, and `330J` the value, 330 × 10⁻¹ ohm, so the `J` I read as 5 % is a multiplier. JLCPCB's library row agrees: ±1 %, ±100 ppm/°C, 62.5 mW, 0402, basic, SMT, 1.4 million in stock in the snapshot of 2026-11-03. The −0.4 ps stack reported with the edge measurement used a +5 % that this part does not have, and is withdrawn.

The owner's candidate, YAGEO RC0402FR-0733RL, C138002, was checked: ±1 % (`F`), ±100 ppm/°C for 10 ohm to 10 Mohm, body 1.00 × 0.50 × 0.35 mm against Uniroyal's 1.00 × 0.50 × 0.35 mm, so the fitted `R_0402_1005Metric` land suits both; SMT, 7.0 million in the same snapshot, extended. It would add a fee line and a second 33 ohm BOM line for the same tolerance and coefficient, so it was not swapped in. Schematic, netlist, BOM, board, footprints and routing are unchanged; `tools/design.py` gains a comment naming the part and its tolerance where it is chosen.

With the fitted 1 %: Slow corner, 5 pF, DC offset +6.9 mV, one edge **+4.5 ps**; with 60 °C of the 100 ppm/°C as well, +3.8 ps; 125 MHz +23.9 ps. At that offset R208 would have to reach 34.55 ohm, +4.7 %, to use the margin up. **1 % is the resistance as delivered, not a complete allowance:** temperature is shown only as that one row, and solder shift, load life and the resistor's parasitics are not modelled. The margin is still a few picoseconds at an assumed 5 pF, and Ethernet TX stays provisional for the reasons above. No value was swept.

**U13 regulator cell routed (2026-11-05).** `SW+2V5`, `FB+2V5` and `EN_2V5` are complete, the regulator's five grounds reach the planes, and U13.3, C200 and C268 form the local `+5V` input node. This closes the list left open in the `+2V5` entry above except the feeder: **`+5V` itself is still unrouted, so the rail is still not powered in layout terms.** All 27 `+2V5` pads still reach L4.1.

*Part and pins.* The fitted part is TLV62569PDRLR (`tools/design.py`, C398364), TI's SOT-563 DRL package with power good. SLVSDG1C section 5, SOT563-6 column: 1 FB, 2 GND, 3 VIN, 4 SW, 5 EN, 6 PG. The board's pads 1 to 6 carry `FB+2V5`, GND, `+5V`, `SW+2V5`, `EN_2V5` and nothing, in the top view's order: 4 opposite 3, 6 opposite 1. PG stays open, which the pin table allows. The land is the reviewed EasyEDA import, 0.5 mm pitch, rows 1.44 mm apart with 0.28 x 0.545 mm pads, against TI's DRL0006A example of 1.48 mm and 0.3 x 0.67 mm; not changed here.

*What the cell looked like.* The island tool had left C200 beside the VIN pin the wrong way round, its `+5V` pad at the SW pin and its GND pad at VIN; C268, the 4.7 uF, 4.6 mm away beyond the divider; and both FB pads on the side away from pin 1. No sound input loop could be routed on that placement, so four passives moved, as authorized.

| Part | From | To | Moved, mm |
|---|---|---|---:|
| C200, 100 nF | (159.855, 113.395), 90 | (161.105, 111.740), 0 | 2.07 |
| C268, 4.7 uF | (160.655, 107.995), 0 | (160.750, 110.440), 0 | 2.45 |
| R59, 100k | (160.655, 109.695), 180 | (160.655, 108.870), 180 | 0.83 |
| R60, 31.6k | (160.655, 111.295), 0 | (160.655, 107.300), 0 | 4.00 |

U13, L4, C198, C199, R91 and every other footprint stayed; locks and the `island U13` group are unchanged.

*Layout, against SLVSDG1C 10.1 and Figure 21.* At rotation 180 the north row is VIN, GND, FB from west to east, with L4's SW pad 0.36 mm south of the south row.
- **Input loop.** C200 lies across pins 3 and 2, 0.25 mm from them, `+5V` west and GND east; each pin reaches its pad by a 0.25 mm stub about 0.5 mm long. C268 sits directly behind it the same way round, joined by 0.5 mm straps, so the feeder meets the 4.7 uF first and the 100 nF is nearest the pins. No via is inside the loop.
- **Ground.** Pin 2, C200.2 and C268.2 are one piece of F.Cu with three vias beside the two GND pads, at (162.25, 111.74), (162.30, 111.11) and (162.33, 110.44), into In1, In4 and In6. R60.2 and R91.2 have their own vias, so the divider's ground does not share copper with the power return.
- **SW.** Pin 4 straight into L4.2: 0.28 mm wide, 0.98 mm from pin centre to its end inside the pad, no via.
- **FB.** Pin 1 to a via 0.6 mm east, 5.8 mm on In2 under In1 beneath the middle of the two capacitors, up through a via between R59 and R60, 3.0 mm on F.Cu in all. Nothing added on F.Cu is nearer the SW copper than U13's own pin 1 pad, 1.15 mm; the In2 trace is 1.18 mm away in plan, with In1 between. It goes by In2 because the only F.Cu channel north, between the cell and J53, holds the accepted sense via at (162.37, 109.695), and FB between the two capacitors would cut their straps.
- **Sense.** The accepted In5 line, its via and its F.Cu stub are byte-identical. R59 moved 0.83 mm north to clear C268, so 0.83 mm of 0.2 mm track joins the stub's end to R59.1: the takeoff is still C198.1 and the line still carries no load current.
- **EN.** Pin 5 has 0.36 mm to L4's SW pad and no way out on that side at 0.15 mm clearance, so it leaves north under the package, a SOT-563 with no exposed pad, then west between pins 3 and 4 to R91.1, which did not move. A via there takes it to In5: under L4 between In4 and In6, east on the lane at y 117.318 between the pad rows of J53 and J3A, to a via at (183.66, 119.22) and U7 pin 22. That via is in the one site below pin 22, between R29 and Y1's GND pad, and is the first copper at U7. 29.2 mm on In5, 5.2 mm on F.Cu, two vias.

*`+5V`, the remaining feeder.* The net has 28 pads and its only copper is the 2.5 mm joining U13.3, C200.1 and C268.1; KiCad counts 25 unconnected on it, from 27. **The feeder must arrive at C268.1's west side**, so the 4.7 uF is ahead of the 100 nF and the pin. Room is kept: on a scratch copy two 0.45 mm vias at (158.90, 110.44) and (158.90, 111.12) with a 0.6 mm track passed DRC, clear of the In5 sense line at x 158.0; they are not on the board. The feeder carries about 0.75 A at the rail's 1.34 A, taking 90 % efficiency, an estimate. Where it comes from and on which layer is the global `+5V` work.

*Output capacitance, startup and stability: not qualified.* Nothing changed: C198 and C199, 2 x 22 uF, at L4.1, and 103.4 uF on the net with the bank and selector capacitors (`ref/power-budget.md`). SLVSDG1C 8.2.2.5 gives 10 to 47 uF, and Table 4 checks 2.2 uH only up to 2 x 22 uF at this output voltage. Soft start is 900 us typical (section 6.5), so charging 103.4 uF to 2.5 V takes about 0.29 A on top of the load, from a typical value, not a limit. Open for the bench: loop stability and load-step response at 103.4 uF, start-up into the real load, and a selector joining J19's or J20's capacitors to a running rail. No capacitor value was changed to anticipate the answer.

*U14 and U16.* The same tool placed their cells the same way: C203 and C206 beside the VIN pin with `+5V` at the SW end, C269 and C270 further off. They are untouched and will need the same treatment when their cells are routed.

*Checks.* On a copy first, then transferred. HEAD against the commit board: 33 tracks and 9 vias added, nothing removed; one added `+2V5` segment, the sense extension; four footprints' position lines changed and nothing else in them; every kept track and via byte-identical; header, stackup, rules, nets, groups and drawings byte-identical; four zones refilled with no outline or setting changed. Tracks 2734 to 2767, vias 638 to 647, ratsnest 1092 to 1080. **0 DRC errors, 0 parity with H4 at either position**, the 313 warnings identical item for item, no dangling copper, fresh refills byte-identical. By KiCad on each net alone: `SW+2V5` 0 of 2, `FB+2V5` 0 of 3, `EN_2V5` 0 of 3 unconnected, `+2V5` still 0 of 27; GND 271 to 266, exactly the five grounds; RGMII, management, LINK, SDRAM, PSRAM, MDI, other PHY nets and `+1V8_IO` still 0, HDMI 15, `+3V3` 120, `+1V0` 40. Each plane one piece. Plane copper lost to the four new signal vias and, on In3, to the five GND vias was compared with every accepted track on the layers that use each plane: none runs within 0.3 mm of an opening. Reservation stress copy: nothing on these nets or in the cell and U7 corner. `gate.py --strict`, `check_stackup.py`, `check_erc.py` and `alloc.py --check` pass; `check_positions.py` reports the four moves and nothing else; `check_connector_rework.py` and `audit_easyeda.py` stop where they did. Manual silkscreen untouched; the four parts carry their own outlines with them. The owner's H4 move, its fills and `.prl` remain uncommitted. Evidence: `~/freyja-review/u13-2026-11-05/`, image `images/u13.png`. Nothing has been measured on hardware.

**U14 regulator cell routed (2026-11-05).** `SW+1V8_IO` and `FB+1V8_IO` are complete, U14's ground and its three local passives' grounds reach the planes, and U14.3, U14.5, C203 and C269 form the local `+5V` input node. All 40 `+1V8_IO` pads still reach L5.1. **`+5V` is still unrouted and `+1V8` behind FB1 is a separate chunk, so the rail is still not powered in layout terms.**

*Part and pins.* TLV62569PDRLR, SOT-563, as U13: SLVSDG1C section 5 gives 1 FB, 2 GND, 3 VIN, 4 SW, 5 EN, 6 PG, and the board's pads carry `FB+1V8_IO`, GND, `+5V`, `SW+1V8_IO`, `+5V` and nothing. EN is tied to VIN in `tools/design.py`, so U14 is always on; that is now copper, pin 5 to pin 3 under the package, and no supervisor enable was added. R61 100k and R62 49.9k set 1.802 V; no value changed.

*Why it is not U13's arrangement.* The same defect was here: C203 beside the VIN pin with its `+5V` pad at the SW pin, C269 4.4 mm away beyond the divider. But J2's courtyard ends 5.3 mm north of the pin row, J55 is 2.5 mm west and the board edge 1.9 mm east, and four parts in a column need 5.7 mm. So the 4.7 uF stands beside the 100 nF and not behind it, and the divider is turned upright.

| Part | From | To | Moved, mm |
|---|---|---|---:|
| C203, 100 nF | (252.384, 112.743), 90 | (254.234, 111.188), 0 | 2.42 |
| C269, 4.7 uF | (253.684, 107.643), 0 | (252.450, 111.020), 90 | 3.60 |
| R61, 100k | (253.684, 109.243), 180 | (254.509, 108.418), 90 | 1.17 |
| R62, 49.9k | (253.684, 110.843), 0 | (252.900, 107.940), 270 | 3.01 |

R61 turns about its pad 1, which stays at (254.509, 109.243) on the accepted sense stub, so no `+1V8_IO` copper was added or changed. U14, L5, C201, C202 and every other footprint stayed; locks and the `island U14` group are unchanged.

*Layout, against SLVSDG1C 10.1 and Figure 21.*
- **Input loop.** C203 lies across pins 3 and 2, 0.25 mm from them, `+5V` west and GND east, as at U13. C269's `+5V` pad is 0.55 mm west of C203's, level with it and with pin 3, joined by a 0.5 mm strap; its GND pad joins C203's by a 0.4 mm strap 0.9 mm north of the `+5V` one. Both capacitors are across VIN and GND by F.Cu alone, with no via in either loop; the 4.7 uF's loop is about 2 mm2 against about 1.5 at U13, which is what the missing row costs.
- **Ground.** Vias at both ends of that strap: (255.45, 111.19) and (255.50, 110.60) beside C203.2, 1 mm from pin 2, and (251.55, 110.245) beside C269.2. R62.2 has its own via. All four keep 0.5 mm or more from the accepted In5 sense line, which crosses under the cell.
- **SW.** Pin 4 straight into L5.2: 0.28 mm wide, 0.99 mm, no via.
- **FB.** F.Cu only, no via and no new plane opening: pin 1 east, north at x 256.0 between the accepted sense via and the board edge, 0.45 mm and 0.81 mm from them, over In1 all the way, to R61.2 and R62.1 side by side at the top. 8.7 mm in all. No added FB copper is nearer the SW copper than 1.37 mm; U14's own pin 1 pad is 1.15 mm from pin 4.
- **Sense.** The accepted In5 line from C201, its via and its stub are byte-identical, and the stub still ends on R61.1's centre.

*`+5V`, the remaining feeder.* KiCad counts 22 unconnected on the net, from 25: this cell's four pads are joined. **A practical entry is C269.1's west side**, between C269 and J55, so the 4.7 uF is ahead of the 100 nF and the pin. On a scratch copy two 0.45 mm vias at (251.60, 111.80) and (251.60, 112.50) with a 0.6 mm track passed DRC, clear of the In5 sense line; they are not on the board. The feeder carries about 0.12 A at the budget's 0.308 A and about 0.60 A at the 1.508 A used for sizing the rail, taking 90 % efficiency: estimates.

*Output capacitance, startup and stability: not qualified.* Nothing changed: C201 and C202, 2 x 22 uF, at L5.1; 113.0 uF directly on `+1V8_IO` and 63.5 uF more on `+1V8` behind FB1 (`ref/power-budget.md`). SLVSDG1C 8.2.2.5 gives 10 to 47 uF and Table 4 checks 2.2 uH up to 2 x 22 uF. At the 900 us typical soft start, 113 uF to 1.8 V is about 0.23 A of charging, 0.35 A with the capacitance behind the bead: from a typical value, not a limit. Open for the bench: loop stability and load step at 113 uF, the bead and its 63.5 uF as a second filter stage, start-up with the FPGA's VCCAUX on this rail, and a selector joining J19's or J20's capacitors to a running rail. No simulation was started and no value changed.

*Silkscreen.* U14's `1V8 SUPPLY` label was placed by hand across the cell at y 108.0 to 109.5 and was not moved. It crossed R61 before; it now crosses R61 and R62, so the cell has two more silk overlaps, 11 from 9. Where it should sit is the owner's call.

*Warning counts and KiCad's limit.* KiCad lists at most 199 violations of one type, 499 for clearance and unconnected items, and `silk_overlap` is at 199 on this board, so that list is a sample: whole-board comparisons of it, including "313 warnings identical" in the U13 entry, could not have shown a change. From here the capped type is compared in a cropped copy of the cell, where nothing is near the limit. U14's window: `silk_overlap` 9 to 11, the three R61 and R62 segments against the label new and one old R61 one gone; `silk_over_copper` 6 and 6. U13's window, rechecked the same way: 10 and 5 before and after, identical item for item, so that entry's conclusion stands. Every other warning type is below the limit and identical item for item on the whole board.

*Placement tool, for its next cleanup.* The TLV62569 profile in `tools/island_profiles.yaml` puts the input capacitor "on the VIN flank". On the DRL package VIN and GND are neighbours in one pin row, so that rule leaves the 100 nF beside the package with `+5V` at the SW pin, and the 4.7 uF, matched by no rule, lands wherever the ring puts it. It did this at U13, U14 and U16. The rule should place the capacitor across pins 3 and 2, outward from the row, and the larger one behind or beside it. **U16's cell still has the defect**; nothing was regenerated and no other island was touched. Separately, `tools/island_profiles.yaml` does not load at present: `yaml.safe_load` stops at an unquoted colon in the TPS25942A `source:` line (line 178 now, 173 before the comment added here), so `islands.py` cannot read any profile until that line is quoted. That was so before this chunk and is left for the same cleanup; the comment added at the TLV62569 rule changes nothing the parser sees.

*Checks.* On a copy first, then transferred. HEAD against the commit board: 24 tracks and 4 vias added, nothing removed, no `+1V8_IO` copper added; four footprints differ only in position and angle lines, with R61's and R62's two silkscreen lines changing order in the file; every kept track and via byte-identical; header, stackup, rules, nets, groups and drawings byte-identical; one zone refilled, In3, with no outline or setting changed. Tracks 2767 to 2791, vias 647 to 651, ratsnest 1080 to 1070. **0 DRC errors, 0 parity with H4 at either position**, no dangling copper, fresh refills byte-identical. By KiCad on each net alone: `SW+1V8_IO` 0 of 2, `FB+1V8_IO` 0 of 3, `+1V8_IO` still 0 of 40 unconnected; GND 266 to 262, exactly U14.2, C203.2, C269.2 and R62.2; `+2V5` 0 of 27, RGMII, management, LINK, SDRAM, PSRAM, MDI and other PHY nets still 0, HDMI 15, `+3V3` 120, `+1V0` 40. Each plane one piece. The only plane copper lost is on In3 around the four GND vias; no accepted track on a layer that uses In3 runs within 0.3 mm of it. Reservation stress copy: 33 errors before and after, none on these nets or in this area. `gate.py --strict`, `check_stackup.py`, `check_erc.py` and `alloc.py --check` pass; `check_positions.py` reports the four moves and nothing else; `check_connector_rework.py` and `audit_easyeda.py` stop where they did. No KiCad process or lock file existed when the board was transferred. The owner's H4 move, its fills and `.prl` remain uncommitted. Evidence: `~/freyja-review/u14-2026-11-05/`, image `images/u14.png`. Nothing has been measured on hardware.

**U16 regulator cell routed (2026-11-05).** *Superseded the same day: U16, its cell and `+1V2_MGT` were removed when the GTP supplies were grounded, entry below.* `SW+1V2_MGT`, `FB+1V2_MGT` and `EN_1V2` are complete, the cell's seven grounds reach the planes, U16.3, C206 and C270 form the local `+5V` input node, and L6.1, C204, C205 and R63.1 the local output node. This is the last of the three TLV62569 cells with the placement defect. **`+5V` is still unrouted and `+1V2_MGT` goes no further than C205, so the rail is not powered and feeds nothing in layout terms.**

*Part, pins and references.* TLV62569PDRLR, SOT-563, as U13 and U14: SLVSDG1C section 5 gives 1 FB, 2 GND, 3 VIN, 4 SW, 5 EN, 6 PG, and the board's pads carry `FB+1V2_MGT`, GND, `+5V`, `SW+1V2_MGT`, `EN_1V2` and nothing. The netlist has `SW+1V2_MGT` on L6.2 and U16.4; `FB+1V2_MGT` on R63.2, R64.1 and U16.1; `EN_1V2` on R93.1, U16.5 and U7.26 (GPIO25). L6, C204/C205 (2 x 22 uF), C206 (100 nF), C270 (4.7 uF), R63/R64 (100k/100k, 1.200 V) and R93 (100k pull-down) are the parts `tools/design.py` gives this cell. No value, and nothing about the enable, changed.

*The space.* The cell had no copper at all. MK66's courtyard is 5.4 mm north of the pin row, J54 0.9 mm east and the board edge 3.8 mm west of the package, so neither U13's column of four nor U14's coordinates fit. The divider was already in one column with its FB pads under pin 1, the owner's amendment, and stays so.

| Part | From | To | Moved, mm |
|---|---|---|---:|
| C206, 100 nF | (159.847, 154.555), 90 | (161.097, 152.900), 0 | 2.07 |
| C270, 4.7 uF | (158.155, 154.095), 90 | (159.347, 153.000), 90 | 1.62 |
| R63, 100k | (160.548, 152.655), 0 | (160.548, 150.600), 0 | 2.06 |
| R64, 100k | (160.548, 151.055), 180 | (160.548, 149.000), 180 | 2.06 |
| R93, 100k | (160.548, 149.455), 180 | (157.950, 149.700), 90 | 2.61 |

U16, L6, C204, C205 and every other footprint stayed; locks and the `island U16` group are unchanged.

*Layout, against SLVSDG1C 10.1 and Figure 21.*
- **Input loop.** C206 lies across pins 3 and 2, 0.25 mm from them, `+5V` west and GND east. C270 stands beside it with its `+5V` pad level with pin 3, 0.9 mm from it, joined straight to the pin and to C206.1; its GND pad joins C206.2 by a 0.4 mm strap. Both capacitors are across VIN and GND by F.Cu alone, with no via in either loop.
- **Ground.** Two vias on that strap, at (160.40, 152.00) and (161.26, 152.00), 1.7 mm from pin 2 centre to centre. C204.2 and C205.2 share a 0.5 mm bar with vias at (161.20, 162.555) and (161.20, 164.83). R64.2 and R93.2 share one via at (158.87, 148.95), apart from the power return.
- **SW.** Pin 4 straight into L6.2: 0.28 mm wide, 0.93 mm, no via.
- **FB.** F.Cu only, 5.8 mm, no via and no plane opening: pin 1 east, north at x 162.25 between the cell and J54's pads, 0.32 mm from C206's GND pad and 0.53 mm from J54 pin 2, also ground, into R63.2 and R64.1 one above the other. In1 is continuous under all of it. No added FB copper is nearer the SW copper than 1.37 mm.
- **Output and sense.** A 1.4 and 1.0 mm bar from L6.1 through C204.1 to C205.1, as at U13. The sense leaves C204.1 by a via under C204, runs 14.4 mm on In5 between In4 and In6 up the east side under the FB track, and reaches R63.1 through a via under R63: it takes the output capacitor's voltage and carries no load current. The west side was kept for the enable and the feeder.
- **EN.** Pin 5 has 0.30 mm to L6's SW pad, so it leaves north under the package and west between pins 3 and 4, then runs up the west side to R93.1, which stands upright in the north-west corner. A via there takes it to In2: north along the west edge at x 157.75, 0.79 mm inside the board edge, past U13's cell, then east on the lane at y 117.318, above `EN_2V5` on In5, to a via inside U7's pad ring at (185.359, 117.318) and pin 26. 61.5 mm on In2, 9.3 mm on F.Cu, two vias. It passes the accepted `+2V5` sense via at (158.3, 120.3) with 0.25 mm. The enable is still U7's GPIO25 with R93 to ground and nothing else.

*`+5V`, the remaining feeder.* KiCad counts 20 unconnected on the net, from 22. **A practical entry is C270.1's west side**: on a scratch copy two 0.45 mm vias at (158.40, 153.30) and (158.40, 153.95) with a 0.6 mm track passed DRC between the capacitor and the enable track; they are not on the board. The feeder carries about 0.04 A at the budget's 0.150 A, an estimate. With U13's entry at C268.1 and U14's at C269.1, all three cells now name one.

*`+1V2_MGT`, onward.* 27 of the net's 31 pads are still open: U1's twelve MGTAVTT balls (AD15, AD7, AE10, AE12, AE14, AE8, B10, B12, B14, B8, C15, C7), C380 to C391 and C393, R35.2 and R89.2. **The connection point is the south end of the output bar at C205.1**, (159.298, 163.655): on the scratch copy two vias at (158.95, 164.85) and (159.65, 164.85) below it passed DRC, clear of MK67. Distribution itself is a separate chunk.

*Output capacitance, startup and stability: not qualified.* Nothing changed: C204 and C205, 2 x 22 uF, at L6.1, 49.9 uF on the net (`ref/power-budget.md`), against SLVSDG1C 8.2.2.5's 10 to 47 uF; Table 4 checks 2.2 uH up to 2 x 22 uF at this voltage. At the 900 us typical soft start that is about 0.07 A of charging. The margin over TI's range is small here, but stability, load step and start-up with the transceiver supply still belong on the bench, and no simulation was started.

*Warnings, compared locally.* `silk_overlap` is at KiCad's 199 limit on the whole board, so it was compared in a cropped copy of the cell: 22 before and after, and `silk_over_copper` 7 and 7, identical item for item. U16's `1V2 SUPPLY TRANSCEIVERS` label and MK66's `KEY B` cross the divider column as before; neither was moved, and U14's label was left for the owner's review. Every other warning type is below the limit and identical item for item on the whole board.

*Checks.* On a copy first, then transferred. HEAD against the commit board: 44 tracks and 9 vias added, nothing removed; five footprints differ only in position and angle lines; every kept track and via byte-identical; header, stackup, rules, nets, groups and drawings byte-identical; four zones refilled with no outline or setting changed. Tracks 2791 to 2835, vias 651 to 660, ratsnest 1070 to 1053. **0 DRC errors, 0 parity with H4 at either position**, no dangling copper, fresh refills byte-identical. By KiCad on each net alone: `SW+1V2_MGT` 0 of 2, `FB+1V2_MGT` 0 of 3, `EN_1V2` 0 of 3 unconnected; GND 262 to 255, exactly the seven grounds; `+2V5` 0 of 27, `+1V8_IO` 0 of 40, RGMII, management, LINK, SDRAM, PSRAM, MDI and other PHY nets still 0, HDMI 15, `+3V3` 120, `+1V0` 40. Each plane one piece. Plane openings: the four signal vias on In1, In4 and In6 and all nine on In3; no accepted track on a layer that uses the plane runs within 0.3 mm of any. The comparison now restores the holes in each saved fill first, because the zero-width slits of a saved fill move when holes are added and leave zero-area slivers; 20 pieces under 0.0001 mm2 remain and are left out as numerical residue. Reservation stress copy: nothing on these nets, the west strip or the lane. `gate.py --strict`, `check_stackup.py`, `check_erc.py` and `alloc.py --check` pass; `check_positions.py` reports the five moves and nothing else; `check_connector_rework.py` and `audit_easyeda.py` stop where they did. No generator was run. No KiCad process or lock file existed when the board was transferred. The owner's H4 move, its fills and `.prl` remain uncommitted. Evidence: `~/freyja-review/u16-2026-11-05/`, image `images/u16.png`. Nothing has been measured on hardware.

**Island profile file repaired (2026-11-05).** `tools/island_profiles.yaml` loads again. Two `source:` values held an unquoted colon followed by a space, which YAML reads as a second mapping: the TPS25942A entry, the one known, and behind it the TPS564201 entry, which the parser could not reach until the first was fixed. Both values are now double-quoted and nothing else in the file changed: 2 of 342 lines. Through its normal consumer, `islands.load_profiles`, the file gives 13 profiles; each of the two parsed `source` strings equals the text that was on its line, character for character; all 13 `source` values match their own lines; and `profile_for` selects a profile for the fitted parts of every family, none left unused. No placement was run, no island regenerated, and the board, schematic and netlist are untouched. The TLV62569 rule's placement defect recorded above is not repaired by this: it is a rule that parses and places wrongly.

**`+1V8` behind FB1 routed, with `MON_1V8` (2026-11-05).** All 18 pads of `+1V8` reach FB1.2 by copper and all 3 pads of `MON_1V8` are joined. The eleven capacitor grounds reach In1, In4 and In6. `+1V8` and `+1V8_IO` meet only through FB1. **`+5V` is still unrouted, so U14 has no input and the rail is not powered in layout terms.**

*Endpoints, from the netlist and the board, which agree.* `+1V8`, 18: FB1.2; U1 J9, L9, N9, R9, U9 (VCCAUX) and M12 (VCCADC_0); C319 (47 uF), C320 to C322 (4.7 uF), C323 to C327 (0.47 uF), C328 (100 nF); R87.1. `MON_1V8`, 3: R87.2 (1k), C229.1 (100 nF), U7.55 (GPIO44/ADC4). C319 to C328 are the expected decouplers. Neither net had any copper.

*Route.*

| Section | Layer, width | Notes |
|---|---|---|
| FB1.2 to two vias at (196.2, 130.0), (197.2, 130.0) | F.Cu 0.6 mm | east of the `+1V8_IO` feed on B.Cu at x 195.4; FB1.1's copper untouched |
| Trunk east, y 127.89, x 197.5 to 218.8 | In5, 1.0 mm, 23.5 mm | between In4 and In6, in the lane between the two reserved via rows of the north capacitors. B.Cu is closed here by the `+1V8_IO` feeds at x 195.4 and 198.92 and the `+2V5` lane at x 210 to 213 |
| Two vias at (217.8, 127.89), (218.8, 127.89), then trunk to (223.8, 131.575) | B.Cu, 1.0 mm | 35 um copper from here on |
| Two necks between the reserved power vias of C383, C374, C384 | B.Cu, 0.45 mm, 5.5 and 2.0 mm | the only way into the ball field that keeps those reservations |
| NE block of the ball field to U9's via (217.7, 142.34) | B.Cu, 1.0 mm | that block is unconnected balls; no signal lane is taken |
| Ladder on the VCCAUX column | B.Cu, 0.22 mm | lanes on ball columns 9 and 8, y 142.84 to 150.84, each dogbone via tied to both; M12 by the row lane y 147.84 |
| Six dogbones | F.Cu, 0.2 mm | the reserved sites, all six used |
| East capacitors C323 to C326 | B.Cu 1.0 mm to one via at (228.35, 140.865), then F.Cu 0.3 mm between the capacitor pads | J5A and J5B take 48 slot signals east across this strip, so nothing here runs north to south on an inner layer or B.Cu |
| South capacitors C319 to C321 | B.Cu 0.22 mm lane, 14.2 mm, from J9's via down ball column 10 to C321's reserved via; F.Cu 0.5 mm bar joining the three | |
| South-west capacitors C322, C327, C328 | 32 mm from C320: F.Cu and In2, 0.15 to 0.3 mm, four vias; F.Cu bars between the three | see below |
| Monitor branch to R87.1 | In2 0.2 mm, 19.9 mm, from the FB1 vias; one via beside R87 | its own branch: it reads the bead's output and carries no load current |
| `MON_1V8` | F.Cu: R87.2 to C229.1 0.25 mm; one 0.1 mm lane to U7.55 | lane on the south side of the gap between C121 and C226, so one more lane, pin 56 `MON_1V0`, still fits |

Reservations: of the 13 reserved `+1V8` via sites, 7 are used (six balls, C321). The other six capacitors join on F.Cu and need none. All 7 reserved GND sites are used; C321's already held an accepted GND via, which now serves it. C323, C324, C325 and C229 had none and got measured new sites. No footprint moved.

*Sizing and DC drop.* Load from `ref/power-budget.md`: 0.180 A for VCCAUX and VCCADC, an estimate, inside the 0.308 A board load on U14. Copper at 25 C, 1.72e-8 ohm m; F.Cu and B.Cu 35 um, **In2 and In5 15.2 um, the board's own stackup value**; vias 0.20 mm drill with an assumed 18 um barrel; FB1 at its 50 mohm maximum. Regulated point C201.1, as for `+1V8_IO`.

| Case | To FB1.1 | Bead | FB1.2 to worst ball | Worst ball, total |
|---|---:|---:|---:|---:|
| Board load 0.308 A, 0.18 A shared by the six balls | 8.6 mV | 9.0 mV | 7.8 mV (M12) | **25.4 mV** |
| Same, all 0.18 A drawn at J9, a bound | 8.6 | 9.0 | 9.3 | 26.8 mV |
| Both selectors also exporting 0.6 A at 1.8 V, 1.508 A | 24.8 | 9.0 | 7.8 | 41.6 mV |
| Same, all at J9 | 24.8 | 9.0 | 9.3 | 43.1 mV |

FB1.2 to each ball alone is 41 to 54 mohm. The most loaded new track is the In5 trunk, 0.18 A against 0.65 A for 10 C by IPC-2221; the lanes carry at most 0.09 A against 0.80 A; the two FB1 vias share the 0.18 A.

Against the FPGA limits, VCCAUX and VCCADC 1.71 to 1.89 V: U14's feedback is 0.588 to 0.612 V (SLVSDG1C, electrical characteristics) and R61, R62 are 1 % parts (C25803, C23184), so the output is 1.743 to 1.863 V, 1.802 V nominal.
- Nominal: 1.777 V at the worst ball at board load, 1.761 V with both selectors exporting.
- Regulator at its low limit, board load: **1.718 V, 8 mV above the minimum** (6 mV with all the current at J9).
- Regulator at its low limit, both selectors exporting: **1.701 V, 9 mV below the minimum.** The new copper is 7.8 mV of that; with none at all it would still be 1.709 V. This case is set by the regulator tolerance, the existing `+1V8_IO` trunk and the bead, not by this chunk.
- High side: 1.863 V at no load, 27 mV under the maximum.

Ripple, load regulation, temperature and transients are not in these figures. No simulation was started and no value changed.

*The three south-west capacitors: connected, but poorly placed for this job.* C322, C327 and C328 stand 17 to 23 mm from the balls, behind the capacitor field. No single layer reaches them. The link found is the shortest over four layers and is long and narrow by necessity; it carries no DC load. Its vias at (203.45, 170.69), (205.0, 164.84) and (211.5, 170.84) are the only pockets in that field, each about 0.02 mm over the clearance rule. C327's reserved via site was not used: it sits 0.012 mm over the rule from `SDRAM_A2` and beside `LINK_P_TXD_P`; the cluster's via is at (199.95, 167.65) instead, 0.165 mm over. A route through U1's south-west quadrant has cleaner via sites but takes a B.Cu lane from the unrouted slot A to D balls, so it was not used. These three add little at the balls from where they stand; moving them next to C319 to C321 or to the east column would be the owner's decision.

*Plane openings under accepted routes.* 17 new `+1V8` vias open In1, In3, In4 and In6; the 10 new GND vias open In3 only. For every accepted track on a layer that uses an opened plane and passes within 1.2 mm, 94 pairs, the centre line and both edges were sampled before and after: **no accepted track lost copper beneath it.** Openings do come close to track edges, all at the south-west link: (205.0, 164.84) is 0.017 mm from `SDRAM_A4` on In2 and `SDRAM_A5` on In5 and 0.222 mm from `LINK_Q_TXD_N`; (211.5, 170.84) is 0.018 mm from `PHY_RXD1` and 0.108 mm from `PHY_RXC` on B.Cu; (203.45, 170.69) is 0.108 mm from `SDRAM_A6` and 0.171 mm from `LINK_Q_TXD_P`. The six ball vias are 0.265 mm from the SDRAM DQ dogbones beside them, as every dogbone on this lattice is. Return current was not simulated.

*What this closes for later routing.* In5 along y 127.89 from x 197 to 219 is now a wall as B.Cu already is at y 122 to 126: signals crossing north to south there have In2 and F.Cu. `CFG_M0`, `CFG_M1`, `CFG_M2` must cross the NE block on In2 or In5. `JTAG_TCK`, `JTAG_TMS` and `CFG_CCLK` lose B.Cu eastward past ball column 10, rows y 151.84 to 159.69. The remaining 577 reserved vias and 577 stubs were added to a scratch copy of the commit board: 31 DRC errors, every one already present at HEAD, none naming the new copper. The current list is `~/freyja-review/1v8-2026-11-05/tmp/res_no1v8.json`.

*A correction that reaches back.* Earlier DC figures in this file took inner copper as 17.5 um. The stackup in the board says 15.2 um, so drops on In2 and In5 in those entries are up to 15 % low: the `+2V5` bus and the regulator sense lines. They were not recomputed here.

*Checks.* On a copy first, then transferred. HEAD against the commit board: 122 tracks and 27 vias added (`+1V8` 106 and 17, GND 11 and 10, `MON_1V8` 5), nothing removed; no footprint text changed; every kept track and via byte-identical; header, stackup, rules, nets, groups and drawings byte-identical; five zones refilled with no outline or setting changed. Tracks 2835 to 2957, vias 660 to 687, ratsnest 1053 to 1023. **0 DRC errors, 0 parity with H4 at either position**, no dangling copper, fresh refills byte-identical. By KiCad on each net alone: `+1V8` 0 of 18 and `MON_1V8` 0 of 3 unconnected; GND 255 to 244, exactly the eleven grounds; `+2V5`, `+1V8_IO`, RGMII, management, LINK, SDRAM, PSRAM, MDI and other PHY nets still 0, HDMI 15, `+3V3` 120, `+1V0` 40. Each plane one piece. In the DC model, with FB1 taken out no `+1V8` pad reaches `+1V8_IO`, and R87.1 sits at FB1.2's potential. `silk_overlap` is at KiCad's 199 limit, so warnings were compared in six cropped windows around the new F.Cu copper: identical item for item; every other warning type is below the limit and identical on the whole board. Strict gate electrical and mechanical PASS, stackup guard and ERC pass on the live tree. Evidence: `~/freyja-review/1v8-2026-11-05/`. Nothing measured on hardware.

**U14 feedback divider changed for the `+1V8` voltage window (2026-11-05).** R61 is now 102k and R62 49.9k, both 0.1 %, 25 ppm/C (YAGEO RT0603BRD07102KL, C861068; RT0603BRD0749K9L, C705780; same 0603 lands, both in stock for SMT, both extended lines). The setpoint moves from 1.802 V to 1.826 V. No footprint moved and no copper changed.

*The undervoltage, reproduced.* With 15.2 um inner copper the worst VCCAUX ball is 41.6 mV below C201.1 at 25 C with both selectors exporting, 51.5 mV at 85 C copper with the bead at 50 mohm scaled the same way. The entry above set that against 1.743 V and gave 1.701 V. Three things were missing there: TI's 0.588 to 0.612 V is a 25 C figure at 5 V in (SLVSDG1C 6.5), the 1 % resistors drift 100 ppm/C each, and the regulator's output falls about 0.2 % at 1.5 A (Figure 10, typical). With those, the fitted divider gives 1.727 to 1.880 V at the regulator over 60 K, and the worst ball is at 1.698 V at 25 C and **1.673 V at 85 C, 37 mV under the 1.71 V minimum.**

*Loads checked.* On `+1V8`: the five VCCAUX balls and VCCADC, 0.18 A by estimate. On `+1V8_IO`: bank 13 VCCO 0.10 A, four PSRAM 0.028 A, U9 and U10 VCCA, the pull-ups and the divider itself, microamps. Through J19 and J20 at the 1.8 V position: banks 15 and 34, 0.10 A each, and the PIN V export of 0.50 A each, the allowance in `tools/budget.py`, **kept as it is.** That is 1.508 A against U14's 2 A.

*Options, every static term stacked.* Feedback at its limit with 0.1 % allowed for temperature and line (Figure 3 is typical only; TI gives no limit over temperature), both resistors adverse in tolerance and in drift over 60 K, 0.2 % load regulation, copper and bead at 85 C, both exports at full allowance.

| Divider | Regulator, V | Worst VCCAUX ball, full load, 85 C | To 1.71 V | Highest output, light load | Left under 1.89 V |
|---|---|---:|---:|---:|---:|
| 100k / 49.9k, 1 %, 100 ppm/C (was fitted) | 1.727 to 1.880 | 1.673 V | **-37 mV** | 1.880 V | 10 mV |
| 100k / 49.9k, 0.1 %, 25 ppm/C | 1.759 to 1.846 | 1.704 V | -6 mV | 1.846 V | 44 mV |
| 102k / 49.9k, 1 %, 100 ppm/C | 1.750 to 1.906 | 1.695 V | -15 mV | 1.906 V | -16 mV |
| **102k / 49.9k, 0.1 %, 25 ppm/C (fitted now)** | 1.782 to 1.871 | 1.727 V | **+17 mV** | 1.871 V | **19 mV** |

Tighter resistors alone do not reach the minimum, and the higher setpoint with 1 % parts breaks the maximum. Together they are better than the old pair on both sides. 102k / 49.9k is the lowest E96 ratio above the old one; the next step down is the old ratio. The E192 values in between that were looked up, 101k and 49.3k, are in the JLCPCB library only at 0.5 %.

*Every load with the new pair, both selectors exporting, 85 C.* VCCAUX and VCCADC balls 1.727 V (1.725 V if J9 drew all of it) against 1.71 V. Bank 13 VCCO balls 1.748 V. PSRAM pin 8 1.735 V against 1.62 V. U9 and U10 VCCA 1.732 V against 1.65 V. At the selector pins, J19.5 1.725 V and J20.5 1.746 V: the `VCCIO_1` and `VCCIO_2` copper beyond them is not routed, so banks 15 and 34 and the export pins have those figures less whatever that copper, U23 and U24 and the slot fuses drop. At board load and 25 C the worst ball is at 1.762 V, 52 mV over. Nominal parts: 1.781 V at the worst ball with both selectors exporting, at 25 C.

*Maximum at light load: the limiting inequality.* Highest regulator output plus the power-save rise must stay at or under 1.89 V at the VCCAUX balls, so the rise, ripple and overshoot together have **19 mV** (10 mV with the old pair). Below about 0.45 A the TLV62569 runs in power-save mode and the output sits above nominal (SLVSDG1C 7.3.1). Figure 10 shows about 43 mV at 0.1 A and less with TI's 10 uF, the same in millivolts at 1.8 V and 3.3 V out, which is what a fixed charge per pulse into the output capacitor gives, about 0.77 uC. Scaled to this board that is 4 mV on the whole 113 uF, 12 mV on C201 and C202 alone with tolerance and bias, 18 mV at TI's -50 % derating of those two: **1 to 15 mV left by estimate, and 24 mV over if the rise were the full 43 mV.** That scaling is an estimate, not a datasheet figure. The unconfigured FPGA is exactly this light-load case. PSRAM, 1.98 V, keeps 91 mV or more; bank 13 runs to 3.465 V.

*Left for ripple and transients.* 17 mV at the bottom, 19 mV at the top less the power-save rise. Switching ripple in PWM is about 1 mV on these capacitors by calculation. Load steps were not analysed and nothing was simulated. **Bench check that closes this: `+1V8` at C319 with the FPGA unconfigured, and with both selectors loaded.** If the light-load figure comes out too high, the smallest next step is more capacitance at L5, which lowers the rise, before any change to the supply arrangement.

*Not examined.* The same tolerance stack applies to U13 and U16; their windows were not opened here.

*Applied.* `tools/design.py` holds the pair and both part numbers, with the reason. Regenerated from it: `kicad/power.kicad_sch` (R61 and R62 move within U14's group, because the generator orders parts by value), `kicad/odin.net`, `ref/bom-jlcpcb.csv`, `ref/parts-guide.md`, and `ref/jlc-stock.md` against the 2026-11-05 library snapshot, which also brings in R208 to R213. The board was synchronised with `load_pcb.py` on a copy with `update_silkscreen.py` held back: R61 and R62 differ in value, description and a hidden part-number field, nothing else; positions, pads, nets and every track, via and fill are byte-identical. `ref/power-budget.md` does not change: the budget works from nominal rail voltages. 0 DRC errors, 0 parity with H4 at either position; strict gate electrical and mechanical PASS, stackup guard and ERC pass on the live tree. Evidence: `~/freyja-review/1v8-margin-2026-11-05/`, `scripts/vbudget.py` and `reports/vbudget.txt`. Nothing measured on hardware.

**C322, C327 and C328 moved to the east side (2026-11-05).** The three distant `+1V8` capacitors now stand in a row above C323, beside the east capacitors, and the south-west link described two entries above is gone with its four vias. Values and footprints are unchanged; no other part moved.

| Part | From | To | Moved, mm |
|---|---|---|---:|
| C322, 4.7 uF | (200.468, 169.865), -90 | (235.310, 136.120), 90 | 48.5 |
| C327, 0.47 uF | (202.528, 169.645), -90 | (237.160, 136.295), 90 | 48.1 |
| C328, 100 nF | (197.678, 165.125), -90 | (238.490, 136.590), 90 | 49.8 |

*Why there.* The land east of C307 and above C323, x 234.3 to 241.1, y 130.0 to 137.9, held no part, copper, silkscreen or reservation, and it adjoins `+1V8` copper that reaches the balls by the 1.0 mm B.Cu trunk. Nearer land is taken: the column at x 227 to 230 by the other rails' capacitors, and the gap of about 1.9 mm beside R1, R2, R3, R5 and R19 was left for those resistors' supply vias. No wider search was run.

*Connections, before and after.* Shortest copper path from pad 1 to a ball, the narrowest track on it and its DC resistance at 25 C:

| Part | Before | After | GND stub, before and after |
|---|---|---|---|
| C322 to the nearest VCCAUX ball | 51.4 mm, 0.15 mm, 183 mohm | **22.0 mm, 0.20 mm, 18 mohm** | 0.90, 0.97 mm |
| C327 to the nearest VCCAUX ball | 53.4 mm, 0.15 mm, 185 mohm | **23.8 mm, 0.20 mm, 20 mohm** | 0.88, 0.92 mm |
| C328 to M12, VCCADC | 63.7 mm, 0.15 mm, 207 mohm | **33.5 mm, 0.20 mm, 40 mohm** | 0.59, 0.81 mm |

The 0.20 mm that remains is the ball's own dogbone. C328 is still 33.5 mm of copper from M12: M12 is an inner ball, 11 mm from the nearest edge of the ball field, and every capacitor is on F.Cu. C323 gains as well, 23 to 16 mohm.

*Copper.* The three pad 1s lie on one line at y 137.07: an F.Cu bar along them, 0.5 and 0.4 mm, and a 0.5 mm link 1.6 mm straight down from C322.1 into C323.1. One new via at (233.9, 138.6), in the bar between C324.1 and C323.1, and a 0.9 mm B.Cu lane, 6.5 mm, east to west from the east via at (228.35, 140.865): the five capacitors here no longer depend on the 0.3 mm F.Cu link alone. Each ground pad has its own via, at (235.31, 134.2), (237.16, 134.6) and (238.49, 135.3). Removed, and nothing else: the 27 tracks and 4 vias of the south-west link and its bars, and the three old ground stubs with their vias. Tracks 2957 to 2935, vias 687 to 684.

*Reference planes.* The link's vias at (203.45, 170.69), (205.0, 164.84) and (211.5, 170.84), whose openings came within 0.02 mm of `SDRAM_A4`, `SDRAM_A5` and `PHY_RXD1` and within 0.17 to 0.22 mm of two LINK Q tracks, no longer exist: each GND plane gains 1.78 mm2 there. The one new `+1V8` via opens In1, In3, In4 and In6 under its own bar; no accepted signal track runs within 1.2 mm of any new via.

*Checks.* On a copy first, then transferred. The three footprints differ only in position and angle lines; group `island U1`, locks, values and every other footprint unchanged; every kept track and via byte-identical; header, stackup, rules, nets and drawings byte-identical; five zones refilled with no outline or setting changed. **0 DRC errors, 0 parity with H4 at either position**, no dangling copper, fresh refills byte-identical. By KiCad on each net alone: `+1V8` 0 of 18, `MON_1V8` 0 of 3, `+1V8_IO` 0 of 40 unconnected; GND 244 and 244; every other group unchanged. Eleven of eleven capacitor grounds on In1, In4 and In6. The DC model still has `+1V8` in one piece behind FB1 and the drops to the balls are unchanged, 25.4 and 41.6 mV, so the voltage window in the entry above stands. The 577 reserved vias and stubs on a scratch copy give 32 errors before and after, none on the new copper; one pair of reserved SDRAM stubs at (201.2, 144.84) is reported in place of another. Warnings compared in cropped windows around the new site, the old site and U14: identical, and no silkscreen lies in the new site. Strict gate electrical and mechanical PASS, stackup guard and ERC pass on the live tree. `ref/islands/U1.svg` still draws the three at their old sites; no placement tool was run. Close-up: `~/freyja-review/1v8-margin-2026-11-05/images/close_up.png`. Nothing measured on hardware.

**Forced-PWM regulators checked for U14 and U16; no part changed (2026-11-05).** Neither candidate could be fitted without an assumption its datasheet does not support, and for U16 no part with a 2 % reference closes the window. The comparison, the three budgets and the corrections recommended are below. Board, schematic, netlist and BOM are untouched.

| | TLV62569PDRLR, fitted | TLV62569APDRLR | TPS62A0569APDRLR |
|---|---|---|---|
| Datasheet | SLVSDG1C | SLVSE95B | SLUSG30A, December 2025, revised February 2026 |
| Pins 1 to 6, SOT-563 | FB, GND, VIN, SW, EN, PG | the same | the same |
| Unused PG | open, as fitted | leave floating | float or GND |
| Light load | power save below about 0.45 A | forced PWM | forced PWM |
| Feedback, guaranteed | 0.588 to 0.612 V at 25 C, 5 V in | 0.588 to 0.612 V at 25 C, 5 V in | 588 to 612 mV, "PWM mode, 25 C" |
| Feedback over temperature | typical curve only, Figure 3 | typical curve only, Figure 2 | **no table line and no curve**; the front page says "2% feedback accuracy including temperature effects" |
| Switching frequency | 1.5 MHz | 1.5 MHz | 2.4 MHz |
| Inductors in TI's matrix | 1 and 2.2 uH | **1 uH only** | 0.47, 1 and 2.2 uH; effective 0.4 to 2.5 uH |
| Output capacitance | 10 to 47 uF | 22 to 47 uF | 10 to 90 uF effective; matrix up to 4 x 22 uF |
| Soft start, prebiased start | 0.9 ms, yes | 0.9 ms, yes | 0.6 ms, yes |
| Output discharge when off | none | none | active, 68 mA typical through SW |
| Current limit | 2.5 A minimum | 3 A minimum | 2.3 A minimum, 3.4 A typical; hiccup after 32 limit cycles, also during start-up |
| Junction to ambient | 146 C/W | 143 C/W | 157 C/W |
| Input current with no load | 35 uA | about 6.5 mA at 5 V, Figure 7, typical | not given for forced PWM |
| JLCPCB, 2026-11-05 snapshot | C398364, 6107 | C398366, 8836 | C54220884, 168 |

*What the candidates do and do not give.* Both remove the power-save rise, the one term in U14's maximum that no datasheet bounds. Neither gives a guaranteed feedback limit over temperature: the TPS62A0569's only feedback line is conditioned "PWM mode, 25 C", so its front-page claim is not in its own table. The TLV62569A is proven by TI only with 1 uH and 22 to 47 uF; L4, L5 and L6 are 2.2 uH (SRN4018-2R2M), so it would need three inductors changed as well. The TPS62A0569A lists 2.2 uH: "++" with 22 or 2 x 22 uF from 1.2 V, "+" at 1.8 V and above, which TI defines as stable on its board but possibly needing adaptation.

*U14, every load, with the divider fitted in 1eb285c.* Stacked as before: feedback limit, 0.1 % taken once for temperature and line, 0.1 % resistors with drift over 60 K, 0.2 % load regulation at 1.5 A, copper and bead at 85 C. The minimum is the same for all three parts:

| Case, 85 C | Worst VCCAUX ball | Bank 13 | PSRAM | U9, U10 | J19.5, and what is left to 1.71 V for the copper to bank 15 | J20.5, and to bank 34 |
|---|---:|---:|---:|---:|---|---|
| Both selectors exporting, 1.508 A | 1.727 V, +17 mV | 1.748 V | 1.735 V | 1.732 V | 1.725 V, **15 mV** | 1.746 V, 36 mV |
| J19 alone exporting, 0.908 A | 1.732 V, +22 mV | 1.753 V | 1.740 V | 1.736 V | 1.730 V, 20 mV | 1.780 V, 70 mV |
| J20 alone exporting, 0.908 A | 1.750 V, +40 mV | 1.769 V | 1.771 V | 1.771 V | 1.771 V, 61 mV | 1.750 V, 40 mV |
| Board load, 0.308 A | 1.751 V, +41 mV | 1.770 V | 1.772 V | 1.772 V | 1.772 V, 62 mV | 1.782 V, 72 mV |

J19 exporting alone costs almost as much as both, because its current shares the north trunk with the feed to FB1. **The `VCCIO_1` copper from J19 to bank 15 has 15 mV to spend at 0.1 A of bank current with both selectors exporting, and `VCCIO_2` 36 mV; the export pins have no stated tolerance and take whatever U23, U24 and the slot fuses leave.** That allowance is now a routing requirement for those two nets.

The maximum at light load is 1.871 V at the regulator, 19 mV under 1.89 V. With the fitted part the power-save rise comes out of that, 4 to 18 mV by the earlier estimate and not bounded. With either forced-PWM part the whole 19 mV is left for ripple and overshoot, 21 mV if the TPS62A0569's front page is taken at its word. So a forced-PWM part does clearly improve U14's maximum.

*Why U14 was not changed.* The node carries 113 uF directly and 63.5 uF more behind FB1 (`ref/power-budget.md`). That is above the TPS62A0569A's 90 uF effective maximum and above its matrix; TI asks for a Bode plot outside it. The fitted part is further outside its own 10 to 47 uF, which is already listed for the bench, so the swap would narrow the gap, not close it. Its light-load input current is not published, and U14 runs in recovery on a weak USB port, where the TLV62569A's figure would be 6.5 mA. JLCPCB holds 168 pieces of a part released in December 2025. **Recommended: TPS62A0569APDRLR in U14's existing pads, with the divider as fitted, once loop stability with this capacitance and its no-load input current have been measured on a board or TI's evaluation module.** No copper changes for it. Removing FPGA decoupling to fit a regulator's range is not proposed.

*U16, before onward routing.* *Closed by removal: the GTP supplies are grounded and U16 is gone, entry below.* MGTAVTT is 1.17 to 1.23 V, absolute maximum 1.32 V (DS181 v1.27.1, Tables 1 and 2). The transceivers are unused but powered in rev A and the rail is not routed beyond C205.

| U16 arrangement | Regulator output | To 1.17 V, before any copper drop | To 1.23 V |
|---|---|---:|---:|
| Fitted: TLV62569PDRLR, 100k / 100k at 1 % | 1.156 to 1.245 V | **-14 mV** | **-15 mV**, before a power-save rise of 10 to 18 mV by estimate |
| Fitted part, 100k / 100k at 0.1 %, 25 ppm/C | 1.172 to 1.228 V | +1.9 mV | +1.7 mV, before the same rise |
| Forced PWM, divider at 1 % | 1.156 to 1.245 V | -14 mV | -15 mV |
| Forced PWM, divider at 0.1 % | 1.172 to 1.228 V | +1.9 mV | +1.7 mV |

The 2 % reference alone takes 48 of the 60 mV window. With a 0.1 % divider and forced PWM, 3.6 mV in all is left for copper drop, ripple and the temperature term no datasheet guarantees, so **none of the three parts closes MGTAVTT's window, and forced PWM is not the correction for U16.** At 0.15 A that 3.6 mV is 24 mohm of copper with nothing left over. The limiting inequality is reference tolerance against a 2.5 % window. Two ways on, for the owner: accept the rail outside the recommended window while the transceivers are unused, in which case only the 1.32 V absolute maximum matters and the fitted arrangement is 75 mV under it before the rise; or, before the transceivers are used, a regulator with 1 % or better feedback accuracy over temperature, a 0.1 % divider and its sense taken at the load, which is a different part and outside this comparison. Either way the copper is the same: route `+1V2_MGT` for the lowest practical resistance. A 0.1 % divider at R63 and R64 (100k, C122538) would bring the regulator itself inside the window and costs one extended line; it was not fitted because by itself it leaves the rise in place.

*U13, brief check: it fails too.* Bank 16 VCCO is 2.5 V at 5 %, 2.375 to 2.625 V (DS181 Table 2, note 5); the limits of U30's DVDD_RG are not in the repository. Drops recomputed with 15.2 um inner copper: 27.6 mV at the worst bank 16 ball with both selectors at 2.5 V, 34.2 mV at 85 C; J20.3 48.7 and 60.2 mV, where the earlier entry had 48.6 mV with 17.5 um.

| U13 divider | Regulator | Bank 16 balls, board load, 85 C | Both selectors at 2.5 V, 85 C | Maximum, before the power-save rise |
|---|---|---:|---:|---:|
| Fitted: 100k / 31.6k at 1 % | 2.388 to 2.614 V | 2.377 V, +2 mV | **2.349 V, -26 mV** | 2.614 V, 11 mV left |
| 100k / 31.6k at 0.1 %, 25 ppm/C | 2.437 to 2.561 V | 2.426 V, +51 mV | 2.398 V, +23 mV | 2.561 V, 64 mV left |

**Recommended for U13: the same two values at 0.1 %, 25 ppm/C: 100k C122538 and 31.6k C705766 (RT0603BRD0731K6L, 3818 in stock), no setpoint change.** With both selectors exporting, J20.3 is then at 2.372 V, 3 mV under 2.375 V before the `VCCIO_2` copper, so banks at 2.5 V under full export stay marginal; 102k / 31.6k would add 37 mV there and still leave 25 mV at the top. Not applied: U13 was to be checked, not changed.

*What only hardware can settle.* None of this is transient closure. Left for measurement: U14's output at C319 with the FPGA unconfigured and with each selector loaded; loop stability and load-step response of whichever part drives 113 uF plus 63.5 uF behind the bead; U14's start-up into that capacitance; the feedback voltage over temperature, which no table here guarantees; ripple at the VCCAUX balls. Datasheets used are in `~/freyja-review/regcheck-2026-11-05/datasheets/`, the arithmetic in `scripts/regbudget.py` and `reports/regbudget.txt` there.

**U13 feedback divider changed to 0.1 % parts (2026-11-05).** R59 is 100k and R60 31.6k as before, now both 0.1 % and 25 ppm/C: YAGEO RT0603BRD07100KL, C122538, and RT0603BRD0731K6L, C705766, on the same 0603 lands. The nominal setpoint stays 2.4987 V. No footprint moved and no copper changed. JLCPCB lists both as extended SMT parts; the 2026-11-05 snapshot has 1 363 538 and 3818 in stock, and its process field for C705766 is empty, so `ref/jlc-stock.md` prints "?" there, while JLCPCB's own part page on the same day says SMT with 2337 in stock.

*Limits, with what is guaranteed kept apart from what is typical.* Guaranteed: VFB 0.588 to 0.612 V at 5 V in and 25 C (SLVSDG1C 6.5), the resistors' tolerance and temperature coefficient, both adverse over 60 K, and bank 16's 2.375 to 2.625 V (DS181 v1.27.1 Table 2, note 5). Typical and taken once each: 0.1 % of VFB for temperature and line (Figure 3; TI gives no limit over temperature) and 0.2 % load regulation in the 1.34 A case (Figure 10). Estimates: the loads of `tools/budget.py`, 18 um via barrels, copper at 85 C. Drops are from the saved copper with 15.2 um inner layers.

| 85 C, lowest output | Before, 1 % | Now, 0.1 % |
|---|---:|---:|
| Regulator, lowest / nominal / highest | 2.388 / 2.499 / 2.614 V | 2.437 / 2.499 / 2.561 V |
| The same from the guaranteed terms alone | 2.390 to 2.612 V | 2.440 to 2.558 V |
| Bank 16 balls, board load 0.14 A | 2.377 V, +2 mV | 2.426 V, **+51 mV** |
| Bank 16 balls, J19 alone exporting at 2.5 V | 2.370 V, -5 mV | 2.419 V, +44 mV |
| Bank 16 balls, J20 alone exporting | 2.360 V, -15 mV | 2.410 V, +35 mV |
| Bank 16 balls, both exporting, 1.34 A | 2.349 V, **-26 mV** | 2.398 V, **+23 mV** |
| U30 pin 28 (DVDD_RG), both exporting | 2.357 V | 2.407 V |
| J19.3, J19 alone / both exporting | 2.349 / 2.337 V | 2.398 / 2.386 V, 23 / 11 mV left for the `VCCIO_1` copper |
| J20.3, J20 alone / both exporting | 2.334 / 2.323 V | 2.384 / 2.372 V, 9 mV left / **3 mV short** |
| Highest output, light load | 2.614 V, 11 mV under 2.625 V | 2.561 V, **64 mV** under |

*What it does not close.* *The J20 feed was lowered in resistance the same day, entry "`+2V5` feeder to J20" below: J20.3 is now 23 mV above the minimum in this case.* With both selectors at 2.5 V and both exports at the full allowance of `tools/budget.py`, kept as it is, J20.3 stands at 2.372 V before any `VCCIO_2` copper, so bank 34 at 2.5 V under full export from both selectors is still below 2.375 V, and with J20 alone that copper has 9 mV. J20.3 is the far end of the rail, 60 mV below the regulator at 85 C with both exporting. A setpoint step to 102k / 31.6k would add 37 mV and leave 25 mV at the top; it was not taken, the nominal setpoint was to stay. So the `VCCIO_2` routing inherits no allowance at 2.5 V: J20's 2.5 V position under full export from both selectors stays outside the recommended window unless the `+2V5` feed to J20.3 is lowered in resistance or the setpoint is raised. The power-save rise at light load is not bounded by the datasheet; by the same scaling as for U14 it is 5 to 18 mV, against 64 mV of room. The limits of U30's DVDD_RG are not in the repository. Nothing here is transient closure: loop stability into 103 uF, start-up and ripple remain for hardware.

*Applied.* `tools/design.py` holds the pair and both part numbers, with the reason. Regenerated from it: `kicad/power.kicad_sch` (R59 and R91 change places within U13's group, because the generator orders parts by value), `kicad/odin.net`, `ref/bom-jlcpcb.csv`, `ref/parts-guide.md` and `ref/jlc-stock.md`. The board was synchronised with `load_pcb.py` on a copy with `update_silkscreen.py` held back: R59 and R60 differ in value, description and a hidden part-number field, nothing else; `check_positions.py` reports 0 moved of 561; pads, nets and every track, via and fill are byte-identical, fresh refills too. `ref/power-budget.md` does not change. `gateware/rgmii1000/README.md` named the old 1 % bound in one sentence; it now gives this one, and its conclusion, that no ball goes as low as the Slow corner's 2.375 V at DC, holds with 23 mV where it did not before. 0 DRC errors, 0 parity with H4 at either position; the sixteen tracked net groups unchanged, `+2V5` 27 of 27; strict gate electrical and mechanical PASS, stackup guard and ERC pass on the live tree. Evidence: `~/freyja-review/u13-divider-2026-11-05/`, `scripts/u13budget.py` and `reports/u13budget.txt`. Nothing measured on hardware.

**Unused GTP supplies grounded: AMD's fully-unused connection transferred (2026-11-05). Rev A cannot use either GTP group.** Reviewed as a copy (`~/freyja-review/gtp-unused-2026-11-05/repo`, on top of the U13 divider commit), then transferred to the live board, schematic, netlist and generated files as reviewed, with the 24 ground dogbones kept. Quads 213 and 216, supply groups G10 and G11, have MGTAVCC, MGTAVTT and MGTRREF on GND; the regulator, filter, calibration resistors, capacitors and copper a transceiver would need are not on the board, so no bitstream can use one on rev A.

*The correction.* Earlier entries and `tools/design.py` say the unused transceivers must stay powered, citing UG482 Tables 5-5 and 5-6. Those tables are for a power supply group or a quad that is partly used. UG482 v1.9 (December 19, 2016), "Unused GTP Quad Power Supply Group", Table 5-4, p. 223: if none of the quads in a power supply group is used, MGTAVCC to GND, MGTAVTT to GND, MGTREFCLKP/N float, MGTRXP/N to GND, MGTTXP/N float, MGTRREF to GND; its note says this is the only case in which MGTRREF may be grounded. Table 5-2, p. 220: on the XC7A100T-FGG676 quad MGT213 is group G10 and MGT216 is group G11, one quad each.

*Balls, from AMD's `xc7a100tfgg676pkg.txt` and matching the board's U1 pad for pad, 64 in all.*

| | G10, quad 213 | G11, quad 216 | Now |
|---|---|---|---|
| MGTAVCC | AA10 AA12 AC9 AC11 AC13 | D9 D11 D13 F10 F12 | GND, was `+1V0_MGT` |
| MGTAVTT | AD7 AD15 AE8 AE10 AE12 AE14 | B8 B10 B12 B14 C7 C15 | GND, was `+1V2_MGT` |
| MGTRREF | AF15 | A15 | GND, was through R89, R35 to `+1V2_MGT` |
| MGTPRXP/N | AC12 AC14 AD12 AD14 AE11 AE13 AF11 AF13 | A11 A13 B11 B13 C12 C14 D12 D14 | GND, as before |
| MGTPTXP/N | AC8 AC10 AD8 AD10 AE7 AE9 AF7 AF9 | A7 A9 B7 B9 C8 C10 D8 D10 | no net, as before |
| MGTREFCLK0/1 P/N | AA11 AA13 AB11 AB13 | E11 E13 F11 F13 | no net, as before |

*Both groups qualify.* Hardware: every TX and reference-clock ball of both quads has no net and no copper; there is no transceiver connector and no reference oscillator; the four nets `+1V0_MGT`, `+1V2_MGT`, `MGTRREF` and `MGTRREF_213` reach only U1 and the parts listed below. Gateware: `gateware/gate`, `rgmii1000` and `sdram100` instantiate no GTPE2_COMMON, GTPE2_CHANNEL or IBUFDS_GTE2 and no constraint file names an MGT pin, so no reference-clock buffer feeds the fabric; the fabric clock is X4 on bank 14. `EN_1V2` reaches only U7 pin 26, R93 and U16. Nothing else on the board draws from either supply. **What it costs: with these balls on GND neither quad can be used on this board, whatever the bitstream.**

*Affected parts, 37, all removed; nothing added.*

| Circuit | Parts |
|---|---|
| U16 cell, `+5V` to `+1V2_MGT` | U16, L6, R63, R64, R93 (enable pull-down), C204, C205, C206, C270 |
| MGTAVCC filter off `+1V0` | L9, C224 |
| Calibration resistors | R35 (quad 216), R89 (quad 213) |
| MGTAVCC capacitors | C370 to C379 (100 nF), C392 (4.7 uF) |
| MGTAVTT capacitors | C380 to C391 (100 nF), C393 (4.7 uF) |

The sources are disconnected, not renamed: L9 was the only path from `+1V0` to the MGTAVCC balls and U16 the only source of `+1V2_MGT`; both are gone with every part on those nets, and U16's `+5V` input node goes with it. U7 pin 26 (GPIO25) is left without a net; firmware outside this repository must no longer expect an enable there. Designators are consumed, not reused: every other part keeps its reference, value, footprint, nets and position (`scripts/cmp_design.py`, `check_positions.py` 0 moved of 524). 557 parts become 520.

*Copper.* Removed: the 44 tracks and 9 vias of U16's cell, which is all the copper those nets had: `+1V2_MGT` 9 tracks and 2 vias, `EN_1V2` 13 and 2 including the In2 run to U7 pin 26, `FB+1V2_MGT` 5, `SW+1V2_MGT` 1, the cell's `+5V` node 5, its ground stubs 11 with 5 vias. Added: 24 ground dogbones, 0.2 mm on F.Cu, each to a 0.45 / 0.20 mm via at the site already reserved for that ball, for the 22 supply and 2 MGTRREF balls; the 16 RX balls had theirs. Tracks 2935 to 2915, vias 684 to 699. Each of the 40 grounded balls has a via standing in solid fill on In1, In4 and In6. `+5V` now has 25 pads, `+1V0` 40. Island U16's group with its frame and notes on User.Comments is gone; island U1 keeps 114 of 142 items. No silkscreen drawing was touched.

*Planes.* Each GND plane gains 1.81 mm2. In3 gains 1.31 mm2 of `+3V3` net and its `+1V0` island loses 7.81 mm2 to 20 of the new clearance holes and stays one piece. No accepted track lost plane copper beneath it (centre line and both edges sampled). Thirteen of the In3 openings lie beside accepted In2 tracks, 0.057 mm from the track edge at the nearest: PHY_TXC passes four of them, PHY_MDC, PHY_MDIO, SDRAM_DQ2, DQ4 and DQ6 the others. In2 is 0.10 mm from In1, which is untouched there, and 0.21 mm from In3. The same sites were reserved for supply vias, which would have opened In1 as well. Not modelled. The dogbones were kept on review. *In1 beneath those tracks, checked on transfer:* the 11 In2 segments of the six nets that pass a new via were sampled along their whole length on the centre line, both edges and 0.2 mm beyond each edge, 13455 samples; the samples without In1 copper are the same 889 before and after. Under the tracks themselves In1 is missing only inside each track's own via opening, 0.38 mm at the last segment of `PHY_TXC`, `PHY_MDC` and `PHY_MDIO`, as before; the nearest of those is 0.79 mm from a new via. All 24 new vias stand in In1 copper, so the reference directly above these tracks is continuous past every new via (`reports/in1.txt`, `images/closeup_in1.png` in the transfer folder).

*Budget, `ref/power-budget.md`.* `+1V0` 2.150 A to 2.050 A, U15 at 51 % of 4 A; `+1V2_MGT`, 0.150 A, and U16 gone; `+5V` 0.840 A to 0.773 A, U11 at 26 % of 3 A; light mode 7.32 W to 6.99 W, full 18.92 W to 18.59 W, the same sources fit as before. U15's output loses the 10.4 uF behind L9; U16's capacitor row, one of the bench qualification items, goes. BOM: the `100 1%` and 1 uH lines disappear, six lines shorten.

*What this closes.* U16's MGTAVTT window, which no part with a 2 % reference could meet (entry above), the onward `+1V2_MGT` and `+1V0_MGT` routing, the `+5V` entry at C270.1, and 74 fanout reservations: 24 used here and 50 that belonged to the removed capacitors, leaving 503. The capacitor rows north and south of U1 and U16's cell are free land.

*Checks.* On the copy first, then on the live tree after transfer. The review baseline was verified before anything moved: the live tree was the reviewed base commit plus this document, the committed board the U13 divider board byte for byte, the working board that board with the owner's H4 position and its fills. Fresh refill byte-identical, with H4 at either position. 0 DRC errors, 0 parity, no dangling copper; ERC pass; stackup guard pass; strict gate electrical and mechanical PASS, 520 of 520 parts described. KiCad drops the seven empty nets on save and renumbers the rest, so the board file differs on many lines; compared with net names in place of numbers, every kept track, via, footprint, zone outline, drawing and setting is identical to the board before, U1 differs in 24 pad nets and U7 in one, and the same holds between the two working boards with H4 moved. Completed groups unchanged: `+1V8` 18 of 18, `MON_1V8` 3 of 3, `+2V5` 27 of 27, `+1V8_IO` 40 of 40, RGMII, management, LINK, SDRAM, PSRAM, MDI and the other PHY nets complete, HDMI 15 open as before; GND open items 244 to 219, the removed capacitors' pads. All 40 grounded balls have a dogbone and a via in solid fill on In1, In4 and In6. Warnings: none new on the whole board or in three cropped windows; eight gone, all at removed parts; silkscreen drawings and every kept footprint's text identical. Stress copy with the remaining 503 reservations: 30 errors, all among the 32 present before. `check_connector_rework.py` and `audit_easyeda.py` report the same findings as before.

*Reconciled on transfer.* `kicad/odin.kicad_pro`: the three island colour classes of the vanished nets (`ISL27_U16_5V_TO_1V2_MGT`, `ISL59_GTP_CALIBRATION`, `ISL60_GTP_CALIBRATION`) and their five patterns removed by text, every other class, pattern and setting identical; `island_classes.py --netclasses` was not run, it would renumber and recolour every island. `floorplan.md`, `ref/island-layouts.md`, `ref/jlcpcb-import-checklist.md`: U16 and the transceiver rails taken out, the TLV62569 row and profile kept for U13 and U14. City plan: U16's entry removed from `ref/city/plan.yaml` and `ref/city/city.svg` by hand, and from `DOORS`, the district box and U6's shelf anchor in `tools/city.py`; `city.py` was not run, the other entries and the district frames stand as planned. `tools/placement.py` loses the three group anchors and `ref/floorplan.svg` was redrawn from it, six lines fewer. `ref/islands/U16.svg` deleted. `ref/ballmap.md` states that neither quad can be used. Left as they are: the unused `+1V0_MGT` and `+1V2_MGT` power symbols in `kicad/odin.kicad_sym` (removing them means running `gen_kicad.py`, which rewrites the imported library), `ref/islands/U1.svg`, which already drew old capacitor sites, and older entries of this document, which describe U16 as it stood. No placement tool, `update_silkscreen.py` or board generator was run.

Evidence: `~/freyja-review/gtp-unused-2026-11-05/` for the review: `datasheets/` (UG482 v1.9, the package file), `scripts/edit_sources.py`, `stage_a.py`, `verify_gtp.py`, `reports/`, `review.patch`. `~/freyja-review/gtp-transfer-2026-11-05/` for the transfer: `scripts/reconcile.py`, `final.sh`, `in1.py`, `reports/`, `final/commit.kicad_pcb` and `working.kicad_pcb`, `images/before_after.png`, `images/closeup_in1.png`. Nothing measured on hardware.

**`+2V5` feeder to J20 lowered in resistance (2026-11-05).** With both selectors exporting at 2.5 V and the copper at 85 C, J20.3 was 61.2 mV below C198.1 and is now 34.0 mV. At the regulator's low limit that is 2.398 V, 23 mV above bank 34's 2.375 V, where it stood 4 mV under. The divider, the setpoint, the loads and the export allowances are as they were. No footprint moved, no signal copper changed, and the regulator cell with its output bar, its four vias and the sense takeoff at C198.1 is untouched. **This is a DC result on copper; nothing was measured.**

*Reproduced first.* Same model and terms as the divider entry above: copper from the saved board, 35 um outer and 15.2 um inner as in the board's stackup, via barrels 18 um on a 0.20 mm drill (assumed) over the stackup's depths, 85 C, loads from `tools/budget.py`. It returns that entry's 60.2 mV. One correction: the In5 hop under the `+1V8_IO` trunk at x 240 was three overlapping tracks, 0.5, 1.0 and 0.5 mm, which the model counted as 2.0 mm of copper; they are 1.1 mm. Counted as that, J20.3 was 61.2 mV down, 2.371 V, 4 mV under. No other section had overlapping parallel tracks, and the new copper has none.

| Section of J20's path, both exporting, 85 C | Before, mV | After, mV | What changed |
|---|---:|---:|---|
| Cell output bar and its four vias | 3.7 | 3.5 | nothing; the current shares differently below |
| West neck through the J53 / J3A pins, 1.34 A | 12.9 | 5.2 | three lanes on B.Cu and three on In5 where there were two on B.Cu |
| North trunk, x 173.7 to 239.9 | 17.1 | 8.9 | In5 added under both B.Cu trunks |
| Hop under `+1V8_IO` at x 240 | 2.5 | 0.8 | one 2.2 mm track on In5 and one on In2 |
| Lane through the J5A pins | 4.7 | 2.6 | In2 and In5 lanes under the B.Cu lane |
| East trunk to J20, 64 mm | 16.2 | 10.6 | 1.5 to 2.3 mm on B.Cu |
| Entry between the J20 pins | 4.1 | 2.4 | second 0.4 mm lane |
| **J20.3 below C198.1** | **61.2** | **34.0** | |

*The copper, and what each part gives at J20.3.*

- **West neck, 4.6 mV, and a third lane, 3.0 mV.** Every load on the rail passes here. In5 lanes under the two B.Cu lanes at y 124.94 and 127.51, same widths, same pin gaps. A third lane, 0.5 mm on B.Cu and on In5, between J53 pins 6 and 7 at y 122.4; it leaves the column at y 123.4 and passes C199's ground via at 0.06 mm over the rule. At the cell's four vias one 1.6 mm column on B.Cu and one on In5 replace the 1.2 and 0.55 mm B.Cu pieces. East of J3A a 2.0 mm B.Cu block replaces the 1.0 mm corner, and a 1.5 mm In5 column joins the three In5 lanes to the In5 trunk. Two new vias on the x 172.95 column, at y 124.94 and 127.51.
- **North trunk, 8.5 mV.** 3.1 mm on In5 from x 173.9 to 239.65, y 122.45 to 125.55, under the `+2V5` and `+1V8_IO` B.Cu trunks, where no via could stand already; 2.45 mm for 3.3 mm past the `+1V8_IO` via at (193.92, 125.3). One new via at (174.3, 123.2); at the east end it lands on the hop's existing vias. The B.Cu trunk was not widened: the land north of it is under Y1, U15, U11 and the supervisor's passives, all unrouted and all needing vias there, and `+1V8_IO` is 0.09 mm over the rule to the south.
- **East neck, 3.7 mV.** The hop's three In5 tracks become one of 2.2 mm, the same again on In2 on the same four vias; In2 and In5 lanes under the 0.5 mm B.Cu lane through J5A at y 127.48, one new via at (246.2, 127.478) inside the B.Cu trunk's start.
- **East trunk, 5.6 mV.** 2.3 mm, widened on its east side only, up to the rule against the square pads of J64 and J56; the west edge stays at x 246.75.
- **Entry, 1.8 mV.** A second 0.4 mm B.Cu lane between J20 pins 2 and 4, mirroring the one between 4 and 6.

29 tracks and 4 vias added, 9 tracks removed, each replaced by a wider one in the same place: tracks 2915 to 2935, vias 699 to 703. Most loaded against IPC-2221 at 10 C rise is still the cell's F.Cu bar, 56 %; worst via 0.36 A, from 0.45 A.

| Regulator at its low limit, 85 C | Bank 16 balls | U30 pin 28 | J19.3 | J20.3 |
|---|---|---|---|---|
| Board load, 0.14 A | 2.428 V, +53 mV (was +51) | 2.428 V | | |
| J19 alone at 2.5 V | 2.424 V, +49 mV (+44) | 2.425 V | 2.402 V, +27 mV (+23) | |
| J20 alone at 2.5 V | 2.419 V, +44 mV (+35) | 2.424 V | | 2.407 V, **+32 mV** (+8) |
| Both exporting, 1.34 A | 2.410 V, +35 mV (+23) | 2.415 V (2.407) | 2.393 V, +18 mV (+11) | 2.398 V, **+23 mV** (−4) |

Drops below C198.1 with both exporting: bank 16 34.2 to 21.7 mV, U30 pin 28 25.6 to 17.1 mV, J19.3 45.8 to 38.9 mV, J20.3 61.2 to 34.0 mV. DVDD_RG minus VCCO, which `gateware/rgmii1000` took as −1.0 to +6.9 mV, is now −1.2 to +3.8 mV at 25 C and +4.7 mV at most at 85 C, so its +6.9 mV rows stand as an upper bound; the profile was not re-run.

*Routed 2026-11-06, entry "`VCCIO_1` and `VCCIO_2` routed" below: 4.8 mV to the worst ball.* *Allowance for the unrouted `VCCIO_2`.* The 23 mV at J20.3 is not the bank's margin. Between J20.3 and the bank 34 balls K4, L1, M8, N5, P2 and T6 stand the shunt on pins 3-4 and the `VCCIO_2` copper, and what is then left is all there is for ripple and transients.

- **Shunt, 12 mV assumed.** All 0.6 A passes through it. No shunt is in the BOM; 20 mohm is the usual limit for a 2.54 mm shunt and is an assumption to replace with the chosen part's figure [verify]. *Superseded the same day: a shunt was named in the assembly checklist, a Samtec part is now selected, and 20 mohm for the complete path is a requirement to measure, not a part figure; see the selector hardware entry below.*
- **Copper, 6 mV: the requirement.** From J20.4 to the worst bank 34 ball no more than 60 mohm at 85 C for the bank's 0.1 A, an estimate from `tools/budget.py`. The export branch to U24 must leave at the selector pins and share no copper with the bank feed: 10 mohm shared with the 0.5 A export costs another 5 mV. The balls are 46 to 52 mm north and 21 to 28 mm west of J20. Over 85 mm, 1.5 mm on an outer layer or 3.5 mm on an inner one is 34 mohm, 3.4 mV, which leaves 2.6 mV inside the ball field; 1.0 mm outer is 52 mohm and leaves 0.8 mV, too little for 0.2 mm dogbone lanes. On B.Cu pin 4 is now enclosed by the two `+2V5` lanes, so `VCCIO_2` leaves the pins on F.Cu, where C165 and C166 stand, or on an inner layer.
- **Left after both: 5 mV with both selectors exporting, 14 mV with J20 alone.**

*Ripple and transients, separately.* At the bottom, 5 mV with both exporting and 14 mV with J20 alone, once the shunt and the copper have taken the figures above. At the top nothing changed: 2.561 V, 64 mV under 2.625 V, less a power-save rise the datasheet does not bound, 5 to 18 mV by the earlier scaling. Switching ripple in PWM is about 1 mV on these capacitors by calculation. A load step of the 0.5 A export, loop stability into 103 uF and start-up were not analysed; they remain for hardware, and 5 mV will not hold a load step. **So J20's 2.5 V position under full export from both selectors now holds at DC with a practical allowance for the shunt and the `VCCIO_2` copper; it is not transient closure.**

*J19, checked and not repaired.* J19.3 gains 7 mV from the shared sections and is now the lower of the two pins with both exporting: +18 mV, 6 mV after the same 12 mV shunt, which is the whole of a 60 mohm `VCCIO_1` feed and leaves nothing for ripple. With J19 alone it has +27 mV. Its limit is its own branch, the 1.0 mm B.Cu column x 172.95, 25 mV over 69 mm, and the single 0.4 mm entry lane. That branch is not part of J20's feeder and was left. On a scratch copy, the 1.3 mm that fits between J3A, J3B and the `+1V8_IO` column, with a second entry lane, brings J19.3 to 31.1 mV, 2.401 V, +26 mV with both exporting; not laid out further and not checked by DRC. **Open for the owner: the same repair on J19's branch before `VCCIO_1` is routed.** *Done the same day on B.Cu only, 32.4 mV; see the J19 branch entry below.*

*What still limits J20, if more is wanted.* The path is 57 mohm for the selector's 0.6 A. Each further millivolt needs 1.7 mohm less in the sections that carry 0.6 A or 0.75 mohm less in the west neck and the cell. In order of size: the east trunk, 10.6 mV, held to 2.3 mm by the slot strips' pads on one side and the fuse via column on the other; the north trunk, 8.9 mV, which could only gain on In2 and would then close both inner layers to crossings; the west neck, 5.2 mV; the cell's bar and vias, 3.5 mV, cell copper that was to stay, where doubling the 1.0 mm bar south of C198 would return about 1.3 mV to every load. No setpoint change is proposed. If the bench shows the 5 mV is not enough, 102k / 31.6k remains the next step, +37 mV at the bottom and 27 mV left at the top before the power-save rise.

*What it costs later routing.* In5 is now closed to north-south crossings from x 172.4 to 241.2 along y 122.45 to 125.55, as B.Cu already was: the 30 configuration, JTAG, SD, debug, LED and supervisor nets that have pads on both sides, and the unrouted `+5V`, VSYS, `AUX_RAIL`, `+3V3_EXT` and VCCIO nets, cross on In2 or F.Cu. The fuse band between J5A / J5B and the slot strips keeps its west via column, via centres x 246.16 to 246.38, and loses the east one, x 248.63 to 248.84, from y 128 to 194.5; the three bus ends of each slot's fuses and the capacitor grounds have the west column. In the J53 / J3A field B.Cu and In5 are taken in three pin gaps, y 122.4, 124.94 and 127.51; In2 and F.Cu stay open there for the slot A and B buses. The J5A gap at y 127.48 is taken on B.Cu, In2 and In5; F.Cu stays. Each of these is a separate track or lane and can be taken out alone, at the gain listed above.

*Planes and reservations.* The four new vias stand in `+2V5`'s own B.Cu copper. Each opens In1, In4, In6 and the `+3V3` area of In3 by 0.446 mm2, 1.78 mm2 per plane; every plane stays one piece. No accepted track of another net passes within 1.2 mm of a new via, so no track lost reference beneath it; the only copper over the openings is `+2V5` itself. The In5 copper lies between In4 and In6 and changes neither. The 503 reserved vias and stubs of `res_gtp.json`, added to scratch copies of the board before and after, give 33 errors each, the same but for one pair that names another segment of the same SDRAM stub at the same via; none names `+2V5`.

*Checks.* On a copy first, then transferred. The live board at the start was the committed board with the owner's H4 position and its refill, byte for byte. Against it: only `+2V5` tracks and vias added, exactly the nine planned tracks removed, every kept track, via and footprint byte-identical, net table identical with no renumbering, header, stackup, rules, groups and drawings byte-identical, four zones refilled with no outline or setting changed. **0 DRC errors, 0 parity with H4 at either position**, no dangling copper, fresh refills byte-identical, unconnected count 945 before and after. By KiCad on each net alone: `+2V5` 0 of 27, `+1V8` 0 of 18, `MON_1V8` 0 of 3, `+1V8_IO` 0 of 40, RGMII, management, LINK, SDRAM, PSRAM, MDI and the other PHY nets 0, HDMI 15, GND 219, `+3V3` 120, `+1V0` 39, all as before. Warnings of every type below KiCad's 199 limit identical item for item on the whole board; silkscreen compared in four cropped windows, west neck, north trunk, east neck and J20, identical. Strict gate electrical and mechanical PASS, stackup guard and ERC pass, on the live tree. No KiCad process or lock when the board was transferred. No generator, placement tool or silkscreen updater was run.

Evidence: `~/freyja-review/j20-feeder-2026-11-05/`: `scripts/plan.py` (the copper, by element), `dc.py`, `budget.py`, `sections.py`, `cum.sh`, `final.sh`, `stress.sh`, `reports/`, `final/commit.kicad_pcb` and `working.kicad_pcb`, `images/before_after.png`, `images/close_up.png`.

**Selector hardware for J19 and J20: shunt selected, resistance not specified by any maker, qualification hold kept (2026-11-05).** One Samtec SNT-100-BK-G on each of J19 and J20, hand-fitted; the fitted header, BOOMELE 2.54-2*3P (C65114), stays. No maker publishes a maximum for the complete path between the two PCB pads, so the 20 mohm of the previous entry is not replaced by a part figure: it becomes a requirement to measure, and nothing here is a measured resistance. No schematic, netlist, board or JLCPCB BOM line changed.

*What was already in the repository.* The previous entry said no shunt was in the BOM. The assembly checklist did name one, XFCN F254D-02-PT-B (C501335), as a loose accessory for all selectors, thirteen of them from the time of the twelve 2x3 selectors. It is not in `ref/bom-jlcpcb.csv`, which lists only placed parts.

*What the documents give.*

| | Fitted header, BOOMELE 2.54-2*3P | XFCN F254D-02-PT-B | Samtec SNT-100-BK-G |
|---|---|---|---|
| Source | drawing 2.54-2*NP H2.54 L11.2, 2026-01-16 | drawing rev A1, 2024 | catalogue page F-226, print SNT-100-XX-X-X, reports 105265 and 90410 |
| Post or lead | 0.64 mm square, 5.8 ± 0.2 mm above the body, no tolerance on the section | not stated | accepts 0.64 mm square, 4.32 mm minimum insertion |
| Material, plating | brass, "gold plated", no thickness, no underplate named | phosphor bronze, "matte tin or gold plated over nickel", no thickness | phosphor bronze, 10 µin gold in the contact area; underplate not stated |
| Current | 3 A, no temperature | 3 A, no temperature | 4.3 A per pin at a 30 C rise, 20 % derated, one neighbour powered; 5.0 A derated at 85 C ambient, 4.3 A at 95 C; measured on SNT-100-YW-G with TSW-102-08-L-S, EIA-364-70 |
| Temperature | −55 to 105 C | −40 to 105 C | −55 to 125 C with gold |
| Resistance | "contact resistance ≤ 20 mohm" | "contact resistance 20 mohm max" | none in the catalogue page, the print or either report |
| Method, mate, conditioning for that figure | none | none | not applicable |
| Mating cycles | none | none | none |
| Other | | | vibration 15 g, 10 to 2000 Hz, 4 h per axis, 100 mA: no interruption over 1 µs (report 90410, 1990) |

*Why the Samtec shunt.* Fit on the fitted posts can be checked from documents: 0.64 mm square both sides, 5.6 mm of post at the low limit against 4.32 mm needed, the post shorter than the 6.10 mm body, gold on gold. Its plating is defined and its current is measured at temperature, 5.0 A at 85 C against 0.6 A here. The XFCN drawing leaves tin or gold open, and tin against a gold post is a fretting pair; it stays for J52, which carries a signal. What Samtec does not give is the same thing the others do not give: resistance and mating life. Distributor listings quote 5 mohm for the SNT and 15 mohm for TE and Amphenol shunts; none of those figures is in a maker's document I could open, none names a method, and none is used here.

*The complete path.* Pad, post, interface, shunt bridge, interface, post, pad. The two 20 mohm figures cannot be added into a maximum for it and cannot be read as one either. The header's is for one pin in an unnamed socket. The shunt's is on unnamed pins and does not say whether it is across the shunt or per contact. Neither says initial or after conditioning. Read as one figure per interface, the path is 40 mohm plus metal, 24 mV at 0.6 A, more than either selector has. Read as the whole shunt, 20 mohm plus two posts. By calculation only: the two brass posts are about 1.6 mohm at 20 C, 0.41 mm2 over about 5 mm each; the phosphor-bronze bridge is of the same order; the two gold interfaces cannot be calculated. So a few milliohms is plausible and 20 mohm is not excluded. **There is no supported maximum, initial or after conditioning, and no typical measurement, for any of the three parts.**

*The requirement, from the voltage budget and not from a data sheet.* All 0.6 A of a selector passes through the path: 0.1 A of bank and the 0.5 A PIN V allowance. On the copper as committed, at 85 C, regulator at its low limit, with 6 mV kept for the VCCIO copper to the bank (60 mohm at 0.1 A):

| Position and case | At the selector pin, above the bank's minimum | Left with 10 mohm | 20 mohm | 30 mohm | Path resistance for 0 mV |
|---|---:|---:|---:|---:|---:|
| J20 2.5 V, both exporting | 23.1 mV | 11.1 | 5.1 | −0.9 | 28.6 mohm |
| J20 2.5 V, alone | 31.8 mV | 19.8 | 13.8 | 7.8 | 43.0 mohm |
| J19 2.5 V, both exporting | 18.2 mV | 6.2 | 0.2 | −5.8 | 20.4 mohm |
| J19 2.5 V, alone | 26.9 mV | 14.9 | 8.9 | 2.9 | 34.8 mohm |
| J20 1.8 V, both exporting | 36 mV | 24 | 18 | 12 | 50 mohm |
| J19 1.8 V, both exporting | 15 mV | 3 | −3 | −9 | 15 mohm |

The 1.8 V rows are U14's figures from the forced-PWM entry, not recalculated. **Requirement: 20 mohm or less between the pads at 0.6 A and 85 C, after conditioning.** At that value J20's 2.5 V position keeps 5 mV with both exporting. J19's 2.5 V position keeps nothing until its branch is repaired, the next entry. J19's 1.8 V position with both exporting does not hold at 20 mohm: it needs 15 mohm for nothing left, or less `VCCIO_1` copper than the 6 mV allowed, or more from the `+1V8_IO` branch to J19, which is U14's rail and was not touched.

*Qualification hold.* Before the 2.5 V or 1.8 V position is relied on: four-wire between the pad pairs 1-2, 3-4 and 5-6 on the back of an assembled board, at 0.6 A, as fitted, after 25 moves between positions, and at temperature. 25 is a proposal for the owner to set; no document supports a cycle count. *Set by the owner on 2026-11-09: 25 complete removal and reinsertion cycles, a provisional prototype check, read before and after; the entry "Selector check set" below replaces this sentence and holds the results.* The figure found replaces 20 mohm in the table above. This stands beside U14's hold, which is unchanged: TPS62A0569APDRLR remains recommended and not fitted until loop stability into 113 uF plus 63.5 uF and its no-load input current are measured.

*If the fitted header fails.* Samtec HTSW-103-07-L-D fits the same footprint and position: 0.64 mm square posts on the 2.54 mm grid, 5.84 mm above the body, 2.54 mm tail for a 1.6 mm board, recommended hole 1.02 ± 0.03 mm against 1.05 mm drilled, 10 µin gold on the post, lead-free solderable body. It is the post family and plating the shunt's current rating was measured on. Its posts are phosphor bronze, so more metal resistance than brass, and Samtec gives no resistance for the pair either: the swap would define the plating and not remove the measurement. Not applied.

*Recorded.* `tools/qualified.py`: J19 and J20's entry now carries the header's figures, the shunt, what is not specified and the requirement; `ref/qualified-parts.md` regenerated, one row. `ref/jlcpcb-import-checklist.md`: two SNT-100-BK-G as hand-fitted parts with their position, 3.3 V on pins 1-2 as `ref/freya.xdc` assumes, the J52 shunt reduced to one, the hold, and the stale "twelve 2x3 selectors" row corrected to two. `ref/bom-jlcpcb.csv` is unchanged because JLCPCB does not place a shunt. `tools/roles.py` and the parts guide were left: their text is copied into the schematic and the board's description fields, and neither was to change here. Strict gate electrical and mechanical PASS, stackup guard and ERC pass. Documents and arithmetic in `~/freyja-review/selector-2026-11-05`. Owner's H4 move, its fills and `.prl` left out. Nothing measured on hardware.

**`+2V5` branch to J19 widened on B.Cu (2026-11-05).** With both selectors exporting at 2.5 V and the copper at 85 C, J19.3 was 38.9 mV below C198.1 and is 32.4 mV: 2.400 V at the regulator's low limit, 24.8 mV above bank 15's 2.375 V where it had 18.2 mV. With J19 alone, +33.5 mV where +26.9 mV. Five tracks on B.Cu replace four; no via, no other layer, nothing in the north band. Divider, setpoint, loads and export allowances unchanged; regulator cell, sense takeoff at C198.1, every footprint and all signal copper untouched. J20, bank 16 and U30 are as they were.

*Access first, before any copper.* The missing connections were rebuilt from the saved copper, because KiCad's DRC report stops at 499 unconnected items; 569 on nets without a plane. Capacity is the number of 0.20 mm tracks at 0.15 mm clearance that can cross a wall side by side on a 0.35 mm grid, orthogonal steps only, against every pad, track, via and reserved via, in a window reaching beyond both faces so a corridor that dead-ends behind the wall does not count; zones are closed at their sides. Both simplifications make the figure low.

| North band, y 122.4 to 125.8 (B.Cu trunks, In5 trunk), x | Missing connections crossing | In2 tracks, 3 mm / 7 mm window | F.Cu tracks, 3 mm / 7 mm | Via sites within 7 mm, north / south |
|---|---:|---:|---:|---:|
| 172.4 to 180 | 6 | 15 / 15 | 7 / 7 | 93 / 8 |
| 180 to 190 | 13 | 20 / 18 | 0 / 0 | 44 / 56 |
| 190 to 200 | 12 | 23 / 15 | 10 / 3 | 48 / 41 |
| 200 to 210 | 2 | 20 / 20 | 13 / 8 | 75 / 52 |
| 210 to 220 | 6 | 14 / 15 | 5 / 3 | 76 / 30 |
| 220 to 230 | 4 | 30 / 28 | 6 / 6 | 62 / 79 |
| 230 to 241.2 | 10 | 24 / 24 | 13 / 13 | 103 / 118 |
| Total | 53 | 146 / 135 | 54 / 40 | 501 / 384 |

In2 has room in every zone. Two places are thin and were already so: under U7's passives, x 180 to 190, F.Cu has no crossing and only 2 via sites stand within 3 mm of the north face, so those 13 connections enter In2 further north; and south of the band at x 172.4 to 180, 8 via sites within 7 mm, where U6 and the `+1V8_IO` branches stand, so the six connections there stay on In2 past it. The previous entry said 30 nets with pads on both sides; 53 missing connections cross on a straight line, the eight slot A lines from J3A and the eight slot E lines from J5A among them. Through the J53 and J3A pin field west of x 172.4, 6 cross against 17 on In2 and 6 on F.Cu.

| Wall beside J3A and J3B, x 172.3 to 177.0 (`+2V5` and `+1V8_IO` on B.Cu), y | Missing connections crossing | In2 | In5 | F.Cu |
|---|---:|---:|---:|---:|
| 128 to 140 | 8 | 7 | 7 | 5 |
| 140 to 150 | 8 | 6 | 6 | 0 |
| 150 to 160 | 6 | 5 | 5 | 2 |
| 160 to 170 | 7 | 5 | 5 | 5 |
| 170 to 180 | 6 | 6 | 6 | 2 |
| 180 to 195 | 7 | 17 | 17 | 14 |
| Total | 42 | 46 | 46 | 28 |

Zone by zone neither inner layer carries the crossings alone, 8 against 6 at y 140 to 150 and 7 against 5 at 160 to 170; the slot A to D lines need both, two tracks per pin gap. **So nothing was added on In2 or In5 along J19's column**, which would have taken half of that, and the repair is B.Cu only, where the old column already closed the layer. Capacity through both walls is the same before and after, zone for zone.

*What was applied.*

| Section to J19.3, both exporting, 85 C | Before | After | What changed |
|---|---:|---:|---|
| Cell bar and vias, shared | 3.5 mV | 3.5 mV | untouched |
| West neck through the J53 and J3A pins, shared | 5.3 mV | 5.3 mV | untouched |
| Column east of J3A and J3B, B.Cu | 25.2 mV, 42.0 mohm, 1.0 mm, with its foot | 20.2 mV, 33.7 mohm, 1.21 mm | one track x 172.945, y 124.94 to 194.6 |
| Foot and entry at J19 | 4.9 mV, one 0.4 mm lane | 3.3 mV, foot 1.0 and lanes 2.3 | foot 1.0 mm extended west to x 167.68, second 0.4 mm lane between pins 2 and 4 |
| J19.3 | 38.9 mV | 32.4 mV | |

1.21 mm is the widest straight track the lane takes with 0.2 mm on each side: the J3 pin pads on the west, the sixteen ground vias at x 174.0 to 175.05 down to y 160, and below y 178.2 the `+1V8_IO` column, which stood 0.3 mm from the old track. No via site is lost: none existed between the pads and the old track, and the ground-via line keeps its distance. The two lanes fill the 0.74 mm gaps either side of pin 4 with 0.17 mm to the pads, as the old lane did. Tracks 2935 to 2936.

*Not taken.* Widening to about 2 mm in the two stretches without vias, y 127.6 to 133.6 and 160.3 to 176.5: about 2 mV more, at the cost of the via sites beside R156, R57 and C283 and two reserved ground vias. An inner layer under the column, about 12 mV: see the wall above. The scratch estimate of the previous entry, 1.33 mm and 31.1 mV, did not hold 0.2 mm to the ground via at (174.0, 141.04).

*Every load, 85 C, regulator at its low limit, 2.4370 V and 2.4321 V in the 1.34 A case.*

| Case | Bank 16 balls | U30 pin 28 | J19.3 | J20.3 |
|---|---|---|---|---|
| Board load, 0.14 A | 2.4277 V, +52.7 mV | 2.4283 V | 2.4361 V | 2.4356 V |
| J19 alone exporting, 0.74 A | 2.4239 V, +48.9 mV | 2.4245 V | 2.4085 V, **+33.5 mV** (was +26.9) | 2.4318 V |
| J20 alone exporting, 0.74 A | 2.4191 V, +44.1 mV | 2.4238 V | 2.4324 V | 2.4068 V, +31.8 mV |
| Both exporting, 1.34 A | 2.4104 V, +35.4 mV | 2.4151 V | 2.3998 V, **+24.8 mV** (was +18.2) | 2.3981 V, +23.1 mV |

*Beyond the selector pins, to banks 15 and 34.* In series: the selector, all 0.6 A, and the VCCIO copper, the bank's 0.1 A. With the requirement of the selector entry, 20 mohm between the pads, and 6 mV of copper:

| Bank, case | At the pin | Selector, 20 mohm required | VCCIO copper, 60 mohm allowed | Left at the worst ball | Selector resistance for nothing left |
|---|---:|---:|---:|---:|---:|
| Bank 15 through J19, both exporting | 24.8 mV | 12 mV | 6 mV | **6.8 mV** (was 0.2) | 31.3 mohm |
| Bank 15 through J19, alone | 33.5 mV | 12 mV | 6 mV | 15.5 mV | 45.8 mohm |
| Bank 34 through J20, both exporting | 23.1 mV | 12 mV | 6 mV | 5.1 mV | 28.5 mohm |
| Bank 34 through J20, alone | 31.8 mV | 12 mV | 6 mV | 13.8 mV | 43.0 mohm |

At 10 mohm the two worst rows have 12.8 and 11.1 mV. The selector figure is a requirement awaiting measurement, not a property of the parts.

*Routed 2026-11-06, entry below: 4.9 mV to the worst ball.* *Allowance for the unrouted `VCCIO_1`: 60 mohm, 6 mV, from J19's even pins to the worst of the bank 15 balls F26, G23, H20, J17, K14 and M18.* On the board as it stands a single 1.5 mm track finds a legal way on In2 from pin 6 to the bank's decoupling at C344, 55.3 mm, 51.6 mohm at 85 C, 5.2 mV; at 1.0 mm it is 77 mohm, too much, and at 2.0 mm one width does not pass end to end. That shows a corridor exists today; it is not a route, reserves nothing, and leaves 8 mohm for the fan-in to the six balls, so the real net wants the wide part wider or on two layers. On B.Cu pin 4 is now enclosed, as at J20: `VCCIO_1` leaves the pins on F.Cu, where C163, C164 and U23 stand, or inside. **Split at the selector:** one bar across pins 2, 4 and 6; the export branch leaves its west end at pin 2 for U23, 4 mm away; the bank feeder leaves its east end at pin 6. In every shunt position the 0.5 A then shares no copper with the bank's 0.1 A beyond the pad it enters by. J20 is the mirror image: export from pin 6 east to U24, bank feeder from pin 2 west. 10 mohm shared with the export costs the bank 5 mV.

*Ripple and transients, separately.* What the static budget leaves at the bottom: 6.8 mV for bank 15 and 5.1 mV for bank 34 with both exporting, 15.5 and 13.8 mV with one. At the top nothing changed: 2.561 V, 64 mV under 2.625 V, less a power-save rise the datasheet does not bound, 5 to 18 mV by the earlier scaling. PWM ripple about 1 mV by calculation. A load step of the 0.5 A export, loop stability into 103 uF and start-up are not analysed and remain for hardware. This is DC closure with a practical allowance, conditional on the selector measurement.

*1.8 V position, U14's rail, not touched.* J19.5 still has 15 mV with both exporting: 3 mV short with a 20 mohm selector and 6 mV of copper, closed only by a selector of 15 mohm or less, by less `VCCIO_1` copper, or by the same kind of repair on the `+1V8_IO` column beside this one. U14's hold stands: TPS62A0569APDRLR recommended and not fitted until loop stability and no-load input current are measured.

*Planes and reservations.* No via was added, so no plane lost copper: every plane has the same area and is one piece, and no track's reference changed. With the 503 reservations on scratch copies the board gives 33 errors before and 32 after. The difference is the SDRAM_A5, A6 and A11 stub shorts at (200.7 to 202.2, 143.8 to 145.3), which KiCad reports against a different neighbouring item from run to run; by type and net pair the 19 distinct signatures are identical, none names `+2V5`, and none lies in the window of the column.

*Checks.* On a copy first, then transferred. The live board at the start was the committed board with the owner's H4 position and its refill, byte for byte. Against it: five `+2V5` tracks added, exactly the four planned tracks removed, every kept track, via and footprint byte-identical, net table identical, header, stackup, rules, groups and drawings byte-identical; no zone outline or setting changed, and with H4 at its committed position no fill changed either. **0 DRC errors, 0 parity with H4 at either position**, no dangling copper, fresh refills byte-identical, unconnected count 945 before and after. By KiCad on each net alone: `+2V5` 0 of 27, `+1V8` 0 of 18, `MON_1V8` 0 of 3, `+1V8_IO` 0 of 40, RGMII, management, LINK, SDRAM, PSRAM, MDI and the other PHY nets 0, HDMI 15, GND 219, `+3V3` 120, `+1V0` 39, all as before. Warnings below KiCad's 199 limit identical item for item; silkscreen compared in two cropped windows along the column and at J19, identical. Most loaded track 56 % of IPC-2221 at a 10 C rise, the cell's F.Cu bar, unchanged. Strict gate electrical and mechanical PASS, stackup guard and ERC pass, on the live tree. The PCB editor had the board open while this was prepared; nothing was written until the owner closed it, the lock was gone and the board on disk was still byte-identical to the one validated against. No generator, placement tool or silkscreen updater was run.

*Evidence.* `~/freyja-review/j19-feeder-2026-11-05`: `README.md`, plans, scripts, the commit and working boards, DRC reports, corridor tables, the budget and DC results, `images/before_after.png` and `images/close_up.png`. Owner's H4 move, its fills and `.prl` left out of the commit. Nothing measured on hardware.

**`VCCIO_1` and `VCCIO_2` routed: J19 to bank 15, J20 to bank 34 (2026-11-06).** Both nets are complete: 22 of 22 pads each, both monitor branches 3 of 3, and the 26 associated ground pads reach the planes. With the copper at 85 C and the bank's 0.100 A, the worst ball is **4.9 mV below the selector pin on bank 15 and 4.8 mV on bank 34, against the 6 mV target, in each of the three shunt positions and with the 0.5 A export flowing**. 238 tracks and 64 vias added, nothing removed. No footprint, setpoint, export allowance, selector requirement, regulator cell, sense takeoff, feeder or accepted signal track changed. The switched export nets and the switch controls are not routed.

*Endpoints, from the board and the netlist, same set.*

| | `VCCIO_1`, J19, bank 15 | `VCCIO_2`, J20, bank 34 |
|---|---|---|
| Selector pins 2, 4, 6 | 3 | 3 |
| Selector bulk, 22 uF | C163, C164 | C165, C166 |
| Switch input pins 1, 2 and its 1 uF | U23, C220 | U24, C221 |
| VCCO balls | F26, G23, H20, J17, K14, M18 | K4, L1, M8, N5, P2, T6 |
| Bank capacitors | C342, C343 4.7 uF; C344 to C347 0.47 uF; C367 47 uF | C354, C355 4.7 uF; C356 to C359 0.47 uF; C369 47 uF |
| Monitor resistor, rail side | R198.1 | R199.1 |
| Pads | 22 of 22 | 22 of 22 |
| Monitor branch | `MON_VCCIO_1`: R198.2, C277.1, U7.57, 3 of 3 | `MON_VCCIO_2`: R199.2, C278.1, U7.58, 3 of 3 |
| Grounds | the 10 capacitors, C277, U23 pin 5 and pad 9 | the 10 capacitors, C278, U24 pin 5 and pad 9 |

`GND` goes from 219 to 193 pads without copper, the 26 above. U7's own grounds are not part of this.

*Overview.*

| Section | `VCCIO_1` | `VCCIO_2` |
|---|---|---|
| Bar across pins 2, 4, 6 | 1.6 mm on F.Cu, In2 and In5 | 1.6 mm on F.Cu and In5 |
| Export branch, as far as the switch input | from pin 2, the west end: 1.2 mm F.Cu to C220.1, 0.5 mm to U23 pins 1 and 2 | from pin 6, the east end: 1.5 mm F.Cu north and east round R73, 0.5 mm to U24 pins 1 and 2; C221.1 by a 0.3 mm track between C276's pads |
| Bank feeder leaves | pin 6, the east end | pin 2, the west end |
| Past the existing trunks | F.Cu 2.0 mm at x 173.9 between J3B/J19 and J7/J57, over the `+2V5` and `+1V8_IO` columns; three vias at y 187.75 | In5 2.0 mm with 1.6 mm of B.Cu beside it for 5.4 mm, into In5 2.3 mm exactly under the `+2V5` B.Cu trunk at x 247.9, y 187.7 to 147.8 |
| Trunk | B.Cu 2.2 mm along y 187.5 between U22 and J7, then 2.0 mm up x 194.4 under U9's west end, 39.5 mm | that In5 trunk, 39.9 mm, one layer |
| Crossing | the `+2V5` feeder on B.Cu at y 163: two vias each side, 1.6 mm on F.Cu and In2 | the J5A/J5B pin field: In5 0.6 mm in gap rows 147.798 and 150.338 through the east column, a via in each cell, row 147.798 on four layers through the west column |
| To the bank's capacitors | In2 1.7 mm under C342 to C344, fingers to their three reserved vias | B.Cu 2.0 mm along y 147.25, 1.2 mm through the capacitor via column at y 148.59; F.Cu 1.0 mm to C369.1 |
| Balls | F26 on F.Cu from C343; B.Cu 0.22 mm on rows 153.84 (G23) and 151.84 (H20, J17); In2 0.22 mm G23 to H20 to J17 to K14 and J17 to M18 | B.Cu 0.22 mm on row 148.84 (L1, K4, N5, M8) and on row 144.84 from C359's via (P2, T6) |
| Sense line to the monitor resistor | In2 0.10 mm from M18's via through the north-west of the ball field, then 0.15 mm beside the `+1V8` sense lane across the north band, via beside R198.1 | In5 from C354's via, 0.10 mm in the strip between the `+2V5` and `+1V8` In5 trunks, then In2 beside the other two lanes, via beside R199.1 |

Every ball uses its reserved dogbone. Both monitor branches leave U7 through the gap between C119 and C121 as two 0.09 mm tracks; `MON_VCCIO_1` then changes to In2 for 2 mm to pass under the `MON_1V8` track, which lies between its pin and its parts.

*Voltage drop, selector pin to ball, from the saved copper.* Outer copper 35 um, inner 15.2 um, via barrels 18 um on a 0.20 mm drill, assumed, each barrel on the stackup's depths. A through-hole pin joins its layers; the bar is the copper drawn between the pins, centre to centre. Source: the even pin the shunt lands on. Loads: the bank's 0.100 A, an estimate from `tools/budget.py`, split evenly over its six balls as bank 16 was; the 0.500 A export allowance leaving at the switch's two input pins. Nodal solution, 85 C:

| Shunt position | Bank 15: F26, G23, H20, J17, K14, M18 | Worst | Bank 34: K4, L1, M8, N5, P2, T6 | Worst |
|---|---|---:|---|---:|
| 3.3 V, pin 2 | 3.04, 3.56, 4.05, 4.43, 4.91, 4.91 mV | **4.91 mV** | 4.45, 4.03, 4.63, 4.54, 4.43, 4.66 mV | 4.66 mV |
| 2.5 V, pin 4 | 2.99, 3.51, 4.00, 4.38, 4.86, 4.86 mV | 4.86 mV | 4.51, 4.10, 4.70, 4.61, 4.50, 4.72 mV | 4.72 mV |
| 1.8 V, pin 6 | 2.94, 3.46, 3.95, 4.33, 4.80, 4.80 mV | 4.80 mV | 4.57, 4.16, 4.76, 4.67, 4.55, 4.78 mV | **4.78 mV** |
| Left of 6 mV | | 1.1 mV | | 1.2 mV |
| At 25 C | | 3.97, 3.93, 3.89 mV | | 3.77, 3.82, 3.87 mV |

The figures are the same to 0.01 mV with the export switched off: in no position does the export's 0.5 A share copper with the bank's 0.1 A beyond the pin it enters by. The bar costs the bank 0.10 mV at J19 in the 3.3 V position and 0.13 mV at J20 in the 1.8 V position, where the bank's current crosses it. The switch input pin is 2.0 to 2.5 mV below the source pin at U23 and 2.2 to 2.8 mV at U24 at 0.5 A. Most loaded track 35 % of IPC-2221 at a 10 C rise, the 0.5 mm entries to the switch pins; most loaded via 0.06 A.

| To the worst ball, 85 C | `VCCIO_1`, pin 2 to K14 | `VCCIO_2`, pin 6 to T6 |
|---|---:|---:|
| Bar | 0.10 mV | 0.13 mV |
| From the pin to the trunk | 0.54 mV | 0.45 mV |
| Trunk | 1.14 mV, 11.5 mohm | **2.27 mV, 22.7 mohm** |
| Crossing | 0.20 mV | 0.67 mV |
| To the capacitors and their vias | 1.08 mV | 0.72 mV |
| Lanes to the ball, via and dogbone | **1.85 mV** | 0.54 mV |
| Total | 4.91 mV | 4.78 mV |

*Limiting sections.* Bank 34: the trunk on one inner layer. In2 beside it would take 1.1 mV off; it was left free, see access. Bank 15: the one 0.22 mm B.Cu lane that carries four balls 10 mm into the field, and the In2 links behind it, which are thin copper. A second B.Cu row would lower it and take one more of the five rows the slot signals have left there; not taken.

*Voltage budget per setting, worst ball of each bank.* The pin figures are those of the earlier entries, regulator at its low limit, copper at 85 C; the selector is the requirement of 20 mohm between the pads at 0.6 A, 12 mV, awaiting measurement; the copper is now the routed figure and no longer the 6 mV allowance.

| Setting, case | At the pin, above the bank's minimum | Selector, required | Copper, routed | Left at the worst ball | Selector resistance for nothing left |
|---|---:|---:|---:|---:|---:|
| 2.5 V, bank 15, both exporting | 24.8 mV | 12 mV | 4.9 mV | **7.9 mV** (6.8 with the allowance) | 33 mohm |
| 2.5 V, bank 15, J19 alone | 33.5 mV | 12 mV | 4.9 mV | 16.6 mV | 48 mohm |
| 2.5 V, bank 34, both exporting | 23.1 mV | 12 mV | 4.7 mV | **6.4 mV** (5.1) | 31 mohm |
| 2.5 V, bank 34, J20 alone | 31.8 mV | 12 mV | 4.7 mV | 15.1 mV | 45 mohm |
| 1.8 V, bank 15, both exporting | 15 mV | 12 mV | 4.8 mV | **1.8 mV short** (3 short) | 17 mohm |
| 1.8 V, bank 15, J19 alone | 20 mV | 12 mV | 4.8 mV | 3.2 mV | 25 mohm |
| 1.8 V, bank 34, both exporting | 36 mV | 12 mV | 4.8 mV | 19.2 mV | 52 mohm |
| 1.8 V, bank 34, J20 alone | 40 mV | 12 mV | 4.8 mV | 23.2 mV | 59 mohm |
| 3.3 V, either bank | not drawn up | 12 mV | 4.9 and 4.7 mV | open | |

The 3.3 V position is the one `ref/freya.xdc` assumes and has no figure at the pin: U12's cell and its connection to In3 are unrouted, 120 of 153 `+3V3` pads have no copper, and no entry carries U12's window to J19.1 or J20.1. Its copper beyond the pin is routed and inside the target; the rest is open.

*Kept open, not changed to obtain a pass.* The selector's 20 mohm is a requirement, not a property: four-wire at the pads, before and after 25 complete removal and reinsertion cycles, at 0.6 A and 85 C, as the entry "Selector check set" below now words it. Bank 15 at 1.8 V with both selectors exporting closes only with a selector of 17 mohm or less, or with the repair of the `+1V8_IO` column beside J19 that the J19 entry names; it was 15 mohm with the allowance. **U14's hold stands: TPS62A0569APDRLR recommended and not fitted until loop stability into 113 uF plus 63.5 uF and no-load input current are measured.** U13 and U14's power-save rise at light load is not bounded by the datasheet, 5 to 18 mV by the earlier scaling, and comes out of the top of each window, which this copper does not touch. A load step of the 0.5 A export, loop stability and start-up are not analysed: this is DC closure. The bank's 0.1 A is an estimate and its even split over six balls an assumption.

*Access, before and after.* Capacity as in the J19 entry: 0.20 mm tracks at 0.15 mm on a 0.35 mm grid, low by construction. Missing connections rebuilt from the saved copper, 569 before and 523 now on nets without a plane.

| Place | Missing connections crossing | Before | After |
|---|---:|---|---|
| North band, y 122.4 to 125.8, 3 mm window | 51 | F.Cu 54, In2 146, via sites south 121 | F.Cu 54, In2 143, via sites south 114 |
| North band, 7 mm window | | F.Cu 40, In2 135 | F.Cu 40, In2 128 |
| Wall beside J3A and J3B, x 172.3 to 177.0 | 41 | F.Cu 28, In2 46, In5 46 | F.Cu 20, In2 46, In5 46 |
| J5A and J5B pin field | 20 | F.Cu 28, In2 32, In5 32 | F.Cu 25, In2 29, In5 11: the trunk closes In5 east of the field from y 147.8 to 187.7 |
| Strip under the `+2V5` east trunk, y 149 to 190 | 7 | F.Cu 24, In2 30, In5 30 | F.Cu 23, **In2 30**, In5 0 |
| B.Cu band north of J7, y 186.4 to 188.6 | 12 | F.Cu 7, In2 7, In5 7, B.Cu 7 | F.Cu 6, In2 7, In5 7, B.Cu 0 |
| B.Cu column under U9, x 193.2 to 195.6 | 7 | F.Cu 44, In2 61, In5 54, via sites west 85 | F.Cu 41, In2 56, In5 51, via sites west 55 |
| In2 beside the PSRAM resistor vias, x 190.5 | 21 | In2 4, In5 3, B.Cu 0 | the same |
| Bank 34 east face, rows 142.84 to 150.84: free 0.10 mm row lanes into the field, and of those open in front | 34 | In2 6 and 4, In5 7 and 5, B.Cu 9 and 6 | In2 6 and 4, In5 7 and 5, **B.Cu 5 and 4** |
| Bank 15 west face, rows 146.84 to 154.84 | 38 | In2 0, In5 0, B.Cu 7 and 2 | In2 0, In5 0, **B.Cu 5 and 2** |

What was done for it. The wall beside J3A and J3B keeps both inner layers: `VCCIO_1` passes it on F.Cu and takes eight F.Cu crossings at its south end. `VCCIO_2`'s trunk lies under a B.Cu trunk that already closed the layer, costs no via site there, and uses one inner layer: **In2 under the fuses of slots E to H stays free for the export buses**, which have no other layer there. No bar stands in front of either bank face: the bank 34 capacitors are fed along the rows, and bank 15's capacitor column is fed on In2, which has no row left at that face, so B.Cu in front of it is as open as it was. Both sense lines run where an existing trunk or lane already closes the layer. A first layout that did none of this measured 4.2 and 3.6 mV and was not kept.

*For the owner, found on the way and not changed.*

- **Bank 15's slot signals have five B.Cu rows at the west face and nothing else there.** 38 missing connections cross that face. In2 and In5 have no free row at that face, all taken by accepted PSRAM and SDRAM lanes; B.Cu had seven rows before this chunk and two are now `VCCIO_1`'s, the two its capacitor vias already stood on. This is older than this chunk and decides the slot A to D escape.
- *Corrected 2026-11-09, entry "Four capacitors corrected" below: both now stand over the In2 feeder at the south-west corner of U1.* **C346 and C347 are connected but no longer decouple the bank.** No legal 0.2 mm link was found on In2, In5 or B.Cu from their reserved vias to the nearest ball vias, J17's and K14's, searched over x 203 to 218, y 147 to 163: accepted LINK, RGMII and SDRAM lanes fill the columns between. They hang on C367 by F.Cu, 11.5 mm and 22 mm with one In2 hop, and C367 on the trunk by 12 mm of 0.4 mm F.Cu. At 0.125 mm a 17 mm path with three more vias exists and was not taken. Bank 15's close capacitors are C342, C343 and C344; C345 joins C344 by 7 mm of 0.2 mm F.Cu under C340 and C338, the shortest legal link found; its reserved via is not used. Moving the three is the owner's call.
- *Corrected 2026-11-09, same entry; exchanging the two would not have been enough, both stood at the wrong end of the package as well.* **At U24 the two capacitors stand on the wrong sides.** C221, the input capacitor, is under output pins 7 and 8, and C276, the output capacitor, under input pins 1 and 2; U23 has them the right way round. C221.1 is reached by the 0.3 mm track between C276's pads. Exchanging the two positions would correct it.
- For the export chunk: 0.8 mm via sites and a 1.0 mm inner track are free beside U23's and U24's output pins and beside C273.1 and C276.1 (`reports/takeoff.txt`). A 1.0 mm track centred on pins 7 and 8 of either switch comes 0.125 mm from pin 6, so the EXT_2A width cannot land on those pads without a local rule. *At U24 this is now done within the rule, entry of 2026-11-09 below: a 1.0 mm patch over pins 7 and 8 and two 0.8 mm vias; the sites named here beside C276.1 no longer apply, C276 has moved.*
- `MON_1V0` on U7 pin 56 cannot pass on F.Cu between R199 and the `MON_1V8` track, 0.34 mm. `MON_VCCIO_1`'s first via stands at (195.02, 110.08) so that a via site remains at (195.02, 110.70) for it.

*Planes and reservations.* 64 new vias, 28 on reserved sites and 36 on new ones. Every plane is one piece: In1, In4 and In6 lose 17.84 mm2 each, In3 `+3V3` 25.98 mm2 and the `+1V0` island 2.45 mm2. Of 140 pairs of an accepted track and a plane within 1.2 mm of a new via, none lost copper under its centre line or edges. At the reserved sites beside them the new plane openings come to 0.007 mm from the edges of `SDRAM_A3` and `SDRAM_BA1` on In5; not modelled. The reservation list is now `tmp/res_vccio.json` in the evidence folder, 471 vias: 28 of the 503 are real, and four sites are released, C345's two and the unused ones of C346.1 and C347.1. With reservations on scratch copies the board gives 33 errors before and 31 after; by type and net pair 19 signatures before and 18 after, none new, the missing one an SDRAM stub crossing that KiCad reports against a different neighbour from run to run; none names these nets.

*Checks.* On a copy first, then transferred. The live board at the start was the committed board with the owner's H4 position and its refill, byte for byte. Against it: 238 tracks and 64 vias added on `VCCIO_1`, `VCCIO_2`, `MON_VCCIO_1`, `MON_VCCIO_2` and `GND`, nothing removed, every existing track, via and footprint byte-identical, net table identical, header, stackup, rules, groups and drawings byte-identical, no zone outline or setting changed. **0 DRC errors, 0 parity with H4 at either position**, no dangling copper, fresh refills byte-identical, unconnected 945 to 873. By KiCad on each net alone: the four nets 0; `+2V5` 0 of 27, `+1V8` 0 of 18, `MON_1V8` 0 of 3, `+1V8_IO` 0 of 40, RGMII, management, LINK, SDRAM, PSRAM, MDI and the other PHY nets 0, HDMI 15, `+3V3` 120, `+1V0` 39, all as before; `GND` 193. Warnings below KiCad's 199 limit identical item for item; silkscreen compared in six cropped windows, identical. Smallest margin of any planned item 0.005 mm beyond the 0.15 mm rule. Tracks 2936 to 3174, vias 703 to 767. Strict gate electrical and mechanical PASS, stackup guard and ERC pass, on the live tree; every schematic, the netlist, project, rules and libraries unchanged by hash. The PCB editor had the board open while this was prepared; nothing was written until the owner closed it, the lock was gone and the board on disk was still byte-identical to the one validated against. No generator, placement tool or silkscreen updater was run.

*Evidence.* `~/freyja-review/vccio-2026-11-06`: `README.md`, the three plans and their scripts, the commit and working boards, DRC reports, the DC results at 25 and 85 C with the path to the worst ball, corridor and row tables, `images/overview.png` and five detail figures. Owner's H4 move, its fills and `.prl` left out of the commit. Nothing measured on hardware.

**Selector check set: 25 cycles, a provisional prototype check (2026-11-09).** The owner's decision, replacing "25 moves, a proposal for the owner" in the selector hardware entry above. Documents only: no schematic, netlist, board or BOM line changed.

> Use 25 complete removal/reinsertion cycles as a provisional prototype check, with the board unpowered during mating. Measure assembled pad-to-pad resistance four-wire before and after conditioning, at the stated current and temperature. This is not a lifetime qualification.

*Requirement, unchanged.* 20 mohm or less between the two PCB pads at 0.6 A and 85 C, in the reading before and in the reading after. It comes from the voltage budget, not from a data sheet.

*Pairs tested.* On J19 and on J20, each of the three positions with the Samtec SNT-100-BK-G on it: pins 1-2, the 3.3 V position; pins 3-4, 2.5 V; pins 5-6, 1.8 V. Four-wire at the two pads of the pair on the back of the assembled board, so that both solder joints, both posts, both interfaces and the bridge are inside the reading. For each pair: fit the shunt and read; take it off completely and push it back down to the header body 25 times, board unpowered; read again. Six pairs, twelve readings. Each pair gets its own 25 cycles, because the posts wear as well as the shunt; if one shunt serves all three pairs of a header it has seen 75 cycles by the last reading, and that is noted with the result.

*Results.* None yet; no assembled board exists.

| Selector | Pins | Position | Before, mohm | After 25 cycles, mohm | 20 mohm or less |
|---|---|---|---:|---:|---|
| J19, slots A-D, bank 15 | 1-2 | 3.3 V | not measured | not measured | open |
| J19 | 3-4 | 2.5 V | not measured | not measured | open |
| J19 | 5-6 | 1.8 V | not measured | not measured | open |
| J20, slots E-H, bank 34 | 1-2 | 3.3 V | not measured | not measured | open |
| J20 | 3-4 | 2.5 V | not measured | not measured | open |
| J20 | 5-6 | 1.8 V | not measured | not measured | open |

*What a pass closes and what it does not.* A pass on a pair supports the selector term of that position's budget in the `VCCIO` entry above, for a prototype: 12 mV at 0.6 A. **It does not close bank 15 at 1.8 V with both selectors exporting.** That case is 1.8 mV short at 20 mohm. A reading of 17 mohm or less on J19 pins 5-6 would bring its DC figure to nothing left and no further: the power-save rise at light load, a load step of the 0.5 A export, loop stability and start-up are not analysed, and U14's hold stands, TPS62A0569APDRLR recommended and not fitted until loop stability into 113 uF plus 63.5 uF and no-load input current are measured. The 3.3 V position still has no figure at the pin, U12's cell being unrouted. And 25 cycles says that a prototype's selector can be set a number of times; no maker gives mating life for the header, the shunt or the pair, so it is not a lifetime figure.

*Recorded.* `ref/jlcpcb-import-checklist.md`, selector shunts, the same wording, pairs and requirement. `tools/qualified.py` and `ref/qualified-parts.md` already state "20 mohm pad to pad at 0.6 A and 85 C after conditioning" and name no count; unchanged.

**Four capacitors corrected: C346 and C347 at bank 15, C221 and C276 at U24 (2026-11-09).** The four were moved and reconnected; nothing else moved. C346 and C347 now stand over the bank's own In2 feeder at the south-west corner of U1, 11.5 and 13.4 mm of copper from the nearest bank 15 ball where they had 44.6 and 55.7 mm. C221 is 1.2 mm from U24's input pins where it had 15.6 mm, and C276 is connected to the output pins for the first time. Both `VCCIO` nets keep 22 of 22 pads, both monitor nets 3 of 3, and the worst-ball drops stay inside the 6 mV target: 4.83 mV on bank 15, 4.78 mV on bank 34. No setpoint, allowance, selector requirement, regulator cell, sense takeoff, feeder or accepted signal track changed. Export distribution and the switch controls are still not routed.

*Why C346 and C347 did not decouple the bank.* They stood in the capacitor row south of U1, and the only copper from them ran away from the FPGA: 10 to 15 mm south on 0.3 and 0.2 mm tracks to the 47 uF C367, then 12 mm west on 0.4 mm to the trunk, up the trunk and back in through the feeder. C346 had 25 mm of track under 0.45 mm wide in its path and six via barrels, C347 36 mm and eight. UG483 v1.14, "0805 and 0603 Ceramic Capacitors", p. 24: as close as possible to the FPGA, any placement within two electrical inches of the point of load acceptable, mounting optimised for low inductance, vias butted against the pads. C347's 55.7 mm was outside the two inches, 50.8 mm, to the nearest ball and further to the others; C346 was inside it by length only, on a quarter of a millimetre of copper. The reason they could not be linked where they stood is the one recorded on 2026-11-06: the columns between them and the J17 and K14 ball vias are full of accepted LINK, RGMII and SDRAM lanes.

*Where they are now.* F.Cu had one free pocket at that corner, between C351, the F.Cu hop of the `VCCIO_1` trunk, C350's `+2V5` link and C312, and the bank's 1.7 mm In2 feeder passes under it.

| Part | Was | Is | Supply side | Ground side |
|---|---|---|---|---|
| C346, 0.47 uF | (207.67, 161.87), -90 | (196.85, 159.85), 0 | own via butted against pad 1 at (195.4, 159.85), 0.6 mm on In2 into the feeder; 0.6 mm on F.Cu to the hop's vias as well | via butted against pad 2 at (198.3, 159.85) |
| C347, 0.47 uF | (213.06, 161.87), -90 | (196.55, 162.75), 0 | pad 1 by 0.8 mm of F.Cu into the hop, whose four vias go down to the feeder | via at (197.75, 163.55), at the pad's corner |
| C221, 1 uF, U24 input | (255.2, 195.6), -90 | (252.4, 190.35), 180 | pad 1 to pin 1 by 0.5 mm F.Cu, pins 1 and 2 joined as before | via butted against pad 2 at (250.95, 190.35) |
| C276, 1 uF, U24 output | (253.4, 195.6), -90 | (254.995, 188.27), 90 | 1.0 mm throughout, see below | 0.6 mm F.Cu to the ground pad of key post MK72, a via on it at (253.6, 187.495) |

Through vias cannot stand inside the feeder's outline there, four SDRAM address lanes run under it on In5, so the vias are at its west and east sides. C347 stands 1.3 mm south of C346 and not against it: against it, its pad lay under the last letter of X4's "FPGA CLOCK" label.

*Paths, before and after, from the saved copper.* Shortest copper from pad 1 to the load, and pad 2 to its ground via, centre to centre.

| Capacitor | Before | After | Ground before | Ground after |
|---|---|---|---|---|
| C346 to ball F26 | 44.6 mm, 6 via barrels, 25.2 mm of it under 0.45 mm wide, 67 mohm | 11.5 mm, 2 barrels, 1.4 mm under 0.45 mm, 19 mohm | via 0.82 mm | via 0.68 mm |
| C347 to ball F26 | 55.7 mm, 8 barrels, 36.3 mm under 0.45 mm, 139 mohm | 13.4 mm, 2 barrels, 1.4 mm under 0.45 mm, 17 mohm | via 0.80 mm | via 0.91 mm |
| C221 to U24 pin 1 | 15.6 mm: 6.1 mm of 0.3 mm from J20 pin 6 between C276's pads, then back along the 1.5 mm export stub | 1.2 mm of 0.5 mm | via 1.10 mm | via 0.68 mm |
| C276 to U24 pin 7 | no copper | 4.1 mm at 1.0 mm, 2 barrels | no copper | via 1.40 mm, MK72's pad 2.4 mm |

For comparison, unchanged: C344 6.8 mm, C345 11.9 mm of which 5.1 mm is its 0.2 mm link. The 1.4 mm under 0.45 mm that all of them share is the F26 dogbone. The other five balls are further by the bank's lanes, as before. These are lengths and DC resistance, not a loop inductance; nothing here is simulated.

*U24 against its pins and TI's guidance.* TPS22975, SLVSDD0B: pins 1 and 2 VIN, 3 ON, 4 VBIAS, 5 GND, 6 CT, 7 and 8 VOUT, pad GND. Section 10.1.2: a 1 uF input capacitor between VIN and GND placed close to the pins, against the dip when the switch turns on into a discharged load. Section 12.1: input and output capacitors close to the device, wide VIN, VOUT and GND, the CT trace as short as possible. On the board U24 stands at rotation 0, so pins 1, 2, 7 and 8 are its north end, and both capacitors stood south of it at the pin 4 and 5 end. C221 was not on the way to the pins at all: it hung on its own 0.3 mm branch from J20 pin 6. **The note of 2026-11-06 that exchanging the two would correct it is withdrawn**: exchanged, C221 would still have been about 14 mm from pins 1 and 2 with pin 4's link to C274 across the way. C221 now lies west-north-west of pin 1, and the export stub was re-laid to reach it: the column from J20 pin 6 as before at 1.5 mm, then 1.4 mm north of C221 between it and MK72's pad, a 0.7 mm drop onto pad 1, and on from the pad to the pins, so the capacitor is in the path. U23 has its capacitors at the right end and was not touched.

*C276 and the 1.0 mm rule.* The custom rule "extension buses 2A" makes any `VCCIO_2_EXT` track under 1.0 mm an error, and the strip between U24's east pins and the board edge is 0.57 mm wide beside C275. So there is no narrow link on F.Cu, and **no local rule was added**. C276 is connected inside the rule: one 1.0 mm patch 0.44 mm long over pins 7 and 8, a 0.8 / 0.4 mm via beside them at (255.87, 191.78), 2.7 mm of 1.0 mm on In2, a second such via butted against C276.1 at (255.87, 189.045), and 1.0 mm into the pad. The patch clears pin 6 by 0.165 mm, U24's ground pad by 0.18 mm and the edge by 0.51 mm against 0.50 mm. The In2 piece and the two vias are also where the export bus can start: on In2 a track up to 1.26 mm wide still passes from either via to fuse F37, the same figure as before the change; In5 is closed there by the `VCCIO_2` trunk, as it was.

*Bank feed, recalculated.* Same model as on 2026-11-06, nodal, 0.100 A over six balls, 0.500 A export at the switch input pins, copper at 85 C.

| Shunt position | Bank 15 worst ball, was | is | Bank 34 worst ball, was | is | U24 input pin below the source pin, was | is |
|---|---:|---:|---:|---:|---:|---:|
| 3.3 V, pin 2 | 4.91 mV | **4.83 mV** | 4.66 mV | 4.66 mV | 2.84 mV | 3.72 mV |
| 2.5 V, pin 4 | 4.86 mV | 4.78 mV | 4.72 mV | 4.72 mV | 2.51 mV | 3.38 mV |
| 1.8 V, pin 6 | 4.80 mV | 4.73 mV | 4.78 mV | **4.78 mV** | 2.21 mV | 3.08 mV |

Bank 15 gains 0.08 mV because C346's and C347's links lie in parallel with the first millimetres of the feeder; at 25 C 3.91 mV where 3.97. Bank 34 is unchanged to 0.001 mV: the export stub shares no copper with it. The export loses 0.9 mV at 0.5 A on the longer stub round C221; it has no stated tolerance. The budget tables of 2026-11-06 stand as written, to 0.1 mV. **Bank 15 at 1.8 V with both selectors exporting is still short, by 1.7 mV where 1.8, and still closes only at 17 mohm or less, DC only.** The selector measurement, U14's hold, the power-save rise, load step, loop stability and start-up are as open as they were.

*Copper.* 18 tracks and 5 vias removed: the two spurs to C367 with their In2 hop and two vias, the old ground vias of C346, C347 and C221, C221's 0.3 mm branch, and the four pieces of the export stub that were re-laid. 19 tracks and 7 vias added on `VCCIO_1`, `VCCIO_2`, `VCCIO_2_EXT` and `GND`. Tracks 3174 to 3175, vias 767 to 769. C367, its ground via and its 0.4 mm link to the trunk stay. `GND` pads without copper 193 to 192: C276 is new, the other three keep a ground. `VCCIO_2_EXT` 6 missing connections to 4.

*Left for later, and what this leaves it.*

- **`U24_CT` cannot be routed on F.Cu alone.** C275 stands north of the package, so the CT track from pin 6 and anything leaving pins 7 and 8 must cross at the north-east corner. It needs two vias; both sites are free with the new copper in place, (255.9, 192.72) beside pin 6 and (253.6, 189.2) north-west of C275.1, and In2 and In5 are open between them. The export stub's drop onto C221 was laid clear of that site. This is older than this chunk; moving C275 south of the package would remove it and is the owner's call.
- Pin 3's exit west between R73 and C274 and pin 4's link to C274.1 are open on F.Cu, 0.27 and 0.51 mm wide.
- U23's output capacitor C273 has no copper and stays with the export chunk, which meets the same rule at U23's pins 7 and 8.
- Strip under the `+2V5` east trunk, zone y 180 to 190: F.Cu crossings 9 to 7, via sites on its east side 5 to 3, because the stub now turns 1.45 mm further north; In2 12 and the strip's In2 total 30 unchanged, 7 connections cross. Every other corridor table of 2026-11-06 and the row lanes at both bank faces are identical before and after: bank 15 west face still 5 B.Cu rows, 2 open in front.
- The sites C346 and C347 left, (207.67, 161.87) and (213.06, 161.87), are free, with their four via sites.
- C345 is as it was, 5.1 mm of 0.2 mm to C344; it was not part of this.

*Silkscreen, compared in four cropped windows.* One new warning: C221's own silk line lies under MK72's "KEY H" label, and that label, already clipped by C275's pads, now also crosses C221's pads. Nothing else new; the count of clipped labels is the same. No label was moved and no silkscreen writer was run; the label is the owner's to place.

*Planes and reservations.* Seven new vias, none on a reserved site; the reservation list is unchanged, `tmp/res_vccio.json` of the 2026-11-06 evidence, 471. Every plane one piece. In1, In4 and In6 lose 2.41 mm2 and regain 0.89 mm2; In3 `+3V3` loses 3.96 mm2, the `+1V0` island regains 1.78 mm2 where four vias left. No accepted signal track lost copper beneath it: the one opening near a track is the new `VCCIO_1` via beside C341's own `+3V3` stub and under the feeder it feeds. With the reservations on scratch copies 33 errors before and 32 after, 19 signatures by type and net pair both times, none naming these nets.

*Checks.* On a copy first, then transferred. The live board at the start was the committed board with the owner's H4 position and its refill, byte for byte. Against it: C346, C347, C221 and C276 moved, same footprint, value, side, pads and pad nets; the planned copper removed and added and nothing else; every other footprint, track and via byte-identical, net table, header, stackup, rules, groups and drawings byte-identical, no zone outline or setting changed. **0 DRC errors, 0 parity with H4 at either position**, no dangling copper, fresh refills byte-identical, unconnected 873 to 870. Every tracked group unchanged: `+2V5` 0 of 27, `+1V8` 0 of 18, `MON_1V8` 0 of 3, `+1V8_IO` 0 of 40, RGMII, management, LINK, SDRAM, PSRAM, MDI and the other PHY nets 0, HDMI 15, `+3V3` 120, `+1V0` 39. Warnings of every type below KiCad's 199 limit identical item for item. Smallest margin of a planned item 0.012 mm beyond a rule, the In2 link against the board edge. Courtyards meet within 0.02 mm at C221 and R73, C221 and C275, C276 and C275. Strict gate electrical and mechanical PASS, stackup guard and ERC pass, on the live tree; every schematic, the netlist, project, rules and libraries unchanged by hash. No KiCad process and no lock before or after the transfer. No generator, placement tool or silkscreen updater was run; the four moves are in `tmp/plan_A.json`.

*Evidence.* `~/freyja-review/caps-2026-11-09`: `README.md`, the two plans and their scripts, commit and working boards, DRC reports, paths before and after (`reports/loops.txt`), DC results at 25 and 85 C, what is left for the later nets (`reports/later.txt`), corridor and row tables, UG483 v1.14 as downloaded, `images/close_up.png`. Owner's H4 move, its fills and `.prl` left out of the commit. Nothing measured on hardware.

**U15's cell routed: `+5V` to `+1V0`, the FPGA core regulator (2026-11-09).** SW, bootstrap, feedback and enable are complete, the cell's input and output nodes and its seven grounds are connected, and the output reaches the `+1V0` island on In3 through six vias. Six passives moved; U15, L7, C212 and R94 did not. R67 and R68 are now 0.1 %, same values. Global `+5V` and the core fanout are not routed. **Start-up, load step and loop stability into this output network are not established by any of this and stay a bench hold.**

*Preflight.*

- *Pins.* TPS564201, SLVSDJ7B section 5, DDC top view: 1 GND, 2 SW, 3 VIN, 4 VFB, 5 EN, 6 VBST. The board's pads carry `GND`, `SW+1V0`, `+5V`, `FB+1V0`, `EN_1V0`, `BST+1V0` in that order.
- *Parts against the netlist*, all equal: U15 TPS564201DDCR; L7 4.7 uH SWPA6045S4R7MT between `SW+1V0` and `+1V0`; C207 22 uF and C286 100 nF from `+5V` to ground; C211 and C212 22 uF from `+1V0` to ground; C285 100 nF from `BST+1V0` to `SW+1V0`; R67 3.09k from `+1V0` to `FB+1V0`, R68 10k from `FB+1V0` to ground; R94 100k from `EN_1V0` to ground. The 22 uF is Murata GRM21BR61E226ME44L, 25 V X5R.
- *Load.* 2.050 A from `tools/budget.py` as it stands after the GTP removal: 2.000 A VCCINT, a planning allowance, and 0.050 A VCCBRAM. Not the earlier 2.150 A.
- *Inductor.* Ripple 0.30 A at 5 V in, 0.39 A at 5.5 V with the inductance 20 % low; peak 2.24 A against 4.97 A guaranteed saturation, 2.05 A against the 3.30 A heating rating, DCR 34 mohm at most. U15's valley limit is 4.2 A at least. At the regulator's own 4 A the heating rating would be exceeded: this cell is a 3.3 A cell, which the budget does not approach.
- *Regulator tolerance.* VFB 0.745 / 0.760 / 0.775 V over -40 to 125 C junction, 2 % each way, specified at 12 V in, 1.05 V out, continuous mode; TI gives no line figure for 5 V in. With 3.09k / 10k the nominal is 0.995 V.
- *Output network: nominal, effective, distributed.* TI's Table 2 covers 20 to 68 uF with 1.5 to 4.7 uH, a double pole between 8.9 and 29 kHz. Nominal here 506.9 uF: the cell's 2 x 22 uF and, on the island, 330 uF polymer tantalum, 100 uF, 6 x 4.7 uF and 10 x 0.47 uF, the UG483 set. Effective at 1 V about 480 uF by my estimate of the ceramics' bias loss, not read from Murata's curves. Double pole with 4.7 uH about 3.4 kHz, 2.6 times below TI's lowest. Distributed: only the 44 uF stands at the cell. The 100 uF is 0.9 mohm of island away, the north-face 4.7 uF 1 to 2 mohm, and the 330 uF is at the island's far end, 7.3 mohm of plane away, with up to 25 mohm of its own ESR.
- *What that means for the loop, by TI's published model and not by measurement.* SLVA546 gives D-CAP2 as plant double pole, one zero from the ripple injection and a delay, and publishes the two parameters for the TPS54325 and TPS53114 only, not for the TPS564201. With the TPS54325's 1.05 V row as a stand-in (`scripts/loop.py`), TI's own typical circuit comes out at 41 degrees of phase margin and TI's lowest-pole corner, 4.7 uH with 68 uF, at 28 degrees. The fitted network comes out at 38 to 49 degrees with the polymer's ESR between 6 and 25 mohm, crossing at 26 to 34 kHz where TI's circuits cross at 66 to 135 kHz; with the stand-in gain halved or doubled or the zero moved, 33 to 52 degrees, never below TI's lowest corner under the same assumption. Without the polymer branch the same ceramics give 21 degrees. **So extra capacitance is not harmless here, and it is not shown unstable either: the margin rests on the series resistance of the 330 uF branch, and the parameters are another part's.**
- *Start-up, by arithmetic.* Soft start 1.0 ms, inside DS181's 0.2 to 50 ms ramp. Charging 480 to 545 uF in 1 ms takes 0.48 to 0.54 A; DS181's power-on current for the XC7A100T adds about 0.39 A; under 1 A against the 4.2 A limit.
- *Hold.* The existing line of `ref/power-budget.md`, "beyond: bench qualification", stands and is the hold for this rail: start-up into the full bank with the FPGA unconfigured and configuring, a load step read at the core capacitors, and loop margin if it can be measured. Nothing found requires a different power stage before layout, so none was laid out. **Prepared, not applied:** Sunlord SWPA6045S2R2NT, C36500, 2.2 uH, TI's typical value, on L7's footprint: 7.4 A saturation, 4.6 A heating, 18 mohm, 2313 in stock on 2026-11-08; ripple 0.65 A; the same model gives 50 to 55 degrees. A value-only change if the bench asks for it.

*Layout.* TI 10.1: input and output capacitors close, SW short and wide, no switching current under the device, a separate VOUT path to the upper resistor, a Kelvin ground for the feedback, VFB node small.

| Part | Was | Is | Why |
|---|---|---|---|
| C286, 100 nF input | (213.14, 122.7), -90 | (213.1, 122.1), 180 | `+5V` pad 0.9 mm from pin 3 |
| C207, 22 uF input | (211.24, 122.1), -90 | (213.0, 123.65), 180 | `+5V` pad 1.7 mm from pin 3; it stood 3.2 mm away with its ground pad over the `+2V5` trunks, where no via can go |
| C285, bootstrap | (215.74, 118.7), 180 | (216.05, 119.05), 180 | 1.2 mm from pin 6 |
| C211, 22 uF output | (204.74, 121.9), -90 | (207.3, 121.2), 0 | beside L7.1; its ground pad was over the trunks too |
| R67, 3.09k | (207.0, 121.8), -90 | (218.35, 124.22), 180 | at pin 4; the VFB node would have been 9 mm long |
| R68, 10k | (208.8, 121.8), 90 | (218.35, 122.65), 0 | its VFB pad on pin 4's pad |

- *Switch node.* F.Cu only: from pin 2 west and north into L7.2, 1.0 mm wide, 2.2 mm of centre line between the pads. L7's pad stands 0.27 mm north of pin 1, so SW passes pin 1's west end.
- *Power ground.* Pin 1 leaves north between L7's pad and C285 on a 0.85 mm strip with three vias. Nothing of the power path is under the package.
- *Input loop.* Pin 3 to C286 and C207, their ground pads to two vias 0.7 mm west of C286, return in In1, 0.11 mm below, to the three pin 1 vias 3.5 mm away. SW lies between pins 1 and 3 on F.Cu, so the loop cannot close on the surface; it closes in the plane under it.
- *Bootstrap.* C285.1 to pin 6, 1.2 mm. C285.2 to pin 2 by a 0.25 mm track 2.6 mm long under the package: gate-drive current only.
- *Feedback.* VFB node: pin 4, R68.1 on it, 1.6 mm to R67.2; In1 under it; SW on the far side of the package. Sense: R67.1 by 2.4 mm to its own via into the island at (220.1, 121.95), in a bay of the island that carries no load current. Ground: R68.2 has no via; a 0.125 mm track 10.5 mm long ties it to the inner end of pin 1's pad, under the package beside the bootstrap track, north round C285 and down the east side past R94. It carries the divider's 76 uA.
- *Enable.* U7 pin 25, a via inside U7's pad ring at (184.96, 117.45), In5 along y 117.3 under L7, down U15's east side, a via between pin 5 and R94.1; 35.8 mm on In5. R94 pulls it down at the pin. The In2 lane the removed `EN_1V2` used is closed by the three sense lanes at x 196.4 to 197.2; In5 was free.
- *Output.* L7.1, C212.1 and C211.1 on 1.0 to 1.4 mm of F.Cu; six vias on a 1.0 mm pitch at x 203.8, 204.8, 205.8 and y 120.1, 121.1 into In3, 1.0 mm clear of the trunks. They share the load between 0.17 and 0.60 A.

| Net | Pads | |
|---|---|---|
| `SW+1V0` | 3 of 3 | U15.2, L7.2, C285.2 |
| `BST+1V0` | 2 of 2 | U15.6, C285.1 |
| `FB+1V0` | 3 of 3 | U15.4, R68.1, R67.2 |
| `EN_1V0` | 3 of 3 | U15.5, R94.1, U7.25 |
| `+5V`, local node | 3 | U15.3, C286.1, C207.1; `+5V` 19 missing connections to 17 |
| `+1V0` | 4 | L7.1, C212.1, C211.1 and R67.1, joined by the island; 39 pads without copper to 36 |
| `GND` | 7 | U15.1, C207.2, C286.2, C211.2, C212.2, R94.2 by vias, R68.2 by its track; 192 to 185 |

*Onward budget, preliminary, DC only.* The island was solved as a sheet from its fill on a copy holding all 471 reserved vias, so the holes of the later fanout are in it: 15.2 um copper, 0.05 mm raster, 2.050 A split evenly over the 17 core ball vias, an assumption (`scripts/island.py`).

| | 85 C | 25 C |
|---|---:|---:|
| Feedback takeoff below the output vias | 2.6 mV | 2.1 mV |
| North-face capacitors C303 to C306 below the output vias | 2.6 to 4.7 mV | |
| First core ball W13 | 10.3 mV | 8.4 mV |
| Worst core balls J11, K12, and the 330 uF beyond them | 15.1 mV, 7.4 mohm | 12.3 mV |
| **Worst ball below the takeoff** | **12.6 mV, 6.1 mohm** | 10.2 mV |
| With its via barrel and dogbone, estimated | 13.0 mV, 6.3 mohm | |

Two thirds of it is inside the ball field, where the island is perforated. VCCINT and VCCBRAM take 0.95 to 1.05 V (DS181 v1.27.1, Table 2).

| At the takeoff and at the worst ball | 1 % pair, 100 ppm/C, as fitted | 0.1 % pair, 25 ppm/C |
|---|---:|---:|
| Minimum at the takeoff, tolerance and 60 C of drift | 0.9678 V | 0.9740 V |
| Maximum at the takeoff | 1.0221 V | 1.0157 V |
| Worst ball, 2.05 A, 85 C | 0.9549 V | 0.9611 V |
| **Left above 0.95 V for load steps, ripple and error** | **4.9 mV** | **11.1 mV** |
| Left below 1.05 V at no load | 27.9 mV | 34.3 mV |
| Feeder and fanout resistance for nothing left | 8.7 mohm | 11.7 mohm |
| For 10 mV left | 3.8 mohm | **6.8 mohm** |

**Allowance for the next chunks: 6.8 mohm from the takeoff to the worst core ball, ball via and dogbone included, if 10 mV is to remain. The island as outlined already takes 6.3 mohm of it; each further milliohm costs 2.05 mV.** The 10 mV is my figure, for the owner to set. What would return margin: taking the feedback from a core ball via once the fanout exists, up to 10 mV, at the price of a 27 mm sense lane through the ball field; R67.1's track is 2.4 mm long, so it can be re-pointed. Or a load figure from AMD's XPE in place of the 2.000 A allowance.

*Divider.* On that budget the substitution the owner allowed is material, 4.9 to 11.1 mV, and was made: R67 YAGEO RT0603BRD073K09L, C861371, and R68 RT0603BRD0710KL, C95204, both 0.1 % and 25 ppm/C, the series U13 and U14 use; 2432 and 2.1 million in stock on 2026-11-08, SMT. Same values, same footprints, setpoint 0.995 V unchanged. The 10k becomes an extended line; the 3.09k already was one.

*Connection points for the next chunks.*

- **`+5V`:** the local node is U15.3, C286.1 and C207.1. Two via sites are free 1.1 mm west of the input ground vias, (210.85, 121.0) and (210.85, 121.8); from them 0.6 mm of F.Cu passes round the south of C207 into C207.1, 7.4 mm. A track up to 1.58 mm reaches the sites from the east on B.Cu or on In2, where U11's cell and U34 stand. A site under U15 beside pin 3 also exists and is not preferred.
- **`+1V0`:** the island is fed. Left: the 17 core balls and the capacitors on their reserved vias; C307, C308, C309 and C312, which stand outside the island's outline; the monitor resistor R88.1 at (201.1, 109.0), north-west of the island; and `MON_1V0`, three pads.

*Access.* North band, 3 mm window: In2 143 to 139 lanes for 51 crossings, F.Cu 54 to 46, via sites on the north face 168 to 145; 7 mm window: In2 128 unchanged, F.Cu 40 to 34, via sites 501 to 447. Every other corridor table is unchanged. The cell takes the north face from x 203.6 to 220.3; nothing was added in the band itself, and the EN lane is north of it.

*Silkscreen, two cropped windows.* U15's own "1V0 SUPPLY / FPGA CORE" label lies across the cell: C286's and R68's silk lines now cross it and C207's no longer does, two warnings new and one gone. Nothing else changed; no label was moved.

*Planes and reservations.* 19 vias, none on a reserved site, list unchanged at 471. Every plane one piece; In1, In4 and In6 lose 4.0 mm2 each, the island 4.9 mm2 to the ground vias, `+3V3` 0.4 mm2. No accepted track within 1.2 mm of a new via lost copper beneath it. KiCad's isolated-copper warning for the island is gone, as intended. Stress copies 33 errors before and after, the same 19 signatures, none naming the cell's nets.

*Checks.* On a copy first, then transferred. The live board at the start was the committed board with the owner's H4 position and its refill, byte for byte. Routing was accepted against the unchanged schematic, then the board was synced to the new netlist with the silkscreen updater held back: 0 footprints moved by the sync, R67 and R68 differ in value, description and part number and in nothing else. Against the starting board: six footprints moved, same footprint, side, pads and pad nets; 40 tracks and 19 vias added on the cell's nets and `GND`, nothing removed; every other footprint, track and via byte-identical, net table, stackup, rules, groups and drawings byte-identical, no zone outline or setting changed. **0 DRC errors, 0 parity with H4 at either position**, no dangling copper, fresh refills byte-identical, unconnected 870 to 851. Every tracked group unchanged, `VCCIO_1` and `VCCIO_2` 22 of 22. Smallest margin of a planned item 0.012 mm beyond the rule, the Kelvin track beside C285. Tracks 3175 to 3215, vias 769 to 788. Strict gate electrical and mechanical PASS, stackup guard and ERC pass, on the live tree. Regenerated from `tools/design.py`: `power.kicad_sch`, `odin.net`, the BOM, the parts guide and the stock list; every other sheet, the project, rules and libraries unchanged by hash. No KiCad process and no lock before or after. No placement generator or silkscreen updater was run; the moves are in `tmp/plan_A.json`.

*Evidence.* `~/freyja-review/u15-2026-11-09`: `README.md`, plans and scripts, routed, commit and working boards, DRC reports, the island solution at 25 and 85 C, the loop comparison, SLVA546, SLVSDJ7B, DS181, the library snapshot, `images/close_up.png`. Owner's H4 move, its fills and `.prl` left out of the commit. Nothing measured on hardware.

**Timing and signal integrity remain unverified.** No length tuning; 33 ohm is
provisional. Lengths are not delays, because these routes mix layers. Pair
impedance through the transitions and stitching is not modelled, and rule
passes do not establish any of this. For the memories: within-port skew to SCK
and via stubs are not assessed. The stitching and continuity above describe copper,
not simulated return current.

**+1V8_IO distribution routed.** All 40 pads on the net reach L5.1 by copper: U1
balls AC25, T16, T26, U23, V20, Y24, U2–U5, U9/U10 VCCA, decoupling, pull-ups, the
J19/J20 selector pins, FB1.1 and the R61 sense. Their 16 local decoupling GND pads
have vias into In1, In4 and In6. No footprint, rule, plane or accepted signal
copper changed. This completes rail distribution only: U14's +5V input, SW and FB
nets, the upstream +5V supply and the +1V8 network behind FB1 are not routed, so
the rail is not yet powered in layout terms. (Since then, 2026-11-05: U14's SW
and FB, and the +1V8 network behind FB1, entries above. +5V is still open.)

Sizing is from `ref/power-budget.md` and copper of 1 oz outer, 0.5 oz inner.
Board load is 0.308 A. Connector exports are not in that figure, so J19 and J20
each carry 0.6 A at the 1.8 V setting (0.5 A PIN V allowance plus the 0.1 A bank
estimate), 1.508 A at the source against U14's 2 A. Source node four 0.45/0.20 mm
vias; north trunk 1.5 mm B.Cu with a 0.6 mm neck through J5A's pin pitch; west
spine 1.5 mm; J20 branch 1.0 mm; bank 13 spine 0.6 mm F.Cu, 0.4 mm beside R18/R4;
ball lanes 0.22 mm, the widest that keeps both neighbouring dogbone rows on the
1 mm lattice. Calculated DC drop from C201 at 25 C, assuming 18 um via barrels:
**9.5 mV worst at board load; 43 mV at J19, 25 mV at the balls with both selectors
at 1.8 V.** Conductor sizing and connectivity do not prove transient power
integrity; decoupling and the 113 uF output capacitance still need bench
qualification (`ref/power-budget.md`).

B.Cu is now walled by the north trunk (y≈125) and west spine (x≈176): crossing
signals there need In2 or In5. PSRAM2/3 was planned around 626 reserved vias: every
other connected ball's dogbone, plus capacitor, memory and pull supply vias. 34 of
those sites are now real GND vias; the rest are unplaced. All fit, which shows
only that those vias fit. Slot
and bus signals have no onward routes yet, and PSRAM2/3 now uses the free
rows y 134–139 north of the BGA on In2, In5 and B.Cu.

**Resistor-adjacent via solder-mask geometry needs fabrication review.** Landing
and memory-side vias sit 0.095 mm from their own R104–R115 pads and 0.097 mm from
R116–R127 (measured, edge to edge) and DRC passes, but tenting or via fill
and the mask dam need the fabricator's answer.

Results after refill: DRC with parity **0 errors, 0 parity issues, 334 warnings**
(silk_overlap 199, capped; silk_over_copper 104; track_dangling 24; text_height 4;
lib_footprint_mismatch 2; isolated_copper 1). Ratsnest **1278**, from 1352 at the
U1 ground checkpoint, 1479 at PSRAM ground, 1509 at PSRAM2/3 and 1649 before routing, by `GetUnconnectedCount(True)`; the DRC
unconnected list stops at 499. The X4 mismatch comes from its bottom silk line,
opened over C337's pads on this board only; J1 and the isolated +1V0 fill predate
routing. `gate.py --strict` passes and reports **1449 tracks and 446 vias**, of which 228 vias are GND; both match
pcbnew.

To keep silk clear of the routing, UI_ROLE labels of U2, U3, U4 and X4 moved.
`update_silkscreen.py`, which `load_pcb.py` also runs, recreates those fields and
would undo this. U5's label still overlaps R125/R127 silk, as it overlapped
R125/R126 before these moves. Evidence and scripts:
`~/freyja-review/psram-pilot-2026-11-03/` (`transfer/`, `scripts/transfer.py`),
`~/freyja-review/1v8-io-2026-11-03/`, `~/freyja-review/psram23-2026-11-03/`
(`reports/verify_live.txt`, per-signal lengths, layers and vias) and
`~/freyja-review/psram-gnd-2026-11-03/` (`reports/verify_live.txt`,
`reports/continuity_live.txt`).

The cleanup status below predates this transfer: its tracks/vias and DRC counts
are the pre-routing baseline.

## Current status — 2026-11-03 repository cleanup

Starting commit: `3f76447e95960261cd3486e88a7cd382be51181f`; tracked/untracked
working tree clean. Existing ignored KiCad backups, Vivado build outputs
and Python caches were left in place. During the session the local `.prl`
selected layer changed from 25 to 6 and the editor lock disappeared; that
editor-state change is preserved, not restored over current work. See
[the current workflow](ref/ide-agent-prompt.md)
for ownership, generator side effects and the recurring cleanup checkpoint.

FREYA HW 0.1.0-proto.1 is the **100 × 140 mm, eight-layer** KiCad board with
XC7A100T-2FGG676I and RP2350B. The schematic has 551 parts; the PCB has those
551 plus board-only H1–H4. All 555 footprint origins are inside the outline's
bounding box, with zero B.Cu footprints. **Tracks/vias: 0/0; routing remains
unfinished.** The board is authoritative for current manual placement/zones.
Its five zones already contain saved fills; cleanup did not refill them.

Checks on the unchanged hardware, with identical results before/after cleanup:

- `tools/gate.py --strict`: electrical/mechanical PASS; netlist, XDC/gate top
  and parts-guide comparisons pass. ERC: zero errors and the two expected
  DXP/DXN warnings. Connector placement contract passes.
- Full DRC with schematic parity: **0 errors, 313 warnings, 499 unrouted
  items, 0 parity issues**. The explicit `--exit-code-violations` invocation
  exits 5, as expected for the remaining findings. Gate PASS is not a clean
  fabrication DRC.
- `tools/audit_easyeda.py`: **pre-existing FAIL**. F2/F6/F10/F14/F18/F22/F26/
  F30/F34/F38 select C269119 without a matching imported symbol. D3/D4 select
  C22452 without a matching imported symbol, and their imported footprint's
  LCSC property still says C8678. Reconcile the selected parts and imported
  metadata deliberately before the next part/library sync; do not substitute
  stock footprints or relax the audit. Libraries are unchanged in cleanup.
- `tools/check_connector_rework.py`: **pre-existing FAIL** at its exact
  PCB/netlist reference-set assertion. H1–H4 are board-only footprints and
  absent from the netlist; no schematic references are missing from the PCB.
  The checker stops there, so its later topology assertions are not certified
  by this run. Resolve its board-only accounting in a separate bounded change.
- Supplemental read-only parity confirms all 551 schematic footprints' values,
  footprint IDs and pad nets match; H1–H4 are separately confirmed board-only.
  Allocation checks, Markdown file links and Python syntax pass. The archived
  extractor reproduces all five saved outputs exactly in a disposable copy.
- Imported 3D models: six of 39 distinct live-board model paths name files
  absent from the repository even after mapping `KICAD_3RD_PARTY` to `easyeda/`.
  That variable is unset in the verification shell. See [project setup](kicad/README.md)
  for the pre-existing preview limitations; no models or identifiers changed.

The opening SHA-256 manifest covers 280 files. All 278 other files still
match exactly; only the local `.prl` active-layer preference and editor lock
changed as described above. In particular the PCB, all schematics, netlist,
`.kicad_pro` settings, `.kicad_dru` constraints, libraries/models and allocation
constraints are unchanged. All 33 relocated tracked files are accounted for;
archive notices/link fixes and the extractor's path guard are intentional edits.

Next routing work should review the 313 DRC warnings and saved zone geometry,
preserve the qualified land patterns, and account for the two checker failures
above. The impedance reference still labels RGMII geometry as an estimate;
FPGA power and prototype measurements remain qualifications, not cleanup fixes.
Cleanup made no circuit or library edits.

## Dated review record — historical

Everything below records earlier revisions, including completed tasks and
superseded conclusions. Do not treat item 5 onward or Part V as a current
open-task list. The [2026-10-29 practical audit](#final-practical-verdict)
reviewed `6ad8068`; later implementation/placement evidence is in
[the phase history](archive/history/rev-a-report.md). The
[archive index](archive/README.md) maps original export/report paths retained
in the prose to their current locations. Keep engineering rationale and dates;
revalidate any older statement before acting on it.

---

# Part I — historical (EasyEDA era, closed)

*Kept for the reasoning, not as open work. The netlist/BOM/pcbdoc revision
mismatch that these describe is moot now that the design is generated.*


## 1. BLOCKER — the netlist, BOM and pcbdoc are the *previous* revision

**Entities:** `Netlist_Odin_0_2026-09-02.net`,
`BOM_Odin_V1.0.0_Odin_0_2026-09-02.xlsx`, `Odin_V1.0.0/Odin_0.pcbdoc`
versus `Odin_V1.0.0/Odin/*.schdoc`.

**What is wrong.** The netlist and BOM agree with each other exactly (0
designators netlist-only, 0 BOM-only) and both agree with the pcbdoc. All
three describe a **single-FPGA ECP5 board programmed over an FT232H**. The
schdoc export describes a **different, later board**: Artix-7 + ECP5 + RP2040
with a new power tree. Only 9 of 40 schdoc part types appear in the netlist
(`odin.srcdiff`).

Present in the schdocs, absent from netlist/BOM/pcbdoc:

| Part | Schdoc symbols | Role |
|---|---|---|
| `XC7A50T-2CSG325I` | 8 | the Artix-7 that Goals 1–2 are about |
| `RP2040_C2040` | 1 | the supervisor that Goal 1 is about |
| `W25Q32JVZPIQ` | 1 | RP2040 boot flash |
| `TPS563257DRLR` | 6 | new buck rails |
| `TPS55340RTER` | 1 | boost |
| `TPS25940ARVCR` | 1 | eFuse |
| `APS1604M-3SQR-SN` | 4 | PSRAM |
| `SN74LXCH8T245PWR` | 4 | level shifters |
| `ADS7950SBRGET` | 1 | ADC |
| `2.54-2*8P_`, `PM2.54-1X8PM-H85`, `ZX-PZ2.54-2-4PZZ`, `PH2.54-01-03PZD` | 6/4/4/4 | new extension headers |

Present in netlist/BOM/pcbdoc, absent from the schdocs: `FT232HQ-REEL`,
`IS61WV25616BLL-10BLI`, `FM25V02A-GTR`, `TLV62569DRLR` ×3, `TPS54202DDCR` ×4,
`TYPE-C-31-E-07`, `TYPE-C-31-M-12`, `PS-1049SVD-4PN`.

**Consequence for the prompt's ground rules.** The prompt makes the Protel
netlist the identity source and forbids citing schdoc refdes. That rule cannot
be satisfied: the netlist contains no Artix-7 and no RP2040, so there is no
real designator to cite for any part in Goal 1. Symbol matching bears this
out — 25 of 230 schdoc symbols map to a netlist part (`odin.desigmap`), and
the matches are confined to the 9 shared part types.

**Proposed change (EasyEDA).** Re-export both the Protel netlist and the BOM
from the schematic that contains the Artix-7 and RP2040 — the one exported to
`Odin_V1.0.0/Odin/`. In EasyEDA Pro the netlist is exported per board, and
`Odin_0` is the old board; the new schematic appears to have no board/PCB yet,
which is why its netlist was never produced. If the new schematic needs a PCB
created before a netlist can be exported, that is the prerequisite step.

---

## 2. BLOCKER — the ECP5 is still instantiated in the new schematic

**Entities:** `LFE5U-25F-6BG256C`, 9 symbol parts on `fpga.schdoc`.

**What is wrong.** You have confirmed the ECP5 is a mistake and the board is
meant to be dual Artix-7. It is not a stray symbol: in the *old* netlist the
same part is `U1` with **170 connected balls**, driven through an
`SN74CB3T3245PWR` level shifter on a `TOL_*` bus. Whatever of that carried
into the new schematic is real wiring, not a placement error, so removing it
is a schematic-scale edit rather than a symbol delete.

**Proposed change (EasyEDA).** Delete the `LFE5U-25F-6BG256C` symbol parts
from `fpga.schdoc` and replace with a second `XC7A50T-2CSG325I`. The second
Artix-7 needs its own config chain — flash, `PROG_B`/`INIT_B`/`DONE`, `M[2:0]`
strap, JTAG — which feeds directly into item 3.

**Blocked on item 1**: I cannot enumerate which nets the ECP5 currently holds
in the *new* schematic, only in the old one.

---

## 3. BLOCKER — RP2040 GPIO count cannot carry Goal 1; assume RP2350B

Per your decision, the review will be run against an **RP2350B (48 GPIO)** and
the swap reported as a blocker. The sizing that forces it, for a dual Artix-7
board with the supervisor scope in Goal 1:

| Function | GPIO |
|---|---|
| Config flash SPI (CS, CLK, MOSI, MISO), shared across both FPGAs | 4 |
| Second flash CS (one CS per FPGA, bus shared) | 1 |
| FPGA A config: `PROG_B`, `INIT_B`, `DONE`, `CCLK`, `DIN` | 5 |
| FPGA B config: same | 5 |
| `M[2:0]` ×2 — driven, not hard-strapped, to switch master-SPI vs slave-serial | 6 |
| FPGA JTAG (TCK/TMS/TDI/TDO), both parts daisy-chained on one port | 4 |
| Fabric sideband JTAG for NEORV32 debug | 4 |
| Sideband UART TX/RX | 2 |
| Spare GPIO bus | 4–8 |
| Regulator enables (8 rails: 6× buck, boost, eFuse) | 8 |
| Power-good readback | 8 |
| Extension board-ID | 2–4 |
| **Total** | **53–59** |

Against 30 on an RP2040 this overflows by roughly 2×; against 48 on an
RP2350B it still overflows unless something gives. The cheapest reductions
that keep the "direct wiring" philosophy:

- **Hard-strap `M[2:0]`** to master-SPI and reach slave-serial by holding
  `PROG_B` and driving `CCLK`/`DIN` only — saves 6, and `M[2:0]` is a
  build-time choice, not a runtime one.
- **Share one JTAG port** across both Artix-7s via the standard daisy chain —
  already assumed above, saves 4.
- **Power-good as a single wired-OR fault line** plus per-rail readback over
  the ADC already on the board (`ADS7950SBRGET`, 12-bit 16-ch) — saves 7,
  and rail voltage readback is strictly better information than a PG bit.

With those three, the count lands near **40**, which fits a RP2350B with
headroom for the spare bus. This is a proposal, not a verified finding —
confirming it needs item 1.

---

## 4. Extension connector keying — the 16-pin unit reads as 14 + 2

You asked me to work out the pattern. From the old netlist, where the
connectors are fully wired, one group is:

- `J4` `2.54-2*7P母` — 2×7 female, **14 pins**
- `H5` `3-644456-2` — 2×1, **2 pins**
- `P3` `2.54-1*1P针` — 1×1 male post, **1 pin**

14 + 2 = **16 pins = 8 columns × 2 rows**, with the 1×1 post as the
polarizing key. There are 8 of each (`J4–J11`, `H5–H12`, `P3–P10`), so the old
board carries **8 × 16 = 128 positions**, i.e. two 64-pin extension sites of
four 16-pin patterns each — which is the 16/32/64 prefix rule you described,
and the split into a 7-column block plus a 1-column block is what makes the
mating polarity unambiguous.

Two cautions. First, this is the **old** board; the new schdocs carry a
different connector mix (`2.54-2*8P_` ×6, `PM2.54-1X8PM-H85` ×4,
`ZX-PZ2.54-2-4PZZ` ×4, `PH2.54-01-03PZD` ×4 alongside the 8× `2.54-2*7P_` and
8× `3-644456-2`), so the new pattern is not yet 14+2. Second, your arithmetic
"8+7+1" counts *columns* and reaches 16 columns (a 2×8 block + a 2×7 block + a
key), which matches the new schdoc's part mix rather than the old board's. If
16 **columns** (32 pins) is the intended unit, then a 64-**column** extension
is 128 pins, and the new mix is the right one. Which of the two — 16 pins or
16 columns — is the unit needs to be your call; item 1 has to land first
either way, since `ref/extension-pinout.md` needs real designators and FPGA
bank data.

---

## Steps not yet run

| Step | Status |
|---|---|
| 0 setup | done — baseline commits, `ref/adabmp` cloned, `extract.py` read |
| 1 netlist-first IR | tooling done; output is of the wrong revision (item 1) |
| 2 FPGA datasheet facts | not started — blocked on the Artix-7 count (item 2) |
| 3 power review | not started — the new power tree is in no netlist |
| 4 config/boot review | not started — no RP2040 in any netlist |
| 5 extension connector | not started — see item 4 |
| 6 Gameboy gap analysis | not started — depends on step 5 |
| 7 BOM check | partial — the BOM is self-consistent with the old netlist; every placed part has an LCSC number; see below |

**Step 7, valid only for the old revision.** Zero JLCPCB stock:
`TC211A106M016Y` (C128289, 10 parts) and `CA45-A6R3K226T` (C122912, 4 parts).
Near-zero: `RT1206FRE07120KL` (C136861, stock 9), `2NM27000C33YC` (C668764,
stock 3), `1SMA5918A` (C19077487, stock 71), `FT232HQ-REEL` (C82158, stock 28)
— the FT232H is being removed anyway. 51 of 56 BOM lines are Extended Part;
only `0603WAF8202T5E`, `0603WAF5101T5E`, `0603WAF200JT5E` are Basic. Most of
the Extended lines are ordinary 0402/0603 passives with Basic equivalents;
that consolidation pass is worth doing once the BOM is re-exported, not now.


---

---

# Part II — live, against the current KiCad design

## 5. FIXED — differential oscillator pinout confirmed

**Entities:** `X2`, `DSC1123CI2-125.0000` (`C617173`), footprint
`EasyEDA:OSC-SMD_6P-L3.2-W2.5-BL`.

The Microchip datasheet and imported part agree: 1 EN, 2 NC, 3 GND, 4 OUT+,
5 OUT-, 6 VDD. This differs from the old assumed mapping; the schematic now
uses the imported exact symbol and footprint.

## 6. FIXED — MGTRREF was connected to the wrong rail

**Entities:** `R35` (formerly `R30`), 100R 1% 0603, from `U1.A15`
(`MGTRREF_216`, FGG676) to `+1V2_MGT` (MGTAVTT).

The old circuit used 100R to GND with no explicit tolerance. The ground
connection was wrong. [UG482 v1.9, Figure 5-1 and pp. 217–219](https://0x04.net/~mwk/xidocs/ug/ug482_7Series_GTP_Transceivers.pdf#page=218)
specifies 100 ohm, 1% to MGTAVTT for Artix-7 GTP calibration, not 499/500 ohm
to GND. The design source, schematic, netlist and PCB now specify `100 1%`
and connect the resistor to the 1.2 V MGT supply. This closes the schematic
error; high-speed link performance still requires hardware validation.

## 7. FIXED — board outline now matches the mechanical contract

`kicad/odin.kicad_pcb` is now 100 x 100 mm, matching the required board size.
(Superseded 2026-11-03: the outline is 100 x 140 mm, see `floorplan.md`.)
A–H use four continuous 2x16 signal bodies plus four parallel 1x16 power
bodies (two logical zones per body), plus two complete 5V-bus signal and power
connector pairs. Placement
and routing remain deliberately absent. The exact stack-through connector MPN
is still a mechanical purchasing choice; the schematic fixes 2.54 mm pitch.


## 8. FIXED — nonexistent extension board-ID promise removed

**Entities:** `ref/extension-ux.md`, the nine slot connectors, `PD_CFG1..3`.

An earlier `ref/extension-ux.md` stated that each module had board-ID pins so
the supervisor could tell what was plugged in. **It had none.** The four
`BOARDID_*` nets that existed went to the supervisor and a pull-down each and
reached no connector; they have since been repurposed for the USB-PD sink,
which genuinely needed them.

The options considered were:

1. **Give up one I/O per module** for a strapped ID pin.
2. **Drop the claim.** Extensions are identified by the human. Honest, and
   costs nothing but the feature.
3. **Widen the module** solely to add identification.

Option 2 was chosen. The claim and dead nets are gone. The newer third power
row is used for clear, well-grounded power distribution, not to silently
reintroduce an identification protocol. The supervisor still power-gates the
extension rails and reports SFP module identity.


## 9. FIXED — the supervisor could not enable its own power rail

`EN_3V3` was driven by supervisor GPIO21 and gated `U12`, which produced the
+3V3 that powers the supervisor. A deadlock: the board could never start.
`EN_5V` compounded it, since +3V3 was derived from +5V.

Fixed: +3V3 is now always on, from a wide-input `AP63300` (`U12`) straight off
`VSYS`. Its datasheet permits automatic startup with EN floating, so no GPIO
is involved. GPIO21 was freed and reused for the VBUS pass switch below.

## 10. FIXED — a Schottky from VBUS to the 5V rail was an overvoltage hazard

`D2` fed USB `VBUS` into the +5V rail so the board could run from a plain 5 V
source. The moment the PD sink negotiated 9 V, that diode would have put
~8.6 V onto a rail feeding four `TLV62569` regulators rated 5.5 V maximum —
destroying them on the first PD handshake.

Fixed: replaced with a supervisor-commanded high-side switch (`Q2` P-MOS,
`Q3` gate driver), **default open**. Firmware measures `VSYS` and only closes
it when the input really is 5 V.


## 11. CLOSED — level translator pinout confirmed

**Entities:** `U9`, `U10`, symbol `odin:SN74LXC8T245PW`.

The original `SN74AVC8T245PW` was wrong: the AVC family is specified for
1.2–3.6 V supplies and 5 V on `VCCB` exceeded its absolute maximum. It has been
replaced with `SN74LXC8T245PW` (1.1–5.5 V both rails).

KiCad ships no symbol for it, so the generated one is AVC8T245's symbol
renamed. That mapping has since been checked against TI's TSSOP-24 pinout for
`SN74LXC8T245PW` — 1 `VCCA`, 2 `DIR`, 3–10 `A1..A8`, 11–13 `GND`, 14–21
`B8..B1`, 22 `OE`, 23–24 `VCCB` — and matches. **Closed.**

## 12. FIXED — two complete 5V buses replace the 8+2 orphan

`SN74LXC8T245` is direction-controlled: one `DIR` pin steers eight signals
together. An earlier Slot L was an eight-bit bus plus an awkward two-bit tail,
costing 12 FPGA I/O for ten connector signals. A two-bit Nexperia converter
was briefly qualified for that tail, but optimizing the orphan did not fix the
interface. Odin now provides two identical complete eight-bit 5V buses, each
with one direction control. The second bus uses fixed bank 13.

`ref/extension-ux.md` now says this plainly. If per-pin bidirectional 5 V is
actually wanted, the part is a `TXB0108`-class auto-direction translator,
which trades away drive strength and forbids external pull-ups. There is no
option that gives strong drive, per-pin direction and 5 V at once.

## 13. partly fixed — qualify the placeholder components before layout

Inductor saturation current and capacitor voltage rating are not purchasing
details — a 22 µF 6.3 V part on the 12 V AUX rail fails immediately, and an
undersized inductor saturates under load. These need real part numbers
**before layout**, not before ordering, because package size affects
placement.

**Done since:**

- **A qualified-parts table exists and is enforced.** `tools/qualified.py`
  records MPN, manufacturer package code, footprint, the ratings that matter
  on this board, and how the pin map was confirmed, for every non-generic
  part. `tools/design.py` refuses to build if a part is missing from it or is
  fitted with a different footprint, so a new IC cannot enter the netlist
  anonymously. Rendered to `ref/qualified-parts.md`.
- **Every inductor is selected and checked.** `tools/budget.py` computes the
  ripple, peak current and required saturation current per rail and names the
  part: `SRN6045TA-100M` (10 µH, Isat 4.6 A) on `U11` and the boost,
  `SRN6045TA-4R7M` (4.7 µH, Isat 6.8 A) on `U12`, `SRN4018-2R2M`
  (2.2 µH, Isat 3.0 A) on the four `TLV62569`s,
  `SRN4018-1R0Y` on the MGT filter, and the mandated Abracon part on the
  supervisor. The tool fails if any of them saturates below its rail's
  requirement.
- **MOSFETs are real parts.** `Q1` and `Q2` are `DMG2305UX`; `Q3` is a
  `BSS138`. Reading the DMG2305UX datasheet is what turned up item 21.
- **Capacitors on rails above 3.3 V carry their rating in the value field**,
  set automatically from the net rather than typed: `25V` on `VSYS`, `VBUS`
  and `+12V`. Everything unmarked is 16 V minimum, X5R or better.

**Still open:**

- The SFP electrical connectors are selected; their separate metal cages are
  still not encoded because the `C5164658` mechanical import failed.
- The nine 300 mA +3.3 V polyfuses still need an exact MPN. The 200 mA and
  500 mA positions are selected.
- **Capacitor DC-bias derating is not accounted for.** A 22 µF 25 V X5R 0805
  at 12 V retains well under half its nominal value. The bulk capacitance is
  ample enough that this is unlikely to bite, but "22 µF" on the `VSYS` rail
  means perhaps 8 µF in circuit and nothing in the design says so yet.
- The ~340 ordinary passives can take LCSC numbers later via the JLCPCB
  plugin.

## 14. open — the 16/32/64 mechanical claim is unproven

Adjacent 16/32/64 module compatibility is a *mechanical* property: it depends
on slot pitch, board-edge geometry and the position of the keying posts, none
of which exist until placement. The electrical numbering supports it. Verify
it on the board, and until then treat the claim in `ref/extension-ux.md` as an
intent rather than a fact.


## 15. FIXED — the JTAG owner is now selected in hardware

`J2` sits directly in parallel with the FPGA's JTAG nets. The supervisor is
separated only by its 33 R series resistors, so an external programmer and a
misbehaving supervisor GPIO can both drive the same line. The comment claiming
a jumper isolates the supervisor was wrong and has been corrected.

Two ways to make it true:

1. **Firmware contract** (currently assumed): the supervisor tri-states
   GPIO0–3 whenever an external programmer may be attached, and does so as its
   *reset default*, not only when asked. Free, but it depends on firmware
   being correct — which is a poor guard for a debug path you reach for
   precisely when things are broken.
2. **A bus switch** (`SN74CB3T3245`, the part Odin_0 used) between the
   supervisor and the JTAG net, with its enable strapped or jumpered. Real
   isolation. Costs one part and one control line, and there is no spare
   supervisor GPIO — it would have to be a physical jumper.

Recommendation: option 2 with a jumper, because "hold the board in a known
state so I can debug it" should not itself depend on working firmware.

**Fixed with option 2.** `U20` is an `SN74CB3Q3384APW` 10-bit FET bus switch;
the supervisor's four JTAG lines pass through bank 1 (`1A1..1A4` to
`1B1..1B4`) on their way to the FPGA and to `J2`. `~{1OE}` is held low by a
10 k pull-down, so the switch is closed and the supervisor owns JTAG in the
shipped state — that is the primary programming path and it has to work out of
the box. Fitting **`EXT JTAG` (`J52`)** pulls `~{1OE}` to +3V3
and takes the supervisor electrically out of the chain, whatever its firmware
is doing. The controlling net is named `EXTERNAL_JTAG_SELECTED`, so its high
state says exactly what happened.
Bank 2 is unused with `~{2OE}` tied high.

This adds one intentional ERC warning: the FPGA's `TDO` output meets a
tri-state switch pin, which is what a FET bus switch pin always looks like to
ERC.

## 16. FIXED — RP2350 support parts now match the reference design

`U7`'s internal switcher uses a generic `3.3uH SRN4018` inductor and generic
15 pF crystal loading capacitors. Raspberry Pi's hardware-design guide is
explicit that RP2350's on-chip regulator depends on the prescribed inductor
selection, orientation and placement, and on specific capacitor choices.

This is a **netlist-level** task, not a layout note: copy the exact component
values and manufacturer part numbers from the RP2350B minimal-board reference
into `tools/design.py`, then follow the placement guidance during layout.
Getting this wrong produces a supervisor that mostly works, which is the worst
failure mode available.

**Fixed, from RP-008280 sections 2.1, 2.2.1, 3 and 4:**

| Reference | What it is | Now in the netlist |
|---|---|---|
| `L1` | `AOTA-B201610S3R3-101-T`, the 3.3 µH part Abracon made for Raspberry Pi with a polarity dot | `L1`, on a generated `odin:L_Abracon_AOTA-B201610S_2.0x1.6mm` land taken from the datasheet's Recommended Land Pattern (1.00 × 1.60 mm pads, 1.00 mm gap) |
| `C6`, `C7`, `C9` | 4.7 µF 0402 at `VREG_VIN`, at the output, and on `VREG_AVDD` | three 4.7 µF 0402 |
| `R3` | 33 Ω, RC-filtering the analogue supply | 33 Ω 0402 into net `SUP_VREG_AVDD` |
| `Y1` | `ABM8-272-T3`, 12 MHz, CL 10 pF, ESR 50 Ω max | named in the value field |
| `R2` | **1 kΩ in series with `XOUT`**, so the crystal is not over-driven | added; it was missing entirely |
| `C3`, `C4` | 15 pF at the crystal terminals | were already right, and now sit on the crystal side of `R2` |
| `R1` | 10 kΩ pull-up on `QSPI_SS`, shipped Do-Not-Fit | added, DNP |
| decoupling | one 100 nF per supply pin | 11 on +3V3 (8 IOVDD, QSPI_IOVDD, USB_OTP_VDD, ADC_AVDD) and 3 on +1V1 (3 DVDD) |

The 1 kΩ `XOUT` resistor is the important one: without it the crystal is
over-driven, which is a slow reliability failure rather than an obvious one.

**Still a layout obligation.** Raspberry Pi are explicit that the regulator's
performance depends on the inductor's *orientation* as well as its part
number, and on their exact placement. The footprint carries a polarity dot on
silk and a solid pin-1 marker on `F.Fab` so the requirement survives into the
assembly drawing, but honouring it is placement work, guided by RP-008280
Figure 4.

## 17. FIXED — eleven components had footprints for the wrong package

Symbol and footprint disagreed on the physical package for `U2`–`U6`, `U8`,
`U13`–`U16`, `U17`, `U18`, `U19` and `D6`. Neither ERC nor schematic parity can
see this class of error; it surfaces at assembly.

Corrected: PSRAM to SOP-8 150 mil, `W25Q256JVEIQ` to WSON-8 8x6, `W25Q32JVZP`
to WSON-8 6x5, `TLV62569DRL` to SOT-563, `CH224K` to SSOP-10-1EP, `PCF8574T`
to SOIC-16W, `TPS61085PW` to TSSOP-8 4.4x3, `ESDA6V1BC6` to SOT-23-6.

**Prevented from recurring:** `Design.add()` now checks every footprint against
the symbol's `ki_fp_filters` and refuses to build on a mismatch. The one
deliberate exception is the polyfuse, where KiCad ships no `*polyfuse*`
footprint and a 1206 chip PTC is the physically correct package; that override
is explicit in the source and carries its reason.

## 18. FIXED — per-slot fuse ratings implied nine times the available current

Nine slots x 500 mA suggested 4.5 A per rail. The real sources are far
smaller. Fuse ratings have been rebalanced (AUX 200 mA, +3V3 300 mA, +5V
500 mA) and `ref/extension-ux.md` states the shared budget per rail
explicitly, with the note that fuses are fault protection and not an
allowance.

The `~700 mA` first quoted for AUX was `5 V x 2 A x η / 12 V` — an ideal
upper bound from a nominal switch rating, not an available current. It has
been replaced by TI's own design procedure (SLVS859B equations 1–4) at the
worst-case input, run by `tools/budget.py`:

- the boost, with a 10 µH inductor at 650 kHz and the **2.0 A minimum**
  switch limit, can deliver **622 mA**;
- but AUX at full output draws 1766 mA from a +5 V rail with 1615 mA spare,
  so the binding limit is **570 mA**, and the constraint is the 5 V rail, not
  the boost;
- and that is still arithmetic at an assumed 90% efficiency with no thermal
  derating, so it is published as a **provisional design target**.

The inductor changed as part of this: 4.7 µH at 650 kHz sat outside TI's
recommended 6–13 µH range and gave 69% ripple. 10 µH gives 26% ripple *and*
more output current.

Every other shared-rail figure was equally unsubstantiated. `+3V3` was
described as having "~1.5 A spare"; the worst-case load table puts it at
**500 mA**, because `U12` also carries the supervisor, four PSRAMs, the config
flash, FPGA bank 14, the oscillator, two SFP modules (610 mA on their own) and
both VCCIO domains when they are jumpered to 3.3 V. See
`ref/power-budget.md`.

## 19. constraint — firmware must never request more than 9 V over USB-PD

`D7` is an `SMBJ13A`, a 13 V standoff TVS on `VBUS`. The `CH224K`
configuration pins are supervisor-driven, so this limit lives in firmware and
must be an assertion there, not a comment. Raising the ceiling means
re-selecting `D7` first.

Two corrections to how this was first written. The mechanism is **avalanche,
not forward conduction**: the part is unidirectional with its cathode on
`VBUS`, so a 20 V contract drives it into sustained reverse breakdown, which a
600 W *transient* device does not survive as a DC condition. Forward
conduction is what happens if it is fitted backwards, which is a different
failure — and the reason the schematic no longer uses KiCad's bidirectional
`Device:D_TVS` symbol. And the margin is narrower than "13 V" suggests but not
zero: `VBR` is 14.4 V minimum, so a 15 V contract sits in the region above the
rated standoff where leakage climbs steeply rather than in hard avalanche.

## 20. FIXED — the always-on +3V3 rail now starts on a weak 5 V port

**Entities:** `U12` (`AP63300WU-7`), `D3`, `U26`, net `VSYS`.

The original `TPS54202` needed 4.5 V at its input, while the weak-host path
could provide only about 4.24 V after protection and OR-ing. It was therefore
wrong for the one rail that must always start.

`U12` is now an `AP63300WU-7`, rated from 3.8–32 V and 3 A. The worst-case
path is now:

| | |
|---|---|
| `VBUS` on a weak host port, guaranteed minimum | 4.75 V |
| less `D3` forward drop | −0.45 V |
| less conservative `U26` on-resistance drop | −0.03 V |
| **`VSYS`** | **4.27 V** |
| `AP63300` minimum input voltage | **3.8 V** |

That leaves 0.47 V of startup margin. Its 3.3 V feedback network, 4.7 µH
inductor, input capacitor, three output capacitors, bootstrap capacitor and
feed-forward capacitor copy the manufacturer's reference circuit.
`tools/budget.py` checks its full load and inductor peak current and passes.

## 21. FIXED — Q2 gate overvoltage under a 9 V firmware fault

**Entities:** Q2 (DMG2305UX), Q3, R49, EN_VBUS5.

R49, between VBUS5_PULL and VBUS5_GATE, is now **47k**, replacing 10k.
Together with the existing 100k gate-source pull-up, it sets
`VGS = -VBUS * 100/(100+47)`: -3.40 V at 5 V and -6.12 V at 9 V.
Even 9.45 V with 1% resistor tolerances gives only 6.47 V magnitude,
below the [DMG2305UX's ±8 V gate limit](https://www.diodes.com/datasheet/download/DMG2305UX.pdf).

The weaker gate drive at 5 V increases on-resistance compared with -4.5 V
characterization. With the existing 100nF gate-source capacitor, the gate
RC time constant becomes approximately **3.20ms**; it is not a specified
linear output ramp or current limiter. Firmware must still forbid turning
Q2 on at 9 V, because doing so overvolts the +5V rail and its loads.

## 22. FIXED — screw-terminal input lacked a transient clamp

**Entities:** J50, new D8, VIN_EXT, D4, VSYS.

Added **SMBJ15A-13-F / C135046** on VIN_EXT, before D4, with cathode on
VIN_EXT and anode on GND. The standard SMB footprint uses pad 1 cathode,
pad 2 anode. Put it at J50 with a short, wide surge-current return to J50 GND.

[Diodes rates this unidirectional TVS](https://www.diodes.com/part/view/SMBJ15A)
at 15 V standoff, 16.7–19.2 V breakdown, 24.4 V maximum clamp at its rated
pulse current, and 600 W pulse power. It suppresses transients; it is not a
15 V regulator or a sustained-overvoltage disconnect. A bench supply left
at 24 V can still overload the TVS. The permitted input remains **9–14 V**;
continuous fault protection would require current limiting/fusing or cutoff.
PCB parasitic overshoot and surge energy still require validation.

## 23. FIXED — the `VSYS` monitor divider overdrove the supervisor's ADC

**Entities:** `MON_VSYS`, `MON_5V`, `GPIO40/ADC0`, `GPIO41/ADC1`.

The divider was 100 k / 33 k, which is 33/133 of the input. At 9 V that reads
2.23 V and is fine. At the 20 V `ref/power-input.md` then permitted on `J50`
it reads **4.96 V** — onto an RP2350 GPIO whose maximum is `ADC_AVDD`, 3.3 V.
A rail monitor that destroys the microcontroller in the fault it exists to
report is the wrong way round.

Fixed by sizing every monitor divider from an **absolute maximum**, not a
nominal:

| Monitor | Divider | Nominal reading | At absolute maximum |
|---|---|---|---|
| `MON_VSYS` | 100 k / 16 k | 1.24 V at 9 V | 2.76 V at 20 V |
| `MON_5V` | 100 k / 47 k | 1.60 V at 5 V | 2.88 V at 9 V |

`MON_5V` was 100 k / 100 k, safe at 5 V and 4.5 V in the same firmware fault
item 21 describes; it is now sized for that fault too.

`tools/design.py` computes both from `adc_divider()`, which rounds the bottom
resistor **down** through E24 — rounding to nearest can put the result back
over the ceiling — and raises if the absolute maximum would exceed 3.0 V.
E24 rather than E96 because firmware calibrates a monitor ratio, so precision
buys nothing and stock availability buys something.

Each of the six monitor nodes also gained a 100 nF capacitor. Two reasons: the
ADC's sample-and-hold needs charge that a 14 kΩ Thevenin divider cannot
supply, and firmware compares these readings against thresholds, so switching
ripple should not be in them.

## 24. FIXED — USB attach inrush exceeded the specification by 5x

**Entities:** `U26`, `D3`, `VBUS`, `VSYS`.

USB limits a device's `VBUS` bypass capacitance to 10 µF, or 50 µC of inrush
charge; USB-PD raises that to `cSnkBulkPd` = 100 µF only *after* a contract
exists, and at cable insertion there is no contract. The board presented
10 µF on `VBUS` plus 44 µF of `VSYS` bulk through a forward-biased `D3` —
about 54 µF and 270 µC, five times the allowance. Symptoms would have been
source droop, connector arcing, and starting reliably on some chargers and not
others.

Fixed with `U26`, a `TPS259470A` eFuse. Its 2.2 nF `dVdt` capacitor sets an
approximately 0.91 V/ms output rise, so 44 µF charges at about 40 mA. It is
autonomous rather than firmware-controlled: this path produces +3V3, which
firmware needs in order to exist. UVLO is about 3.75 V, OVLO about 9.98 V and
the typical current limit about 2.03 A. The 10 µF left directly on `VBUS` is
the attach allowance, spent deliberately.

`Q2` has a series gate resistor and 100 nF gate-source capacitor because
closing it connects `VBUS` to 66 µF of +5V bulk. R49 is now 47k (item 21),
giving a 3.20ms gate RC time constant with the 100k pull-up. This provides
slew control, not a specified inrush-current limit.

Unlike the passive RC, the eFuse also controls PD voltage-transition current
and disconnects on an overvoltage request. `D7` remains the independent TVS;
firmware must still enforce the 9 V PD ceiling in item 19.

## 25. FIXED — extension power faults could reach the base-board rails

**Entities:** `U21`–`U25`, `EXT_EN`, `EXT_FAULT`, all slot power PTCs.

Every connector rail previously branched directly from an internal rail. A
short, back-powered shield or large startup capacitor could therefore pull
down or energize the FPGA, supervisor and memories through the shared source.

There are now five protected connector buses. Four `TPS22950CDDCR` switches
protect +5 V, +3V3 and the two selectable VCCIO domains. A
`TPS259470LRPWR` protects +12 V with true reverse blocking, 13.2 V nominal
OVLO, a 500 mA typical limit, controlled rise and latch-off. All switches have
a hardware-default-off `EXT_EN`; their fault outputs wire-OR to `EXT_FAULT`.
The old per-slot PTCs remain downstream.

`TPS22950C` has an off-state output-discharge path. With an extension applying
5 V, its nominal 160 Ω path draws about 31 mA and dissipates about 0.16 W;
reverse current into the internal source remains blocked. Its output absolute
maximum is 6 V, so this closes the stated 5 V-on-low-rail mistake, not an
arbitrary 12 V miswire. That boundary is now explicit in the user documents.

## 26. FIXED — larger FPGA has a 4 A 1.0 V supply

**Entities:** `U1`, `U15`, the +1V0 inductor, the future FPGA image.

`U1` is now `XC7A100T-2FGG676I` (`C1521803`) in the imported 676-ball,
27 x 27 mm package. Its 676 symbol pin numbers match all 676 footprint pads,
every supply ball is connected. Both GTP supply groups remain powered:
G10 serves quad 213 and G11 serves quad 216 (UG482 Table 5-2).

The unused-quad wiring is now corrected in `tools/gen_sch.py:net_for()`.
Quad 213 has all eight RX pins grounded and its own 100R 1% resistor (`R89`)
from `MGTRREF_213` to MGTAVTT; its TX and reference clocks float. Quad 216's
unused lanes 2/3 also have their RX pins grounded and TX pins floating.
These follow [UG482 Tables 5-5 and 5-6](https://0x04.net/~mwk/xidocs/ug/ug482_7Series_GTP_Transceivers.pdf#page=223).

U15 is now a 4 A `SY8047QDC` (`C3018651`) with its datasheet reference circuit
and a 1 uH `FTC201610S1R0MBCA` (`C5832342`). At the conservative 1.5x FPGA
transient target, calculated peak inductor current is 2.80 A and the project's
required saturation rating is 3.64 A; the fitted inductor is rated 4.60 A.
The power audit passes. AMD XPE remains useful before fabrication, but it is
no longer needed to justify an undersized regulator.

## 27. FIXED — press-fit SFP cages replaced with solder-tail cages

**Entities:** SH1/SH2, J60/J61, `tools/placement.py`.

TE 2007198-1 was a press-fit part unsuitable for the requested JLC solder
assembly. SH1/SH2 now use **Amphenol U77A11133001 / C5355132**, which JLC lists
as Extended with wave soldering for Economic and Standard PCBA. The
standalone cage's host-board pattern matches the TE connector datum, so
**1888247-1 is retained** and no integrated connector/cage replacement is
needed. A new drawing-based `odin` footprint replaces the old cage import.

The connector depth is **35.40 mm from PCB edge** (34.50 to cage datum F,
then 0.90 to the locating-peg centreline), or 42.40 mm from the cage mouth.
The mouth overhang is 7.00 mm. Placement now uses an explicit edge-datum
origin and correct relative cage/connector rotations. TE's two connector
locating holes are also corrected from the import's 1.70 mm plated holes
to the specified 1.55 mm NPTH.

Amphenol lists this cage at **2.5 Gb/s**; the old TE cage's 16 Gb/s rating
is not retained. Higher-rate operation remains unqualified. See
the former `ref/sfp-cage.md` (removed before cleanup; see the
[historical phase report](archive/history/rev-a-report.md)).

## 28. FIXED — DONE LED loaded the open-drain configuration signal

**Entities:** CFG_DONE, R7, D1, new R98 and Q4, SUP_DONE.

D1 previously drew current directly from DONE through 330 ohms. Its brightness
and the DONE high level therefore depended on the weak pull-up or an actively
driven DONE output. The circuit no longer uses DONE as an LED supply.

R98 adds 4.7k from CFG_DONE to +3V3 (bank 0 VCCO). Q4, BSS138LT1G / C82045,
has gate on CFG_DONE, source on GND and drain on D1's cathode. The LED current
path is +3V3 → R7 (330 ohms) → D1 → Q4 → GND. With the specified green LED's
2.0–2.6 V forward drop, expected current is approximately 2–4 mA. DONE sees
the MOSFET gate and the existing supervisor input path, not that LED current.
The added pull-up draws about 0.70 mA when DONE is held low.

No `DriveDone=Yes` requirement is imposed on reference bitstreams. The LED
illuminates when DONE is released high and extinguishes when DONE is low;
SUP_DONE retains its existing connection. This follows the default open-drain
behavior described in [AMD UG470](https://docs.amd.com/v/u/en-US/ug470_7Series_Config).
Q4's low-voltage switching rating is checked against the
[onsemi BSS138LT1/D datasheet](https://www.onsemi.com/pdf/datasheet/bss138lt1-d.pdf).
The LED reports the DONE level, not application health, and is not a reliable
indicator during supply ramp-up.

## 29. FIXED — PUDC_B low strap was too weak

R6 is now **1k** (0402, C11702), from PUDC_B to GND, replacing 4.7k.
This follows the ≤1k strap recommendation in
[AMD UG470, Configuration Pins](https://docs.amd.com/v/u/en-US/ug470_7Series_Config)
and retains the intended internal I/O pull-ups during configuration.
Generator, schematic, netlist and PCB are synchronized; R6's connections
and physical placement are unchanged.

## 30. FIXED — two SFP EEPROMs collided on the shared I2C bus

**Entities:** J60/J61, U27, C231, R99–R103, SFP_SCL/SFP_SDA.

Both modules formerly connected their fixed-address 0x50 EEPROMs directly
to the same bus. Added **PCA9543APW,118 / C2652904** at 0x70, with one
channel per cage and separate downstream pull-ups. Both modules can remain
powered while firmware enumerates them separately. This chooses the mux
option; Q1 and U17 P7 retain shared power control. Documentation now states
that power removal affects both ports.

Select 0x01 or 0x02, finish selection with STOP, then read 0x50; never
select 0x03. Deselect with 0x00 before shared power-off. RESET is tied to
SUP_RUN, providing a hardware recovery path if a module holds I2C low;
a software controller reset alone may leave the mux selected. These rules,
startup handling and stuck-bus limits are in the former `ref/sfp-i2c.md` (removed before cleanup; see the
[historical phase report](archive/history/rev-a-report.md)),
with the NXP datasheet and procurement links. Firmware remains to be written.

## 31. FIXED — PSRAM series termination was documented but absent

Added **R104–R127**, 24 populated 33 ohm 0402 resistors (C25105), one on
each port's SCK, CE_B and IO0–IO3. FPGA-side nets and ball allocation remain
unchanged. Each resistor connects its original FPGA net to a distinct `_MEM`
net at the PSRAM; connectivity checks verify there is no direct bypass.

The generator, schematic, netlist and PCB are synchronized. `tools/place.py`
places the resistor bank at U1's right-hand escape edge instead of beside
the memory chips. Exact positions still require escape routing. 33 ohms is
a bring-up value; FPGA-end damping does not establish source termination
for PSRAM-driven reads or guarantee 100 MHz timing. The tuning and placement
requirements are in [ref/psram.md](ref/psram.md).

## 32. FIXED — +12V_EXT lacked local output capacitance

Added **C232, 10uF 25V**, 0805 X5R, Samsung CL21A106KAYNNNE / C15850,
from U25 OUT (+12V_EXT) to GND, before the selectors and branch PTCs.
The generator now explicitly rates capacitors on +12V_EXT at 25V.
Existing designators and connections are preserved. C232 belongs to U25's
placement group and must sit close to its OUT pin and ground return.

At the existing approximately 20ms output ramp, the nominal added charging
current is about 6mA; extension capacitance remains additional. The capacitor
provides local output charge storage, not a substitute for extension-side
decoupling. The selected part's voltage and package are confirmed by
[LCSC C15850](https://www.lcsc.com/product-detail/C15850.html).

## 33. FIXED — no supervisor/user indicators and unused core power-good

U17 P0/P1/P2 now sink three green LEDs (D9/D10/D11), labeled CTRL HB,
USER 1 and USER 2, with individual 1k resistors R128–R130 from +3V3.
They default off, need no extra supervisor GPIOs, and use the same qualified
LED as DONE. P3 now reads CORE_1V0_GOOD with its existing 100k pull-up.
P7 retains shared SFP power control; P4–P6 remain unused.

The [firmware contract](ref/status-leds.md) requires a shadow output byte,
P3–P6 always written high, and masked updates so heartbeat/user LEDs cannot
change SFP power or drive PG low. PG polling and LED control share the SFP
upstream bus, so a stuck bus also stops heartbeat updates. This implements
the hardware; supervisor firmware and physical placement/routing remain.

# Part III — independent schematic and city audit, 2026-10-29

## Audit conclusion and scope

**The architecture and much of the voltage-domain planning are sound, but
the schematic needs corrections before detailed placement is frozen.** The
most consequential findings are the FPGA's indefinite partial-power state,
USB backfeed through Q2, missing USB termination, an unsafe PD startup
default, inadequate local buck input bypass, and PSRAM power-up pin states.
Passing ERC has not established correct bring-up.

This review covers the current seven-sheet KiCad design, `tools/design.py`,
ball allocation, actual PCB island membership, `ref/city/plan.yaml`, the city
preview, and the floorplan/routing rules. Baseline: commit `82cb093` plus the
working tree at review time. Earlier EasyEDA exports are historical. The
older statements marked FIXED above are not evidence that the current
design still satisfies the associated requirement; some reference numbers
have since been reused.

This is a review of the schematic and placement intent. Unrouted connections,
staging outside the outline, and the absence of final copper are expected
at this stage. They are not counted as design defects. No parts, nets,
placement, routing, or generator behavior were changed for this audit.

**Priorities:** P1 = correct before committing the prototype PCB; P2 = resolve
the design choice or qualification before placement/routing is frozen;
P3 = resolve during the normal footprint/fabrication review. A qualification
gap means the decision is unproven, not that failure has been demonstrated.

| Independently reproduced check | Result |
|---|---|
| Schematic export versus stored netlist | Matches |
| Declarative design pin nets versus actual PCB pads | 0 mismatches across 499 parts |
| XDC and gate top versus allocation generator | Matches |
| ERC | 0 errors; the 2 documented temperature-diode label warnings |
| PCB schematic parity | 0 differences |
| Copper / assembly | 8 copper layers, all components on front; 0 tracks, 0 vias |
| Footprint staging | 66 origins inside the board, 433 outside |
| DRC | 4 hole-clearance errors, 296 warnings, 499 unconnected items |
| Mechanical lattice checker | Fails; not propagated into `GATE PASS` |

The last two rows need interpretation; see items 47 and 49. Machine-readable
snapshot evidence is in
[audit-2026-10-29.json](archive/history/board-review/audit-2026-10-29.json).

## 34. P1 — always-on FPGA VCCO with switchable VCCAUX violates the recovery case

**Evidence:** `tools/gen_sch.py` connects bank 0 and banks 14/35, plus the
unbonded-bank supply balls, directly to always-on `+3V3`. `U14` supplies
`+1V8_IO`, then FB1 supplies VCCAUX/VCCADC as `+1V8`. U14 depends on `+5V`
and `EN_1V8`; both can remain off while a blank RP2350 flash sits in the ROM
USB loader. The same condition occurs during controller reset or a policy
that powers down the FPGA while retaining the supervisor.

AMD distinguishes its recommended supply order from a reliability limit:
with 3.3 V VCCO, VCCO minus VCCAUX must not exceed 2.625 V beyond the
per-cycle time allowance. DS181 Table 7 specifies 500 ms at the stated
100 °C condition. Here the difference is about 3.27 V for an unbounded
time. Holding PROGRAM_B low does not change the supply voltages.
[AMD DS181, Power-On/Off Power Supply Sequencing and Table 7](https://docs.amd.com/v/u/en-US/ds181_Artix_7_Data_Sheet).

**Required change:** separate the supervisor's always-on domain from the
FPGA supply policy, or provide an autonomous AUX/VCCO relationship that
satisfies this bound. Prove it during ROM recovery, reset, faults and
power-down, including discharge of the large capacitor banks. Firmware
alone cannot fix the blank-flash case. Also check powered peripheral signals
against any FPGA bank that the revised scheme leaves unpowered.

## 35. P1 — Q2 bypasses USB reverse blocking and current protection

**Evidence:** Q2 source/pin 2 is VBUS; drain/pin 3 is `+5V`. Its intrinsic
diode conducts from `+5V` toward VBUS. With J50 powering U11 and the USB
source absent or falling, USB VBUS can therefore be energized even with
Q2 commanded off. When Q2 is on, its channel conducts both ways. D3/D4 and
U26 do not interrupt this separate path.

This follows from the actual net connections and the MOSFET internal
schematic; it is not a firmware hypothesis.
[Diodes DMG2305UX, internal schematic and ratings](https://www.diodes.com/datasheet/download/DMG2305UX.pdf).

The forward bypass also feeds the `+5V` loads without U26's current limit
or specified output slew. C183 slows the gate; it does not establish a
bounded load-current ramp. A firmware mistake or reset during a PD voltage
transition can still pass 9 V into 5.5 V-rated consumers.

**Required change:** give the bypass reverse blocking and a defined current/
inrush limit, with a hardware voltage-valid interlock if it must be safe
independently of firmware. Back-to-back FETs or a suitable power-path device
are candidate implementations, not an audited replacement circuit. Verify
USB alone, J50 alone, both sources, either source being removed, and 5-to-9 V
transitions. This reopens the system-level protection claims in items 10/24.

## 36. P1 — RP2350 USB D+ and D− lack their required 27 ohm resistors

**Evidence:** J1, D6 and U7 pins 66/67 share `USB_DM` and `USB_DP` directly.
Neither path contains a series resistor. The 33 ohm supervisor-to-FPGA
resistors serve unrelated nets.

Raspberry Pi requires 27 ohm USB series termination close to the MCU.
Add both resistors to the U7 island, with separate connector-side net names.
Keep D6 at J1 and route the pair through the protection point without stubs.
[Hardware design with RP2350, section 5.1](https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf).

This is a schematic correction even though the USB cable carries only
full-speed data. USB enumeration and ROM recovery are not established until
this is corrected and tested.

## 37. P1 — CH224K has no independent safe voltage default

**Evidence:** U18 CFG1/2/3 go directly to RP2350 GPIO27/28/29. There is no
external configuration resistor on CFG1. The board relies on firmware to
forbid requests above 9 V, but U18 starts from VBUS before that firmware.

WCH explicitly warns that MCU startup/default pin states can select 20 V,
and specifies a configuration resistor when the downstream system cannot
tolerate that. A 6.8 kohm CFG1-to-ground setting selects 9 V in resistor
configuration. The exact interaction with subsequent GPIO drive must be
checked before adopting that implementation.
[WCH CH224 datasheet, section 5.2, manufacturer-authored mirror](https://uelectronics.com/wp-content/uploads/2025/04/ch224k-Datasheet.pdf).

**Consequence:** U26's approximately 10 V OVLO disconnects the supervisor
path at a high request, potentially removing the controller that would
correct it. D7 is a 13 V-standoff TVS, not a continuous 20 V regulator.
RP2350 internal pulls are not an independently powered startup strap.
This is a missing guarantee; an actual 20 V startup was not measured.

**Required change:** establish a safe hardware default valid before MCU
power-up and through ROM recovery/reset. Verify cold attach on a PD source
offering 20 V, then every permitted voltage transition. Retain the 9 V
firmware ceiling after adding the hardware default.

## 38. P1 — several buck islands lack local input energy storage

| Converter | What its island currently contains at VIN | Conclusion |
|---|---|---|
| U11 AP63300, VSYS to 5 V | No VIN-to-GND capacitor | C185/C186 belong to U26, C192 to U12; none travels with U11 |
| U12 AP63300, VSYS to 3.3 V | C192, 10 uF | Correct ownership; verify effective capacitance at 21 V |
| U13 / U14 / U16 TLV62569 | C200 / C203 / C206, each 100 nF | Small HF bypass only; no local multi-uF input reservoir |
| U15 SY8047 | C207, 22 uF, plus SVIN RC filter | Correct reference topology; retain the tight power loop |

TI's TLV62569 example uses 4.7 uF at VIN. Its layout guidance requires a
short input-capacitor loop. The AP63300 guidance likewise places input
capacitors directly across VIN/GND. A common upstream capacitor is not
proof of an adequate local switching-current loop.
[TI TLV62569, sections 8.2.2.5 and 10](https://www.ti.com/lit/ds/symlink/tlv62569.pdf),
[Diodes AP63300, PCB Layout](https://www.diodes.com/datasheet/download/AP63300_AP63301.pdf).

**Required change:** assign or add a properly rated local input capacitor
to U11; add the reference-sized local input capacitors to U13/U14/U16 and
their island profiles. Select against DC bias and ripple current. Place
these before the inductor/output row and close the VIN-cap-GND loop locally.
The regulator street can remain; its shared supply does not replace these
capacitors.

## 39. P1 — PSRAM startup pin states conflict with PUDC_B low

**Evidence:** all four PSRAMs share U14's `+1V8_IO` with bank 13. Their CE,
clock and data pins have series resistors but no external state-setting
resistors. PUDC_B is strapped low, enabling FPGA configuration pull-ups.

AP Memory requires, from the start of the supply ramp through 150 us after
stable VDD: CE high tracking VDD within 200 mV, clock low, and all four
data pins low. Initialization then requires the reset command sequence.
FPGA pull-ups on clock/data give the opposite idle state; before FPGA
initialization their availability is also not established.
[APS6404L-SQN rev 4.0, section 8](ref/datasheets/aps6404l-sqn.pdf).

**Required change:** define hardware pin states that satisfy the entire
power-up interval, including FPGA-unconfigured operation. Candidate pulls
must overcome the worst configuration pull-up and meet the PSRAM thresholds
without excessive operating load. An alternative supply/isolation scheme
must provide the same guarantee. Put these parts at the PSRAM-side nodes,
then explicitly implement 150 us wait, reset-enable/reset, and reset recovery
in the memory controller. A reset command after boot is not evidence that
the earlier electrical requirement was met.

## 40. P2 — total regulator output capacitance has not been qualified

Summing actual direct rail-to-ground capacitor values, rather than only the
two capacitors inside each regulator box, gives:

| Rail | Nominal direct capacitance | Additional state-dependent load |
|---|---:|---|
| U13 `+2V5` | 103.38 uF | J19/J20 bank capacitors and enabled connector branches |
| U14 `+1V8_IO` | 112.98 uF | 63.55 uF behind FB1, plus selected banks/branches |
| U16 `+1V2_MGT` | 49.90 uF | No connector export |
| U15 `+1V0` | 506.90 uF | MGT filter capacitance behind L9 |
| U12 `+3V3` | 221.16 uF | Selected VCCIO banks, switched branches, inserted cards/modules |

These are BOM-value sums, not measured effective capacitances. The bead and
inductor loads are frequency-dependent, not simply parallel capacitors.
The selectable banks add 44 uF each before the branch loads are enabled.

TLV62569 Table 4 validates particular LC combinations up to 2 x 22 uF for
these voltages; it asks for other combinations to be checked individually.
Matching the local two-cap example therefore does not qualify U13/U14's
assembled load. Do not remove FPGA decoupling just to make this table fit.
[TI TLV62569, sections 8.2.2.3–5](https://www.ti.com/lit/ds/symlink/tlv62569.pdf).

U15's recovered Silergy datasheet confirms the pin map, 0.6 V feedback,
22 uF PVIN bypass, 1 uF SVIN bypass and programmed soft-start topology.
It does not demonstrate stability with this board's approximately 507 uF
direct output network.
[Silergy SY8047 rev 0.9, manufacturer-authored mirror](https://atta.szlcsc.com/upload/public/pdf/source/20220517/73BFF7B078F09CB6F3A268820B2D4DA9.pdf).

**Required resolution:** qualify startup, loop stability and load release
with effective capacitance/ESR bounds and every jumper/load state; use vendor
support, simulation and representative load-step measurements as appropriate.
Revisit compensation or regulator selection if necessary. Oscillation has
not been established by this audit.

## 41. P2 — the 1.8 V extension setting has no load-switch input margin

U23/U24 take their VIN from selectable VCCIO_1/VCCIO_2. The 1.8 V setting is
nominally 1.8024 V, while TPS22950C specifies VIN >= 1.8 V. Even a 1% low
rail is below that bound, before divider tolerance, ripple and copper loss.
[TI TPS22950x, Recommended Operating Conditions](https://www.ti.com/lit/ds/symlink/tps22950.pdf).

This does not invalidate the FPGA/PSRAM 1.8 V domain, whose operating window
is wider. It invalidates a guaranteed protected extension supply across that
domain's tolerance. Select a switch qualified below the minimum rail, or
choose a rail target/tolerance that simultaneously meets every consumer's
limits. Bench success at room-temperature nominal voltage is insufficient.

The switch choices otherwise make sense: reverse blocking, externally held
OFF enables, fault reporting, local input bypass and the documented
current-limit settings are useful protections.

## 42. P2 — RP2350 pin allocation requires avoidable custom peripheral handling

| Board function | Assigned GPIO | Native peripheral function |
|---|---:|---|
| SUP_SCL | 14 | I2C1 SDA |
| SUP_SDA | 31 | I2C1 SCL |
| SUP_UART_TX | 19 | UART0 RTS, or auxiliary UART0 RX |
| SUP_UART_RX | 20 | UART1 TX, or auxiliary UART0 TX |

The I2C roles are reversed. The UART assignments do not form a native
transmit/receive pair for one UART. Swapping just the UART signal names
does not automatically make a valid pair.
[RP2350 datasheet, GPIO functions](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf).

**Recommendation:** swap the I2C assignments and allocate a legal UART pair
while spare GPIOs remain. Otherwise explicitly budget PIO/software drivers
and test recovery when the expander bus stalls. The shared FPGA-flash SPI
pins also do not form a native SPI peripheral pinout; that interface needs
an intentional PIO/software implementation. These are functional planning
issues, not electrically crossed I2C wires: software can implement the
present mapping, at additional complexity.

## 43. P2 — hard-strapped master SPI cannot also provide slave-serial loading

M[2:0] are hard-strapped to 001. The RP2350 cannot change M1/M2. AMD assigns
001 to master SPI and 111 to slave serial; PROGRAM_B resets configuration
but does not override mode straps. After release the FPGA drives CCLK in
master mode, so the supervisor must not also drive it as a slave-serial
source.
[AMD UG470, Configuration Modes and Serial Configuration](https://docs.amd.com/v/u/en-US/ug470_7Series_Config).

The direct flash-writing plan remains plausible while PROGRAM_B holds the
FPGA reset, with correct bus ownership. For volatile FPGA loading, either
use the already-wired JTAG path and correct the slave-serial promise, or add
a deliberate mode-selection circuit. Firmware must also restore the flash's
boot-compatible address/protocol state before releasing PROGRAM_B. Verify
golden/fallback addressing with the actual 256 Mbit flash rather than
assuming every MultiBoot address is interchangeable.

## 44. P2 — several island memberships do not preserve the intended electrical location

The actual PCB groups, not the older placement prose, contain:

| Parts | Current group | Required placement decision |
|---|---|---|
| R104–R109, R110–R115, R116–R121, R122–R127 | U2, U3, U4, U5 respectively | FPGA-driven clock/CE source damping belongs at the FPGA escape, not locked to the memory island |
| R151, 22 ohm SDRAM clock | U32 | Source is U1; move its ownership/location to the FPGA clock escape |
| Q2 | J1 | Keep with the reviewed power path |
| Q2 gate parts R46/C183 | U26 | They serve Q2, not U26; prevent their separation when moving blocks |
| X4, R147, C246 | Ungrouped | Keep the oscillator, source resistor and bypass as one clock island attached to U1 |

A membership error is significant now because a rigid group move preserves
the error. `place.py` can place PSRAM resistors at the FPGA, but that is not
where their current city groups keep them. Split source parts from memory
load parts deliberately, or add an explicit source-location constraint.
R147 should remain at X4, which is the source of SYS_CLK.

Bidirectional PSRAM data needs separate consideration: an FPGA-end resistor
does not source-terminate memory-driven reads. Retain tuning footprints and
verify both directions; do not add a second 33 ohm automatically. The
existing warning in `ref/psram.md` is correct.

## 45. P2 — the inboard microSD socket needs an access contract

The city script deliberately gives J74 no edge reservation. Its opening
faces toward the bottom, broadly behind J72's edge position. A push-push
socket needs space for the card's travel and a finger/tool to latch and
eject it; a no-overlap rectangle around the socket body does not supply that.

**Resolution:** choose explicit access from above with a keep-out through
any shield/enclosure, or reserve a board-edge opening and move other blocks.
Check insertion and ejection with adjacent jacks populated and a shield
installed. Inboard placement can be acceptable; the current plan does not
yet establish usable access. Do not treat J74 as an ordinary wired IC.

## 46. P2 — power checks do not establish the aggregate input-source envelope

`budget.py` currently checks board-only rail load against regulator ratings
and the VSYS input window. It does not enforce source-profile power,
simultaneous exported loads, thermal limits, or the inductor checks claimed
in some documentation.

The current planning model consumes approximately 0.721 A from 5 V and
0.919 A from 3.3 V: about **6.64 W** before upstream losses and extensions.
Its default-USB profile supplies only 4.75 V x 0.9 A = 4.28 W. That profile
can support a restricted mode, not the modeled full board. Moreover, 900 mA
is not a universal USB default; ordinary USB 2.0 configured bus power is
500 mA, and higher Type-C current requires the corresponding advertisement
or contract.
[USB-IF power compliance policy](https://compliance.usb.org/index.asp?Format=Standard&UpdateFile=Policies).

For both VCCIO domains selected to 3.3 V, nominal low-voltage switch limits
allow another 1 A x 5 V + 3 x 0.5 A x 3.3 V = 9.95 W. Together this is
16.59 W. Assuming 90% upstream efficiency and roughly 8.5 V after the USB
path requires about 2.17 A, already above U26's 2.03 A typical limit.
Using the switch upper-limit tolerances raises this to about 2.49 A. These
are planning calculations, not measured efficiencies or available allocations.

**Resolution:** define recovery/light/full-power input modes and a shared
export allowance for each. Include source-current knowledge, U26 minimum
limit, jumper combinations, conversion losses, DC-biased capacitors,
inductor peak current and hot-board thermals in qualification. Existing
warnings that fuse ratings are not additive remain necessary. A 4 A
regulator label also does not prove a 4 A core at temperature; XPE and the
chosen inductor's tolerance/saturation curve remain open work.

## 47. P2 — a green gate currently conceals a failed mechanical check

`tools/gate.py` prints `place.py --check exit 1`, then still prints
`GATE PASS`: that return code never updates `ok`. The present lattice
failure is understandable while connectors and posts are staged or remain
in old hand positions; reporting a complete pass is nevertheless misleading.
Separate electrical-consistency and mechanical gates, or make the final
status depend on every check it claims to enforce.

The existing Vivado gate has a different, deliberate limit:
`gateware/gate/gate.xdc` false-paths all inputs and outputs. Its routed
bitstream is useful evidence for legal balls/I/O primitives and internal
implementation, not for PSRAM, SDRAM, RGMII, HDMI or cable timing. The
existing timing report's success must be interpreted within that scope.
No new Vivado functional timing sign-off was performed in this audit.

Before routing, define real interface budgets: flight time, clock-to-data,
setup/hold, skew and allowable via/layer changes. RGMII clock skew must be
provided once; the PHY's enabled delay straps should not be combined with
another automatic MAC-side delay without analysis.

## 48. P2 — contradictory documents can produce an incorrectly wired shield

`ref/user-manual.md` still shows the old signal-row grounds in the last
two columns. The current schematic uses columns 3 and 6 for ground. It also
describes obsolete connector bodies, per-slot selectors and a 14 V input
ceiling. `floorplan.md` retains its old opposite slot sides/top-network
contract above the accepted rotated city. `ref/network.md` still calls the
PHY controls bank 13, although they now correctly use bank 35.

Other stale examples include the old VCCO grouping in `ref/decoupling.md`,
the deleted boost in `ref/supervisor-flash.md`, and SFP-related details in
older findings. These are not just prose discrepancies when a user builds
a mating PCB from the wrong pin table.

**Resolution:** establish one current connector/power/floorplan contract,
mark earlier revisions as historical, and regenerate all dependent tables.
Keep item 14's shield mating, key projection and height qualification open.
The circuit-to-PCB net map is consistent; the human-facing contract is not.

## 49. P3 — USB-C footprint holes violate the current drill-clearance rule

All four actual DRC errors are J1: ground pads A1/A12/B1/B12 versus its
NPTH locating holes. Actual hole clearance is 0.1847 mm; the board rule is
0.2500 mm. This is a footprint/fabrication issue independent of unfinished
routing. Check the connector drawing and the chosen fabricator's hole-to-
copper capability; correct the footprint or justify a local rule. Do not
silently lower the global hole clearance.

## 50. P2 — telemetry does not cover every rail the supervisor claims to verify

The six ADC connections measure VSYS, 5 V, 3.3 V, 2.5 V, `+1V8_IO` and
1.0 V. There is no measurement of `+1V2_MGT`, either selected VCCIO domain,
or actual `+1V8` **after FB1**. Core PG is additionally read through U17.
Consequently, an open/missing FB1 can leave VCCAUX absent while MON_1V8
reports a healthy regulator output. The jumpers are not automatically sensed.

**Resolution:** measure the rails needed for the intended sequencing/fault
policy, especially actual VCCAUX, or narrow the claimed observability and
document the checks firmware cannot make. Spare ADC-capable GPIO46 is
available, but all desired measurements may need further pin allocation or
a multiplexer. Keep monitor bypass capacitors at the ADC inputs and evaluate
fault voltages as well as nominal divider ratios. This is separate from
item 34: observing a supply cannot enforce its required startup relationship.

## 51. P2 — city planning assigns the wrong key posts to the 5 V buses

Both city variants associate MK71 with J7 and MK72 with J8. In the current
design, `MK{ord(slot)}` makes MK71/MK72 the **G/H** keys; L/M require
**MK76/MK77**. The latter remain in the board's fixed-ghost set instead of
traveling with the proposed top bus neighborhoods. All these posts are GND,
so electrical parity cannot detect the semantic mistake.

Correct the city anchor references and group each post with the power row
it actually keys. Keep G/H keys with their side-edge sections. This is a
specific planning error beyond the expected unfinished placement, and one
reason the mating lattice must be verified from real pad coordinates.

## City planning verdict

**A regulator street is acceptable.** Regulator proximity should minimize
the high-current output path and input switching loop, while quiet feedback
and clocks remain protected. Putting all regulator bodies in a neat row is
not itself an electrical requirement. The accepted U1 rotation and opposite
slot sides are a reasonable starting point; the score is a wiring heuristic,
not a routing or power-integrity proof.

| Neighborhood | Assessment and placement instruction |
|---|---|
| U15 core supply above U1 | Keep its priority and a wide output corridor into the core balls. Align the **inductor output/output capacitor copper**, not merely the IC centre. Keep FB sensing away from SW and take the sense point from the intended regulated output. |
| U14 1.8 V / U16 MGT in the same row | The row is reasonable. With the actual 90-degree U1 rotation, bank 13's PSRAM/buffer balls are toward the upper-left. Consider U14 on that side before spending the left corridor on the unused-MGT regulator. VCCAUX still needs its filtered, quiet distribution. |
| U13 2.5 V below U1 beside U30 | Good relative location for bank 16 and the PHY's 2.5 V pads. Keep its switching loop clear of the PHY crystal and pair escape. Resolve its capacitor qualification first. |
| U11 feeding the low-voltage regulators | Good upstream relationship to the row. Add its own input bypass and local bypass at every downstream converter; keep the wide 5 V distribution out of sensitive clock corridors. |
| U12 3.3 V on the left | Acceptable for a distributed rail with broad plane copper; it need not sit beside the RP2350. Keep VSYS input routing and local CIN controlled, and check worst-case drop to the distant supervisor/SDRAM. |
| U2–U5 PSRAM | Give all four short escapes toward their bank-13 balls before legalizing slow support circuitry. U2 is currently to the right while the others are left; this is an avoidable detour candidate, not proof of an unroutable board. Group by timing-critical nets, and split the source resistors as in item 44. |
| U7 supervisor with U8/Y1 | Correct neighborhood and useful satellites. Keep the regulator loop as a protected sub-island, USB resistors at U7, crystal loop quiet, and QSPI short. Avoid putting U14/U15 switch-node fields across Y1 or VREG_AVDD. |
| U30 / X3 / J70 | Keeping the PHY between bank 16 and its jack is sound. Its present lateral offset from J70 still needs a clear four-pair MDI corridor; prefer moving slow/status blocks over bending those pairs through power circuitry. |
| J71/J72 and ESD arrays | Correct ownership of connector-side ESD; use flow-through paths and very short ground returns. Their bottom-left position agrees with the network-facing bank. |
| J73 with U31 | Correct satellite choice and edge location for bank 35. Preserve the direct connector-to-protection paths and differential pair corridors. |
| U32 SDRAM | The lower corner between bank 35 data/control and bank 14 address is a reasonable compromise. Orient its data and address pin rows toward their actual escapes and prioritize the forwarded clock; move R151 to its source. |
| U33 MRAM | Correct low-speed bank-14 neighborhood; lower placement priority than PSRAM/SDRAM/clock escapes. |
| J74 microSD | Connectivity attracts it to the right functional neighborhood, but access must override the wire-count solution. See item 45. |
| Slots, power rows, keys | The intended parallel lattice is appropriate for bridging shields. Correct the MK71/MK72 versus MK76/MK77 planning error in item 51, then reconcile old positions and run the real pad-coordinate check. |
| J1/U26/Q2 and J50/D4/D8 | Correct to treat these as source-entry neighborhoods. Rework the electrical path first, put TVS return loops at the entry, and keep Q2's gate network with Q2. |
| J68 AUX | Keep an edge position with wire bend/screwdriver clearance and an independent wide path to the branch fuses. Its raw, unswitched behavior is a deliberate product constraint. |

### Power plane and routing implications

The eight-layer S/GND/S/PWR/GND/S/GND/S concept is sensible: signal escape
layers have nearby ground references, and the power/ground pair is tight.
Keep these ground planes continuous; the small RP2350 LX clearance called
for by its reference layout is a local exception, not permission to split
signal return planes. Outer-layer differential geometry must not be reused
on an inner layer without recalculation. USB also needs a defined 90 ohm
pair geometry; it currently has no dedicated net class. The 0.125 mm RGMII/
SDRAM width is an outer-layer estimate, not a universal 50 ohm rule for
In2/In5.

The power doors are a useful way to reserve corridors. They do not prove
that In3 has room for every split rail or that narrow In5 power traces can
replace plane areas without cost. Draw those polygons and trial-escape a
representative set of core supply vias and deep signal balls before fixing
every neighborhood. The depth report contains 80 assigned signal balls at
depth >=7, of which 63 are classified as allocation choices; this is a
reason to trial-route the escapes, not proof that 63 can all be eliminated.

As an illustrative copper calculation, a 15 mm x 5 mm corridor of 15.2 um
copper is about 3.4 milliohms at room temperature, or 14 mV drop at 4 A,
before vias and necks. The 1 V rail has little voltage margin after regulator
and resistor tolerances. Check the complete supply/return path, hot copper,
and output-capacitor/load locations; a favourable centroid score cannot
establish this. The 4 A figure here is a sizing example, not a measured load.

### Island rules to preserve during compaction

1. Reserve connector mating/card/cable/tool space before packing circuitry.
2. Place local switching loops and the RP2350 reference regulator first;
   keep feedback/analogue nodes away from SW/LX and inductor fields.
3. Place FPGA/source clock resistors at their actual drivers, then memory
   loads and timing-critical escapes. Keep ESD at the external entry.
4. Preserve each bank's capacitor ownership while changing U1 orientation.
   The top-side-only decoupling ring is not inherently wrong: UG483 permits
   these mid-frequency capacitors within two electrical inches, with low-
   inductance mounting. Vias and plane continuity decide whether this ring
   actually works.
   [AMD UG483, PCB Capacitor Placement](https://docs.amd.com/v/u/en-US/ug483_7Series_PCB).
5. Pack slow expanders, LEDs and service details into the remaining space.
   A rigid island is a convenience, not a reason to retain an electrically
   wrong orientation or separated input capacitor.

## Electrical decisions supported by this audit

| Decision | Conclusion and evidence boundary |
|---|---|
| FPGA bank voltages | Coherent: bank 13 at 1.8 V for PSRAM/translators; bank 14 at 3.3 V for configuration; bank 16 at 2.5 V for RGMII/LVDS; bank 35 at 3.3 V for HDMI/SDRAM; selectable banks 15/34. This does not resolve item 34's sequencing defect. |
| Configuration straps | CFGBVS high agrees with 3.3 V configuration; 001 straps agree with master SPI; PROGRAM_B/INIT_B pull-ups, low PUDC_B strap and buffered DONE LED have sensible topology. Slave serial and startup defaults are separate findings. |
| Hardware JTAG ownership | U20 plus J52 gives a useful independent isolation path for external recovery. Verify the header's chosen cable pinout; it is not a standard AMD 14-pin header. |
| FPGA decoupling values | The VCCINT/VCCBRAM/VCCAUX and per-bank networks match the cited UG483 device/package prescription. Keep local bank placement and via inductance under review; capacitance quantity does not qualify the regulators' control loops. |
| PSRAM part/voltage | APS6404L-SQN-SN is the 1.8 V, 64 Mbit SOP-8 part, giving 8 MB per chip and 32 MB total. Bank 13 now matches it. Four independent buses are correctly connected; initialization and SI remain open. |
| SDRAM / MRAM / SD | The present pin maps and 3.3 V supply domains are coherent. SDRAM has seven supply bypasses and CS/CKE bias parts; MRAM has CS/WP/HOLD pull-ups; SD SPI contacts and five pulls are present. This is topology evidence, not 166 MHz SDRAM qualification or a guarantee for every SD card's peak current. |
| 5 V translators | SN74LXC8T245 supports the 1.8 V A side; DIR/OE reference that side, with OE held disabled externally. The B side is 5 V. A-H remain direct FPGA pins; the existence of translators on L/M does not protect A-H. |
| Extension power | Bank voltage and selected PIN V have the same upstream source; separate protected low-voltage exports preserve the base-board domains during a branch fault. The 1.8 V switch margin, aggregate budget and mechanical pin map still need resolution. |
| PHY digital interface | Realtek rev 1.7 supports external 2.5 V RGMII with CFG_EXT=1/CFG_LDO=01. Reset held low permits its delayed I/O supply; 10 ms reset and at least 72 ms settling remain gateware obligations. The 3.3 V reset/interrupt controls correctly moved to bank 35. |
| Ethernet jack wiring | HanRun's current rev B drawing confirms P1 as common chip-side centre taps, P10 as the internal 75 ohm/capacitor network return, MDI polarities, and LED 11/12 and 14/13 polarity. The current schematic agrees. |
| PHY analogue passives | A published FriendlyELEC RTL8211F design supports the 2.49 kohm RSET and capacitively grounded centre-tap approach. That board uses the switching-core variant: it does **not** independently prove the exact FD internal-LDO output capacitor requirement. Keep that distinction and verify FD loop/rail behavior. |
| Raw LVDS links | Real pair positions and clock-capable receive pins are allocated; bank voltage and internal DIFF_TERM intent agree. Existing STP-only, common-ground, both-boards-powered restrictions are substantive electrical constraints. They do not establish arbitrary cable length, hot-plug or unpowered-peer tolerance. |
| HDMI | TMDS_33 in a 3.3 V bank with receiver termination and the TPD12S016 companion is coherent. VCCA/VCC5V/5V_OUT bypass, enables, DDC/HPD/CEC paths and utility-pin resistor are present. Keep U31 at the jack; 720p operation still needs actual serializer/timing and SI validation. |
| Supervisor regulator/crystal | The selected inductor, AVDD RC filter, crystal load and damping topology are reasonable. Preserve winding orientation and the reference local copper arrangement; consider the recommended extra remote DVDD bulk capacitor. A generic ring profile alone does not prove regulator layout equivalence. |
| Input ratings | The stated 21 V J50 operating range is consistent with the wide-input bucks and explicit VSYS capacitor ratings. TVS clamps are pulse limits, not continuous overvoltage regulation; bench/surge testing must use a defined source impedance and waveform. |
| AUX pass-through | A separate raw input with 33 V branch PTCs is coherent for the stated 9–28 V use. It is unregulated and unswitched; EXT_EN does not isolate it. Preserve the explicit no-backfeed and shared-capacity contract. |

Sources for the cross-checks above:
[AMD UG470](https://docs.amd.com/v/u/en-US/ug470_7Series_Config),
[AMD UG483](https://docs.amd.com/v/u/en-US/ug483_7Series_PCB),
[AP Memory datasheet](ref/datasheets/aps6404l-sqn.pdf),
[Winbond SDRAM datasheet](ref/datasheets/w9825g6kh.pdf),
[Everspin MRAM datasheet](ref/datasheets/mr25h10cdf.pdf),
[TI SN74LXC8T245](https://www.ti.com/lit/ds/symlink/sn74lxc8t245.pdf),
[Realtek rev 1.7, manufacturer-authored mirror](https://static.chipdip.ru/lib/595/DOC042595102.pdf),
[HanRun rev B drawing](https://hrdzcn.oss-cn-beijing.aliyuncs.com/202601/ab534667d942f65.pdf),
[FriendlyELEC NanoPi R2S Plus schematic, sheet 11](https://wiki.friendlyelec.com/wiki/images/d/da/NanoPi_R2S_Plus_2309_SCH.PDF),
[TI TPD12S016](https://www.ti.com/lit/ds/symlink/tpd12s016.pdf),
[Raspberry Pi hardware guide](https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf).

### Optional simplification, not a defect

The unused GTPs do not have to consume a powered regulator neighborhood.
UG482 Table 5-4 permits grounding MGTAVCC/MGTAVTT/MGTRREF when the entire
power-supply group is unused, with the specified RX/TX/reference-clock
connections. The current powered treatment is also a valid design choice
if its supply requirements are met. If rev A will truly never use GTP,
evaluate removing U16 and the associated filtering/decoupling; do not ground
only one of the supplies or mix the two prescribed schemes.
[AMD UG482, Unused GTP Quad Power Supply Group](https://docs.amd.com/v/u/en-US/ug482_7Series_GTP_Transceivers).

## Recommended order of resolution

Correct items 34–39 first, because they can change the power tree, nets and
island contents. Resolve regulator/load-switch qualification and source
budgets next. Then settle native peripheral use and the FPGA-loading modes,
repair island ownership, and reconcile the mechanical/access contract.
Only then compact the city, trial-route critical escapes and freeze the
plane corridors. Final routing/SI, prototype measurements and fabrication
checks remain later milestones; the absence of those results at this stage
is expected.

## Status of items 34–51 after the corrections of 2026-10-29

Commits a557379, 49ebd65, b9d464b, cd02e23 and the documents commit that
follows. Every step ends with the electrical gate passing (ERC 0 errors,
DRC 0 errors, parity 0) and nothing inside the board outline moved; the new
parts (53 footprints) are staged in the import band for the owner to island.
The entries in `archive/history/rev-a-report.md` carry the numbers.

| Item | Status | What changed |
|---|---|---|
| 34 VCCO/VCCAUX | **FIXED** | U11 (EN floating, DS42002 automatic start) and U14 (EN tied to +5V, SLVSDG1C EN ≤ 6 V) run whenever +3V3 does, so VCCAUX is up within the regulators' own start-up of the 3.3 V banks and never depends on firmware or a blank flash. Power-down: both banks discharge through their loads within tens of ms (221 µF on +3V3 into ≥ 100 mA; 176 µF on 1.8 V); **[verify]** the DS181 Table 7 500 ms bound on the prototype with a scope. GPIO23/26 freed. |
| 35 Q2 backfeed | **FIXED** | Q2/Q3 gate network removed. U34 TPS2121 power mux: IN1 VBUS, IN2 U11 (+5V_BUCK), OUT +5V; reverse blocking both inputs, 2.5 A limit, 100 nF soft start, 5 µs switchover; dividers select VBUS only between 4.44 V (PR1 > CP2) and 5.63 V (OV1), so a 9 V contract hands the rail to U11 without firmware. ST on GPIO21. Items 10/21/24 are superseded by this path. **[verify]** the five source cases on the bench. |
| 36 USB 27 Ω | **FIXED** | R162/R163, 27 Ω 0402 at U7 (USB_DP_MCU/USB_DM_MCU); J1 and D6 stay on USB_DP/USB_DM. |
| 37 PD default | **FIXED** | CFG1 10k pull-up to the CH224K's own 3.3 V (5 V request before any controller, WCH Table 5-2); Q3 pulls it low for 9 V (PD_REQ_9V, GPIO27, gate pull-down); CFG2/CFG3 grounded, so 9 V is the highest code the pins can form. Firmware ceiling in item 19 is now also copper. |
| 38 input caps | **FIXED** | 10 µF 50 V 1210 across U11's VIN; 4.7 µF 0603 at each TLV62569 VIN (U13/U14/U16). Island profiles place them on the VIN flank. |
| 39 PSRAM power-up | **FIXED** | PUDC_B strapped high (no configuration pull-ups; every line that needs a level already had its resistor). Per PSRAM: CE#_MEM 10k up to +1V8_IO, SCK/IO0-3_MEM 10k down. Gateware obligation: 150 µs wait and the 66h/99h reset pair (ref/psram.md). |
| 40 COUT qualification | **open, now tracked** | `budget.py` sums the direct output capacitance per regulator against each datasheet's validated figure: U12 221 µF, U13 103 µF, U14 113 µF, U15 507 µF, U16 50 µF are beyond it. Bench qualification (start-up, load step per jumper position) before fabrication sign-off; table in ref/power-budget.md. |
| 41 1.8 V switch | **FIXED** | U23/U24 are TPS22953DSQR: BIAS from +3V3, input 0.7 V to VBIAS, reverse blocking while off, CT 1 nF. No programmable current limit; the 500 mA PINV fuses are the overload protection. |
| 42 controller pins | **FIXED** | SPI1 for the flash bus (SCK 10, TX 11, RX 12, CSn 9; FD2 13, FD3 7 by PIO for quad), I2C1 SDA 14 / SCL 31, UART0 TX 32 / RX 33, EXT_FAULT 34. Verified against the RP2350 pin-function table (Zephyr `rpi-pico-pinctrl-common.h`, generated from the datasheet). |
| 43 slave serial | **documented** | No slave-serial path exists or is promised: M[2:0] are 001 in copper; volatile loading is JTAG through U20; MultiBoot addressing and the W25Q256 address mode are called out in ref/supervisor-flash.md. |
| 44 island ownership | **FIXED** | `islands.py`: the anchor a part's design.py group names wins, and a part parked in another island is reclaimed when its group names the run's anchor. Groups renamed `U1 PSRAM{n} series termination`, `U1 SDRAM clock source`, `X4 system clock`. Applied (owner's go-ahead): R104–R127 and R151 are in U1's island at its escape, X4/R147/C246 are one island, Q2's parts are gone. |
| 45 microSD access | **decided** | Access from above: card travel plus 12 mm finger room kept clear of tall parts, shield/enclosure cut-out over it, no edge opening (floorplan.md). Check with J72/J2 populated before freezing. |
| 46 source envelope | **FIXED (tool), contract set** | `budget.py` models recovery / light / full modes per source profile with the U26 and U34 limits: a USB 2.0 port carries recovery only; light fits any Type-C ≥ 1.5 A or PD 9 V; full export fits J50 only (2.05 A against U26's 1.7 A minimum on PD). Inductor peak current is now checked (all pass). Firmware must ration EXT_EN by source. |
| 47 gate | **FIXED** | `gate.py` prints `GATE electrical` and `GATE mechanical` separately; the exit code follows the electrical gate, `--strict` adds the mechanical one. Today: electrical PASS, mechanical FAIL (B3 open). |
| 48 stale documents | **FIXED** | user-manual.md (pin tables, connector bodies, AUX instead of per-slot selectors, 21 V input, slot sides), floorplan.md (current plan header, microSD contract, historical top-edge section), network.md (bank 35), decoupling.md (groups), supervisor-flash.md (start-up order, no slave serial), psram.md, power*.md, extension-ux.md, island-layouts.md, status-leds.md, gameboy-extension.md, jlcpcb-import-checklist.md. |
| 49 J1 holes | **FIXED** | odin copy of the KiCad footprint with A1/A12/B1/B12 shortened to 0.6 × 1.15 mm on the hole side: 0.31 mm hole-to-copper (rule 0.25, JLC NPTH-to-track 0.20). DRC: 0 errors. **[verify]** against the HCTL drawing (LCSC serves it only through a browser). |
| 50 telemetry | **FIXED** | MON_1V8 reads +1V8 (VCCAUX, after FB1); ADC6/ADC7 read VCCIO_1/VCCIO_2 so the jumpers are sensed. +1V2_MGT is the one unmeasured rail (no GTP load in rev A; U16 has no PG). |
| 51 key posts | **FIXED** | city.py maps MK76/MK77 to J7/J8; an off-board post whose row is on the board goes onto the board at position 1 of that row, a post on the board whose row is a planned block joins the block at the same offset. Applied (owner's go-ahead): MK71/MK72 stand one pitch before J56/J65 on the board, MK76/MK77 ride with J57/J58 at the top edge; slots G, H, L and M pass `place.py --check`. Consequence to decide: the zero-gap contract makes the KiCad courtyards of each post and its neighbouring rows overlap by about 0.5 mm (10 DRC courtyard errors; the plastic bodies touch but do not overlap). Either a documented courtyard exception for the posts, or more than 20.32 mm per zone. |

Not changed on purpose: the unused GTP quads stay powered (the audit's
optional simplification), the TPS22950C stays on U21/U22, and the hand
placement inside the outline. Same day, on the owner's go-ahead: every
staged footprint islanded (X4, U34, Q3, U11, U13, U14, U16, U7, U2–U5, U23,
U24, U8, Y1, U1 extended with the source resistors), the city re-planned
and applied, the four key posts placed. Remaining owner work: the post
courtyard decision above, the six hand-placed posts A–F that `place.py`
flags, compaction of the city onto the board, routing, the bench items
(COUT, U34 source cases, power-down timing) and the J1 drawing check (LCSC
refuses non-browser access).

---

# Part IV — independent re-audit after corrections, 2026-10-29

## Re-audit verdict

**Most corrections are present and electrically coherent, but the schematic
still needs three corrections before committing a prototype PCB:** U34's
overvoltage threshold permits the 5 V rail outside its loads' operating
range; connecting J50 does not relieve USB of the 5 V load; and U6's flash
chip select lacks its required pull-up. Four additional P2 findings cover
source-current detection, load-switch support and the applied city plan.

Baseline: `9dd5fa85e318972e9969e3accb2eaf53ae8f3831`, compared with the
previous audit's `82cb093`. This review checked the changed generator,
schematic/netlist, all actual PCB pin nets, island memberships and positions,
the current city preview, and the cited manufacturer requirements. The
correction-status table above was treated as a claim to verify. No circuit,
placement, routing or generator was changed. Unrouted staging remains
appropriate to this phase. P1/P2/P3 retain the definitions in Part III.

Evidence, baseline hashes, relevant pin connections, source-case calculations,
DRC pairs and selected pad coordinates are saved in
[reaudit-2026-10-29.json](archive/history/board-review/reaudit-2026-10-29.json).

| Independently reproduced check | Current result |
|---|---|
| Design model versus PCB pads | 544 parts / 544 footprints; **0 pin-net mismatches** |
| Schematic export versus stored netlist | Matches |
| Allocation versus XDC and gate top | Matches |
| Parts-role coverage | 544/544; 0 problems or gaps |
| ERC / schematic parity | 0 errors, 2 allowlisted temperature-diode warnings / 0 differences |
| Assembly / copper | All footprints front; 8 copper layers; 0 tracks, 0 vias |
| Footprint origins | 66 inside the outline, 478 staged outside |
| DRC | **10 courtyard errors**, 298 warnings, 499 reported unconnected items; no remaining J1 hole-clearance errors |
| Mechanical checker | **Fails with 10 findings**: four lattice/row findings and six A–F key-position findings |
| Gate | Electrical PASS; mechanical FAIL; ordinary exit code 0, as now explicitly documented |
| Deep FPGA signal balls | 80 at depth >=7: 17 inherent, 63 classified as allocation choices |

The electrical gate now reports its scope honestly. Its PASS establishes
consistency and the checks it implements; the analogue issues below remain
outside those checks.

## Verification of the earlier corrections

| Earlier item | Independent disposition |
|---|---|
| 34 VCCO/VCCAUX sequencing | **Original indefinite firmware-dependent state removed.** U11 automatically starts; U14 EN is tied to its input. Keep the DS181 rail-ramp and power-down waveform check open. A load estimate is not a guaranteed discharge path. |
| 35 USB backfeed | **Q2 body-diode defect removed.** U34 is correctly pinned and provides the intended reverse-blocking topology. Its threshold and source-priority implementation need items 52–53. |
| 36 USB termination | **Verified.** The fitted pair is **R170/R171**, 27 ohm, between the connector/ESD nets and U7. The correction table's R162/R163 are actually U34 divider resistors. Final placement must keep the pair at U7. |
| 37 PD default | **Verified topology.** CFG1 is pulled to PD_VDD, Q3 has a gate pull-down, and CFG2/CFG3 are grounded: default 5 V, asserted request 9 V. No higher digital code is available. This proves voltage selection, not available current. |
| 38 Converter input caps | **Schematic and ownership verified.** C267 is 10 uF/50 V at U11; C268–C270 are 4.7 uF at U13/U14/U16, in their respective islands. Preserve short VIN/GND loops during compaction. |
| 39 PSRAM startup | **Original conflict removed.** PUDC_B is high; all four memories have CE pull-ups and five clock/data pull-downs on their memory-side nets. The 150 us wait/reset sequence remains a gateware obligation. The global strap change also exposes item 54. |
| 40 Regulator COUT | **Still open, now tracked.** Direct sums agree with the report. U11 also has **81.7 uF downstream of U34**, in addition to its direct 66 uF; the mux does not establish control-loop isolation. Qualify the complete network, jumper choices, effective capacitance and ESR. Exceeding an example's capacitor range is a qualification gap, not proof of instability. |
| 41 Switch operation at 1.8 V | **Voltage-margin defect removed.** TPS22953 BIAS is +3V3 and the selected rails are within its input range. Support-pin and fault-coverage conditions remain in item 56. |
| 42 Native controller peripherals | **Verified against the RP2350 function table.** SPI1 SCK/TX/RX = GPIO10/11/12, CSn = GPIO9; I2C1 SDA/SCL = GPIO14/31; UART0 TX/RX = GPIO32/33. Quad flash still needs the documented PIO handling. |
| 43 Slave serial | **Closed by scope decision.** Fixed master SPI and volatile JTAG loading are now the contract; no copper change is required for that decision. |
| 44 Island ownership | **Ownership fixed.** R104–R127 and R151 belong to U1; X4/R147/C246 are together and merged into U1; U8/Y1 are back with U7; Q2 is gone. Correct membership does not establish the final source-termination distance or clock-side placement; see item 58. |
| 45 microSD access | **Design choice documented, mechanical proof pending.** Above-board card travel and 12 mm finger space must survive compaction and the populated shield/enclosure arrangement. |
| 46 Source envelope | **Substantially improved, incomplete.** The model now distinguishes modes and hardware limits. It omits the mixed-source case in item 53 and relies on unavailable source information in item 55. Further model limits are listed below. |
| 47 Gate scope | **Verified fixed.** Separate electrical/mechanical verdicts and `--strict` remove the earlier ambiguity. |
| 48 Documentation | **Partly fixed.** Main pin maps are improved. The manual still calls the network edge “top” while the current city puts it below U1, and still offers full export on PD9 despite the budget rejecting it. `floorplan.md` still describes a left-side X4 that is now above U1. |
| 49 J1 clearance | **DRC defect fixed; footprint qualification pending.** The custom pads clear the holes. The shortened land pattern still needs comparison with the HCTL drawing; the public PDF redirects to a JavaScript viewer and direct retrieval was denied in this review. No manufacturer-pattern match is claimed. |
| 50 Telemetry | **Verified.** MON_1V8 senses the post-FB1 VCCAUX rail; ADC6/7 sense both selected VCCIO rails. The explicitly unmeasured, unused-GTP 1.2 V rail remains an accepted limitation. |
| 51 Key posts | **Reference/ownership correction verified; mechanical closure incomplete.** MK76/MK77 follow the 5 V buses, and G/H/L/M pass the individual key-offset test. However, **J7/J57/MK76 still fails the signal-to-power-row lattice check**. This is separate from the six A–F key failures. See the mechanical disposition below. |

The native-peripheral cross-check uses the
[Raspberry Pi RP2350 datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf).
USB and local regulator placement remain governed by the
[Raspberry Pi hardware guide](https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf).

## 52. P1 — U34 hands off above the downstream 5.5 V operating limit

**Entities:** U34 OV1, R164 = 100k, R165 = 23.2k; U13/U14/U16 and the other
5 V consumers. See `tools/design.py`, U34 support network.

The rising trip is `1.06 × (1 + 100/23.2) = 5.629 V`. Using the specified
1.01–1.10 V comparator reference and assuming 1% divider resistors, the static trip
envelope is approximately **5.277–5.937 V**, before leakage and dynamics.
U34 selects the rising VBUS until this trip. At light load its output can
therefore exceed 5.5 V during a normal 5→9 V negotiation. The reverse
transition also needs checking. The TLV62569's operating maximum is 5.5 V;
its 6 V absolute maximum is not an operating allowance.
[TI TPS2121, sections 7.5 and 9.3.5](https://www.ti.com/lit/ds/symlink/tps2121.pdf),
[TI TLV62569, sections 6.1 and 6.3](https://www.ti.com/lit/ds/symlink/tlv62569.pdf).

**Required correction:** establish a handoff/clamp design whose worst-case
output stays within the downstream operating limits while accepting the
allowed 5 V input range. Include divider/comparator tolerances and source
slew. The advertised 5 us is a typical switchover figure, **not a guaranteed
OV-response bound**; the comments currently treat it as one. Scope both
negotiation directions after the schematic is corrected.

## 53. P1 — J50 does not take over the 5 V load while USB supplies 5 V

**Entities:** U34 PR1/CP2 dividers, D3/D4, J50; `budget.py::mode_rows()` and
the manual's simultaneous-input claim.

With both sources connected, PR1 is about 1.337 V at VBUS = 5 V and CP2 is
about 1.187 V at +3V3 = 3.3 V. OV1 has not tripped. Table 9-3 consequently
selects **IN1 = USB VBUS**, even if J50 supplies VSYS. This is a deliberate
result of the fitted dividers, not an uncertain handoff race.
[TI TPS2121, Table 9-3](https://www.ti.com/lit/ds/symlink/tps2121.pdf).

| Connected sources | Actual source of the +5V rail |
|---|---|
| USB 5 V alone | USB through U34 IN1 |
| USB 9 V alone | U11 through IN2 after OV1 trips; item 52 applies |
| J50 alone | U11 through IN2 |
| **J50 + USB 5 V** | **USB through IN1**, including downstream converters and +5V_EXT |
| J50 + USB 9 V | U11 through IN2; D3/D4 select the VSYS source |

The model's full J50 row assumes all loads come through D4. That assumption
fails in the highlighted case. Its own 5 V allowance is about 1.72 A at
the rail: a programming cable attached to a 500 mA computer port cannot
supply it, despite the bench supply being connected. U34's 2–3 A current
limit does not protect that source allocation.

**Required correction:** give the external input an effective way to take
the complete board load, or explicitly support and budget this hybrid
case with the USB load capped appropriately. Update the source-state
table and user contract together. The existing hardware has no MCU mux
select connection that firmware can simply toggle.

## 54. P1 — FPGA configuration-flash chip select has no startup pull-up

**Entities:** U6 pin 1, U1 P18/FCS_B, R22, U7 GPIO9, PUDC_B.

`FLASH_CS_B` connects only U1, U6 and R22; `SUP_FCS_B` continues through
R22 to U7. Neither net has a pull-up. The FPGA's internal configuration
pull-ups are now disabled, and its core remains off in recovery. The
controller does not provide a hardware-guaranteed high CS during the
flash supply ramp.

UG470 Table 2-4 explicitly requires an **external pull-up of at most 4.7k
to VCCO_14 on FCS_B**. Winbond also requires CS to follow VCC through
power-up/down. Add that bias at the flash/configuration bus and include the
controller's reset state in its sizing. This is a missing schematic part,
not a firmware initialization fix.
[AMD UG470, Table 2-4](https://docs.amd.com/v/u/en-US/ug470_7Series_Config),
[Winbond W25Q256JV rev Q, sections 4.1 and 9.3, manufacturer-authored PDF hosted by TI](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/908/W25Q256JV-SPI-RevQ-02072025-Plus.pdf).

This finding is specifically CS. The fitted **IQ** ordering option has QE
fixed high, so the WP/HOLD pins' quad-I/O behavior does not independently
justify alleging two more missing control pull-ups.
[Winbond ordering information and section 7.1.4](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/908/W25Q256JV-SPI-RevQ-02072025-Plus.pdf).

## 55. P2 — the source-current policy depends on information U7 cannot read

**Entities:** U18 CH224K, USB_CC1/2, PD_PG, VBUS5_ST; `budget.py::SOURCES`
and the generated power-budget instructions.

The budget says Type-C Rp is “read by the CH224K” and that firmware reads
the advertisement. CC1/2 connect only J1 and U18. U7 gets a voltage-request
control and **PG**, not a current/contract data interface. VBUS5_ST reports
the mux selection. These signals cannot distinguish 5 V/default, 1.5 A and
3 A capability, or establish a 3 A PD contract.

The WCH manual distinguishes the CH224K's resistor/logic configuration from
the **CH224A/Q** I2C interface that can report contract current. That newer
interface must not be attributed to the fitted K part.
[WCH CH224 manual 1 v2.1, overview, Table 4-2 and section 5.2.3, manufacturer-authored mirror](https://atta.szlcsc.com/upload/public/pdf/source/20250227/6D68A1393FFD6E9F0B2393231A5DDBA5.pdf).

**Required resolution:** provide observable source capability, or define a
conservative/user-declared power policy that works with the existing
signals. A successful voltage request alone cannot authorize the table's
current allowance. Retain the safe hardware 9 V ceiling if changing the
PD controller. Verify USB startup and the load allowed before enumeration
separately from the table's explicitly configured 500 mA case.

## 56. P2 — TPS22953 support and fault coverage are not fully closed

**Entities:** U23/U24 pin 7 PG, their CT/BIAS bypass networks, PIN V branches.

Both PG pins are marked unconnected. TI section 9.3.3 explicitly says to
**tie unused PG to ground for proper functionality**. Ground them, or use
them with the specified pull-ups in a deliberate reporting circuit.
[TI TPS22953, section 9.3.3](https://www.ti.com/lit/ds/symlink/tps22953.pdf).

The 1.8 V operating-range fix is valid, but the old aggregate current limit
and fault indication were removed. Four slots share each PIN V domain;
four 500 mA PTCs do not impose a 500 mA aggregate ceiling. `EXT_FAULT` now
connects U26/U21/U22, not U23/U24. With SNS tied to OUT, the switches also
have the documented automatic restart after an output-undervoltage fault.
Qualify that behavior with a shorted branch and the upstream shared rail;
do not assume a PTC necessarily trips before a base-board brownout.
[TI TPS22953, sections 9.3.4 and 9.4](https://www.ti.com/lit/ds/symlink/tps22953.pdf).

This tradeoff is acknowledged in the new extension document. The older item
25's blanket “fault isolation fixed” description no longer describes this
hardware. A 0.5 A software allocation remains possible, but is not enforced
by U23/U24. At the 1.8 V jumper setting the upstream source also supplies
VCCAUX, making this a meaningful fault test.

Before freezing these islands, shorten the CT and BIAS loops. The current
C272/C275 pad-to-CT distance is about 5.35 mm and C271/C274 to BIAS about
4.94 mm, with other parts occupying the intervening area. The profile name
“at pin” does not establish local placement. TI calls for CT and bypass
close to the device and a copper clearance beneath CT.
[TI TPS22953, section 12.1](https://www.ti.com/lit/ds/symlink/tps22953.pdf).

## 57. P2 — the regulator street is missing its new high-current junction

**Entities:** U11 → U34 → +5V → U14/U15/U16, the city `CRITICAL`/`DOORS`
rules, and U34's IN2 bypass.

The regulator row remains a sensible arrangement, but U34 is planned below
U7 on the far right. In the staged city, U11→U34 is about 111 mm and
U34→U15 about 94 mm; U11→U15 directly is only 21 mm. These are planning
distances, not final trace lengths. The important error is that the
planner still strongly attracts **U11 directly to U15**, while every ampere
of regulated +5V now passes through U34.

Move U34 into the upstream supply junction near U11 and the low-voltage
row, and reserve the actual U11→U34→loads copper path. Reassess its
connection toward J1 at the same time. IN2 has no bypass in U34's own
island; the documented plan borrows U11's capacitors, which only works if
the two become genuinely adjacent. TI calls for short, wide paths and
local bypass on IN1, IN2 and OUT.
[TI TPS2121, sections 11 and 12.1](https://www.ti.com/lit/ds/symlink/tps2121.pdf).

This is a relative-placement correction worth doing before city
compaction. Grouping the power converters into a street remains acceptable;
aligning the real supply path is what makes that street useful.

## 58. P2 — X4 returned to the power-door side instead of the SYS_CLK side

**Entities:** X4/R147/C246, U1 M21, `city.py::attach`, `SATELLITES`, `RESEAT`.

The latest satellite restoration recovered membership, but the actual PCB
puts X4 at `(759.38, 95.51)` above U1 `(760.00, 122.83)`. SYS_CLK is ball
M21 at `(752.50, 124.33)`, on the left side. R147's SYS_CLK pad is about
31.55 mm straight-line from that ball in this staged placement. The plan
explicitly labels the satellite **N side**, contradicting the floorplan's
left-side correction and placing the clock beside the power door again.

`attach()` averages shared supply pads along with the clock connection;
its result can be dominated by +3V3. The pin-specific `RESEAT` rule only
runs when its parts already belong to the host at planning time, so it
did not govern the separately restored X4 island in this plan.

Use the actual SYS_CLK pin to choose the side, independent of temporary
group state. Keep **X4, R147 and C246** together when applying that rule
(the current RESEAT list names only X4/R147). Put R147 at the oscillator
output and retain a quiet, short clock corridor toward M21. The distance
here flags the wrong neighborhood; it is not a claimed final SI failure.

## Remaining mechanical and qualification work

**The key-post correction is useful but has not proved the mating lattice.**
`place.py --check` still reports J5/J3 pad-lattice disagreement; the
J5/J55/MK69, J3/J53/MK65 and J7/J57/MK76 row-lattice failures; and the six
A–F key offsets. Passing G/H/L/M's individual position-1 check does not
close the row checks. Preserve the recorded above-board microSD access
volume while settling these connector positions.

The ten courtyard errors are six post-to-header pairs and **four
post-to-capacitor pairs**: MK71/C159, MK72/C161, MK76/C143 and MK77/C145.
The latter need their own clearance review; the zero-gap header-body
argument alone does not dispose of them. These are courtyard findings,
not demonstrated body intersections. Reposition the nearby capacitors or
justify each exception from actual body, lead and assembly clearances.
The full DRC pairs are in the evidence file.

**The budget is a better planning model, not a power qualification.** Its
recovery mode selects only RP2350/flash/U20 entries on +3V3, but X4 and the
PHY's 3.3 V supply/internal LDO remain physically powered. SDRAM standby,
other always-on circuitry and the controller's own regulator input power
also need a consistent recovery accounting. Reset is not a supply switch;
use reset/standby current evidence rather than the full-active figures or
zero. This does not prove recovery exceeds 500 mA; it leaves its guarantee
unproven. The light-mode 1.47 A estimate also has only about 30 mA margin
against a 1.5 A source before estimate/efficiency uncertainty.

`mode_rows()` additionally combines U26/U34 limits rather than checking
each path separately, and the new inductor calculation uses nominal L,
frequency and a 9 V input for the wide-input converters. Extend the checks
to each path and the 21 V/tolerance envelope before treating PASS as
qualification. The fitted inductors' nominal margins are a useful positive
result; no saturation failure was demonstrated here.

Keep item 40's complete regulator-network qualification and item 34's
power-down/ramp measurements open. Final FPGA XPE/load estimates, escape
trials, return paths, impedance geometry and prototype SI remain later
milestones. In particular, source-resistor membership in U1 does not
prove sufficiently short driver-side stubs after escape routing.

**Neighborhoods that still make sense:** all four PSRAMs now occupy the
bank-13 side; U13 remains beside bank 16 and the PHY; PHY/crystal/jack and
connector-side ESD ownership remain coherent; SDRAM is between its bank
14/35 escapes; the RP2350 still owns its flash and crystal. Keep these
relationships while correcting U34 and X4. The unused-MGT supply remains
a valid, optional simplification opportunity, not a new defect.

Address 52–54 first, settle 55–56 before freezing the schematic, then
repair 57–58 and the connector lattice while compacting. The earlier
architecture/bank-voltage conclusions remain supported within their stated
boundaries; the changes above are necessary to close the remaining gaps.


## Status of the Part IV findings, 2026-10-29

Corrected the same day, against `9dd5fa8`. Commits `cd74e9f` (schematic
and budget), `e243a09`..`dd31f75` (one island each: Q6, Q7, U34 twice,
J57, J58, U23, U24), `bb9ab7f` (city re-planned and applied). Gate
electrical PASS (parts 553, ERC 0, netlist/XDC/guide in step, parity 0);
DRC 8 courtyard errors (was 10); mechanical 9 findings (was 10). The
entries "Re-audit corrections, part 1 and 2" in `archive/history/rev-a-report.md`
carry the numbers.

| Item | Status | What changed |
|---|---|---|
| 52 U34 handoff above 5.5 V | **FIXED** | The handoff is decided by intent, not by a threshold: Q6 (BSS138) pulls PR1 to ground while PD_REQ_9V is high and, through D24 (1N4148W) into 470k/10 uF, for 2.4-7.2 s after it falls (Table 9-3: PR1 < VREF with CP2 ≥ VREF selects IN2). The rail is on U11 before the charger moves VBUS and stays there until VBUS is back at 5 V; a dead or resetting controller releases the request through R173 and the same hold covers the fall. During the negotiation the rail is U11 in dropout, about 4.5 V (AP63300 LDO mode), inside every +5V consumer's range; EXT_EN stays off until the request is settled. OV1 stays at 5.63 V typical as a fault backstop only; `design.py` now computes its 5.26-5.96 V worst case (reference 1.01-1.10 V, 1 % resistors) and refuses a build that exceeds the TLV62569's 6 V absolute maximum or rejects a 5.25 V USB 2.0 port. The 5 us figure is called typical where it appears. |
| 53 J50 + USB 5 V | **FIXED** | Q7 (BSS138) pulls PR1 to ground while VIN_EXT carries voltage (100k/33k before D4: on between 3.2 and 6.0 V, 2.2 V on the gate at the 9 V minimum, 5.2 V at 21 V). With J50 connected the whole board runs from J50 through U11, whatever is on USB. `budget.py`: the J50 row is also the J50 + USB row; each path (U34, U26) is checked against its own limit and the sum against the source. `user-manual.md`, `power-input.md`, `power.md` say so. |
| 54 FCS_B pull-up | **FIXED** | R203, 4.7k from FLASH_CS_B to +3V3 (UG470 Table 2-4; W25Q256JV CS# follows VCC). Sized with the controller's reset state: an RP2350 pad at reset has its pull-down enabled, which through R22 (33 ohm) leaves CS near 3.0 V [verify the RP2350 pad reset defaults]. |
| 55 source-current policy | **RESOLVED by policy, hardware option recorded** | No readable Rp: the CC lines go only to the CH224K, which has no data interface. The CH224A is pin-compatible but its I2C mode is the single-resistor mode, where register 0x0A can request up to 28 V (CH224 manual 1 v2.1, 5.2.3, Table 5-3), which would give up the 9 V ceiling by construction; not fitted. `budget.py` SOURCES now say what is observable: any 5 V source is a 500 mA port unless user-declared; a granted 9 V request (PD_PG) is a 15 W guarantee under the PD power rules [verify PD3 10.2], so light mode fits and full export does not; J50 is detected on MON_VSYS. Recovery is 0.21 A at 4.75 V: inside 500 mA, above the 100 mA an unconfigured USB 2.0 device may draw, stated as open (PHY, SDRAM, X4 and U20 sit on the always-on +3V3 with no switch). Hardware alternative if wanted: two dual comparators on CC1/CC2 at 0.66 V and 1.23 V into four spare GPIOs, through 1 M series resistors so Rd is not loaded. |
| 56 TPS22953 PG and fault coverage | **PG FIXED; coverage stated, bench open** | U23/U24 PG tied to ground (SLVSCT5D 9.3.3); the symbol pin typed passive so ERC does not call the tie a driver conflict. `extension-ux.md` and `power-input.md` now say plainly: no fault report from U23/U24, four 500 mA PTCs are not a 500 mA ceiling, automatic restart after an output undervoltage (9.3.4, 9.4); the shorted-branch test against the shared rail is a bench item. Islands U23/U24 re-applied with the TPS22953 profile: CT pin to its capacitor pad 1.43 mm (was 5.35), BIAS 1.60 mm (was 4.94). |
| 57 regulator junction | **FIXED** | C280, 1 uF at U34 IN2 (SLVSEA3F 11), innermost at pin 2 by profile rule; the 3 x 22 uF at U11 stay the bulk. `city.py`: U34 closes the top door row (U16, U15, U14, U34) on the USB side; CRITICAL pulls U11-U34 (6), U34-U15 (4), U34-J1 (2) replace U11-U15, so U11 sits above the row against the mux; Q6 and Q7 are satellites of U34 on its PR1 pin (same-side satellites now stack outward). U11 inside the row was tried both ways and rejected: at the right end it pushed U26 off J1, at the left end it pushed PSRAM U2 off the bank-13 side, which the audit asked to keep. Applied, in the 2.2x staged city: U11 to U34 45 mm (was 111), U34 to U15 40 (was 94), U34 to U14 23, U34 to U26 18; U26 kept its place at J1; the four PSRAMs stay on the bank-13 side. |
| 58 X4 side | **FIXED** | `city.py` SATELLITES take a deciding net (X4: SYS_CLK), so attach() uses the M21 ball alone, not the +3V3 pads; RESEAT lists X4, R147 and C246. Applied: X4 on U1's west side at the ball row, R147's SYS_CLK pad 22.7 mm from M21 in the staged city (was 31.6, north side, beside the power door). floorplan.md corrected. |
| mechanical | **PARTLY** | J7/J57/MK76 row lattice: `city.py` snaps the inboard L/M rows to the bus headers' 2.54 mm lattice (J57 is now 6 pitches below J7, MK76/MK77 at position 1 of their rows). J57/J58 re-applied with the slot-row profile change (PIN V fuse and 10 uF inboard, on the AUX fuse's row), which clears MK76/C143 and MK77/C145. Left to the owner (hand placement is authoritative): C159 and C161 on the board, 1.2 mm from MK71/MK72 (park them off the board and re-run J56/J65 with the same profile, or nudge them inboard by hand); the J5/J3 lattice (J5 sits 0.81 mm off J3's row); the A-F posts; the six post-to-header courtyard pairs are the zero-gap contract. |
| budget model | **FIXED as asked** | Per-path limits; inductor peaks at the 21 V / 5.5 V envelope with L at -20 % (all pass, U12 3.19 A of 6.8 A worst); recovery column per load with standby/reset figures (U33 MRAM added to the table); the pre-enumeration allowance stated as not met. |

Still open after this pass: item 40 (COUT beyond the validated range on
U12-U16, bench), item 34 (DS181 ramp and power-down waveforms), the
U23/U24 shorted-branch test, the J1 land pattern against the HCTL drawing
[verify], the pre-enumeration current, the A-F posts and the J5/J3 lattice,
compaction and routing.

---

# Part V — final practical audit, 2026-10-29

## Final practical verdict

**The schematic and district plan are a reasonable basis for detailed
placement and a first prototype. The previous three P1 circuit findings
are corrected. I found no additional confirmed schematic blocker.**

This is the verdict at `6ad8068`, including the new Q6/Q7 mux controls and
the `districts` city plan. It supersedes the older audit's open/closed
language. It is approval to advance the design to placement, not a claim
that the present staged board is ready to order. No hardware or placement
was changed during this review.

The earlier reviews mixed schematic defects with normal layout and
prototype work too readily. In particular, a nominal capacitor sum above
a datasheet example, or a few millimetres in an unfinished island, does
not establish a faulty circuit. Those points are treated proportionately
below.

| Reproduced check | Result |
|---|---|
| Design model versus every connected PCB pad | **553 parts, 553 footprints, 0 mismatches** |
| Schematic netlist, XDC, gate top and parts guide | Match their generators; 553/553 roles covered |
| ERC / schematic parity | **0 errors / 0 differences**; the two intentional temperature-diode warnings remain |
| DRC | 8 courtyard errors, 297 warnings; a separate error-only run also finds just those 8 courtyard errors |
| Mechanical checker | 9 findings: 3 lattice/row findings and 6 A–F key-position findings |
| Gate | Electrical PASS, mechanical FAIL |
| Stage | 66 origins on-board, 487 staged outside; all front-side; no tracks or vias |

The old phase-report note about an L1/R8 copper-clearance error was not
reproduced by either current DRC run; it is not counted as another blocker.
The saved evidence is
[final-audit-2026-10-29.json](archive/history/board-review/final-audit-2026-10-29.json).

## Previous findings: final disposition

| Item | Verdict now |
|---|---|
| 52 Mux overvoltage during negotiation | **Original normal-transition defect addressed.** Q6 pulls PR1 low during the 9 V request and holds it afterward; the mux selects U11 rather than waiting for OV1. The circuit is sensible for the intended startup sequence. Confirm transitions and controller resets on the prototype. |
| 53 J50 plus USB 5 V | **Fixed.** Q7 senses VIN_EXT before D4 and overrides PR1. At the valid 9–21 V J50 input, it selects U11 even with USB connected. |
| 54 Flash chip-select bias | **Fixed.** R203 is fitted, 4.7k from FLASH_CS_B to +3V3. |
| 55 Source-current policy | **No automatic Type-C current claim remains, but the source-qualification wording still needs the clarification below.** This can be resolved in policy/firmware without a new power-tree design. |
| 56 TPS22953 support | **Pin/bypass corrections verified.** Both PG pins are grounded. CT and BIAS pad distances are now about 1.43 and 1.60 mm respectively: reasonable. The accepted PTC-based fault behavior is a prototype test, not an unfinished pin-map fix. |
| 57 Power junction placement | **Fixed at planning level.** U34 is in the power district, C280 supplies its local IN2 bypass, and the planner follows the actual U11→U34→loads path. |
| 58 Oscillator side | **Fixed.** X4/R147/C246 are together west of U1, selected from SYS_CLK/M21 rather than shared supply pins. |

The mux selection agrees with
[TI TPS2121 Table 9-3](https://www.ti.com/lit/ds/symlink/tps2121.pdf).
Q6/Q7 are switching a small divider current, not the board load; their
threshold/headroom is appropriate to that task.
[onsemi BSS138L datasheet](https://www.onsemi.com/pdf/datasheet/bss138lt1-d.pdf).

The long Q6 hold is a reasonable practical solution. Its exact “2–7 s”
value is an estimate, not a precision timer specification. USB PD allows a
25–35 ms preparation interval before a fixed-voltage transition, and a
normal SPR voltage transition settles within 275 ms of transition start.
Check the actual gate charging and release waveforms; there is no reason
to redesign this circuit merely because the RC timing is approximate.
[USB-IF PD R3.2 v1.1, section 7 timing parameters, author-issued specification mirrored at HWWiki](https://www.hwwiki.net/lib/exe/fetch.php?media=%E6%A0%87%E5%87%86%3Ausb%3Apd%3Ausb_pd_r3_2_v1.1_2024-10.pdf).

## What still merits action

**Finish the extension connector geometry before ordering.** J5/J3 still
have different pad lattices, J5/J55/MK69 and J3/J53/MK65 still fail their
row tests, and the A–F keys remain out of position. Those errors affect
whether an extension physically plugs in. They are real, expected
placement work at the present stage.

Six of the eight courtyard errors are the acknowledged zero-gap
post/header arrangement. A justified courtyard exception is reasonable
where the real bodies fit; it does not warrant expanding the board just
to satisfy a library outline. The other two are MK71/C159 and MK72/C161:
move/check those capacitors when legalizing the connectors. No body
intersection or copper short was demonstrated by these courtyard reports.

**Make source qualification explicit in firmware and the power contract.**
Two current statements are too strong:

- **MON_VSYS alone does not identify J50.** USB-PD at 9 V and J50 near
  9 V can produce the same VSYS voltage; with USB attached, PD_PG and the
  mux status can also agree in those two cases. Before authorizing the
  J50-only full-export budget, require a declared external supply or a
  source test, for example requesting USB 5 V and confirming that VSYS
  remains in the external-input range after settling. No additional
  detector is necessary if that policy is acceptable.
- **A granted 9 V request is not universally a 15 W guarantee.** Managed
  multi-port sources may offer 9 V at a reduced available power, and
  optional PDOs also exist. The fitted CH224K still does not report that
  current to U7. For this prototype, specify a qualified source providing
  at least 9 V / 1 A for the present board-only estimate of about 0.83 A,
  with practical headroom, and keep full export on the qualified J50
  supply. Do not infer the 1.67 A budget solely from PD_PG.

The second point follows from the actual source rules, including the
managed-port cases in Table 10-3; it does not require designing around
every possible charger. A stated, qualified supply requirement is enough.
[USB-IF PD R3.2 v1.1, sections 10.2 and 10.2.3, Table 10-3](https://www.hwwiki.net/lib/exe/fetch.php?media=%E6%A0%87%E5%87%86%3Ausb%3Apd%3Ausb_pd_r3_2_v1.1_2024-10.pdf).

**Keep the known USB cold-start limitation visible.** The approximately
0.21 A recovery estimate exceeds legacy USB 2.0's 100 mA allowance before
configuration. This does not mean every computer port will fail; many
will power the board. It does mean universal bus-powered startup has not
been established. For an engineering prototype, a qualified port or J50
is a practical operating restriction. If guaranteed startup on arbitrary
legacy computer ports is a release requirement, the always-powered load
needs reduction or switching before that guarantee can be made. This is
already acknowledged in the budget, rather than a new hidden defect.

## District and island verdict

**The regulator street is acceptable.** It now contains the real mux
junction, with U11/U12 together in the input district and U13 beside the
PHY. U11→U34 is about 30 mm in the staged city, versus 111 mm in the old
plan. These distances are not final copper lengths. During compaction,
prioritize each converter's switching loop, then its output-capacitor
connection to the rail, and preserve a wide U34 output corridor to the
low-voltage row. The row itself does not need further rearrangement for
appearance or marginal centroid improvements.

| District | Practical assessment |
|---|---|
| Four PSRAMs in a 2×2 block | Good use of the bank-13 neighborhood. Source resistors stay with U1; shorten the actual escapes when routing. |
| FPGA clock | Correct west-side ownership and direction now. The staged distance is not a reason to reopen item 58. |
| RP2350, its flash and crystal | Correct grouping. Preserve the local regulator/crystal sub-islands when moving the whole controller block. |
| USB input and converters | Coherent: J1/U26/U18 together, U34 at the power row, U11/U12 adjacent. Reserve the VSYS route from the separate J50 entry. |
| PHY, crystal, jack and 2.5 V regulator | Sensible arrangement; the PHY is now directly above its jack. Keep MDI pairs clear of switching circuitry. |
| Configuration flash and MRAM shelf | Acceptable. Keep the configuration SPI run direct; there is no benefit in pulling the much wider SDRAM bus into this shelf. |
| SDRAM below U1 | Reasonable compromise between its bank-14 and bank-35 connections. Actual clock/data routing decides timing. |
| PIN V controls in opposite service corners | Reasonable relative to their separate banks and slot columns. They need wide supply distribution, not side-by-side placement. |
| JTAG corner and LED dashboard | Sensible access/ownership choices; both have low placement priority compared with memory and power loops. |
| Inboard microSD | Accepted above-board access choice. Preserve the already documented travel/finger space. |

The 2.2× city is a planning diagram. Fitting connector bodies and routing
corridors into the real 100×100 mm outline (100 x 140 mm since 2026-11-03)
still has to be done. That is
the next design phase, not evidence that these neighborhoods are wrong.
The new district names should be reflected in the current-plan paragraph
of `floorplan.md` eventually; stale “best” wording is documentation cleanup.

## Prototype checks, rather than another schematic redesign

Use the first board to answer the following concrete questions:

1. **Mux:** capture VBUS, +5V and the hold signal through 5→9 V, 9→5 V,
   controller reset, and USB/J50 connection changes. Confirm handoff
   occurs before VBUS rises and lasts through its return.
2. **Regulators:** check startup and load steps on the assembled output
   networks, especially the large 1 V FPGA capacitor bank, at relevant
   input voltages and jumper choices. Do not remove required FPGA
   decoupling to match a regulator's example schematic.
3. **FPGA supplies:** capture +3V3/VCCAUX ramps and power-down, including
   recovery/reset. The hardware no longer leaves VCCAUX waiting on
   firmware; verify the resulting waveforms.
4. **PIN V faults:** short a protected extension branch under a controlled
   supply and observe the shared rail/restart behavior. A base-board
   reset is possible under the documented PTC-only contract; decide
   whether that behavior is acceptable from the measurement.

## Minor points that do not block progress

- U16's approximately 50 uF nominal sum versus a 47 uF example is not an
  independent defect. Part tolerance and effective capacitance are larger
  effects. Include it in ordinary bring-up, without a special redesign.
- The corrected CT/BIAS placement is adequately local for this stage.
  There is no useful audit action in shaving fractions of a millimetre.
- BOOTSEL button distance is an access/low-speed routing choice; it is
  not equivalent to moving the QSPI flash away from U7.
- A small series resistor in D24's charging path would be sensible
  cleanup to limit the 10 uF capacitor's initial GPIO charge pulse. The
  present waveform deserves observation; no damaging current or failed
  negotiation has been demonstrated. RP2350 drive-strength settings are
  not hard current limits.
  [Raspberry Pi RP2350 datasheet, section 14.9.4.1](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf).
- J1's modified land pattern still deserves the usual connector-drawing
  comparison before fabrication. Its drill-clearance error is fixed; the
  outstanding comparison is ordinary footprint review, not a renewed
  electrical blocker.

**Advance to placement.** Resolve the physical connector fit before PCB
ordering, implement the conservative source policy, and use prototype
measurements to close the remaining analogue questions. The current
evidence does not justify another broad architectural redesign.
