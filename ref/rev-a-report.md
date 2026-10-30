# Freya rev A: phase report

Appended per phase. Numbers come from `python3 tools/gate.py`; the escape
depth from `python3 tools/depth.py --pcb`. Baseline is `bf28a92`, see
`ref/rev-a-plan.md` section 1.

## Phase A0 2026-10-23
Parts: 520 -> 520
B.Cu footprints: 0
Escape depth >= 7: 58 (17 inherent, 41 allocator choice)
ERC: 0 errors, 2 warnings (allowlisted FPGA_DXP/FPGA_DXN)
DRC: 49 errors, 344 warnings, 499 unrouted, 0 parity
PCB sync: `load_pcb.py` between `check_positions.py` snapshots, 0 of 520 moved
Files changed: tools/design.py, tools/place.py, tools/placement.py,
tools/depth.py (new), tools/gate.py (new), kicad/fpga.kicad_sch, kicad/odin.net,
kicad/odin.kicad_pcb, ref/rev-a-report.md (new)
What: mode-pin straps 4.7 k -> 1 k (UG470 v1.17 Table 2-4); the `place.py`
rule that flipped FPGA decoupling to B.Cu is deleted (single-sided
assembly); `tools/depth.py` measures escape depth; `tools/gate.py` runs the
phase checks.
Known: `place.py --check` fails on the connector contract (J3/J5 not at
y = 50, key posts unplaced). Hand placement in phase B, as recorded in
`ref/kicad-validation.md`.
Open questions for the owner: none

## Phase A1 2026-10-23
Parts: 520 -> 477
B.Cu footprints: 0
Escape depth >= 7: 58 (17 inherent, 41 allocator choice)
ERC: 0 errors, 2 warnings (allowlisted FPGA_DXP/FPGA_DXN)
DRC: 18 errors, 325 warnings, 499 unrouted, 0 parity
PCB sync: `load_pcb.py` between `check_positions.py` snapshots, 0 of 477
moved; removed C233-C247, D12-D16, J66, J67, L10, Q5-Q8, R131-R144, U28, U29
Files changed: tools/design.py, tools/budget.py, tools/qualified.py,
tools/gen_kicad.py, tools/gen_project.py, tools/check_connector_rework.py,
tools/update_silkscreen.py, tools/placement.py, tools/check_aux_magnetics.py
(deleted), ref/aux-magnetics.md (deleted), kicad/odin.pretty/L_PROD_PSSCAQ1285
(deleted), ref/power.md, ref/power-input.md, ref/extension-ux.md,
ref/jlcpcb-import-checklist.md, generated: ref/power-budget.md,
ref/qualified-parts.md, kicad/odin.kicad_sym, kicad/power.kicad_sch,
kicad/odin.net, kicad/odin.kicad_pcb
What: decision D1. The LM5157 SEPIC lab rail and its 9/12/15/24 V cap
selector and REG/AUX/RAW source selector are removed. J68 AUX IN now drives
`AUX_RAIL` directly; the only other parts on that net are the ten C70150
branch PTCs. Power-row pinout unchanged (pin 7 = slot AUX). `AUX_REG` and
`AUX_RAW` nets, the `AUX_5A` net class and the 50 V capacitor marking on
`AUX_RAIL` are kept. The surge release hold (SMBJ22A 35.5 V clamp plus a
charged 24 V output over the LM5157 SW 50 V absolute maximum) closes with
the converter. The 18 remaining DRC errors are the pre-existing placement
collisions (C185/C186/C192, J57/F4, C158/F31, J60/J61/X2, J1 hole clearance).
Known: `place.py --check` still fails on the connector contract (phase B).
Open questions for the owner: none

