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

1. The `LFE5U-25F-6BG256C` (ECP5) in the current schematic is a mistake.
2. RP2040 GPIO count does not carry the supervisor scope below. Review against
   an **RP2350B (48 GPIO)** and report the swap as a blocker finding.
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

## Ask these before doing anything else

- **One Artix-7 or two?** The prompt history says dual, but the Gameboy target
  and the cost-effectiveness goal both argue for one. Two doubles the config
  chain and the GPIO pressure. Get a decision.
- **Extension unit: 16 pins or 16 columns?** On the old board a group was a
  2×7 (14 pins) + a 2×1 (2 pins) + a 1×1 key post = 16 pins / 8 columns, ×8
  groups = 128 positions. The human's "8+7+1=16" counts columns, which matches
  the *new* schdoc mix (2×8 ×6, 2×7 ×8, plus keys) and makes 16 columns = 32
  pins. These give different meanings to "a 64". Get a decision.

## Steps

**0. Unblock the netlist.** The current schematic has no exported Protel
netlist — EasyEDA exports per board, and the only board is the old one. Tell
the human exactly what to do in EasyEDA (create a PCB for the current
schematic, then export Protel netlist + BOM), and wait. Without it, no
designator in any finding is trustworthy. Do not fake it with schdoc refdes.

**1. Re-derive.** Run `extract.py` on the new netlist. Confirm
`odin.srcdiff` is empty-ish and `odin.desigmap` maps nearly all symbols.
Report every part in the netlist missing from the BOM and vice versa.

**2. FPGA facts.** Identify the exact part from the netlist. Fetch, from
DS181 and UG470, only the facts you need: every supply rail and its voltage,
the sequencing rule between them, bank VCCO rules, config pin behaviour,
decoupling recommendations. Write `ref/fpga-facts.md` with a source citation
per fact. Do not paraphrase from memory.

**3. Power review.** For each regulator: input rail, output rail, feedback
divider and the output voltage it actually computes to, enable wiring,
power-good wiring. Check against the step 2 sequencing rule. Check decoupling
per FPGA rail. Confirm the supervisor is on an always-on rail and that every
other enable is supervisor-driven with power-good (or ADC readback) returned.

**4. Config and boot.** Verify every item in decision 3 is wired: series
resistors on shared lines, pull-ups/downs per UG470, M[2:0] strapping,
PROG_B/INIT_B/DONE and the DONE LED, PUDC_B strap, a manual 2×5 JTAG header in
parallel with a jumper to isolate the supervisor, and the fabric sideband
landing on real user I/O. Produce `ref/rp2040-pinmap.md` — supervisor GPIO →
net → FPGA pin / regulator / flash pin. Produce `ref/adabmp-changes.md` — the
firmware change list: new pin map, direct-SPI flash path replacing
spiOverJtag, slave-serial load, power sequencing commands, board-ID read.

**5. Extension connector.** Extract every net reaching the male/female
headers. Produce `ref/extension-pinout.md`: position, net, FPGA pin, bank,
**bank VCCO**, LVDS-capable yes/no, rail current budget. Verify keying,
prefix compatibility across the agreed unit size (so a 32 and a 32 can sit
side by side where a 64 would go), GND adjacency for differential pairs, a
resettable fuse per exported rail, and board-ID pins. Exported rails: 5V,
3.3V, 2.5V, 1.8V, VIN. **Never the 1.0V core.** Note explicitly that a 2.5V
pin does not give an extension LVDS — the bank VCCO does — and say which
banks feed which connectors.

**6. Gameboy gap.** From step 5, state whether a parallel-RGB or SPI LCD,
8–10 buttons, and a PWM or DAC audio path can all be done on an extension
alone. List anything the base board must add. Be concrete about pin counts.

**7. BOM.** Every placed part has an LCSC number. Flag Extended parts that
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
