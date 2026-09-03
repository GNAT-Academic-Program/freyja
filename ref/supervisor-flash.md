# The supervisor's boot flash

`U8`, a `W25Q32JVZP` — 4 MB of QSPI flash next to the RP2350B.

## It is not an accessory

The RP2350 has **no internal program flash**. This chip *is* the supervisor's
program store, and the processor executes straight out of it. Remove it and
the supervisor is a brick. That is why it sits on the RP2350's dedicated QSPI
pins rather than sharing anything.

Note this is a *different* flash from `U6`, the 32 MB `W25Q256` that holds the
FPGA bitstream. Two flashes, two jobs, no sharing:

| | `U8` (4 MB) | `U6` (32 MB) |
|---|---|---|
| Bus | RP2350 dedicated QSPI | shared: FPGA master-SPI + supervisor |
| Holds | supervisor firmware, board state | FPGA bitstream, NEORV32 firmware |
| Written by | USB drag-and-drop | supervisor, over plain SPI |

## You cannot brick the supervisor

`SW1` pulls the flash chip-select low through a 1 k resistor. Hold it at
reset and the RP2350 cannot read a program, so it falls back to its mask-ROM
bootloader and enumerates as a **USB mass-storage device**. Drag a firmware
file onto it and let go.

No programmer, no debug probe, no recovery jig — the `SWD` header at `J51` is
there for real debugging, not for getting out of trouble. This is the single
most important property of the whole supervisor design: the thing that owns
every power rail on the board can always be recovered by a human with a USB
cable.

## What else lives in the 4 MB

Firmware is maybe 400 KB. The rest is the interesting part:

- **Board state that must survive power-off.** Which PD voltage to request,
  which rails are allowed on, the per-slot AUX policy, the board serial, the
  VCCIO jumper positions as last read.
- **A fault log.** Which rail browned out, at what input voltage, how long
  ago. The supervisor already measures every rail on its ADC; writing the
  interesting moments down turns "it randomly resets" into a timestamped
  record you can read over the console.
- **Optionally, a built-in self-test bitstream.** An `XC7A50T` image is
  2.19 MB, which fits. Then a virgin board with a blank config flash still
  comes up, blinks an LED, and prints *"no user bitstream — running built-in
  self test"*. That is a much better first five minutes than a dead board.

## Where FPGA image redundancy actually belongs — not here

It is tempting to keep a golden FPGA image in the supervisor flash and
slave-serial it in when the main one fails. Don't. Artix-7 already has
**MultiBoot with fallback** (UG470): a golden image at address 0 of the config
flash that jumps to an update image and falls back automatically on a CRC
failure, in hardware, with no supervisor involvement and no 2 MB of bit-banging.

`U6` is 32 MB. That is fourteen `XC7A50T` bitstreams. Use MultiBoot and spend
the supervisor's flash on things only the supervisor can do.

## Sizing

400 KB firmware + 2.19 MB self-test image = 2.6 MB of 4 MB. It fits, with
about 1.4 MB spare — enough, but not roomy. A `W25Q128` is 16 MB in the same
USON-8 package for roughly $0.30 more and removes the question entirely. Worth
doing if the self-test image is wanted; unnecessary if it is not.
