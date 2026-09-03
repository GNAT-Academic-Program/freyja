# Odin extension connector — the whole spec

If you are building an extension, this page is all you need.

## The module

One **module** = 16 pins (2×8, 0.1"). Extensions come in 1, 2 or 4 modules —
a **16**, a **32** or a **64**. Modules are identical and adjacent, so two 32s
sit side by side exactly where a 64 goes.

```
        1     2     3     4     5     6     7      8
 row A  P0+   P1+   GND   P2+   P3+   P4+   VCCIO  +5V
 row B  P0-   P1-   GND   P2-   P3-   P4-   +3V3   AUX
```

10 IO, 2 GND, 4 rails. Pin 1 is keyed.

**Every column is a differential pair.** All ten I/O are true LVDS-capable
pairs on the FPGA, arranged so `P+` and `P-` are vertically adjacent on the
header. Doing single-ended? Ignore the signs and call them `IO0..IO9`. Nothing
is wasted either way.

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

## The slots, and the two voltage domains

Nine slots. `XC7A50T-CSG325` has exactly **three** I/O banks, and `VCCO` is per
bank, so three is the hard ceiling on voltage domains — one of which is spent
on the config flash. That leaves **two settable domains**:

| Slots | Bank | VCCIO | Path |
|---|---|---|---|
| **L** | 14 | fixed 3.3V | **buffered**, 5V tolerant |
| **A B C D** | 15 | **settable** 3.3 / 2.5 / 1.8V | direct |
| **E F G H** | 34 | **settable** 3.3 / 2.5 / 1.8V | direct |

| You plug in a | You get | VCCIO |
|---|---|---|
| **16** (1 module) | 10 IO | shares the domain with 3 neighbours |
| **32** (2 modules) | 20 IO | shares the domain with 2 neighbours |
| **64** (4 modules) | 40 IO | **owns its domain outright — set it freely** |

**Only a 64 gets a private voltage.** If your extension needs 2.5V or 1.8V
signalling, build it as a 64 and take a whole bank, or agree the voltage with
whatever else is sharing your domain. Two extensions at different voltages
means one in the A–D domain and one in E–H.

## Slot L — the buffered one

Slot L runs through `SN74LXCH8T245` auto-direction level shifters. Everything
else goes straight to the FPGA ball.

| | Slot L | Slots A–H |
|---|---|---|
| 5V tolerant | **yes** | no (3.3V max) |
| Speed | low — tens of MHz | full FPGA speed |
| LVDS | no | **yes, 5 pairs** |
| VCCIO | fixed 3.3V | settable per domain |

**Junk 5V parts?** Slot L. The shifter handles it, and it costs no voltage
domain because bank 14 is pinned at 3.3V by the config flash anyway.
**Anything fast — LVDS, video, RJ45?** Any of A–H. Nothing in the path.

## Differential pairs

Every column is a pair, with GND at column 3. At moderate rates this is fine
over a short ribbon. A 0.1" header is not a great LVDS medium at any price, so
keep aggressive links short and set VCCIO to 2.5V first — Artix-7 HR banks only
do true LVDS outputs at 2.5V.

## Rules

- **The 1.0V FPGA core never reaches a connector.** Do not look for it.
- Every rail is individually fused. Shorting your extension does not take the
  board down.
- **Not implemented yet:** board-ID pins. All 16 positions are spoken for, so
  there is nowhere to put them without giving up an I/O. See `findings.md`
  item 8. The supervisor still fuses and power-gates every rail; it just
  cannot yet tell *what* you plugged in.
- IO are numbered globally `IO_1..IO_90`, ten per module, so a slot's identity
  is readable from the net name.
- Exact FPGA ball for every pin: `ref/ballmap.md`.

## Confirmed against the package file

Bank count, pair count and every ball assignment come from AMD's
`xc7a50tcsg325` package file, checked into `ref/xc7a50tcsg325pkg.txt` and
processed by `tools/ballmap.py`. Three banks, 50 HR I/O each, 24 differential
pairs each. 126 of 150 I/O assigned, 24 free for base-board peripherals.
