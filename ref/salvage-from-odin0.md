# What to keep from Odin_0 (last year's board)

Derived from `Netlist_Odin_0_2026-09-02.net`, which is the only fully-wired
description of the extension scheme. Designators here are Odin_0's, real and
trustworthy. They do **not** carry to the new schematic — the pattern does.

## 1. KEEP — the modulo-16 IO slot scheme

Eight identical 2×7 female connectors, `J4`–`J11`. Each one owns a **16-wide
slot in a global `IO_1..IO_128` numbering space**:

| Connector | IO slot | IO actually brought out |
|---|---|---|
| `J8`  | 1–16    | IO_1…IO_10, IO_12 |
| `J9`  | 17–32   | IO_17…IO_26, IO_28 |
| `J10` | 33–48   | IO_33…IO_42, IO_44 |
| `J11` | 49–64   | IO_49…IO_58, IO_60 |
| `J4`  | 65–80   | IO_65…IO_74, IO_76 |
| `J5`  | 81–96   | IO_81…IO_90, IO_92 |
| `J6`  | 97–112  | IO_97…IO_106, IO_108 |
| `J7`  | 113–128 | IO_113…IO_122, IO_124 |

This is the "modulo number of pins" idea, and it is the thing worth
preserving. An extension declares how many 16-slots it occupies. A 16 takes
one, a 32 takes two adjacent, a 64 takes four. Two 32s sit side by side
exactly where a 64 would go, because the slot boundaries are fixed and the
in-slot layout is identical everywhere.

## 2. KEEP — the in-slot layout, identical on all eight

Every connector has the same 14 pins in the same order:

| Pin | Slot offset | Content |
|---|---|---|
| 1–10 | +1 … +10 | IO |
| 11 | +11 | **P3.3V** |
| 12 | +12 | IO |
| 13 | +13 | **P5V** |
| 14 | +14 | **P9V** |
| — | +15, +16 | not present — this is the key column |

11 IO + 3 rails per module. The rails land at a **fixed offset inside every
slot**, which is what actually makes prefix compatibility work: an extension
can hardcode where its power is without knowing which slot it was plugged
into.

**This also resolves "8 + 7 + 1 = 16".** The unit is 16 grid positions =
8 columns × 2 rows, realised as a **7-column connector (2×7, 14 pins) plus a
1-column key/gap**. Not 16 pins. A 64 is four units = 32 columns = 56
populated pins + 4 key columns.

## 3. KEEP — the core rail is not exported

`P1.1V` (ECP5 core) fans out to `U1`, `L1`, `R1` and three caps only. It never
reaches a connector. The Artix-7's 1.0V `VCCINT` must stay off the connectors
the same way.

## 4. KEEP — a 1×1 test post per rail

`P3`–`P10` are single male posts, one per rail: `24VTO5V`, `P5V`, `GND`,
`P9V`, `P12V`, `VWALL`, `9VTO5V`, and one unnamed net. Cheap, and the
difference between debugging a rail and guessing at one.

## 5. KEEP — rail topology, re-target the voltages

Odin_0 tree: `VWALL` (USB1) → `P12V`, `P9V` → `24VTO5V` / `9VTO5V` → `P5V` →
`P3.3V`, `P2.5V`, `P1.1V`. Bucks are `TPS54202DDCR` ×4 and `TLV62569DRLR` ×3.
The shape is sound. The voltages change for Artix-7: `VCCINT` 1.0V,
`VCCBRAM` 1.0V, `VCCAUX` 1.8V, `VCCADC` 1.8V, per-bank `VCCO` — all to be
confirmed against DS181, not assumed.

## 6. FIX — 2.5V exists but is not exported

`P2.5V` fans out to `U1` and `U8` (SRAM) only. It reaches no connector. For
the stated goal of "plug in an RJ45 and do LVDS without rolling your own",
2.5V has to be reachable from an extension **and** the bank feeding that
connector has to be at VCCO=2.5V. The rail alone is not enough.

## 7. NOT SALVAGE — H5–H12 are not part of the keying

I previously read `H5`–`H12` (`3-644456-2`, 2-pin) as part of a 16-pin
extension group. They are not: all eight are simply `GND` + `P12V`. Aux 12V
taps. Keep or drop on their own merits; they have nothing to do with the
extension scheme.

## 8. NOT SALVAGE — the jumper rail selector is new, not old

Odin_0 has no rail-selection jumper. The idea lives only in the **new**
schematic, which carries `PH2.54-01-03PZD` ×4 (1×3 headers — the classic
three-pin rail selector, centre pin to the load, ends to two rail choices)
and `ZX-PZ2.54-2-4PZZ` ×4. Four of each, against eight connectors. What they
select cannot be read without the new netlist.

## The one real tension to resolve

A 14-pin module has room for exactly 3 rail pins, and Odin_0 spent them on
3.3V / 5V / 9V. The goal is to also offer 2.5V, 1.8V and VIN. Three ways out,
in order of preference:

1. **Make offset +14 the jumper-selected rail.** Fixed 3.3V at +11, fixed 5V
   at +13, and +14 becomes per-module selectable (9V / 2.5V / 1.8V / VIN) via
   the 1×3 headers already in the new schematic. Costs no IO, and the four
   1×3 headers suggest this is already the intent.
2. **Widen the module to a 2×8 (16 pins, 8 columns, no key column).** The new
   schematic has six `2.54-2*8P_`. Buys 2 more pins but removes the key gap,
   so keying must come from elsewhere.
3. **Trade an IO for a rail.** 10 IO + 4 rails. Cheapest to draw, worst for
   the LCD extension, which wants every pin it can get.

Whichever is chosen, **VCCO per module is the decision that matters more than
the rail pins.** Each 16-slot's IO should sit entirely within one Artix-7
bank, and that bank's VCCO should track the selectable rail — otherwise a
2.5V pin buys nothing and an extension cannot do LVDS.
