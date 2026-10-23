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
