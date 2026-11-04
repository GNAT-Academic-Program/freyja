# Freyja

An FPGA development board intended to remove the setup work between an idea
and a working project: independent memory ports, a USB board controller,
observable power rails and keyed extension connectors.

The repository is **Freyja**; the current hardware stamp is **FREYA HW
0.1.0-proto.1**, with **XC7A100T-2FGG676I + RP2350B**. Identity comes from
[`tools/identity.py`](tools/identity.py). The KiCad basename `odin` and imported
library names are retained for compatibility; they do not identify another
active project.

## Open the current project

Open **[`kicad/odin.kicad_pro`](kicad/odin.kicad_pro)** in KiCad 9.
[`kicad/odin.kicad_pcb`](kicad/odin.kicad_pcb) owns placement and routing;
[`kicad/odin.kicad_sch`](kicad/odin.kicad_sch) is the generated root schematic.
See [the project map](kicad/README.md) and the single
[current workflow](ref/ide-agent-prompt.md) before editing or regenerating.

The board is 100 × 140 mm with eight copper layers, 551 schematic components
and 555 placed footprints including four board-only mounting holes. All
assembly is on F.Cu. **Routing is unfinished.** All four PSRAM ports, their
ground connections and return stitching, the `+1V8_IO` distribution, the SDRAM,
the four HDMI pairs and the LINK escapes are on the board; counts and open issues are in
[current findings](findings.md). The gate reports DRC and unrouted items
without gating them, so a passing gate is not a fabrication pass.

Historical baseline, 2026-11-03 cleanup at `3f76447`, before any routing: zero
tracks and vias, 499 unrouted items listed, DRC zero errors and 313 warnings,
zero schematic-parity issues. Independent import/connector checks had
pre-existing failures, listed in the findings.

## Work and validate

Run from the repository root with Python 3, KiCad CLI/pcbnew 9 and PyYAML:

```sh
python3 tools/alloc.py --check
python3 tools/gate.py --strict
python3 tools/audit_easyeda.py
python3 tools/check_connector_rework.py
git diff --check
```

The gate reports DRC/unrouted counts without failing on them. Read the report
and independent checker results. [The workflow](ref/ide-agent-prompt.md)
explains exact ERC expectations, scratch DRC reports, file ownership,
generator writes and the cleanup checkpoint after several routing chunks.
Documentation cleanup must preserve hardware contents. Never use
`tools/gen_pcb.py` without `--rules-only` on the existing board.

Circuit ownership is [`tools/design.py`](tools/design.py); FPGA allocation is
[`tools/alloc.py`](tools/alloc.py). The project uses generated `odin:` libraries,
stock KiCad libraries, and **active imported `EasyEDA:` symbols, footprints and
3D models under [`easyeda/`](easyeda/)**. Preserve their identifiers and exact
qualified land patterns.

## Design intent

Four independent QSPI PSRAM links provide 32 MB without forcing a project to
start with a DDR controller; a 32 MB SDRAM provides another memory option.
The RP2350B is the board controller for configuration, power control and
readback. Eight direct extension sections and two buffered sections expose
documented signals and rails. ETH, raw LVDS LINK P/Q and HDMI are present in
the current circuit. Firmware, timing and operating performance still require
their own validation; PCB/ERC checks alone do not establish them.

For future decisions, keep the original test: **does this remove work that
was never the point, or add work that looks like the point?** Prefer explicit
limits, direct wiring and references an extension builder can understand.

## Supporting references

- [User manual](ref/user-manual.md), [extension connector contract](ref/extension-ux.md) and [worked Gameboy extension](ref/gameboy-extension.md).
- [Parts guide](ref/parts-guide.md), [qualified parts](ref/qualified-parts.md), [power budget](ref/power-budget.md), [assembly/import checklist](ref/jlcpcb-import-checklist.md) and [BOM](ref/bom-jlcpcb.csv).
- [Power input](ref/power-input.md), [power tree](ref/power.md), [PSRAM](ref/psram.md), [controller flash](ref/supervisor-flash.md), [network](ref/network.md) and [raw LVDS links](ref/link-ports.md).
- [Mechanical intent and history](floorplan.md), [FPGA decoupling](ref/decoupling.md), [island layout rationale](ref/island-layouts.md), [impedance/stackup](ref/pcb-impedance.md) and [local datasheets](ref/datasheets/).
- [SDRAM profile, 100 MHz CL3](gateware/sdram100/README.md): implementation contract, timing fixture and constraints, separate from the allocation gate.
- [Current status and chronological findings](findings.md). Its older numbered findings are dated history, not a fresh open-task list.
- [Archive index and provenance](archive/README.md): old Altium/EasyEDA exports, extraction reports, superseded workflow/plans, dated review evidence and Vivado scratch outputs. [Salvage rationale](ref/salvage-from-odin0.md) retains useful earlier engineering decisions.
