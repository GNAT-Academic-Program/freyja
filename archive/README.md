# Historical archive — not the active design

These files preserve provenance, engineering decisions and evidence. Their
instructions and task lists are superseded. Follow the
[current KiCad workflow](../ref/ide-agent-prompt.md) and open
[`kicad/odin.kicad_pro`](../kicad/odin.kicad_pro) for current work.

Organized on 2026-11-03 from starting commit
`3f76447e95960261cd3486e88a7cd382be51181f`. The working tree was clean;
ignored editor backups, Python caches and the Vivado build directory were
left in place. The editor lock disappeared during the session and the local
`.prl` active-layer preference changed; these were not restored over current
editor state. No active hardware or library files were relocated.

| Original location | Archive location | Reason / provenance |
|---|---|---|
| `Odin_V1.0.0/` | [legacy-odin/Odin_V1.0.0/](legacy-odin/Odin_V1.0.0/) | Altium exports used in the early migration. The schdocs and PCB export describe different earlier design states; neither is current KiCad authority. |
| Root `BOM_Odin_V1.0.0_Odin_0_2026-09-02.xlsx` and `Netlist_Odin_0_2026-09-02.net` | [legacy-odin/](legacy-odin/) | Old export inputs, consumed only by the historical extractor; the live netlist is `kicad/odin.net`. |
| Root `odin.parts.ir`, `odin.nets.ir`, `odin.desigmap`, `odin.bomdiff`, `odin.srcdiff` | [legacy-odin/](legacy-odin/) | Migration reports derived from those inputs; no active generator reads them. |
| Root `extract.py` | [legacy-odin/extract.py](legacy-odin/extract.py) | Migration-only parser. Its data and outputs remain adjacent. It now resolves paths relative to itself and runs only as a script; use a disposable copy to reproduce historical outputs. It is not a KiCad regeneration step. |
| `ref/ide-agent-prompt.md` (old text) | [history/ide-agent-prompt-legacy.md](history/ide-agent-prompt-legacy.md) | Superseded EasyEDA review brief. A new current workflow occupies the original path. |
| `ref/rev-a-plan.md` | [history/rev-a-plan.md](history/rev-a-plan.md) | Dated rebased implementation plan with useful rationale; completed/superseded phase instructions are not a current task list. |
| `ref/rev-a-report.md` | [history/rev-a-report.md](history/rev-a-report.md) | Chronological phase evidence through 2026-11-03. Counts describe the revisions of each entry. |
| `ref/kicad-validation.md` | [history/kicad-validation.md](history/kicad-validation.md) | Earlier synchronization/ERC/DRC history, including the former six-layer/SFP design. |
| `ref/board-review/` | [history/board-review/](history/board-review/) | Exported SVG/DRC/source hashes and 2026-10-29 audit JSON. The README says 2026-09-15 while some filenames say 2026-10-29; those original dates are retained, not reconciled into a current result. |
| Root `.Xil/` and `clockInfo.txt` | [vivado-2026-10-29/](vivado-2026-10-29/) | Vivado-generated scratch outputs with dated host/source metadata. The live constraints remain `ref/freya.xdc` and `gateware/gate/gate.xdc`; no active script reads these archived copies. |

Historical prose may retain original repository paths to identify what
changed at the time; use this table to locate relocated material. Broken
references to the former SFP-specific pages in the findings have been labelled
as removed history; those pages were already absent at the starting commit.

The imported libraries under **[`easyeda/`](../easyeda/)** are deliberately
**not archived**: library tables, allocation, generation, PCB loading and
the live board consume them. `tools/gen_sch.py` is also retained because
`design.py` imports its FPGA rail/configuration policy. City/island planning
assets and supporting electrical/mechanical references remain in place for
their consumers; the live PCB owns actual placement.
