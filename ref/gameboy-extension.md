# Reference extension: LCD + speaker + gamepad

A worked example, and the proof that the module scheme is sized right. A
student builds against this without touching the base board.

Global IO numbering is `IO_1..IO_80`, ten per slot:

| Slot | IO | Path |
|---|---|---|
| A | IO_1–10  | buffered |
| B | IO_11–20 | buffered |
| C | IO_21–30 | direct |
| D | IO_31–40 | direct |
| E | IO_41–50 | direct |
| F | IO_51–60 | direct |
| G | IO_61–70 | direct |
| H | IO_71–80 | direct |

**Use direct slots.** A parallel LCD clocks pixels at 25 MHz+; the
auto-direction shifters on A/B will not do that and are the wrong part for a
unidirectional video bus anyway.

---

## Tier 1 — the easy one: a 32 in slots C+D (20 IO)

| Function | Pins | IO |
|---|---|---|
| SPI LCD (ST7789 / ILI9341): SCK, MOSI, CS, DC, RST | 5 | IO_21–25 |
| LCD backlight PWM | 1 | IO_26 |
| Audio: PWM out + amp shutdown | 2 | IO_27–28 |
| Buttons: Up, Down, Left, Right, A, B, Start, Select | 8 | IO_29–36 |
| **spare** | **4** | IO_37–40 |

Everything runs at 3.3V. Set VCCIO = 3.3V; it is the default.

## Tier 2 — the real one: a 64 in slots C–F (40 IO)

Parallel RGB565. The FPGA generates video timing in fabric, which is the
reason to own an FPGA at all.

| Function | Pins | IO |
|---|---|---|
| LCD RGB565 data: R[4:0], G[5:0], B[4:0] | 16 | IO_21–36 |
| LCD sync: PCLK, HSYNC, VSYNC, DE | 4 | IO_37–40 |
| Buttons ×8 | 8 | IO_41–48 |
| LCD RESET, backlight PWM | 2 | IO_49–50 |
| Audio I2S: BCLK, LRCLK, SDATA (PCM5102, no MCLK needed) | 3 | IO_51–53 |
| microSD SPI: SCK, MOSI, MISO, CS — for ROMs and assets | 4 | IO_54–57 |
| **spare** | **3** | IO_58–60 |

Fits in 40 with slack. Slots C+D are one bank, E+F the next, both at
VCCIO = 3.3V.

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
| 4 contiguous **direct** slots | Tier 2 needs a 64 with nothing in the signal path |
| +5V able to source **≥1 A** to extensions | class-D amp peaks |
| AUX jumperable to 12V on those slots | backlight |
| **PSRAM reachable from fabric** | see framebuffer note below |
| Board oscillator + MMCM | extension carries no crystal |
| Board-ID pins per module | supervisor only enables 12V for a board that asked |

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
Not yet checked: that the current design actually has 6 direct slots in a
contiguous run, that the +5V buck can deliver 1 A beyond the board's own load,
that the PSRAM is wired to fabric rather than reserved, and the real bank
boundaries on `XC7A50T-2CSG325I`. All are step 6/7 work in
`ref/ide-agent-prompt.md`.
