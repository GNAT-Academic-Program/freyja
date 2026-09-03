# Powering Odin

**One USB-C connector. That is the whole story.** Plug it into a computer, a
charger, or a USB-C power bank. There is no barrel jack you must find and no
battery to charge.

## The budget, so the numbers are not a guess

| | Peak |
|---|---|
| FPGA core (`VCCINT`, a busy design) | 1.0 W |
| `VCCAUX` + `VCCBRAM` | 0.25 W |
| `VCCO` and I/O | 1.0 W |
| PSRAM x4, active | 0.66 W |
| Supervisor + flash | 0.2 W |
| Transceiver rails, 2 lanes | 0.4 W |
| Two SFP modules | 2.0 W |
| **Base board** | **≈ 5.5 W** |
| LCD logic (Gameboy extension) | 0.5 W |
| Class-D audio amp, peak | 2.5 W |
| LCD backlight | 1.35 W |
| **With one extension** | **≈ 10 W** |

Add two-stage regulator losses and it is **12–13 W at the connector**.

That matters, because it rules something out. **Plain 5 V USB is not enough.**
A laptop port often gives 5 V at 0.9 A — 4.5 W. Even a good 5 V/3 A source is
15 W, which is the budget with nothing to spare.

## How reliable is 9 V, really?

Reliable **from a charger**, and often absent **from a computer** — which is
the awkward part, because a dev board spends its life plugged into a computer.

The USB-PD Power Rules make this precise. A source's fixed voltages are
determined by its rating:

| Source rating | Must offer |
|---|---|
| up to 15 W | 5 V |
| 15–27 W | 5 V, **9 V** |
| 27–45 W | 5 V, 9 V, 15 V |
| 45–60 W | 5 V, 9 V, 15 V, 20 V |

So **9 V is mandatory on any PD source above 15 W** — every phone charger,
laptop brick and decent power bank has it. Note what is *not* in that table:
**12 V is not a PD Power Rules voltage at all.** It is an optional extra some
sources add, which is why this board does not depend on it.

The catch is the other end. Plenty of laptop and desktop USB-C ports do no PD
negotiation whatsoever and simply offer 5 V at 0.9 A or 3 A. That is the port
you are plugged into while you write HDL.

## Therefore: 5 V is the design assumption, PD is headroom

The board is built so that **everything works at 5 V**. Power Delivery changes
how much current you can draw, not what functions. Specifically, the 12 V AUX
rail is **boosted from the 5 V rail** rather than taken from the input, so an
extension's backlight or motor works whether you are on a laptop port or a
45 W charger.

What PD actually buys you: at 9 V a 3 A source delivers 27 W against a 13 W
budget, and the current through the connector drops from ~2.6 A to ~1.4 A.
Headroom and less loss — not features.

## The negotiation, in the schematic

A `CH224K` sink chip owns the connector's CC lines and asks for 9 V. If the
source cannot supply it, the board stays on 5 V and keeps working.

The supervisor drives the sink's three configuration pins, so **the requested
voltage is firmware, not a soldered strap.** It can ask for something else if
your extension needs it, and it reads the sink's power-good pin to find out
whether the request actually succeeded.

## What actually changes on a plain 5 V source

Only two things:

- **The 5 V rail is USB `VBUS` itself**, passed through a MOSFET switch
  (`Q2`) rather than the buck, so it sits a few tens of millivolts below
  whatever the host supplies — not the ~0.4 V a diode would have cost.
- **You have less power.** 15 W at best, 4.5 W from a weak laptop port,
  against a 13 W budget. Populate two SFP modules and a loud speaker on a
  laptop port and you will run out.

Everything still *functions*, including 12 V AUX. The supervisor measures
`VSYS` on its ADC, reports the negotiated voltage over the console, and can
refuse to enable rails the source cannot sustain. Not a mystery brownout at
2am.

## Autonomy: use a USB-C power bank

**No lithium cell on the board, deliberately.** A PD power bank is
$25–40, does 9 V under load, comes in whatever capacity you want, and is
swappable. Putting a cell on the board means a charger, protection, a fuel
gauge, thermal design, a cell connector, and shipping rules for a product
containing a battery — a product-engineering project, not a dev-board feature.

At ~12 W, a 20 000 mAh (74 Wh) PD bank runs the board and a Gameboy extension
for roughly five hours. A smaller 10 000 mAh bank gives about two and a half.

One caution worth knowing: **not every power bank holds 9 V under a 1.5 A
load**, and cheap ones drop to 5 V without warning. The supervisor will tell
you when that happens, which is the point.

## The optional extra input

`J50` is a 2-pin header, Schottky-OR'd with USB-C — the higher voltage wins.
Feed it 9–20 V if you are driving something the connector cannot. Nothing
requires it. It exists so a power-hungry extension does not force a board
respin.

## In the schematic

| Ref | Part | Role |
|---|---|---|
| `J1` | USB-C receptacle | the only required input |
| `U18` | `CH224K` | PD sink; supervisor drives CFG1..3, reads PG |
| `D6`, `D7` | ESD array, TVS | protects D+/D-/CC and clamps `VBUS` |
| `Q2`, `Q3` | P-MOS + gate driver | passes `VBUS` to the 5 V rail, **default open**; firmware closes it only when the input really is 5 V |
| `D3`, `D4` | Schottky | OR-ing USB-C and the optional input into `VSYS` |
| `U12` | `TPS54202` | `VSYS` down to **3.3 V, always on** — the supervisor's own rail, ungated |
| `U11` | `TPS54202` | `VSYS` (9 V) down to 5 V |
| `U13`–`U16` | `TLV62569` x4 | 5 V down to 2.5 / 1.8 / 1.0 / 1.2 V |
| `U19` | `TPS61085` | 5 V **up** to 12 V for AUX — works on any source |

`U12` is deliberately a wide-input `TPS54202` rather than a `TLV62569` like
the rest: it must run from 5 V or 9 V, because it comes up before anything has
negotiated anything. See `ref/supervisor-flash.md`.
