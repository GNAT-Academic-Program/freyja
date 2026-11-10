# Current KiCad workflow

This is the detailed contributor and agent workflow for Freyja. The hardware
is **FREYA HW 0.1.0-proto.1**, from `tools/identity.py`; `odin` remains the
KiCad basename and a library namespace. Run commands from the repository root
with Python 3, KiCad CLI/pcbnew 9 and PyYAML. Checked with KiCad 9.0.8.

## Read first

Read [README](../README.md), [the project map](../kicad/README.md), and the
current section of [findings](../findings.md). For layout, also read
[floorplan](../floorplan.md), [decoupling](decoupling.md),
[island layout rationale](island-layouts.md) and [impedance](pcb-impedance.md).
Consult the relevant subsystem references and qualified-parts table.
Dated findings and everything in [the archive](../archive/README.md) describe
earlier revisions; their instructions and counts do not govern current work.

## Ownership

| Concern | Owner and derivation |
|---|---|
| Identity | `tools/identity.py`, matching the board's FREYA version stamp. |
| Circuit, parts, connectivity | `tools/design.py` (`build()`), with `qualified.py` for part/package qualification, `budget.py` for loads/ratings, `roles.py` for descriptions, and FPGA rail/configuration policy imported from `tools/gen_sch.py`. |
| FPGA allocation | `tools/alloc.py` (`assign()`), reading the imported FGG676 symbol. `ballmap.py` and `gen_xdc.py` derive the ball table, XDC and gate top. |
| Placement, routing, outline, zones, mounting-hole positions | **`kicad/odin.kicad_pcb`**. Preserve manual layout. `tools/placement.py`, its lock/profile YAML, floorplan, city plans and island SVGs describe intent/checks; they cannot replace the live board. |
| Libraries | Project `sym-lib-table` / `fp-lib-table` select `kicad/odin.kicad_sym`, `kicad/odin.pretty/`, `easyeda/EasyEDA.kicad_sym` and `easyeda/EasyEDA.pretty/`. `easyeda/EasyEDA.3dshapes/` has live model consumers. System KiCad libraries are also required. |
| Stackup and rules | Live stackup/layers in the PCB, net classes/settings in `.kicad_pro`, custom DRC in `.kicad_dru`; `tools/gen_pcb.py` owns generated portions. Stackup/impedance JSON and [impedance](pcb-impedance.md) record the engineering basis. |
| Derived outputs | `gen_project.py` writes the root schematic and seven sheets; KiCad exports `odin.net`. Reference tables/constraints have the generators below. Regeneration is an intentional write operation. |

**`EasyEDA:` identifiers remain active imported project dependencies.**
`alloc.py`, `symlib.py`, `gen_kicad.py`, `load_pcb.py` and the library tables
consume them. Do not replace qualified footprints with stock parts or rename
the namespace as cleanup. The small `kicad/EasyEDA.*` copies remain in place;
the project tables select the `easyeda/` versions.

## One bounded change

1. Record `git rev-parse HEAD`; inspect `git status --short --ignored`,
   `git diff` and `git diff --cached`. Preserve existing work; do not reset,
   stash, discard or commit unrelated changes. Identify intended files.
   Record SHA-256 hashes of the PCB, schematics, netlist, project settings,
   rules and all project libraries/models when hardware must be preserved.
   Keep manifests/reports in a fresh `/tmp` directory. Preserve editor locks,
   autosaves and backups.
2. Change the owning source or requested documentation only. Documentation
   cleanup permits no moves, connectivity/footprint changes, routing, zone
   fills or manufacturing-rule changes. For an intended layout-preserving
   electrical sync, first use `tools/check_positions.py --snapshot
   /tmp/<run>/before.json`; review additions/removals/replacements explicitly.
3. Run applicable checks below; distinguish pre-existing failures from new
   failures. Do not suppress findings, relax checks or regenerate the board
   to obtain a pass.
4. Review the complete diff and compare protected hashes. For a permitted
   PCB sync, also inspect copper, zones, locks, footprint geometry and nets.
   `check_positions.py --compare /tmp/<run>/before.json` checks common
   references' x/y/rotation/side and lists additions/removals; it does not
   certify routing or locks.
5. Report the change, checks/results, preservation evidence and next unresolved
   issue. Update existing current status when needed. Commit/push only when
   requested; avoid a new overlapping audit document for routine work.

## Checks that do not write hardware

```sh
python3 tools/alloc.py --check
python3 tools/gate.py --strict
python3 tools/check_stackup.py
python3 tools/audit_easyeda.py
python3 tools/check_connector_rework.py
git diff --check
```

