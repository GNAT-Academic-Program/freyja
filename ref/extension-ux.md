# Odin extension connector — the whole spec

If you are building an extension, this page is all you need.

## The module

One **module** = one 16-position signal connector (2×8, 0.1") plus its
separate 8-pin power row on **each of two opposite edges**. An extension is a
shield that bridges the 100 x 100 mm base board:

```text
16:       [ A ]================[ E ]
32:   [ A ][ B ]============[ E ][ F ]
64: [ A ][ B ][ C ][ D ]==[ E ][ F ][ G ][ H ]
```

The name is the connector width on each side:

- a **16** bridges one signal block on each edge: **24 I/O**;
- a **32** bridges two signal blocks on each edge: **48 I/O**;
- a **64** bridges four signal blocks on each edge: **96 I/O**.

The schematic divides each edge into four 16-pin electrical sections: A-D on
one edge and E-H on the other. That does **not** require four separate plastic
headers. The generated schematic and board use the original arrangement of **two
continuous 32-pin stack-through signal headers on each edge**, with a parallel
continuous 32-pin single-row power header. The 16-position boundaries are
labels that let a small shield occupy part of those headers.

That gives the extension support at both ends and most of the board area above
Odin. Each shield carries female sockets underneath and matching male pins on
top, so another shield can stack over it.

Matching pairs are A/E, B/F, C/G and D/H. Placement must put every pair
directly opposite, at identical pitch and orientation. This mechanical fit is
not proven until the base board, a reference shield and the stacking height
are laid out together.

```text
             1     2     3     4     5     6     7     8
signal row 1 IO0   IO2   IO4   IO6   IO8   IO10  GND   GND
signal row 2 IO1   IO3   IO5   IO7   IO9   IO11  GND   GND
power row    GND   PIN V GND   3V3   GND   5V    GND   SLOT PWR
```

The two signal rows contain 12 ordinary numbered I/O and four grounds. The
third row contains all power and four more grounds. Power is never hidden
between signal pins.

**The guide is a separate post,** not the header itself: a 1x1 pin beside each
slot with a matching hole in the extension. A bare 2x8 header cannot stop reversed
insertion on its own, and pretending otherwise would be the expensive kind of
wrong. This is the same trick Odin_0 used.

Treat the pins as ordinary `IO0..IO11`. The FPGA allocation preserves six
adjacent differential-capable pairs per slot. Pairing is an optional electrical
capability, not the connector's identity. The exact pair map is in
`ref/ballmap.md` for extensions that genuinely need it.

## The four rails, and why you are never blocked

| Pin | Rail | Fixed or set | What it is for |
|---|---|---|---|
| Power 2 | **PIN V** | **set per group: 3.3 / 2.5 / 1.8V** | Powers your voltage-matching logic and sets the FPGA pin voltage. |
| Power 6 | **+5V** | fixed | Crappy 5V parts, LCD backlights, servos. |
| Power 4 | **+3V3** | fixed | Always there even when PIN V is 1.8V. Power your sensor here. |
| Power 8 | **SLOT PWR** | set beside this slot: **+12V / +5V / +3V3** | Motors, relays, op-amps or backlights. |

**+3V3 is fixed on purpose.** If PIN VOLTAGE is set to 1.8V you still have a
normal 3.3V supply for the part you are powering. Signalling level and supply
rail are separate problems and this is the pin that keeps them separate.

## PIN VOLTAGE changes the pins — this is the important bit

An FPGA pin has no fixed voltage. Pins live in **banks**, and a bank's `VCCO`
supply *is* the logic level of every pin in it. Odin calls the connector pin
`PIN V`; the schematic's technical net name is `VCCIO`. One jumper changes
both the FPGA pins and the power delivered on `PIN V`.

So: jumper the module to 2.5V and you get a 2.5V rail on B7… and IO0–IO9
become 2.5V pins, LVDS-capable. Jumper it to 3.3V and they are 3.3V pins.
**The rail on the connector and the logic level of the pins can never
disagree.** You do not have to know this to use the board. That is the point.

## The slots, and the two voltage domains

Ten extension ports: eight direct sections and two complete 5V buses. The
`XC7A100T-FGG676` has six HR I/O banks. This board deliberately
uses two as the extension voltage domains: bank 15 for A-D and bank 34 for E-H.
Bank 14 stays fixed at 3.3V for flash, memory, control signals and 5V BUS 0.
5V BUS 1 uses fixed-3.3 V bank 13. Banks 16 and 35 remain reserved. Therefore this
revision has **two settable extension domains**:

| Slots | FPGA group | PIN VOLTAGE | Path |
|---|---|---|---|
| **5V BUS 0** | 14 | fixed 3.3V | **buffered**, 5V compatible |
| **5V BUS 1** | 13 | fixed 3.3V | **buffered**, 5V compatible |
| **A B C D** | 15 | **settable** 3.3 / 2.5 / 1.8V | direct |
| **E F G H** | 34 | **settable** 3.3 / 2.5 / 1.8V | direct |

| You plug in a | You get | PIN VOLTAGE |
|---|---|---|
| **16** (1 module) | 12 IO per edge, 24 total | shares each domain with 3 neighbours |
| **32** (2 modules) | 24 IO per edge, 48 total | shares each domain with 2 neighbours |
| **64** (4 modules) | 48 IO per edge, 96 total | **owns both domains outright** |

**Only a 64 gets a private voltage.** If your extension needs 2.5V or 1.8V
signalling, build it as a 64 and take a whole bank, or agree the voltage with
whatever else is sharing your domain. Two extensions at different voltages
means one in the A–D domain and one in E–H.

## The two 5V buses

5V BUS 0 and 5V BUS 1 are identical complete eight-bit buses. Each uses one
`SN74LXC8T245`, accepts 3.3 V on the FPGA side and 5 V on the connector side,
and has one direction control for all eight signals. Each also has a separate
FPGA-controlled `OE_N`, pulled up to +3V3 by 10k so the bus is disabled during
configuration. Set direction and data with OE_N high, then drive OE_N low to
enable; disable again before changing direction.

They are not eight unrelated bidirectional GPIOs: all eight bits on one bus
turn around together. Use them for parallel displays, legacy byte-wide parts
and other 5 V buses. Use A-H when pins need independent direction.

| | 5V BUS 0/1 | Slots A–H |
|---|---|---|
| 5V tolerant | **yes** | no (3.3V max) |
| Speed | moderate | full FPGA speed |
| LVDS | no | **yes, 5 pairs** |
| Direction | shared per complete 8-bit bus | per pin, it is a raw FPGA ball |
| VCCIO | fixed 3.3V | settable per domain |

**Junk 5V parts?** Use either 5V BUS. BUS 0 shares fixed bank 14; BUS 1 uses
fixed bank 13. Neither consumes a selectable extension voltage domain.
**Anything fast, or needing per-pin direction?** Any of A–H.

## Differential-capable pins

The connector is an ordinary numbered-I/O interface. Underneath that simple
view, six selected adjacent pin pairs per slot are routed to FPGA pair-capable
balls. Use the pairing only when it helps; consult the ball map instead of
assuming every column is a pair. A 0.1" header is not a precision
high-speed connector, so keep aggressive links short and set PIN V to 2.5V
for true LVDS output from an Artix-7 HR bank.

## How much current you actually get

**The per-slot fuses are fault protection, not an allowance.** Nine slots x
500 mA does not mean the board can source 4.5 A. Each rail has one source, and
all ten extension ports share it:

| Rail | Source | **Shared total, all slots** | Per-slot fuse |
|---|---|---|---|
| VCCIO | protected separately for A-D and E-H | **500 mA typical per domain**, subject to source headroom | 500 mA |
| +5V | `TPS54202`, or USB directly, then protected switch | **1.0 A typical** | 500 mA |
| +3V3 | `AP63300`, then protected switch | **limited to 500 mA typical at the connector bus** | 300 mA |
| **AUX 12V** | `TPS61085`, then latch-off eFuse | **500 mA typical** | 200 mA |

Those numbers are computed, not estimated round figures: every one of them
comes out of [`ref/power-budget.md`](power-budget.md), which
`tools/budget.py` generates from a worst-case load table and the regulators'
datasheet limits. Three things about them are worth knowing before you design
against them.

**+3V3 is the tight one, not AUX.** It carries the supervisor, the PSRAMs, the
config flash, FPGA bank 14, the oscillator, both SFP modules, and both VCCIO
domains if you jumper them to 3.3 V. That leaves 500 mA for all extension ports. Two
SFP modules alone are 610 mA of it — power them down and you get that back.

**AUX and +5V share a pot.** The 12 V rail is boosted *from* +5 V, and at 12 V
out each milliamp of AUX costs 2.8 mA of +5 V. The boost itself could manage
620 mA; the +5 V rail can only feed 570 mA of it, and every milliamp a slot
takes from its +5 V pin comes off that. One backlight is fine. Nine motors are
not.

## What a bad extension can do

Connector power does not come directly from Odin's internal rails. Five
shared protection channels sit before the existing slot fuses: +5V, +3V3,
VCCIO for A-D, VCCIO for E-H, and AUX 12V. They start off, limit startup and
short-circuit current, block power flowing backward into Odin, and report one
shared `EXT_FAULT` signal. A fault can turn off every slot using that shared
bus. It does not turn off the FPGA, memories, supervisor or internal rails.

This protects Odin's **power pins**. It does not make A-H signal pins tolerate
5 V. Only 5V BUS 0 and 5V BUS 1 have translated 5 V-compatible signals.

**On a plain 5 V source the +5V ceiling is the USB port, not the regulator.**
1.6 A assumes `U11` is running, which needs 9 V. Plugged into a weak laptop
port you have 0.9 A total for the whole board. If your extension needs real
current, feed it from `J50` and do not take it from the connector.

**AUX is marked provisional deliberately.** 570 mA is arithmetic on datasheet
limits at 90% assumed efficiency; it ignores thermals and board droop. Treat
it as a design target until a board has been measured.

And remember the whole board is limited by what the USB source gives you —
see `ref/power-input.md`.

## Rules

- **The 1.0V FPGA core never reaches a connector.** Do not look for it.
- Every rail is individually fused. Shorting your extension does not take the
  board down.
- **Not implemented yet:** board-ID pins. All 16 positions are spoken for, so
  there is nowhere to put them without giving up an I/O. See `findings.md`
  item 8. The supervisor still fuses and power-gates every rail; it just
  cannot yet tell *what* you plugged in.
- IO are numbered globally `IO_1..IO_112`: eight on each 5V bus, then twelve
  on each direct slot A-H, so every port's identity is readable from the net name.
- Exact FPGA ball for every pin: `ref/ballmap.md`.
- Where every current figure above comes from: `ref/power-budget.md`.

## Confirmed against the package file

Bank count, pair count and every ball assignment come from the imported
`XC7A100T-2FGG676I` symbol and are processed by `tools/ballmap.py`. Six HR
banks provide 300 user I/O. The generated `ref/ballmap.md` is authoritative.
