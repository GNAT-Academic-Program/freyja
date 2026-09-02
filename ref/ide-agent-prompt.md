# Odin — IDE agent prompt

You are reviewing and fixing the Odin FPGA dev board. Work in
`/home/henley/Desktop/odin`.

## Source of truth

EasyEDA Pro is the source of truth. You never edit the board. You read derived
files, find problems, and phrase every fix as an EasyEDA edit the human makes
by hand, then re-exports.

- `Odin_V1.0.0/Odin/*.schdoc` — Altium ASCII export of the **current** design.
  Topology is right. Designators were **renumbered by the exporter** — never
  cite one outside `odin.desigmap`.
- `Netlist_*.net`, `BOM_*.xlsx`, `Odin_0.pcbdoc` — the **previous** revision
  (single ECP5, FT232H programmer). Do not review these as if they were the
  design. They are useful only as a worked example of the extension connector,
  which was fully wired there.
- `extract.py` — derives `odin.parts.ir`, `odin.nets.ir`, `odin.desigmap`,
  `odin.bomdiff`, `odin.srcdiff`. Run `python3 extract.py` from the repo root.
  Read it before changing it.
- `findings.md` — what is already known. Extend it, don't restart it.
- `ref/extension-ux.md` — **the extension connector spec. This is the
  product.** One page, written for the human building an extension, not for
  you. Your job in step 6 is to make the schematic match it, and to keep it
  one page. If it grows past two, you have failed.
- `ref/gameboy-extension.md` — the worked reference extension (LCD, speaker,
  gamepad) that proves the module sizing. Step 7 verifies it.
- `ref/salvage-from-odin0.md` — **read this too.** What in last year's board
  is worth keeping, derived from its netlist, with the reasoning. The
  modulo-16 IO slot scheme described there is the core idea of the product.
- `ref/adabmp/` — clone of github.com/greerelias/adabmp. Working RP2040
  firmware in Ada that programs an Artix-7 bitstream and a NEORV32 firmware.
  Its Basys-3 assumptions (spiOverJtag helper bitstream, flying leads) are
  legacy to be replaced, not preserved.

## What the board is for

An FPGA dev board that is powerful but simple. Prefer the direct wiring over
the clever one. Near-term target: run a NEORV32 soft core, and support a
Gameboy-like extension board (LCD, 8–10 buttons, audio out) **without changing
the base board**. Base board stays cost-effective; VGA / dual RJ45 / USB3 are
explicitly out of scope for now but must not be designed out.

## Decisions already made by the human

1. **One Artix-7. No ECP5.** The `LFE5U-25F-6BG256C` comes out of the current
   schematic entirely — not replaced by a second Artix-7. Rationale: Xilinx
   tooling is the one we live with, and a single part halves the config chain
   and the supervisor GPIO pressure.
2. RP2040 GPIO count may not carry the supervisor scope below. Size it against
   an **RP2350B (48 GPIO)**; if a single Artix-7 lets an RP2040 fit, say so —
   the RP2040 is preferred if it fits, since working firmware already exists.
3. The RP2040/RP2350 is the **board supervisor**, not a programmer bolted on
   the side. Direct control of: config flash over plain SPI, FPGA config pins
   (PROG_B, INIT_B, DONE, CCLK, DIN, M[2:0]), FPGA JTAG, a sideband into the
   fabric (second JTAG for NEORV32 debug + UART + spare GPIO), every regulator
   enable and power-good, extension board-ID pins. **Programming flash must
   not require a helper bitstream**: hold PROG_B low, write flash over SPI,
   release PROG_B. Slave-serial SRAM load uses the same lines. Series
   resistors (~33R) on every line shared between supervisor and FPGA.
4. Host side is one USB-C on the supervisor: CDC + BOOTSEL. Nothing else on
   the board has firmware.

## The design has been decided — see `ref/extension-ux.md`

The module is 2×8 = 16 pins: 10 IO, 2 GND, and four rails (VCCIO, +5V, +3V3,
AUX). Odin_0's 2×7 had **no GND pin at all** — ground returned through a
separate 2-pin header. That is fixed here and is not up for rediscussion.

Three properties are load-bearing. Do not quietly trade them away:

1. **VCCIO on the connector *is* the FPGA bank's `VCCO`**, moved by one
   jumper. A rail pin whose voltage can disagree with the bank's logic level
   is the exact trap this design exists to remove.
2. **+3V3 is fixed and always present**, independent of VCCIO, so an
   extension running 1.8V signalling can still power a normal part.
3. **Two slots are buffered through the level shifters, the rest are
   direct.** Junk 5V parts go in the buffered slots; anything fast goes in a
   direct slot with nothing in the path. Both kinds must exist.

