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

## Programming it the first time — you don't

This is the part that surprises people: **a virgin board with a blank flash
needs no programmer at all.**

On reset the RP2350's mask ROM looks for a valid image in the QSPI flash.
Blank flash means no valid image, so the ROM falls straight through into its
USB bootloader and the board enumerates as a **mass-storage device**. Plug in
the USB-C cable, a drive appears, drag the firmware file onto it, done. You do
not even need to hold `SW1` — the button exists for *later*, when there is a
working image and you want to override it.

The flash is soldered blank from the factory and never touched by a
programmer. The RP2350 writes it itself, through its own ROM, over the same
cable you were going to plug in anyway.

For this to work the supervisor must be alive the instant USB power appears,
before any firmware has run. That drives the power sequencing below.

## Why +3V3 is not switchable

The supervisor runs on +3V3. If the supervisor also had to *enable* +3V3, it
could never start — it would be waiting for a rail only it can turn on.

So **+3V3 is always on**: a wide-input buck (`U12`) straight off `VSYS`, with
its enable tied high through a resistor, not wired to any GPIO. Power appears,
+3V3 appears, the supervisor boots, and only then does it bring up the rails
it actually controls. That is also why `U12` is a `TPS54202` rather than the
`TLV62569` used for the other rails: it has to run from either 5 V or 9 V at
the input, since it comes up before anything has negotiated anything.

The order, on a virgin board:

1. USB-C plugged in. `VBUS` = 5 V, the default before any negotiation.
2. `U12` sees `VSYS` and produces +3V3 unconditionally.
3. RP2350 boots. Flash is blank, so its ROM enters USB bootloader mode.
4. You drag firmware on. It writes the flash and resets.
5. Now firmware runs: it measures `VSYS`, decides whether to ask the source
   for 9 V, closes or opens the `VBUS` pass switch accordingly, and brings up
   +5V, +2V5, +1V8, +1V0, +1V2 and the 12 V boost in order.

Steps 1–4 need nothing but a cable.

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
