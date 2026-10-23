# Odin KiCad project

**Everything here is generated.** Do not hand-edit the `.kicad_sch` files,
`odin.kicad_sym` or `odin.pretty/` — edit the generators and re-run.

Six pages, one per functional block, from `odin.kicad_sch` (the root):

| Page | Contents |
|---|---|
| `fpga.kicad_sch` | FPGA, decoupling, configuration straps |
| `power.kicad_sch` | input, regulators, monitoring and five protected extension buses |
| `memory.kicad_sch` | PSRAM x4 and configuration flash |
| `supervisor.kicad_sch` | RP2350B, USB-C, flash, links to the FPGA |
| `slots.kicad_sch` | Nine extension slots, rail selection, fusing, shifting |
| `network.kicad_sch` | RTL8211FD-CG PHY, ETH jack, LINK P and LINK Q |

Parts are grouped: each regulator sits in a dashed box with its own inductor,
feedback divider and capacitors; each slot with its jumper and its fuses.
Rails and grounds use real power symbols, so only actual signals carry a
label. Rearranging by hand means giving up regeneration — a fair trade once
the design settles, just know that is the moment you make it.

## Regenerate

```bash
python3 tools/gen_kicad.py      # normalize imported XC7A100T symbol + validate FGG676 footprint + custom parts
python3 tools/ballmap.py --write
python3 tools/budget.py --write # rail qualification -> ref/power-budget.md
python3 tools/qualified.py --write   # part table -> ref/qualified-parts.md
python3 tools/audit_easyeda.py # imported symbol/pad/LCSC consistency
python3 tools/gen_project.py    # schematic from tools/design.py
python3 tools/gen_pcb.py --rules-only   # stackup, net classes, design rules; placement kept
kicad-cli sch export netlist --format kicadsexpr -o kicad/odin.net kicad/odin.kicad_sch
python3 tools/load_pcb.py       # sync footprints and nets into the board, placement kept
python3 tools/gen_xdc.py        # ref/freya.xdc and the Vivado gate top from tools/alloc.py
python3 tools/gate.py           # every phase check in one run (ref/rev-a-report.md numbers)
```

`load_pcb.py` reads `kicad/odin.net`, so export the netlist before running it
or you will load the previous revision's parts.

`tools/budget.py --write` currently passes and regenerates the power budget.
The input-voltage issue in findings item 20 is fixed. The command exits
non-zero if a load, input-window or inductor qualification check fails.

**`gen_pcb.py` destroys any routing.** Run it only before you start laying out;
`gen_pcb.py --rules-only` is the safe form once placement exists. `load_pcb.py`
keeps the position, rotation, side and lock of every reference already on the
board, stages new references in a band below everything else, removes
references the schematic no longer has, and refuses to save if any common
reference would move. Bracket it with `tools/check_positions.py --snapshot`
and `--compare` to prove that.

`tools/alloc.py` is the single source for ball allocation; `ref/ballmap.md` and
the schematic both come from it and cannot drift.

## Verify

The allocation is proven on the real part by a throwaway Vivado design that
uses every constrained ball (`gateware/gate/`): synthesis, place, route and
`write_bitstream` against `ref/freya.xdc`. It takes minutes, so it is not in
`gate.py`:

```bash
python3 tools/gen_xdc.py
source /tools/Xilinx/2026.1/Vivado/settings64.sh
vivado -mode batch -nojournal -nolog -source gateware/gate/run.tcl   # ends with GATE BITSTREAM OK
```

```bash
kicad-cli sch erc --severity-all -o erc.rpt odin.kicad_sch
kicad-cli pcb drc --severity-all -o drc.rpt odin.kicad_pcb
kicad-cli sch export netlist --format kicadsexpr -o odin.net odin.kicad_sch
```

```bash
kicad-cli pcb drc --schematic-parity --severity-all -o drc.rpt odin.kicad_pcb
```

## Expected ERC

Run from the repository root after regenerating the library and schematic:

```bash
python3 tools/check_erc.py
```

Expected result: **zero errors and exactly two intentional warnings**:

| Rule | Item | Reason |
|---|---|---|
| `global_label_dangling` | `FPGA_DXP` | External temperature-diode terminal is intentionally exposed only as a label. |
| `global_label_dangling` | `FPGA_DXN` | External temperature-diode terminal is intentionally exposed only as a label. |

