# Odin KiCad project

**Everything here is generated.** Do not hand-edit `odin.kicad_sch`,
`odin.kicad_sym` or `odin.pretty/` — edit the generators and re-run. The
schematic is laid out mechanically (every pin carries a global label); it is
electrically correct and editable, but it is not pretty. Rearranging it by
hand means giving up regeneration, which is a fair trade once the design
settles — just know that is the moment you make it.

## Regenerate

```bash
python3 tools/gen_kicad.py      # XC7A50T symbol + CSG325 footprint + W25Q256 symbol
python3 tools/ballmap.py > ref/ballmap.md
python3 tools/gen_project.py    # schematic from tools/design.py
python3 tools/gen_pcb.py        # empty 4-layer board (only if you have not started routing)
```

`tools/alloc.py` is the single source for ball allocation; `ref/ballmap.md` and
the schematic both come from it and cannot drift.

## Verify

```bash
kicad-cli sch erc --severity-all -o erc.rpt odin.kicad_sch
kicad-cli pcb drc --severity-all -o drc.rpt odin.kicad_pcb
kicad-cli sch export netlist --format kicadsexpr -o odin.net odin.kicad_sch
```

Expected ERC: **35 violations, all of them the reserved GTP transceivers** —
23 dangling labels and 12 undriven inputs on `MGTP*`/`MGTREFCLK*`, plus the
unused `DXP`/`DXN` temperature diode. Anything else is a regression.

## Your workflow from here

1. Open `odin.kicad_pcb`, press **F8** (Update PCB from Schematic) to pull in
   all 289 footprints.
2. Place and route.
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
