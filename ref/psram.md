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

Bank 14 is pinned at 3.3V by the config flash, so it also carries PSRAM (24),
the board-controller sideband (6), the flash pins (6), and 5V BUS 0 with its
direction and active-low enable pins. 5V BUS 1 lives in fixed bank 13. Banks 15 and 34 are the two
settable extension domains, four slots each. Banks 16 and 35 remain reserved
for future base-board peripherals. See
`ref/ballmap.md`, which is generated from the package file.

## Layout note

All **24 signals have populated 33 ohm series resistors**, 0402, LCSC
C25105. The FPGA-side names and ball assignments are unchanged; the PSRAM
side of each resistor has a `_MEM` suffix. There are no direct bypass nets.

| Port | Resistors, in SCK / CE_B / IO0 / IO1 / IO2 / IO3 order |
|---|---|
| PSRAM0 / U2 | R104–R109 |
| PSRAM1 / U3 | R110–R115 |
| PSRAM2 / U4 | R116–R121 |
| PSRAM3 / U5 | R122–R127 |

`tools/place.py` places these at U1's right-hand escape edge, pad 1 toward
the FPGA and pad 2 toward the memory. The starting column is 15.4 mm from
U1's centre, with 1 mm pitch, ordered by the assigned ball row/column.
Refine each position during escape routing to keep the FPGA-to-resistor
trace short; the resistor must precede the long trace to the PSRAM. Existing
board placement and routing are unfinished, so this is not routed termination.

**33 ohms is an initial tuning value, not a verified impedance match.** The
clock and chip-select are driven by the FPGA; IO0–IO3 reverse direction on
reads. An FPGA-end resistor does not provide source termination at the PSRAM
end during reads. Check both read and write waveforms and timing, tune drive
strength/slew and resistance (including 0 ohms if appropriate), and do not
assume these footprints alone establish 100 MHz operation. Source-end
placement follows [TI's SPI termination guidance](https://e2e.ti.com/support/microcontrollers/arm-based-microcontrollers-group/arm-based-microcontrollers/f/arm-based-microcontrollers-forum/643087/tm4c1294kcpdt-spi-terminations-for-multiple-slave).

Match timing within each chip's six-signal group, including the FPGA escape
and resistor. Independent ports do not require matching to each other.

## Why four, and not two or six

Four is not arbitrary. It is the count where three separate things line up:

- **Four is the realistic number of independent consumers** in a non-trivial
  design: a display, a CPU, a capture/DMA stream, and scratch. Below four you
  start arbitrating, and arbitration is exactly the predictability you bought
  PSRAM to avoid.
- **Four ganged is a natural 16-bit wide bus** for streaming mode. Three would
  be an awkward 12-bit.
- **Four × 2 MB = 8 MB** clears the threshold where whole classes of project
  stop being "does it fit" and start being "what shall I build".

Two chips (12 pins) would free enough IO for one more extension slot, and
would still cover the Gameboy case. It would kill everything in the second
half of the table below. Six chips (36 pins) costs a whole extension slot and
repays it in almost nothing — past four independent consumers is rare.

**Keep four.**

## What four ports actually unlocks

| Experiment | Ports | Why it needs them |
|---|---|---|
| Gameboy tier 2 | 2 | video reads framebuffer, CPU runs game logic |
| Tearing-free double buffering | 3 | front buffer, back buffer, CPU |
| **Multi-core NEORV32, private RAM per core** | **4** | four cores, four memories, **no cache coherency to design** |
| Stereo vision / dual camera | 4 | two capture streams, one work buffer, one output |
| Retro console emulation | 4 | ROM, work RAM, framebuffer, audio samples |
| Dual Ethernet packet buffers | 4 | RX and TX rings that never stall each other |
| SDR receiver | 3 | sample ring, FFT scratch, output |
| CNN inference | 3 | weights streaming while activations ping-pong |
| **Deep logic analyser** | 4 **ganged** | 8 MB capture at 200 MB/s — the streaming mode |
| **no-MMU Linux on NEORV32** | 4 contiguous | 8 MB is roughly the floor for a useful userland |

The two bolded rows are the ones that justify the decision. **Four private
memories for four cores** turns "design a coherency protocol" — a PhD-shaped
distraction — into "instantiate four of them", which is a semester project a
student can actually finish. And **no-MMU Linux** is only on the table at all
because 8 MB exists.

Note the table uses both wiring modes: independent for nine rows, ganged x16
for the logic analyser. That is the superset argument paying off — one board
does both because the buses were wired independently.

## Worth considering: let the supervisor preload PSRAM

During FPGA configuration every user I/O is high-Z. So while `PROG_B` is held
low, the supervisor can drive a PSRAM chip's bus directly, with no contention
and no mux — the FPGA physically cannot fight it.

Add one chip's QSPI bus to the supervisor's existing SPI, with its own `CE#`
and the same ~33R series resistors used elsewhere. **Cost: one supervisor GPIO
and four resistors.**

What it buys: drag a 2 MB game ROM, a texture set, or a pile of CNN weights
over USB-C, have the supervisor write it into PSRAM, then release `PROG_B`.
The fabric wakes up with its data already in memory. No bootloader in HDL, no
UART trickle, no SD card required.

This is a proposal, not a decision — it wants confirming that the chosen
PSRAM bank's IO really are high-Z during config (check `PUDC_B` strapping,
which sets whether unconfigured IO float or pull up).

## To verify

- Capacity per chip. `APS1604M` reads as 16 Mbit = **2 MB**, so ×4 = **8 MB**,
  not 4. Confirm against the AP Memory datasheet and correct this file.
- Max clock for the `-3` grade (expect 84–133 MHz) — the 50 MB/s per chip
  figure above assumes 100 MHz.
- Four independent buses and all 24 series paths are verified in the
  generated netlist. Physical routing and signal integrity still need checking.
- Whether the supervisor-preload path above is worth its one GPIO. Depends on
  `PUDC_B` strapping and on whether the supervisor GPIO budget has slack after
  step 5.