Your job is to verify the schematic can deliver this and report where it
cannot — not to redesign it.

## Steps

**0. Unblock the netlist.** The current schematic has no exported Protel
netlist — EasyEDA exports per board, and the only board is the old one. Tell
the human exactly what to do in EasyEDA (create a PCB for the current
schematic, then export Protel netlist + BOM), and wait. Without it, no
designator in any finding is trustworthy. Do not fake it with schdoc refdes.

**1. Salvage forward.** Read `ref/salvage-from-odin0.md`. For each KEEP item,
check whether the current schematic already honours it and report per item:
the modulo-16 IO slot numbering, the fixed in-slot rail offsets identical
across every connector, core rail never exported, a 1×1 test post per rail.
Odin_0's final circuit is dead — its *patterns* are not. Where the new
schematic has diverged without reason, say so.

**2. Re-derive.** Run `extract.py` on the new netlist. Confirm
`odin.srcdiff` is empty-ish and `odin.desigmap` maps nearly all symbols.
Report every part in the netlist missing from the BOM and vice versa.

**3. FPGA facts.** Identify the exact part from the netlist. Fetch, from
DS181 and UG470, only the facts you need: every supply rail and its voltage,
the sequencing rule between them, bank VCCO rules, config pin behaviour,
decoupling recommendations. Write `ref/fpga-facts.md` with a source citation
per fact. Do not paraphrase from memory.

**4. Power review.** For each regulator: input rail, output rail, feedback
divider and the output voltage it actually computes to, enable wiring,
power-good wiring. Check against the step 2 sequencing rule. Check decoupling
per FPGA rail. Confirm the supervisor is on an always-on rail and that every
other enable is supervisor-driven with power-good (or ADC readback) returned.

**5. Config and boot.** Verify every item in decision 3 is wired: series
resistors on shared lines, pull-ups/downs per UG470, M[2:0] strapping,
PROG_B/INIT_B/DONE and the DONE LED, PUDC_B strap, a manual 2×5 JTAG header in
parallel with a jumper to isolate the supervisor, and the fabric sideband
landing on real user I/O. Produce `ref/rp2040-pinmap.md` — supervisor GPIO →
net → FPGA pin / regulator / flash pin. Produce `ref/adabmp-changes.md` — the
firmware change list: new pin map, direct-SPI flash path replacing
spiOverJtag, slave-serial load, power sequencing commands, board-ID read.

**6. Extension connector.** Extract every net reaching the male/female
headers. Check the schematic against `ref/extension-ux.md` line by line and
report every divergence. Then produce `ref/extension-pinout.md` — the
per-position table backing the spec: position, net, FPGA ball, bank, VCCO
source, buffered or direct, LVDS pair yes/no, rail current budget. Verify
keying,
prefix compatibility (a 32 and a 32 sit side by side exactly where a 64
would go, because slot boundaries are fixed and the in-slot layout is
identical), GND adjacency for differential pairs, a resettable fuse per
exported rail, and board-ID pins. **Every 16-slot's IO must sit inside one
Artix-7 bank**, and that bank's VCCO must track the module's selectable rail
— otherwise the 2.5V pin buys nothing. Exported rails: 5V,
3.3V, 2.5V, 1.8V, VIN. **Never the 1.0V core.** Note explicitly that a 2.5V
pin does not give an extension LVDS — the bank VCCO does — and say which
banks feed which connectors.

**7. Gameboy gap.** `ref/gameboy-extension.md` already does this fit on
paper: a 32 in slots C+D for an SPI LCD build, a 64 in slots C–F for parallel
RGB565 + I2S + microSD, 40 IO with 3 spare. Your job is to confirm it against
the real schematic. Specifically: are there 6 direct slots in a contiguous
run, can +5V source 1 A beyond the board's own load, is the PSRAM reachable
from fabric for a framebuffer, and where do the real bank boundaries fall.
Report what the base board must add. Update that file with verified numbers.

**8. BOM.** Every placed part has an LCSC number. Flag Extended parts that
have a Basic equivalent. Flag zero-stock and near-zero-stock parts.

## Output

Append to `findings.md` as a numbered list. Each item: severity
(blocker / should-fix / nit), the entities involved **by real designator**,
what is wrong, and the fix phrased as an EasyEDA edit.

Never edit the exports or the BOM. Commit derived files and docs; leave inputs
untouched.

## How to behave

Make the evident things happen without asking. When something is genuinely
ambiguous, ask once, in a sentence, and keep working on everything that does
not depend on the answer. Report what you actually verified and what you
assumed — separately. If a step is blocked, say so and do the other steps. No
procedural dance.
