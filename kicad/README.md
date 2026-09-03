# Odin KiCad project

**Everything here is generated.** Do not hand-edit the `.kicad_sch` files,
`odin.kicad_sym` or `odin.pretty/` — edit the generators and re-run.

Six pages, one per functional block, from `odin.kicad_sch` (the root):

| Page | Contents |
|---|---|
| `fpga.kicad_sch` | FPGA, decoupling, configuration straps |
| `power.kicad_sch` | 12V input to every rail, with monitoring |
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
python3 tools/gen_kicad.py      # XC7A50T symbol + CSG325 footprint + W25Q256 symbol
python3 tools/ballmap.py > ref/ballmap.md
python3 tools/gen_project.py    # schematic from tools/design.py
python3 tools/gen_pcb.py        # 4-layer board: outline, stackup, design rules
python3 tools/load_pcb.py       # load every footprint and net into that board
```

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

Expected ERC: **6 violations, all intentional** — the unused `DXP`/`DXN`
temperature diode and the spare `MGTREFCLK1` reference clock input.

Expected DRC before placement: **0 schematic parity issues**, ~499
`unconnected_items` (the ratsnest — nothing is routed yet), and about a dozen
silk/courtyard/hole-clearance complaints from the dump placement. A parity
issue, or a footprint count other than 359, is a regression.

## Your workflow from here

1. Open `odin.kicad_pcb`. **All 359 footprints and 392 nets are already
   loaded** — `tools/load_pcb.py` does what F8 does in the GUI, so the board
   in git is a real board rather than an empty outline. Press F8 anyway if you
   have edited the schematic since.
2. Everything sits in a coarse grid *below* the board outline. Drag the groups
   in and place them. That dump position is why DRC currently reports silk and
   courtyard overlaps — they are placement artifacts, not design errors.
3. Route.
3. Fabrication outputs:
   ```bash
   jlcpcb-export -p "$PWD/odin.kicad_pcb" --autoTranslate --autoFill --excludeDNP --noBackup
   ```

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

120 x 100 mm, 4 layer, ENIG, 1.6 mm. Stackup is F.Cu / In1.Cu (GND plane) /
In2.Cu (power planes) / B.Cu. Size is a starting guess — nine 2x8 headers plus
the FPGA drove it, adjust once you start placing.
