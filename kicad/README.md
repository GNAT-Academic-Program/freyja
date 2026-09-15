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
python3 tools/gen_pcb.py        # 4-layer board: outline, stackup, design rules
kicad-cli sch export netlist --format kicadsexpr -o kicad/odin.net kicad/odin.kicad_sch
python3 tools/load_pcb.py       # load every footprint and net into that board
```

`load_pcb.py` reads `kicad/odin.net`, so export the netlist before running it
or you will load the previous revision's parts.

**`tools/budget.py` exits non-zero on purpose.** Item 20 in `findings.md` is
an unresolved input-voltage problem, and the tool refuses to pretend
otherwise. Every other check in it passes.

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

Expected ERC: **2 intentional warnings** — the unused `DXP`/`DXN`
temperature-diode labels.

Expected DRC before placement: **0 schematic parity issues**, ~499
`unconnected_items` (the ratsnest — nothing is routed yet), and about thirty
silk/courtyard/hole-clearance complaints from the dump placement. A parity
issue, or a schematic footprint count other than 432, is a regression.

## Your workflow from here

1. Open `odin.kicad_pcb` and update it from the schematic. The schematic now
   contains **432 footprints**; the checked-in PCB intentionally has not been
   reloaded after the U15 redesign because `tools/load_pcb.py` would discard
   placement. Use KiCad's normal schematic-to-PCB update so existing placement
   is preserved.
2. Everything sits in a coarse grid *below* the board outline. Drag the groups
   in and place them. That dump position is why DRC currently reports silk and
   courtyard overlaps — they are placement artifacts, not design errors.
3. Route.
3. Fabrication outputs:
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

Only the parts carried over from your existing BOM have an `LCSC` field set:
`APS1604M-3SQR-SN` (C18214056), `W25Q256JVEIQ` (C97522), `W25Q32JVZP`
(C82317), `TLV62569DRL` (C163217), `TPS54202DDC` (C191884).

**The ~200 generated passives deliberately have none.** I am not going to
invent LCSC numbers for resistors and capacitors from memory when they feed
straight into a fab order. Use **Bouni/kicad-jlcpcb-tools** to assign them —
searching its local parts database for a 100nF 0402 Basic Part is exactly the
job that plugin exists to do, and it is the right tool here.

## Board

100 x 100 mm, 4 layer, ENIG, 1.6 mm. Stackup is F.Cu / In1.Cu (GND plane) /
In2.Cu (power planes) / B.Cu. A–H are eight logical zones carried by four
continuous 2x16 signal bodies and four parallel 1x16 power bodies; L is one
separate 2x8 connector.
Placement and routing are intentionally not started.
