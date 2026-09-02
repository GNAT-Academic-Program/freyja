# PSRAM — 4 chips, 4 independent ports

`APS1604M-3SQR-SN` ×4 (LCSC C18214056), QSPI, 3.3V. The point of this part is
what BRAM and DDR3 both fail at: **enough capacity to be useful, with
single-cycle-predictable random access down to one byte.** No burst-shaped
thinking, no calibration, no memory controller IP you cannot read.

## The one wiring decision

Four QSPI chips can be wired three ways. Only one of them is right.

| Wiring | Pins | What you get |
|---|---|---|
| Shared bus, 4 chip selects | 9 | one chip active at a time. ~50 MB/s total. Cheapest, worst. |
| Ganged x16 (shared SCK/CS, separate IO[3:0]) | 20 | 200 MB/s as **one wide port**. Great for streaming, terrible for a 1-byte write — every access hits all four chips. |
| **4 fully independent QSPI buses** | **24** | **200 MB/s as four ports that do not block each other.** |

**Wire them independently.** The argument is not bandwidth, it is that
independent wiring is a superset: in HDL you can still drive all four in
lockstep to get the ganged x16 streaming mode when you want it. The reverse is
not true — ganged wiring can never be un-ganged. You are paying 4 extra pins
for the option to have both, and the board has the pins.

Per chip: `SCK`, `CE#`, `IO0..IO3` = 6 pins. ×4 = **24 FPGA pins**.

## What that buys, concretely

Video reads its framebuffer from chip 0 while the NEORV32 does random
scattered access on chips 1–3. **No arbiter, no stall, no worst-case latency
analysis.** That is the whole reason to spend the pins.

Bandwidth per chip at 100 MHz QSPI is 4 bits/clock = 50 MB/s. For reference:

| Framebuffer | Bytes | @60 Hz | Chips needed |
|---|---|---|---|
| 320×240 RGB565 | 150 KB | 9 MB/s | well under one |
| 480×272 RGB565 | 261 KB | 16 MB/s | under one |
| 640×480 RGB565 | 614 KB | 37 MB/s | one, with headroom |

One chip covers VGA. Three are left for everything else.

## Recommended default presentation

The wiring gives four ports; how you expose them is an HDL choice. The default
the reference design should ship:

- **chip 0** — video / DMA. Own port, no CPU contention.
- **chips 1–3** — contiguous CPU RAM behind one address decoder, presented to
  NEORV32 as a single Wishbone region.

A student who wants all four for one job just re-wires the HDL. Nothing in the
hardware forces the split.

## Two gotchas that must be in the controller

1. **`tCEM` — maximum CS-low time.** PSRAM self-refreshes internally, but only
   between accesses. Hold `CE#` low longer than ~8 µs and the contents rot.
   Long bursts must be chopped. This is the single most common way people
   break a PSRAM bring-up.
2. **Read latency is fixed, not zero.** There is a wait-state count between
   command and data. Fixed and documented, which is the good news — it is
   predictable, unlike DDR.

Both belong in the HDL controller, not in user code.

## Bank placement — this interacts with the extension design

The PSRAM runs at 3.3V, so its FPGA bank `VCCO` must be **fixed at 3.3V**. It
therefore cannot live in one of the extension slots' VCCIO-selectable banks.

That is not a problem, it is the constraint that makes the numbers work: with
five I/O banks, one bank absorbs PSRAM (24) + supervisor sideband (~14) +
config/flash, leaving four banks for eight extension slots — exactly the
2-slots-per-bank pairing that `ref/extension-ux.md` assumes.

## Layout note

24 single-ended lines at 100 MHz. Series termination at the FPGA, length-match
within each chip's own 6-line group. Groups do not need matching to each
other, since the buses are independent — another small win from the
independent wiring.

## To verify

- Capacity per chip. `APS1604M` reads as 16 Mbit = **2 MB**, so ×4 = **8 MB**,
  not 4. Confirm against the AP Memory datasheet and correct this file.
- Max clock for the `-3` grade (expect 84–133 MHz) — the 50 MB/s per chip
  figure above assumes 100 MHz.
- That the current schematic wires all four independently rather than sharing
  a bus. **If it shares, that is a should-fix finding.**
