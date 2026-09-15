# The board controller's startup memory

`U8`, a `W25Q32JVZP` — 4 MB of QSPI flash next to the RP2350B.

## It is not an accessory

The RP2350 has **no internal program flash**. This chip *is* the board controller's
program store, and the processor executes straight out of it. Remove it and
the board controller is a brick. That is why it sits on the RP2350's dedicated QSPI
pins rather than sharing anything.

Note this is a *different* flash from `U6`, the 32 MB `W25Q256` that holds the
FPGA bitstream. Two flashes, two jobs, no sharing:

| | `U8` (4 MB) | `U6` (32 MB) |
|---|---|---|
| Bus | RP2350 dedicated QSPI | shared: FPGA master-SPI + board controller |
| Holds | board-controller firmware and board state | FPGA bitstream and fabric software |
| Written by | USB drag-and-drop | board controller, over plain SPI |

## You cannot brick the board controller

`SW1` pulls the flash chip-select low through a 1 k resistor. Hold it at
reset and the RP2350 cannot read a program, so it falls back to its mask-ROM
bootloader and enumerates as a **USB mass-storage device**. Drag a firmware
file onto it and let go.

No programmer, no debug probe, no recovery jig — the `SWD` header at `J51` is
there for real debugging, not for getting out of trouble. This is the single
most important property of the whole board-controller design: the thing that owns
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

For this to work the board controller must be alive the instant USB power appears,
before any firmware has run. That drives the power sequencing below.

## Why +3V3 is not switchable

The board controller runs on +3V3. If it also had to *enable* +3V3, it
could never start — it would be waiting for a rail only it can turn on.

So **+3V3 is always on**: a wide-input `AP63300` buck (`U12`) straight off
`VSYS`. Its enable is deliberately left floating, which its datasheet defines
as automatic startup; it is not wired to any GPIO. Power appears, +3V3
appears, the board controller boots, and only then does it bring up the rails it
controls. Its 3.8 V minimum input is why it is used here instead of the
`TLV62569`: it must start from the worst-case plain-USB path before anything
has negotiated anything.

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
  which rails are allowed on, each SLOT POWER policy, the board serial, and
  the PIN VOLTAGE jumper positions as last read.
- **A fault log.** Which rail browned out, at what input voltage, how long
  ago. The board controller already measures every rail; writing the
  interesting moments down turns "it randomly resets" into a timestamped
  record you can read over the console.
- **Optionally, a built-in self-test bitstream.** The controller flash can hold
  one only after the actual `XC7A100T` self-test image and controller firmware
  have been measured. Then a virgin board with a blank config flash still
  comes up, blinks an LED, and prints *"no user bitstream — running built-in
  self test"*. That is a much better first five minutes than a dead board.

## Where FPGA image redundancy actually belongs — not here

It is tempting to keep a golden FPGA image in the controller memory and
slave-serial it in when the main one fails. Don't. Artix-7 already has
**MultiBoot with fallback** (UG470): a golden image at address 0 of the config
flash that jumps to an update image and falls back automatically on a CRC
failure, in hardware, with no board-controller involvement and no 2 MB of bit-banging.

`U6` is 32 MB. Use MultiBoot and spend the controller memory on things only
the board controller can do. Do not publish an image count until the generated
`XC7A100T` bitstream size is measured.

## Sizing

The controller has 4 MB. Reserve the firmware and fault-log space first, then
measure the actual self-test image before promising it fits. The FPGA's own
`U6` configuration flash is 32 MB and is where golden and update images belong.
