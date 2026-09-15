# Board review snapshot

Exported 2026-09-15 with KiCad 9.0.8 from the current working-tree board.
This commit records review artifacts; the source hashes in
[board-state.json](board-state.json) identify the exact uncommitted source
state used for export.

- **498 footprints.** Placement is incomplete: 494 footprint origins are
  outside the outline's 100 × 100 mm bounding box (X/Y 30–130 mm).
- **6 copper layers**, in both `odin.kicad_pcb` setup/stackup and
  `tools/gen_pcb.py`: F.Cu / In1.Cu / In2.Cu / In3.Cu / In4.Cu / B.Cu.
  KiCad's loaded copper-layer count also equals 6.
- DRC with **all severities, including exclusions**, plus schematic parity:
  **693 violations, 499 unconnected items, 2 parity issues**. Command exit
  status is 0; this does not mean the board passes fabrication DRC.

## Exports

- [Full DRC report](odin-drc.rpt)
- [DRC command and complete console output](drc-console.txt)
- [Current board SVG: F.Cu + Edge.Cuts + F.CrtYd](odin-placed.svg)
- [SVG command and console output](svg-console.txt)
- [Counts, layer comparison and source SHA-256 hashes](board-state.json)

The SVG includes all staged components outside the outline, rather than
cropping them from the review. No component was moved for this export.

SVG export trailing whitespace was removed; geometry is unchanged.
