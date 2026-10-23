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
