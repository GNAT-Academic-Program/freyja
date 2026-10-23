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
bank 13; banks 13, 14 and 16 depth sorted (15 and 34 are full and keep
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
(`SYS_CLK`), allocated before the PSRAM pairs; `alloc.py --check` verifies
the MRCC placement. One more deep ball results (the shallow MRCC pair went
to the clock). floorplan.md rewritten for the rev A board (jacks, network
strip, decoupling placement rule).
Known: oscillator current and OE behaviour are from the YXC family listing
(datasheet PDF did not download); `place.py --check` connector contract
still fails (phase B).
Open questions for the owner: 50 MHz chosen as a safe NEORV32 default; say
if you want another frequency (any 3225 CMOS part fits the same land).