The U20 JTAG tri-state paths currently produce **no ERC warning**: the
existing series link on TDO separates the FPGA output and bus-switch pin.
There is no U20 blanket exclusion. Any new U20 warning, or any other finding
outside the exact list above, is a regression and makes `check_erc.py` fail.
A change to the expected labels also requires updating this table and the
checker together.

`tools/gen_kicad.py` normalizes imported connector/LED pin types to passive,
models J51 SWCLK/SWDIO (pins 1/3) as bidirectional debugger connections, and
assigns the PCF8574's actual supply, input, bidirectional and open-drain pin
types. J51 ground and mechanical pins remain passive. No project-level
ERC rule is disabled and no ERC exclusion is added.

The per-phase numbers (footprints, DRC, parity, escape depth) are in
[ref/rev-a-report.md](../ref/rev-a-report.md); `python3 tools/gate.py`
reproduces them. Passing the ERC allowlist does not establish fabrication
readiness.

## Your workflow from here

1. Open `odin.kicad_pcb`. Its footprints are synchronized with the
   schematic (`tools/gate.py` proves it). The connectors follow the
   mechanical placement contract; much of the remaining circuitry is still
   staged outside the board.
2. Complete placement using `tools/placement.py` / `tools/place.py` and verify
   the result in KiCad. The latest placement and validation status is in
   [ref/kicad-validation.md](../ref/kicad-validation.md). Resolve DRC findings
   as well as placement overlaps; the current reports include electrical errors.
3. Route.
4. Fabrication outputs:
   ```bash
   jlcpcb-export -p "$PWD/odin.kicad_pcb" --autoTranslate --autoFill --excludeDNP --noBackup
   ```

## Two checks that ERC and parity cannot do

`ki_fp_filters` catches a footprint that contradicts its symbol. It does not
catch a part that is the wrong part, or one that cannot survive the voltage on
its net. Two generators close that gap and both are enforced from
`tools/design.py`, so the netlist will not build if either fails:

- **`tools/qualified.py`** — MPN, manufacturer package code, footprint,
  ratings that matter here, and how the pin map was confirmed, for every
  non-generic part. A new IC cannot enter the design without an entry.
- **`tools/budget.py`** — per-rail worst-case load, regulator input window,
  inductor ripple, peak current and saturation margin. It fails if any
  inductor saturates below what its rail needs, or if a regulator's source can
  fall below its minimum input.

## LCSC part numbers — read this

Exact LCSC IDs are carried in the generated schematic/netlist for qualified
ICs, connectors and selected passives. Other passive values still need BOM
matching against the required package, tolerance and voltage rating. Use
[the import checklist](../ref/jlcpcb-import-checklist.md) and the generated
[qualified-parts table](../ref/qualified-parts.md); do not substitute a nearby
suffix without checking its package and ratings.

## Board

100 x 100 mm, ENIG, nominal 1.6 mm. The stackup is being moved from six to
eight layers in rev A phase B1 (`ref/rev-a-plan.md`); the text below
describes the six-layer rules still in `odin.kicad_pro` until then. Keep both
ground planes continuous under the PSRAM groups, the RGMII bus and the link
pairs.

Dielectric spacings follow [JLC06161H-1080B](https://jlcpcb.com/impedance),
with 0.0764 mm outer prepregs and 0.1 mm cores next to the inner signal and
power layers. The central prepreg/core/prepreg spacer is represented as a
three-sublayer, 1.1208 mm dielectric. Material Dk values and the 100 Ω
geometry come from JLC's calculator tables; see [PCB impedance](../ref/pcb-impedance.md)
for the inputs and saved solver responses. The `MGT_100R` class has no nets
in rev A and is replaced by `LVDS_100R` and `RGMII` in phase B1. PSRAM has a
0.1 mm minimum width; default clearance is 0.15 mm.

Regenerate stackup and rules without replacing placement or routing:
`python3 tools/gen_pcb.py --rules-only`. Net classes live in `odin.kicad_pro`;
DRC constraints live in the generated `odin.kicad_dru`.

A–H are eight logical zones carried by one continuous 2x32 through-hole
signal body on each left/right edge. Every A–H/L/M zone has a position-1 long key post and its own
1x7 female power body at positions 2..8; L and M each use a separate 2x8
through-hole signal body.
