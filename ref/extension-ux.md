# Odin extension connector — the whole spec

If you are building an extension, this page is all you need.

## The module

One **module** = 16 pins (2×8, 0.1"). Extensions come in 1, 2 or 4 modules —
a **16**, a **32** or a **64**. Modules are identical and adjacent, so two 32s
sit side by side exactly where a 64 goes.

```
        1    2    3    4    5    6    7    8
 row A  IO0  IO1  GND  IO2  IO3  IO4  VCCIO  +5V
 row B  IO5  IO6  GND  IO7  IO8  IO9  +3V3   AUX
```

10 IO, 2 GND, 4 rails. Pin 1 is keyed.

## The four rails, and why you are never blocked

| Pin | Rail | Fixed or set | What it is for |
|---|---|---|---|
| A7 | **VCCIO** | **set per module: 3.3 / 2.5 / 1.8V** | Powers the FPGA bank *and* your logic. See below. |
| A8 | **+5V** | fixed | Crappy 5V parts, LCD backlights, servos. |
| B7 | **+3V3** | fixed | Always there even when VCCIO is 1.8V. Power your sensor here. |
| B8 | **AUX** | set per module: VIN / +12V / +9V | Motors, relays, op-amps, boost-fed backlights. |

**+3V3 is fixed on purpose.** If VCCIO is jumpered to 1.8V you still have a
normal 3.3V supply for the part you are powering. Signalling level and supply
rail are separate problems and this is the pin that keeps them separate.

## VCCIO is the bank voltage — this is the important bit

An FPGA pin has no fixed voltage. Pins live in **banks**, and a bank's `VCCO`
supply *is* the logic level of every pin in it. On Odin the module's VCCIO pin
**is** that bank's `VCCO`. One jumper moves both together.

So: jumper the module to 2.5V and you get a 2.5V rail on B7… and IO0–IO9
become 2.5V pins, LVDS-capable. Jumper it to 3.3V and they are 3.3V pins.
**The rail on the connector and the logic level of the pins can never
disagree.** You do not have to know this to use the board. That is the point.

## Bank alignment: what a 16 / 32 / 64 actually buys you

`VCCO` is per bank, not per pin, so module independence is limited by how many
banks the FPGA has. Modules are paired into banks:

| You plug in a | You get | VCCIO independence |
|---|---|---|
| **16** (1 module) | 10 IO | shares VCCIO with its partner slot |
| **32** (2 modules) | 20 IO | **owns its bank — set VCCIO freely** |
| **64** (4 modules) | 40 IO | owns two banks, two independent VCCIO |

If you need a voltage nobody else on the board is using, **use a 32**. That is
the whole rule.

## Buffered slots vs direct slots

Two slots run through `SN74LXCH8T245` auto-direction level shifters. The rest
go straight to the FPGA ball.

| Slots | Path | 5V tolerant | Speed | LVDS |
|---|---|---|---|---|
| **A, B** | buffered | yes | low — tens of MHz, auto-direction | no |
| **C–H** | direct | no (VCCIO max 3.3V) | full FPGA speed | yes, on pairs |

**Building with junk 5V parts?** Slots A/B. The shifter handles it.
**Building anything fast — LVDS, DDR, video, RJ45?** Slots C–H. Nothing in the
signal path.

That is the trade and it is the only reason the two kinds exist.

## Differential pairs

On direct slots, IO0/IO1 and IO3/IO4 and IO7/IO8 are routed as matched pairs
with GND at A3/B3 between them. Use those for LVDS. Set VCCIO to 2.5V first.

## Rules

- **The 1.0V FPGA core never reaches a connector.** Do not look for it.
- Every rail is individually fused. Shorting your extension does not take the
  board down.
- Each module has board-ID pins so the supervisor knows what you plugged in
  and can refuse to power a rail into a board that does not want it.
- IO are numbered globally `IO_1..IO_80`, ten per module, so a slot's identity
  is readable from the net name.

## Still to be confirmed against the datasheet

The bank count on `XC7A50T-2CSG325I` sets how many modules pair per bank; the
2-per-bank figure above assumes four usable I/O banks and must be checked
against DS181. The 3× shifter count for two buffered slots (20 IO, 24
channels) assumes the four `SN74LXCH8T245` in the current schematic are
available for this. Both are flagged in `findings.md`.
