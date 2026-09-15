# PCB routing rules and impedance

`python3 tools/gen_pcb.py --rules-only` regenerates the stackup, project net
classes and `kicad/odin.kicad_dru` while preserving placement and routing.
Without that flag the generator creates an empty board.

## Selected fabrication stackup

**JLC06161H-1080B**, 6 layers, nominal 1.6 mm, 1 oz outer / 0.5 oz inner,
ENIG: Sig / GND / Sig / PWR / GND / Sig.
Sources: [JLC stackup table](https://jlcpcb.com/impedance) and
[JLC impedance calculator](https://jlcpcb.com/pcb-impedance-calculator),
retrieved 2026-09-15. The calculator template ID is
`44d74b19da284af7ae31a739dbf6b16b`.

| Dielectric between copper layers | Thickness, mm | Material | Dk |
| --- | ---: | --- | ---: |
| F.Cu / In1.Cu | 0.0764 | NP-155F 1080 RC67% | 3.91 |
| In1.Cu / In2.Cu | 0.1000 | NP-155F core | 4.36 |
| In2.Cu / In3.Cu, first sublayer | 0.2104 | NP-155F 7628 RC49% | 4.40 |
| In2.Cu / In3.Cu, middle sublayer | 0.7000 | NP-155F core | 4.53 |
| In2.Cu / In3.Cu, last sublayer | 0.2104 | NP-155F 7628 RC49% | 4.40 |
| In3.Cu / In4.Cu | 0.1000 | NP-155F core | 4.36 |
| In4.Cu / B.Cu | 0.0764 | NP-155F 1080 RC67% | 3.91 |

The material-specific calculator table supplies the core Dk values above;
the general stackup page's generic core Dk is 4.6. The central spacer has
three explicit dielectric sublayers in KiCad. Nominal copper thicknesses are
0.035 mm outer and 0.0152 mm inner.

## 100 Ω differential calculation

Use coated edge-coupled microstrip on **F.Cu referenced to In1.Cu**, or
**B.Cu referenced to In4.Cu**. Keep those reference planes continuous.
The calculator model is `DiffEdgeCoupledCoatedMicrostrip1B`.
Its current copper and solder-mask parameter tables were used, including
the 0.5 oz base-copper row for finished 1 oz outer copper:

| Solver input | Value |
| --- | ---: |
| H1 | 0.0764 mm |
| Er1 | 3.91 |
| Finished trace thickness T1 | 1.6 mil (0.04064 mm) |
| Etch taper W1 − W2 | 0.5 mil (0.0127 mm) |
| Mask C1 / C2 / C3 | 1.0 / 0.6 / 1.0 mil |
| Mask CEr | 3.8 |
| Pair gap S1 | 0.200 mm |
| Target | 100 Ω |

Inverse calculation returns W1 = 3.8828125 mil = **0.0986234375 mm**,
W2 = 3.3828125 mil, with calculated impedance 100.0068 Ω. Set KiCad's
trace width to **0.099 mm**, gap **0.200 mm**. A forward calculation with
the rounded width returns **99.8515 Ω**. The width exceeds JLC's 3.5 mil
(0.0889 mm) minimum. The nominal stackup copper thickness and solver's
finished trace thickness are distinct manufacturer inputs.

These are solver predictions, not measured board impedance. Order controlled
100 Ω impedance with this stackup and have JLC confirm the production geometry.
The public page's generic mask table differs from the current calculator's
mask table; this calculation uses the latter. The table rows, exact solver
requests and responses are saved in
[jlc06161h-1080b-impedance.json](jlc06161h-1080b-impedance.json).

## Generated classes and DRC constraints

| Class | Nets | Rules |
| --- | --- | --- |
| Default | Other nets | 0.15 mm clearance |
| MGT_100R | `MGTP*`, `MGTREFCLK*`, `SFP?_TD_*`, `SFP?_RD_*`, `REFCLK_OSC_*` | Outer-only tracks; 0.099 mm width; 0.200 mm coupled gap; max 0.1 mm intra-pair skew |
| PSRAM | `PSRAM*`, including chip-side `_MEM` nets | 0.1 mm minimum and preferred width; 0.15 mm clearance |

The MGT class covers both sides of AC-coupling capacitors. Skew is checked
within each continuous P/N net pair, not between unrelated lanes or across
capacitors. KiCad 9 recognizes the existing `MGTPTXP0` / `MGTPTXN0` naming
(the suffix matcher skips trailing digits). All ten actual pairs were checked
with KiCad's `BOARD.DpCoupledNet()`.

Other copper stays at least 0.31 mm from MGT copper (approximately four
outer dielectric heights) to limit coplanar loading of the non-coplanar
model. Reference planes on adjacent layers are unaffected. Inner MGT tracks
are prohibited because this geometry is not calculated for those layers.
Plane transitions still require nearby ground stitching vias. Default vias
are 0.45 mm pad / 0.20 mm drill; board minimum track width is 0.0889 mm.