## Phase A2 2026-10-23
Parts: 477 -> 459
B.Cu footprints: 0
Escape depth >= 7: 58 (17 inherent, 41 allocator choice)
ERC: 0 errors, 2 warnings (allowlisted FPGA_DXP/FPGA_DXN)
DRC: 18 errors, 324 warnings, 499 unrouted, 0 parity
PCB sync: `load_pcb.py` between `check_positions.py` snapshots, 0 of 367
common refs moved; removed C1-C110, added C301-C392 staged outside the board
Files changed: tools/design.py, tools/qualified.py, tools/load_pcb.py,
ref/decoupling.md (new), kicad/README.md, generated: ref/qualified-parts.md,
kicad/*.kicad_sch, kicad/odin.net, kicad/odin.kicad_pcb
What: FPGA decoupling is now UG483 v1.14 Table 2-2, row FGG676 / XC7A100T,
in the Table 2-5 packages: VCCINT 1 x 330 uF D-case tantalum
(T520V337M2R5ATE025) + 6 x 4.7 uF 0805 + 8 x 0.47 uF 0603; VCCBRAM (on
+1V0) 1 x 100 uF 1210 + 2 x 0.47 uF; VCCAUX 1 x 47 uF 1210 + 3 x 4.7 uF +
5 x 0.47 uF; VCCO bank 0 1 x 47 uF; each I/O bank 2 x 4.7 uF + 4 x 0.47 uF;
one 47 uF per voltage group of up to four banks (note 3), computed from
`gen_sch.RAIL` so A4's bank 16 move regroups itself. MGTAVCC/MGTAVTT
(note 2, UG482) and VCCADC keep their previous 100 nF-per-ball scheme. 67
UG483 parts + 24 MGT + 1 VCCADC = 92, replacing 110. The new parts take
explicit refs C301.. so they do not inherit the script-made 0402 positions
around U1 (those 96 were not hand placement); `reserve('C', 110)` keeps
every later C ref, including the 11 hand-placed ones inside the board.
Placement rule written in `ref/decoupling.md`.
Tool fix: `load_pcb.py` started its import band at a fixed y = 145 and
stacked new parts on footprints staged there by earlier imports (C351-C354
landed on U9/U10, 23 DRC errors). It now starts below the lowest existing
footprint. The PCB was restored from the A1 commit and re-synced.
Known: `place.py --check` still fails on the connector contract (phase B).
No LCSC listing found for the tantalum; owner sources it at quote time (D3).
Open questions for the owner: none

## Phase A3 + A4 2026-10-23
Parts: 459 -> 459 (53 Fast Links parts out, 39 Network parts in, status
expander and its LEDs moved to the Board Controller sheet, one more 47 uF
for the new +2V5 VCCO group)
B.Cu footprints: 0
Escape depth >= 7: 50 (17 inherent, 33 allocator choice); was 58 (17, 41)
ERC: 0 errors, 2 warnings (allowlisted FPGA_DXP/FPGA_DXN)
DRC: 9 errors, 323 warnings, 499 unrouted, 0 parity (the 9: C185/C186/C192,
F4/J57, C158/F31 collisions and the four J1 hole clearances, all
pre-existing)
PCB sync: `load_pcb.py` between `check_positions.py` snapshots, 0 of 420
common refs moved; removed X2, Q1, FB1/FB2, J60/J61, SH1/SH2, U27 and their
R/C; added U30, J70-J72, X3, D20-D23 and their R/C, staged outside the board
Files changed: tools/design.py, tools/alloc.py, tools/gen_sch.py,
tools/gen_project.py, tools/gen_kicad.py, tools/ballmap.py, tools/budget.py,
tools/qualified.py, tools/placement.py, tools/place.py,
tools/update_silkscreen.py, tools/check_connector_rework.py,
tools/sfp_cage.py (deleted), easyeda/EasyEDA.kicad_sym (+5 imports),
easyeda/EasyEDA.pretty (+5 footprints), easyeda/EasyEDA.3dshapes (+6),
kicad/odin.pretty/Amphenol_U77A11133001 (deleted), kicad/network.kicad_sch
(new, replaces highspeed.kicad_sch), ref/network.md (new),
ref/link-ports.md (new), ref/highspeed.md, ref/sfp-cage.md, ref/sfp-i2c.md
(deleted), ref/status-leds.md, ref/user-manual.md, ref/extension-ux.md,
ref/jlcpcb-import-checklist.md, kicad/README.md, generated: ref/ballmap.md,
ref/power-budget.md, ref/qualified-parts.md, kicad/*.kicad_sch,
kicad/odin.kicad_sym, kicad/odin.net, kicad/odin.kicad_pcb
What (A3): Fast Links are gone: the two SFP ports, cages, 125 MHz oscillator,
power gate and I2C switch, and the SFP nets on the RP2350B (GPIO32-39 and
46 are spare; GPIO14/31 are now SUP_SCL/SUP_SDA for U17, renamed "status
expander", P7 spare). Both GTP quads stay powered with grounded RX, floating
TX/refclk and one RCAL each (UG482 Tables 5-5/5-6). New Network sheet:
RTL8211FD-CG (D2, C2687133) on RGMII at 2.5 V with straps per datasheet rev
1.7 Tables 10/11 (PHYAD 1, PLLOFF 0, TXDLY 1, RXDLY 1 to DVDD_RG; CFG_EXT 1
and CFG_LDO 01 to 3.3 V/GND), 1.5 k MDIO pull-up (section 7.11.2), 1 k
pull-down on PHYRSTB and 4.7 k pull-up on INTB with both pins on bank 13
(bank 35 since 2026-10-29)
(Table 58 note, Table 53 note 5 case II), LEDs in the jack wired per section
7.9 Figure 5, HanRun HR911130A 1000Base-T magjack (C54408) with P1 centre
tap to GND through 100 nF 50 V and P10 (internal Bob-Smith) to GND, YXC
25 MHz crystal (C9006, Table 56) with 18 pF loads and a 0 ohm series spot,
RSET 2.49 k 1 %. Two plain shielded 8P8C jacks (Kinghelm C2683360) carry
eight DC-coupled LVDS_25 pairs with TPD4E1U06 arrays (C124691) at the jacks;
pinout and the "power both boards first" rule in ref/link-ports.md. Parts
imported with easyeda2kicad (scratch venv); the TVS and crystal footprints
got their own copies because the importer had reused another part's
identically named land; the jacks' mounting holes were corrected to NPTH.
What (A4): VCCO_16 = +2V5 (gen_sch.RAIL; the UG483 decoupling regrouped by
itself: one more 47 uF). alloc.py allocates bank 16 shallowest-first with
PHY_RXC on an MRCC P ball, LINK P RXC on the other MRCC pair, LINK Q RXC on
an SRCC pair; both 5 V buses and their DIR/OE plus PHY_RESET_N/PHY_INT_N in
bank 13 (the PHY pins moved to bank 35 on 2026-10-29); banks 13, 14 and 16 depth sorted (15 and 34 are full and keep
their order). `alloc.py --check` verifies the clock placements and bank
membership.
Decisions taken without the owner: RSET 2.49 k and the centre-tap capacitor
come from public RTL8211F boards (NanoPi M5), not the Realtek datasheet,
marked [verify] in ref/network.md; PHY load in the budget is a 0.2 A
planning estimate (the datasheet has no active-mode consumption table);
jack positions in placement.py are a proposal for phase B, mouth
orientation to be confirmed in 3D (STEP models imported).
Known: `place.py --check` still fails on the connector contract (phase B).
`gen_pcb.py` MGT_100R patterns and ref/pcb-impedance.md still describe the
SFP nets; replaced by LVDS_100R/RGMII in B1 as planned.
Open questions for the owner: none blocking. If a 1000Base-T jack with a
different LED arrangement is preferred, only `J70`'s pin map changes.

## Phase A4b (system clock) 2026-10-23
Parts: 459 -> 462
B.Cu footprints: 0
Escape depth >= 7: 51 (17 inherent, 34 allocator choice)
ERC: 0 errors, 2 warnings (allowlisted FPGA_DXP/FPGA_DXN)
DRC: 9 errors, 324 warnings, 499 unrouted, 0 parity (unchanged set)
PCB sync: `load_pcb.py` between `check_positions.py` snapshots, 0 of 459
moved; added X4, C246, R147
Files changed: tools/alloc.py, tools/design.py, tools/gen_kicad.py,
tools/qualified.py, tools/budget.py, tools/placement.py,
tools/update_silkscreen.py, tools/ballmap.py, easyeda/EasyEDA.kicad_sym,
easyeda/EasyEDA.pretty/OSC-SMD_4P-L3.2-W2.5-BL (new), floorplan.md,
generated: ref/ballmap.md, ref/power-budget.md, ref/qualified-parts.md,
kicad/*.kicad_sch, kicad/odin.kicad_sym, kicad/odin.net, kicad/odin.kicad_pcb
What: audit gap found while preparing the XDC: the fabric had no clock
source. X2 only fed the GTP reference input, Y1 is the RP2350's crystal and
the PHY's RXC exists only with a link up, so nothing could clock NEORV32 at
power-on (ref/gameboy-extension.md already assumed a "board oscillator +
MMCM"). Added X4, YXC OT322550MJBA4SL 50 MHz CMOS oscillator (C717684,
imported with easyeda2kicad; 1.8-3.3 V, +/-20 ppm), tri-state pin tied to
VDD, 100 nF bypass, 33 ohm source resistor, into bank 14 on an MRCC P ball
(`SYS_CLK`), allocated before the PSRAM pairs (now the SDRAM address pool); `alloc.py --check` verifies
the MRCC placement. One more deep ball results (the shallow MRCC pair went
to the clock). floorplan.md rewritten for the rev A board (jacks, network
strip, decoupling placement rule).
Known: oscillator current and OE behaviour are from the YXC family listing
(datasheet PDF did not download); `place.py --check` connector contract
still fails (phase B).
Open questions for the owner: 50 MHz chosen as a safe NEORV32 default; say
if you want another frequency (any 3225 CMOS part fits the same land).

## Phase A5 2026-10-23
Parts: 462 (unchanged)
B.Cu footprints: 0
Escape depth >= 7: 51 (17 inherent, 34 allocator choice)
ERC: 0 errors, 2 warnings (allowlisted FPGA_DXP/FPGA_DXN)
DRC: 9 errors, 324 warnings, 499 unrouted, 0 parity (unchanged)
PCB sync: none (no netlist change)
Files changed: tools/gen_xdc.py (new), tools/gate.py, ref/freya.xdc (new),
gateware/gate/top.v (new, generated), gateware/gate/gate.xdc (new),
gateware/gate/run.tcl (new), kicad/README.md, .gitignore
What: `tools/gen_xdc.py` renders `ref/freya.xdc` from `tools/alloc.py`:
185 constrained balls (then; bank 13: 22 LVCMOS33, 14: 37 LVCMOS33, 15: 48 and
34: 48 LVCMOS33 at the 3.3 V jumper position, 16: 14 LVCMOS25 + 16 LVDS_25
with DIFF_TERM on the eight receive pins), SLEW FAST on the RGMII
transmit pins, four input clocks (SYS_CLK 50 MHz, PHY_RXC 125 MHz, the two
link receive clocks at a 100 MHz placeholder) and the SPIx4 configuration
properties (CFGBVS VCCO, CONFIG_VOLTAGE 3.3, SPI_BUSWIDTH 4, CONFIGRATE 33,
COMPRESS). The same run writes `gateware/gate/top.v`, a throwaway design
that uses every constrained port (BUFG on each clock, IBUFDS/OBUFDS on the
LVDS pairs, IOBUF on every bidirectional pin). `gate.py` now fails on XDC
drift the way it fails on netlist drift.
Vivado gate: `vivado v2026.1 (64-bit)` at /tools/Xilinx/2026.1, part
xc7a100tfgg676-2, `gateware/gate/run.tcl` in batch mode: synthesis, opt,
place, route, `write_bitstream` -> GATE BITSTREAM OK, 0 DRC checks found
on the routed design, 0 critical warnings, all timing constraints met
(worst setup slack 8.739 ns), 578745-byte compressed bitstream. This proves
the allocation is legal on the real part: clock-capable balls, LVDS_25 at
VCCO 2.5 V with DIFF_TERM, LVCMOS25/LVDS_25 mixing in bank 16, SPIx4 flash
pins and PUDC_B as user I/O after configuration.
Known: Vivado part names carry no temperature grade; the -2 speed grade is
what the industrial -2I part times to. The link clock periods are
placeholders until the ports are characterised. Run time about six
minutes, so the Vivado gate stays a manual step (README "Verify").
Open questions for the owner: none

## Phase B1 2026-10-23
Parts: 462 (unchanged)
B.Cu footprints: 0
Escape depth >= 7: 51 (17 inherent, 34 allocator choice)
ERC: 0 errors, 2 warnings (allowlisted FPGA_DXP/FPGA_DXN)
DRC: 9 errors, 324 warnings, 499 unrouted, 0 parity (unchanged set; the
new rules add nothing on the unrouted board)
PCB sync: `gen_pcb.py --rules-only` only; footprint count and the 111
inside / 351 staged split unchanged
Files changed: tools/gen_pcb.py, tools/islands.py (docstring),
ref/pcb-impedance.md, ref/jlc08161h-1080a-stackup.json (new),
kicad/README.md, kicad/odin.kicad_pcb (layer list and stackup blocks only),
kicad/odin.kicad_pro (net classes), kicad/odin.kicad_dru
What: the board is 8 layers, JLC08161H-1080A, S/GND/S/PWR/GND/S/GND/S:
F.Cu, In1 GND, In2 signal, In3 power, In4 GND, In5 signal, In6 GND, B.Cu
(KiCad 9 layer ids). The template comes from JLC's impedance-template API
as published by gsuberland/jlcpcb_autogenerated_stackups (retrieved
2026-10-23, saved in the repo). It keeps the 0.0764 mm / Dk 3.91 1080 outer
prepreg of the old 6-layer template, so the saved JLC solver result for the
100 ohm coated microstrip (0.099 mm / 0.200 mm) still applies to F.Cu over
In1 and B.Cu over In6; every 0.1 mm core puts a routing layer against a
ground plane and the power plane against a ground plane. Net classes:
MGT_100R dropped; LVDS_100R (LINK_*) and MDI_100R (ETH_MDI*) with the 100
ohm geometry, outer layers only, 0.1 mm intra-pair skew and 0.31 mm
track-to-other-copper clearance; RGMII (the twelve RGMII lines) at
0.125 mm, a Hammerstad-Jensen estimate for 50 ohm to be confirmed with
JLC's calculator; PSRAM and AUX_5A unchanged. `islands.py --netclasses`
re-ran so the 71 island classes carry no SFP nets.
Tool fix: the first form of the 0.31 mm rule fired between the PHY's
0.4 mm-pitch pads (15 errors); it now applies to tracks only.
Known: RGMII 50 ohm width is an estimate, flagged in ref/pcb-impedance.md
and tools/gen_pcb.py. `place.py --check` connector contract still fails
(phase B3). The owner orders the JLC08161H-1080A template by name (D3).
Open questions for the owner: none

## Annotation, part 1 (mechanism, FPGA and Network sheets) 2026-10-27
Parts: 462 (unchanged)
ERC: 0 errors, 2 warnings (allowlisted); DRC: 9 errors, 324 warnings, 499 unrouted, 0 parity
PCB sync: `load_pcb.py` between snapshots, 0 of 462 moved (Description fields only)
Files changed: tools/roles.py (new), tools/gen_project.py, tools/load_pcb.py,
tools/gate.py, kicad/README.md, ref/parts-guide.md (new, generated),
kicad/*.kicad_sch, kicad/odin.net, kicad/odin.kicad_pcb
What: every part now carries a plain-words "what it's for". tools/roles.py
holds a paragraph per schematic group, a line per active part, and notes on
nets whose resistors mean more than their topology (straps, RCAL); lines for
resistors, capacitors, inductors and fuses are derived from their nets
(bypass, pull-up, series, ...) and name the part they serve. The text goes
into each symbol's Description, a paragraph inside every group box, each
footprint's Description field, and ref/parts-guide.md. gate.py fails on an
unexplained part or group on a covered sheet, a stale entry, or a stale
guide. Covered: FPGA and Network; Power, Memory, Supervisor and Slots are
reported (125 gaps) and come next.
Open questions for the owner: tone and depth of the sample text.

## Annotation, part 2 (all sheets) 2026-10-27
Parts: 462 (unchanged); roles: 462/462 described, 0 problems
ERC: 0 errors, 2 warnings (allowlisted); DRC: 9 errors, 324 warnings, 499 unrouted, 0 parity
PCB sync: `load_pcb.py` between snapshots, 0 of 462 moved; no footprint has an empty Description
Files changed: tools/roles.py, ref/parts-guide.md, kicad/*.kicad_sch, kicad/odin.net, kicad/odin.kicad_pcb
What: text for the Power, Memory, Board Controller and Slots sheets; every
sheet is now enforced by the gate. Net notes can match a family by prefix
(FB_, SW_, EN_, PSRAM, ...); a passive's "for ..." now names the IC or
connector of its group, not the key post; MON_ nets are measurements, not
supplies; parts not fitted say so.
Open questions for the owner: none

## Memory pass 2026-10-29
Parts: 499 (was 470); B.Cu footprints: 0; nothing placed inside the outline.
ERC: 0 errors, 2 warnings (allowlisted FPGA_DXP/FPGA_DXN). alloc.py --check,
audit_easyeda.py, qualified.py and roles.py pass. Constrained balls: 273.
What, one commit per step:
1. `+1V8_IO`: U14's output node (L5, its 22 uF pair, the feedback divider,
   the J19/J20 1.8 V position, MON_1V8); VCCAUX and VCCADC stay `+1V8` behind
   FB1 (BLM18PG121SN1D, C14709) with 10 uF + 100 nF at the regulator.
   budget.py: U14 at 0.308 A of 2 A.
2. Bank 13 VCCO = `+1V8_IO`; U2-U5 become APS6404L-SQN-SN (C5360304, 8 MB,
   1.8 V) on hand-chosen bank 13 pairs, VDD and C111-C114 on `+1V8_IO`,
   R104-R127 kept; U9/U10 VCCA, their bypass and the OE pull-ups on
   `+1V8_IO` (SCES916A section 6.3: VCCA 1.08-5.5 V); bank 13 LVCMOS18.
3. PHY_RESET_N -> G1, PHY_INT_N -> G2 (bank 35).
4. U32 W9825G6KH-6 (C62246): DQ/control on 24 plain bank 35 balls, A0-A12
   and BA0/BA1 on the bank 14 block the PSRAMs left; 7 x 100 nF + 10 uF,
   22 ohm on CLK, 10k CS up, 10k CKE down; SDRAM_CLK in its own XDC section.
5. U33 MR25H10CDF (C246234) on K25 K26 L24 L25 with its 100 nF and three
   10k; footprint with two ground vias in the pad. Fitted on every board
   (owner, 2026-10-29; it was a DNP option for one commit).
6. J74 TF-01A (C91145) microSD in SPI mode on L22 L23 T22 R22 T23, five 10k
   pull-ups, 100 nF + 10 uF; SD_CD read with the FPGA pull-up.
7. Documents regenerated and the hand-written text updated.
Same day, after the owner's word: U33 fitted on every board (no DNP).
Islands built and parked for U32, U33 and J74 (generic rules, no layout
profile: the datasheets give no layout example); U1 extended with FB1,
C261, C262 and the +1V8_IO 47 uF C394. design.py now appends a new rail's
group capacitor after the MGT ones (the first regeneration had renumbered
C366..C393 and swapped two packages at reviewed spots); load_pcb.py keeps
a replaced footprint in its island group. City plan rerun and applied:
51 groups, 40 moved rigidly, J74 inboard south-west of U1 (no edge has
its 14.5 mm), U32 below U1 between banks 14 and 35, U33 west of U1.
Known: the 12 new footprints and FB1 sit in the import band below the
board, unplaced; sequential C numbers above C250 shifted between steps 1
and 5 (nothing on the board depends on them yet).

## Audit corrections, part 1: power path and board-controller pins 2026-10-29
Parts: 516 (was 499); roles 516/516; ERC 0 errors, 2 allowlisted warnings;
DRC 4 errors (the J1 hole clearances, part 3), 0 parity; nothing moved:
`check_positions.py` 0 of 499 common footprints; 25 new footprints staged in
the import band, 8 removed (Q2, R46-R49, C183, R90, R92).
Findings items 34, 35, 36, 37, 38, 42 and 50 (findings.md Part III).
What:
- U11 and U14 have no enable any more: U11's EN floats (DS42002 p. 3,
  automatic start-up, as U12), U14's EN is tied to +5V (SLVSDG1C: EN
  -0.3..6 V absolute). +1V8, VCCAUX, is therefore up whenever +3V3 is, so
  the 3.3 V banks never wait on firmware for their VCCAUX (DS181 Table 7).
  GPIO23 and GPIO26 are spare.
- The Q2/Q3 VBUS pass switch is replaced by U34, a TI TPS2121 power mux
  (SLVSEA3F): IN1 VBUS, IN2 U11's output (+5V_BUCK), OUT +5V. Reverse
  blocking on both inputs, 2.5 A limit (44.2k), 100 nF soft start, 5 us
  switchover. PR1/CP2 dividers select VBUS only between 4.44 V and 5.63 V
  (OV1), so a 9 V contract hands the rail to U11 in copper, not firmware.
  ST on GPIO21 (VBUS5_ST). U11 runs all the time so the hand-over has no gap.
- 27 ohm series resistors in USB D+/D- at the controller (RP2350 hardware
  design guide 5.1): U7 on USB_DP_MCU/USB_DM_MCU, J1 and D6 on USB_DP/USB_DM.
- CH224K: CFG1 10k pull-up to PD_VDD (5 V request before and without the
  controller; WCH Table 5-2), Q3 pulls it low for 9 V (PD_REQ_9V, GPIO27,
  100k gate pull-down), CFG2/CFG3 grounded so no pin state can request more
  than 9 V. GPIO28/29 spare.
- Local input capacitors: 10 uF 50 V 1210 across U11's VIN (DS42002 Figure
  39), 4.7 uF at each TLV62569 VIN (SLVSDG1C 8.2.2.5).
- Controller pins on native peripherals (RP2350 datasheet 9.4): flash bus on
  SPI1 (SCK 10, TX 11, RX 12, CSn 9; FD2 13, FD3 7 for quad mode by PIO),
  I2C1 SDA 14 / SCL 31, UART0 TX 32 / RX 33, EXT_FAULT GPIO34.
- Monitors: MON_1V8 reads +1V8 (VCCAUX, after FB1); ADC6/ADC7 (GPIO46/47)
  read VCCIO_1 and VCCIO_2. +1V2_MGT is the one unmeasured rail.
Open for the owner: U34, the 27 ohm pair, Q3's new role, the input
capacitors and the monitor parts sit in the import band; island them with
islands.py (U34 has no datasheet layout example beyond "short wide traces,
vias under IN/OUT", SLVSEA3F 12.1). Firmware: VBUS5_ST, PD_REQ_9V, new pins.

## Audit corrections, part 2: memory power-up and the PIN V switches 2026-10-29
Parts: 544 (was 516); roles 544/544; ERC 0 errors, 2 allowlisted warnings;
DRC 4 errors (J1 holes), 0 parity; nothing moved: 0 of 516 common
footprints; 28 new footprints staged, U23/U24 swapped in place (their island
groups kept), R76/R77 removed.
Findings items 39 and 41.
What:
- PUDC_B is strapped high (1 k to +3V3, UG470 Table 2-4): no configuration
  pull-ups. Every line that needs a level has its own resistor already
  (SDRAM CS/CKE, MRAM, microSD, 5 V bus OE, PHY reset); the PSRAMs get
  theirs: per chip CE# 10k up to +1V8_IO, SCK and IO0-3 10k down, on the
  _MEM side of the 33 ohm resistors (APS6404L rev 4.0 section 8: CE# tracks
  VDD, clock and data low until 150 us after VDD, then reset-enable/reset).
  The memory controller must implement the wait and the reset pair.
- U23/U24 are TI TPS22953DSQR (SLVSCT5D): BIAS from +3V3, input 0.7 V to
  VBIAS, so the 1.8 V setting of J19/J20 is inside the switch's rating
  (the TPS22950 needed 1.8 V minimum). Reverse blocking while off, CT 1 nF
  (about 1.5 ms rise), SNS tied to OUT, PG open, 100 nF BIAS and 1 uF OUT
  bypass. No programmable current limit: the 500 mA PINV PTC per slot is
  the overload protection. U21/U22 stay TPS22950C.
Open for the owner: 28 staged footprints to island (PSRAM pulls belong at
U2-U5, the TPS22953 parts at U23/U24; profiles added to island_profiles.yaml).

## Audit corrections, part 3: tools 2026-10-29
Parts: 544; roles 544/544; ERC 0 errors, 2 allowlisted warnings; DRC **0
errors** (was 4), 295 warnings, 0 parity; nothing moved: 0 of 544 common
footprints (J1's footprint swapped in place, its island group kept).
Findings items 40, 44, 46, 47, 49, 51.
What:
- gate.py prints two verdicts, `GATE electrical` and `GATE mechanical`
  (place.py --check), and no longer says PASS over a failed lattice check.
  Exit code follows the electrical gate; `--strict` adds the mechanical one.
  Today: electrical PASS, mechanical FAIL (14 lattice findings, phase B3).
- islands.py: when a series part reaches two anchors, the anchor its
  design.py group names wins (then hops, then distance). Groups renamed so
  the source resistors follow their drivers: `U1 PSRAM{0-3} series
  termination` (R104-R127), `U1 SDRAM clock source` (R151), `X4 system
  clock` (R147, C246). Dry runs confirm: the U2 island now reports R104-R109
  as U1's, the U1 island reports R147 as X4's. The board's KiCad groups still
  hold R104-R127 in islands U2-U5 and R151 in U32; moving them is an apply:
  `islands.py --anchor U1 --extend --with R104,...,R127,R151` after review.
- city.py: the L/M keys are MK76/MK77 (design.py MK{ord(slot)}), not
  MK71/MK72; an off-board key post is planned at position 1 of its own power
  row (one pitch before pin 1, place.py's rule) when that row is on the
  board, so MK71 goes to J56 and MK72 to J65. MK76/MK77 sit on the board at
  the old bottom bus position while J7/J8 are planned at the top: the plan
  prints a NOTE; they are hand placement and were not moved. Plan
  regenerated (ref/city/plan.yaml), not applied in this commit.
- J1: odin copy of KiCad's HCTL USB-C footprint with A1/A12/B1/B12 shortened
  to 0.6 x 1.15 mm on the locating-hole side (0.31 mm hole-to-copper; rule
  0.25, JLC NPTH-to-track 0.20). [verify] against the HCTL drawing, which
  LCSC serves only through a browser.
- budget.py: per-regulator output capacitance against what each datasheet
  validated (U12 221 uF, U13 103 uF, U14 113 uF, U15 507 uF, U16 50 uF are
  beyond: bench qualification, not a build error); inductor peak current
  per rail against Isat (all pass, worst U12 2.86 of 6.8 A); an input
  envelope by mode (recovery / light / full) per source profile with the
  U26 and U34 limits. Checked contract: recovery and light fit a 9 V PD
  contract, full export fits J50 only (2.05 A against U26's 1.7 A minimum
  on PD). All in ref/power-budget.md.

## City plan applied: G/H keys at their rows 2026-10-29
Parts: 544; ERC 0 errors; DRC 0 errors, 0 parity. `check_positions.py`:
254 of 544 moved, every one of them outside the outline before and after
(the 66 hand-placed footprints untouched). Gate electrical PASS, mechanical
FAIL (unchanged: B3 open).
The corrected plan (part 3) applied with `islands.py --city --apply`: MK71
and MK72 now stand at position 1 of J56 and J65 in the sketch (the plan's
`why` text lost its colon, which broke the YAML flow mapping). MK76/MK77
remain where the owner put them, with the plan's NOTE. The 53 footprints
staged by parts 1-3 are not in any island yet and did not move.

## Audit corrections, part 4: documents 2026-10-29
Parts: 544; gate electrical PASS, mechanical FAIL (B3 open); no netlist or
board change. Findings items 43, 45, 48, plus the status table for 34-51
appended to findings.md and the audit's evidence file
ref/board-review/audit-2026-10-29.json committed.
What: user-manual.md (ground columns 3 and 6, post + 1x7 power row, one
2x32 body per edge, slots left/right and buses on top, AUX instead of the
per-slot selectors, 9-21 V input, 5 V default / 9 V on request, no slave
serial), floorplan.md (current plan header, microSD access from above with
a cut-out contract, top-edge network section marked historical, R104-R127
ownership), network.md (PHY controls on bank 35), decoupling.md (voltage
groups), supervisor-flash.md (start-up order without enables, MultiBoot and
address-mode cautions), psram.md (power-up states section), power.md,
power-input.md, extension-ux.md (U23/U24, MON_VCCIO), island-layouts.md
(U34, U23/U24 rows), status-leds.md, gameboy-extension.md,
jlcpcb-import-checklist.md, kicad/README.md.

## Islands placed and the city re-applied (owner's go-ahead) 2026-10-29
Parts: 544; roles 544/544; ERC 0 errors; DRC 10 errors (all
courtyards_overlap: each of the four key posts against its neighbouring
rows and one hand-placed capacitor), 0 parity; parity and netlist
unchanged. Gate electrical PASS; mechanical: slots G, H, L, M pass, A-F
still fail (the owner's hand-placed posts sit 2.8 mm beside their rows).
What, one commit per island, each render reviewed:
- New islands: X4 (R147, C246), U34 (profile TPS2121: dividers, SS, ILIM,
  bulk), Q3 (--with R172 R173), U8 and Y1 (U7's satellites, which the U7
  extension had dropped out of the merged group; lesson recorded).
- Extended: U11/U13/U14/U16 (input capacitors on the VIN flank), U7 (27 ohm
  pair, PIN V monitors), U2-U5 (six 10k each), U23/U24 (profile TPS22953:
  BIAS and CT at their pins, OUT bypass), U1 (--extend: R104-R127 and R151
  laid out at the FPGA escape on the N/W/E sides; R151 reclaimed out of
  island U32, islands.py lock_state/marker_edits).
- City: plan regenerated and applied (430 footprints moved, none that was
  inside the outline except the two posts below). MK71/MK72 moved from the
  lot onto the board at position 1 of J56/J65 (120.90, 73.14) and (121.00,
  93.34), their island markers dropped; MK76/MK77 left the old bottom bus
  position and joined the J57/J58 blocks at the top edge, one pitch before
  pin 1. The first apply corrupted the file (the marker group deleted
  twice); restored from git, fixed, re-applied.
Open: the ten courtyard overlaps are the zero-gap contract (17.78 mm socket
+ 2.54 mm post per 20.32 mm zone leaves no courtyard margin): decide on a
documented exception for the posts or a wider zone; the A-F posts; the city
compaction; routing.

## City re-applied: the satellites back with their chips 2026-10-29
Owner's question: why are X4, U8 and Y1 not in the city. Cause: the key-post
loop added to city.py that morning was inserted in front of the loop that
writes the satellite lines, which pushed that loop inside the new one, so
no `merge_into` line was written for X4, U8 or Y1 and the three islands
stayed in the lot. Fixed (the satellite loop is back inside the per-block
loop), plan regenerated and applied: 311 footprints moved, none that was
inside the outline. X4 is in island U1 on its north side at the SYS_CLK
ball, U8 (west) and Y1 (south) in island U7. DRC unchanged: 10 courtyard
overlaps at the key posts, 0 parity. Gate electrical PASS.

## Re-audit corrections, part 1: schematic 2026-10-29
Parts: 553 (+9: Q6, Q7, D24, R200-R203, C279, C280); roles 553/553; ERC 0
errors; netlist, XDC and guide in step; DRC 10 courtyard errors (unchanged,
the key posts), 0 parity; load_pcb moved nothing, staged the nine new
footprints. Gate electrical PASS; mechanical FAIL (unchanged).
What (findings Part IV, items 52-57; the independent re-audit against
9dd5fa8, evidence in ref/board-review/reaudit-2026-10-29.json):
- 52/53, U34 selection by intent: Q6 pulls PR1 to ground while PD_REQ_9V
  is high and, through D24 into 470k/10 uF, for 2.4-7.2 s after it falls,
  so the +5V rail is on U11 before the charger moves VBUS and until it is
  back at 5 V (Table 9-3, PR1 < VREF with CP2 high selects IN2). Q7 pulls
  PR1 to ground while VIN_EXT carries more than 3.2-6 V (100k/33k), so a
  powered J50 carries the whole board with a USB cable attached. OV1 stays
  at 5.63 V typical (5.26-5.96 V worst case, now computed and checked in
  design.py against the 6 V TLV62569 absolute maximum and the 5.25 V USB
  2.0 port) as a backstop only. During a negotiation the rail is U11 in
  dropout, about 4.5 V. No comparator threshold can separate vSafe5V's
  5.5 V from the TLV62569's 5.5 V, so none is asked to.
- 54: R203, 4.7k from FLASH_CS_B to +3V3 (UG470 Table 2-4; W25Q256JV CS
  follows VCC); the controller's reset pull-down through R22 leaves it high.
- 56: U23/U24 PG tied to ground (SLVSCT5D 9.3.3); the symbol pin typed
  passive so ERC does not call the tie a driver conflict. Fault coverage
  stated plainly in extension-ux.md and power-input.md: no report, no
  aggregate limit, automatic restart after an output undervoltage; bench.
- 57: C280, 1 uF at U34 IN2 (SLVSEA3F 11); the 3 x 22 uF at U11 stay the
  bulk, and city.py now pulls U11 -> U34 (6) and U34 -> U15 (4) instead of
  U11 -> U15 directly; U34 -> J1 (2).
- 58: city.py attach() takes the deciding net (X4: SYS_CLK, not the +3V3
  pads), RESEAT lists X4, R147 and C246; city.py snaps the inboard L/M rows
  (J57/J58) to the edge rows' 2.54 mm lattice. Applied in part 2.
- 55: no hardware change. CH224K exposes no contract data (the CH224A/Q I2C
  status register is not on the K; the A is pin-compatible but its I2C
  mode is the single-resistor mode, in which register 0x0A can request up
  to 28 V, which would give up the 9 V ceiling by construction). Policy in
  budget.py: any 5 V source is a 500 mA port unless user-declared; a
  granted 9 V request is a 15 W guarantee (PD power rules [verify]);
  J50 is detected on MON_VSYS. The alternative, two dual comparators on
  the CC lines into four spare GPIOs, is recorded as the hardware option.
- budget.py: each path checked against its own limiter (U34, U26) and the
  sum against the source; inductor peaks at the 21 V / 5.5 V envelope with
  L at -20 % (all pass); LOADS carry a recovery column (standby or reset
  currents, never zero for a powered part; U33 MRAM added): recovery is
  0.21 A at 4.75 V, inside a 500 mA port, above the 100 mA an unconfigured
  USB 2.0 device may draw, stated as open, not met.
- Documents: user-manual.md (jacks on the bottom edge, no full export on
  PD, what the controller can know about a port, the brief 5 V dip),
  power-input.md, power.md, extension-ux.md, island-layouts.md,
  floorplan.md (X4 left, U34 junction), supervisor-flash.md (FCS_B).
Open after this part: item 40 COUT qualification, item 34 DS181 ramp and
power-down waveforms, the U23/U24 shorted-branch test, the pre-enumeration
current, the J1 land pattern against the HCTL drawing.

## Re-audit corrections, part 2: islands and the city 2026-10-29
Parts: 553; ERC 0; DRC 8 courtyard errors (was 10: MK76/C143 and
MK77/C145 cleared; the remaining pairs are the six post-to-header zero-gap
pairs and the owner's C159/C161 beside MK71/MK72), 0 parity; mechanical 9
findings (was 10: J7/J57/MK76 now on the lattice). Gate electrical PASS.
What, one commit per island, each dry run reviewed:
- Q6 (--without Q7: Q is not an anchor family, so the two transistors
  pulled each other in) and Q7 (--without Q6), own design groups "Q6  mux
  hold: 9 V request" and "Q7  mux hold: screw input present".
- U34 re-applied twice: with C280 (IN2 bypass), then with a profile rule
  "IN2 bypass" so the 1 uF is innermost at pin 2 and the 22 uF beside it.
- J57 and J58 re-applied with the XFCN profile change: PIN V fuse and 10 uF
  on the inboard row with the AUX fuse. The posts MK76/MK77 are an anchor
  family and did not move with the chunk; the apply drops them from the
  group and the city merges them back at position 1 (POST_WITH_ROW).
- U23 and U24 re-applied: CT 1.43 mm and BIAS 1.60 mm pin to pad.
- City, applied twice (bb9ab7f, then the final plan): door row U16, U15,
  U14, U34 with U11 wired against the mux. U11 inside the row was tried at
  both ends: right end pushed U26 off J1, left end pushed PSRAM U2 off the
  bank-13 side (the first apply had that defect; corrected in the second).
  Q6/Q7 are satellites of U34 on PR1 (city.py stacks same-side satellites
  outward). SATELLITES net for X4; RESEAT with C246; the inboard L/M rows
  snapped to the lattice. 488 footprints moved as rigid groups, none inside
  the outline except MK76/MK77 (1.4 mm, with their rows). X4 west of U1 at
  the SYS_CLK row (R147 pad to M21 22.7 mm staged, was 31.6 north);
  U11 -> U34 45 mm (was 111), U34 -> U15 40 (was 94), U34 -> U14 23,
  U34 -> U26 18, staged at 2.2x.
Open: see the Part IV status table in findings.md.

## City re-planned: districts, the owner's seven points 2026-10-29
Parts: 553; ERC 0; DRC 8 courtyard errors (unchanged: the six post-to-
header zero-gap pairs and the owner's C159/C161 beside MK71/MK72), 0
parity; mechanical 9 findings (unchanged). Gate electrical PASS. 450
footprints moved as rigid island groups, all in the staging city (2.2x
frame beside the sheet), nothing inside the outline.
The owner moved the islands by hand in the city (JTAG far bottom-left,
every cable jack on the bottom edge, USB-C alone on top, the PSRAMs in
one column, the LEDs and the PIN V jumpers at the bottom-right) and asked
for seven things. tools/city.py variant `districts` (now the default)
encodes that arrangement as rules instead of coordinates, so a re-plan
reproduces it: each district block is set against a neighbour already
placed (x: right_of/left_of/left/right/centre REF; y: above/below/top/
bottom/centre REF), after the edge rows and the door; `rows` merges cells
into a host island at a fixed pitch; `boxes` draws a dashed, named box
round each finished district in the city frame.
1. LED dashboard: D9, D10, D11 merged into island D1 as cells at 5 mm
   pitch, LED centres on one line, the block right-aligned above the AUX
   terminal in the bottom-right corner. tools/stencil.py writes the
   silkscreen labels (DONE, CTRL HB, USER 1, USER 2 from
   status-leds.md) as user texts inside the LED footprints, 0.8 mm /
   0.15 mm stroke, one baseline 0.9 mm under the parts; it moves no
   footprint (check_positions 0 moved) and reruns idempotently.
2. PSRAM: four identical cells in a 2 x 2 block against the FPGA's left,
   top-aligned with its island: PSRAM0/1 series resistors sit on the north
   flank of U1, PSRAM2/3 on the west flank, so the block's top row serves
   the first pair and the bottom row the second; the longest chip-to-
   resistor run is shorter than in the 62 mm column.
3. Jumpers as a control corner: J19 with U23 on top in the service corner
   (bottom-left, with J2, U20, J52), J20 with U24 on top as its mirror
   above the HDMI jack (bottom-right). The two PIN V jumpers are not
   side by side: each selects a bank supply (VCCIO_1 at the FPGA's
   bottom-left, VCCIO_2 at its right) and feeds a fused rail up its own
   slot column; one centre would drag a 2 A rail across the board.
4. USB story in one place: J1 on the top edge, U26 straight under it, U18
   beside the eFuse, U34 closing the door row, U11 and U12 (the two
   identical VSYS converters) side by side under U26 against the mux.
   They stay separate islands because each IC's passives follow its own
   datasheet figure; the district box "USB POWER IN" shows them as one.
5. Serial memory shelf: U6 and U33 continue the door row leftwards (both
   SPI, 4-6 lines, both leaving the FPGA's left half). The SDRAM U32
   stays under the FPGA where its 38 lines leave (its balls are in the
   package's lower half): it is the widest, fastest bus on the board and
   does not travel to the flash.
6. Regulators in rows: the door row U16, U15, U14, U34 against the FPGA's
   top edge, then U11 and U12 one step below its right end. U13 (2.5 V)
   sits beside the PHY, its load, under the FPGA (district entry, no
   longer a bottom door; the two overlapped when both were rules).
7. JTAG together: J2 standing at the far bottom-left one row in, above
   the LINK P jack, U20 beside it, J52 on top. Not on the edge: at real
   size the bottom edge is 89.6 mm (the slot rows end at y 82-85 at both
   corners, a jack 18-21 mm deep starts at x 10.4) and the five cable
   jacks take 80.1 mm (J71 17.0, J72 17.0, J70 17.6, J73 18.5, J68 10.0);
   the 8.8 mm header fits only with the AUX terminal turned onto the
   right edge at 0.5 mm gaps. The microSD (16.7 mm) does not fit on the
   edge either (finding unchanged) and stays inboard, pulled by its bank
   lines (it landed above the service corner, left of the PSRAM block).
Wiring solver left in charge of: J51, J74, Q3, SW1, U7, U9, U10, U17,
U21, U22, U32. Plan refusals met on the way (each printed with both
boxes, now part of the message): U34/U11, U26/U11, U30/U13, J73/D1 (the
LED islands' title bars made four boxes too wide for a row: hence
`rows`). The pre-existing L1/R8 0.18 mm clearance pair inside island U7
is in the committed board too (kicad-cli --severity-error lists it; the
gate's DRC summary counts courtyards only).
Open: SW1 (BOOT button) landed by the solver at the door's top, 35 mm
staged from U7's flash; the bottom-edge budget above is the first thing
to settle when compacting to 1:1; check "CTRL HB" against its 5 mm cell
in KiCad (about 4.5 mm at 0.8 mm).

## Slot strips turned inside out: power parts between the edge and the rail header 2026-10-30
Parts: 553; ERC 0; DRC 8 courtyard errors (unchanged pairs), 0 parity;
mechanical 9 findings (unchanged set, new numbers). Gate electrical PASS.
The owner wants the slot power parts (the XFCN power headers, the fuses,
the 10 uF/100 nF pairs and the posts) on the other side of each 2x32 IO
rail header: between the board edge and the header, the header inboard.
KiCad cannot mirror a footprint (Flip changes side, Mirror skips
footprints), so tools/islands.py gained `--mirror REF,...`: the listed
hand-placed parts have their positions mirrored across the strip's own
vertical centre line, the strip keeps its box and edge margin (0.52 mm),
rotations are kept. Pads symmetric about the part's own vertical axis
(one-row headers, posts, two-pad parts along y) mirror exactly; a two-pad
row along x (the 1.1 A fuses) is given a half turn, which is its exact
mirror, pad numbers included; the 2x32 header only moves (pin 1 stays on
its own corner) and the report says so. Dry run, render, --apply with
write verification and DRC, one strip per commit, like any island.
A-D strip (J3 island, 33 parts, line x 40.275): J3 from x 33.00 to 47.55,
the power headers from 39.10 to 41.45, posts from 41.90 to 38.65, the
1.1 A fuses from 46.80 to 33.75 turned 180. check_positions: 33 moved,
nothing else. Render ref/islands/J3-mirror.svg.
E-H strip (J5 island, 33 parts, line x 119.475, next commit): J5 from
x 127.00 to 111.95, the power headers from 120.9/121.0 to 118.05/117.95,
posts from 118.0/117.7/120.9/121.0 to 120.95/121.25/118.05/117.95, the
1.1 A fuses from 113.2/112.7 to 125.75/126.25 turned 180. check_positions
against the snapshot taken before both strips: 66 moved, nothing else;
DRC pairs identical to the committed board. Render
ref/islands/J5-mirror.svg.
place.py --check still fails its 9 lattice findings (the rows were off
the lattice before the move; the strips' x values changed, the set did
not): the shield lattice contract is to be settled when the strips are
compacted to 1:1.

## Slot strips on the keyed lattice 2026-10-30
Parts: 553; ERC 0; 0 parity; DRC courtyard errors are the post-to-header
corner touches only (see below). Gate electrical PASS.
The owner's hand placement of the A-D strip, snapped to the 2.54 mm
lattice of the rail header and written as a rule, `islands.py --strip`
(tool, dry run, render, --apply, one strip per commit):
- power header line two pitches inside the rail's inner row, its seven
  pins on columns 1..7 of the slot's eight-column section (pin 1, PIN V,
  on the IO0 column);
- key post MK<ord(slot)> on column 8, one more pitch toward the edge, so
  it is off the header's line: a plain 1x8 strip cannot mate it, the
  shield needs the bare hole exactly there (the owner's keying; the
  in-line position-1 scheme written in tools/placement.py, place.py
  --check and ref/extension-ux.md is superseded and still to be rewritten,
  so the mechanical gate keeps reporting it);
- AUX fuse on the edge side of the header body, tucked above the post;
- the slot's caps and 1206 fuses in one stack midway between header body
  and rail body, 0.3 mm apart, pin order from the top, centred on the
  header body (18.79 mm on an 18.33 mm body), nothing in a header
  courtyard.
A-D (J3 at the owner's 54.47, 78.86): header line x 48.12, posts 45.58,
AUX fuses 43.32, stack 50.70; 32 footprints moved. MK66 (slot B) and MK69
(slot E) traded places, refs follow design.py. The post courtyard touches
the header courtyards at a corner (0.27 x 0.55 mm, own header and the next
section's): courtyard-only, the known post-to-header pair.
E-H (next commit): J5 kept at x 111.95, moved to y 78.86 so its 32
columns are J3's (a shield must bridge them); header line 118.30, posts
120.84, AUX fuses 123.10, stack 115.72, edge margin 3.68 mm.
