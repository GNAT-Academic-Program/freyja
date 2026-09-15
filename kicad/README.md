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
| `highspeed.kicad_sch` | SFP cages, reference clock, power gate |

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
python3 tools/gen_pcb.py        # 6-layer board: outline, stackup, design rules
kicad-cli sch export netlist --format kicadsexpr -o kicad/odin.net kicad/odin.kicad_sch
python3 tools/load_pcb.py       # load every footprint and net into that board
```

`load_pcb.py` reads `kicad/odin.net`, so export the netlist before running it
or you will load the previous revision's parts.

`tools/budget.py --write` currently passes and regenerates the power budget.
The input-voltage issue in findings item 20 is fixed. The command exits
non-zero if a load, input-window or inductor qualification check fails.

**`gen_pcb.py` destroys any routing.** Run it only before you start laying out.
`load_pcb.py` re-imports footprints and nets and is safe to re-run, but it
replaces the footprints, so it also discards placement.

`tools/alloc.py` is the single source for ball allocation; `ref/ballmap.md` and
the schematic both come from it and cannot drift.

## Verify

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

Latest KiCad 9.0.8 validation: **498 footprints**, with all design values,
footprint IDs and connections synchronized to the PCB. DRC remains separate:
693 violations, 499 unrouted connections and two parity warnings for the
standard SFP symbol's `CAGE` pin missing from its 20-pad electrical connector.
The separate cages are SH1/SH2. See [the validation report](../ref/kicad-validation.md).
Passing the ERC allowlist does not establish fabrication readiness.

## Your workflow from here

1. Open `odin.kicad_pcb`. Its **498 footprints** are synchronized with the
   schematic. The SFP assemblies follow the mechanical placement contract;
   much of the remaining circuitry is still staged outside the board.
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

100 x 100 mm, 6 layer, ENIG, nominal 1.6 mm. Stackup is F.Cu (signal) /
In1.Cu (GND plane) / In2.Cu (signal) / In3.Cu (power planes) /
In4.Cu (GND plane) / B.Cu (signal). The third routing layer supports the
FGG676 inner-ball escape. Keep both ground planes continuous for the GTP
pairs and PSRAM groups.

Dielectric spacings follow [JLC06161H-1080B](https://jlcpcb.com/impedance),
with 0.0764 mm outer prepregs and 0.1 mm cores next to the inner signal and
power layers. The central prepreg/core/prepreg spacer is represented as a
three-sublayer, 1.1208 mm dielectric. Material Dk values and the 100 Ω
geometry come from JLC's calculator tables; see [PCB impedance](../ref/pcb-impedance.md)
for the inputs and saved solver responses. MGT outer tracks use 0.099 mm width /
0.200 mm gap with 0.1 mm maximum intra-pair skew. PSRAM has a 0.1 mm minimum
width; default clearance is 0.15 mm.

Regenerate stackup and rules without replacing placement or routing:
`python3 tools/gen_pcb.py --rules-only`. Net classes live in `odin.kicad_pro`;
DRC constraints live in the generated `odin.kicad_dru`.

A–H are eight logical zones carried by four
continuous 2x16 signal bodies and four parallel 1x16 power bodies; L is one
separate 2x8 connector.
Placement and routing are intentionally not started.