`gate.py` runs circuit/budget/qualification checks and the stackup check, compares a temporary
netlist export, XDC/gate top and parts guide, checks exact ERC and DRC with
schematic parity, verifies the connector placement contract, and reports
escape depth. `--strict` also gates mechanical failures. **DRC violations and
unrouted items are reported, not gated**: a passing gate is not a fabrication
pass. Read the DRC report. For persistent output, use an existing scratch dir:

```sh
kicad-cli pcb drc --schematic-parity --severity-all --format json \
  --exit-code-violations -o /tmp/<run>/drc.json kicad/odin.kicad_pcb
```

This deliberately returns nonzero while violations remain. Standalone
`python3 tools/check_erc.py` requires zero errors and exactly two
`global_label_dangling` warnings, `FPGA_DXP` and `FPGA_DXN`; there is no U20
blanket exemption. [Current findings](../findings.md) records measured results
and known independent checker failures. Use the Python interpreter with the
installed pcbnew bindings.

For allocation/gateware changes, separately run
`vivado -mode batch -nojournal -nolog -source gateware/gate/run.tcl` after
loading your installed Vivado environment. It writes ignored
`gateware/gate/build/` products and may create `.Xil/` / `clockInfo.txt` in its
working directory. This longer allocation check is outside `gate.py` and does
not check PCB routing. Regeneration is not needed merely to run it.

## Commands that overwrite files

Use only writers needed for the intended source change. This is a write map,
not a routine command sequence. All Python scripts below are under `tools/`.

| Command | Writes / limits |
|---|---|
| `gen_kicad.py` | **Rewrites imported source symbol pin types** in `easyeda/EasyEDA.kicad_sym`; writes generated `kicad/odin.kicad_sym` and custom footprints. Validates the imported FPGA footprint rather than replacing it. |
| `gen_project.py` | Replaces root and seven block schematics from circuit/library sources. Manual schematic arrangements are lost. Does not export the netlist or synchronize the PCB. |
| `kicad-cli sch export netlist --format kicadsexpr -o kicad/odin.net kicad/odin.kicad_sch` | Replaces the tracked netlist. Export to `/tmp/<run>/odin.net` for inspection instead; the gate ignores date/tool metadata when comparing. |
| `load_pcb.py` | **Saves the PCB**, then runs `update_silkscreen.py`, which saves it again. Reads `kicad/odin.net`: export the intended schematic first. Retains common origins/rotation/side/locks, stages new parts, removes absent schematic references except board-only items, may replace footprints, and reassigns pad nets. Routed copper correctness is not certified. |
| `gen_pcb.py --rules-only` | Replaces PCB **stackup and layer-list blocks**, merges generated net classes/default minima into `.kicad_pro`, and replaces `.kicad_dru`. Preserves other PCB text but changes manufacturing constraints and may overwrite manual rule edits. Use only for an intended rules change; inspect implementation and diff. |
| `gen_xdc.py` | Replaces `ref/freya.xdc` and `gateware/gate/top.v` from allocation; does not write `gateware/gate/gate.xdc`. |
| `ballmap.py --write`, `budget.py --write`, `qualified.py --write`, `roles.py --write`, `bom_jlc.py --write` | Replace `ref/ballmap.md`, `power-budget.md`, `qualified-parts.md`, `parts-guide.md`, `bom-jlcpcb.csv`, respectively. Without `--write` these tools report/check without replacing those files. |

**Never run `tools/gen_pcb.py` without `--rules-only` on an existing board.**
Its default emits an empty board, destroying placement, routing and zones.

`gen_sch.py` stays because `design.py` imports its FPGA policy, but its
executable mode is an older **FPGA-only schematic writer** that overwrites
the root schematic. Do not use it for project regeneration.

`place.py` without `--check`, especially `--stage`, moves footprints and saves
the board. `islands.py --apply`, `split_strip.py --apply` and
`stencil.py --apply` also write the board; `update_silkscreen.py` always saves
it. These are not cleanup or validation commands. Dry-run islands can write
preview SVGs: direct them to `/tmp` with `--render`. `city.py` writes planning
YAML/SVG and `floorplan.py` writes an SVG; neither snapshots manual layout.
Inspect any other script before describing it as safe or running it live.

## Recurring cleanup checkpoint

After several routing chunks or a substantive design change:

- Inspect staged and unstaged diffs for unintended changes.
- Update existing current status; close or revise affected tasks.
- Reconcile instructions whose assumptions changed.
- Check stale links, competing active documents and temporary outputs;
  keep transient verification outside the tracked project and label history.
- Run checks appropriate to changed files; report remaining findings.
- Confirm required placement/routing preservation with opening hashes,
  snapshots and the actual copper diff.

Keep reports short; reuse this workflow and `findings.md`.
