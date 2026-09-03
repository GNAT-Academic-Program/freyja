# Reference extension: LCD + speaker + gamepad

A worked example, and the proof that the module scheme is sized right. A
student builds against this without touching the base board.

Global IO numbering is `IO_1..IO_90`, ten per slot:

| Slot | IO | Bank | Path |
|---|---|---|---|
| L | IO_1–10  | 14 | **buffered**, 5V tolerant, shared direction |
| A | IO_11–20 | 15 | direct |
| B | IO_21–30 | 15 | direct |
| C | IO_31–40 | 15 | direct |
| D | IO_41–50 | 15 | direct |
| E | IO_51–60 | 34 | direct |
| F | IO_61–70 | 34 | direct |
| G | IO_71–80 | 34 | direct |
| H | IO_81–90 | 34 | direct |

**Use direct slots.** A parallel LCD clocks pixels at 25 MHz+, and it needs
per-pin direction control that slot L's shared-direction translators cannot
give. Slots A–D are one bank and one voltage domain, so a 64 built there owns
its `VCCIO` outright.

---

## Tier 1 — the easy one: a 32 in slots A+B (20 IO)

| Function | Pins | IO |
|---|---|---|
| SPI LCD (ST7789 / ILI9341): SCK, MOSI, CS, DC, RST | 5 | IO_11–15 |
| LCD backlight PWM | 1 | IO_16 |
| Audio: PWM out + amp shutdown | 2 | IO_17–18 |
| Buttons: Up, Down, Left, Right, A, B, Start, Select | 8 | IO_19–26 |
| **spare** | **4** | IO_27–30 |

Everything runs at 3.3V. Set VCCIO = 3.3V; it is the default.

## Tier 2 — the real one: a 64 in slots A–D (40 IO, one whole bank)

Parallel RGB565. The FPGA generates video timing in fabric, which is the
reason to own an FPGA at all.

| Function | Pins | IO |
|---|---|---|
| LCD RGB565 data: R[4:0], G[5:0], B[4:0] | 16 | IO_11–26 |
| LCD sync: PCLK, HSYNC, VSYNC, DE | 4 | IO_27–30 |
| Buttons x8 | 8 | IO_31–38 |
| LCD RESET, backlight PWM | 2 | IO_39–40 |
| Audio I2S: BCLK, LRCLK, SDATA (PCM5102, no MCLK needed) | 3 | IO_41–43 |
| microSD SPI: SCK, MOSI, MISO, CS — for ROMs and assets | 4 | IO_44–47 |
| **spare** | **3** | IO_48–50 |

Fits in 40 with slack. Slots A–D are bank 15 in its entirety, so this
extension owns the `VCCIO` domain and can set it without consulting anyone.

---

## Rails — all four get used, which is the point

| Rail | Used for | Draw |
|---|---|---|
| VCCIO = 3.3V | FPGA bank level, and every logic part on the extension | — |
| **+3V3** | LCD logic, SD card, I2S DAC | ~150 mA |
| **+5V** | class-D amp (PAM8302 or similar) | ~500 mA peak, ~150 mA avg |
| **AUX = 12V** | backlight constant-current driver | ~150 mA |

This is exactly the case the four-rail module was designed for: a 1.8V-capable
signalling rail would have been useless here, but the extension still needs
3.3V logic, 5V for an analogue amp, and a higher rail for a backlight. Nobody
has to roll their own regulator.

On a 64 the extension gets **four** of each rail pin, so per-module fusing
gives it four times the single-module current budget.

---

## What the base board has to provide

| Requirement | Why |
|---|---|
| 4 contiguous **direct** slots in one bank | Tier 2 needs a 64 with nothing in the signal path and one voltage domain |
| +5V able to source **≥1 A** to extensions | class-D amp peaks |
| AUX jumperable to 12V on those slots | backlight; 12V is boosted on-board so it works on any USB source |
| **PSRAM reachable from fabric** | see framebuffer note below |
| Board oscillator + MMCM | extension carries no crystal |

**Framebuffer.** 320×240 RGB565 is 150 KB; `XC7A50T` has ~337 KB of BRAM, so
it fits but eats most of it. 480×272 is 261 KB and does not leave room for a
NEORV32 with any cache. The 4× `APS1604M` PSRAM on the base board (8 MB) is
what makes a comfortable framebuffer possible — so the LCD path should be
designed as PSRAM framebuffer + line buffer in BRAM, not BRAM framebuffer.

## What the student does *not* have to do

No level shifters. No crystal. No regulators. No JTAG header, no programmer —
the supervisor loads the bitstream and the NEORV32 firmware over the one
USB-C. Plug the extension in, set two jumpers, write HDL.

---

## Unverified

This is a paper fit against `ref/extension-ux.md`, not against the schematic.
Bank boundaries and slot-to-bank mapping are now confirmed against the AMD
package file (`ref/ballmap.md`). Still unchecked: that the +5V rail can
deliver 1 A beyond the board's own load on a given USB source, and the real
current draw of a chosen LCD and amplifier. Both are measurements, not
paperwork.
