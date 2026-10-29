# FPGA decoupling

The XC7A100T-FGG676 decoupling network is the one UG483 v1.14 (7 Series FPGAs
PCB Design Guide) prescribes for this exact device and package, nothing
derived. `tools/design.py` fits it as refs **C301..C392**, groups `decap *`
on the FPGA sheet. The counts are not a design choice here; change them only
against a newer UG483 or a measured PDN.

## Quantities: UG483 Table 2-2, row FGG676 / XC7A100T

| Supply | Net | Parts |
|---|---|---|
| VCCINT | `+1V0` | 1 x 330 uF, 6 x 4.7 uF, 8 x 0.47 uF |
| VCCBRAM | `+1V0` (shared with VCCINT, `gen_sch.py` RAIL) | 1 x 100 uF, 2 x 0.47 uF |
| VCCAUX | `+1V8` | 1 x 47 uF, 3 x 4.7 uF, 5 x 0.47 uF |
| VCCO bank 0 | `+3V3` | 1 x 47 uF |
| VCCO, each I/O bank 13, 14, 15, 16, 34, 35 | bank rail | 2 x 4.7 uF, 4 x 0.47 uF |
| VCCO, per voltage group of up to four banks (note 3) | group rail | 1 x 47 uF |

Note 2 of the table excludes MGTAVCC and MGTAVTT: those are UG482's. They stay
as fitted before this change, one 100 nF 0402 per ball (10 + 12) and one
4.7 uF 0603 per rail. Not re-derived. VCCADC is not in the table; its single
100 nF 0402 on `+1V8` stays.

Banks 12 and 33 exist in the FGG676 ball list but have only VCCO balls on the
XC7A100T (unbonded). They are tied to `+3V3` and are not banks for the
per-bank row.

Voltage groups today: `+3V3` = banks 14 and 35 (one 47 uF, C366), `VCCIO_1`
= bank 15 (one), `+2V5` = bank 16 (one), `VCCIO_2` = bank 34 (one), `+1V8_IO`
= bank 13 (one, C394, appended after the MGT capacitors). The grouping is
computed from `gen_sch.RAIL`; a bank that moves to another rail regroups its
47 uF automatically.

Total: 15 + 3 + 9 + 1 + 36 + 3 = 67 UG483 parts, plus 24 MGT and 1 VCCADC
= 92. The previous scheme was 96 x 100 nF plus 14 x 4.7 uF (110).

## Packages and parts: UG483 Table 2-5

| Ideal value | Body | Type | ESL max | ESR range | Rating | Suggested part |
|---|---|---|---|---|---|---|
| 330 uF | 7343 / D | 2-terminal tantalum | 1 nH | 5-40 mohm | 2.5 V | T520V337M2R5ATE025 |
| 100 uF | 1210 | X7R/X5R ceramic | 1 nH | 1-40 mohm | 2.5 V | GRM32ER60J107ME20L |
| 47 uF | 1210 | X7R/X5R ceramic | 1 nH | 1-40 mohm | 6.3 V | GRM32ER70J476ME20L |
| 4.7 uF | 0805 | X7R/X5R ceramic | 0.5 nH | 1-20 mohm | 6.3 V | GRM21BR71A475KA73 |
| 0.47 uF | 0603 | X7R/X5R ceramic | 0.5 nH | 1-20 mohm | 6.3 V | GRM188R70J474KA01 |

Table notes: value may be larger, body may be smaller, ESR must be in range,
voltage rating may be higher. The schematic values carry the rating
(`4.7uF 6.3V`, `100uF 2.5V`, ...). The ceramics are ordinary BOM-matched
passives; the tantalum is in `tools/qualified.py` because no LCSC listing was
found on 2026-10-23, so the owner sources it (or an equivalent meeting the
330 uF line) at quote time.

## Placement rule (UG483 "PCB Capacitor Placement and Mounting Techniques")

The board is assembled on one side; nothing goes under the package on B.Cu.

- **0.47 uF 0603**: as close to the package as possible, ring around U1 on
  F.Cu, each on its own supply via pair. UG483: any placement within two
  electrical inches of the point of load is acceptable; vias butted against
  the pads, preferably at the sides of the pads (Figure 2-1C).
- **4.7 uF 0805**: the next ring out, same mounting rule.
- **1210 and D-case bulk**: anywhere near the FPGA, best as close as the
  rings allow; short wide connections to the planes with multiple vias.
  Location is not critical for the low-frequency energy they supply.
- Put each bank's six capacitors on that bank's side of the package. With
  U1 at rotation 0 (row A toward the left board edge, column 26 toward the
  top edge) the bank centroids are: 13 top-right, 14 top-centre, 15 upper
  left, 16 top-left corner, 34 bottom-centre, 35 bottom-left. Computed from
  `tools/alloc.py`; see `ref/rev-a-plan.md` for the ball-to-edge map.
- The MGT 100 nF 0402s keep the same ring rule on the GTP corner.

The refs start in the import band outside the board. Hand placement in phase
B; no script places them.
